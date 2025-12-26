# Typing App - Project Manual

## 🎯 Project Overview
A local-first Python application for practicing typing using scraped novel content (NovelBin) and user-uploaded PDFs.

## 🛠 Tech Stack
- **Language:** Python 3.10+
- **Scraping:** cloudscraper, BeautifulSoup
- **Database:** SQLite (local-first)
- **UI:** CustomTkinter
- **AI Integration:** Gemini CLI for code gen and error drills.

## 📜 Coding Rules & Conventions
- **Modularity:** Keep scrapers separate from the typing engine logic.
- **Safety:** Always include rate-limiting (time.sleep) in scrapers.
- **Data Format:** Use JSON for "stashed" content to ensure future mobile compatibility.
- **Commit Messages:** Follow Conventional Commits (e.g., `feat:`, `fix:`, `docs:`).

## 🚀 Roadmap & Task List
- [x] **Task 1: Project Setup** - Initialize git, create virtualenv, and set up folder structure.
- [x] **Task 2: Main GUI Application** - Create a `main.py` to integrate all modules into a functional graphical user interface using CustomTkinter.
- [x] **Task 3: Stats Tracker & DB Logging** - Log errors, WPM, and accuracy. Implemented detailed error tracking and session logging to the database.
- [x] **Task 4: NovelBin Scraper** - Create a module to extract text from a URL and integrate it into the UI.
- [x] **Task 5: Local "Stash" System** - Implement SQLite/JSON storage for stashed chapters, accessible from the UI.
- [x] **Task 6: Stashed Chapters UI** - Build a UI component to list and load stashed chapters from the database.
- [ ] **Task 7: Gemini Drill Generator** - Integration to send error logs to Gemini and receive "practice sentences."
- [ ] **Task 8: Create Cross-Platform Startup Scripts** - Add `run.sh` for Linux/macOS compatibility.

## ⚠️ Development Notes & Issues
- **Database Initialization:** Encountered and fixed an `sqlite3.OperationalError` caused by attempting to execute multiple `CREATE TABLE` statements in a single `cursor.execute()` call. The fix was to separate each SQL statement into its own `execute()` call.
- **Web Scraper Brittleness:** The NovelBin scraper failed multiple times due to changes in the website's HTML structure. The initial CSS class selector (`chapter-content`) was too generic. The issue was resolved by using a much more specific and stable ID selector (`chr-content`), which successfully isolated the chapter text.
- **Git Commit Message Formatting:** Ran into issues with multi-line commit messages using `git commit -m "..." -m "..."`. The shell misinterpreted parts of the message body as file paths. This was resolved by formatting the entire multi-line body as a single string literal with escaped newlines (`\n`) and quotes.