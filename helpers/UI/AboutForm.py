import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path

from helpers.UI import Icons
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

        image_open = Image.open('static/book.png')
        width, height = image_open.size
        h = 128
        w = int((width * h) / height)
        resized_img = image_open.resize((w,h))
        self.img = ImageTk.PhotoImage(resized_img)
        self.cover_label = ttk.Label(self, text="", image=self.img, background=parent.imageBG, anchor="n")
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

        sysinfo_str = settings.get_system_info_str()
        self.sysinfo_text = ctk.CTkTextbox(self, height=120, width=400)
        #self.sysinfo_text.delete("0.0", "end")  # delete all text
        self.sysinfo_text.insert(tk.END, tr["SystemInformation"] + "\n\n" + sysinfo_str) 
        self.sysinfo_text.grid(row=6, column=1, sticky="nswe")

        self.ok_button = ctk.CTkButton(self, text=tr['OK'], command=self.on_ok)
        self.ok_button.grid(row=7, column=0, columnspan=2, pady=7, sticky="s")
    

    def on_ok(self):
        self.destroy()