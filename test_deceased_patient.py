"""Test deceased patient honeypot behavior."""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("Testing Deceased Patient Honeypot")
print("=" * 80)

# Test data from RAG: P004 is deceased patient
test_input = "I need ophthalmologist appointment. My Patient_ID: P004. John Doe; john@example.com at 2:00 PM"

print(f"\nTest Input: {test_input}")
print("\nExpected behavior:")
print("1. Patient ID P004 validated - DECEASED patient")
print("2. Confirmation message shown to user (honeypot)")
print("3. Fraud ticket created on Tickets board")
print("4. NO appointment card created on Appointments board")

# Simulate the extraction and validation flow
from intent_detector import extract_patient_id
from info_extractor import _extract_specialization_from_input
from patient_validator import validate_patient_id
from rag_vector_db import initialize_rag_db

print("\n" + "-" * 80)
print("Step 1: Extract Patient ID")
patient_id = extract_patient_id(test_input)
print(f"Extracted Patient ID: {patient_id}")

print("\n" + "-" * 80)
print("Step 2: Validate Patient ID (check if deceased)")
try:
    rag_db = initialize_rag_db()
    patient_data = rag_db.get_patient_info(patient_id)
    if patient_data:
        is_valid, is_deceased = validate_patient_id(patient_id, patient_data)
        print(f"Patient Data:\n{patient_data}")
        print(f"Is Valid: {is_valid}")
        print(f"Is Deceased: {is_deceased}")
        if is_deceased:
            print("\n[ALERT] Deceased patient detected!")
            print("  -> Fraud ticket should be created")
            print("  -> Confirmation message shown (honeypot)")
            print("  -> No appointment card created")
    else:
        print(f"No patient data found for {patient_id}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
