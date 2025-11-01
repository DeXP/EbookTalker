import threading
import tkinter as tk
import customtkinter as ctk
from PIL import Image

from helpers.translation import TT
from helpers import settings


class AboutForm(ctk.CTkToplevel):
    def __init__(self, parent, tr: dict, cfg:dict, var: dict):
        super().__init__(parent)
        self.parent = parent

        self.tr = tr
        self.cfg = cfg
        self.var = var

        self.title(f"{tr['AboutApplication']}: {tr["appTitle"]}")
        self.geometry(parent.get_child_geometry(width=580, height=350))
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(6, weight=1)

        self.img = Image.open('static/book.png')
        width, height = self.img.size
        h = 128
        w = int((width * h) / height)
        image_size = (w, h)
        self.img = self.img.resize((w, h), Image.LANCZOS)
        self.photo = ctk.CTkImage(light_image=self.img, dark_image=self.img, size=image_size)
        self.cover_label = ctk.CTkLabel(self, image=self.photo, text="", fg_color="transparent")
        self.cover_label.grid(row=0, column=0, padx=20, pady=10, sticky="n", columnspan=1, rowspan=8)

        self.title_label = ctk.CTkLabel(self, text=tr["appTitle"])
        self.title_label.grid(row=0, column=1, pady=0, sticky="w")

        self.desc_label = ctk.CTkLabel(self, text=tr["appDescription"])
        self.desc_label.grid(row=1, column=1, pady=0, sticky="w")

        self.silero_label = ctk.CTkLabel(self, text=tr["silero-line"])
        self.silero_label.grid(row=2, column=1, pady=0, sticky="w")

        self.version_label = ctk.CTkLabel(self, text=f"{tr['appVersion']}: {parent.version}")
        self.version_label.grid(row=3, column=1, pady=0, sticky="w")

        self.author_label = ctk.CTkLabel(self, text=tr["appAuthor-line"])
        self.author_label.grid(row=4, column=1, pady=0, sticky="w")

        self.beta_testers_label = ctk.CTkLabel(self, text=tr["appBetaTesters-line"])
        self.beta_testers_label.grid(row=5, column=1, pady=0, sticky="w")

        self.sysinfo_text = ctk.CTkTextbox(self, height=120, width=400)
        #self.sysinfo_text.delete("0.0", "end")  # delete all text
        self.sysinfo_text.insert(tk.END, TT(tr, "Loading:") + " " + tr["SystemInformation"])
        self.sysinfo_text.configure(state="disabled")   
        self.sysinfo_text.grid(row=6, column=1, sticky="nswe")

        self.ok_button = ctk.CTkButton(self, text=tr['OK'], command=self.on_ok)
        self.ok_button.grid(row=7, column=0, columnspan=2, pady=7, sticky="s")

        # Start background work
        self.after(10, self._start_background_task)


    def _start_background_task(self):
        # Run the long-running task in a separate thread
        thread = threading.Thread(target=self._collect_stats, daemon=True)
        thread.start()


    def _collect_stats(self):
        # Simulate slow operation (e.g., gathering system info)
        stats = settings.get_system_info_str(self.var)

        # Schedule UI update on main thread
        self.after(0, self._update_textbox, stats)


    def _update_textbox(self, stats):
        # This runs on the main thread — safe to update UI
        self.sysinfo_text.configure(state="normal")
        self.sysinfo_text.delete("0.0", "end")
        self.sysinfo_text.insert("0.0", self.tr["SystemInformation"] + "\n\n" + stats)
        self.sysinfo_text.configure(state="disabled")
    

    def on_ok(self):
        self.destroy()