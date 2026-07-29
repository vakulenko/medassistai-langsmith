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
   GOOGLE_API_KEY=your_key
   LANGSMITH_API_KEY=your_key
   LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
   ```

### Run Chatbot

```bash
chatbot.bat
# or: python chatbot.py
```

Opens at **http://localhost:8501**

### Debug with LangSmith Studio (Development)

```bash
debug.bat
# or: python debug.py
```

Opens development server at **http://127.0.0.1:2024**

Then visit **https://smith.langchain.com** to test and debug your agent in real-time.

## Features

- 🤖 **Conversational Booking** - Intent detection and natural language understanding
- 👨‍⚕️ **Multiple Doctors** - Support for multiple doctor profiles
- 📋 **Session Management** - Create, switch, and delete independent chat sessions
- 🔍 **LangSmith Integration** - Real-time tracing, monitoring, and debugging
- 📝 **Appointment Tracking** - Store bookings in Trello (optional)
- 🔥 **Hot-Reload** - Edit code and see changes instantly in Studio

## Architecture

```
Streamlit UI (app.py)
    ↓
LangGraph Agent (graph.py)
├── Intent Detection
├── Information Extraction
├── Response Generation
└── Appointment Confirmation
    ↓
LangSmith Tracing
    ↓
Trello Integration (optional)
```

## Project Structure

```
medassistai-langsmith/
├── debug.py / debug.bat           # Start with LangSmith Studio
├── chatbot.py / chatbot.bat       # Start regular chatbot
├── app.py                         # Streamlit UI
├── graph.py                       # LangGraph agent
├── state.py                       # State models & session management
├── config.py                      # Configuration
├── llm_setup.py                   # LLM initialization
├── intent_detector.py             # Intent detection
├── info_extractor.py              # Information extraction
├── response_generator.py          # Response generation
├── langsmith_debug.py             # LangSmith utilities
├── langgraph.json                 # LangGraph config
└── requirements.txt               # Dependencies
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

Optional features in `.env`:

```env
# Trello integration (optional)
TRELLO_API_KEY=your_key
TRELLO_API_TOKEN=your_token
TRELLO_BOARD_APPOINTMENTS=board_id

# Doctor profiles (optional)
GOOGLE_DRIVE_LINK_DR_WILLI_BEDNA=link
GOOGLE_DRIVE_LINK_DR_TERRY_KLOCK=link
GOOGLE_DRIVE_LINK_DR_JACKI_SENGE=link
GOOGLE_DRIVE_LINK_DR_DALLA_MCDER=link
```

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: Google Gemini 3.6 Flash
- **Orchestration**: LangGraph
- **Tracing**: LangSmith Studio
- **Integration**: Trello API, Google Drive

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
