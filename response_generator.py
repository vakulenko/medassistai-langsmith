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
You are a helpful medical appointment booking assistant for MedAssistAI.

Current extracted information:
- Patient Name: {patient_name}
- Patient Email: {patient_email}
- Preferred Doctor: {doctor_name}
- Preferred Date: {appointment_date}
- Preferred Time: {appointment_time}
- Reason for Visit: {appointment_reason}

Available Doctors: {available_doctors}

Relevant Doctor Information:
{doctor_context}

Relevant Patient Information:
{patient_context}

User's latest message: {user_input}
Conversation history: {conversation_history}

Based on the information above and the user's message, provide a helpful response that:
1. Confirms what information you've collected
2. Asks for any missing critical information
3. Suggests available options if needed
4. Use the doctor and patient information to provide personalized recommendations
5. Is warm and professional

If all required information is present, confirm the appointment details and indicate the booking is ready.
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
        prompt = BOOKING_PROMPT
        extracted = state.extracted_info

        # Get RAG context
        doctor_context = ""
        patient_context = ""
        if rag_db:
            doctor_name = extracted.get("doctor_name", "")
            if doctor_name:
                doc_info = rag_db.get_doctor_info(doctor_name)
                doctor_context = doc_info or "No specific information found"
            else:
                # Generic doctor query
                doctor_context_list = rag_db.retrieve_relevant_context("doctor availability specialties", top_k=2)
                doctor_context = "\n".join(doctor_context_list) if doctor_context_list else "Available information about doctors"

            patient_name = extracted.get("patient_name", "")
            if patient_name:
                patient_info = rag_db.get_patient_info(patient_name)
                patient_context = patient_info or "No specific patient information found"

        response = llm.invoke(prompt.format_prompt(
            patient_name=extracted.get("patient_name", "Not provided"),
            patient_email=extracted.get("patient_email", "Not provided"),
            doctor_name=extracted.get("doctor_name", "Not specified"),
            appointment_date=extracted.get("appointment_date", "Not specified"),
            appointment_time=extracted.get("appointment_time", "Not specified"),
            appointment_reason=extracted.get("reason", "Not specified"),
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
