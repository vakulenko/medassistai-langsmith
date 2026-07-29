"""Debug the exact flow to see where appointment_ready_for_confirmation is lost."""
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from state import ChatState, Intent, SessionManager
from config import DOCTOR_PROFILES
from intent_detector import detect_intent
from info_extractor import extract_info
from response_generator import generate_response
from graph import should_continue, check_fraud_and_alert

load_dotenv()

print("=" * 80)
print("Debugging Message 1 Flow")
print("=" * 80)

user_input = "I need a ophthalmologist tomorrow. I have sight issue. My Patient_ID: P002. My name is Sergii Vakulenko; test@test.com at 12:34 PM"

# Create initial state
state = ChatState(
    user_input=user_input,
    messages=[{"role": "user", "content": user_input}],
    available_doctors=list(DOCTOR_PROFILES.keys())
)

print(f"\n[INITIAL STATE]")
print(f"  appointment_ready_for_confirmation: {state.appointment_ready_for_confirmation}")
print(f"  detected_intent: {state.detected_intent}")

# Step 1: detect_intent
print(f"\n[STEP 1] Calling detect_intent...")
state = detect_intent(state)
print(f"  detected_intent: {state.detected_intent}")
print(f"  appointment_ready_for_confirmation: {state.appointment_ready_for_confirmation}")

# Step 2: extract_info
print(f"\n[STEP 2] Calling extract_info...")
state = extract_info(state)
print(f"  extracted_info keys: {list(state.extracted_info.keys())}")
print(f"  patient_id: {state.patient_id}")
print(f"  appointment_ready_for_confirmation: {state.appointment_ready_for_confirmation}")

# Step 3: check_fraud
print(f"\n[STEP 3] Calling check_fraud_and_alert...")
state = check_fraud_and_alert(state)
print(f"  appointment_ready_for_confirmation: {state.appointment_ready_for_confirmation}")

# Step 4: generate_response
print(f"\n[STEP 4] Calling generate_response...")
state = generate_response(state)
print(f"  last_response length: {len(state.last_response)}")
print(f"  appointment_ready_for_confirmation: {state.appointment_ready_for_confirmation}")

# Step 5: should_continue
print(f"\n[STEP 5] Calling should_continue...")
print(f"  BEFORE should_continue:")
print(f"    appointment_ready_for_confirmation: {state.appointment_ready_for_confirmation}")
print(f"    detected_intent: {state.detected_intent}")
print(f"    patient_id: {state.patient_id}")
print(f"    extracted_info has all required: {all(state.extracted_info.get(f) for f in ['patient_name', 'patient_email', 'doctor_name', 'appointment_date', 'appointment_time'])}")

next_node = should_continue(state)

print(f"  AFTER should_continue:")
print(f"    next_node returned: {next_node}")
print(f"    appointment_ready_for_confirmation: {state.appointment_ready_for_confirmation}")

print("\n" + "=" * 80)
