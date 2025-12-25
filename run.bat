@echo off
REM This script activates the virtual environment and runs the main Python application.
REM It accepts an optional "debug" argument to enable logging.

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

REM Check for debug flag
set "DEBUG_FLAG="
IF /I "%1"=="debug" (
    set "DEBUG_FLAG=--debug"
    echo "Debug mode enabled. Logging to debug.log"
)

REM Run the main application
echo "Launching application..."
python main.py %DEBUG_FLAG%

echo "--- Application Closed ---"
pause
