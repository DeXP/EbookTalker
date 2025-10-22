# loading_splash.py
import customtkinter as ctk
from PIL import Image


class LoadingSplashScreen:
    def __init__(self, app_name: str, image_path: str, image_size: tuple = (128, 128)):
        """
        Create a borderless, compact loading splash screen.
        Must be used on the main thread.
        """
        self.ask_for_exit = False
        
        # Create borderless window
        self.root = ctk.CTk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 480
        window_height = 160  # reduced height
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Layout
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        
        # Image (left)
        try:
            img = Image.open(image_path)
            img = img.resize(image_size, Image.LANCZOS)
            self.photo = ctk.CTkImage(light_image=img, dark_image=img, size=image_size)
            image_label = ctk.CTkLabel(self.root, image=self.photo, text="")
            image_label.grid(row=0, column=0, rowspan=4, padx=(16, 12), pady=(14, 0), sticky="nw")
        except Exception:
            placeholder = ctk.CTkLabel(
                self.root,
                text="APP",
                width=image_size[0],
                height=image_size[1],
                fg_color=("gray80", "gray20"),
                corner_radius=6,
                font=ctk.CTkFont(size=16, weight="bold")
            )
            placeholder.grid(row=0, column=0, rowspan=4, padx=(16, 12), pady=(14, 0), sticky="nw")
        
        # App name
        self.app_name_label = ctk.CTkLabel(
            self.root,
            text=app_name,
            font=ctk.CTkFont(size=17, weight="bold")
        )
        self.app_name_label.grid(row=0, column=1, padx=16, pady=(14, 2), sticky="w")
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.root,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray50"
        )
        self.status_label.grid(row=1, column=1, padx=16, pady=(0, 6), sticky="w")
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(self.root, mode="indeterminate", height=5)
        self.progress.grid(row=2, column=1, padx=16, pady=(0, 8), sticky="ew")
        self.progress.start()
        
        # Exit button
        self.exit_button = ctk.CTkButton(
            self.root,
            text="Exit",
            width=65,
            height=24,
            command=self._request_exit
        )
        self.exit_button.grid(row=3, column=1, padx=16, pady=(0, 12), sticky="e")
        
        self.root.protocol("WM_DELETE_WINDOW", self._request_exit)
    
    def _request_exit(self):
        self.ask_for_exit = True
    
    def status(self, text: str):
        if not self.ask_for_exit:
            self.status_label.configure(text=text)
    
    def update(self):
        if not self.ask_for_exit:
            self.root.update_idletasks()
            self.root.update()
    
    def show(self):
        self.root.deiconify()
        self.update()
    
    def hide(self):
        self.root.withdraw()
    
    def destroy(self):
        self.progress.stop()
        self.root.destroy()
    
    def is_exit_requested(self) -> bool:
        return self.ask_for_exit