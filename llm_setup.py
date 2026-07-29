import os
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY, GEMINI_MODEL, LANGSMITH_API_KEY, LANGSMITH_ENDPOINT

# Configure LangSmith environment variables
os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
os.environ["LANGSMITH_ENDPOINT"] = LANGSMITH_ENDPOINT
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "medassistai-chatbot"

def get_llm():
    """Initialize and return Gemini LLM instance."""
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        convert_system_message_to_human=True,
    )

if __name__ == "__main__":
    llm = get_llm()
    print("[OK] LLM initialized successfully")
    print(f"Model: {GEMINI_MODEL}")
    print(f"LangSmith Tracing: Enabled")
