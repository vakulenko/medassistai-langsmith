"""Patient validation against clinic data from RAG."""
from typing import Dict, Optional, Tuple
from config import DOCTOR_PROFILES


def extract_doctor_specializations_from_rag(rag_db) -> Dict[str, list]:
    """Extract doctor specializations from RAG data.

    Reads doctor profiles from RAG and extracts specializations mentioned.
    """
    if not rag_db:
        return {}

    specializations = {}

    for doctor_name in DOCTOR_PROFILES.keys():
        # Get doctor info from RAG
        doctor_info = rag_db.get_doctor_info(doctor_name)
        if not doctor_info:
            continue

        info_lower = doctor_info.lower()

        # Extract specializations from the doctor's profile
        # Look for keywords that indicate specialization
        potential_specs = [
            "ophthalmology", "ophthalmologist", "eye", "vision", "sight",
            "cardiology", "cardiologist", "heart", "cardiovascular",
            "orthopedics", "orthopedic", "spine", "bone", "joint",
            "pediatrics", "pediatrician", "children", "child",
            "general practice", "general practitioner", "gp",
            "internal medicine", "internist",
            "dermatology", "dermatologist", "skin",
            "psychiatry", "psychiatrist", "mental",
            "neurology", "neurologist", "brain", "nerve",
            "surgery", "surgeon", "surgical",
        ]

        doc_specs = []
        for spec in potential_specs:
            if spec in info_lower:
                doc_specs.append(spec)

        if doc_specs:
            specializations[doctor_name] = doc_specs

    return specializations


def check_specialization_available(specialization: str, rag_db=None) -> Tuple[bool, Optional[list]]:
    """Check if requested specialization is available in clinic using RAG data.

    Returns:
        (is_available, list_of_doctors) or (False, None)
    """
    if not rag_db:
        return False, None

    spec_lower = specialization.lower().strip()

    # Get specializations from RAG data
    doctor_specs = extract_doctor_specializations_from_rag(rag_db)

    available_doctors = []
    for doctor_name, specs in doctor_specs.items():
        for spec in specs:
            if spec_lower in spec or spec in spec_lower:
                available_doctors.append(doctor_name)
                break

    if available_doctors:
        return True, available_doctors

    return False, None


def get_doctor_specializations(doctor_name: str, rag_db=None) -> Optional[list]:
    """Get specializations for a doctor from RAG data."""
    if not rag_db:
        return None

    doctor_specs = extract_doctor_specializations_from_rag(rag_db)

    for doc, specs in doctor_specs.items():
        if doctor_name.lower() in doc.lower() or doc.lower() in doctor_name.lower():
            return specs

    return None


def validate_patient_id(patient_id: str, patient_data: str) -> Tuple[bool, bool]:
    """Validate patient ID against patient data.

    Returns:
        (patient_exists, is_deceased)
    """
    if not patient_id or not patient_data:
        return False, False

    patient_id_lower = patient_id.lower().strip()
    patient_data_lower = patient_data.lower()

    # Check if patient ID exists in data
    if patient_id_lower not in patient_data_lower:
        return False, False

    # Check if patient is marked as deceased
    # Look for patterns like "deceased", "died", "deceased_date", etc. near patient ID
    lines = patient_data_lower.split('\n')
    for line in lines:
        if patient_id_lower in line:
            if any(marker in line for marker in ['deceased', 'died', 'death', 'expired', '†']):
                return True, True

    return True, False


def get_available_doctors_list() -> list:
    """Get list of all doctors in clinic from config."""
    return list(DOCTOR_PROFILES.keys())
