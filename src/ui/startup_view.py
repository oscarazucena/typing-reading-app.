import customtkinter as ctk

class StartupView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        # Main layout frames
        self.grid_columnconfigure(0, weight=1)

        # --- Title and New Chapter Frame ---
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        top_frame.grid_columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(top_frame, text="Start Typing", font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        url_label = ctk.CTkLabel(top_frame, text="New Chapter URL:")
        url_label.grid(row=1, column=0, padx=(0, 5), sticky="w")

        self.url_entry = ctk.CTkEntry(top_frame)
        self.url_entry.grid(row=1, column=1, padx=5, sticky="ew")

        fetch_button = ctk.CTkButton(top_frame, text="Fetch", command=self.controller.fetch_chapter_from_url)
        fetch_button.grid(row=1, column=2, padx=(5, 0))

        toc_url_label = ctk.CTkLabel(top_frame, text="Table of Contents URL:")
        toc_url_label.grid(row=2, column=0, padx=(0, 5), pady=(10, 0), sticky="w")

        self.toc_url_entry = ctk.CTkEntry(top_frame)
        self.toc_url_entry.grid(row=2, column=1, padx=5, pady=(10, 0), sticky="ew")

        self.chapter_limit_entry = ctk.CTkEntry(top_frame, width=50)
        self.chapter_limit_entry.grid(row=2, column=2, padx=5, pady=(10, 0), sticky="w")
        self.chapter_limit_entry.insert(0, "10")

        fetch_all_button = ctk.CTkButton(top_frame, text="Fetch All", command=self.controller.fetch_all_chapters_from_toc)
        fetch_all_button.grid(row=2, column=3, padx=(5, 0), pady=(10, 0))
        
        # --- Progress Bar ---
        self.progress_bar = ctk.CTkProgressBar(top_frame)
        self.progress_bar.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(15, 5))
        self.progress_bar.set(0) # Initially hidden

        # --- Stashed Chapters Button ---
        stashed_button = ctk.CTkButton(self, text="View Stashed Chapters", command=self.controller.show_stash_view)
        stashed_button.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 10))

        # --- Quit Button ---
        quit_button = ctk.CTkButton(self, text="Quit", command=self.controller.quit)
        quit_button.grid(row=2, column=0, pady=(0, 10))
