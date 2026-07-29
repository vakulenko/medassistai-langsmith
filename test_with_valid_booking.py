"""Test with a complete valid booking that should create a Trello card."""
import os
from dotenv import load_dotenv
from graph import graph
from state import ChatState, Intent, SessionManager
from config import DOCTOR_PROFILES

load_dotenv()

print("=" * 80)
print("Complete Valid Booking - Should Create Trello Card")
print("=" * 80)

# Initialize session
session = SessionManager.create_session("Test Booking")

# ============================================================================
# MESSAGE 1: User provides all details needed for confirmation
# ============================================================================
print("\n[MESSAGE 1] User provides all booking details")
print("-" * 80)

# Use a doctor we know exists and a valid specialization
user_msg1 = "My name is Jane Smith. I want to book Dr. Willi Bedna for an eye exam tomorrow at 10:30 AM. My email is jane@test.com and my patient ID is P002."

print(f"Input: {user_msg1}\n")

session.chat_history.append({"role": "user", "content": user_msg1})
session.conversation_history.append({"role": "user", "content": user_msg1})

state1 = ChatState(
    user_input=user_msg1,
    messages=session.chat_history,
    conversation_history=session.conversation_history,
    available_doctors=list(DOCTOR_PROFILES.keys())
)

print(f"[INVOKING GRAPH]")
result1 = graph.invoke(state1)

print(f"\nResult 1:")
print(f"  Intent: {result1.get('detected_intent')}")
print(f"  Patient ID: {result1.get('patient_id')}")
print(f"  Doctor: {result1.get('extracted_info', {}).get('doctor_name')}")
print(f"  Date: {result1.get('extracted_info', {}).get('appointment_date')}")
print(f"  Time: {result1.get('extracted_info', {}).get('appointment_time')}")
print(f"  Confirmation ready: {result1.get('appointment_ready_for_confirmation')}")
print(f"  Booking confirmed: {result1.get('booking_confirmed')}")
print(f"  Has available doctor: {result1.get('has_available_doctor')}")
print(f"  Specialization: {result1.get('requested_specialization')}")

response1 = result1.get('last_response', '')
print(f"\nBot says (first 300 chars):")
print(f"  {response1[:300]}...\n")

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
print("\n[MESSAGE 2] User confirms booking")
print("-" * 80)

user_msg2 = "Yes, I approve this booking"
print(f"Input: {user_msg2}\n")

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

print(f"[INVOKING GRAPH]")
print(f"State before:")
print(f"  appointment_ready_for_confirmation: {state2.appointment_ready_for_confirmation}")
print(f"  extracted_info keys: {list(state2.extracted_info.keys())}")
print()

result2 = graph.invoke(state2)

print(f"\nResult 2:")
print(f"  Booking confirmed: {result2.get('booking_confirmed')}")
print(f"  Patient: {result2.get('extracted_info', {}).get('patient_name')}")
print(f"  Doctor: {result2.get('extracted_info', {}).get('doctor_name')}")
print(f"  Date: {result2.get('extracted_info', {}).get('appointment_date')}")
print(f"  Time: {result2.get('extracted_info', {}).get('appointment_time')}")

response2 = result2.get('last_response', '')
print(f"\nBot says (first 300 chars):")
print(f"  {response2[:300]}...\n")

# ============================================================================
# RESULT
# ============================================================================
print("=" * 80)
if result2.get('booking_confirmed'):
    print("[SUCCESS] Booking confirmed! Trello card should have been created.")
else:
    print("[FAIL] Booking not confirmed.")
print("=" * 80)
