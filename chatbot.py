#!/usr/bin/env python
"""
MedAssistAI - Streamlit Chatbot

This script starts the Streamlit chatbot application for regular use
(without LangSmith Studio debugging).

Usage:
    python chatbot.py

The chatbot will open at http://localhost:8501

Note: Conversations are still traced to LangSmith Cloud automatically.
For debugging with LangSmith Studio, use: python debug.py
"""

import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

def main():
    print("=" * 70)
    print("MedAssistAI Chatbot")
    print("=" * 70)
    print()

    # Load environment
    load_dotenv()

    # Check requirements
    print("Checking requirements...")

    if not Path(".env").exists():
        print("✗ ERROR: .env file not found")
        print("Please create .env with your API keys")
        sys.exit(1)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("✗ ERROR: GOOGLE_API_KEY not set in .env")
        sys.exit(1)

    print("✓ .env configured")
    print("✓ GOOGLE_API_KEY set")

    if not Path("app.py").exists():
        print("✗ ERROR: app.py not found")
        sys.exit(1)

    print("✓ app.py found")
    print()

    print("=" * 70)
    print("Starting Streamlit Chatbot")
    print("=" * 70)
    print()
    print("Opening at: http://localhost:8501")
    print()
    print("Features:")
    print("  • Chat with the appointment booking agent")
    print("  • Manage multiple chat sessions")
    print("  • Traces sent to LangSmith Cloud automatically")
    print()
    print("For debugging with LangSmith Studio, use: python debug.py")
    print()
    print("Press Ctrl+C to stop the chatbot")
    print()
    print("-" * 70)
    print()

    try:
        # Start Streamlit app
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app.py"],
            check=False
        )
    except KeyboardInterrupt:
        print()
        print("Chatbot stopped")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
