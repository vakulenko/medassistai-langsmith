import os
from langsmith import Client
from config import LANGSMITH_API_KEY, LANGSMITH_ENDPOINT, LANGSMITH_PROJECT
from datetime import datetime

def _get_client():
    """Initialize and return LangSmith client."""
    # Set environment variables first
    os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGSMITH_ENDPOINT"] = LANGSMITH_ENDPOINT
    # Client reads from environment variables
    return Client()

# Initialize LangSmith client for debugging and tracing
client = _get_client()

def initialize_langsmith_tracing():
    """Initialize LangSmith tracing with project configuration."""
    os.environ["LANGSMITH_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGSMITH_ENDPOINT"] = LANGSMITH_ENDPOINT
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = LANGSMITH_PROJECT

def get_langsmith_client():
    """Get the LangSmith client for manual run creation and debugging."""
    return client

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
        print(f"[WARN] Failed to log to LangSmith: {str(e)}")

def get_langsmith_project_url():
    """Get the LangSmith Studio URL for the current project."""
    return f"https://smith.langchain.com/o/default/projects/p/{LANGSMITH_PROJECT}"

def list_recent_runs(limit: int = 10):
    """List recent runs in LangSmith for debugging."""
    try:
        runs = client.list_runs(
            project_name=LANGSMITH_PROJECT,
            limit=limit,
        )
        return list(runs)
    except Exception as e:
        print(f"[WARN] Failed to fetch runs from LangSmith: {str(e)}")
        return []

if __name__ == "__main__":
    initialize_langsmith_tracing()
    print(f"[OK] LangSmith initialized for project: {LANGSMITH_PROJECT}")
    print(f"[OK] Endpoint: {LANGSMITH_ENDPOINT}")
    print(f"[OK] Studio URL: {get_langsmith_project_url()}")
