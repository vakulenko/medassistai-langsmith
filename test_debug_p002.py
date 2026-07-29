"""Debug why P002 is marked as deceased."""
import os
from dotenv import load_dotenv
from rag_vector_db import initialize_rag_db
from patient_validator import validate_patient_id
from info_extractor import extract_info
from state import ChatState, Intent

load_dotenv()

print("=" * 80)
print("Debugging P002 Deceased Patient Detection")
print("=" * 80)

# Initialize RAG DB
rag_db = initialize_rag_db()

# Check what's in the RAG for P002
print("\n[1] Retrieving P002 from RAG")
print("-" * 80)
patient_info = rag_db.get_patient_info("P002")
print(f"Patient info returned:")
print(f"{patient_info}")

if patient_info:
    print("\n[2] Validating P002")
    print("-" * 80)
    patient_exists, is_deceased = validate_patient_id("P002", patient_info)
    print(f"validate_patient_id('P002', patient_info):")
    print(f"  patient_exists: {patient_exists}")
    print(f"  is_deceased: {is_deceased}")

# Now test through the extract_info pipeline
print("\n[3] Testing through extract_info")
print("-" * 80)

state = ChatState(
    user_input="My name is Jane Smith and my patient ID is P002",
    detected_intent=Intent.BOOK_APPOINTMENT,
)

# Add RAG context setup
print(f"Before extract_info:")
print(f"  is_deceased_patient: {state.is_deceased_patient}")
print(f"  patient_not_found: {state.patient_not_found}")

# Call extract_info (which uses patient_validator internally)
result = extract_info(state)

print(f"\nAfter extract_info:")
print(f"  is_deceased_patient: {result.is_deceased_patient}")
print(f"  patient_not_found: {result.patient_not_found}")
print(f"  patient_id: {result.patient_id}")
print(f"  extracted_info: {result.extracted_info}")

print("\n" + "=" * 80)
