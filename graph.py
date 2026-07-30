from langgraph.graph import StateGraph, END
from state import ChatState, Intent
from langsmith import traceable
from agents import (
    IntentDetectionAgent,
    ExtractionAgent,
    PatientValidationAgent,
    FraudDetectionAgent,
    ResponseGenerationAgent,
    ConfirmationValidationAgent
)
from trello_tools import create_appointment_card, create_fraud_card, create_add_patient_card


# Initialize agents
intent_agent = IntentDetectionAgent()
extraction_agent = ExtractionAgent()
validation_agent = PatientValidationAgent()
fraud_agent = FraudDetectionAgent()
response_agent = ResponseGenerationAgent()
confirmation_agent = ConfirmationValidationAgent()


# Node functions
@traceable(name="intent_detection_node", run_type="chain")
def intent_detection_node(state: ChatState) -> ChatState:
    """Detect user intent.

    Note: If resuming from interrupt (appointment_ready_for_confirmation=True),
    skip intent detection to preserve the booking context.
    """
    # Skip intent detection when resuming from interrupt
    if state.appointment_ready_for_confirmation and state.detected_intent == Intent.BOOK_APPOINTMENT:
        print("[IntentDetectionAgent] SKIPPED - Resuming from interrupt")
        return state

    return intent_agent.execute(state)


@traceable(name="extraction_node", run_type="chain")
def extraction_node(state: ChatState) -> ChatState:
    """Extract appointment information.

    Note: If resuming from interrupt, skip extraction to preserve existing extracted data.
    """
    # Skip extraction when resuming from interrupt
    if state.appointment_ready_for_confirmation and state.extracted_info:
        print("[ExtractionAgent] SKIPPED - Using preserved extracted info from previous turn")
        return state

    return extraction_agent.execute(state)


@traceable(name="fraud_detection_node", run_type="chain")
def fraud_detection_node(state: ChatState) -> ChatState:
    """Check for fraudulent patterns."""
    return fraud_agent.execute(state)


@traceable(name="patient_validation_node", run_type="chain")
def patient_validation_node(state: ChatState) -> ChatState:
    """Validate patient data and check availability."""
    return validation_agent.execute(state)


@traceable(name="response_generation_node", run_type="chain")
def response_generation_node(state: ChatState) -> ChatState:
    """Generate response based on state.

    Note: Skip when resuming from interrupt with confirmation input to let
    confirmation_validation handle the response instead.
    """
    # Skip response generation when resuming from interrupt with confirmation
    if state.appointment_ready_for_confirmation and state.user_input:
        if any(word in state.user_input.lower() for word in ["yes", "approve", "confirm", "agree", "ok", "go", "no", "reject", "cancel", "decline"]):
            print("[ResponseGenerationAgent] SKIPPED - Confirmation input detected, routing to confirmation validation")
            print(f"[ResponseGenerationAgent] Current last_response: {state.last_response[:50] if state.last_response else 'None'}...")
            return state  # Return state unchanged - last_response is already set from message 1

    return response_agent.execute(state)


@traceable(name="confirmation_validation_node", run_type="chain")
def confirmation_validation_node(state: ChatState) -> ChatState:
    """Validate user confirmation response."""
    return confirmation_agent.execute(state)


@traceable(name="appointment_creation_node", run_type="chain")
def appointment_creation_node(state: ChatState) -> ChatState:
    """Create appointment on Trello."""
    if state.is_deceased_patient:
        create_fraud_card(
            patient_name=state.extracted_info.get("patient_name", "Unknown"),
            fraud_type="Deceased patient",
            reason=f"Booking attempt for deceased patient ID: {state.patient_id}",
            session_id=state.extracted_info.get("session_id", "unknown"),
            patient_email=state.extracted_info.get("patient_email")
        )
        state.booking_confirmed = True
        return state

    extracted = state.extracted_info or {}

    if extracted or state.patient_id:
        success = create_appointment_card(
            patient_name=extracted.get("patient_name", "Unknown"),
            doctor_name=extracted.get("doctor_name", "Unknown"),
            appointment_date=extracted.get("appointment_date", "Unknown"),
            appointment_time=extracted.get("appointment_time", "Unknown"),
            reason=extracted.get("reason", "General checkup"),
            patient_email=extracted.get("patient_email"),
            patient_id=state.patient_id
        )

        if state.patient_not_found:
            success_patient_card = create_add_patient_card(
                patient_name=extracted.get("patient_name", "Unknown"),
                patient_email=extracted.get("patient_email"),
                patient_id=state.patient_id,
                notes=f"New patient booking: {extracted.get('reason', 'General')}"
            )

        state.booking_confirmed = True

    return state


@traceable(name="set_confirmation_flags", run_type="chain")
def set_confirmation_flags(state: ChatState) -> ChatState:
    """Set confirmation flags based on state."""
    if state.appointment_ready_for_confirmation:
        return state

    if state.detected_intent == Intent.BOOK_APPOINTMENT:
        if state.is_deceased_patient:
            state.appointment_ready_for_confirmation = True

        required_fields = ["patient_name", "patient_email", "doctor_name", "appointment_date", "appointment_time"]
        missing_fields = [f for f in required_fields if not state.extracted_info.get(f)]

        if state.patient_not_found:
            if state.extracted_info.get("patient_name") and state.extracted_info.get("patient_email"):
                state.appointment_ready_for_confirmation = True
        elif state.patient_id and not missing_fields:
            state.appointment_ready_for_confirmation = True

    return state


def should_route_to_validation(state: ChatState) -> bool:
    """Determine if patient validation should run."""
    return state.detected_intent == Intent.BOOK_APPOINTMENT


def should_continue(state: ChatState) -> str:
    """Determine routing after flag setting.

    When resuming from interrupt (appointment_ready_for_confirmation=True and
    user has provided confirmation input), route directly to confirmation_validation.
    """
    # CHECK FOR RESUME FIRST - confirmation input detected while already ready for confirmation
    if state.appointment_ready_for_confirmation and state.user_input:
        user_input_lower = state.user_input.lower()
        confirm_words = ["yes", "approve", "confirm", "agree", "ok", "go"]
        reject_words = ["no", "reject", "cancel", "decline", "stop"]

        if any(word in user_input_lower for word in confirm_words + reject_words):
            print(f"[should_continue] RESUME MODE: Routing to confirmation_validation (user said '{state.user_input}')")
            return "confirmation_validation"
        return "ask_for_confirmation"

    if state.appointment_ready_for_confirmation:
        print(f"[should_continue] Ready for confirmation but no clear response, staying at ask_for_confirmation")
        return "ask_for_confirmation"

    if state.detected_intent == Intent.BOOK_APPOINTMENT:
        if state.requested_specialization and not state.has_available_doctor:
            return END

        required_fields = ["patient_name", "patient_email", "doctor_name", "appointment_date", "appointment_time"]
        missing_fields = [f for f in required_fields if not state.extracted_info.get(f)]

        if not state.patient_id:
            return "ask_for_info"

        if state.patient_not_found:
            if state.extracted_info.get("patient_name") and state.extracted_info.get("patient_email"):
                return "ask_for_confirmation"
            return "ask_for_info"

        if not missing_fields:
            return "ask_for_confirmation"
        return "ask_for_info"

    return END


def handle_confirmation(state: ChatState) -> str:
    """Handle confirmation routing."""
    user_input_lower = state.user_input.lower().strip()

    if any(keyword in user_input_lower for keyword in ["yes", "approve", "confirm", "agree", "ok", "okay", "go ahead"]):
        return "create_appointment"
    elif any(keyword in user_input_lower for keyword in ["no", "reject", "cancel", "decline", "stop"]):
        return "reject_booking"
    else:
        return END


def reject_booking(state: ChatState) -> ChatState:
    """Handle booking rejection."""
    state.last_response = "Booking cancelled. Feel free to contact us if you change your mind."
    return state


def build_graph():
    """Build the multi-node LangGraph workflow with interrupt support.

    Interrupts occur when user confirmation is needed to save LLM tokens.
    The graph pauses execution and waits for user input before continuing.
    """
    workflow = StateGraph(ChatState)

    # Add all nodes
    workflow.add_node("intent_detection", intent_detection_node)
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("fraud_detection", fraud_detection_node)
    workflow.add_node("patient_validation", patient_validation_node)
    workflow.add_node("set_flags", set_confirmation_flags)
    workflow.add_node("response_generation", response_generation_node)
    workflow.add_node("ask_for_info", lambda state: state)
    workflow.add_node("ask_for_confirmation", lambda state: state)
    workflow.add_node("confirmation_validation", confirmation_validation_node)
    workflow.add_node("create_appointment", appointment_creation_node)
    workflow.add_node("reject_booking", reject_booking)

    # Set entry point
    # When resuming from interrupt, detected_intent will already be set
    # and appointment_ready_for_confirmation will be true
    # In that case, we want to skip intent/extraction and go straight to confirmation
    workflow.set_entry_point("intent_detection")

    # Add edges
    workflow.add_edge("intent_detection", "extraction")
    workflow.add_edge("extraction", "fraud_detection")

    # Conditional edge: route to validation only for booking intent
    workflow.add_conditional_edges(
        "fraud_detection",
        should_route_to_validation,
        {
            True: "patient_validation",
            False: "set_flags"
        }
    )

    workflow.add_edge("patient_validation", "set_flags")

    # Route directly to confirmation if resuming from interrupt
    def route_from_set_flags(state: ChatState) -> str:
        if state.appointment_ready_for_confirmation and state.user_input:
            confirmation_words = ["yes", "approve", "confirm", "agree", "ok", "go", "no", "reject", "cancel", "decline"]
            if any(w in state.user_input.lower() for w in confirmation_words):
                return "confirmation_validation"
        return "response_generation"

    workflow.add_conditional_edges(
        "set_flags",
        route_from_set_flags,
        {
            "confirmation_validation": "confirmation_validation",
            "response_generation": "response_generation",
        }
    )

    # For normal flow: response_generation routes based on confirmation readiness
    # Add conditional edge: route based on confirmation readiness
    workflow.add_conditional_edges(
        "response_generation",
        should_continue,
        {
            "ask_for_info": "ask_for_info",
            "ask_for_confirmation": "ask_for_confirmation",
            "confirmation_validation": "confirmation_validation",  # Direct route on resume
            END: END,
        }
    )

    # Handle responses
    workflow.add_edge("ask_for_info", END)
    workflow.add_edge("ask_for_confirmation", "confirmation_validation")

    # Confirmation routing
    workflow.add_conditional_edges(
        "confirmation_validation",
        handle_confirmation,
        {
            "create_appointment": "create_appointment",
            "reject_booking": "reject_booking",
            END: END,
        }
    )

    workflow.add_edge("create_appointment", END)
    workflow.add_edge("reject_booking", END)

    # DO NOT use interrupt_before here - it causes issues with resuming from interrupt
    # Instead, the app handles pausing at ask_for_confirmation
    # When resuming with confirmation input, the graph routes from set_flags directly to confirmation_validation
    return workflow.compile()


graph = build_graph()

if __name__ == "__main__":
    print("[OK] Multi-node multi-agent graph initialized successfully")
