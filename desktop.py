import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import customtkinter
from pathlib import Path
from CTkTable import CTkTable
import sys, json, time, shutil, locale, datetime, multiprocessing, threading, platformdirs

import converter
from helpers import book
from helpers.UI import Icons, PreferencesForm, AboutForm, ScrollableCTkTable, loading_splash
from helpers.translation import TT


# customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
# customtkinter.set_default_color_theme("blue")


class App(customtkinter.CTk):
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


    def __init__(self, tr: dict, que: list, proc, cfg, var):
        super().__init__()

        self.tr = tr
        self.que = que
        self.proc = proc
        self.cfg = cfg
        self.var = var

        self.sizeFmt = (tr["byte"], tr["KB"], tr["MB"], tr["GB"], tr["TB"], tr["PB"], "EiB", "ZiB")
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
    

    def get_child_geometry(self, width: int, height: int):
        self.update_idletasks()  # Ensure parent dimensions are current       
        parent_x, parent_y = self.winfo_x(), self.winfo_y()
        parent_width, parent_height = self.winfo_width(), self.winfo_height()
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        return f"{width}x{height}+{x}+{y}"


    def on_closing(self):
        #if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.var['askForExit'] = True
        self.destroy()


    def add_button_callback(self):
        book_file = filedialog.askopenfilename(filetypes=[(self.tr["Books"], 
            "*.txt *.epub *.fb2 *.fb2.zip *.fb2z *.txt.zip *.zip")])
        if book_file:
            book_path = Path(book_file)
            info, _ = book.ParseBook(book_path)
            new_file = var['queue'] / book.SafeBookFileName(info)
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


    def sizeof_fmt(self, num):
        for unit in self.sizeFmt:
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f}YiB"


    def refresh_queue(self):
        all_data = list()
        for info in self.que:
            new_row = [ book.AuthorName(info),
                       info['title'] or "",
                       self.sizeof_fmt(info['size'] or 0), 
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
                    converter.fillQueue(self.que, self.var)
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

            time.sleep(1)


def replace_substrings(s: str, replacements) -> str:
    for key, value in replacements.items():
        s = s.replace(key, value)
    return s


def terminate_background_requested(splash, res):
    if splash.is_exit_requested():
        res['cancelled'] = True
        return True
    

def do_background_initialization(splash, res, appname, appauthor):
    global tr
    res['status'] = "Init..."

    userFolders = {
        '##HOME##': str(Path.home().absolute()),
        '##MUSIC##': platformdirs.user_music_dir(),
        '##LOGS##': platformdirs.user_log_dir(appname, appauthor),
        '##CONFIG##': platformdirs.user_config_dir(appname, appauthor),
        '##APPDATA##': platformdirs.user_data_dir(appname, appauthor, roaming=True), # synchronized
        '##LOCALAPPDATA##': platformdirs.user_data_dir(appname, appauthor)
    }
    
    with open("default.cfg", "rt") as f:
        res['cfg'] = dict((lambda l: (l[0].strip(" '\""), replace_substrings(l[2][:-1].strip(" '\""), userFolders)))(line.partition("="))
                    for line in f)
        
    var = converter.Init(res['cfg'])

    if terminate_background_requested(splash, res):
        return
    
    localeFile = 'ru.json' if ('rus' in locale.getlocale()[0].lower()) else 'en.json'
    localeFile = localeFile if not var['settings']['app']['lang'] else var['settings']['app']['lang'] + ".json"
    tr = None
    with open("static/i18n/" + localeFile, encoding='utf-8') as json_file:
        tr = json.load(json_file)
    res['tr'] = tr

    if terminate_background_requested(splash, res):
        return

    
    res['status'] = TT(tr, "Creating variables", "status")
    res['manager'] = multiprocessing.Manager()
    res['que'] = res['manager'].list()
    res['proc'] = res['manager'].dict()

    if terminate_background_requested(splash, res):
        return

    res['status'] = TT(tr, "Initializing neural networks", "status")
    var = converter.InitModels(res['cfg'], var)
    res['var'] = var

    if terminate_background_requested(splash, res):
        return

    res['success'] = True


if __name__ == '__main__':
    global que, proc, var, cfg, tr
    appname = "EbookTalker"
    appauthor = "DeXPeriX"
    multiprocessing.freeze_support()

    try:
        import pyi_splash
        pyi_splash.close()
    except:
        pass

    splash = loading_splash.LoadingSplashScreen(app_name=appname, image_path='static/book.png', icon="static/favicon.ico", topmost=True)
    splash.show()

    # Start background work
    res = {'status': '', 'success': False, 'cancelled': False, 'error': None, 'translated': False}
    init_worker = threading.Thread(target=do_background_initialization, args=(splash, res, appname, appauthor), daemon=True)
    init_worker.start()

    while init_worker.is_alive():
        if res['status']:
            splash.status(res['status'])
            res['status'] = ''
        if ('tr' in res) and not res['translated']:
            splash.set_title(TT(tr, "appTitle"))
            res['translated'] = True
        if splash.is_exit_requested():
            splash.hide()
        splash.update()
        time.sleep(0.05)

    if splash.is_exit_requested():
        splash.destroy()
    else:
        que, proc, var, cfg, tr = res['que'], res['proc'], res['var'], res['cfg'], res['tr']

        if sys.platform == "win32":
            p = threading.Thread(target=converter.ConverterLoop, args=(que, proc, cfg, var))
        else:
            p = multiprocessing.Process(target=converter.ConverterLoop, args=(que, proc, cfg, var))

        p.start()

        splash.hide()
        splash.destroy()

        app = App(tr, que, proc, cfg, var)
        app.mainloop()
