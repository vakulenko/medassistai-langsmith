# Multi-Node Multi-Agent Graph Architecture

## Graph Structure

The application now uses a **multi-node LangGraph** where each agent is represented as a separate node:

```
start
  ↓
intent_detection ──────────────────────────────────────────┐
  ↓                                                          │
extraction                                                   │
  ↓                                                          │
fraud_detection ──────────────────────────────────────────┐ │
  ↓                                                        │ │
[should_route_to_validation?]                             │ │
  ├─ YES → patient_validation ──────────────────────────┐ │ │
  │         ↓                                           │ │ │
  └─ NO ─────────────────────────────────────────────┐ │ │ │
                                                     ↓ ↓ ↓ │
                                              set_flags ──┘ │
                                                 ↓           │
                                        response_generation ┘
                                                 ↓
                                        [should_continue?]
                                         ├─ ask_for_info → end
                                         ├─ ask_for_confirmation → confirmation_validation
                                         └─ end → end

                        confirmation_validation
                              ↓
                       [handle_confirmation?]
                         ├─ create_appointment → end
                         ├─ reject_booking → end
                         └─ end → end
```

## Nodes Overview

### 1. intent_detection
**Agent**: IntentDetectionAgent  
**Function**: `intent_detection_node(state: ChatState) -> ChatState`  
**Responsibility**: Analyze user input to determine intent

**Input**:
- `user_input` - Current user message
- `conversation_history` - Previous messages for context

**Output**:
- `detected_intent` - One of: BOOK_APPOINTMENT, VIEW_DOCTORS, CHECK_AVAILABILITY, CANCEL_APPOINTMENT, GENERAL_INFO, UNKNOWN

**Downstream**: Always routes to `extraction`

---

### 2. extraction
**Agent**: ExtractionAgent  
**Function**: `extraction_node(state: ChatState) -> ChatState`  
**Responsibility**: Extract structured appointment data

**Input**:
- `user_input` - Current message
- `conversation_history` - For context

**Output**:
- `extracted_info` - Dictionary with:
  - `patient_id` - Patient identifier
  - `patient_name` - Patient full name
  - `patient_email` - Patient email
  - `doctor_name` - Preferred doctor
  - `appointment_date` - Date (YYYY-MM-DD)
  - `appointment_time` - Time (HH:MM)
  - `reason` - Reason for appointment
  - `specialization` - Medical specialty

**Downstream**: Always routes to `fraud_detection`

---

### 3. fraud_detection
**Agent**: FraudDetectionAgent  
**Function**: `fraud_detection_node(state: ChatState) -> ChatState`  
**Responsibility**: Detect suspicious patterns in booking requests

**Input**:
- `extracted_info` - Extracted appointment data

**Output**:
- `fraud_score` - Confidence level (0-1)
- Creates Trello fraud cards if needed

**Downstream**: Conditional routes based on `detected_intent`
- If `BOOK_APPOINTMENT` → `patient_validation`
- Otherwise → `set_flags`

---

### 4. patient_validation (Conditional)
**Agent**: PatientValidationAgent  
**Function**: `patient_validation_node(state: ChatState) -> ChatState`  
**Responsibility**: Validate patient data and check doctor availability

**Input**:
- `patient_id` - Patient to validate
- `extracted_info` - Appointment details
- `detected_intent` - Must be BOOK_APPOINTMENT

**Output**:
- `patient_not_found` - Is patient new?
- `is_deceased_patient` - Fraud flag
- `has_available_doctor` - Doctor available?
- `requested_specialization` - Specialty requested
- Updates `extracted_info` with auto-assigned doctor

**Uses**: RAG vector database for lookups

**Downstream**: Always routes to `set_flags`

**Condition**: Only runs if `detected_intent == BOOK_APPOINTMENT`

---

### 5. set_flags
**Function**: `set_confirmation_flags(state: ChatState) -> ChatState`  
**Responsibility**: Determine if ready for confirmation

**Input**:
- `detected_intent` - Intent from intent_detection
- `extracted_info` - Data from extraction
- `patient_id` - Patient identifier
- `patient_not_found` - New patient?
- `is_deceased_patient` - Fraud flag

**Output**:
- `appointment_ready_for_confirmation` - Boolean flag

**Logic**:
```
IF appointment_ready_for_confirmation already true:
    return

IF intent == BOOK_APPOINTMENT:
    IF is_deceased_patient:
        appointment_ready_for_confirmation = true
    
    IF patient_not_found AND has (patient_name + patient_email):
        appointment_ready_for_confirmation = true
    
    IF patient_id AND all required fields present:
        appointment_ready_for_confirmation = true
```

**Downstream**: Always routes to `response_generation`

---

### 6. response_generation
**Agent**: ResponseGenerationAgent  
**Function**: `response_generation_node(state: ChatState) -> ChatState`  
**Responsibility**: Generate user-facing response

**Input**:
- `detected_intent` - What the user wants
- `extracted_info` - Appointment details
- `conversation_history` - Context
- Patient flags and availability

**Output**:
- `last_response` - Message to send user

**Responses**:
- **Booking intent**: Detailed prompt with patient/appointment context
- **Patient not found**: Special prompt confirming new patient registration
- **General intent**: Info about services and doctors

**Uses**: RAG context for doctor/patient information

**Downstream**: Conditional routes based on `should_continue()`
- If `ask_for_info` → `ask_for_info` (END)
- If `ask_for_confirmation` → `ask_for_confirmation`
- If END → END

---

### 7. ask_for_info
**Function**: `lambda state: state` (passthrough)  
**Responsibility**: Present response requesting more information

**Input**: State with `last_response` set

**Output**: Same state

**Downstream**: Always routes to END

---

### 8. ask_for_confirmation
**Function**: `lambda state: state` (passthrough)  
**Responsibility**: Present response asking for confirmation

**Input**: State with confirmation prompt in `last_response`

**Output**: Same state

**Downstream**: Routes to `confirmation_validation`

---

### 9. confirmation_validation
**Agent**: ConfirmationValidationAgent  
**Function**: `confirmation_validation_node(state: ChatState) -> ChatState`  
**Responsibility**: Interpret user confirmation response

**Input**:
- `user_input` - User's response
- `extracted_info` - Appointment details

**Output**:
- `booking_confirmed` - Boolean flag

**Logic**:
```
IF user_input contains ("yes", "approve", "confirm", "agree", "ok", "go ahead"):
    booking_confirmed = true
ELSE IF user_input contains ("no", "cancel", "decline", "reject", "stop"):
    booking_confirmed = false
ELSE:
    booking_confirmed = false (unclear)
```

**Downstream**: Conditional routes based on `handle_confirmation()`
- If confirmed → `create_appointment`
- If rejected → `reject_booking`
- If unclear → END

---

### 10. create_appointment
**Function**: `appointment_creation_node(state: ChatState) -> ChatState`  
**Responsibility**: Create appointment card on Trello

**Input**:
- `extracted_info` - Appointment details
- `patient_id` - Patient identifier
- `is_deceased_patient` - Fraud flag
- `patient_not_found` - New patient?

**Output**:
- `booking_confirmed` - Set to true
- Creates Trello cards:
  - Appointment card with all details
  - Fraud card if deceased patient
  - Add-patient card if new patient

**Downstream**: Always routes to END

---

### 11. reject_booking
**Function**: `reject_booking(state: ChatState) -> ChatState`  
**Responsibility**: Handle booking rejection

**Input**: State with rejected confirmation

**Output**:
- `last_response` - "Booking cancelled..." message

**Downstream**: Always routes to END

---

## Routing Decisions

### Conditional Route 1: fraud_detection → patient_validation OR set_flags

**Function**: `should_route_to_validation(state: ChatState) -> bool`

**Decision**: Is intent BOOK_APPOINTMENT?
- `True` → patient_validation
- `False` → set_flags

**Logic**:
```python
return state.detected_intent == Intent.BOOK_APPOINTMENT
```

---

### Conditional Route 2: response_generation → ask_for_info OR ask_for_confirmation OR END

**Function**: `should_continue(state: ChatState) -> str`

**Decisions**:
1. If `appointment_ready_for_confirmation` → "ask_for_confirmation"
2. If intent is BOOK_APPOINTMENT:
   - If specialization not available → END
   - If missing patient_id → "ask_for_info"
   - If patient not found but has name+email → "ask_for_confirmation"
   - If missing required fields → "ask_for_info"
   - If all fields present → "ask_for_confirmation"
3. Otherwise → END

---

### Conditional Route 3: confirmation_validation → create_appointment OR reject_booking OR END

**Function**: `handle_confirmation(state: ChatState) -> str`

**Decisions**:
1. If confirmed (yes/approve/confirm/ok) → "create_appointment"
2. If rejected (no/cancel/decline) → "reject_booking"
3. Otherwise (unclear) → END

---

## Data Flow Example: Complete Booking

```
User: "Book ophthalmology appointment, ID P001, John Smith, john@email.com, tomorrow 2pm"

intent_detection:
  INPUT: user_input="Book ophthalmology appointment..."
  OUTPUT: detected_intent=BOOK_APPOINTMENT
  
extraction:
  INPUT: user_input (same)
  OUTPUT: extracted_info={
    patient_id: "P001",
    patient_name: "John Smith",
    patient_email: "john@email.com",
    specialization: "ophthalmology",
    appointment_date: "2026-08-01",
    appointment_time: "14:00"
  }

fraud_detection:
  INPUT: extracted_info
  OUTPUT: fraud_score=0 (no fraud)

should_route_to_validation:
  INPUT: detected_intent=BOOK_APPOINTMENT
  OUTPUT: true → route to patient_validation

patient_validation:
  INPUT: patient_id="P001", specialization="ophthalmology"
  OUTPUT: 
    patient_not_found=false
    is_deceased_patient=false
    has_available_doctor=true
    requested_specialization="ophthalmology"
    extracted_info["doctor_name"]="Dr. Dalla McDer"

set_flags:
  INPUT: All info present
  OUTPUT: appointment_ready_for_confirmation=true

response_generation:
  INPUT: extracted_info (full), state flags
  OUTPUT: last_response="Please confirm appointment with 
                         Dr. Dalla McDer on 2026-08-01 at 14:00?"

should_continue:
  INPUT: appointment_ready_for_confirmation=true
  OUTPUT: "ask_for_confirmation" → route to ask_for_confirmation

ask_for_confirmation:
  INPUT: state with prompt
  OUTPUT: same state (passthrough)
  Routes to: confirmation_validation

---

User: "Yes, confirm"

confirmation_validation:
  INPUT: user_input="Yes, confirm"
  OUTPUT: booking_confirmed=true

handle_confirmation:
  INPUT: booking_confirmed=true
  OUTPUT: "create_appointment" → route to create_appointment

create_appointment:
  INPUT: extracted_info, patient_id, flags
  OUTPUT: Creates Trello appointment card
  Routes to: END
```

## LangSmith Visualization

The graph now displays in LangSmith with separate nodes:

```
__start__
    ↓
intent_detection
    ↓
extraction
    ↓
fraud_detection
    ├─ (conditional) ──→ patient_validation
    │                         ↓
    └─ (skip validation) ────→ set_flags
                                ↓
                        response_generation
                                ↓
                        [conditional routing]
                                ├─ ask_for_info → __end__
                                ├─ ask_for_confirmation → confirmation_validation
                                └─ __end__
                                
                        confirmation_validation
                                ├─ create_appointment → __end__
                                ├─ reject_booking → __end__
                                └─ __end__
```

## Key Features

### Explicit Nodes
Each agent is a visible node in LangSmith:
- intent_detection
- extraction
- fraud_detection
- patient_validation
- response_generation
- confirmation_validation

### Conditional Routing
Smart routing based on:
- Intent type (booking vs general)
- Confirmation readiness
- User response interpretation

### Backward Compatible
- Same state structure
- Same output format
- Same integration points
- Works with existing UI

### Traceable
Each node has `@traceable` decorator for LangSmith visibility.

---

## Execution Modes

### Mode 1: General Information Request
```
User: "What doctors do you have?"

intent_detection (GENERAL_INFO)
  ↓
extraction (no data)
  ↓
fraud_detection (no fraud)
  ↓
[skip patient_validation]
  ↓
set_flags (no confirmation)
  ↓
response_generation (info response)
  ↓
END (ask_for_info → END)
```

### Mode 2: Incomplete Booking Request
```
User: "I want to book an appointment"

intent_detection (BOOK_APPOINTMENT)
  ↓
extraction (no specifics)
  ↓
fraud_detection (no fraud)
  ↓
patient_validation (no patient_id)
  ↓
set_flags (not ready)
  ↓
response_generation (ask for more info)
  ↓
END (ask_for_info → END)
```

### Mode 3: Complete Booking Request
```
User: "Book with Dr. X, ID P001, tomorrow 2pm"

intent_detection (BOOK_APPOINTMENT)
  ↓
extraction (full data)
  ↓
fraud_detection (no fraud)
  ↓
patient_validation (patient valid, doctor available)
  ↓
set_flags (ready for confirmation)
  ↓
response_generation (confirmation prompt)
  ↓
ask_for_confirmation
  ↓
[awaits user response]
```

### Mode 4: Confirmation Response
```
User: "Yes, confirm"

[Same flow as above until...]
  ↓
confirmation_validation (yes detected)
  ↓
create_appointment (creates Trello card)
  ↓
END (success)
```

---

## Benefits of Multi-Node Architecture

✅ **Visible in LangSmith** - Each agent shows as separate node  
✅ **Traceable** - LangSmith traces each node execution  
✅ **Debuggable** - Can inspect individual node inputs/outputs  
✅ **Modular** - Each node is independent  
✅ **Extensible** - Easy to add new nodes  
✅ **Testable** - Can test individual nodes  
✅ **Maintainable** - Clear node responsibility  
✅ **Monitorable** - Performance per node  

---

## Summary

The graph now features:
- **11 nodes** representing different workflow stages
- **6 agent nodes** (one per agent class)
- **3 passthrough nodes** (ask_for_info, ask_for_confirmation, state setters)
- **2 conditional edges** for intelligent routing
- Full **LangSmith visibility** of each node
- 100% **backward compatible** with existing code
