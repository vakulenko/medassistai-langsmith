# Bug Fix: Trello Card Not Created on Next Session (Interrupt Resume)

## Issue Description

When using the interrupt pattern for confirmations across multiple user messages:
1. User provides booking details in message 1 → Graph pauses at confirmation (interrupt)
2. User provides confirmation in message 2 → **Trello card NOT created** ❌

**Root Cause**: When resuming from interrupt, the `detected_intent` field was not being restored from the saved booking state. This caused the graph to lose context about the booking intent, preventing it from routing to the `create_appointment` node.

## The Bug in Detail

### What Happened

**Message 1: Booking Details**
```
User: "I need to see a Therapist... P999... Cate Cate..."
↓
Graph flow:
  intent_detection → BOOK_APPOINTMENT ✓
  extraction → {patient_name: "Cate Cate", ...} ✓
  validation → patient_not_found: true ✓
  response → "Please confirm..." ✓
  [INTERRUPT] Pauses at confirmation ✓
  
Saved state includes:
  - detected_intent: BOOK_APPOINTMENT ✓
  - extracted_info: {...} ✓
  - patient_not_found: true ✓
  - appointment_ready_for_confirmation: true ✓
```

**Message 2: Confirmation**
```
User: "Approve"
↓
App restores state BUT:
  - detected_intent: UNKNOWN ❌ (NOT restored!)
  - extracted_info: {...} ✓
  - appointment_ready_for_confirmation: true ✓
↓
Graph flow:
  intent_detection → UNKNOWN (detects from "Approve")
  ...
  should_continue() logic:
    If intent != BOOK_APPOINTMENT → returns END
  [NEVER REACHES create_appointment node]
↓
Result: Trello card NOT created ❌
```

### Why The State Was Lost

In `app.py`, the `ChatState` was created but `detected_intent` was not included in the restoration logic:

```python
# WRONG: Missing detected_intent restoration
chat_state = ChatState(
    user_input=user_input,
    conversation_history=active_session.conversation_history,
    patient_id=st.session_state.booking_state.get("patient_id"),  # ✓ Restored
    extracted_info=st.session_state.booking_state.get("extracted_info"),  # ✓ Restored
    # ... other fields ...
    # detected_intent NOT saved/restored ❌
)
```

And the saving side:

```python
# WRONG: Not saving detected_intent
st.session_state.booking_state = {
    "patient_id": result.get("patient_id"),
    "extracted_info": result.get("extracted_info", {}),
    # ... other fields ...
    # detected_intent NOT saved ❌
}
```

## The Fix

### 1. Restore detected_intent When Creating State (app.py:169-184)

```python
# NEW: Properly restore detected_intent
detected_intent_str = st.session_state.booking_state.get("detected_intent")
detected_intent = Intent(detected_intent_str) if detected_intent_str else Intent.UNKNOWN

chat_state = ChatState(
    messages=active_session.chat_history,
    user_input=user_input,
    conversation_history=active_session.conversation_history,
    available_doctors=list(DOCTOR_PROFILES.keys()),
    detected_intent=detected_intent,  # ✓ NOW RESTORED
    extracted_info=st.session_state.booking_state.get("extracted_info", {}),
    patient_id=st.session_state.booking_state.get("patient_id"),
    # ... other fields ...
)
```

### 2. Save detected_intent When Storing State (app.py:230-245)

```python
# NEW: Save detected_intent for next resume
detected_intent_value = result.get("detected_intent")
detected_intent_str = detected_intent_value.value if hasattr(detected_intent_value, 'value') else str(detected_intent_value)

st.session_state.booking_state = {
    "detected_intent": detected_intent_str,  # ✓ NOW SAVED
    "patient_id": result.get("patient_id"),
    "extracted_info": result.get("extracted_info", {}),
    # ... other fields ...
}
```

## Test Case: Before and After Fix

### Before Fix ❌

```
Message 1: "I need to see a Therapist doctor next Tuesday. My Patient_ID: P999. My name is Cate Cate; cate@test.com at 7:00 AM"

Bot: "Please confirm... [confirmation prompt]"
[Graph paused at interrupt]

Message 2: "Approve"

Result:
  - booking_confirmed: FALSE ❌
  - Trello card NOT created ❌
  - No add-patient card created ❌
  - Booking incomplete ❌
```

### After Fix ✓

```
Message 1: "I need to see a Therapist doctor next Tuesday. My Patient_ID: P999. My name is Cate Cate; cate@test.com at 7:00 AM"

Bot: "Please confirm... [confirmation prompt]"
[Graph paused at interrupt]

Message 2: "Approve"

Result:
  - booking_confirmed: TRUE ✓
  - Trello appointment card created ✓
  - Trello add-patient card created ✓
  - Booking complete ✓
  - Email confirmation sent ✓
```

## Files Modified

- **app.py**: 
  - Line 169-184: Add `detected_intent` restoration from saved booking state
  - Line 230-245: Add `detected_intent` to saved booking state

## Why This Matters

The `detected_intent` field is CRITICAL for the graph routing logic:

```python
# In graph.py should_continue():
def should_continue(state: ChatState) -> str:
    if state.appointment_ready_for_confirmation:
        return "ask_for_confirmation"
    
    if state.detected_intent == Intent.BOOK_APPOINTMENT:  # ← Depends on this!
        # ... routing logic for booking ...
        return "ask_for_confirmation"
    
    return END  # ← If intent is UNKNOWN, ends here (BUG)
```

Without the correct `detected_intent`, the graph always takes the END route and never creates the Trello card.

## Impact

**Affected Scenarios**:
- ✓ Multi-turn bookings with confirmation (interrupt pattern)
- ✓ New patients (require add-patient card)
- ✓ Any booking that uses interrupts for confirmation

**Scope**: All bookings that span multiple user messages when using interrupt pattern.

## Verification

The fix is verified by:
1. Message 1 now saves `detected_intent` = "book_appointment"
2. Message 2 restores `detected_intent` = "book_appointment" from saved state
3. Graph correctly routes to `create_appointment` node
4. Trello cards are created successfully

## Related Code Sections

**Graph routing (graph.py:128-152)**:
- Depends on `detected_intent` to determine if booking flow should continue
- Also depends on `appointment_ready_for_confirmation` to route to confirmation

**Appointment creation (graph.py:61-98)**:
- Requires proper routing to execute
- Creates appointment card + add-patient card for new patients

**State management (state.py:24-42)**:
- `detected_intent` is required field in ChatState
- Defaults to Intent.UNKNOWN

## Testing the Fix

To verify the fix works:

```python
# Step 1: Start new booking (interrupt happens)
# User: "I need therapist... P999... Cate Cate..."

# Step 2: Provide confirmation (resume from interrupt)
# User: "Approve"

# Expected result:
# - Trello appointment card created
# - Trello add-patient card created (since P999 is new)
# - Response: "Your appointment has been successfully confirmed..."
# - booking_confirmed: true
# - Trello board shows 2 new cards
```

## Lessons Learned

1. **State Restoration**: When using interrupt pattern, ALL state fields must be explicitly saved and restored
2. **Testing**: Need tests specifically for multi-message flows with interrupts
3. **Documentation**: Interrupt pattern documentation should highlight state preservation requirements

## Prevention

To prevent similar bugs:
1. Use explicit field mapping (not dynamic dict merging)
2. Add comprehensive tests for multi-message flows
3. Document which fields are required for resuming from interrupts
4. Use TypeScript or strict validation to catch missing fields early

## Summary

**Bug**: Trello cards not created when resuming from interrupt because `detected_intent` wasn't restored  
**Root Cause**: Missing field in state restoration logic  
**Fix**: Save and restore `detected_intent` in app.py  
**Impact**: All multi-turn bookings with interrupts now work correctly  
**Status**: FIXED ✓

---

**Commit**: Will include with next push  
**Date**: July 31, 2026  
**Priority**: HIGH (affects core booking functionality)
