# MedAssistAI LangSmith Chatbot - Claude.md

## Project Overview

This is a conversational AI chatbot for doctor appointment booking, built with Streamlit, LangGraph, Google Gemini, and LangSmith tracing.

## Collaboration Guidelines

### Git & Commits
- **Do NOT commit changes automatically.** Only create commits when explicitly requested by the user.
- This preserves the user's control over version history and staging decisions.
- When asked to commit, review staged changes and create clear, descriptive commit messages.

### Code Changes
- Prioritize fixing bugs and implementing requested features
- Test changes in the running application before reporting completion
- Use the existing architectural patterns established in the codebase

### Testing
- For UI changes: start the dev server and manually test in browser
- Check for regressions in core functionality (chatbot responses, message history)
- Verify LangSmith tracing is working

## Project Structure

```
medassistai-langsmith/
├── app.py                    # Main Streamlit UI
├── graph.py                  # LangGraph workflow
├── state.py                  # Chat state models
├── config.py                 # Configuration (models, API keys)
├── llm_setup.py             # LLM initialization
├── intent_detector.py       # Intent detection module
├── info_extractor.py        # Information extraction
├── response_generator.py    # Response generation
├── appointment_manager.py   # Trello integration
├── start.bat                # Windows launch script
├── requirements.txt         # Dependencies
├── .env                     # Environment variables (local)
└── README.md               # Documentation
```

## Current LLM Setup

- **Model**: Google Gemini 3.6 Flash
- **Configuration**: Disabled sampling parameters (fixed defaults)
- **Response Format**: Dict with 'text' key for text content

## Known Patterns

### Response Parsing
The LLM returns responses as dicts with structure: `{'type': 'text', 'text': '...', 'extras': {...}}`
- Use `_extract_text()` helper from intent_detector.py to safely extract text
- Handles dict, list, and string response formats

### UI Layout
- Conversation takes full-width display
- Sidebar is minimal (only LangSmith info)
- Chat messages displayed via Streamlit's `chat_message()` component

## Development Commands

```bash
# Start application (Windows)
start.bat

# Start application (Linux/macOS)
streamlit run app.py

# Run tests
python -m pytest tests/
```

## Environment Variables Required

- `GOOGLE_API_KEY` - Google Gemini API key
- `LANGSMITH_API_KEY` - LangSmith tracing API key
- `LANGSMITH_ENDPOINT` - LangSmith endpoint (EU: https://eu.api.smith.langchain.com)
- `TRELLO_API_KEY`, `TRELLO_API_TOKEN`, `TRELLO_BOARD_APPOINTMENTS` - Trello integration
- `GOOGLE_DRIVE_LINK_*` - Doctor profile links
