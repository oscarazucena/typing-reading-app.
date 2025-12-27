import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, width=150)
        self.controller = controller

        self.practice_button = ctk.CTkButton(self, text="Practice", command=self.controller.show_practice_view)
        self.practice_button.pack(pady=10, padx=10, fill="x")

        self.library_button = ctk.CTkButton(self, text="Library", command=self.controller.show_library_view)
        self.library_button.pack(pady=10, padx=10, fill="x")

        # Future buttons
        self.stats_button = ctk.CTkButton(self, text="Stats", state="disabled")
        self.stats_button.pack(pady=10, padx=10, fill="x")

        self.settings_button = ctk.CTkButton(self, text="Settings", state="disabled")
        self.settings_button.pack(pady=10, padx=10, fill="x")
