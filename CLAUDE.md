# MedAssistAI Chatbot - Project Guidelines

## Overview

Educational chatbot for doctor appointment booking using Streamlit, LangGraph, Gemini, and LangSmith Studio.

## Collaboration Guidelines

**Git & Commits:**
- No automatic commits. Only on explicit request.
- Review staged changes before committing.
- Write clear, descriptive commit messages.

**Code Changes:**
- Fix bugs and implement features using existing patterns.
- Test UI changes in running app before reporting completion.
- Keep code simple and readable (educational example).

**Documentation:**
- Keep README.md focused and under 400 lines.
- Link between docs instead of duplicating.
- Use clear, concise language.

## Quick Start

```bash
# Debug with LangSmith Studio (development)
debug.bat

# Run chatbot (regular use)
chatbot.bat
```

See README.md for details.

## Project Structure

```
medassistai-langsmith/
├── debug.py / debug.bat      # LangSmith Studio debugging
├── chatbot.py / chatbot.bat  # Streamlit chatbot UI
├── app.py                    # Streamlit application
├── graph.py                  # LangGraph agent
├── state.py                  # State models & sessions
├── config.py                 # Configuration
├── llm_setup.py              # LLM setup
├── intent_detector.py        # Intent detection
├── info_extractor.py         # Info extraction
├── response_generator.py     # Response generation
├── langsmith_debug.py        # LangSmith utilities
├── langgraph.json            # LangGraph config
└── requirements.txt          # Dependencies
```

## Key Technologies

- **Frontend**: Streamlit
- **Agent**: LangGraph
- **LLM**: Google Gemini 3.6 Flash
- **Tracing**: LangSmith Studio
- **Integration**: Trello, Google Drive

## Environment Variables

Required:
- `GOOGLE_API_KEY` - Gemini API
- `LANGSMITH_API_KEY` - LangSmith tracing

Optional:
- `TRELLO_*` - Appointment storage
- `GOOGLE_DRIVE_LINK_*` - Doctor profiles

## Session Management

- Sessions stored in Streamlit state
- Each session has isolated chat history
- Create, switch, delete via UI
- Safe delete (can't delete last session)

## Development

Use `debug.bat` for development with:
- Real-time LangSmith Studio tracing
- Hot-reload on code changes
- Full agent execution visualization
