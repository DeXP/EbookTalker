import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import customtkinter
from pathlib import Path
import sys, json, time, uuid, shutil, locale, datetime, multiprocessing, threading

import converter
from helpers import book, dxaudio, dxfs
from helpers.UI import Icons, PreferencesForm, AboutForm


# customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
# customtkinter.set_default_color_theme("blue")



class App(customtkinter.CTk):
    def __init__(self, tr: dict, que: list, proc, cfg, var):
        super().__init__()

        self.tr = tr
        self.que = que
        self.proc = proc
        self.cfg = cfg
        self.var = var

        self.sizeFmt = (tr["byte"], tr["KB"], tr["MB"], tr["GB"], tr["TB"], tr["PB"], "EiB", "ZiB")
        self.icon_font = customtkinter.CTkFont(size=18)

        self.version = Path('static/version.txt').read_text()

        self.orig_title = f"{tr['appTitle']} ({self.version})"
        self.title(self.orig_title)
        self.geometry(self.get_geometry(width=920, height=600))
        self.grid_columnconfigure((0,1), weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.iconbitmap('static/favicon.ico')

        self.imageBG = "white"
        if 'Dark' == customtkinter.get_appearance_mode():
            self.imageBG = "#242424"

            self.style = ttk.Style()
    
            self.style.theme_use("default")
    
            self.style.configure("Treeview",
                            background="#2a2d2e",
                            foreground="white",
                            fieldbackground="#343638",
                            bordercolor="#343638",
                            borderwidth=0)
            self.style.map('Treeview', background=[('selected', '#22559b')])
    
            self.style.configure("Treeview.Heading",
                            background="#565b5e",
                            foreground="white",
                            relief="flat")
            self.style.map("Treeview.Heading", background=[('active', '#3484F0')])
        
        ttk.Style().configure("Treeview", rowheight=30)
        
        # self.cover_label = customtkinter.CTkLabel(self, text="", image=self.default_cover)
        self.cover_label = ttk.Label(self, text="", background=self.imageBG)
        self.cover_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew", columnspan=1, rowspan=4)
        self.load_cover()

        self.inProcessTextLabel = customtkinter.CTkLabel(self, text=tr["inProcess:"])
        self.inProcessTextLabel.grid(row=0, column=1, padx=10, pady=2, sticky="w")

        self.inProcessLabel = customtkinter.CTkLabel(self, text=tr["emptyBookName"])
        self.inProcessLabel.grid(row=0, column=2, padx=10, pady=2, sticky="w")

        self.preferences_button = customtkinter.CTkButton(
            self, fg_color="transparent", border_color=self.imageBG,
            command=self.show_preferences, border_width=2, width=24, height=24,
            font=self.icon_font, text=Icons.options
        )
        self.preferences_button.grid(row=0, column=2, padx=(10,40), pady=0, sticky="e", columnspan=1)

        self.about_button = customtkinter.CTkButton(
            self, fg_color="transparent", border_color=self.imageBG,
            command=self.show_about, border_width=2, width=24, height=24,
            font=self.icon_font, text=Icons.info
        )
        self.about_button.grid(row=0, column=2, padx=10, pady=0, sticky="e", columnspan=1)


        self.chapterTextLabel = customtkinter.CTkLabel(self, text=tr["chapter:"])
        self.chapterTextLabel.grid(row=1, column=1, padx=10, pady=2, sticky="wn")

        self.chapterLabel = customtkinter.CTkLabel(self, text="...")
        self.chapterLabel.grid(row=1, column=2, padx=10, pady=2, sticky="wn")


        self.readingTextLabel = customtkinter.CTkLabel(self, text=tr["reading:"], height=56, anchor="nw")
        self.readingTextLabel.grid(row=2, column=1, padx=10, pady=2, sticky="w")

        self.readingLabel = customtkinter.CTkLabel(self, text="...", height=56, anchor="nw", wraplength=650)
        self.readingLabel.grid(row=2, column=2, padx=10, pady=2, sticky="w")

        self.progressbar = customtkinter.CTkProgressBar(self, orientation="horizontal")
        self.progressbar.set(0)
        self.progressbar.grid(row=3, column=1, padx=10, pady=10, sticky="nswe", columnspan=2)


        self.treeview = ttk.Treeview(columns=("lastName", "title", "seqNumber", "sequence", "size", "datetime"))
        self.treeview.heading("#0", text=tr["firstName"])
        self.treeview.column("#0", minwidth=70, width=120, anchor='center')
        self.treeview.heading("lastName", text=tr["lastName"])
        self.treeview.column("lastName", minwidth=70, width=120, anchor='center')
        self.treeview.heading("title", text=tr["title"])
        self.treeview.column("title", minwidth=80, width=250, anchor='center')
        self.treeview.heading("seqNumber", text=tr["seqNumber"])
        self.treeview.column("seqNumber", minwidth=20, width=30, anchor='center')
        self.treeview.heading("sequence", text=tr["sequence"])
        self.treeview.column("sequence", minwidth=80, width=170, anchor='center')
        self.treeview.heading("size", text=tr["size"])
        self.treeview.column("size", minwidth=40, width=70, anchor='center')
        self.treeview.heading("datetime", text=tr["datetime"])
        self.treeview.column("datetime", minwidth=90, width=150, anchor='center')
        # self.treeview.insert(
        #     "",
        #     tk.END,
        #     text="Ольга",
        #     values=("Громыко", "Профессия Ведьма", "1", "Белорский цикл", "234 KБ", "15.03.2025 12:34")
        # )
        self.treeview.grid(row=4, column=0, padx=10, pady=0, sticky="nswe", columnspan=3)

        self.add_button = customtkinter.CTkButton(self, text=tr["addBookToQueue"], command=self.add_button_callback, border_spacing=10)
        self.add_button.grid(row=5, column=0, padx=10, pady=10, sticky="e", columnspan=3)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.update_thread = threading.Thread(target=self.update_UI).start()


    def get_geometry(self, width: int, height: int):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        return f"{width}x{height}+{x}+{y}"

    def on_closing(self):
        #if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.var['askForExit'] = True
        self.destroy()


    def add_button_callback(self):
        book_file = filedialog.askopenfilename(filetypes=[(self.tr["Books"], "*.txt *.epub *.fb2 *.fb2.zip *.fb2z *.txt.zip")])
        if book_file:
            book_path = Path(book_file)
            info, _ = book.ParseBook(book_path)
            info['file'] = book.SafeBookName(info) + "." + info['ext']
            new_file = var['queue'] / info['file']
            shutil.copy(book_path, new_file)

            converter.fillQueue(self.que, self.var)
            self.refresh_queue()


    def show_preferences(self):
        preferences_form = PreferencesForm.PreferencesForm(self, tr, cfg, var)
        preferences_form.grab_set()  # Make the preferences form modal


    def show_about(self):
        about_form = AboutForm.AboutForm(self, tr, cfg, var)
        about_form.grab_set()


    def update_theme(self, theme):
        # Update the theme of the main form
        customtkinter.set_appearance_mode(theme)
        print(f"Theme updated to: {theme}")


    def load_cover(self):
        cover = ''
        for c in self.var['genout'].glob("cover.*"):
            cover = c
        if not cover:
            cover = 'static/default-cover.png'

        # Load and display an image 
        image_open = Image.open(cover)
        width, height = image_open.size
        w, h = 150, 180
        w = int((width * h) / height)

        img = image_open.resize((w,h))
        self.cover_img = ImageTk.PhotoImage(img)
        self.cover_label.configure(image=self.cover_img)


    def sizeof_fmt(self, num):
        for unit in self.sizeFmt:
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f}YiB"


    def refresh_queue(self):
        for row in self.treeview.get_children():
            self.treeview.delete(row)

        for book in self.que:
            self.treeview.insert(
                "",
                tk.END,
                text=book['firstName'] or "",
                values=(book['lastName'] or "",
                        book['title'] or "", 
                        book['seqNumber'] or "", 
                        book['sequence'] or "", 
                        self.sizeof_fmt(book['size'] or 0), 
                        datetime.datetime.fromtimestamp(book['datetime'] or 0).strftime(self.tr["datetimeFormat"])
                )
            )


    def update_UI(self):
        while not self.var['askForExit']:
            if 'bookName' in self.proc:
                bookName = self.proc['bookName']
                prevBookName = self.inProcessLabel.cget("text")

                if bookName != prevBookName:
                    # Book got updated - refresh the UI
                    self.inProcessLabel.configure(text=bookName)
                    converter.fillQueue(self.que, self.var)
                    self.refresh_queue()
                    self.load_cover()
                    self.title(f"{self.orig_title} - [ {bookName} ]")

            if "sectionTitle" in self.proc:
                self.chapterLabel.configure(text=self.proc["sectionTitle"])

            if "sentenceText" in self.proc:
                self.readingLabel.configure(text=self.proc["sentenceText"])

            if ("totalSentences" in self.proc) and ("sentenceNumber" in self.proc):
                percent = float(self.proc['sentenceNumber']) / (float(self.proc['totalSentences']) + 1)
                self.progressbar.set(percent)
                self.title(f"{self.orig_title} - [ {self.proc['bookName']} ] - {int(100*percent)}%")

            if ("status" in self.proc) and ('idle' == self.proc['status']) and ("..." != self.readingLabel.cget("text")):
                self.chapterLabel.configure(text="...")
                self.readingLabel.configure(text="...")
                self.inProcessLabel.configure(text=tr["emptyBookName"])
                self.title(self.orig_title)
                self.progressbar.set(0)

            time.sleep(1)



if __name__ == '__main__':
    multiprocessing.freeze_support()

    with open("default.cfg", "rt") as f:
        cfg = dict((lambda l: (l[0].strip(" '\""), l[2][:-1].strip(" '\"")))(line.partition("="))
                    for line in f)
    
    manager = multiprocessing.Manager()
    global que, proc, var
    que = manager.list()
    proc = manager.dict()
    var = converter.Init(cfg)

    localeFile = 'ru.json' if ('rus' in locale.getlocale()[0].lower()) else 'en.json'
    localeFile = localeFile if not var['settings']['app']['lang'] else var['settings']['app']['lang']
    tr = None
    with open("static/i18n/" + localeFile, encoding='utf-8') as json_file:
        tr = json.load(json_file)

    if sys.platform == "win32":
        p = threading.Thread(target=converter.ConverterLoop, args=(que, proc, cfg, var))
    else:
        p = multiprocessing.Process(target=converter.ConverterLoop, args=(que, proc, cfg, var))

    p.start()

    try:
        import pyi_splash
        pyi_splash.close()
    except:
        pass

    app = App(tr, que, proc, cfg, var)
    app.mainloop()
