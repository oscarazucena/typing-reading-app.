@echo off
REM This script activates the virtual environment and runs the main Python application.

echo "--- Starting Typing Practice App ---"

REM Check if the virtual environment directory exists
IF NOT EXIST .venv (
    echo "Virtual environment not found. Please run 'python -m venv .venv' to create it."
    pause
    exit /b
)

REM Activate the virtual environment
echo "Activating virtual environment..."
call .\.venv\Scripts\activate

REM Run the main application
echo "Launching application..."
python main.py

echo "--- Application Closed ---"
pause
