"""Test that state is preserved across multiple messages in a session."""
from state import ChatState, Intent
from info_extractor import extract_info

print("=" * 80)
print("Testing State Preservation Across Messages")
print("=" * 80)

# Simulate a 3-message booking flow
print("\n[TEST] Multi-Message Booking Flow")
print("-" * 80)

# Message 1: User requests ophthalmologist, provides P001
print("\nMessage 1: User requests ophthalmologist")
print("Input: 'I need to see a ophthalmologist tomorrow. My Patient_ID: P001.'")

state1 = ChatState(
    user_input="I need to see a ophthalmologist tomorrow. My Patient_ID: P001.",
    detected_intent=Intent.BOOK_APPOINTMENT,
    conversation_history=[],
    extracted_info={},
)

# Note: In reality, intent_detector runs first, patient_id extraction happens there
state1.patient_id = "P001"

result1 = extract_info(state1)

print(f"\nAfter Message 1:")
print(f"  Patient ID: {result1.patient_id}")
print(f"  Patient not found: {result1.patient_not_found}")
print(f"  Requested specialization: {result1.requested_specialization}")
print(f"  Doctor suggested: {result1.extracted_info.get('doctor_name', 'None')}")
print(f"  Has available doctor: {result1.has_available_doctor}")

# Message 2: User provides time and reason (no specialization mentioned again)
print("\n\nMessage 2: User provides time and reason")
print("Input: '11:00 AM. Sight issue.'")

state2 = ChatState(
    user_input="11:00 AM. Sight issue.",
    detected_intent=Intent.BOOK_APPOINTMENT,
    conversation_history=[
        {"role": "user", "content": "I need to see a ophthalmologist tomorrow. My Patient_ID: P001."},
        {"role": "assistant", "content": "...booking details..."}
    ],
    extracted_info=result1.extracted_info,  # PRESERVE previous extraction
    patient_id=result1.patient_id,
    requested_specialization=result1.requested_specialization,
    has_available_doctor=result1.has_available_doctor,
    patient_not_found=result1.patient_not_found,
)

result2 = extract_info(state2)

print(f"\nAfter Message 2:")
print(f"  Patient ID: {result2.patient_id} [PRESERVED from Message 1]")
print(f"  Patient not found: {result2.patient_not_found} [PRESERVED from Message 1]")
print(f"  Requested specialization: {result2.requested_specialization} [PRESERVED from Message 1]")
print(f"  Doctor suggested: {result2.extracted_info.get('doctor_name', 'None')} [PRESERVED from Message 1]")
print(f"  Has available doctor: {result2.has_available_doctor} [PRESERVED from Message 1]")
print(f"  Time extracted: {result2.extracted_info.get('appointment_time', 'None')} [NEW]")
print(f"  Reason extracted: {result2.extracted_info.get('reason', 'None')} [NEW]")

# Message 3: User confirms
print("\n\nMessage 3: User confirms")
print("Input: 'Yes, approve.'")

state3 = ChatState(
    user_input="Yes, approve.",
    detected_intent=Intent.BOOK_APPOINTMENT,
    conversation_history=[
        {"role": "user", "content": "I need to see a ophthalmologist tomorrow. My Patient_ID: P001."},
        {"role": "assistant", "content": "...booking details..."},
        {"role": "user", "content": "11:00 AM. Sight issue."},
        {"role": "assistant", "content": "...confirmation request..."}
    ],
    extracted_info=result2.extracted_info,  # PRESERVE previous extraction
    patient_id=result2.patient_id,
    requested_specialization=result2.requested_specialization,
    has_available_doctor=result2.has_available_doctor,
    patient_not_found=result2.patient_not_found,
)

result3 = extract_info(state3)

print(f"\nAfter Message 3:")
print(f"  Patient ID: {result3.patient_id} [PRESERVED]")
print(f"  Patient not found: {result3.patient_not_found} [PRESERVED]")
print(f"  Requested specialization: {result3.requested_specialization} [PRESERVED]")
print(f"  Doctor suggested: {result3.extracted_info.get('doctor_name', 'None')} [PRESERVED]")
print(f"  Has available doctor: {result3.has_available_doctor} [PRESERVED]")
print(f"  All appointment details present: {all(result3.extracted_info.get(f) for f in ['patient_name', 'appointment_date', 'appointment_time', 'doctor_name', 'reason'])}")

print("\n" + "=" * 80)
print("Verification")
print("=" * 80)

print("\nExpected Behavior:")
print("  1. Message 1 detects: ophthalmologist specialization, P001 patient, Dr. Dalla McDer")
print("  2. Message 2 adds: time (11:00 AM), reason (sight issue)")
print("  3. Message 3 confirms: all details consistent, no contradictions")

print("\nActual Behavior:")
if (result1.requested_specialization == "ophthalmologist" and
    result2.requested_specialization == "ophthalmologist" and
    result3.requested_specialization == "ophthalmologist" and
    result1.patient_id == "P001" and
    result2.patient_id == "P001" and
    result3.patient_id == "P001" and
    result1.has_available_doctor and
    result2.has_available_doctor and
    result3.has_available_doctor):
    print("  [PASS] All state preserved correctly across messages")
else:
    print("  [FAIL] State not preserved properly")

print("\n" + "=" * 80)
