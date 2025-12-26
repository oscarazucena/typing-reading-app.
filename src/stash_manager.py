import sqlite3
import json
import os
from datetime import datetime

DB_FILE = os.path.join('data', 'stash.db')

def initialize_db():
    """
    Initializes the SQLite database and creates the necessary tables if they don't exist.
    """
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Drop tables to ensure a clean slate during development (for now)
    cursor.execute('DROP TABLE IF EXISTS books')
    cursor.execute('DROP TABLE IF EXISTS chapters')
    cursor.execute('DROP TABLE IF EXISTS typing_sessions')

    # Create books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            source_url TEXT UNIQUE NOT NULL
        )
    ''')

    # Create chapters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            chapter_url TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            chapter_number INTEGER, -- New column for ordering
            stashed_date TEXT NOT NULL,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')
    
    # Typing sessions table
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
            errors_json TEXT,
            FOREIGN KEY (chapter_id) REFERENCES chapters(id)
        )
    ''')

    conn.commit()
    conn.close()

def add_book(title: str, author: str, source_url: str) -> int:
    """
    Adds a new book to the database or retrieves the ID of an existing one.
    Returns the book's ID.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM books WHERE source_url = ?", (source_url,))
        result = cursor.fetchone()
        if result:
            return result[0]
        
        cursor.execute("INSERT INTO books (title, author, source_url) VALUES (?, ?, ?)", (title, author, source_url))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def add_chapter(book_id: int, title: str, chapter_url: str, content: str, chapter_number: int | None = None) -> int | None:
    """
    Adds a new chapter to a book.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        stashed_date = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO chapters (book_id, title, chapter_url, content, chapter_number, stashed_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (book_id, title, chapter_url, content, chapter_number, stashed_date))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"Chapter with URL {chapter_url} already exists.")
        return None
    finally:
        conn.close()

def get_chapter(chapter_id: int) -> dict | None:
    """
    Retrieves a single chapter by its ID.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, book_id, title, chapter_url, content, chapter_number, stashed_date FROM chapters WHERE id = ?', (chapter_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0], 'book_id': row[1], 'title': row[2], 'chapter_url': row[3],
            'content': row[4], 'chapter_number': row[5], 'stashed_date': row[6]
        }
    return None

def get_book(book_id: int) -> dict | None:
    """
    Retrieves a single book by its ID.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, author, source_url FROM books WHERE id = ?', (book_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'title': row[1], 'author': row[2], 'source_url': row[3]}
    return None

def list_books() -> list[dict]:
    """
    Lists all stashed books.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, author, source_url FROM books ORDER BY title')
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'title': r[1], 'author': r[2], 'source_url': r[3]} for r in rows]

def list_chapters_for_book(book_id: int) -> list[dict]:
    """
    Lists all chapters for a given book.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, chapter_url, chapter_number, stashed_date FROM chapters WHERE book_id = ? ORDER BY chapter_number ASC', (book_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'title': r[1], 'chapter_url': r[2], 'chapter_number': r[3], 'stashed_date': r[4]} for r in rows]

if __name__ == '__main__':
    initialize_db()
    print("Database initialized.")

    # Example usage for new book-centric schema
    print("\n--- Testing New Book/Chapter Functions ---")

    # Add a test book
    test_book_title = "Demon's Diary"
    test_book_author = "Fei Xiang"
    test_book_url = "https://novelbin.com/b/demons-diary"
    book_id = add_book(test_book_title, test_book_author, test_book_url)
    print(f"Added/retrieved Book ID: {book_id}")

    # Add chapters to this book
    add_chapter(book_id, "Chapter 1: The Beginning", f"{test_book_url}/chapter-1", "Content of chapter 1.", 1)
    add_chapter(book_id, "Chapter 2: The Journey", f"{test_book_url}/chapter-2", "Content of chapter 2.", 2)
    add_chapter(book_id, "Chapter 3: The Discovery", f"{test_book_url}/chapter-3", "Content of chapter 3.", 3)
    print("Added sample chapters.")

    # List all books
    print("\nAll Books:")
    books = list_books()
    for book in books:
        print(f"  ID: {book['id']}, Title: {book['title']}, Author: {book['author']}")

    # List chapters for a specific book
    if books:
        first_book_id = books[0]['id']
        print(f"\nChapters for ' {books[0]['title']} ':")
        chapters_of_book = list_chapters_for_book(first_book_id)
        for chapter in chapters_of_book:
            print(f"  ID: {chapter['id']}, Title: {chapter['title']}, Chapter Number: {chapter['chapter_number']}")

        # Get a specific chapter
        if chapters_of_book:
            first_chapter_id = chapters_of_book[0]['id']
            chapter_data = get_chapter(first_chapter_id)
            if chapter_data:
                print(f"\nRetrieved Chapter {chapter_data['chapter_number']}: {chapter_data['title']}")
                print(f"  Content snippet: {chapter_data['content'][:30]}...")
    
    print("\nDatabase operations tested.")

def log_typing_session(chapter_id: int, duration: float, correct_chars: int, incorrect_chars: int, total_errors: int, error_details: list) -> int | None:
    """
    Logs a completed typing session to the database.
    This function is intended to be called from the main application logic.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        from datetime import datetime, timedelta
        end_time = datetime.now()
        start_time = (end_time - timedelta(seconds=duration))

        from src.stats_tracker import calculate_wpm, calculate_accuracy
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
        print(f"Successfully logged session {session_id} to the database for chapter {chapter_id}.")
        return session_id
    except Exception as e:
        print(f"Error logging typing session to database: {e}")
        return None
    finally:
        conn.close()
