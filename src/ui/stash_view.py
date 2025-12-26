import customtkinter as ctk

class StashView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- Title ---
        self.title_label = ctk.CTkLabel(self, text="Stashed Books", font=("Arial", 20, "bold"))
        self.title_label.grid(row=0, column=0, pady=(10, 5))

        # --- Skip to Chapter Frame (will be populated dynamically) ---
        self.skip_frame = ctk.CTkFrame(self)
        self.skip_frame.grid_columnconfigure(1, weight=1)
        
        self.skip_label = ctk.CTkLabel(self.skip_frame, text="Skip to Chapter:")
        self.skip_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.skip_entry = ctk.CTkEntry(self.skip_frame, width=60)
        self.skip_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.skip_button = ctk.CTkButton(self.skip_frame, text="Go") # Command will be set dynamically
        self.skip_button.grid(row=0, column=2, padx=5, pady=5)

        # --- Stashed Items List ---
        self.stashed_items_list = ctk.CTkScrollableFrame(self)
        self.stashed_items_list.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

        # --- Back Button ---
        back_button = ctk.CTkButton(self, text="< Back to Main Menu", command=self.controller.show_startup_view)
        back_button.grid(row=3, column=0, pady=10)
