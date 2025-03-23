import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path

from helpers.UI import Icons

class AboutForm(ctk.CTkToplevel):
    def __init__(self, parent, tr: dict, cfg:dict, var: dict):
        super().__init__(parent)
        self.parent = parent

        self.tr = tr
        self.cfg = cfg
        self.var = var

        self.title(f"{tr['AboutApplication']}: {tr["appTitle"]}")
        self.geometry(parent.get_geometry(width=750, height=320))
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        image_open = Image.open('static/default-cover.png')
        width, height = image_open.size
        h = 300
        w = int((width * h) / height)
        resized_img = image_open.resize((w,h))
        self.img = ImageTk.PhotoImage(resized_img)
        self.cover_label = ttk.Label(self, text="", image=self.img, background=parent.imageBG)
        self.cover_label.grid(row=0, column=0, padx=20, pady=10, sticky="ew", columnspan=1, rowspan=6)

        self.title_label = ctk.CTkLabel(self, text=tr["appTitle"])
        self.title_label.grid(row=0, column=1, sticky="w")

        self.desc_label = ctk.CTkLabel(self, text=tr["appDescription"])
        self.desc_label.grid(row=1, column=1, sticky="w")

        self.version_label = ctk.CTkLabel(self, text=f"{tr['appVersion']}: {parent.version}")
        self.version_label.grid(row=2, column=1, sticky="w")

        self.author_label = ctk.CTkLabel(self, text=tr["appAuthor-line"])
        self.author_label.grid(row=3, column=1, sticky="w")

        self.beta_testers_label = ctk.CTkLabel(self, text=tr["appBetaTesters-line"])
        self.beta_testers_label.grid(row=4, column=1, sticky="w")


        self.ok_button = ctk.CTkButton(self, text=tr['OK'], command=self.on_ok)
        self.ok_button.grid(row=5, column=1)
    

    def on_ok(self):
        self.destroy()