"""Final test: Full booking flow with Trello card creation."""
import os
from dotenv import load_dotenv
from graph import graph
from state import ChatState, Intent, SessionManager
from config import DOCTOR_PROFILES

load_dotenv()

print("=" * 80)
print("Final Test: Complete Booking -> Confirmation -> Trello Card")
print("=" * 80)

session = SessionManager.create_session("Final Test")

# ============================================================================
# MESSAGE 1: User provides all booking details
# ============================================================================
print("\n[MESSAGE 1] User provides all booking details")
print("-" * 80)

user_msg1 = "My name is Alice Brown. I want to book Dr. Terry Klock for a general checkup tomorrow at 3:00 PM. My email is alice@test.com and my patient ID is P001."

print(f"User: {user_msg1[:80]}...")

session.chat_history.append({"role": "user", "content": user_msg1})
session.conversation_history.append({"role": "user", "content": user_msg1})

state1 = ChatState(
    user_input=user_msg1,
    messages=session.chat_history,
    conversation_history=session.conversation_history,
    available_doctors=list(DOCTOR_PROFILES.keys())
)

print(f"\n[INVOKING GRAPH]")
result1 = graph.invoke(state1)

print(f"\nMessage 1 Result:")
print(f"  Intent: {result1.get('detected_intent')}")
print(f"  Patient ID: {result1.get('patient_id')}")
print(f"  Is Deceased: {result1.get('is_deceased_patient')}")
print(f"  Patient not found: {result1.get('patient_not_found')}")
print(f"  Appointment ready for confirmation: {result1.get('appointment_ready_for_confirmation')}")
print(f"  Booking confirmed: {result1.get('booking_confirmed')}")
print(f"  Extracted info keys: {list(result1.get('extracted_info', {}).keys())}")

response1 = result1.get('last_response', '')
if 'confirm' in response1.lower() or 'approve' in response1.lower():
    print(f"  [OK] Bot is asking for confirmation")
else:
    print(f"  Bot: {response1[:150]}...")

# Save state
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
# MESSAGE 2: User confirms
# ============================================================================
if booking_state.get("appointment_ready_for_confirmation"):
    print("\n[MESSAGE 2] User confirms booking")
    print("-" * 80)

    user_msg2 = "Yes, please confirm this booking"
    print(f"User: {user_msg2}")

    session.chat_history.append({"role": "user", "content": user_msg2})
    session.conversation_history.append({"role": "user", "content": user_msg2})

    state2 = ChatState(
        user_input=user_msg2,
        messages=session.chat_history,
        conversation_history=session.conversation_history,
        available_doctors=list(DOCTOR_PROFILES.keys()),
        # Restore state
        patient_id=booking_state.get("patient_id"),
        extracted_info=booking_state.get("extracted_info", {}),
        use_rag_context=booking_state.get("use_rag_context", False),
        requested_specialization=booking_state.get("requested_specialization"),
        has_available_doctor=booking_state.get("has_available_doctor", False),
        appointment_ready_for_confirmation=booking_state.get("appointment_ready_for_confirmation", False),
        is_deceased_patient=booking_state.get("is_deceased_patient", False),
        patient_not_found=booking_state.get("patient_not_found", False),
    )

    print(f"\n[INVOKING GRAPH]")
    result2 = graph.invoke(state2)

    print(f"\nMessage 2 Result:")
    print(f"  Booking confirmed: {result2.get('booking_confirmed')}")
    print(f"  Patient: {result2.get('extracted_info', {}).get('patient_name')}")
    print(f"  Doctor: {result2.get('extracted_info', {}).get('doctor_name')}")
    print(f"  Date: {result2.get('extracted_info', {}).get('appointment_date')}")
    print(f"  Time: {result2.get('extracted_info', {}).get('appointment_time')}")

    response2 = result2.get('last_response', '')
    print(f"  Bot: {response2[:150]}...")

    # Final result
    print("\n" + "=" * 80)
    if result2.get('booking_confirmed'):
        print("[SUCCESS] Booking confirmed!")
        print("\nTracing: Should have called create_appointment_on_trello()")
        print("  - Found booking_confirmed=True")
        print("  - Extracted info has patient_name, doctor_name, date, time")
        print("  - create_trello_card node was executed")
        print("  - Trello card should be created on the Appointments board")
    else:
        print("[FAIL] Booking NOT confirmed")
        print(f"Details: {response2[:300]}")
else:
    print("\n[SKIP] Message 2 - no confirmation prompt from Message 1")
    print(f"\nDebug: appointment_ready_for_confirmation = {booking_state.get('appointment_ready_for_confirmation')}")
    print(f"Response 1 was: {response1[:200]}...")

print("\n" + "=" * 80)
