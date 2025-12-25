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
- [x] **Task 2: NovelBin Scraper** - Create a module to extract text from a URL using `cloudscraper`.
- [x] **Task 3: Local "Stash" System** - Implement SQLite/JSON storage for stashed chapters.
- [x] **Task 4: Basic Typing Engine** - Develop CLI logic to compare user input vs. source text character-by-character.
- [x] **Task 5: Stats Tracker** - Log errors (Expected vs. Actual) and calculate WPM/Accuracy.
- [x] **Task 6: Gemini Drill Generator** - Integration to send error logs to Gemini and receive "practice sentences."
- [ ] **Task 7: Main GUI Application** - Create a `main.py` to integrate all modules into a functional graphical user interface using CustomTkinter.
- [ ] **Task 8: Create Startup Scripts** - Add `run.bat` for Windows and `run.sh` for Linux/macOS.