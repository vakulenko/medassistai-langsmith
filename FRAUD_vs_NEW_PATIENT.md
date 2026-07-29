# Fraud Detection vs New Patient Handling

## Overview

The system distinguishes between two different scenarios using separate logic paths:

1. **DECEASED PATIENT** (fraud detection)
2. **NEW PATIENT** (not in database)

## Scenario 1: Deceased Patient

When a patient ID exists in the database AND patient is marked as deceased:

### What Happens
- `state.is_deceased_patient = True` (set by patient_validator.py)
- User provides booking details
- Bot asks for confirmation (normal flow)
- User approves
- **System creates FRAUD TICKET** (honeypot alert)
- **NO appointment card created**
- User sees success message (honeypot)

### Trello Tickets Created
- **FRAUD TICKET** on Tickets board
  - Title: `[FRAUD] Deceased patient`
  - Type: Deceased patient booking attempt
  - Patient ID: P004 (example)
  - Session ID: (for tracing)

### Code Path
**File:** `graph.py` - `create_appointment_on_trello()` (lines 79-92)

```python
if state.is_deceased_patient:
    create_fraud_card(...)  # Creates FRAUD ticket
    state.booking_confirmed = True  # Honeypot response
    return state  # EXIT - no appointment created
```

---

## Scenario 2: New Patient (Not in Database)

When a patient ID does NOT exist in the database:

### What Happens
- `state.patient_not_found = True` (set by patient_validator.py)
- User provides booking details (with non-existent patient ID)
- Bot detects patient not in registry
- Bot asks for confirmation
- User approves
- **System creates APPOINTMENT CARD** (actual booking)
- **System creates ADD PATIENT TICKET** (registration request)

### Trello Tickets Created
1. **APPOINTMENT CARD** on Appointments board
   - Title: `John Smith - Dr. Dalla McDer`
   - Date: 2026-07-31
   - Time: 2:30 PM
   - Reason: Eye exam
   - Email: john.smith@test.com

2. **ADD PATIENT TICKET** on Tickets board
   - Title: `[ADD PATIENT] John Smith`
   - Type: Patient registration request
   - Requested ID: P999
   - Email: john.smith@test.com
   - Notes: New patient booking for eye exam

### Code Path
**File:** `graph.py` - `create_appointment_on_trello()` (lines 94-128)

```python
# Normal booking: create appointment card
create_appointment_card(...)  # Creates appointment

# If patient not found in system, create add-patient card as well
if state.patient_not_found:
    create_add_patient_card(...)  # Creates registration ticket
```

---

## Key Differences

| Aspect | Deceased Patient | New Patient |
|--------|-----------------|-------------|
| **Patient in DB?** | Yes (but deceased) | No |
| **Appointment Card** | ❌ No | ✅ Yes |
| **Fraud Ticket** | ✅ Yes (Honeypot) | ❌ No |
| **Registration Ticket** | ❌ No | ✅ Yes |
| **User Sees** | Success (Honeypot) | Appointment confirmation |
| **Admin Sees** | Fraud alert | Appointment + patient reg |

---

## Testing

Run the verification test:
```bash
python test_fraud_vs_new_patient.py
```

This test verifies:
- Deceased patients create ONLY fraud tickets
- New patients create BOTH appointment AND registration tickets
- Logic is properly separated with no cross-contamination

---

## Summary

✅ **CORRECT IMPLEMENTATION**

- **Fraud detection**: Isolated for deceased patients, creates honeypot ticket only
- **New patient handling**: Creates actual appointment + registration ticket
- **Logic separation**: Two completely separate code paths, no overlap
