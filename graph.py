from langgraph.graph import StateGraph, END
from state import ChatState, Intent
from intent_detector import detect_intent
from info_extractor import extract_info
from response_generator import generate_response
from langsmith import traceable

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

def build_graph():
    """Build the LangGraph workflow for appointment booking."""
    workflow = StateGraph(ChatState)

    # Add nodes
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("extract_info", extract_info)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("ask_for_info", lambda state: state)
    workflow.add_node("confirm_booking", lambda state: {**state.__dict__, "booking_confirmed": True})

    # Set entry point
    workflow.set_entry_point("detect_intent")

    # Add edges
    workflow.add_edge("detect_intent", "extract_info")
    workflow.add_edge("extract_info", "generate_response")
    workflow.add_conditional_edges(
        "generate_response",
        should_continue,
        {
            "ask_for_info": END,
            "confirm_booking": END,
            END: END,
        }
    )

    return workflow.compile()

graph = build_graph()

if __name__ == "__main__":
    print("✓ Graph initialized successfully")
