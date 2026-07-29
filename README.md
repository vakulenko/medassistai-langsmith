# MedAssistAI Chatbot - Doctor Appointment Booking System

A conversational AI chatbot built with **Streamlit**, **LangGraph**, and **Google Gemini** that helps patients book doctor appointments. Built with **LangSmith Studio** integration for real-time debugging and monitoring.

## Quick Start

### Option 1: Debug with LangSmith Studio (Development)

Start the development server with full debugging capabilities:

```bash
python debug.py
# or on Windows:
debug.bat
```

Then open **https://smith.langchain.com** to test your agent with real-time tracing.

### Option 2: Run the Chatbot (Production/Regular Use)

Start the Streamlit chatbot interface:

```bash
python chatbot.py
# or on Windows:
chatbot.bat
```

Opens at **http://localhost:8501**

**Note:** Conversations are still traced to LangSmith Cloud automatically.

## Features

✨ **Core Features**
- 🤖 Conversational appointment booking with intent detection
- 👨‍⚕️ Support for multiple doctors
- 📅 Date and time selection
- 👤 Patient information collection
- ✅ Appointment confirmation
- 📝 Trello integration for appointment management

✨ **Session Management**
- 📋 Create multiple independent chat sessions
- 🔄 Switch between sessions instantly
- 🗑️ Delete sessions
- 💾 Each session maintains its own context

✨ **LangSmith Integration**
- 🔍 Real-time tracing with LangSmith Studio
- 📊 Monitor intent detection, info extraction, response generation
- 🐛 Debug LLM calls and agent execution
- 🔥 Hot-reload support for development

## Architecture

```
User Input
    ↓
Streamlit UI
    ↓
LangGraph Workflow
├── Intent Detection (What does the user want?)
├── Information Extraction (What info do we have?)
├── Response Generation (What should we say?)
└── Appointment Confirmation
    ↓
LangSmith Trace (Monitoring & Debugging)
    ↓
Trello (Appointment Storage)
```

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: Google Gemini 3.6 Flash
- **Orchestration**: LangGraph
- **Tracing**: LangSmith
- **Backend Integration**: Trello API, Google Drive

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file with required API keys:

```env
# Google Gemini API
GOOGLE_API_KEY=your_api_key

# LangSmith (for tracing and studio)
LANGSMITH_API_KEY=your_api_key
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com

# Trello (optional - for appointment storage)
TRELLO_API_KEY=your_key
TRELLO_API_TOKEN=your_token
TRELLO_BOARD_APPOINTMENTS=board_id

# Doctor Profiles (optional - Google Drive links)
GOOGLE_DRIVE_LINK_DR_WILLI_BEDNA=link
GOOGLE_DRIVE_LINK_DR_TERRY_KLOCK=link
GOOGLE_DRIVE_LINK_DR_JACKI_SENGE=link
GOOGLE_DRIVE_LINK_DR_DALLA_MCDER=link
```

### 3. Run with LangSmith Studio (Recommended for Development)

```bash
python debug.py
```

This starts the development server with LangSmith Studio integration at http://127.0.0.1:2024

Then open https://smith.langchain.com to test your agent in real-time.

### 4. Run the Streamlit Chatbot

In a separate terminal:

```bash
streamlit run app.py
```

Opens at http://localhost:8501

## Project Structure

```
medassistai-langsmith/
├── app.py                 # Main Streamlit application
├── graph.py              # LangGraph workflow definition
├── state.py              # Chat state and data models
├── config.py             # Configuration management
├── llm_setup.py          # LLM initialization with LangSmith
├── intent_detector.py    # Intent detection module
├── info_extractor.py     # Information extraction from messages
├── response_generator.py # Response generation
├── appointment_manager.py # Trello integration
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
└── README.md            # This file
```

## Usage Examples

### Book an Appointment
```
User: "I'd like to book an appointment with Dr. Willi Bedna"
Bot: [Detects booking intent, asks for required info]
User: "My name is John Doe, email is john@example.com, next Monday at 2 PM"
Bot: [Confirms appointment details and books it]
```

### View Available Doctors
```
User: "Show me available doctors"
Bot: [Lists all doctors and their profiles]
```

### Check Appointment Details
```
User: "When is my appointment?"
Bot: [Retrieves and displays appointment information]
```

### Using Session Management

**Create a New Session:**
1. In the sidebar, enter a session name (e.g., "Dr. Appointment 1")
2. Click the "➕ New" button
3. A fresh session is created with empty conversation history

**Switch Between Sessions:**
1. Use the "Switch session" dropdown in the sidebar
2. Sessions show their name and creation time
3. Switching instantly loads that session's conversation history

**Delete a Session:**
1. Navigate to the session you want to delete
2. Click "🗑️ Delete Current Session" button
3. (The button is disabled if it's the last remaining session)

## LangSmith Studio Integration

The chatbot uses **LangSmith Studio** for real-time debugging and monitoring.

### Development: Debug Mode

For development and debugging, use debug mode which connects directly to LangSmith Studio:

```bash
python debug.py
```

Then open https://smith.langchain.com to:
- Test your agent in real-time
- Watch LLM calls and responses
- Monitor intent detection and info extraction
- See hot-reloading as you edit code
- Debug agent execution step-by-step

### Production: Conversation Traces

All conversations are automatically traced in LangSmith Cloud:
- Every user message is logged with context
- Intent detection results are captured
- LLM calls and responses are recorded
- Session-based filtering for easy analysis
- Full execution traces for debugging

## Workflow Details

### 1. Intent Detection
Analyzes user input to determine their intent:
- `book_appointment` - User wants to book
- `view_doctors` - User wants doctor list
- `check_availability` - User checking schedules
- `cancel_appointment` - User wants to cancel
- `general_info` - General questions

### 2. Information Extraction
Extracts structured data from conversation:
- Patient name and email
- Doctor preference
- Preferred date and time
- Reason for visit

### 3. Response Generation
Generates contextual responses:
- Confirms collected information
- Asks for missing details
- Suggests alternatives
- Confirms bookings

## Error Handling

The system handles:
- Invalid date/time formats
- Missing required information
- LLM API failures
- Trello connection issues
- Invalid doctor selections

## Performance Considerations

- **LLM Calls**: Each user message triggers multiple LLM calls (intent detection, extraction, response)
- **Token Usage**: Optimized prompts to minimize token consumption
- **Caching**: Conversation history maintained for context (last 3 messages)
- **Latency**: ~2-5 seconds per response depending on LLM latency

## Testing

To test the application locally:

```python
python -m pytest tests/
```

## Contributing

1. Create a feature branch
2. Make changes following the existing code style
3. Test thoroughly with LangSmith monitoring
4. Submit a pull request

## Key Updates

- **LangSmith Studio Integration**: Full debugging support with `debug.py` script
- **Session Management**: Multiple independent chat sessions with isolated contexts
- **LangGraph-based Agent**: Built with official LangChain patterns for maintainability
- **Hot-reload Support**: Edit code and changes appear instantly in Studio
- **Official Setup**: Follows LangChain's recommended LangGraph CLI approach

## Future Enhancements

- [ ] Real-time doctor availability calendar
- [ ] SMS/Email appointment confirmations
- [ ] Payment integration
- [ ] Multi-language support
- [ ] Appointment reminders
- [ ] Medical history integration
- [ ] Insurance verification

## Troubleshooting

### LangSmith Not Tracing
- Verify `LANGSMITH_API_KEY` is set correctly
- Check `LANGSMITH_TRACING=true` in environment
- Ensure internet connection to LangSmith

### Gemini API Errors
- Verify `GOOGLE_API_KEY` is valid
- Check API quotas in Google Cloud Console
- Ensure gemini-3.6-flash is available in your region

### Trello Integration Issues
- Verify `TRELLO_API_KEY` and `TRELLO_API_TOKEN`
- Check board ID is correct
- Ensure API token has necessary permissions

## License

MIT License - feel free to use this project!

## Support

For issues and questions:
1. Check LangSmith logs for detailed error traces
2. Review conversation history in the UI
3. Check environment variables are correctly set
