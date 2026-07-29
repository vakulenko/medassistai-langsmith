# MedAssistAI Chatbot - Doctor Appointment Booking

A conversational AI chatbot for booking doctor appointments, built with **Streamlit**, **LangGraph**, and **Google Gemini**.

## Quick Start

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` with API keys:**
   ```env
   GOOGLE_API_KEY=your_gemini_api_key
   LANGSMITH_API_KEY=your_key
   TRELLO_API_KEY=your_key
   TRELLO_API_TOKEN=your_token
   TRELLO_BOARD_APPOINTMENTS=board_id
   TRELLO_BOARD_TICKETS=board_id
   ```

### Run Chatbot

```bash
python -m streamlit run app.py
```

Opens at **http://localhost:8501**

## Features

- **Conversational Booking** - Intent detection, multi-turn confirmation, and natural language understanding
- **Multiple Doctors** - Support for multiple doctor profiles with specializations
- **Session Management** - Create, switch, and delete independent chat sessions
- **Appointment Tracking** - Automatic Trello card creation for confirmed bookings
- **New Patient Registration** - Automatic Trello ticket for adding new patients NOT in database
- **Fraud Detection** - Honeypot alerts for deceased patients and suspicious patterns

## How It Works

1. User describes appointment needs in natural language
2. Bot extracts patient info, preferred doctor, date, and time
3. Bot confirms all details with user (multi-turn confirmation)
4. User approves appointment
5. Trello card automatically created with appointment details

### Example Conversation - Existing Patient

**User:** "I need ophthalmologist tomorrow. Patient ID: P002. Name: Sergii Vakulenko. Email: test@test.com. At 12:34 PM"

**Bot:** [Summarizes appointment details and asks for confirmation]

**User:** "Approve"

**Bot:** [Confirms booking, Trello appointment card created]

### Example Conversation - New Patient

**User:** "I need ophthalmologist tomorrow. Patient ID: P999 (NEW). Name: John Smith. Email: john.smith@test.com. At 2:30 PM"

**Bot:** [Detects patient NOT in database, asks for confirmation]

**User:** "Yes, approve"

**Bot:** [Confirms booking, creates TWO Trello cards:
  - Appointment card for the booking
  - "Add Patient" ticket for patient registry team]

## Project Structure

```
medassistai-langsmith/
├── chatbot.py / chatbot.bat          # Run chatbot
├── app.py                            # Streamlit UI
├── graph.py                          # LangGraph workflow
├── state.py                          # State models
├── config.py                         # Configuration
├── llm_setup.py                      # LLM setup
├── intent_detector.py                # Intent detection
├── info_extractor.py                 # Information extraction
├── date_time_parser.py               # Date/time parsing
├── response_generator.py             # Response generation
├── patient_validator.py              # Patient validation
├── rag_vector_db.py                  # Vector database
├── trello_tools.py                   # Trello integration
├── langsmith_debug.py                # LangSmith utilities
├── load_rag_data.py                  # Load data into vector DB
├── requirements.txt                  # Dependencies
└── .vector_db/                       # Chroma vector database
```

## Configuration

### Environment Variables

```env
# Required
GOOGLE_API_KEY=your_gemini_api_key
LANGSMITH_API_KEY=your_langsmith_key

# Trello (optional but recommended)
TRELLO_API_KEY=your_trello_key
TRELLO_API_TOKEN=your_trello_token
TRELLO_BOARD_APPOINTMENTS=board_id_for_appointments
TRELLO_BOARD_TICKETS=board_id_for_fraud_alerts

# Google Drive RAG (optional)
GOOGLE_DRIVE_LINK_PATIENT_DATA=https://drive.google.com/file/d/.../view
```

## Tech Stack

- **UI**: Streamlit
- **LLM**: Google Gemini 3.6 Flash
- **Workflow**: LangGraph
- **Tracing**: LangSmith Studio
- **Data Integration**: Trello API
- **Vector DB**: Chroma with Google Gemini embeddings

## Troubleshooting

### Trello Cards Not Creating
- Verify `TRELLO_API_KEY` and `TRELLO_API_TOKEN` in `.env`
- Check board IDs are correct
- Ensure "In Queue" list exists on both boards

### Gemini API Errors
- Verify `GOOGLE_API_KEY` is valid
- Check API quotas in Google Cloud Console

### Scripts Won't Start
- Verify `.env` file exists
- Run: `pip install -r requirements.txt`
- Check Python 3.11+ is installed

## License

MIT License
