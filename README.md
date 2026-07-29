# MedAssistAI Chatbot - Doctor Appointment Booking System

A conversational AI chatbot built with **Streamlit**, **LangGraph**, and **Google Gemini** that helps patients book doctor appointments. All conversations are traced and monitored using **LangSmith**.

## Features

✨ **Core Features**
- 🤖 Conversational appointment booking with intent detection
- 👨‍⚕️ Support for multiple doctors
- 📅 Date and time selection
- 👤 Patient information collection
- ✅ Appointment confirmation
- 📝 Trello integration for appointment management
- 🔍 LangSmith tracing for all conversations

✨ **Session Management**
- 📋 Create multiple independent chat sessions
- 🔄 Switch between sessions instantly
- 🗑️ Delete sessions (with safety—cannot delete the last session)
- 💾 Each session maintains its own conversation history and context

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

Create a `.env` file (or verify your existing one contains):

```env
# Google Gemini API
GOOGLE_API_KEY=your_google_api_key

# LangSmith
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
LANGSMITH_TRACING=true

# Trello (for appointment storage)
TRELLO_API_KEY=your_trello_api_key
TRELLO_API_TOKEN=your_trello_token
TRELLO_BOARD_APPOINTMENTS=board_id

# Doctor Profiles (Google Drive links)
GOOGLE_DRIVE_LINK_DR_WILLI_BEDNA=link
GOOGLE_DRIVE_LINK_DR_TERRY_KLOCK=link
GOOGLE_DRIVE_LINK_DR_JACKI_SENGE=link
GOOGLE_DRIVE_LINK_DR_DALLA_MCDER=link

# Patient Data
GOOGLE_DRIVE_LINK_PATIENT_DATA=link
```

### 3. Run the Application

**Windows:**
```bash
start.bat
```

**Linux/macOS:**
```bash
streamlit run app.py
```

The chatbot will be available at `http://localhost:8501`

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

## LangSmith Integration

All conversations are automatically traced in LangSmith for:
- **Debugging**: View the exact LLM calls, prompts, and responses
- **Monitoring**: Track conversation metrics and performance
- **Quality Assurance**: Review conversations for improvement

### Access LangSmith Dashboard
1. Go to https://smith.langchain.com
2. Navigate to the "medassistai-chatbot" project
3. View traces, metrics, and conversation history

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

## Recent Changes

- **Session Management**: Added ability to create, switch, and delete chat sessions with independent contexts
- Updated LLM model from Gemini 1.5 Pro to Gemini 3.6 Flash for improved performance and cost efficiency
- Fixed response parsing to handle Gemini's response format (dict with 'text' key)
- Simplified UI: removed sidebar sections (Available Doctors, How It Works)
- Made conversation interface full-width for better UX
- Added `start.bat` script for easy Windows application launch

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
