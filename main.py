import customtkinter as ctk
from tkinter import Text, END
import time
import os
import json
import logging
import argparse
from src.stats_tracker import calculate_wpm, calculate_accuracy
from src.stash_manager import initialize_db, add_book, add_chapter, list_books, list_chapters_for_book, get_chapter, get_book, log_typing_session
from src.novelbin_scraper import scrape_novel_chapter, scrape_novel_table_of_contents
from src.ui.startup_view import StartupView
from src.ui.typing_view import TypingView
from src.ui.stash_view import StashView

# --- Settings ---
SETTINGS_FILE = "config/settings.json"

# --- Main Application ---
class TypingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Typing Practice App")
        self.geometry("800x600")

        # --- Typing State ---
        self.source_text = ""
        self.chapter_id = None
        self.current_book_chapters = []
        self.current_chapter_index_in_book = -1
        
        self.current_index = 0
        self.correct_chars = 0
        self.incorrect_chars = 0
        self.total_errors = 0
        self.error_details = []
        self.start_time = None
        self.test_in_progress = False
        self.test_completed_correctly = False
        self.last_fetched_url = ""
        
        # --- Main Container ---
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Views ---
        self.startup_view = StartupView(self.container, self)
        self.typing_view = TypingView(self.container, self)
        self.stash_view = StashView(self.container, self)

        # --- Load data and settings ---
        self.load_settings()
        self.load_text("Welcome! Load a chapter using the options below to begin.")
        # self.populate_stashed_books() # Removed this to start on startup_view

        # --- Initially, show the startup frame ---
        self.show_startup_view()

    def show_startup_view(self):
        self.typing_view.pack_forget()
        self.stash_view.pack_forget()
        self.startup_view.pack(fill="both", expand=True)

    def show_typing_view(self):
        self.startup_view.pack_forget()
        self.stash_view.pack_forget()
        self.typing_view.pack(fill="both", expand=True)
        self.typing_view.text_display.focus()
        self.update_nav_buttons()

        # Enable/disable stash button
        if self.chapter_id is not None:
            self.typing_view.stash_button.configure(state="disabled")
        else:
            self.typing_view.stash_button.configure(state="normal")

    def show_stash_view(self):
        self.startup_view.pack_forget()
        self.typing_view.pack_forget()
        self.stash_view.pack(fill="both", expand=True)
        self.populate_stashed_books() # Refresh books when showing this view

    def populate_stashed_books(self):
        # Clear any existing widgets
        for widget in self.stash_view.stashed_items_list.winfo_children():
            widget.destroy()
        
        self.stash_view.title_label.configure(text="Stashed Books")
        self.stash_view.skip_frame.grid_forget() # Hide skip frame when showing books

        books = list_books()
        if books:
            for book in books:
                # Frame for each book
                book_frame = ctk.CTkFrame(self.stash_view.stashed_items_list)
                book_frame.pack(fill="x", pady=5, padx=5)

                book_label = ctk.CTkLabel(book_frame, text=f"{book['title']} by {book['author']}", anchor="w")
                book_label.pack(side="left", fill="x", expand=True, padx=10)

                view_chapters_button = ctk.CTkButton(book_frame, text="View Chapters",
                                                     command=lambda b_id=book['id']: self.show_chapters_for_book(b_id))
                view_chapters_button.pack(side="right", padx=10)
        else:
            no_books_label = ctk.CTkLabel(self.stash_view.stashed_items_list, text="No books stashed yet.")
            no_books_label.pack()
            
    def show_chapters_for_book(self, book_id):
        # Clear the list and show chapters for the selected book
        for widget in self.stash_view.stashed_items_list.winfo_children():
            widget.destroy()
            
        book = get_book(book_id)
        self.stash_view.title_label.configure(text=f"Chapters for: {book['title']}")

        # Show and configure the skip frame
        self.stash_view.skip_frame.grid(row=1, column=0, pady=(5,10), sticky="ew")
        self.stash_view.skip_button.configure(command=lambda: self.skip_to_chapter(book_id))
            
        chapters = list_chapters_for_book(book_id)
        self.current_book_chapters = chapters # Store for navigation

        if chapters:
            for idx, chapter in enumerate(chapters):
                chapter_button = ctk.CTkButton(
                    self.stash_view.stashed_items_list,
                    text=chapter['title'],
                    command=lambda ch_id=chapter['id'], index=idx: self.load_chapter_and_show_view(ch_id, index)
                )
                chapter_button.pack(fill="x", padx=5, pady=2)
        else:
            no_chapters_label = ctk.CTkLabel(self.stash_view.stashed_items_list, text="This book has no chapters stashed.")
            no_chapters_label.pack()

        # Add a back button
        back_button = ctk.CTkButton(self.stash_view.stashed_items_list, text="< Back to Books", command=self.populate_stashed_books)
        back_button.pack(pady=10)

    def skip_to_chapter(self, book_id):
        try:
            start_num_str = self.stash_view.skip_entry.get()
            start_num = int(start_num_str)
        except (ValueError, TypeError):
            print("Invalid chapter number.")
            return

        book = get_book(book_id)
        if not book:
            print("Could not find book to skip.")
            return

        # Scrape the full ToC to find the target chapters
        book_data = scrape_novel_table_of_contents(book['source_url'])
        if not book_data:
            print("Failed to fetch ToC for skipping.")
            return
            
        # Determine the slice of chapters to fetch (e.g., start_num to start_num + 10)
        chapters_to_fetch = [ch for ch in book_data['chapters'] if ch['chapter_number'] >= start_num][:10] # Fetch next 10

        if not chapters_to_fetch:
            print(f"Could not find chapters starting from number {start_num}.")
            return
        
        total_to_fetch = len(chapters_to_fetch)
        # self.startup_view.progress_bar.set(0) # TODO: Add a progress bar to stash view

        for i, chapter_info in enumerate(chapters_to_fetch):
            try:
                # Check if chapter already exists before scraping
                # This is a simplified check; a more robust app would check the URL
                existing_chapters = [c['chapter_number'] for c in self.current_book_chapters]
                if chapter_info['chapter_number'] in existing_chapters:
                    print(f"Chapter {chapter_info['chapter_number']} already stashed. Skipping scrape.")
                    continue
                    
                content = scrape_novel_chapter(chapter_info['url'])
                if content:
                    add_chapter(
                        book_id=book_id,
                        title=chapter_info['title'],
                        chapter_url=chapter_info['url'],
                        content=content,
                        chapter_number=chapter_info['chapter_number']
                    )
                    print(f"Stashed: {chapter_info['title']}")
                else:
                    print(f"Failed to scrape content for: {chapter_info['title']}")

            except Exception as e:
                print(f"An error occurred while stashing {chapter_info['title']}: {e}")
            finally:
                # Update progress bar
                # progress_value = (i + 1) / total_to_fetch
                # self.startup_view.progress_bar.set(progress_value)
                self.update_idletasks() # Force UI update

        # Refresh the chapter list to show the newly added chapters
        self.show_chapters_for_book(book_id)
        # self.startup_view.progress_bar.set(0)

        # Automatically load the chapter the user skipped to
        chapters = list_chapters_for_book(book_id)
        for idx, ch in enumerate(chapters):
            if ch['chapter_number'] == start_num:
                self.load_chapter_and_show_view(ch['id'], idx)
                break

        if chapters:
            for idx, chapter in enumerate(chapters):
                chapter_button = ctk.CTkButton(
                    self.stash_view.stashed_items_list,
                    text=chapter['title'],
                    command=lambda ch_id=chapter['id'], index=idx: self.load_chapter_and_show_view(ch_id, index)
                )
                chapter_button.pack(fill="x", padx=5, pady=2)
        else:
            no_chapters_label = ctk.CTkLabel(self.stash_view.stashed_items_list, text="This book has no chapters stashed.")
            no_chapters_label.pack()

        # Add a back button
        back_button = ctk.CTkButton(self.stash_view.stashed_items_list, text="< Back to Books", command=self.populate_stashed_books)
        back_button.pack(pady=10)


    def load_chapter_and_show_view(self, chapter_id, index_in_book):
        chapter_data = get_chapter(chapter_id)
        if chapter_data:
            self.load_text(chapter_data['content'])
            self.chapter_id = chapter_id
            self.current_chapter_index_in_book = index_in_book
            self.last_fetched_url = chapter_data.get('chapter_url', '') # Store the URL
            self.show_typing_view()
        else:
            print(f"Error: Could not retrieve chapter with ID {chapter_id}")

    def fetch_chapter_from_url(self):
        url = self.startup_view.url_entry.get()
        if not url:
            return
        
        self.last_fetched_url = url
        self.current_book_chapters = [] # Clear book context
        self.current_chapter_index_in_book = -1

        try:
            chapter_text = scrape_novel_chapter(url)
            if chapter_text:
                self.load_text(chapter_text)
                self.chapter_id = None # Not a stashed chapter yet
                self.show_typing_view()
                self.startup_view.url_entry.delete(0, END)
            else:
                print("Failed to fetch chapter.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def fetch_all_chapters_from_toc(self):
        toc_url = self.startup_view.toc_url_entry.get()
        if not toc_url:
            return

        book_data = scrape_novel_table_of_contents(toc_url)
        if not book_data:
            print("Could not find any chapters at the given ToC URL.")
            return
        


        book_id = add_book(book_data['book_title'], book_data['book_author'], book_data['source_url'])
        
        try:
            limit_str = self.startup_view.chapter_limit_entry.get()
            limit = int(limit_str) if limit_str.isdigit() else 10
        except (ValueError, TypeError):
            limit = 10

        chapters_to_fetch = book_data['chapters'][:limit]
        total_chapters = len(chapters_to_fetch)

        if total_chapters == 0:
            print("No chapters to fetch.")
            return

        self.startup_view.progress_bar.set(0)

        for i, chapter_info in enumerate(chapters_to_fetch):
            try:
                content = scrape_novel_chapter(chapter_info['url'])
                if content:
                    add_chapter(
                        book_id=book_id,
                        title=chapter_info['title'],
                        chapter_url=chapter_info['url'],
                        content=content,
                        chapter_number=chapter_info['chapter_number']
                    )
                    print(f"Stashed: {chapter_info['title']}")
                else:
                    print(f"Failed to scrape content for: {chapter_info['title']}")

                # Update progress bar
                progress_value = (i + 1) / total_chapters
                self.startup_view.progress_bar.set(progress_value)
                self.update_idletasks() # Force UI update

            except Exception as e:
                print(f"An error occurred while stashing {chapter_info['title']}: {e}")

        print(f"Finished stashing {total_chapters} chapters.")
        self.show_stash_view()
        self.startup_view.toc_url_entry.delete(0, END)
        self.startup_view.progress_bar.set(0)

    def stash_current_chapter(self):
        if not self.source_text or not self.last_fetched_url:
            print("Cannot stash text that was not fetched from a URL.")
            return

        # Simple heuristic to derive book URL
        book_url = self.last_fetched_url.rsplit('/', 1)[0]
        # For single chapters, we don't know the real book title/author yet
        book_title = "Scraped Book"
        book_author = "Unknown"
        
        book_id = add_book(book_title, book_author, book_url)

        # Heuristic for chapter title and number
        chapter_title = f"Chapter from {self.last_fetched_url}"
        match = re.search(r'-(\d+)$', self.last_fetched_url)
        chapter_num = int(match.group(1)) if match else None

        add_chapter(
            book_id=book_id,
            title=chapter_title,
            chapter_url=self.last_fetched_url,
            content=self.source_text,
            chapter_number=chapter_num
        )
        print(f"Chapter stashed successfully into book '{book_title}'")
        self.show_stash_view()

    def update_nav_buttons(self):
        # Disable both by default
        self.typing_view.prev_chapter_button.configure(state="disabled")
        self.typing_view.next_chapter_button.configure(state="disabled")
        
        if not self.current_book_chapters or self.current_chapter_index_in_book == -1:
            return # Not in a book context
            
        # Enable/disable Previous button
        if self.current_chapter_index_in_book > 0:
            self.typing_view.prev_chapter_button.configure(state="normal")
            
        # Enable/disable Next button
        if self.current_chapter_index_in_book < len(self.current_book_chapters) - 1:
            self.typing_view.next_chapter_button.configure(state="normal")

    def go_to_neighbor_chapter(self, direction: int):
        if not self.current_book_chapters:
            return

        new_index = self.current_chapter_index_in_book + direction
        if 0 <= new_index < len(self.current_book_chapters):
            next_chapter = self.current_book_chapters[new_index]
            self.load_chapter_and_show_view(next_chapter['id'], new_index)


    def load_text(self, text):
        self.source_text = text
        self.typing_view.text_display.config(state="normal")
        self.typing_view.text_display.delete("1.0", END)
        self.typing_view.text_display.insert("1.0", self.source_text, "untyped")
        self.typing_view.text_display.config(state="disabled")
        self.reset_test()

    def reset_test(self):
        self.current_index = 0
        self.correct_chars = 0
        self.incorrect_chars = 0
        self.total_errors = 0
        self.error_details = []
        self.start_time = None
        self.test_in_progress = False
        self.test_completed_correctly = False
        
        self.typing_view.wpm_label.configure(text="WPM: 0")
        self.typing_view.accuracy_label.configure(text="Accuracy: 100%")
        
        # Reset all tags to untyped
        self.typing_view.text_display.tag_remove("correct", "1.0", END)
        self.typing_view.text_display.tag_remove("incorrect", "1.0", END)
        self.typing_view.text_display.tag_remove("corrected", "1.0", END)
        self.typing_view.text_display.tag_add("untyped", "1.0", END)

    def on_key_press(self, event):
        logging.debug(f"\n--- Key Press: '{event.char}' ---")

        if self.test_completed_correctly:
            logging.debug("Test is 100% correct. Input is locked.")
            return "break"

        if event.keysym == "BackSpace":
            if self.current_index > 0:
                self.current_index -= 1
                char_pos = f"1.{self.current_index}"
                
                tags = self.typing_view.text_display.tag_names(char_pos)
                if "correct" in tags:
                    self.correct_chars -= 1
                elif "incorrect" in tags:
                    self.incorrect_chars -= 1
                    # Mark the error as 'corrected' visually
                    self.typing_view.text_display.tag_add("corrected", char_pos, f"{char_pos}+1c")
                    self.typing_view.text_display.tag_remove("incorrect", char_pos, f"{char_pos}+1c")
                
                # Allow re-typing by removing existing tags
                self.typing_view.text_display.tag_remove("correct", char_pos, f"{char_pos}+1c")
                logging.debug(f"Backspace pressed. New index: {self.current_index}")
            return "break"

        if len(event.char) != 1 or not event.char.isprintable():
            logging.debug("Ignoring non-printable key.")
            return

        if self.current_index >= len(self.source_text):
            logging.debug("Test finished. Ignoring key press.")
            return "break"

        if not self.test_in_progress:
            logging.debug("First key press. Starting test.")
            self.start_time = time.time()
            self.test_in_progress = True

        if self.current_index < len(self.source_text):
            expected_char = self.source_text[self.current_index]
            typed_char = event.char
            
            char_pos = f"1.{self.current_index}"
            
            if typed_char == expected_char:
                self.correct_chars += 1
                self.typing_view.text_display.tag_add("correct", char_pos, f"{char_pos}+1c")
                self.typing_view.text_display.tag_remove("incorrect", char_pos, f"{char_pos}+1c")
            else:
                if "incorrect" not in self.typing_view.text_display.tag_names(char_pos):
                    self.incorrect_chars += 1
                    self.total_errors += 1
                    error_info = {
                        "expected": expected_char,
                        "actual": typed_char,
                        "position": self.current_index
                    }
                    self.error_details.append(error_info)
                    logging.debug(f"Error logged: {error_info}")
                
                self.typing_view.text_display.tag_add("incorrect", char_pos, f"{char_pos}+1c")
                self.typing_view.text_display.tag_remove("correct", char_pos, f"{char_pos}+1c")
            
            self.current_index += 1
            logging.debug(f"Index incremented to: {self.current_index}")
            self.update_stats()

        if self.current_index >= len(self.source_text):
            logging.debug("--- TEST FINISHED ---")
            self.test_in_progress = False

            # Log the session to the database
            if self.start_time: # Ensure test has started
                duration = time.time() - self.start_time
                self.log_typing_session(
                    chapter_id=self.chapter_id,
                    duration=duration,
                    correct_chars=self.correct_chars,
                    incorrect_chars=self.incorrect_chars,
                    total_errors=self.total_errors,
                    error_details=self.error_details
                )

            if self.incorrect_chars == 0:
                self.test_completed_correctly = True
                logging.debug("Test completed with 100% accuracy. Locking input.")
            
            logging.debug(f"Final error details: {self.error_details}")
            logging.debug(f"Final state: test_in_progress = {self.test_in_progress}")

        return "break"

    def log_typing_session(self, chapter_id: int, duration: float, correct_chars: int, incorrect_chars: int, total_errors: int, error_details: list):
        """
        Calculates stats and logs a completed typing session to the database.
        """
        if chapter_id is None:
            print("Cannot log session for an un-stashed chapter.")
            return

        wpm = calculate_wpm(correct_chars, duration)
        accuracy = calculate_accuracy(correct_chars, total_errors)
        
        # Here we will call the actual database logging function from stash_manager
        from src.stash_manager import log_typing_session as log_to_db
        log_to_db(
            chapter_id=chapter_id,
            duration=duration,
            correct_chars=correct_chars,
            incorrect_chars=incorrect_chars,
            total_errors=total_errors,
            error_details=error_details
        )
        
        print(f"Session logged for Chapter ID {chapter_id}: WPM={wpm:.2f}, Accuracy={accuracy:.2f}%")


    def update_stats(self):
        logging.debug(f"Updating stats. In progress? {self.test_in_progress}")
        if self.start_time and self.test_in_progress:
            duration = time.time() - self.start_time
            
            wpm = calculate_wpm(self.correct_chars, duration)
            acc = calculate_accuracy(self.correct_chars, self.total_errors)

            logging.debug(f"  Duration: {duration:.4f}s")
            logging.debug(f"  Correct Chars: {self.correct_chars}")
            logging.debug(f"  Total Errors: {self.total_errors}")
            logging.debug(f"  WPM: {wpm:.2f}")
            logging.debug(f"  Accuracy: {acc:.2f}%")
            
            self.typing_view.wpm_label.configure(text=f"WPM: {wpm:.2f}")
            self.typing_view.accuracy_label.configure(text=f"Accuracy: {acc:.2f}%")
        else:
            logging.debug("  Skipping stats update (test not in progress or started).")

    def toggle_theme(self):
        mode = "dark" if self.typing_view.theme_switch.get() == 1 else "light"
        ctk.set_appearance_mode(mode)
        self._apply_theme_to_text_widget(mode)
        self.save_settings({"theme": mode})

    def _apply_theme_to_text_widget(self, mode):
        bg_color, fg_color = self._get_text_widget_colors(mode)
        self.typing_view.text_display.config(bg=bg_color, fg=fg_color, insertbackground=fg_color)
        self._update_highlight_colors(mode)

    def _update_highlight_colors(self, mode):
        if mode == "dark":
            correct_fg = "#A5D6A7"  # Light Green
            incorrect_fg = "#EF9A9A" # Light Red
            corrected_fg = "#FFD54F" # Light Orange/Yellow for corrected
        else: # Light mode
            correct_fg = "#388E3C"  # Dark Green
            incorrect_fg = "#D32F2F" # Dark Red
            corrected_fg = "#FFA000" # Dark Orange/Amber for corrected
        
        self.typing_view.text_display.tag_configure("correct", foreground=correct_fg)
        self.typing_view.text_display.tag_configure("incorrect", foreground=incorrect_fg)
        self.typing_view.text_display.tag_configure("corrected", foreground=corrected_fg)

    def _get_text_widget_colors(self, mode):
        if mode == "dark":
            return ("#2B2B2B", "#DCE4EE")
        else:
            return ("#FFFFFF", "#1E1E1E")

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                theme = settings.get("theme", "system")
                if theme not in ["light", "dark"]:
                    theme = "system"
                
                ctk.set_appearance_mode(theme)
                if theme == "dark":
                    self.typing_view.theme_switch.select()
                else:
                    self.typing_view.theme_switch.deselect()
                
                self._apply_theme_to_text_widget(theme)
        except (FileNotFoundError, json.JSONDecodeError):
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            current_theme = ctk.get_appearance_mode().lower()
            self.save_settings({"theme": current_theme})
            self._apply_theme_to_text_widget(current_theme)

    def save_settings(self, settings):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A typing practice application.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging to a file.")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, 
                            filename='debug.log', 
                            filemode='w', 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.debug("Debug mode enabled.")

    # Initialize the database
    initialize_db()

    app = TypingApp()
    app.mainloop()
