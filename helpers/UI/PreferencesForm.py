import sys, json
import customtkinter as ctk
from tkinter import filedialog
from playsound import playsound
from pathlib import Path

import converter
from helpers import book, settings
from helpers.UI import Icons
from helpers.translation import T

from helpers.DownloadItem import DownloadItem


class PreferencesForm(ctk.CTkToplevel):
    def __init__(self, parent, tr: dict, cfg:dict, var: dict):
        super().__init__(parent)
        self.parent = parent

        self.tr = tr
        self.cfg = cfg
        self.var = var

        self.title(tr['Preferences'])
        self.geometry(parent.get_child_geometry(width=600, height=500))

        self.grid_columnconfigure((0,2), weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(7, weight=1)


        self.testBook = book.GetTestBook(tr)
        
        self.lang_label = ctk.CTkLabel(self, text=tr['InterfaceLanguage:'])
        self.lang_label.grid(row=0, column=0, padx=10, pady=2, sticky="w")

        self.supported_languages = {
            '': tr["Default"], 
            'ru': var['languages']['ru'].name, 
            'en': var['languages']['en'].name
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
            self, width=30,
            fg_color="transparent", hover_color=("gray80", "gray30"), text_color=("gray40", "gray60"),
            command=self.get_output_folder,
            font=parent.icon_font, text=Icons.folder_open
        )
        self.output_browse_button.grid(row=1, column=2, padx=(0, 10), pady=2)


        self.codec_label = ctk.CTkLabel(self, text=tr['Codec:'])
        self.codec_label.grid(row=2, column=0, padx=10, pady=2, sticky="w")

        self.codec_combobox = ctk.CTkComboBox(self, values=converter.GetSupportedAudioFormats(cfg, var), state="readonly")
        self.codec_combobox.set(var['settings']['app']['codec'])
        self.codec_combobox.grid(row=2, column=1, columnspan=2, padx=10, pady=2, sticky="w")


        self.bitrate_label = ctk.CTkLabel(self, text=tr['Bitrate:'])
        self.bitrate_label.grid(row=3, column=0, padx=10, pady=2, sticky="w")

        self.available_bitrate = ['32', '64', '128', '192', '320']
        self.bitrate_combobox = ctk.CTkComboBox(self, values=self.available_bitrate, state="readonly")
        self.bitrate_combobox.set(var['settings']['app']['bitrate'])
        self.bitrate_combobox.grid(row=3, column=1, columnspan=2, padx=10, pady=2, sticky="w")


        self.dir_formats = {
            'single': tr["nf-single"],
            'short': tr["nf-short"],
            'full': tr["nf-full"]
        }
        self.dirs_label = ctk.CTkLabel(self, text=tr['NamingFormat:'])
        self.dirs_label.grid(row=4, column=0, padx=10, pady=2, sticky="w")

        self.dirs_combobox = ctk.CTkComboBox(self, values=list(self.dir_formats.values()), state="readonly", command=self.on_dirs_changed)
        self.dirs_combobox.set(self.dir_formats.get(var['settings']['app']['dirs'], tr["nf-short"]))
        self.dirs_combobox.grid(row=4, column=1, padx=10, pady=2, columnspan=2, sticky="w")


        self.dirs_example_label = ctk.CTkLabel(self, text=tr['Example:'])
        self.dirs_example_label.grid(row=5, column=0, padx=10, pady=2, sticky="w")

        self.dirs_example = ctk.CTkLabel(self, text=self.GetNiceTestBookName(var['settings']['app']['dirs']))
        self.dirs_example.grid(row=5, column=1, padx=10, pady=2, sticky="w")


        self.engines = {
            'silero': 'Silero'
        }
        for coqui_key, coqui_item in var['coqui-ai'].items():
            if converter.IsModelFileExists(cfg, var, engine=coqui_key, strict=True):
                self.engines[coqui_key] = coqui_item.name

        self.engine_label = ctk.CTkLabel(self, text=T.T('TTS Engine:'))
        self.engine_label.grid(row=6, column=0, padx=10, pady=2, sticky="w")

        current_engine = self.engines.get(var['settings']['app']['engine'], self.engines['silero'])
        self.engine_combobox = ctk.CTkComboBox(self, values=list(self.engines.values()), state="readonly", command=self.on_engine_changed)
        self.engine_combobox.set(current_engine)
        self.engine_combobox.grid(row=6, column=1, padx=10, pady=2, columnspan=2, sticky="w")


        self.tts_tabview = ctk.CTkTabview(self)
        self.tts_tabview.grid(row=7, column=0, padx=10, pady=2, sticky="nsew", columnspan=3)
        self.tts_tabview.configure(command=self.on_tab_change)
        self.tts_voice_labels = {}
        self.tts_voice_combos = {}
        self.tts_voice_play_buttons = {}
        self.tts_multi_voice_language_labels = {}
        self.tts_multi_voice_language_combos = {}
        self.first_silero_lang = None
        for lang, language in var['languages'].items():
            if converter.IsModelFileExists(cfg, var, lang, 'silero', strict=True):
                if not self.first_silero_lang:
                    self.first_silero_lang = lang
    
                lang_name = language.name
                self.tts_tabview.add(lang_name)
                self.tts_tabview.tab(lang_name).grid_columnconfigure((0,1,2), weight=0)
                voice_parent = self.tts_tabview.tab(lang_name)
                
                row_id = 0
                if 'langs' in language.extra:
                    self.tts_multi_voice_language_labels[lang] = ctk.CTkLabel(voice_parent, text=T.T("Language:"))
                    self.tts_multi_voice_language_labels[lang].grid(row=0, column=0, padx=10, pady=2, sticky="w")

                    sub_lang_names = [name_data['name'] for name_data in language.extra['langs'].values()]
                    self.tts_multi_voice_language_combos[lang] = ctk.CTkComboBox(voice_parent, values=sub_lang_names, state="readonly", command=self.on_sub_lang_changed)
                    self.tts_multi_voice_language_combos[lang].set(sub_lang_names[0])
                    self.tts_multi_voice_language_combos[lang].grid(row=0, column=1, padx=10, pady=2, sticky="w")
                    row_id = 1

                self.tts_voice_labels[lang] = ctk.CTkLabel(voice_parent, text=T.T("Voice:"))
                self.tts_voice_labels[lang].grid(row=row_id, column=0, padx=10, pady=2, sticky="w")

                lang_voice = '' if ('langs' in language.extra) else var['settings']['silero'][lang]['voice']
                self.tts_voice_combos[lang] = ctk.CTkComboBox(voice_parent, state="readonly")
                self.tts_voice_combos[lang].set(lang_voice)
                self.tts_voice_combos[lang].grid(row=row_id, column=1, padx=10, pady=2, sticky="w")

                self.tts_voice_play_buttons[lang] = ctk.CTkButton(
                    voice_parent, width=30,
                    fg_color="transparent", hover_color=("gray80", "gray30"), text_color=("gray40", "gray60"),
                    command=lambda lang=lang: self.on_play(lang),
                    font=parent.icon_font, text=Icons.play
                )
                self.tts_voice_play_buttons[lang].grid(row=row_id, column=2, padx=10, pady=2, sticky="w")

        # Coqui
        language = next(iter(var['coqui-ai'].values())) # list(var['coqui-ai'].values())[0] # xtts
        self.coqui_frame = ctk.CTkFrame(master=self)

        self.coqui_language_label = ctk.CTkLabel(self.coqui_frame, text=T.T("Language:"))
        self.coqui_language_label.grid(row=0, column=0, padx=10, pady=(7,2), sticky="w")

        sub_lang_names = [name_data['name'] for name_data in language.extra['langs'].values()]
        self.coqui_language_combo = ctk.CTkComboBox(self.coqui_frame, values=sub_lang_names, state="readonly", command=self.on_coqui_lang_changed)
        self.coqui_language_combo.set(sub_lang_names[0])
        self.coqui_language_combo.grid(row=0, column=1, padx=10, pady=(7,2), sticky="w")

        self.coqui_voice_label = ctk.CTkLabel(self.coqui_frame, text=tr["Voice:"])
        self.coqui_voice_label.grid(row=1, column=0, padx=10, pady=2, sticky="w")

        self.coqui_voice_combo = ctk.CTkComboBox(self.coqui_frame, width=300, state="readonly")
        self.coqui_voice_combo.grid(row=1, column=1, padx=10, pady=2, sticky="w")
        self.on_coqui_lang_changed(sub_lang_names[0])

        self.coqui_voice_play_button = ctk.CTkButton(
            self.coqui_frame, width=30,
            fg_color="transparent", hover_color=("gray80", "gray30"), text_color=("gray40", "gray60"),
            command=lambda: self.on_play(),
            font=parent.icon_font, text=Icons.play
        )
        self.coqui_voice_play_button.grid(row=1, column=2, padx=10, pady=2, sticky="w")


        self.install_button = ctk.CTkButton(self, text=T.T('Install components and languages'), command=self.on_install)
        self.install_button.grid(row=8, column=0, padx=10, pady=2, columnspan=3, sticky="e")


        self.warning_note = ctk.CTkLabel(self, text=T.T('PreferencesSaveNote'))
        self.warning_note.grid(row=9, column=0, padx=10, pady=2, columnspan=3, sticky="w")

        # Save and Cancel buttons
        self.save_button = ctk.CTkButton(self, text=T.T("Save"), command=self.on_save)
        self.save_button.grid(row=10, column=0, padx=10, pady=7)

        self.cancel_button = ctk.CTkButton(self, text=T.T("Cancel"), command=self.on_cancel)
        self.cancel_button.grid(row=10, column=1, padx=10, pady=7, columnspan=2, sticky="e")

        self.on_engine_changed(current_engine)
        self.on_sub_lang_changed('')


    def get_child_geometry(self, width: int, height: int) -> str:
        return self.parent.get_child_geometry(width, height)


    def on_save(self):
        # Save preferences logic
        s = settings.LoadOrDefault(self.cfg, self.var)
        engine = self.get_selected_engine()
        s['app']['lang'] = self.get_code_by_lang(self.lang_combobox.get())
        s['app']['output'] = self.output_text.get()
        s['app']['codec'] = self.codec_combobox.get()
        s['app']['bitrate'] = int(self.bitrate_combobox.get())
        s['app']['dirs'] = self.get_dir_format_by_translated(self.dirs_combobox.get())
        s['app']['engine'] = engine

        for lang, language in self.var['languages'].items():
            if lang in self.tts_voice_combos:
                if not 'langs' in language.extra:
                    s['silero'][lang]['voice'] = self.tts_voice_combos[lang].get()
                else:
                    _, sublang = self.get_active_sub_lang_code()
                    if sublang and sublang in s['silero'][lang]:
                        s['silero'][lang][sublang]['voice'] = self.tts_voice_combos[lang].get()

        s[engine]['voice'] = self.coqui_voice_combo.get()

        settings.Save(self.cfg, s)
        self.var['settings'] = s

        self.destroy()


    def on_cancel(self):
        # Cancel logic
        self.destroy()


    def on_install(self):
        from helpers.UI.EbookTalkerInstallerUI import EbookTalkerInstallerUI
        installer_form = EbookTalkerInstallerUI(self, self.var, focus_tab='silero')
        installer_form.grab_set()


    def on_play(self, lang = 'en'):
        engine = self.get_selected_engine()
        voice = self.tts_voice_combos[lang].get() if 'silero' == engine else self.coqui_voice_combo.get()
        if 'silero' != engine:
            lang = self.get_selected_coqui_lang()

        voiceFile = voice.replace(' ', '-')
        wavFile = self.var['tmp'] / f"{engine}-{lang}-{voiceFile}.wav"
        if ("random" == voice) and wavFile.exists():
            wavFile.unlink()

        language = self.var['languages'][lang] if 'silero' == engine else self.var['coqui-ai'][engine]
        phrase = ''
        if ('langs' in language.extra):
            sublang = self.get_just_active_sub_lang() if 'silero' == engine else self.get_selected_coqui_lang()
            phrase =  language.extra['langs'][sublang]['phrase']
        else:
            phrase = language.extra['phrase']

        if converter.SayText(wavFile, lang, voice, phrase, self.cfg, self.var, engine):
            soundfile = str(wavFile.absolute())
            # if sys.platform == "win32":
            #     import winsound
            #     winsound.PlaySound(soundfile, winsound.SND_ALIAS)
            # else:    
            if sys.platform == "win32":
                soundfile = soundfile.replace('\\', '/')
            playsound(soundfile)


    def on_dirs_changed(self, choice):
        dir_format = self.get_dir_format_by_translated(choice)
        self.dirs_example.configure(text=self.GetNiceTestBookName(dir_format))


    def on_engine_changed(self, choice):
        engine = self.get_key_by_value(self.engines, choice)

        if 'silero' == engine:
            self.coqui_frame.grid_forget()
            self.tts_tabview.grid(row=7, column=0, padx=10, pady=2, sticky="nsew", columnspan=3)
            if self.first_silero_lang:
                self.tts_voice_combos[self.first_silero_lang].configure(values=converter.GetModel(self.cfg, self.var, self.first_silero_lang, engine).speakers)
        else:
            self.tts_tabview.grid_forget()
            self.coqui_frame.grid(row=7, column=0, padx=10, pady=2, sticky="nsew", columnspan=3)
            self.coqui_voice_combo.configure(values=sorted(converter.GetModel(self.cfg, self.var, 'en', engine).speakers))


    def GetNiceTestBookName(self, dir_format: str) -> str:
        out_path = book.GetOutputName(Path(self.output_text.get()), self.testBook, dir_format)
        if "full" == dir_format.lower():
            out_path /= "1"
        name = str(out_path)
        # name = name.replace("/", " / ").replace("\\", " \\ ")
        name += "." + self.codec_combobox.get()
        return name


    def get_output_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_text.delete(0, "end")
            self.output_text.insert(0, folder_path)


    def on_tab_change(self):
        selected_tab = self.tts_tabview.get()  # Get the currently selected tab name
        lang = self.get_code_by_lang(selected_tab)
        self.tts_voice_combos[lang].configure(values=converter.GetModel(self.cfg, self.var, lang).speakers)
        if 'langs' in self.var['languages'][lang].extra:
            self.on_sub_lang_changed(None)


    def on_sub_lang_changed(self, choice):
        lang, sublang = self.get_active_sub_lang_code()
        if sublang:
            native = self.var['languages'][lang].extra['langs'][sublang]['native']
            model_speakers = converter.GetModel(self.cfg, self.var, lang).speakers
            speakers = [x for x in model_speakers if x.startswith(native)]
            if (not speakers) or (len(speakers) < 1):
                speakers = model_speakers
            if lang in self.tts_voice_combos:
                self.tts_voice_combos[lang].configure(values=speakers)
                self.tts_voice_combos[lang].set(self.var['settings']['silero'][lang][sublang]['voice'])


    def on_coqui_lang_changed(self, choice):
        engine = self.get_selected_engine()
        if 'silero' == engine:
            engine = next(iter(self.var['coqui-ai'])) # first key in 'coqui-ai' - xtts
        lang = self.get_selected_coqui_lang(engine)
        if lang in self.var['settings'][engine]:
            speaker = self.var['settings'][engine][lang]['voice']
            self.coqui_voice_combo.set(speaker)


    def get_selected_coqui_lang(self, engine: str = ''):
        if not engine:
            engine = self.get_selected_engine()
        return self.get_sub_lang_code_by_name(self.coqui_language_combo.get(), self.var['coqui-ai'][engine].extra['langs'])


    def get_selected_engine(self):
        return self.get_key_by_value(self.engines, self.engine_combobox.get())


    def get_active_sub_lang_code(self):
        selected_tab = self.tts_tabview.get()  # Get the currently selected tab name
        lang = self.get_code_by_lang(selected_tab)
        if (lang in self.var['languages']) and ('langs' in self.var['languages'][lang].extra):
            choice = self.tts_multi_voice_language_combos[lang].get()
            sublang = self.get_sub_lang_code_by_name(choice, self.var['languages'][lang].extra['langs'])
            if (sublang in self.var['settings']['silero'][lang]):
                return lang, sublang
        return lang, None
    

    def get_just_active_sub_lang(self):
        _, sublang = self.get_active_sub_lang_code()
        return sublang
    

    def get_lang_by_code(self, value: str):
        return self.supported_languages.get(value, self.supported_languages[''])
    

    def get_code_by_lang(self, value: str):
        for key, lang in self.var['languages'].items():
            if value == lang.name:
                return key
        return ''
    

    def get_key_by_value(self, dic: dict, value: str) -> str:
        for key in dic:
            if value == dic[key]:
                return key
        return ''


    def get_dir_format_by_translated(self, value: str) -> str:
        return self.get_key_by_value(self.dir_formats, value)
    

    def get_sub_lang_code_by_name(self, lang_name: str, lang_dict: dict) -> str:
        for code, info in lang_dict.items():
            if info.get('name') == lang_name:
                return code
        return None