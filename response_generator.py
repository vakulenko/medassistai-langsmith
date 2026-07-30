from langchain_core.prompts import ChatPromptTemplate
from llm_setup import get_llm
from state import Intent
from config import DOCTOR_PROFILES
from intent_detector import _extract_text

try:
    from rag_vector_db import initialize_rag_db
except Exception as e:
    print(f"Warning: RAG not available: {e}")
    initialize_rag_db = None

BOOKING_PROMPT = ChatPromptTemplate.from_template("""
You are a medical appointment booking assistant for MedAssistAI.

PATIENT IDENTIFICATION:
- Patient ID: {patient_id}
- Patient Name: {patient_name}
- Patient Email: {patient_email}
- Patient Status: {patient_status}

APPOINTMENT DETAILS:
- Requested Doctor: {doctor_name}
- Requested Date: {appointment_date}
- Requested Time: {appointment_time}
- Reason for Visit: {appointment_reason}

SPECIALIZATION CHECK:
- Requested Specialization: {specialization}
- Available: {has_doctor}

DOCTOR & PATIENT CONTEXT:
{doctor_context}
{patient_context}

INSTRUCTIONS:
1. Patient ID must be provided - ask for it if missing
2. Prioritize contextual information from doctor profiles and patient data
3. If requested specialization is NOT available, explain we cannot help
4. Once all details are confirmed, ask explicit approval to proceed
5. Never proceed without explicit user confirmation
6. If patient status is "New (not in system)", mention they will be registered

User message: {user_input}
Conversation: {conversation_history}

Respond helpfully and professionally.
""")

GENERAL_PROMPT = ChatPromptTemplate.from_template("""
You are a helpful medical appointment booking assistant for MedAssistAI.

User message: {user_input}
Available Doctors: {available_doctors}

Relevant Information:
{rag_context}

Conversation history: {conversation_history}

Provide a helpful response about the service, doctors, or general information.
Use the available information to answer questions about doctors and services.
Be warm, professional, and guide the user towards booking an appointment if relevant.
""")

PATIENT_NOT_FOUND_PROMPT = ChatPromptTemplate.from_template("""
A new patient is trying to book an appointment. They provided:
- Patient Name: {patient_name}
- Patient ID: {patient_id}
- Doctor/Specialization: {doctor_name}
- Requested Date: {appointment_date}
- Requested Time: {appointment_time}
- Reason: {reason}

This patient is NOT in our system yet. We will add them, but first ask for confirmation
to proceed with the appointment booking. The patient will be added to our system as a
new patient once booking is confirmed.

Generate a professional response that:
1. Confirms we'll add them as a new patient
2. Shows the doctor/specialization we found for them
3. Asks if they want to proceed with the booking
4. Lists what we have for them
""")

def generate_response(state):
    """Generate appropriate response based on user intent."""
    llm = get_llm()
    available_doctors = list(DOCTOR_PROFILES.keys())

    # Initialize RAG DB
    rag_db = None
    if initialize_rag_db:
        try:
            rag_db = initialize_rag_db()
        except Exception as e:
            print(f"Warning: RAG DB initialization failed: {e}")
            rag_db = None

    if state.detected_intent == Intent.BOOK_APPOINTMENT:
        # If patient not found but NOT in confirmation, show patient-not-found prompt
        if state.patient_not_found and not state.appointment_ready_for_confirmation:
            prompt = PATIENT_NOT_FOUND_PROMPT
            extracted = state.extracted_info
            response = llm.invoke(prompt.format_prompt(
                patient_name=extracted.get("patient_name", "Unknown"),
                patient_id=state.patient_id or "Not provided",
                doctor_name=extracted.get("doctor_name", "Not specified"),
                appointment_date=extracted.get("appointment_date", "Not specified"),
                appointment_time=extracted.get("appointment_time", "Not specified"),
                reason=extracted.get("reason", "General checkup")
            ).messages)
            state.last_response = _extract_text(response)
            return state

        prompt = BOOKING_PROMPT
        extracted = state.extracted_info

        # Check if doctor/patient request (use RAG priority)
        doctor_context = ""
        patient_context = ""

        if state.use_rag_context and rag_db:
            # PRIORITIZE RAG CONTEXT for doctor/patient data
            doctor_name = extracted.get("doctor_name", "")
            if doctor_name:
                doc_info = rag_db.get_doctor_info(doctor_name)
                doctor_context = doc_info or "Doctor information from records"

            # Get patient info by ID first, then by name
            if state.patient_id:
                patient_info = rag_db.get_patient_info(state.patient_id)
                patient_context = patient_info or "Patient information from records"
            elif extracted.get("patient_name"):
                patient_info = rag_db.get_patient_info(extracted.get("patient_name"))
                patient_context = patient_info or "Patient information from records"

        # Determine patient status
        patient_status = "New (not in system)" if state.patient_not_found else "Existing patient"

        # Ensure dates are in proper format for display
        appointment_date = extracted.get("appointment_date", "Not specified")
        appointment_time = extracted.get("appointment_time", "Not specified")

        # If still showing natural language, try to parse
        if appointment_date and appointment_date.lower() in ["tomorrow", "not specified"]:
            from date_time_parser import parse_date_time
            parsed = parse_date_time(state.user_input)
            if parsed.get("appointment_date"):
                appointment_date = parsed["appointment_date"]

        if appointment_time and (":" not in appointment_time or appointment_time.lower() in ["not specified"]):
            from date_time_parser import parse_date_time
            parsed = parse_date_time(state.user_input)
            if parsed.get("appointment_time"):
                appointment_time = parsed["appointment_time"]

        response = llm.invoke(prompt.format_prompt(
            patient_id=state.patient_id or "Not provided",
            patient_name=extracted.get("patient_name", "Not provided"),
            patient_email=extracted.get("patient_email", "Not provided"),
            patient_status=patient_status,
            doctor_name=extracted.get("doctor_name", "Not specified"),
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            appointment_reason=extracted.get("reason", "Not specified"),
            specialization=state.requested_specialization or "Not specified",
            has_doctor="Yes" if state.has_available_doctor else "No",
            available_doctors=", ".join(available_doctors),
            doctor_context=doctor_context,
            patient_context=patient_context,
            user_input=state.user_input,
            conversation_history="\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in state.conversation_history[-3:]])
        ).messages)
    else:
        prompt = GENERAL_PROMPT

        # Get RAG context for general queries
        rag_context = ""
        if rag_db:
            context_list = rag_db.retrieve_relevant_context(state.user_input, top_k=3)
            rag_context = "\n".join(context_list) if context_list else "General information about our medical services"

        response = llm.invoke(prompt.format_prompt(
            user_input=state.user_input,
            available_doctors=", ".join(available_doctors),
            rag_context=rag_context,
            conversation_history="\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in state.conversation_history[-3:]])
        ).messages)

    state.last_response = _extract_text(response)
    return state
