"""LangSmith integration for tracing."""
import os
from langsmith import Client
from config import LANGSMITH_API_KEY, LANGSMITH_ENDPOINT, LANGSMITH_PROJECT
from datetime import datetime

def _get_client():
    """Initialize and return LangSmith client."""
    os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGSMITH_ENDPOINT"] = LANGSMITH_ENDPOINT
    return Client()

client = _get_client()

def initialize_langsmith_tracing():
    """Initialize LangSmith tracing."""
    os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGSMITH_ENDPOINT"] = LANGSMITH_ENDPOINT
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT

def get_langsmith_project_url():
    """Get the LangSmith Studio URL for the current project."""
    return f"https://smith.langchain.com/o/default/projects/p/{LANGSMITH_PROJECT}"

def log_agent_run(session_id: str, intent: str, success: bool, error: str = None):
    """Log agent execution to LangSmith for debugging."""
    try:
        metadata = {
            "session_id": session_id,
            "intent": intent,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }
        if error:
            metadata["error"] = error

        client.create_run(
            name=f"agent_execution",
            run_type="agent",
            inputs={"session_id": session_id, "intent": intent},
            outputs={"success": success},
            metadata=metadata,
        )
    except Exception as e:
        pass  # Silently fail - tracing is optional
