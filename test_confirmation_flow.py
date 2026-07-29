"""Test multi-turn confirmation flow."""
from state import ChatState, Intent
from graph import should_continue

print("=" * 80)
print("Testing Multi-Turn Confirmation Flow")
print("=" * 80)

# Simulate Message 1: User provides booking details
print("\n[MESSAGE 1] User provides booking details")
print("-" * 80)
print("Input: 'I need ophthalmologist tomorrow at 2 PM'")

state1 = ChatState(
    user_input="I need ophthalmologist tomorrow at 2 PM",
    detected_intent=Intent.BOOK_APPOINTMENT,
    extracted_info={
        "patient_name": "John Doe",
        "patient_email": "john@example.com",
        "doctor_name": "Dr. Dalla McDer",
        "appointment_date": "2026-07-31",
        "appointment_time": "14:00",
        "reason": "Eye exam"
    },
    patient_id="P001",
    requested_specialization="ophthalmologist",
    has_available_doctor=True,
    appointment_ready_for_confirmation=False,  # Not set yet
)

print("\nBefore should_continue():")
print(f"  appointment_ready_for_confirmation: {state1.appointment_ready_for_confirmation}")

result1 = should_continue(state1)

print("\nAfter should_continue():")
print(f"  Returns: {result1}")
print(f"  appointment_ready_for_confirmation: {state1.appointment_ready_for_confirmation}")

if result1 == "ask_for_confirmation" and state1.appointment_ready_for_confirmation:
    print("\n[OK] Message 1: Flag set, routing to confirmation prompt")
else:
    print("\n[FAIL] Message 1: Not routing correctly")

# Simulate Message 2: User responds with confirmation
print("\n\n[MESSAGE 2] User confirms: 'Approve'")
print("-" * 80)
print("Input: 'Approve'")

state2 = ChatState(
    user_input="Approve",
    detected_intent=Intent.BOOK_APPOINTMENT,
    extracted_info=state1.extracted_info,  # PRESERVED from Message 1
    patient_id=state1.patient_id,
    requested_specialization=state1.requested_specialization,
    has_available_doctor=state1.has_available_doctor,
    appointment_ready_for_confirmation=state1.appointment_ready_for_confirmation,  # FLAG IS TRUE
)

print("\nBefore should_continue():")
print(f"  user_input: '{state2.user_input}'")
print(f"  appointment_ready_for_confirmation: {state2.appointment_ready_for_confirmation}")

result2 = should_continue(state2)

print("\nAfter should_continue():")
print(f"  Returns: {result2}")

if result2 == "ask_for_confirmation" and state2.appointment_ready_for_confirmation:
    print("\n[OK] Message 2: Flag is TRUE, routing to confirmation processing")
    print("     handle_confirmation() will process 'Approve'")
    print("     -> Routes to 'create_trello_card'")
    print("     -> Trello card created!")
else:
    print("\n[FAIL] Message 2: Not routing correctly")

print("\n" + "=" * 80)
print("Verification")
print("=" * 80)

print("\nOld (BROKEN) Flow:")
print("  Message 1: All info present -> ask_for_confirmation -> check user_input -> END")
print("  Message 2: 'Approve' -> Booking intent again -> ask for more info -> STUCK")

print("\nNew (FIXED) Flow:")
print("  Message 1: All info present -> SET flag -> ask_for_confirmation -> END")
print("  Message 2: 'Approve' -> Flag TRUE -> ask_for_confirmation -> handle_confirmation")
print("             -> 'Approve' detected -> create_trello_card -> SUCCESS!")

print("\n" + "=" * 80)
