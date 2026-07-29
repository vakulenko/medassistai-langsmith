# MedAssistAI Chatbot - Doctor Appointment Booking

A conversational AI chatbot for booking doctor appointments, built with **Streamlit**, **LangGraph**, **Google Gemini**, and **LangSmith Studio**.

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
   ```

3. **Setup RAG (optional):**
   ```bash
   python load_rag_data.py
   ```
   See [RAG_SETUP.md](RAG_SETUP.md) for configuration.

### Run Chatbot

```bash
chatbot.bat
```

Opens at **http://localhost:8501**

### Debug Mode

```bash
debug.bat
```

Opens development server for real-time debugging with LangSmith Studio.

## Features

- 🤖 **Conversational Booking** - Intent detection and natural language understanding
- 👨‍⚕️ **Multiple Doctors** - Support for multiple doctor profiles
- 📋 **Session Management** - Create, switch, and delete independent chat sessions
- 🔍 **LangSmith Integration** - Real-time tracing, monitoring, and debugging
- 📝 **Appointment Tracking** - Store bookings in Trello (optional)
- 📚 **RAG Context** - Google Drive integration for context-aware responses

## Architecture

```
Google Drive
    ↓
Google Drive MCP (google_drive_mcp.py)
    ↓ Downloads doctor profiles & patient data
RAG Vector DB (rag_vector_db.py)
    ↓ Semantic search with Chroma
    ↓
Streamlit UI (app.py)
    ↓
LangGraph Agent (graph.py)
├── Intent Detection
├── Information Extraction
├── Response Generation (injected with RAG context)
└── Appointment Confirmation
    ↓
LangSmith Tracing
    ↓
Trello Integration (optional)
```

## Project Structure

```
medassistai-langsmith/
├── debug.py / debug.bat              # Start with LangSmith Studio
├── chatbot.py / chatbot.bat          # Start regular chatbot
├── app.py                            # Streamlit UI
├── graph.py                          # LangGraph agent
├── state.py                          # State models & session management
├── config.py                         # Configuration
├── llm_setup.py                      # LLM initialization
├── intent_detector.py                # Intent detection
├── info_extractor.py                 # Information extraction
├── response_generator.py             # Response generation
├── langsmith_debug.py                # LangSmith utilities
├── google_drive_mcp.py               # Google Drive integration
├── rag_vector_db.py                  # Vector database & RAG
├── load_rag_data.py                  # Load Google Drive data into vector DB
├── setup_google_drive.py             # Google Drive authentication setup
├── test_rag.py                       # RAG system tests
├── RAG_SETUP.md                      # Detailed RAG setup guide
├── langgraph.json                    # LangGraph config
├── requirements.txt                  # Dependencies
└── .vector_db/                       # Chroma vector database (auto-created)
```

## Development

### With LangSmith Studio (Recommended)

```bash
debug.bat
```

Then open https://smith.langchain.com to:
- Test your agent in the playground
- View real-time execution traces
- Monitor LLM calls and responses
- Debug intent detection and extraction
- See hot-reload as you edit code

### Without Studio

```bash
chatbot.bat
```

Conversations are still traced to LangSmith Cloud automatically.

## Session Management

In the Streamlit UI:
- **Create Session**: Enter name and click ➕ New
- **Switch Session**: Use dropdown to switch between sessions
- **Delete Session**: Click 🗑️ to delete current session

Each session maintains its own conversation history and context.

## Configuration

### RAG with Google Drive

Configure in `.env`:

```env
GOOGLE_API_KEY=your_key

# Google Drive shared links
GOOGLE_DRIVE_LINK_DR_WILLI_BEDNA=https://drive.google.com/file/d/.../view
GOOGLE_DRIVE_LINK_DR_TERRY_KLOCK=https://drive.google.com/file/d/.../view
GOOGLE_DRIVE_LINK_DR_JACKI_SENGE=https://drive.google.com/file/d/.../view
GOOGLE_DRIVE_LINK_DR_DALLA_MCDER=https://drive.google.com/file/d/.../view
GOOGLE_DRIVE_LINK_PATIENT_DATA=https://drive.google.com/file/d/.../view
```

See [RAG_SETUP.md](RAG_SETUP.md) for details.

### Optional Trello Integration

```env
TRELLO_API_KEY=your_key
TRELLO_API_TOKEN=your_token
TRELLO_BOARD_APPOINTMENTS=board_id
```

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: Google Gemini 3.6 Flash
- **Orchestration**: LangGraph
- **Tracing**: LangSmith Studio
- **RAG**: Chroma vector database with Google Gemini embeddings
- **Data Source**: Google Drive with PDF/DOCX/PPTX support
- **Integration**: Trello API, Google Drive MCP

## Troubleshooting

### LangSmith Not Tracing
- Verify `LANGSMITH_API_KEY` in `.env`
- Check internet connection

### Gemini API Errors
- Verify `GOOGLE_API_KEY` is valid
- Check API quotas in Google Cloud

### Scripts Won't Start
- Verify `.env` file exists
- Run: `pip install -r requirements.txt`
- Check Python 3.11+ installed

## Support

1. Check LangSmith logs for error traces
2. Review conversation history in the UI
3. Verify environment variables are set correctly

## License

MIT License
