from langchain_core.prompts import ChatPromptTemplate
from llm_setup import get_llm
from state import Intent

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
    return state


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
