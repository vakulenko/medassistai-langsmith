"""Test booking for patient NOT in database - creates both appointment AND add-patient ticket."""
import os
from dotenv import load_dotenv
from graph import graph
from state import ChatState, Intent, SessionManager
from config import DOCTOR_PROFILES

load_dotenv()

print("=" * 80)
print("Test: New Patient Booking (NOT in database)")
print("=" * 80)
print("\nScenario: Patient ID P999 does NOT exist in database")
print("Expected: Create appointment + add-patient ticket\n")

session = SessionManager.create_session("New Patient Test")

# ============================================================================
# MESSAGE 1: User provides booking details with NON-EXISTENT patient ID
# ============================================================================
print("[MESSAGE 1] New patient provides booking details")
print("-" * 80)

user_msg1 = "I need ophthalmologist tomorrow for eye exam. My name is John Smith. Email: john.smith@test.com. Patient ID: P999. At 2:30 PM"

print(f'User: "{user_msg1}"\n')

session.chat_history.append({"role": "user", "content": user_msg1})
session.conversation_history.append({"role": "user", "content": user_msg1})

state1 = ChatState(
    user_input=user_msg1,
    messages=session.chat_history,
    conversation_history=session.conversation_history,
    available_doctors=list(DOCTOR_PROFILES.keys())
)

print("[INVOKING GRAPH]")
result1 = graph.invoke(state1)

print(f"\nResult 1:")
print(f"  Patient ID: {result1.get('patient_id')}")
print(f"  Patient not found: {result1.get('patient_not_found')}")
print(f"  Confirmation ready: {result1.get('appointment_ready_for_confirmation')}")
print(f"  Date: {result1.get('extracted_info', {}).get('appointment_date')}")
print(f"  Time: {result1.get('extracted_info', {}).get('appointment_time')}")

response1 = result1.get('last_response', '')[:250]
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
    "should_add_patient": result1.get("should_add_patient", False),
}

# ============================================================================
# MESSAGE 2: User confirms booking
# ============================================================================
if booking_state.get("appointment_ready_for_confirmation"):
    print("[MESSAGE 2] User confirms booking")
    print("-" * 80)

    user_msg2 = "Yes, approve this booking"
    print(f'User: "{user_msg2}"\n')

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
        should_add_patient=booking_state.get("should_add_patient", False),
    )

    print("[INVOKING GRAPH]")
    result2 = graph.invoke(state2)

    print(f"\nResult 2:")
    print(f"  Booking confirmed: {result2.get('booking_confirmed')}")
    print(f"  Patient: {result2.get('extracted_info', {}).get('patient_name')}")
    print(f"  Doctor: {result2.get('extracted_info', {}).get('doctor_name')}")
    print(f"  Date: {result2.get('extracted_info', {}).get('appointment_date')}")
    print(f"  Time: {result2.get('extracted_info', {}).get('appointment_time')}")

    response2 = result2.get('last_response', '')[:250]
    print(f"\nBot: {response2}...\n")

    # Final result
    print("=" * 80)
    if result2.get('booking_confirmed'):
        print("[SUCCESS] New patient booking confirmed!")
        print("\nWhat was created on Trello:")
        print("  1. Appointment Card on Appointments board")
        print(f"     - Patient: {result2.get('extracted_info', {}).get('patient_name')} (ID: {result2.get('patient_id')})")
        print(f"     - Doctor: {result2.get('extracted_info', {}).get('doctor_name')}")
        print(f"     - Date: {result2.get('extracted_info', {}).get('appointment_date')}")
        print(f"     - Time: {result2.get('extracted_info', {}).get('appointment_time')}")
        print("\n  2. Add Patient Ticket on Tickets board")
        print(f"     - Patient Name: John Smith")
        print(f"     - Email: john.smith@test.com")
        print(f"     - Requested ID: P999")
        print(f"     - Note: New patient booking for eye exam")
    else:
        print("[FAIL] Booking NOT confirmed")
else:
    print(f"\n[ERROR] Message 1 did not set confirmation flag")

print("=" * 80)
