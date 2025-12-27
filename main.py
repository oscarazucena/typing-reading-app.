import customtkinter as ctk
from tkinter import Text, END
import time
import os
import json
import logging
import argparse
import re
from src.stats_tracker import calculate_wpm, calculate_accuracy
from src.stash_manager import initialize_db, add_book, add_chapter, list_books, list_chapters_for_book, get_chapter, get_book, log_typing_session
from src.novelbin_scraper import scrape_novel_chapter, scrape_novel_table_of_contents
from src.ui.practice_view import PracticeView
from src.ui.library_view import LibraryView
from src.ui.sidebar import Sidebar

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

        # --- Chapter Cache ---
        self.all_source_chapters_cache = []
        self.stashed_chapters_by_url_cache = {}
        self.current_book_id_cache = None
        
        # --- Main Layout ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Sidebar ---
        self.sidebar = Sidebar(self, self)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        # --- Main Container (for content) ---
        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # --- Views ---
        self.practice_view = PracticeView(self.container, self)
        self.library_view = LibraryView(self.container, self)

        # --- Load data and settings ---
        self.load_settings()
        self.load_text("Welcome! Load a chapter using the options below to begin.")
        
        # --- Initially, show the practice frame ---
        self.show_practice_view()

    def show_practice_view(self):
        self.library_view.grid_forget()
        self.practice_view.grid(row=0, column=0, sticky="nsew")

    def show_library_view(self):
        self.practice_view.grid_forget()
        self.library_view.grid(row=0, column=0, sticky="nsew")
        self.populate_stashed_books()

    def populate_stashed_books(self):
        self.all_source_chapters_cache = []
        self.stashed_chapters_by_url_cache = {}
        self.current_book_id_cache = None

        self.library_view.stashed_items_list._parent_canvas.yview_moveto(0)

        for widget in self.library_view.stashed_items_list.winfo_children():
            widget.destroy()
        for widget in self.library_view.nav_frame.winfo_children():
            widget.destroy()
        
        self.library_view.title_label.configure(text="Stashed Books")
        self.library_view.skip_frame.grid_forget()

        books = list_books()
        if books:
            for book in books:
                book_frame = ctk.CTkFrame(self.library_view.stashed_items_list)
                book_frame.pack(fill="x", pady=5, padx=5)
                book_label = ctk.CTkLabel(book_frame, text=f"{book['title']} by {book['author']}", anchor="w")
                book_label.pack(side="left", fill="x", expand=True, padx=10)
                view_chapters_button = ctk.CTkButton(book_frame, text="View Chapters",
                                                     command=lambda b_id=book['id']: self.show_chapters_for_book(b_id))
                view_chapters_button.pack(side="right", padx=10)
        else:
            no_books_label = ctk.CTkLabel(self.library_view.stashed_items_list, text="No books stashed yet.")
            no_books_label.pack()
            
    def show_chapters_for_book(self, book_id, offset=0):
        if self.current_book_id_cache != book_id:
            book = get_book(book_id)
            if not book:
                return
            all_chapters_data = scrape_novel_table_of_contents(book['source_url'])
            if not all_chapters_data or not all_chapters_data['chapters']:
                for widget in self.library_view.stashed_items_list.winfo_children():
                    widget.destroy()
                no_chapters_label = ctk.CTkLabel(self.library_view.stashed_items_list, text="Could not fetch chapter list from source.")
                no_chapters_label.pack()
                back_button = ctk.CTkButton(self.library_view.stashed_items_list, text="< Back to Books", command=self.populate_stashed_books)
                back_button.pack(pady=10)
                return
            
            self.all_source_chapters_cache = all_chapters_data['chapters']
            self.current_book_id_cache = book_id
            stashed_chapters = list_chapters_for_book(book_id)
            self.current_book_chapters = stashed_chapters
            self.stashed_chapters_by_url_cache = {ch['chapter_url']: ch for ch in stashed_chapters}
            self.library_view.title_label.configure(text=f"Chapters for: {book['title']}")
            self.library_view.skip_frame.grid(row=1, column=0, pady=(5,10), sticky="ew")
            self.library_view.skip_button.configure(command=lambda: self.skip_to_chapter(book_id))

        self.library_view.stashed_items_list._parent_canvas.yview_moveto(0)
        for widget in self.library_view.stashed_items_list.winfo_children():
            widget.destroy()

        limit = 200
        chapters_to_display = self.all_source_chapters_cache[offset : offset + limit]

        for chapter_info in chapters_to_display:
            chapter_url = chapter_info['url']
            is_stashed = chapter_url in self.stashed_chapters_by_url_cache
            if is_stashed:
                stashed_chapter = self.stashed_chapters_by_url_cache[chapter_url]
                try:
                    nav_index = [c['id'] for c in self.current_book_chapters].index(stashed_chapter['id'])
                except ValueError:
                    nav_index = -1
                chapter_button = ctk.CTkButton(
                    self.library_view.stashed_items_list,
                    text=f"{chapter_info['title']} (Stashed)",
                    command=lambda ch_id=stashed_chapter['id'], index=nav_index: self.load_chapter_and_show_view(ch_id, index)
                )
                chapter_button.pack(fill="x", padx=5, pady=2)
            else:
                unstashed_label = ctk.CTkLabel(
                    self.library_view.stashed_items_list,
                    text=f"{chapter_info['title']} (Not Stashed)",
                    text_color="gray", anchor="w"
                )
                unstashed_label.pack(fill="x", padx=15, pady=2)

        for widget in self.library_view.nav_frame.winfo_children():
            widget.destroy()

        self.library_view.nav_frame.grid_columnconfigure(0, weight=1)
        self.library_view.nav_frame.grid_columnconfigure(2, weight=1)

        if offset > 0:
            prev_offset = max(0, offset - limit)
            prev_button = ctk.CTkButton(self.library_view.nav_frame, text="< Previous", command=lambda: self.show_chapters_for_book(book_id, prev_offset))
            prev_button.grid(row=0, column=0, padx=5, sticky="w")
        total_pages = -(-len(self.all_source_chapters_cache) // limit)
        page_label = ctk.CTkLabel(self.library_view.nav_frame, text=f"Page {offset // limit + 1} of {total_pages}")
        page_label.grid(row=0, column=1, sticky="ew")
        if len(self.all_source_chapters_cache) > offset + limit:
            next_offset = offset + limit
            next_button = ctk.CTkButton(self.library_view.nav_frame, text="Next >", command=lambda: self.show_chapters_for_book(book_id, next_offset))
            next_button.grid(row=0, column=2, padx=5, sticky="e")
        back_button = ctk.CTkButton(self.library_view.nav_frame, text="< Back to Books", command=self.populate_stashed_books)
        back_button.grid(row=1, column=0, columnspan=3, pady=(5,0), sticky="ew")

    def skip_to_chapter(self, book_id):
        try:
            start_num_str = self.library_view.skip_entry.get()
            start_num = int(start_num_str)
        except (ValueError, TypeError):
            return
        book = get_book(book_id)
        if not book:
            return
        book_data = scrape_novel_table_of_contents(book['source_url'])
        if not book_data:
            return
        chapters_to_fetch = [ch for ch in book_data['chapters'] if ch['chapter_number'] >= start_num][:10]
        if not chapters_to_fetch:
            return
        for i, chapter_info in enumerate(chapters_to_fetch):
            try:
                existing_chapters = [c['chapter_number'] for c in self.current_book_chapters]
                if chapter_info['chapter_number'] in existing_chapters:
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
            except Exception as e:
                print(f"An error occurred while stashing {chapter_info['title']}: {e}")
            finally:
                self.update_idletasks()
        self.show_chapters_for_book(book_id)
        chapters = list_chapters_for_book(book_id)
        for idx, ch in enumerate(chapters):
            if ch['chapter_number'] == start_num:
                self.load_chapter_and_show_view(ch['id'], idx)
                break
        if chapters:
            for idx, chapter in enumerate(chapters):
                chapter_button = ctk.CTkButton(
                    self.library_view.stashed_items_list,
                    text=chapter['title'],
                    command=lambda ch_id=chapter['id'], index=idx: self.load_chapter_and_show_view(ch_id, index)
                )
                chapter_button.pack(fill="x", padx=5, pady=2)
        else:
            no_chapters_label = ctk.CTkLabel(self.library_view.stashed_items_list, text="This book has no chapters stashed.")
            no_chapters_label.pack()
        back_button = ctk.CTkButton(self.library_view.stashed_items_list, text="< Back to Books", command=self.populate_stashed_books)
        back_button.pack(pady=10)

    def load_chapter_and_show_view(self, chapter_id, index_in_book):
        chapter_data = get_chapter(chapter_id)
        if chapter_data:
            self.load_text(chapter_data['content'])
            self.chapter_id = chapter_id
            self.current_chapter_index_in_book = index_in_book
            self.last_fetched_url = chapter_data.get('chapter_url', '')
            self.show_practice_view()
        else:
            print(f"Error: Could not retrieve chapter with ID {chapter_id}")

    def fetch_chapter_from_url(self):
        url = self.practice_view.url_entry.get()
        if not url:
            return
        self.last_fetched_url = url
        self.current_book_chapters = []
        self.current_chapter_index_in_book = -1
        try:
            chapter_text = scrape_novel_chapter(url)
            if chapter_text:
                self.load_text(chapter_text)
                self.chapter_id = None
                self.show_practice_view()
                self.practice_view.url_entry.delete(0, END)
            else:
                print("Failed to fetch chapter.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def fetch_all_chapters_from_toc(self):
        toc_url = self.practice_view.toc_url_entry.get()
        if not toc_url:
            return
        book_data = scrape_novel_table_of_contents(toc_url)
        if not book_data:
            return
        book_id = add_book(book_data['book_title'], book_data['book_author'], book_data['source_url'])
        try:
            limit_str = self.practice_view.chapter_limit_entry.get()
            limit = int(limit_str) if limit_str.isdigit() else 10
        except (ValueError, TypeError):
            limit = 10
        chapters_to_fetch = book_data['chapters'][:limit]
        total_chapters = len(chapters_to_fetch)
        if total_chapters == 0:
            return
        self.practice_view.progress_bar.set(0)
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
                progress_value = (i + 1) / total_chapters
                self.practice_view.progress_bar.set(progress_value)
                self.update_idletasks()
            except Exception as e:
                print(f"An error occurred while stashing {chapter_info['title']}: {e}")
        self.show_library_view()
        self.practice_view.toc_url_entry.delete(0, END)
        self.practice_view.progress_bar.set(0)

    def stash_current_chapter(self):
        if not self.source_text or not self.last_fetched_url:
            return
        book_url = self.last_fetched_url.rsplit('/', 1)[0]
        book_title = "Scraped Book"
        book_author = "Unknown"
        book_id = add_book(book_title, book_author, book_url)
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
        self.show_library_view()

    def update_nav_buttons(self):
        self.practice_view.prev_chapter_button.configure(state="disabled")
        self.practice_view.next_chapter_button.configure(state="disabled")
        if not self.current_book_chapters or self.current_chapter_index_in_book == -1:
            return
        if self.current_chapter_index_in_book > 0:
            self.practice_view.prev_chapter_button.configure(state="normal")
        if self.current_chapter_index_in_book < len(self.current_book_chapters) - 1:
            self.practice_view.next_chapter_button.configure(state="normal")

    def go_to_neighbor_chapter(self, direction: int):
        if not self.current_book_chapters:
            return
        new_index = self.current_chapter_index_in_book + direction
        if 0 <= new_index < len(self.current_book_chapters):
            next_chapter = self.current_book_chapters[new_index]
            self.load_chapter_and_show_view(next_chapter['id'], new_index)

    def load_text(self, text):
        self.source_text = text
        self.practice_view.text_display.config(state="normal")
        self.practice_view.text_display.delete("1.0", END)
        self.practice_view.text_display.insert("1.0", self.source_text, "untyped")
        self.practice_view.text_display.config(state="disabled")
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
        self.practice_view.wpm_label.configure(text="WPM: 0")
        self.practice_view.accuracy_label.configure(text="Accuracy: 100%")
        self.practice_view.text_display.tag_remove("correct", "1.0", END)
        self.practice_view.text_display.tag_remove("incorrect", "1.0", END)
        self.practice_view.text_display.tag_remove("corrected", "1.0", END)
        self.practice_view.text_display.tag_add("untyped", "1.0", END)

    def on_key_press(self, event):
        if self.test_completed_correctly:
            return "break"
        if event.keysym == "BackSpace":
            if self.current_index > 0:
                self.current_index -= 1
                char_pos = f"1.{self.current_index}"
                tags = self.practice_view.text_display.tag_names(char_pos)
                if "correct" in tags:
                    self.correct_chars -= 1
                elif "incorrect" in tags:
                    self.incorrect_chars -= 1
                    self.practice_view.text_display.tag_add("corrected", char_pos, f"{char_pos}+1c")
                    self.practice_view.text_display.tag_remove("incorrect", char_pos, f"{char_pos}+1c")
                self.practice_view.text_display.tag_remove("correct", char_pos, f"{char_pos}+1c")
            return "break"
        if len(event.char) != 1 or not event.char.isprintable():
            return
        if self.current_index >= len(self.source_text):
            return "break"
        if not self.test_in_progress:
            self.start_time = time.time()
            self.test_in_progress = True
        if self.current_index < len(self.source_text):
            expected_char = self.source_text[self.current_index]
            typed_char = event.char
            char_pos = f"1.{self.current_index}"
            if typed_char == expected_char:
                self.correct_chars += 1
                self.practice_view.text_display.tag_add("correct", char_pos, f"{char_pos}+1c")
                self.practice_view.text_display.tag_remove("incorrect", char_pos, f"{char_pos}+1c")
            else:
                if "incorrect" not in self.practice_view.text_display.tag_names(char_pos):
                    self.incorrect_chars += 1
                    self.total_errors += 1
                    error_info = {
                        "expected": expected_char,
                        "actual": typed_char,
                        "position": self.current_index
                    }
                    self.error_details.append(error_info)
                self.practice_view.text_display.tag_add("incorrect", char_pos, f"{char_pos}+1c")
                self.practice_view.text_display.tag_remove("correct", char_pos, f"{char_pos}+1c")
            self.current_index += 1
            self.update_stats()
        if self.current_index >= len(self.source_text):
            self.test_in_progress = False
            if self.start_time:
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
        return "break"

    def log_typing_session(self, chapter_id: int, duration: float, correct_chars: int, incorrect_chars: int, total_errors: int, error_details: list):
        if chapter_id is None:
            return
        wpm = calculate_wpm(correct_chars, duration)
        accuracy = calculate_accuracy(correct_chars, total_errors)
        from src.stash_manager import log_typing_session as log_to_db
        log_to_db(
            chapter_id=chapter_id,
            duration=duration,
            correct_chars=correct_chars,
            incorrect_chars=incorrect_chars,
            total_errors=total_errors,
            error_details=error_details
        )

    def update_stats(self):
        if self.start_time and self.test_in_progress:
            duration = time.time() - self.start_time
            wpm = calculate_wpm(self.correct_chars, duration)
            acc = calculate_accuracy(self.correct_chars, self.total_errors)
            self.practice_view.wpm_label.configure(text=f"WPM: {wpm:.2f}")
            self.practice_view.accuracy_label.configure(text=f"Accuracy: {acc:.2f}%")

    def toggle_theme(self):
        mode = "dark" if self.practice_view.theme_switch.get() == 1 else "light"
        ctk.set_appearance_mode(mode)
        self._apply_theme_to_text_widget(mode)
        self.save_settings({"theme": mode})

    def _apply_theme_to_text_widget(self, mode):
        bg_color, fg_color = self._get_text_widget_colors(mode)
        self.practice_view.text_display.config(bg=bg_color, fg=fg_color, insertbackground=fg_color)
        self._update_highlight_colors(mode)

    def _update_highlight_colors(self, mode):
        if mode == "dark":
            correct_fg = "#A5D6A7"
            incorrect_fg = "#EF9A9A"
            corrected_fg = "#FFD54F"
        else:
            correct_fg = "#388E3C"
            incorrect_fg = "#D32F2F"
            corrected_fg = "#FFA000"
        self.practice_view.text_display.tag_configure("correct", foreground=correct_fg)
        self.practice_view.text_display.tag_configure("incorrect", foreground=incorrect_fg)
        self.practice_view.text_display.tag_configure("corrected", foreground=corrected_fg)

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
                    self.practice_view.theme_switch.select()
                else:
                    self.practice_view.theme_switch.deselect()
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
    initialize_db()
    app = TypingApp()
    app.mainloop()
