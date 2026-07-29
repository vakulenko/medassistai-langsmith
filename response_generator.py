from langchain_core.prompts import ChatPromptTemplate
from llm_setup import get_llm
from state import Intent
from config import DOCTOR_PROFILES
from intent_detector import _extract_text

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

User's latest message: {user_input}
Conversation history: {conversation_history}

Based on the information above and the user's message, provide a helpful response that:
1. Confirms what information you've collected
2. Asks for any missing critical information
3. Suggests available options if needed
4. Is warm and professional

If all required information is present, confirm the appointment details and indicate the booking is ready.
""")

GENERAL_PROMPT = ChatPromptTemplate.from_template("""
You are a helpful medical appointment booking assistant for MedAssistAI.

User message: {user_input}
Available Doctors: {available_doctors}
Conversation history: {conversation_history}

Provide a helpful response about the service, doctors, or general information.
Be warm, professional, and guide the user towards booking an appointment if relevant.
""")

def generate_response(state):
    """Generate appropriate response based on user intent."""
    llm = get_llm()

    available_doctors = list(DOCTOR_PROFILES.keys())

    if state.detected_intent == Intent.BOOK_APPOINTMENT:
        prompt = BOOKING_PROMPT
        extracted = state.extracted_info
        response = llm.invoke(prompt.format_prompt(
            patient_name=extracted.get("patient_name", "Not provided"),
            patient_email=extracted.get("patient_email", "Not provided"),
            doctor_name=extracted.get("doctor_name", "Not specified"),
            appointment_date=extracted.get("appointment_date", "Not specified"),
            appointment_time=extracted.get("appointment_time", "Not specified"),
            appointment_reason=extracted.get("reason", "Not specified"),
            available_doctors=", ".join(available_doctors),
            user_input=state.user_input,
            conversation_history="\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in state.conversation_history[-3:]])
        ).messages)
    else:
        prompt = GENERAL_PROMPT
        response = llm.invoke(prompt.format_prompt(
            user_input=state.user_input,
            available_doctors=", ".join(available_doctors),
            conversation_history="\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in state.conversation_history[-3:]])
        ).messages)

    state.last_response = _extract_text(response)
    return state
