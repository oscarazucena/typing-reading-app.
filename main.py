import customtkinter as ctk
from tkinter import Text, END
import time
import os
import json
from src.stats_tracker import calculate_wpm, calculate_accuracy

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
        self.current_index = 0
        self.correct_chars = 0
        self.incorrect_chars = 0
        self.start_time = None
        self.test_in_progress = False

        # --- Main Frame ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # --- Top Frame for Stats ---
        self.stats_frame = ctk.CTkFrame(self.main_frame)
        self.stats_frame.pack(pady=10, padx=10, fill="x")

        self.wpm_label = ctk.CTkLabel(self.stats_frame, text="WPM: 0", font=("Arial", 16))
        self.wpm_label.pack(side="left", padx=10)

        self.accuracy_label = ctk.CTkLabel(self.stats_frame, text="Accuracy: 100%", font=("Arial", 16))
        self.accuracy_label.pack(side="left", padx=10)
        
        self.reset_button = ctk.CTkButton(self.stats_frame, text="Reset", command=self.reset_test)
        self.reset_button.pack(side="left", padx=10)

        self.theme_switch = ctk.CTkSwitch(self.stats_frame, text="Toggle Dark Mode", command=self.toggle_theme)
        self.theme_switch.pack(side="right", padx=10)

        # --- Text Frame for Typing ---
        self.text_frame = ctk.CTkFrame(self.main_frame)
        self.text_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.text_display = Text(self.text_frame, wrap="word", font=("Arial", 22), 
                                 bg=self._get_text_widget_colors(ctk.get_appearance_mode())[0], 
                                 fg=self._get_text_widget_colors(ctk.get_appearance_mode())[1],
                                 borderwidth=0, highlightthickness=0, insertbackground=self._get_text_widget_colors(ctk.get_appearance_mode())[1])
        self.text_display.pack(fill="both", expand=True)
        self.text_display.focus()

        # Define tags for highlighting
        self.text_display.tag_configure("correct", foreground="green")
        self.text_display.tag_configure("incorrect", foreground="red", underline=True)
        self.text_display.tag_configure("untyped", foreground=self._get_text_widget_colors(ctk.get_appearance_mode())[1])

        # Bind events
        self.text_display.bind("<KeyPress>", self.on_key_press)
        
        self.load_settings()
        self.load_text("The quick brown fox jumps over the lazy dog. Try typing this sentence to test your speed and accuracy.")

    def load_text(self, text):
        self.source_text = text
        self.text_display.config(state="normal")
        self.text_display.delete("1.0", END)
        self.text_display.insert("1.0", self.source_text, "untyped")
        self.text_display.config(state="disabled")
        self.reset_test()

    def reset_test(self):
        self.current_index = 0
        self.correct_chars = 0
        self.incorrect_chars = 0
        self.start_time = None
        self.test_in_progress = False
        
        self.wpm_label.configure(text="WPM: 0")
        self.accuracy_label.configure(text="Accuracy: 100%")
        
        # Reset all tags to untyped
        self.text_display.tag_remove("correct", "1.0", END)
        self.text_display.tag_remove("incorrect", "1.0", END)
        self.text_display.tag_add("untyped", "1.0", END)

    def on_key_press(self, event):
        if event.keysym == "BackSpace":
            if self.current_index > 0:
                self.current_index -= 1
                # Remove tags from the character being erased
                char_pos = f"1.{self.current_index}"
                self.text_display.tag_remove("correct", char_pos, f"{char_pos}+1c")
                self.text_display.tag_remove("incorrect", char_pos, f"{char_pos}+1c")
            return "break" # Prevents default backspace behavior

        # Ignore non-printable keys (e.g., Shift, Ctrl)
        if len(event.char) != 1 or not event.char.isprintable():
            return

        # If test is finished, do nothing
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
                self.text_display.tag_add("correct", char_pos, f"{char_pos}+1c")
            else:
                self.incorrect_chars += 1
                self.text_display.tag_add("incorrect", char_pos, f"{char_pos}+1c")
            
            self.current_index += 1
            self.update_stats()

        if self.current_index >= len(self.source_text):
            self.test_in_progress = False
            # Can add end-of-test logic here

        return "break" # Prevents the key from being inserted into the widget

    def update_stats(self):
        if self.start_time and self.test_in_progress:
            duration = time.time() - self.start_time
            
            wpm = calculate_wpm(self.correct_chars, duration)
            total_typed = self.correct_chars + self.incorrect_chars
            acc = calculate_accuracy(self.correct_chars, total_typed)
            
            self.wpm_label.configure(text=f"WPM: {wpm:.2f}")
            self.accuracy_label.configure(text=f"Accuracy: {acc:.2f}%")

    def toggle_theme(self):
        mode = "dark" if self.theme_switch.get() == 1 else "light"
        ctk.set_appearance_mode(mode)
        self._apply_theme_to_text_widget(mode)
        self.save_settings({"theme": mode})

    def _apply_theme_to_text_widget(self, mode):
        bg_color, fg_color = self._get_text_widget_colors(mode)
        self.text_display.config(bg=bg_color, fg=fg_color, insertbackground=fg_color)
        self.text_display.tag_configure("untyped", foreground=fg_color)

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
                ctk.set_appearance_mode(theme)
                if theme == "dark":
                    self.theme_switch.select()
                else:
                    self.theme_switch.deselect()
                # Apply theme to text widget after loading
                self._apply_theme_to_text_widget(theme)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is invalid, create it with default settings
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            self.save_settings({"theme": "system"})
            self._apply_theme_to_text_widget("system")

    def save_settings(self, settings):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)

if __name__ == "__main__":
    app = TypingApp()
    app.mainloop()
