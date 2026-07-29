"""Test with a correct human doctor for booking."""
import os
from dotenv import load_dotenv
from graph import graph
from state import ChatState, Intent, SessionManager
from config import DOCTOR_PROFILES

load_dotenv()

print("=" * 80)
print("Test Booking with Correct Human Doctor")
print("=" * 80)

# Check what doctors are available
print("\nAvailable doctors:")
for doc in DOCTOR_PROFILES.keys():
    print(f"  - {doc}")

# Use a doctor that's in the system
session = SessionManager.create_session("Test")

# ============================================================================
# MESSAGE 1
# ============================================================================
print("\n[MESSAGE 1] Book with Dr. Jacki Senge")
print("-" * 80)

user_msg1 = "My name is John Doe. I want to book Dr. Jacki Senge for a general checkup tomorrow at 10:30 AM. My email is john@test.com and my patient ID is P001."

session.chat_history.append({"role": "user", "content": user_msg1})
session.conversation_history.append({"role": "user", "content": user_msg1})

state1 = ChatState(
    user_input=user_msg1,
    messages=session.chat_history,
    conversation_history=session.conversation_history,
    available_doctors=list(DOCTOR_PROFILES.keys())
)

print(f"Input: {user_msg1[:80]}...")
print(f"\n[INVOKING GRAPH]")
result1 = graph.invoke(state1)

print(f"\nResult:")
print(f"  Patient: {result1.get('extracted_info', {}).get('patient_name')}")
print(f"  Doctor: {result1.get('extracted_info', {}).get('doctor_name')}")
print(f"  Date: {result1.get('extracted_info', {}).get('appointment_date')}")
print(f"  Time: {result1.get('extracted_info', {}).get('appointment_time')}")
print(f"  Confirmation ready: {result1.get('appointment_ready_for_confirmation')}")
print(f"  Booking confirmed: {result1.get('booking_confirmed')}")
print(f"  Is deceased: {result1.get('is_deceased_patient')}")

response1 = result1.get('last_response', '')
if 'confirm' in response1.lower() or 'approve' in response1.lower():
    print(f"  -> Bot is asking for confirmation")
else:
    print(f"  -> Bot says: {response1[:150]}...")

booking_state = {
    "patient_id": result1.get("patient_id"),
    "extracted_info": result1.get("extracted_info", {}),
    "use_rag_context": result1.get("use_rag_context", False),
    "requested_specialization": result1.get("requested_specialization"),
    "has_available_doctor": result1.get("has_available_doctor", False),
    "appointment_ready_for_confirmation": result1.get("appointment_ready_for_confirmation", False),
    "is_deceased_patient": result1.get("is_deceased_patient", False),
    "patient_not_found": result1.get("patient_not_found", False),
}

session.chat_history.append({"role": "assistant", "content": response1})
session.conversation_history.append({"role": "assistant", "content": response1})

# ============================================================================
# MESSAGE 2
# ============================================================================
if booking_state.get("appointment_ready_for_confirmation"):
    print("\n[MESSAGE 2] User confirms")
    print("-" * 80)

    user_msg2 = "Yes, approve"
    session.chat_history.append({"role": "user", "content": user_msg2})
    session.conversation_history.append({"role": "user", "content": user_msg2})

    state2 = ChatState(
        user_input=user_msg2,
        messages=session.chat_history,
        conversation_history=session.conversation_history,
        available_doctors=list(DOCTOR_PROFILES.keys()),
        patient_id=booking_state.get("patient_id"),
        extracted_info=booking_state.get("extracted_info", {}),
        use_rag_context=booking_state.get("use_rag_context", False),
        requested_specialization=booking_state.get("requested_specialization"),
        has_available_doctor=booking_state.get("has_available_doctor", False),
        appointment_ready_for_confirmation=booking_state.get("appointment_ready_for_confirmation", False),
        is_deceased_patient=booking_state.get("is_deceased_patient", False),
        patient_not_found=booking_state.get("patient_not_found", False),
    )

    print(f"Input: {user_msg2}")
    print(f"\n[INVOKING GRAPH]")
    result2 = graph.invoke(state2)

    print(f"\nResult:")
    print(f"  Booking confirmed: {result2.get('booking_confirmed')}")
    print(f"  Patient: {result2.get('extracted_info', {}).get('patient_name')}")
    print(f"  Doctor: {result2.get('extracted_info', {}).get('doctor_name')}")
    print(f"  Date: {result2.get('extracted_info', {}).get('appointment_date')}")
    print(f"  Time: {result2.get('extracted_info', {}).get('appointment_time')}")

    response2 = result2.get('last_response', '')
    print(f"  Bot: {response2[:150]}...")

    print("\n" + "=" * 80)
    if result2.get('booking_confirmed'):
        print("[SUCCESS] Booking confirmed! Trello card should be created.")
    else:
        print("[FAIL] Booking not confirmed")
else:
    print("\n[SKIP] Message 2 - bot didn't ask for confirmation")

print("=" * 80)
