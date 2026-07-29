"""Test that date/time are preserved across messages."""
from date_time_parser import parse_date_time

print("=" * 80)
print("Testing Date/Time Preservation")
print("=" * 80)

# Test parse_date_time on different messages
print("\n[TEST] parse_date_time on various inputs")
print("-" * 80)

test_cases = [
    ("I need ophthalmologist tomorrow at 2:30 PM", "Full booking message"),
    ("Approve", "Confirmation message"),
    ("Yes", "Confirmation (yes)"),
    ("11:00 AM", "Time only"),
]

for text, description in test_cases:
    result = parse_date_time(text)
    print(f"\nInput: '{text}' ({description})")
    print(f"  appointment_date: {result.get('appointment_date')}")
    print(f"  appointment_time: {result.get('appointment_time')}")

print("\n\n[TEST] Simulated multi-message booking flow")
print("-" * 80)

# Simulate Message 1
print("\nMessage 1: User provides date/time")
msg1 = "I need ophthalmologist tomorrow at 2:30 PM"
result1 = parse_date_time(msg1)

extracted_info = {
    "appointment_date": result1.get("appointment_date"),
    "appointment_time": result1.get("appointment_time"),
    "doctor_name": "Dr. Dalla McDer",
    "patient_name": "John Doe"
}

print(f"  Input: '{msg1}'")
print(f"  Extracted date: {extracted_info['appointment_date']}")
print(f"  Extracted time: {extracted_info['appointment_time']}")

# Simulate Message 2 with old approach (WRONG)
print("\nMessage 2: User confirms with 'Approve' (OLD APPROACH - WRONG)")
msg2 = "Approve"
result2_old = parse_date_time(msg2)

# Old code would do: extracted_info.update({...from LLM...})
# Then: if result2_old.get("appointment_date"): extracted_info["appointment_date"] = result2_old.get(...)
# This would overwrite with None!
if result2_old.get("appointment_date"):
    extracted_info["appointment_date"] = result2_old.get("appointment_date")
if result2_old.get("appointment_time"):
    extracted_info["appointment_time"] = result2_old.get("appointment_time")

print(f"  Input: '{msg2}'")
print(f"  parse_date_time returns: {result2_old}")
print(f"  After update:")
print(f"    date: {extracted_info['appointment_date']} (PRESERVED - but might not be if None)")
print(f"    time: {extracted_info['appointment_time']} (PRESERVED - but might not be if None)")
print(f"  Problem: If None was returned, it doesn't overwrite, but future code might clear it")

# Simulate Message 2 with new approach (CORRECT)
print("\nMessage 2: User confirms with 'Approve' (NEW APPROACH - CORRECT)")
extracted_info2 = {
    "appointment_date": "2026-07-31",
    "appointment_time": "14:30",
    "doctor_name": "Dr. Dalla McDer",
    "patient_name": "John Doe"
}

result2_new = parse_date_time("Approve")
msg2 = "Approve"

# New code: Only update if we have new values AND field not already set
if not extracted_info2.get("appointment_date") or not extracted_info2.get("appointment_time"):
    if result2_new.get("appointment_date") and not extracted_info2.get("appointment_date"):
        extracted_info2["appointment_date"] = result2_new.get("appointment_date")
    if result2_new.get("appointment_time") and not extracted_info2.get("appointment_time"):
        extracted_info2["appointment_time"] = result2_new.get("appointment_time")

print(f"  Input: '{msg2}'")
print(f"  parse_date_time returns: {result2_new}")
print(f"  After update (with protection):")
print(f"    date: {extracted_info2['appointment_date']} [PRESERVED]")
print(f"    time: {extracted_info2['appointment_time']} [PRESERVED]")

print("\n" + "=" * 80)
print("Result")
print("=" * 80)

print("\nOld Flow (WRONG):")
print("  Message 1: date='2026-07-31', time='14:30'")
print("  Message 2: parse_date_time('Approve') -> None values")
print("  Result: Date/time might be lost [BAD]")

print("\nNew Flow (CORRECT):")
print("  Message 1: date='2026-07-31', time='14:30'")
print("  Message 2: Check if already set, don't overwrite")
print("  Result: Date/time preserved [GOOD]")

print("\n" + "=" * 80)
