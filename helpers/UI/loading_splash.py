# loading_splash.py
import customtkinter as ctk
from PIL import Image, ImageTk


class LoadingSplashScreen:
    def __init__(
        self,
        app_name: str,
        image_path: str,
        icon: str = None,
        image_size: tuple = (128, 128),
        topmost: bool = False
    ):
        """
        Create a theme-aware loading splash screen.
        
        Args:
            app_name: Initial application title
            image_path: Path to app logo (PNG recommended)
            icon: Optional path to window/taskbar icon (.ico or .png)
            image_size: Display size for logo (default: 128x128)
            topmost: If True, stays above all windows (no taskbar entry).
                     If False (default), appears in taskbar and can be overlapped.
        """
        self.ask_for_exit = False
        
        # Create window
        self.root = ctk.CTk()
        self.root.overrideredirect(True)  # No OS decorations
        
        # Taskbar icon & window management
        if not topmost:
            # Re-enable decorations just enough to get taskbar presence
            # but keep borderless appearance
            self.root.overrideredirect(False)
            self.root.attributes("-toolwindow", False)
            # Optional: set window title for taskbar tooltip
            self.root.title(app_name)
        else:
            self.root.attributes("-topmost", True)
        
        # Set icon if provided
        if icon:
            try:
                if icon.lower().endswith(".ico"):
                    self.root.iconbitmap(icon)
                else:
                    # Use PIL to load PNG/GIF and convert for iconphoto
                    img = Image.open(icon)
                    icon_img = ImageTk.PhotoImage(img)
                    self.root.iconphoto(False, icon_img)
                    # Keep reference to avoid garbage collection
                    self._icon_ref = icon_img
            except Exception as e:
                print(f"Warning: Could not set window icon '{icon}': {e}")
        
        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 480
        window_height = 160
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
            image_label = ctk.CTkLabel(
                self.root,
                image=self.photo,
                text="",
                fg_color="transparent"
            )
            image_label.grid(row=0, column=0, rowspan=4, padx=(16, 12), pady=(14, 0), sticky="nw")
        except Exception:
            placeholder = ctk.CTkLabel(
                self.root,
                text="APP",
                width=image_size[0],
                height=image_size[1],
                fg_color=("gray85", "gray20"),
                corner_radius=6,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=("gray20", "gray90")
            )
            placeholder.grid(row=0, column=0, rowspan=4, padx=(16, 12), pady=(14, 0), sticky="nw")
        
        # App name
        self.app_name_label = ctk.CTkLabel(
            self.root,
            text=app_name,
            font=ctk.CTkFont(size=17, weight="bold"),
            fg_color="transparent"
        )
        self.app_name_label.grid(row=0, column=1, padx=16, pady=(14, 2), sticky="w")
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.root,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray50",
            fg_color="transparent"
        )
        self.status_label.grid(row=1, column=1, padx=16, pady=(0, 6), sticky="w")
        
        # Taller progress bar (height=8)
        self.progress = ctk.CTkProgressBar(self.root, mode="indeterminate", height=8)
        self.progress.grid(row=2, column=1, padx=16, pady=(0, 8), sticky="ew")
        self.progress.start()
        
        if topmost:
            # Close button ("×")
            self.exit_button = ctk.CTkButton(
                self.root,
                text="×",
                width=28,
                height=28,
                corner_radius=7,
                fg_color="transparent",
                hover_color=("gray80", "gray30"),
                text_color=("gray40", "gray60"),
                hover=True,
                command=self._request_exit
            )
            self.exit_button.grid(row=0, column=1, padx=(0, 12), pady=(12, 0), sticky="ne")
            
        self.root.protocol("WM_DELETE_WINDOW", self._request_exit)
    
    def _request_exit(self):
        self.ask_for_exit = True
    
    def set_title(self, title: str):
        """Update the app title (e.g., after localization)."""
        self.app_name_label.configure(text=title)
        # Also update window title if visible in taskbar
        try:
            self.root.title(title)
        except Exception:
            pass  # Ignore if window is destroyed
    
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