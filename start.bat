@echo off
REM MedAssistAI Chatbot - Start Script
REM This script installs dependencies and runs the Streamlit app

cd /d "%~dp0"

echo.
echo ========================================
echo  MedAssistAI Chatbot - Starting...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/3] Installing/Updating dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Checking environment variables...
if not exist .env (
    echo WARNING: .env file not found
    echo Please create a .env file with the required API keys before running
    echo.
)

echo.
echo [3/3] Installing Streamlit specifically...
pip install streamlit

if errorlevel 1 (
    echo ERROR: Failed to install Streamlit
    pause
    exit /b 1
)

echo.
echo Starting Streamlit app...
echo.
echo The app will open at: http://localhost:8501
echo Press Ctrl+C to stop the server
echo.

python -m streamlit run app.py

pause
