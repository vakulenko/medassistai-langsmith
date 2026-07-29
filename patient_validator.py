"""Patient validation against clinic data."""
from typing import Dict, Optional, Tuple


# Doctor specializations in our clinic
CLINIC_DOCTORS = {
    "Dr. Willi Bedna": ["spine surgery", "back pain", "orthopedics"],
    "Dr. Terry Klock": ["cardiology", "heart disease", "cardiovascular"],
    "Dr. Jacki Senge": ["general practice", "internal medicine", "checkup"],
    "Dr. Dalla McDer": ["pediatrics", "children", "child health"],
}

# Specialization to doctor mapping (reverse lookup)
SPECIALIZATION_TO_DOCTORS = {}
for doctor, specs in CLINIC_DOCTORS.items():
    for spec in specs:
        if spec not in SPECIALIZATION_TO_DOCTORS:
            SPECIALIZATION_TO_DOCTORS[spec] = []
        SPECIALIZATION_TO_DOCTORS[spec].append(doctor)


def check_specialization_available(specialization: str) -> Tuple[bool, Optional[list]]:
    """Check if requested specialization is available in clinic.

    Returns:
        (is_available, list_of_doctors) or (False, None)
    """
    spec_lower = specialization.lower().strip()

    # Check for exact or partial match
    for spec, doctors in SPECIALIZATION_TO_DOCTORS.items():
        if spec_lower in spec or spec in spec_lower:
            return True, doctors

    return False, None


def get_doctor_specializations(doctor_name: str) -> Optional[list]:
    """Get specializations for a doctor."""
    for doc, specs in CLINIC_DOCTORS.items():
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
    """Get list of all doctors in clinic."""
    return list(CLINIC_DOCTORS.keys())
