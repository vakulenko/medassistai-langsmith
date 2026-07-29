import os
from dotenv import load_dotenv

load_dotenv()

# Google Gemini Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-3.6-flash"

# LangSmith Configuration
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_PROJECT = "medassistai-chatbot"

# Trello Configuration
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_API_TOKEN = os.getenv("TRELLO_API_TOKEN")
TRELLO_BOARD_APPOINTMENTS = os.getenv("TRELLO_BOARD_APPOINTMENTS")

# Google Drive Links
DOCTOR_PROFILES = {
    "Dr. Willi Bedna": os.getenv("GOOGLE_DRIVE_LINK_DR_WILLI_BEDNA"),
    "Dr. Terry Klock": os.getenv("GOOGLE_DRIVE_LINK_DR_TERRY_KLOCK"),
    "Dr. Jacki Senge": os.getenv("GOOGLE_DRIVE_LINK_DR_JACKI_SENGE"),
    "Dr. Dalla McDer": os.getenv("GOOGLE_DRIVE_LINK_DR_DALLA_MCDER"),
}

PATIENT_DATA_LINK = os.getenv("GOOGLE_DRIVE_LINK_PATIENT_DATA")
