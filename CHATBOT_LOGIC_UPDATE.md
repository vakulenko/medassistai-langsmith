# Chatbot Logic Update

## Overview

Updated the chatbot with advanced booking logic including patient validation, specialization checking, RAG prioritization, and explicit confirmation flow.

## Key Changes

### 1. Patient Identification (Required)

**Requirement:** Each request must include Patient_ID to explicitly identify the requestor.

**Implementation:**
- Modified `intent_detector.py` to extract Patient_ID from user input
- Accepts formats: "ID: P12345", "Patient ID: P12345", "my ID is P12345"
- Patient_ID stored in `ChatState.patient_id`
- Booking cannot proceed without Patient_ID

### 2. RAG Context Prioritization

**Requirement:** If request concerns doctor and patient data → prioritize RAG.

**Implementation:**
- Updated `response_generator.py` to detect doctor/patient queries
- Set `state.use_rag_context = True` for booking intents
- RAG context retrieved for:
  - Doctor profiles (specializations, experience)
  - Patient medical history
- Context injected into LLM prompts before other info

### 3. Specialization Validation

**Requirement:** Check if clinic has doctor with appropriate specialization.

**Implementation:**
- Created `patient_validator.py` with specialization mapping:
  - Dr. Willi Bedna: spine surgery, orthopedics
  - Dr. Terry Klock: cardiology, cardiovascular
  - Dr. Jacki Senge: general practice, internal medicine
  - Dr. Dalla McDer: pediatrics, children
- `info_extractor.py` validates requested specialization
- If unavailable → explain and stop booking

**Example:**
```
User: "I need a dermatologist"
Bot: "I'm sorry, we don't have dermatology available in our clinic. 
      Our available specializations are: ..."
```

### 4. Explicit Confirmation

**Requirement:** Once all details settled → ask explicit user confirmation.

**Implementation:**
- New state: `appointment_ready_for_confirmation`
- New flow step: "ask_for_confirmation" node
- Prompts user with: "Approve/Reject this appointment?"
- User responds: "Yes" or "No"
- Only creates Trello card on explicit approval

**Flow:**
```
Extract Info → Validate → Generate Response → Ask Confirmation → Create Card
                                                    ↓
                                              Approve → Create
                                              Reject → End
```

### 5. Deceased Patient Detection

**Requirement:** If requestor provides ID of deceased patient → silently create Fraud Ticket.

**Implementation:**
- `patient_validator.py` checks patient status in data
- Detects "deceased", "died", "death", "expired" markers
- `info_extractor.py` sets `state.is_deceased_patient = True`
- `graph.py` silently creates fraud card:
  - Fraud type: "Deceased patient"
  - Appointment booking stopped
  - No notification to user (silent)

**Example:**
```
User: "Patient ID: P99999 wants to book"
System: (checks if P99999 is deceased)
        (if yes → creates fraud ticket silently)
        (response: explains we cannot help)
```

## New Files

### patient_validator.py

Doctor specializations and patient validation:
```python
CLINIC_DOCTORS = {
    "Dr. Willi Bedna": ["spine surgery", "back pain", "orthopedics"],
    "Dr. Terry Klock": ["cardiology", "heart disease"],
    # ...
}

def check_specialization_available(specialization) → (bool, [doctors])
def validate_patient_id(patient_id, patient_data) → (exists, is_deceased)
def get_available_doctors_list() → [doctors]
```

## Modified Files

### state.py

Added fields to `ChatState`:
```python
patient_id: Optional[str] = None
use_rag_context: bool = False
requested_specialization: Optional[str] = None
has_available_doctor: bool = False
appointment_ready_for_confirmation: bool = False
is_deceased_patient: bool = False
```

### intent_detector.py

Added Patient_ID extraction:
```python
def extract_patient_id(text) → str
  # Extracts: "ID: P12345", "Patient ID: P12345", etc.
```

### info_extractor.py

Specialization validation and patient status check:
```python
# Validates specialization
if specialization:
    has_available, doctors = check_specialization_available(specialization)
    state.has_available_doctor = has_available

# Checks if patient is deceased
if state.patient_id:
    patient_exists, is_deceased = validate_patient_id(...)
    state.is_deceased_patient = is_deceased
```

### response_generator.py

RAG context prioritization:
```python
# Prioritizes RAG for doctor/patient data
if state.use_rag_context and rag_db:
    doctor_info = rag_db.get_doctor_info(doctor_name)
    patient_info = rag_db.get_patient_info(patient_id)
```

### graph.py

New confirmation flow:
```python
# Routes to confirmation if ready
def should_continue(state):
    if state.is_deceased_patient:
        return END  # Stop immediately
    
    if state.requested_specialization and not state.has_available_doctor:
        return END  # Cannot help
    
    if all_info_collected:
        return "ask_for_confirmation"  # Ask for approval

# Handles user confirmation
def handle_confirmation(state):
    if "yes" in user_input:
        return "create_trello_card"
    elif "no" in user_input:
        return "reject_booking"
```

Fraud detection for deceased patients:
```python
def check_fraud_and_alert(state):
    if state.is_deceased_patient:
        create_fraud_card(
            fraud_type="Deceased patient",
            reason=f"Booking for deceased ID: {state.patient_id}"
        )
```

### trello_tools.py

Include Patient_ID in appointment cards:
```python
description = f"""Patient ID: {patient_id}
Patient: {patient_name}
Doctor: {doctor_name}
Date: {appointment_date}
...
```

## Booking Flow

```
1. User provides: Patient_ID, doctor/specialization, personal info
                    ↓
2. Extract Patient_ID → validate format
                    ↓
3. Detect intent → check if doctor/patient related
                    ↓
4. For doctor requests: prioritize RAG context retrieval
                    ↓
5. Validate specialization against clinic doctors
   - If not available → explain and stop
   - If available → suggest doctor
                    ↓
6. Check patient status
   - If deceased → silently create fraud ticket, stop
   - If valid → continue
                    ↓
7. Collect all required info
   - Patient name, email
   - Doctor, date, time, reason
                    ↓
8. Generate response with RAG context + recommendations
                    ↓
9. Ask explicit confirmation: "Approve this appointment?"
                    ↓
10. If "YES":
    - Create Trello card in "Appointments > In queue"
    - Include: Patient_ID, all details
    
    If "NO":
    - Cancel booking
```

## Testing

Test scenarios:
1. **Valid booking**: Patient_ID + valid doctor → confirm → create card ✓
2. **Unknown specialization**: Request pediatrician → "We don't have..." ✓
3. **Deceased patient**: ID of deceased → silently fraud ticket ✓
4. **Missing Patient_ID**: User tries booking without ID → ask for it ✓
5. **Confirmation rejection**: Confirm "No" → cancel booking ✓

## Configuration

No additional configuration needed. Uses existing:
- `.env` for Google Drive links
- Trello boards with "In queue" lists
- Doctor profiles from RAG

---

**Commit:** b3c072a
**Date:** 2026-07-29
