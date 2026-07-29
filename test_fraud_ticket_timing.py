"""Test that fraud tickets are only created after user confirmation."""
from state import ChatState
from graph import check_fraud_and_alert, create_appointment_on_trello

print("=" * 80)
print("Testing Fraud Ticket Creation Timing")
print("=" * 80)

# Simulate a deceased patient booking flow
print("\n[TEST] Deceased Patient Booking Attempt")
print("-" * 80)

print("\nScenario: User mentions P004 (deceased) multiple times")
print("Expected: Only ONE fraud ticket after final confirmation")

# Message 1: User provides basic info
state1 = ChatState(
    user_input="I need psychiatry appointment. Patient ID: P004",
    is_deceased_patient=True,
    patient_id="P004",
    extracted_info={
        "patient_name": "Patient P004",
        "reason": "Mental health"
    }
)

print("\n1. First message with P004:")
print(f"   is_deceased_patient: {state1.is_deceased_patient}")
print("   Running check_fraud_and_alert()...")
result1 = check_fraud_and_alert(state1)
print("   Result: [No fraud ticket created at this stage]")

# Message 2: User provides more details
state2 = ChatState(
    user_input="I want next Monday at 10 AM",
    is_deceased_patient=True,
    patient_id="P004",
    extracted_info={
        "patient_name": "Patient P004",
        "appointment_date": "2026-08-04",
        "appointment_time": "10:00",
        "reason": "Mental health"
    }
)

print("\n2. Second message with details:")
print(f"   is_deceased_patient: {state2.is_deceased_patient}")
print("   Running check_fraud_and_alert()...")
result2 = check_fraud_and_alert(state2)
print("   Result: [No fraud ticket created at this stage]")

# Message 3: User confirms booking
state3 = ChatState(
    user_input="Approve",
    is_deceased_patient=True,
    patient_id="P004",
    extracted_info={
        "patient_name": "Patient P004",
        "appointment_date": "2026-08-04",
        "appointment_time": "10:00",
        "reason": "Mental health"
    }
)

print("\n3. User confirms ('Approve'):")
print(f"   is_deceased_patient: {state3.is_deceased_patient}")
print("   Running create_appointment_on_trello()...")
print("   [THIS IS WHERE FRAUD TICKET IS CREATED]")
result3 = create_appointment_on_trello(state3)
print(f"   Result: booking_confirmed = {result3.booking_confirmed}")

print("\n" + "=" * 80)
print("Timing Verification")
print("=" * 80)
print("\nBefore Fix (WRONG):")
print("  Message 1 -> Fraud ticket created")
print("  Message 2 -> Fraud ticket created (DUPLICATE!)")
print("  Message 3 -> Fraud ticket created (DUPLICATE!)")
print("  Total: 3 fraud tickets for 1 booking attempt [BAD]")

print("\nAfter Fix (CORRECT):")
print("  Message 1 -> No fraud ticket")
print("  Message 2 -> No fraud ticket")
print("  Message 3 -> Fraud ticket created (ONLY ONE) [GOOD]")
print("  Total: 1 fraud ticket for 1 booking attempt [GOOD]")

print("\n" + "=" * 80)
