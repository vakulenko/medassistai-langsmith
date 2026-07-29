from langgraph.graph import StateGraph, END
from state import ChatState, Intent
from intent_detector import detect_intent
from info_extractor import extract_info
from response_generator import generate_response
from langsmith import traceable
from trello_tools import create_appointment_card, create_fraud_card, create_add_patient_card, cancel_appointment_card

@traceable(name="should_continue", run_type="chain")
def should_continue(state: ChatState):
    """Determine if booking flow should continue or end."""
    if state.detected_intent == Intent.BOOK_APPOINTMENT:
        # If deceased patient detected, skip to confirmation (but will only create fraud ticket)
        if state.is_deceased_patient:
            state.appointment_ready_for_confirmation = True
            return "ask_for_confirmation"

        # Check if specialization is not available (we cannot help)
        if state.requested_specialization and not state.has_available_doctor:
            return END

        # Check if all required info is present (including Patient ID)
        required_fields = ["patient_name", "patient_email", "doctor_name", "appointment_date", "appointment_time"]
        missing_fields = [f for f in required_fields if not state.extracted_info.get(f)]

        # Patient ID is also required
        if not state.patient_id:
            return "ask_for_info"

        # If patient not found AND we have patient name + email + doctor, go to confirmation
        # (missing fields don't matter for new patient)
        if state.patient_not_found:
            if state.extracted_info.get("patient_name") and state.extracted_info.get("patient_email"):
                state.appointment_ready_for_confirmation = True
                return "ask_for_confirmation"
            return "ask_for_info"

        if not missing_fields:
            # All info present - ask for explicit confirmation
            state.appointment_ready_for_confirmation = True
            return "ask_for_confirmation"
        return "ask_for_info"

    elif state.detected_intent == Intent.CANCEL_APPOINTMENT:
        # Check if we have patient identifier (name or ID)
        if state.patient_id or state.extracted_info.get("patient_name"):
            state.cancel_ready_for_confirmation = True
            return "ask_for_cancellation_confirmation"
        return "ask_for_info"

    return END


def create_appointment_on_trello(state: ChatState):
    """Create appointment card on Trello when booking is confirmed.

    For deceased patients: skip appointment card, create fraud ticket (honeypot).
    For new patients: create both appointment and add-patient cards.
    For existing patients: create appointment card only.
    """
    if state.is_deceased_patient:
        # Deceased patient: don't create appointment card
        # CREATE fraud ticket NOW (after confirmation)
        create_fraud_card(
            patient_name=state.extracted_info.get("patient_name", "Unknown"),
            fraud_type="Deceased patient",
            reason=f"Booking attempt for deceased patient ID: {state.patient_id}",
            session_id=state.extracted_info.get("session_id", "unknown"),
            patient_email=state.extracted_info.get("patient_email")
        )
        # Mark as confirmed to show success response (honeypot)
        state.booking_confirmed = True
        print("[INFO] Deceased patient confirmed booking - fraud ticket created, no appointment card")
        return state

    # Normal booking: create appointment card
    if state.extracted_info:
        create_appointment_card(
            patient_name=state.extracted_info.get("patient_name", "Unknown"),
            doctor_name=state.extracted_info.get("doctor_name", "Unknown"),
            appointment_date=state.extracted_info.get("appointment_date", "Unknown"),
            appointment_time=state.extracted_info.get("appointment_time", "Unknown"),
            reason=state.extracted_info.get("reason", "General checkup"),
            patient_email=state.extracted_info.get("patient_email"),
            patient_id=state.patient_id
        )

        # If patient not found in system, create add-patient card as well
        if state.patient_not_found:
            create_add_patient_card(
                patient_name=state.extracted_info.get("patient_name", "Unknown"),
                patient_email=state.extracted_info.get("patient_email"),
                patient_id=state.patient_id,
                notes=f"New patient booking: {state.extracted_info.get('reason', 'General')}"
            )

        state.booking_confirmed = True
    return state


def handle_cancellation_confirmation(state: ChatState):
    """Handle user confirmation for appointment cancellation."""
    user_input_lower = state.user_input.lower().strip()

    # Check for approval keywords
    if any(keyword in user_input_lower for keyword in ["yes", "approve", "confirm", "agree", "ok", "okay", "go ahead"]):
        return "process_cancellation"
    elif any(keyword in user_input_lower for keyword in ["no", "reject", "cancel", "decline", "stop"]):
        return "reject_cancellation"
    else:
        # Unclear response, ask again
        return END


def process_cancellation(state: ChatState):
    """Process appointment cancellation request."""
    # If deceased patient, just show success without actually cancelling
    if state.is_deceased_patient:
        state.last_response = "Appointment cancellation completed. Thank you."
        print("[INFO] Deceased patient cancellation request - ignoring (not in system)")
        return state

    # For normal patients, delete the appointment card and create cancellation record
    cancel_appointment_card(
        patient_name=state.extracted_info.get("patient_name", "Unknown"),
        patient_id=state.patient_id
    )

    state.last_response = "Your appointment has been successfully cancelled. A confirmation email will be sent to you shortly. If you need to schedule a new appointment, please let us know."
    return state


def reject_cancellation(state: ChatState):
    """Handle cancellation rejection."""
    state.last_response = "Cancellation has been cancelled. Your appointment remains scheduled."
    return state


def check_fraud_and_alert(state: ChatState):
    """Check for fraud patterns and create ticket if suspicious.

    NOTE: For deceased patients, fraud ticket is created AFTER confirmation,
    not here. This node only flags the patient as deceased.
    """
    # Deceased patient handling moved to create_appointment_on_trello
    # after user confirms, to ensure fraud ticket only created after confirmation

    # Simple fraud detection: check for inconsistencies in patient data
    extracted = state.extracted_info or {}
    fraud_detected = False
    fraud_reason = ""

    # Check for suspicious patterns (but not deceased - that's handled later)
    if extracted.get("patient_name") and len(extracted.get("patient_name", "")) < 3:
        fraud_detected = True
        fraud_reason = "Suspiciously short patient name"

    if fraud_detected:
        create_fraud_card(
            patient_name=extracted.get("patient_name", "Unknown"),
            fraud_type="Data validation",
            reason=fraud_reason,
            session_id=extracted.get("session_id", "unknown"),
            patient_email=extracted.get("patient_email")
        )

    return state

def handle_confirmation(state: ChatState):
    """Handle user confirmation of appointment."""
    user_input_lower = state.user_input.lower().strip()

    # Check for approval keywords
    if any(keyword in user_input_lower for keyword in ["yes", "approve", "confirm", "agree", "ok", "okay", "go ahead"]):
        return "create_trello_card"
    elif any(keyword in user_input_lower for keyword in ["no", "reject", "cancel", "decline", "stop"]):
        return "reject_booking"
    else:
        # Unclear response, ask again
        return END


def reject_booking(state: ChatState):
    """Handle booking rejection."""
    state.last_response = "Booking cancelled. Feel free to contact us if you change your mind."
    return state


def build_graph():
    """Build the LangGraph workflow for appointment booking."""
    workflow = StateGraph(ChatState)

    # Add nodes
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("extract_info", extract_info)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("ask_for_info", lambda state: state)
    workflow.add_node("ask_for_confirmation", lambda state: state)
    workflow.add_node("ask_for_cancellation_confirmation", lambda state: state)
    workflow.add_node("confirm_booking", lambda state: {**state.__dict__, "booking_confirmed": True})
    workflow.add_node("create_trello_card", create_appointment_on_trello)
    workflow.add_node("check_fraud", check_fraud_and_alert)
    workflow.add_node("reject_booking", reject_booking)
    workflow.add_node("process_cancellation", process_cancellation)
    workflow.add_node("reject_cancellation", reject_cancellation)

    # Set entry point
    workflow.set_entry_point("detect_intent")

    # Add edges
    workflow.add_edge("detect_intent", "extract_info")
    workflow.add_edge("extract_info", "check_fraud")
    workflow.add_edge("check_fraud", "generate_response")
    workflow.add_conditional_edges(
        "generate_response",
        should_continue,
        {
            "ask_for_info": END,
            "ask_for_confirmation": "ask_for_confirmation",
            "ask_for_cancellation_confirmation": "ask_for_cancellation_confirmation",
            "confirm_booking": "create_trello_card",
            END: END,
        }
    )
    workflow.add_conditional_edges(
        "ask_for_confirmation",
        handle_confirmation,
        {
            "create_trello_card": "create_trello_card",
            "reject_booking": "reject_booking",
            END: END,
        }
    )
    workflow.add_conditional_edges(
        "ask_for_cancellation_confirmation",
        handle_cancellation_confirmation,
        {
            "process_cancellation": "process_cancellation",
            "reject_cancellation": "reject_cancellation",
            END: END,
        }
    )
    workflow.add_edge("create_trello_card", END)
    workflow.add_edge("reject_booking", END)
    workflow.add_edge("process_cancellation", END)
    workflow.add_edge("reject_cancellation", END)

    return workflow.compile()

graph = build_graph()

if __name__ == "__main__":
    print("✓ Graph initialized successfully")
