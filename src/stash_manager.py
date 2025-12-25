import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_FILE = os.path.join('data', 'stash.db')

def initialize_db():
    """
    Initializes the SQLite database and creates the chapters table if it doesn't exist.
    """
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            chapter_url TEXT UNIQUE NOT NULL,
            content JSON NOT NULL,
            stashed_date TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS typing_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id INTEGER,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration REAL NOT NULL,
            correct_chars INTEGER NOT NULL,
            incorrect_chars INTEGER NOT NULL,
            total_chars INTEGER NOT NULL,
            wpm REAL NOT NULL,
            accuracy REAL NOT NULL,
            errors_json JSON,
            FOREIGN KEY (chapter_id) REFERENCES chapters(id)
        )
    ''')
    conn.commit()
    conn.close()

def add_chapter(title: str, author: str, chapter_url: str, content: str) -> int | None:
    """
    Adds a new chapter to the stash.
    The content is stored as a JSON string.
    Returns the ID of the newly added chapter or None if an error occurred.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        content_json = json.dumps({'text': content})
        stashed_date = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO chapters (title, author, chapter_url, content, stashed_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, author, chapter_url, content_json, stashed_date))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"Error: Chapter with URL {chapter_url} already exists.")
        return None
    except Exception as e:
        print(f"Error adding chapter: {e}")
        return None
    finally:
        conn.close()

def get_chapter(chapter_id: int) -> dict | None:
    """
    Retrieves a chapter by its ID.
    Returns a dictionary containing chapter data or None if not found.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, author, chapter_url, content, stashed_date FROM chapters WHERE id = ?', (chapter_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        chapter_data = {
            'id': row[0],
            'title': row[1],
            'author': row[2],
            'chapter_url': row[3],
            'content': json.loads(row[4])['text'],
            'stashed_date': row[5]
        }
        return chapter_data
    return None

def list_chapters() -> list[dict]:
    """
    Lists all stashed chapters.
    Returns a list of dictionaries, each containing chapter overview data.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, author, chapter_url, stashed_date FROM chapters ORDER BY stashed_date DESC')
    rows = cursor.fetchall()
    conn.close()
    chapters_list = []
    for row in rows:
        chapters_list.append({
            'id': row[0],
            'title': row[1],
            'author': row[2],
            'chapter_url': row[3],
            'stashed_date': row[4]
        })
    return chapters_list

def log_typing_session(chapter_id: int, duration: float, correct_chars: int, incorrect_chars: int, total_errors: int, error_details: list) -> int | None:
    """
    Logs a completed typing session to the database, including detailed error analysis.
    """
    from src.stats_tracker import calculate_wpm, calculate_accuracy
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        end_time = datetime.now()
        start_time = (end_time - timedelta(seconds=duration))
        
        wpm = calculate_wpm(correct_chars, duration)
        accuracy = calculate_accuracy(correct_chars, total_errors)
        errors_json = json.dumps(error_details)
        
        cursor.execute('''
            INSERT INTO typing_sessions (chapter_id, start_time, end_time, duration, 
                                         correct_chars, incorrect_chars, total_chars, wpm, accuracy, errors_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (chapter_id, start_time.isoformat(), end_time.isoformat(), duration,
              correct_chars, incorrect_chars, (correct_chars + incorrect_chars), wpm, accuracy, errors_json))
        
        conn.commit()
        session_id = cursor.lastrowid
        print(f"Successfully logged session {session_id} for chapter {chapter_id}.")
        return session_id
    except Exception as e:
        print(f"Error logging typing session: {e}")
        return None
    finally:
        conn.close()

if __name__ == '__main__':
    initialize_db()
    print("Database initialized.")

    # Example usage
    test_title = "The Author's POV - Chapter 1"
    test_author = "Unknown"
    test_url = "https://www.novelbin.org/novel/the-authors-pov-novel/chapter-1.html"
    test_content = "This is the content of the first chapter."

    print(f"Adding chapter: {test_title}")
    chapter_id = add_chapter(test_title, test_author, test_url, test_content)
    if chapter_id:
        print(f"Chapter added with ID: {chapter_id}")

        # Simulate logging a session
        log_typing_session(
            chapter_id=chapter_id,
            duration=60.5,
            correct_chars=len(test_content),
            incorrect_chars=2,
            total_errors=5,
            error_details=[
                {'expected': 'c', 'actual': 'x', 'position': 10},
                {'expected': 'f', 'actual': 'd', 'position': 20}
            ]
        )

        retrieved_chapter = get_chapter(chapter_id)
        if retrieved_chapter:
            print("\nRetrieved Chapter:")
            print(f"  ID: {retrieved_chapter['id']}")
            print(f"  Title: {retrieved_chapter['title']}")
            print(f"  Content (first 100 chars): {retrieved_chapter['content'][:100]}...")
        
        print("\nAll Stashed Chapters:")
        all_chapters = list_chapters()
        for chapter in all_chapters:
            print(f"  ID: {chapter['id']}, Title: {chapter['title']}")
    
    # Attempt to add the same chapter again to test IntegrityError
    print(f"\nAttempting to add duplicate chapter: {test_title}")
    duplicate_chapter_id = add_chapter(test_title, test_author, test_url, test_content)
    if duplicate_chapter_id is None:
        print("Duplicate chapter was not added as expected.")
