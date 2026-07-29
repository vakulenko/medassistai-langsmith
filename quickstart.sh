#!/bin/bash

echo "🏥 MedAssistAI Chatbot - Quick Start Setup"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

echo "✓ pip found"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate || . venv/Scripts/activate

echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "📚 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""

# Verify .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please create a .env file with the required API keys:"
    echo "  - GOOGLE_API_KEY"
    echo "  - LANGSMITH_API_KEY"
    echo "  - LANGSMITH_ENDPOINT"
    echo "  - TRELLO_API_KEY"
    echo "  - TRELLO_API_TOKEN"
    exit 1
fi

echo "✓ .env file found"
echo ""

# Run tests
echo "🧪 Running tests..."
python3 test_graph.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup complete! You're ready to go!"
    echo ""
    echo "🚀 To start the chatbot, run:"
    echo "   streamlit run app.py"
    echo ""
    echo "📊 View LangSmith traces:"
    echo "   https://smith.langchain.com"
else
    echo "⚠️  Tests failed, but setup completed. Check .env and API keys."
fi
