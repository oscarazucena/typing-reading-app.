import customtkinter as ctk
from tkinter import Text

class TypingView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        # --- Top Frame for Stats ---
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.pack(pady=10, padx=10, fill="x")

        self.home_button = ctk.CTkButton(self.stats_frame, text="Home", command=self.controller.show_startup_view)
        self.home_button.pack(side="left", padx=10)
        
        self.wpm_label = ctk.CTkLabel(self.stats_frame, text="WPM: 0", font=("Arial", 16))
        self.wpm_label.pack(side="left", padx=10)

        self.accuracy_label = ctk.CTkLabel(self.stats_frame, text="Accuracy: 100%", font=("Arial", 16))
        self.accuracy_label.pack(side="left", padx=10)
        
        self.reset_button = ctk.CTkButton(self.stats_frame, text="Reset", command=self.controller.reset_test)
        self.reset_button.pack(side="left", padx=10)

        self.stash_button = ctk.CTkButton(self.stats_frame, text="Stash Current Text", command=self.controller.stash_current_chapter)
        self.stash_button.pack(side="left", padx=10)

        # --- Navigation Buttons ---
        self.prev_chapter_button = ctk.CTkButton(self.stats_frame, text="< Prev",
                                                 command=lambda: self.controller.go_to_neighbor_chapter(-1),
                                                 state="disabled")
        self.prev_chapter_button.pack(side="left", padx=(20, 5))

        self.next_chapter_button = ctk.CTkButton(self.stats_frame, text="Next >",
                                                 command=lambda: self.controller.go_to_neighbor_chapter(1),
                                                 state="disabled")
        self.next_chapter_button.pack(side="left", padx=5)

        self.theme_switch = ctk.CTkSwitch(self.stats_frame, text="Toggle Dark Mode", command=self.controller.toggle_theme)
        self.theme_switch.pack(side="right", padx=10)

        # --- Text Frame for Typing ---
        self.text_frame = ctk.CTkFrame(self)
        self.text_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.text_display = Text(self.text_frame, wrap="word", font=("Arial", 22), 
                                 bg=self.controller._get_text_widget_colors(ctk.get_appearance_mode())[0], 
                                 fg=self.controller._get_text_widget_colors(ctk.get_appearance_mode())[1],
                                 borderwidth=0, highlightthickness=0, insertbackground=self.controller._get_text_widget_colors(ctk.get_appearance_mode())[1])
        self.text_display.pack(fill="both", expand=True)
        
        # Define tags for highlighting
        self.text_display.tag_configure("correct")
        self.text_display.tag_configure("incorrect", underline=True)
        self.text_display.tag_configure("untyped")
        self.text_display.tag_configure("corrected")

        # Bind events
        self.text_display.bind("<KeyPress>", self.controller.on_key_press)
