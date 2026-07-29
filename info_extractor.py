from langchain_core.prompts import ChatPromptTemplate
from llm_setup import get_llm
from intent_detector import _extract_text
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

    return state
