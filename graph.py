from langgraph.graph import StateGraph, END
from state import ChatState, Intent
from intent_detector import detect_intent
from info_extractor import extract_info
from response_generator import generate_response
from langsmith import traceable
from trello_tools import create_appointment_card, create_fraud_card

@traceable(name="should_continue", run_type="chain")
def should_continue(state: ChatState):
    """Determine if booking flow should continue or end."""
    if state.detected_intent == Intent.BOOK_APPOINTMENT:
        # Check if all required info is present
        required_fields = ["patient_name", "patient_email", "doctor_name", "appointment_date", "appointment_time"]
        missing_fields = [f for f in required_fields if not state.extracted_info.get(f)]

        if not missing_fields:
            return "confirm_booking"
        return "ask_for_info"
    return END


def create_appointment_on_trello(state: ChatState):
    """Create appointment card on Trello when booking is confirmed."""
    if state.booking_confirmed and state.extracted_info:
        create_appointment_card(
            patient_name=state.extracted_info.get("patient_name", "Unknown"),
            doctor_name=state.extracted_info.get("doctor_name", "Unknown"),
            appointment_date=state.extracted_info.get("appointment_date", "Unknown"),
            appointment_time=state.extracted_info.get("appointment_time", "Unknown"),
            reason=state.extracted_info.get("reason", "General checkup"),
            patient_email=state.extracted_info.get("patient_email")
        )
    return state


def check_fraud_and_alert(state: ChatState):
    """Check for fraud patterns and create ticket if suspicious."""
    # Simple fraud detection: check for inconsistencies in patient data
    extracted = state.extracted_info or {}
    fraud_detected = False
    fraud_reason = ""

    # Check for suspicious patterns (expand this as needed)
    if extracted.get("patient_name") and len(extracted.get("patient_name", "")) < 3:
        fraud_detected = True
        fraud_reason = "Suspiciously short patient name"

    if fraud_detected:
        create_fraud_card(
            patient_name=extracted.get("patient_name", "Unknown"),
            fraud_type="Data validation",
            reason=fraud_reason,
            session_id=state.extracted_info.get("session_id", "unknown"),
            patient_email=extracted.get("patient_email")
        )

    return state

def build_graph():
    """Build the LangGraph workflow for appointment booking."""
    workflow = StateGraph(ChatState)

    # Add nodes
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("extract_info", extract_info)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("ask_for_info", lambda state: state)
    workflow.add_node("confirm_booking", lambda state: {**state.__dict__, "booking_confirmed": True})
    workflow.add_node("create_trello_card", create_appointment_on_trello)
    workflow.add_node("check_fraud", check_fraud_and_alert)

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
            "confirm_booking": "create_trello_card",
            END: END,
        }
    )
    workflow.add_edge("create_trello_card", END)

    return workflow.compile()

graph = build_graph()

if __name__ == "__main__":
    print("✓ Graph initialized successfully")
