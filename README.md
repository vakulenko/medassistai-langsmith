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
- **Smart Trello Integration** - Automatic card creation based on patient status:
  - Existing patients: Appointment card
  - New patients: Appointment + registration ticket
  - Deceased patients: Fraud alert (honeypot)
- **New Patient Registration** - Automatic Trello ticket for adding new patients to database
- **Fraud Detection** - Honeypot alerts for deceased patients (shows success but creates fraud ticket)

## How It Works

### Standard Booking Flow

1. User describes appointment needs in natural language
2. Bot extracts patient info, preferred doctor, date, and time
3. Bot confirms all details with user (multi-turn confirmation)
4. User approves appointment
5. Trello card(s) automatically created based on patient status

### Three Scenarios

#### Scenario 1: Existing Patient

**User:** "I need ophthalmologist tomorrow. Patient ID: P002. Name: Sergii Vakulenko. Email: test@test.com. At 12:34 PM"

**Bot:** [Confirms patient found, summarizes appointment details]

**User:** "Approve"

**Bot:** [Booking confirmed]

**Trello:** Creates **1 card**
- Appointment card on Appointments board

---

#### Scenario 2: New Patient (Not in Database)

**User:** "I need ophthalmologist tomorrow. Patient ID: P999. Name: John Smith. Email: john.smith@test.com. At 2:30 PM"

**Bot:** [Detects patient not in system, asks for confirmation]

**User:** "Yes, approve"

**Bot:** [Booking confirmed, patient will be registered]

**Trello:** Creates **2 cards**
- Appointment card on Appointments board
- "Add Patient" ticket on Tickets board (for admin to register new patient)

---

#### Scenario 3: Deceased Patient (Fraud Detection)

**User:** "I need appointment. Patient ID: P008. Name: Test Person. Email: test@test.com. At 2:00 PM"

**Bot:** [Asks for confirmation (honeypot flow)]

**User:** "Yes, approve"

**Bot:** [Shows success message]

**Trello:** Creates **1 card**
- Fraud alert ticket on Tickets board (honeypot - no appointment created)

**Note:** Deceased patients trigger fraud detection. The system shows a success message to the user (honeypot) but creates a fraud ticket for admin review instead of an actual appointment.

See [FRAUD_vs_NEW_PATIENT.md](FRAUD_vs_NEW_PATIENT.md) for technical details.

## Architecture: Multi-Agent Multi-Node

The chatbot uses a **multi-agent architecture** with each agent running as a separate LangGraph node:

```
__start__
  ↓
intent_detection (IntentDetectionAgent)
  ↓
extraction (ExtractionAgent)
  ↓
fraud_detection (FraudDetectionAgent)
  ├→ patient_validation (PatientValidationAgent) [if BOOK_APPOINTMENT]
  └→ skip [otherwise]
     ↓
  set_flags (Determine confirmation readiness)
     ↓
response_generation (ResponseGenerationAgent)
  ├→ ask_for_info → end
  ├→ ask_for_confirmation → confirmation_validation
  └→ end
     ↓
confirmation_validation (ConfirmationValidationAgent)
  ├→ create_appointment → end
  ├→ reject_booking → end
  └→ end
```

**Key Points:**
- 6 agent nodes (each with LLM reasoning)
- Conditional routing based on intent and state
- Visible in LangSmith Studio for debugging and monitoring
- Full execution tracing per node

See [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md) and [GRAPH_ARCHITECTURE.md](GRAPH_ARCHITECTURE.md) for detailed documentation.

## Project Structure

```
medassistai-langsmith/
├── chatbot.py / chatbot.bat          # Run chatbot
├── app.py                            # Streamlit UI
├── graph.py                          # Multi-node LangGraph workflow
├── agents.py                         # 6 agent implementations
├── agent_orchestrator.py             # Agent orchestration (legacy)
├── state.py                          # State models
├── config.py                         # Configuration
├── llm_setup.py                      # LLM setup
├── intent_detector.py                # Intent detection utilities
├── info_extractor.py                 # Information extraction utilities
├── date_time_parser.py               # Date/time parsing
├── response_generator.py             # Response generation utilities
├── patient_validator.py              # Patient validation utilities
├── rag_vector_db.py                  # Vector database
├── trello_tools.py                   # Trello integration
├── langsmith_debug.py                # LangSmith utilities
├── load_rag_data.py                  # Load data into vector DB
├── requirements.txt                  # Dependencies
├── MULTI_AGENT_ARCHITECTURE.md       # Agent design documentation
├── GRAPH_ARCHITECTURE.md             # Node structure documentation
├── MULTI_AGENT_README.md             # Usage guide
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

## Debugging

### View Multi-Agent Graph in LangSmith Studio

```bash
# Debug with LangSmith tracing
python debug.py
```

Then open [LangSmith Studio](https://smith.langchain.com) to see:
- **Multi-node graph visualization** - All 6 agents visible
- **Per-node execution** - See each agent's input/output
- **Conditional routing** - Watch smart routing in action
- **Full execution trace** - Detailed trace of entire workflow
- **Agent reasoning** - View LLM prompts and responses

The multi-agent architecture is fully integrated into LangSmith for complete visibility and debugging.

## Testing

### Test Scenarios

**Test new patient booking (creates appointment + registration ticket):**
```bash
python test_new_patient_booking.py
```
Use Patient ID: **P999** (not in database)

**Test fraud detection vs new patient logic:**
```bash
python test_fraud_vs_new_patient.py
```
Verifies:
- Deceased patients create fraud ticket only
- New patients create appointment + registration ticket

See [FRAUD_vs_NEW_PATIENT.md](FRAUD_vs_NEW_PATIENT.md) for implementation details.

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
