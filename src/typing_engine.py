import sys
import os
import msvcrt # For Windows-specific character input
import time

def run_typing_test(source_text: str):
    """
    Runs a character-by-character typing test in the CLI.
    Provides immediate feedback and tracks errors.
    """
    print("\nType the following text. Press Esc to quit.")
    print("-" * 70)
    print(source_text)
    print("-" * 70)

    typed_chars = []
    errors = []
    source_index = 0
    start_time = time.time()
    correct_chars = 0
    incorrect_chars = 0

    sys.stdout.write("> ") # Prompt for typing
    sys.stdout.flush()

    try:
        while source_index < len(source_text):
            if msvcrt.kbhit(): # Check if a key has been pressed
                key = msvcrt.getch()
                try:
                    char = key.decode('utf-8')
                except UnicodeDecodeError:
                    # Handle special keys that cannot be decoded (e.g., arrow keys)
                    continue

                if key == b'\x1b': # ESC key to quit
                    print("\nTyping test aborted.")
                    break
                elif key == b'\r': # Enter key
                    # For a typing test, we usually don't want newlines until the source text has them.
                    # We'll treat Enter as a regular character comparison or ignore it if not in source.
                    # For now, let's assume source_text might have newlines.
                    expected_char = source_text[source_index]
                    if expected_char == '\n':
                        sys.stdout.write('\n')
                        sys.stdout.flush()
                        typed_chars.append(expected_char)
                        correct_chars += 1
                        source_index += 1
                    else:
                        # If Enter is pressed but not expected, treat as error
                        sys.stdout.write("[\\n]") # Indicate unexpected newline
                        sys.stdout.flush()
                        errors.append({'expected': expected_char, 'actual': '\n', 'position': source_index})
                        incorrect_chars += 1
                        typed_chars.append('\n')
                        source_index += 1 # Move forward to avoid getting stuck
                    continue
                elif key == b'\x08': # Backspace key
                    if typed_chars: # Only allow backspace if there's something to delete
                        typed_chars.pop()
                        source_index = len(typed_chars) # Adjust source_index based on typed_chars
                        # Re-render the line - this is complex without a TUI library. 
                        # For now, a simpler approach: just print a backspace character
                        sys.stdout.write('\b \b') # Erase last character from console
                        sys.stdout.flush()
                        # Note: This simple backspace handling doesn't visually correct errors already printed.
                        # A full TUI would re-render the entire line based on typed_chars.
                    continue

                if source_index < len(source_text):
                    expected_char = source_text[source_index]
                    if char == expected_char:
                        sys.stdout.write(char) # Print correct char in default color
                        correct_chars += 1
                    else:
                        sys.stdout.write("\033[91m" + char + "\033[0m") # Print incorrect char in red
                        errors.append({'expected': expected_char, 'actual': char, 'position': source_index})
                        incorrect_chars += 1
                    sys.stdout.flush()
                    typed_chars.append(char)
                    source_index += 1
                else:
                    # If user types beyond source text, ignore or log as extra characters
                    pass # For now, we'll just ignore extra characters
    except Exception as e:
        print(f"An error occurred: {e}")

    end_time = time.time()
    duration = end_time - start_time

    print("\nTyping test finished!")
    return {
        'errors': errors,
        'duration': duration,
        'correct_chars': correct_chars,
        'incorrect_chars': incorrect_chars,
        'total_chars': len(source_text)
    }

if __name__ == '__main__':
    sample_text = "The quick brown fox jumps over the lazy dog. This is a second sentence to test the functionality."
    print("Running a sample typing test:")
    test_results = run_typing_test(sample_text)
    print(f"Total errors: {len(test_results['errors'])}")
    print(f"Duration: {test_results['duration']:.2f} seconds")
    print(f"Correct characters: {test_results['correct_chars']}")
    print(f"Incorrect characters: {test_results['incorrect_chars']}")
    print(f"Total source characters: {test_results['total_chars']}")
    if test_results['errors']:
        print("Errors Summary:")
        for error in test_results['errors']:
            print(f"  Pos {error['position']}: Expected 
'{error['expected']}', Got 
'{error['actual']}'")

    # Test with text containing newline
    sample_text_with_newline = "First line.\nSecond line."
    print("\nRunning a typing test with newline:")
    test_results_newline = run_typing_test(sample_text_with_newline)
    print(f"Total errors: {len(test_results_newline['errors'])}")
