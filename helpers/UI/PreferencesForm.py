import sys, json
import customtkinter as ctk
from tkinter import filedialog

import converter
from helpers import settings
from helpers.UI import Icons


class PreferencesForm(ctk.CTkToplevel):
    def __init__(self, parent, tr: dict, cfg:dict, var: dict):
        super().__init__(parent)
        self.parent = parent

        self.tr = tr
        self.cfg = cfg
        self.var = var

        self.title(tr['Preferences'])
        self.geometry(parent.get_child_geometry(width=500, height=280))

        self.grid_columnconfigure((0,2), weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)


        
        self.lang_label = ctk.CTkLabel(self, text=tr['Language:'])
        self.lang_label.grid(row=0, column=0, padx=10, pady=2, sticky="w")

        self.supported_languages = {
            '': tr["Default"], 
            'ru': var['ru']['name'], 
            'en': var['en']['name']
        }
        self.lang_combobox = ctk.CTkComboBox(self, values=list(self.supported_languages.values()), state="readonly")
        self.lang_combobox.set(self.get_lang_by_code(var['settings']['app']['lang']))
        self.lang_combobox.grid(row=0, column=1, padx=10, pady=2, columnspan=2, sticky="w")


        self.output_label = ctk.CTkLabel(self, text=tr['OutputFolder:'])
        self.output_label.grid(row=1, column=0, padx=10, pady=2, sticky="w")

        self.output_text = ctk.CTkEntry(self)
        self.output_text.insert(0, var['settings']['app']['output'])
        self.output_text.grid(row=1, column=1, padx=10, pady=2, sticky="ew")

        self.output_browse_button = ctk.CTkButton(
            self, width=30, border_width=2,
            fg_color="transparent", border_color=parent.imageBG,
            command=self.get_output_folder,
            font=parent.icon_font, text=Icons.folder_open
        )
        self.output_browse_button.grid(row=1, column=2, padx=(0, 10), pady=2)


        self.codec_label = ctk.CTkLabel(self, text=tr['Codec:'])
        self.codec_label.grid(row=2, column=0, padx=10, pady=2, sticky="w")

        self.codec_combobox = ctk.CTkComboBox(self, values=converter.GetSupportedAudioFormats(cfg, var), state="readonly")
        self.codec_combobox.set(var['settings']['app']['codec'])
        self.codec_combobox.grid(row=2, column=1, columnspan=2, padx=10, pady=2, sticky="w")


        self.dir_formats = {
            'single': tr["nf-single"],
            'short': tr["nf-short"],
            'full': tr["nf-full"]
        }
        self.dirs_label = ctk.CTkLabel(self, text=tr['NamingFormat:'])
        self.dirs_label.grid(row=3, column=0, padx=10, pady=2, sticky="w")

        self.dirs_combobox = ctk.CTkComboBox(self, values=list(self.dir_formats.values()), state="readonly")
        self.dirs_combobox.set(self.dir_formats.get(var['settings']['app']['dirs'], tr["nf-single"]))
        self.dirs_combobox.grid(row=3, column=1, padx=10, pady=2, columnspan=2, sticky="w")



        self.tts_tabview = ctk.CTkTabview(self, width=250)
        self.tts_tabview.grid(row=4, column=0, padx=10, pady=2, sticky="nsew", columnspan=3)
        self.tts_tabview.configure(command=self.on_tab_change)
        self.tts_voice_labels = {}
        self.tts_voice_combos = {}
        self.tts_voice_play_buttons = {}
        for lang in var['languages']:
            lang_name = var[lang]['name']
            self.tts_tabview.add(lang_name)
            self.tts_tabview.tab(lang_name).grid_columnconfigure((0,1,2), weight=0)
            voice_parent = self.tts_tabview.tab(lang_name)

            self.tts_voice_labels[lang] = ctk.CTkLabel(voice_parent, text=tr["Voice:"])
            self.tts_voice_labels[lang].grid(row=0, column=0, padx=10, pady=2, sticky="w")

            self.tts_voice_combos[lang] = ctk.CTkComboBox(voice_parent, state="readonly")
            self.tts_voice_combos[lang].set(var['settings']['silero'][lang]['voice'])
            self.tts_voice_combos[lang].grid(row=0, column=1, padx=10, pady=2, sticky="w")

            self.tts_voice_play_buttons[lang] = ctk.CTkButton(
                voice_parent, width=30, border_width=2,
                fg_color="transparent", border_color=parent.imageBG,
                command=lambda lang=lang: self.on_play('silero', lang),
                font=parent.icon_font, text=Icons.play
            )
            if sys.platform == "win32":
                self.tts_voice_play_buttons[lang].grid(row=0, column=2, padx=10, pady=2, sticky="w")


        first_lang = var['languages'][0]
        self.tts_voice_combos[first_lang].configure(values=converter.GetModel(var, first_lang).speakers)




        # Save and Cancel buttons
        self.save_button = ctk.CTkButton(self, text=tr["Save"], command=self.on_save)
        self.save_button.grid(row=5, column=0, padx=10, pady=7)

        self.cancel_button = ctk.CTkButton(self, text=tr["Cancel"], command=self.on_cancel)
        self.cancel_button.grid(row=5, column=1, padx=10, pady=7, columnspan=2, sticky="e")


    def on_save(self):
        # Save preferences logic
        s = settings.LoadOrDefault(self.cfg, self.var)
        s['app']['lang'] = self.get_code_by_lang(self.lang_combobox.get())
        s['app']['output'] = self.output_text.get()
        s['app']['codec'] = self.codec_combobox.get()
        s['app']['dirs'] = self.get_dir_format_by_translated(self.dirs_combobox.get())

        for lang in self.var['languages']:
            s['silero'][lang]['voice'] = self.tts_voice_combos[lang].get()

        with open(self.cfg['SETTINGS_FILE'], 'w', encoding='utf-8') as f:
            json.dump(s, f, indent=2, ensure_ascii=False)

        self.var['settings'] = s

        self.destroy()


    def on_cancel(self):
        # Cancel logic
        self.destroy()


    def on_play(self, tts, lang):
        voice = self.tts_voice_combos[lang].get()
        wavName = f"{tts}-{lang}-{voice}.wav"
        wavFile = self.var['tmp'] / wavName

        if converter.SayText(wavFile, lang, voice, self.var[lang]['phrase'], self.var):
            if sys.platform == "win32":
                import winsound
                winsound.PlaySound(str(wavFile.absolute()), winsound.SND_ALIAS)


    def get_output_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_text.delete(0, "end")
            self.output_text.insert(0, folder_path)


    def on_tab_change(self):
        selected_tab = self.tts_tabview.get()  # Get the currently selected tab name
        lang = self.get_code_by_lang(selected_tab)
        self.tts_voice_combos[lang].configure(values=converter.GetModel(self.var, lang).speakers)


    def get_lang_by_code(self, value: str):
        return self.supported_languages.get(value, self.supported_languages[''])
    

    def get_code_by_lang(self, value: str):
        for lang in self.var['languages']:
            if value == self.var[lang]['name']:
                return lang
        return ''
    

    def get_dir_format_by_translated(self, value: str):
        for key in self.dir_formats:
            if value == self.dir_formats[key]:
                return key
        return ''