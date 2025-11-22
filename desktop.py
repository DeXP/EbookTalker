from tkinter import filedialog
from PIL import Image
import customtkinter
from pathlib import Path
from CTkMessagebox import CTkMessagebox
import sys, json, time, shutil, locale, datetime, multiprocessing, threading, subprocess

import defaults

from helpers import book, settings
from helpers.translation import T

APPNAME = "EbookTalker"
APPAUTHOR = "DeXPeriX"


# customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
# customtkinter.set_default_color_theme("blue")


class App(customtkinter.CTk):
    def __init__(self, tr: dict, cfg, var):
        super().__init__()
        
        from helpers.UI import Icons, ScrollableCTkTable
        self.converter = None
        self.tr = tr
        self.que = list()
        self.proc = ''
        self.cfg = cfg
        self.var = var
        self.icon_font = customtkinter.CTkFont(size=18)

        self.version = self.GetVersionExt()
        if not self.version:
            versionFile = Path('static/version.txt')
            if versionFile.exists():
                self.version = versionFile.read_text()
            else:
                self.version = '0.0.0'

        self.orig_title = f"{tr['appTitle']} ({self.version})"
        self.title(self.orig_title)
        self.geometry(self.get_geometry(width=920, height=600))
        self.grid_columnconfigure((0,1), weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.iconbitmap('static/favicon.ico')

        self.cover_label = customtkinter.CTkLabel(self, text="", fg_color="transparent")
        self.cover_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew", columnspan=1, rowspan=4)
        self.load_cover()

        self.inProcessTextLabel = customtkinter.CTkLabel(self, text=tr["inProcess:"])
        self.inProcessTextLabel.grid(row=0, column=1, padx=10, pady=2, sticky="w")

        self.inProcessLabel = customtkinter.CTkLabel(self, text=tr["emptyBookName"])
        self.inProcessLabel.grid(row=0, column=2, padx=10, pady=2, sticky="w")

        self.preferences_button = customtkinter.CTkButton(
            self, fg_color="transparent", hover_color=("gray80", "gray30"), text_color=("gray40", "gray60"),
            command=self.show_preferences, width=24, height=24,
            font=self.icon_font, text=Icons.options
        )
        self.preferences_button.grid(row=0, column=2, padx=(10,50), pady=0, sticky="e", columnspan=1)

        self.about_button = customtkinter.CTkButton(
            self, fg_color="transparent", hover_color=("gray80", "gray30"), text_color=("gray40", "gray60"),
            command=self.show_about, width=24, height=24,
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


        self.book_table = ScrollableCTkTable.ScrollableCTkTable(parent=self,
            headers=[tr["author"], tr["title"], tr["size"], tr["datetime"]]
        )
        self.book_table.grid(row=4, column=0, padx=10, pady=0, sticky="nswe", columnspan=3)


        self.add_button = customtkinter.CTkButton(self, text=tr["addBookToQueue"], command=self.on_add_button, border_spacing=10, state="disabled")
        self.add_button.grid(row=5, column=0, padx=10, pady=10, sticky="e", columnspan=3)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.update_thread = threading.Thread(target=self.update_UI, daemon=True)
        self.update_thread.start()

        # Start background work
        self.init_worker = threading.Thread(target=self.do_background_initialization, args=(tr, cfg, var), daemon=True)
        self.init_worker.start()


    def GetVersionExt(self):
        if (sys.platform == "win32") and hasattr(sys, 'frozen'):
            try:
                from win32api import GetFileVersionInfo, LOWORD, HIWORD
                info = GetFileVersionInfo(sys.executable, '\\')
                ms, ls = info['FileVersionMS'], info['FileVersionLS']
                major, minor, build = HIWORD(ms), LOWORD(ms), HIWORD(ls)
                return f"{major}.{minor}.{build}"
            except:
                return None
        return None


    def get_geometry(self, width: int, height: int) -> str:
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        return f"{width}x{height}+{x}+{y}"
    

    def get_child_geometry(self, width: int, height: int) -> str:
        self.update_idletasks()  # Ensure parent dimensions are current       
        parent_x, parent_y = self.winfo_x(), self.winfo_y()
        parent_width, parent_height = self.winfo_width(), self.winfo_height()
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        return f"{width}x{height}+{x}+{y}"


    def on_closing(self):
        #if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.var['askForExit'] = True
        time.sleep(1)
        self.destroy()    


    def on_add_button(self):
        if self.converter is None:
            return
        
        book_file_list = filedialog.askopenfilenames(filetypes=[(self.tr["Books"], 
            "*.txt *.epub *.fb2 *.fb2.zip *.fb2z *.txt.zip *.zip")])
        for book_file in book_file_list:
            book_path = Path(book_file)
            info, _ = book.ParseBook(book_path)
            new_file = var['queue'] / book.SafeBookFileName(info)

            if (info['lang'] in self.var['languages']) and not self.converter.IsModelFileExists(self.cfg, self.var, info['lang']):
                # Show language model downloading UI
                from helpers.UI.EbookTalkerInstallerUI import EbookTalkerInstallerUI
                installer_form = EbookTalkerInstallerUI(self, var, focus_tab='silero', preselect_key=info['lang'], automatic=True)
                installer_form.focus_force()
                installer_form.grab_set()
                self.wait_window(installer_form)

            shutil.copy(book_path, new_file)

            self.converter.fillQueue(self.que, self.var)
            self.refresh_queue()


    def show_preferences(self):
        from helpers.UI import PreferencesForm
        preferences_form = PreferencesForm.PreferencesForm(self, tr, cfg, var)
        preferences_form.grab_set()  # Make the preferences form modal


    def show_about(self):
        from helpers.UI import AboutForm
        about_form = AboutForm.AboutForm(self, tr, cfg, var)
        about_form.grab_set()


    def update_theme(self, theme):
        # Update the theme of the main form
        customtkinter.set_appearance_mode(theme)
        # print(f"Theme updated to: {theme}")


    def load_cover(self):
        cover = ''
        for c in self.var['genout'].glob("cover.*"):
            cover = c
        if not cover:
            cover = 'static/book.png'

        # Load and display an image 
        image_open = Image.open(cover)
        width, height = image_open.size
        w, h = 150, 180
        w = int((width * h) / height)
        image_size = (w,h)
        img = image_open.resize(image_size, Image.LANCZOS)
        self.photo = customtkinter.CTkImage(light_image=img, dark_image=img, size=image_size)
        self.cover_label.configure(image=self.photo)


    def refresh_queue(self):
        all_data = list()
        for info in self.que:
            new_row = [ book.AuthorName(info),
                       info['title'] or "",
                       T.SizeFormat(info['size'] or 0), 
                       datetime.datetime.fromtimestamp(info['datetime'] or 0).strftime(self.tr["datetimeFormat"])]
            all_data.append(new_row)

        self.book_table.update_table(all_data)


    def update_UI(self):
        while not self.var['askForExit']:
            if 'bookName' in self.proc:
                bookName = self.proc['bookName']
                prevBookName = self.inProcessLabel.cget("text")

                if bookName != prevBookName:
                    # Book got updated - refresh the UI
                    self.inProcessLabel.configure(text=bookName)
                    if self.converter is not None:
                        self.converter.fillQueue(self.que, self.var)
                    self.refresh_queue()
                    self.load_cover()
                    self.title(f"{self.orig_title} - [ {bookName} ]")

            if "rawSectionTitle" in self.proc:
                self.chapterLabel.configure(text=self.proc["rawSectionTitle"])

            if "sentenceText" in self.proc:
                self.readingLabel.configure(text=self.proc["sentenceText"])

            if ("totalSentences" in self.proc) and ("sentenceNumber" in self.proc) and ("bookName" in self.proc):
                percent = float(self.proc['sentenceNumber']) / (float(self.proc['totalSentences']) + 1)
                self.progressbar.set(percent)
                self.title(f"{self.orig_title} - [ {self.proc['bookName']} ] - {int(100*percent)}%")

            if ("status" in self.proc) and ('idle' == self.proc['status']) and ("..." != self.readingLabel.cget("text")):
                self.chapterLabel.configure(text="...")
                self.readingLabel.configure(text="...")
                self.inProcessLabel.configure(text=tr["emptyBookName"])
                self.title(self.orig_title)
                self.progressbar.set(0)
                self.load_cover()

            if (var["loading"]):
                self.inProcessLabel.configure(text= T.T("Loading:") + " " + var["loading"])

            time.sleep(0.2)


    def do_background_initialization(self, tr, cfg, var):
        T.Cat("status")
        var['loading'] = T.C("Creating variables")
        import multiprocessing
        self.manager = multiprocessing.Manager()
        self.que = self.manager.list()
        self.proc = self.manager.dict()
             
        haveTorch = True
        var['loading'] = T.C("Importing modules")
        try:
            import torch, converter
            var['loading'] = 'Torch ' + str(torch.__version__)
        except:
            haveTorch = False
     
        if haveTorch:
            var['loading'] = T.C("Initializing neural networks")
            converter.InitModels(cfg, var)

            var['loading'] = T.C("Starting converter worker")
            self.converter = converter
            if sys.platform == "win32":
                self.convert_worker = threading.Thread(target=converter.ConverterLoop, args=(self.que, self.proc, cfg, var), daemon=True)
            else:
                import multiprocessing
                self.convert_worker = multiprocessing.Process(target=converter.ConverterLoop, args=(self.que, self.proc, cfg, var))

            self.convert_worker.start()

            # Schedule UI update on main thread
            self.after(0, self._enable_ui, var)
        else:
            var['loading'] = T.C("Torch module not found. Initializing installation")
            from helpers.UI.EbookTalkerInstallerUI import EbookTalkerInstallerUI
            installer_form = EbookTalkerInstallerUI(self, var, focus_tab='torch')
            installer_form.focus_force()
            installer_form.grab_set()
            self.wait_window(installer_form)
            self.on_closing()


    def _enable_ui(self, var):
        # This runs on the main thread — safe to update UI
        var["loading"] = ''
        self.add_button.configure(state="normal")
        self.inProcessLabel.configure(text=tr["emptyBookName"])   



if __name__ == '__main__':
    multiprocessing.freeze_support()

    userFolders = settings.GetUserFolders(APPNAME, APPAUTHOR)
    with open("default.cfg", "rt") as f:
        cfg = dict((lambda l: (l[0].strip(" '\""), settings.ReplaceUserFolders(l[2][:-1].strip(" '\""), userFolders)))(line.partition("="))
                    for line in f)

    var = defaults.GetDefaultVar(cfg)
    var['settings'] = settings.LoadOrDefault(cfg, var)

    localeFile = 'ru.json' if ('rus' in locale.getlocale()[0].lower()) else 'en.json'
    localeFile = localeFile if not var['settings']['app']['lang'] else var['settings']['app']['lang'] + ".json"
    tr = None
    with open("static/i18n/" + localeFile, encoding='utf-8') as json_file:
        tr = json.load(json_file)
    T.Init(tr)

    try:
        import pyi_splash
        pyi_splash.close()
    except:
        pass

    app = App(tr, cfg, var)
    app.mainloop()
