import customtkinter as ctk
from tkinter import Text

class PracticeView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- URL Frame ---
        self.url_frame = ctk.CTkFrame(self)
        self.url_frame.grid(row=0, column=0, columnspan=2, pady=10, padx=10, sticky="ew")
        self.url_frame.grid_columnconfigure(1, weight=1)

        self.url_label = ctk.CTkLabel(self.url_frame, text="Chapter URL:")
        self.url_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.url_entry = ctk.CTkEntry(self.url_frame)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.fetch_button = ctk.CTkButton(self.url_frame, text="Fetch", command=self.controller.fetch_chapter_from_url)
        self.fetch_button.grid(row=0, column=2, padx=5, pady=5)

        self.toc_url_label = ctk.CTkLabel(self.url_frame, text="TOC URL:")
        self.toc_url_label.grid(row=1, column=0, padx=5, pady=5)

        self.toc_url_entry = ctk.CTkEntry(self.url_frame)
        self.toc_url_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.chapter_limit_entry = ctk.CTkEntry(self.url_frame, width=50)
        self.chapter_limit_entry.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.chapter_limit_entry.insert(0, "10")

        self.fetch_all_button = ctk.CTkButton(self.url_frame, text="Fetch All", command=self.controller.fetch_all_chapters_from_toc)
        self.fetch_all_button.grid(row=1, column=3, padx=5, pady=5)

        self.progress_bar = ctk.CTkProgressBar(self.url_frame)
        self.progress_bar.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(10, 5))
        self.progress_bar.set(0)

        # --- Top Frame for Stats ---
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky="ew")
        self.stats_frame.grid_columnconfigure(6, weight=1)

        self.wpm_label = ctk.CTkLabel(self.stats_frame, text="WPM: 0", font=("Arial", 16))
        self.wpm_label.grid(row=0, column=0, padx=10)

        self.accuracy_label = ctk.CTkLabel(self.stats_frame, text="Accuracy: 100%", font=("Arial", 16))
        self.accuracy_label.grid(row=0, column=1, padx=10)
        
        self.reset_button = ctk.CTkButton(self.stats_frame, text="Reset", command=self.controller.reset_test)
        self.reset_button.grid(row=0, column=2, padx=10)

        self.stash_button = ctk.CTkButton(self.stats_frame, text="Stash Current Text", command=self.controller.stash_current_chapter)
        self.stash_button.grid(row=0, column=3, padx=10)

        # --- Navigation Buttons ---
        self.prev_chapter_button = ctk.CTkButton(self.stats_frame, text="< Prev",
                                                 command=lambda: self.controller.go_to_neighbor_chapter(-1),
                                                 state="disabled")
        self.prev_chapter_button.grid(row=0, column=4, padx=(20, 5))

        self.next_chapter_button = ctk.CTkButton(self.stats_frame, text="Next >",
                                                 command=lambda: self.controller.go_to_neighbor_chapter(1),
                                                 state="disabled")
        self.next_chapter_button.grid(row=0, column=5, padx=5)

        self.theme_switch = ctk.CTkSwitch(self.stats_frame, text="Toggle Dark Mode", command=self.controller.toggle_theme)
        self.theme_switch.grid(row=0, column=6, padx=10, sticky="e")

        # --- Text Frame for Typing ---
        self.text_frame = ctk.CTkFrame(self)
        self.text_frame.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="nsew")
        self.text_frame.grid_rowconfigure(0, weight=1)
        self.text_frame.grid_columnconfigure(0, weight=1)

        self.text_display = Text(self.text_frame, wrap="word", font=("Arial", 22), 
                                 bg=self.controller._get_text_widget_colors(ctk.get_appearance_mode())[0], 
                                 fg=self.controller._get_text_widget_colors(ctk.get_appearance_mode())[1],
                                 borderwidth=0, highlightthickness=0, insertbackground=self.controller._get_text_widget_colors(ctk.get_appearance_mode())[1])
        self.text_display.grid(row=0, column=0, sticky="nsew")
        
        # Define tags for highlighting
        self.text_display.tag_configure("correct")
        self.text_display.tag_configure("incorrect", underline=True)
        self.text_display.tag_configure("untyped")
        self.text_display.tag_configure("corrected")

        # Bind events
        self.text_display.bind("<KeyPress>", self.controller.on_key_press)
