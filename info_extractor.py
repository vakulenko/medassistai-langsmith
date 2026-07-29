from langchain_core.prompts import ChatPromptTemplate
from llm_setup import get_llm
from intent_detector import _extract_text
from patient_validator import check_specialization_available, validate_patient_id
from state import Intent
import json

EXTRACTION_PROMPT = ChatPromptTemplate.from_template("""
Extract appointment booking information from the user's message.

User message: {user_input}
Conversation context: {conversation_context}

Extract the following information if present (return as JSON):
- patient_name: Patient's full name
- patient_email: Patient's email address
- doctor_name: Preferred doctor's name
- appointment_date: Preferred appointment date (YYYY-MM-DD format)
- appointment_time: Preferred appointment time (HH:MM format)
- reason: Reason for appointment/chief complaint
- specialization: Required doctor specialization (if doctor not specified)

For any missing information, use null.
Return ONLY valid JSON, no additional text.
""")


def extract_info(state):
    """Extract relevant appointment information from user input."""
    llm = get_llm()
    chain = EXTRACTION_PROMPT | llm

    conversation_context = " ".join([msg.get("content", "") for msg in state.conversation_history[-3:]])

    response = chain.invoke({
        "user_input": state.user_input,
        "conversation_context": conversation_context
    })

    content = _extract_text(response)

    try:
        extracted_info = json.loads(content)
        state.extracted_info = extracted_info
    except json.JSONDecodeError:
        state.extracted_info = {}

    # Determine if this request involves doctor/patient data (should use RAG)
    if state.detected_intent == Intent.BOOK_APPOINTMENT:
        state.use_rag_context = True

        # Initialize RAG DB for specialization checking
        rag_db = None
        try:
            from rag_vector_db import initialize_rag_db
            rag_db = initialize_rag_db()
        except Exception as e:
            pass

        # Check specialization availability using RAG data
        specialization = extracted_info.get("specialization")
        doctor_name = extracted_info.get("doctor_name")

        if specialization and rag_db:
            state.requested_specialization = specialization
            has_available, doctors = check_specialization_available(specialization, rag_db)
            state.has_available_doctor = has_available
            if has_available and doctors:
                # Suggest the first available doctor
                if not doctor_name:
                    extracted_info["doctor_name"] = doctors[0]
                    state.extracted_info = extracted_info

        # Validate patient ID if provided
        if state.patient_id:
            try:
                from rag_vector_db import initialize_rag_db
                rag_db = initialize_rag_db()
                patient_data = rag_db.get_patient_info(state.patient_id)

                if patient_data:
                    patient_exists, is_deceased = validate_patient_id(state.patient_id, patient_data)
                    if is_deceased:
                        state.is_deceased_patient = True
            except Exception as e:
                pass  # Continue even if patient validation fails

    return state
