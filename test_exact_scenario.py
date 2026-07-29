"""Test exact scenario from user input."""
import os
from dotenv import load_dotenv
from graph import graph
from state import ChatState, Intent, SessionManager
from config import DOCTOR_PROFILES

load_dotenv()

print("=" * 80)
print("Testing Exact User Scenario")
print("=" * 80)

session = SessionManager.create_session("User Session")

# ============================================================================
# MESSAGE 1: User input exactly as provided
# ============================================================================
print("\n[MESSAGE 1] User input:")
user_msg1 = "I need a ophthalmologist tomorrow. I have sight issue. My Patient_ID: P002. My name is Sergii Vakulenko; test@test.com at 12:34 PM"
print(f'"{user_msg1}"\n')

session.chat_history.append({"role": "user", "content": user_msg1})
session.conversation_history.append({"role": "user", "content": user_msg1})

state1 = ChatState(
    user_input=user_msg1,
    messages=session.chat_history,
    conversation_history=session.conversation_history,
    available_doctors=list(DOCTOR_PROFILES.keys())
)

print("[INVOKING GRAPH for Message 1]")
result1 = graph.invoke(state1)

print(f"\nResult 1:")
print(f"  Patient ID: {result1.get('patient_id')}")
print(f"  Confirmation ready: {result1.get('appointment_ready_for_confirmation')}")
print(f"  Booking confirmed: {result1.get('booking_confirmed')}")
print(f"  Date: {result1.get('extracted_info', {}).get('appointment_date')}")
print(f"  Time: {result1.get('extracted_info', {}).get('appointment_time')}")

response1 = result1.get('last_response', '')[:300]
print(f"\nBot: {response1}...\n")

session.chat_history.append({"role": "assistant", "content": result1.get('last_response', '')})
session.conversation_history.append({"role": "assistant", "content": result1.get('last_response', '')})

# Save state for Message 2
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

# ============================================================================
# MESSAGE 2: User confirmation
# ============================================================================
if booking_state.get("appointment_ready_for_confirmation"):
    print("[MESSAGE 2] User input:")
    user_msg2 = "Approve"
    print(f'"{user_msg2}"\n')

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

    print("[INVOKING GRAPH for Message 2]")
    result2 = graph.invoke(state2)

    print(f"\nResult 2:")
    print(f"  Booking confirmed: {result2.get('booking_confirmed')}")
    print(f"  Patient: {result2.get('extracted_info', {}).get('patient_name')}")
    print(f"  Doctor: {result2.get('extracted_info', {}).get('doctor_name')}")
    print(f"  Date: {result2.get('extracted_info', {}).get('appointment_date')}")
    print(f"  Time: {result2.get('extracted_info', {}).get('appointment_time')}")

    response2 = result2.get('last_response', '')[:300]
    print(f"\nBot: {response2}...\n")

    # Final result
    print("=" * 80)
    if result2.get('booking_confirmed'):
        print("[SUCCESS] Booking confirmed!")
        print("[SUCCESS] Trello card should have been created!")
    else:
        print("[FAIL] Booking NOT confirmed")
        print(f"Debug: {result2.get('last_response', '')[:200]}")
else:
    print(f"\n[ERROR] Message 1 did not set appointment_ready_for_confirmation")
    print(f"Cannot proceed to Message 2")

print("=" * 80)
