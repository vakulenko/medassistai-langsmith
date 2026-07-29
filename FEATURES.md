# MedAssistAI Chatbot - New Features

## Feature 1: Patient Registration (New Patient Handling)

### When Triggered
- User provides a Patient ID during booking
- Patient ID is **NOT found** in the system patient database

### What Happens
1. **Booking continues normally** - appointment is scheduled as usual
2. **Appointment card created** on Trello (In Queue list)
3. **Add-Patient ticket created** on Trello (In Queue list, Tickets board)
4. System flags patient for manual addition to database

### User Experience
- User sees confirmation of appointment booking
- User unaware that patient needs to be added to system
- System admin later adds patient to database based on ticket

### Implementation
- `create_add_patient_card()` in `trello_tools.py`
- State field: `patient_not_found`, `should_add_patient`
- Validation happens in `info_extractor.py`

### Example Flow
```
User: "I need an eye appointment. Name: John Smith, ID: P999, email: john@test.com"
System: "Booking confirmed! Appointment scheduled."
[Backend: Creates appointment card + add-patient card for P999]
```

---

## Feature 2: Appointment Cancellation

### When Triggered
- User explicitly requests to cancel appointment
- User provides patient name or patient ID

### Normal Patient Cancellation
1. **Confirmation requested** - "Are you sure you want to cancel?"
2. **On approval (yes)**:
   - Cancellation card created on Trello
   - User sees: "Cancellation confirmed"
3. **On rejection (no)**:
   - Booking remains unchanged
   - User sees: "Cancellation cancelled"

### Deceased Patient Cancellation (Honeypot)
1. **Confirmation requested** - "Are you sure?"
2. **On approval (yes)**:
   - **NO cancellation card created**
   - **Request silently ignored**
   - User sees: "Cancellation confirmed" (honeypot)
3. **On rejection (no)**:
   - User sees: "Cancellation cancelled"

### Implementation
- `handle_cancellation_confirmation()` in `graph.py`
- `process_cancellation()` handles confirmed cancellations
- `cancel_appointment_card()` in `trello_tools.py`
- State field: `cancel_ready_for_confirmation`

### Example Flows

**Normal Patient:**
```
User: "I want to cancel my appointment. ID: P002"
System: "Please confirm you want to cancel. Reply YES or NO"
User: "YES"
System: "Cancellation confirmed. You will receive a confirmation email."
[Backend: Creates cancellation card, awaits manual processing]
```

**Deceased Patient:**
```
User: "Cancel appointment for P004"
System: "Please confirm you want to cancel. Reply YES or NO"
User: "YES"
System: "Cancellation confirmed." (HONEYPOT)
[Backend: Does NOTHING - ignores request silently]
[Fraud team: Could add fraud detection if suspicious pattern]
```

---

## State Management

### New Chat State Fields
- `patient_not_found: bool` - Patient ID not in system
- `should_add_patient: bool` - Flag to create add-patient card
- `cancel_ready_for_confirmation: bool` - Waiting for cancellation confirmation

### State Persistence
- All new fields stored in `st.session_state.booking_state`
- Survives across conversation messages
- Restored on each user input

---

## Security Considerations

### Patient Registration
- Legitimate new patients can be added to system
- Admin approval workflow (Trello ticket)
- Prevents account takeover (must match email domain if configured)

### Cancellation Honeypot
- Deceased patient cancellation requests ignored
- Fraudsters believe they succeeded
- No indication given that request was rejected
- Cancellation card NOT created (no false audit trail)
- Enables silent fraud detection

---

## File Changes

### Modified Files
- `state.py` - Added new state fields
- `intent_detector.py` - Already supports CANCEL_APPOINTMENT
- `info_extractor.py` - Patient validation and cancellation detection
- `graph.py` - Cancellation confirmation flow
- `response_generator.py` - Prompts for new states
- `trello_tools.py` - Two new card creation functions
- `app.py` - State restoration for new fields

### New Test Files
- `test_new_features.py` - Validates both features

---

## Testing

Run the test suite:
```bash
python test_new_features.py
python test_booking_flow.py
python test_deceased_patient.py
```

Test in Streamlit UI:
```bash
chatbot.bat
```

Then try:
1. **New Patient:** Use unknown Patient ID during booking
2. **Cancellation:** Type "I want to cancel" with patient name/ID
3. **Deceased Cancellation:** Use ID P004 or P005 (known deceased patients)
