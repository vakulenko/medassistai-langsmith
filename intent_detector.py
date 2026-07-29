from langchain_core.prompts import ChatPromptTemplate
from llm_setup import get_llm
from state import Intent
import re

INTENT_DETECTION_PROMPT = ChatPromptTemplate.from_template("""
Analyze the user's message and determine their intent for booking a doctor appointment.

User message: {user_input}

Determine the intent from these options:
- book_appointment: User wants to book an appointment with a doctor
- view_doctors: User wants to see available doctors
- check_availability: User wants to check doctor availability
- cancel_appointment: User wants to cancel an appointment
- general_info: User is asking general questions about the service
- unknown: Cannot determine the intent

Respond with ONLY the intent name (e.g., "book_appointment"), nothing else.
""")

def detect_intent(state):
    """Detect the user's intent from their input."""
    llm = get_llm()
    chain = INTENT_DETECTION_PROMPT | llm

    response = chain.invoke({"user_input": state.user_input})
    intent_text = _extract_text(response).strip().lower()

    try:
        detected_intent = Intent(intent_text)
    except ValueError:
        detected_intent = Intent.UNKNOWN

    state.detected_intent = detected_intent

    # Extract patient ID if present (format: "ID: XXXXX" or "Patient ID: XXXXX")
    patient_id = extract_patient_id(state.user_input)
    if patient_id:
        state.patient_id = patient_id

    return state


def extract_patient_id(text: str) -> str:
    """Extract Patient ID from user input.

    Looks for patterns like:
    - "ID: P12345"
    - "Patient ID: P12345"
    - "ID P12345"
    - "my ID is P12345"
    """
    # Try different patterns
    patterns = [
        r'(?:patient\s+)?id\s*:\s*([A-Za-z0-9]+)',
        r'(?:patient\s+)?id\s+([A-Za-z0-9]+)',
        r'my\s+id\s+(?:is\s+)?([A-Za-z0-9]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

    return None


def _extract_text(response):
    """Helper to extract text from various response formats."""
    # Handle direct dict response from Gemini API
    if isinstance(response, dict):
        if 'text' in response:
            return response['text']
        return str(response)

    # Handle LangChain message objects
    if hasattr(response, 'content'):
        content = response.content
        if isinstance(content, list):
            if content and isinstance(content[0], dict) and 'text' in content[0]:
                return content[0]['text']
            return str(content[0]) if content else ""
        elif isinstance(content, dict):
            return content.get('text', str(content))
        else:
            return str(content)

    return str(response)
