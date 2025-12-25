# Typing Practice Application

This is a local-first Python application designed for practicing typing using scraped novel content and user-uploaded PDFs. It features a modern graphical user interface (GUI) built with CustomTkinter, offering real-time feedback, WPM and accuracy statistics, and customizable themes.

## Features
- **Interactive Typing Tests:** Practice typing with immediate character-by-character feedback and highlighting for correct and incorrect inputs.
- **Real-time Statistics:** View your Words Per Minute (WPM) and typing accuracy as you type.
- **Theme Switching:** Toggle between light and dark modes for a comfortable typing experience.
- **Content Management (Planned):** Scrape novel chapters from NovelBin and stash them locally (currently implemented in backend modules).
- **Error Drills (Planned):** Integration with Gemini CLI to generate practice sentences based on typing errors (currently implemented in backend modules).

## Getting Started

### Prerequisites
Ensure you have Python 3.10+ installed.

### Installation
1. Clone the repository:
   `git clone <repository_url>`
   `cd typing-reading-app`

2. Create and activate a virtual environment (recommended):
   `python -m venv .venv`
   `./.venv/Scripts/activate` (on Windows)
   `source ./.venv/bin/activate` (on macOS/Linux)

3. Install the required dependencies:
   `pip install -r requirements.txt`

### Running the Application
To start the GUI application, simply run the appropriate script for your operating system:

- **On Windows:** Double-click the `run.bat` file, or run it from your terminal:
  ```
  .\run.bat
  ```

- **On macOS/Linux:** (Coming Soon)

Alternatively, you can run the application manually after activating the virtual environment:
   `python main.py`

## For Developers

### Project Roadmap and Task Management
Refer to `GEMINI.md` for the detailed project roadmap, current task list, and architectural overview. This file is actively updated to reflect development progress and future plans.

### Contributing and GitHub Workflow
All development tasks and progress are tracked in `GEMINI.md`. Please consult this file for guidelines on contributing, including commit message conventions (Conventional Commits) and the overall development strategy.
