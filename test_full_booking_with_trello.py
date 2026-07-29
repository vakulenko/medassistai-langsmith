"""End-to-end test: User booking -> Confirmation -> Trello card creation."""
import os
from dotenv import load_dotenv
from graph import graph
from state import ChatState, Intent, SessionManager
from config import DOCTOR_PROFILES

load_dotenv()

print("=" * 80)
print("End-to-End Booking Flow with Trello Card Creation")
print("=" * 80)

# Initialize session
session = SessionManager.create_session("Test Session")
print(f"\n[SESSION] {session.name} ({session.session_id})")

# ============================================================================
# MESSAGE 1: User provides booking details
# ============================================================================
print("\n[MESSAGE 1] User: 'I need to book with Dr. Dalla McDer tomorrow at 2 PM'")
print("-" * 80)

user_msg1 = "I need to book with Dr. Dalla McDer tomorrow at 2 PM. My name is John Doe and my email is john@test.com. Patient_ID: P001."
session.chat_history.append({"role": "user", "content": user_msg1})
session.conversation_history.append({"role": "user", "content": user_msg1})

# Create initial state
state1 = ChatState(
    user_input=user_msg1,
    messages=session.chat_history,
    conversation_history=session.conversation_history,
    available_doctors=list(DOCTOR_PROFILES.keys())
)

print(f"\nBefore graph.invoke():")
print(f"  intent: {state1.detected_intent}")
print(f"  extracted_info: {state1.extracted_info}")
print(f"  patient_id: {state1.patient_id}")
print(f"  booking_confirmed: {state1.booking_confirmed}")

# Invoke graph
print(f"\n[INVOKING GRAPH]")
result1 = graph.invoke(state1)

print(f"\nAfter graph.invoke():")
print(f"  intent: {result1.get('detected_intent')}")
print(f"  extracted_info: {result1.get('extracted_info')}")
print(f"  patient_id: {result1.get('patient_id')}")
print(f"  appointment_ready_for_confirmation: {result1.get('appointment_ready_for_confirmation')}")
print(f"  booking_confirmed: {result1.get('booking_confirmed')}")

response1 = result1.get('last_response', 'No response')
print(f"\nBot response (first 200 chars):")
print(f"  {response1[:200]}...")

session.chat_history.append({"role": "assistant", "content": response1})
session.conversation_history.append({"role": "assistant", "content": response1})

# Extract state for Message 2
booking_state = {
    "patient_id": result1.get("patient_id"),
    "extracted_info": result1.get("extracted_info", {}),
    "use_rag_context": result1.get("use_rag_context", False),
    "requested_specialization": result1.get("requested_specialization"),
    "has_available_doctor": result1.get("has_available_doctor", False),
    "appointment_ready_for_confirmation": result1.get("appointment_ready_for_confirmation", False),
    "is_deceased_patient": result1.get("is_deceased_patient", False),
    "patient_not_found": result1.get("patient_not_found", False),
    "should_add_patient": result1.get("should_add_patient", False),
}

print(f"\nState saved for next message:")
print(f"  patient_id: {booking_state.get('patient_id')}")
print(f"  appointment_date: {booking_state.get('extracted_info', {}).get('appointment_date')}")
print(f"  appointment_time: {booking_state.get('extracted_info', {}).get('appointment_time')}")
print(f"  appointment_ready_for_confirmation: {booking_state.get('appointment_ready_for_confirmation')}")

# ============================================================================
# MESSAGE 2: User confirms
# ============================================================================
print("\n\n[MESSAGE 2] User: 'Yes, approve the booking'")
print("-" * 80)

user_msg2 = "Yes, approve the booking"
session.chat_history.append({"role": "user", "content": user_msg2})
session.conversation_history.append({"role": "user", "content": user_msg2})

# Create state for Message 2, restoring saved state
state2 = ChatState(
    user_input=user_msg2,
    messages=session.chat_history,
    conversation_history=session.conversation_history,
    available_doctors=list(DOCTOR_PROFILES.keys()),
    # Restore from previous state
    patient_id=booking_state.get("patient_id"),
    extracted_info=booking_state.get("extracted_info", {}),
    use_rag_context=booking_state.get("use_rag_context", False),
    requested_specialization=booking_state.get("requested_specialization"),
    has_available_doctor=booking_state.get("has_available_doctor", False),
    appointment_ready_for_confirmation=booking_state.get("appointment_ready_for_confirmation", False),
    is_deceased_patient=booking_state.get("is_deceased_patient", False),
    patient_not_found=booking_state.get("patient_not_found", False),
    should_add_patient=booking_state.get("should_add_patient", False),
)

print(f"\nBefore graph.invoke():")
print(f"  user_input: '{state2.user_input}'")
print(f"  appointment_ready_for_confirmation: {state2.appointment_ready_for_confirmation}")
print(f"  extracted_info has date: {bool(state2.extracted_info.get('appointment_date'))}")
print(f"  extracted_info has time: {bool(state2.extracted_info.get('appointment_time'))}")

# Invoke graph
print(f"\n[INVOKING GRAPH]")
print(f"This should route to: ask_for_confirmation -> handle_confirmation -> create_trello_card")
result2 = graph.invoke(state2)

print(f"\nAfter graph.invoke():")
print(f"  booking_confirmed: {result2.get('booking_confirmed')}")
print(f"  extracted_info (has date): {bool(result2.get('extracted_info', {}).get('appointment_date'))}")
print(f"  extracted_info (has time): {bool(result2.get('extracted_info', {}).get('appointment_time'))}")

response2 = result2.get('last_response', 'No response')
print(f"\nBot response (first 200 chars):")
print(f"  {response2[:200]}...")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("Result Summary")
print("=" * 80)

if result2.get('booking_confirmed'):
    print("\n[SUCCESS] Booking confirmed!")
    print("\nExtracted appointment details:")
    extracted = result2.get('extracted_info', {})
    print(f"  Patient: {extracted.get('patient_name')}")
    print(f"  Doctor: {extracted.get('doctor_name')}")
    print(f"  Date: {extracted.get('appointment_date')}")
    print(f"  Time: {extracted.get('appointment_time')}")
    print(f"\nThis should have created a Trello card in the 'In Queue' list")
    print("of the Appointments board.")
else:
    print("\n[FAIL] Booking was NOT confirmed")
    print("\nDEBUGGING INFO:")
    print(f"  Last response: {response2[:300]}...")
    print(f"  Booking state flag: {result2.get('booking_confirmed')}")
    print(f"  Extracted info: {result2.get('extracted_info')}")

print("\n" + "=" * 80)
