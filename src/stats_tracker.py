import sqlite3
import json
from datetime import datetime
import os

# Assuming DB_FILE is defined in stash_manager, so we reuse it or define it here if stats_tracker is standalone.
# For now, let's import or redefine it to ensure stats_tracker can connect.
DB_FILE = os.path.join('data', 'stash.db')

def calculate_wpm(correct_chars: int, duration_seconds: float) -> float:
    """
    Calculates Words Per Minute (WPM) based on correct characters and duration.
    Assumes an average of 5 characters per word.
    """
    if duration_seconds <= 0:
        return 0.0
    words_typed = correct_chars / 5
    wpm = (words_typed / duration_seconds) * 60
    return wpm

def calculate_accuracy(correct_chars: int, total_chars: int) -> float:
    """
    Calculates typing accuracy as a percentage.
    """
    if total_chars <= 0:
        return 0.0
    accuracy = (correct_chars / total_chars) * 100
    return accuracy

def log_typing_session(chapter_id: int, errors: list, duration: float, 
                       correct_chars: int, incorrect_chars: int, total_chars: int) -> int | None:
    """
    Logs a typing session's results to the database.
    Returns the session_id of the logged session or None if an error occurred.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        start_time = (datetime.now() - datetime.timedelta(seconds=duration)).isoformat() # Estimate start time
        end_time = datetime.now().isoformat()
        wpm = calculate_wpm(correct_chars, duration)
        accuracy = calculate_accuracy(correct_chars, total_chars)
        errors_json = json.dumps(errors)

        cursor.execute("""
            INSERT INTO typing_sessions (
                chapter_id, start_time, end_time, duration, 
                correct_chars, incorrect_chars, total_chars, wpm, accuracy, errors_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chapter_id, start_time, end_time, duration,
            correct_chars, incorrect_chars, total_chars, wpm, accuracy, errors_json
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error logging typing session: {e}")
        return None
    finally:
        conn.close()

def get_session_stats(session_id: int) -> dict | None:
    """
    Retrieves statistics for a specific typing session by its ID.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            session_id, chapter_id, start_time, end_time, duration, 
            correct_chars, incorrect_chars, total_chars, wpm, accuracy, errors_json
        FROM typing_sessions WHERE session_id = ?
    """, (session_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        stats = {
            'session_id': row[0],
            'chapter_id': row[1],
            'start_time': row[2],
            'end_time': row[3],
            'duration': row[4],
            'correct_chars': row[5],
            'incorrect_chars': row[6],
            'total_chars': row[7],
            'wpm': row[8],
            'accuracy': row[9],
            'errors': json.loads(row[10]) if row[10] else []
        }
        return stats
    return None


if __name__ == '__main__':
    from stash_manager import initialize_db, add_chapter, get_chapter

    initialize_db()
    print("Database initialized (from stats_tracker test).")

    # Add a dummy chapter for foreign key reference
    dummy_chapter_id = add_chapter(
        "Test Chapter for Stats", 
        "Stat Author", 
        "http://example.com/stat_chapter", 
        "This is some content for testing stats."
    )

    if dummy_chapter_id:
        print(f"Dummy chapter added with ID: {dummy_chapter_id}")

        # Simulate a typing session result
        sample_errors = [
            {'expected': 'q', 'actual': 'w', 'position': 5},
            {'expected': 'o', 'actual': 'i', 'position': 12}
        ]
        sample_duration = 35.5
        sample_correct_chars = 40
        sample_incorrect_chars = 2
        sample_total_chars = 42

        print("\nLogging a sample typing session...")
        session_id = log_typing_session(
            dummy_chapter_id, 
            sample_errors, 
            sample_duration, 
            sample_correct_chars, 
            sample_incorrect_chars, 
            sample_total_chars
        )

        if session_id:
            print(f"Typing session logged with ID: {session_id}")
            print("WPM calculated: ", calculate_wpm(sample_correct_chars, sample_duration))
            print("Accuracy calculated: ", calculate_accuracy(sample_correct_chars, sample_total_chars))
            
            retrieved_stats = get_session_stats(session_id)
            if retrieved_stats:
                print("\nRetrieved Session Stats:")
                for k, v in retrieved_stats.items():
                    print(f"  {k}: {v}")
        else:
            print("Failed to log typing session.")
    else:
        print("Failed to add dummy chapter, cannot test stats logging.")
