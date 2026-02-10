// // // Preferences // // //
function PlayClick(id, event) {
  const sp = id.split("-");
  const tts = sp[0];
  const lang = sp[1];
  const comboId = tts + "-" + lang + "-voice";
  const voice = $$(comboId).getValue();
  var sublang = '';
  const subLangCombo = $$(comboId + "-lang")
  if (subLangCombo) sublang = subLangCombo.getValue();

  this.disable();  // Disable button during playback
  const audio = new Audio("/example?engine=" + tts + "&lang=" + lang + "&sublang=" + sublang + "&voice=" + voice);
  
  audio.onended = () => this.enable(); // Re-enable when done
  audio.play().catch(e => {
    this.enable();
    webix.message("Error: " + e.message);
  });
}


function PlayCoquiClick(id, event) {
  const coquiVoiceSelect = $$("coqui-voice-select");
  const coquiLanguageSlect = $$("coqui-language-select");
  const engineSelect = $$("engine");
  if (coquiVoiceSelect && coquiLanguageSlect && engineSelect)
  {
    const voice = coquiVoiceSelect.getValue();
    const lang = coquiLanguageSlect.getValue();
    const engine = engineSelect.getValue();

    this.disable();  // Disable button during playback
    const audio = new Audio("/example?engine=" + engine + "&lang=" + lang + "&voice=" + voice);
    
    audio.onended = () => this.enable(); // Re-enable when done
    audio.play().catch(e => {
      this.enable();
      webix.message("Error: " + e.message);
    });
  }
}


function IsItCoqui(engine) {
  return ('silero' != engine) && (engine in TTS_COQUI) && TTS_COQUI[engine].enabled;
}


function OnEngineChange(newv, oldv) {
  // Get references to conditional UI elements
  const sileroView = $$("silero-tab-view");
  const coquiView = $$("coqui-language-form");
  const coquiSelect = $$("coqui-language-select");

  if (IsItCoqui(newv)) {
    // Show XTTS-specific fields
    coquiView?.show();
    sileroView?.hide();
    // Optionally fetch model list only now
    if (coquiSelect && !coquiSelect.config._loaded) {
      coquiSelect.define("options", "/langs?engine=" + newv);
      coquiSelect.refresh();
      coquiSelect.config._loaded = true; // prevent reload

      const coquiVoiceSelect = $$("coqui-voice-select");
      if (coquiVoiceSelect && !coquiVoiceSelect.config._loaded) {
        coquiVoiceSelect.define("options", "/voices?engine=" + newv);
        coquiVoiceSelect.refresh();
        coquiVoiceSelect.config._loaded = true; // prevent reload
      }
    }
  } else { 
    // Silero
    sileroView?.show();
    coquiView?.hide();
  }
}



function ShowPreferencesWindow() {
  let win = $$("preferencesWindow");

  // If window doesn't exist, create it
  if (!win) {
    langCells = []

    TTS_LANG_LIST.forEach(function(langCode) {
      var language = TTS_LANGUAGES[langCode];
      var curId = language.type + "-" + langCode;
      var comboId = curId + "-voice";
      if (language.enabled)
      {
        const voiceLinkBase = "?engine=" + language.type + "&lang=" + langCode;
        const langsLink = "/langs" + voiceLinkBase;
        const voicesLink = "/voices" + voiceLinkBase;
        langCells.push({
          header: language.name,
          body: {
            id: curId,
            view:"form", 
            elements:[
              {rows: [
                ...('langs' in language ? [{
                    view: "select", label: tr["Language:"], 
                    name: comboId + "-lang", id: comboId + "-lang", options: langsLink,
                    on: {
                      onChange: function(newv, oldv) {
                        const voiceCombo = $$(comboId);
                        if (voiceCombo)
                        {
                          voiceCombo.define("options", voicesLink + "&start=" + language['langs'][newv]['native']);
                          voiceCombo.refresh();
                        }
                      }
                    }
                }] : []),
                {cols:[
                    { view: "select", label: tr["Voice:"], 
                      name: comboId, id: comboId, options: voicesLink, 
                      value: APP_SETTINGS['silero'][langCode]["voice"] },
                    { view: "icon", id: curId + "-play", icon: "mdi mdi-play", click: PlayClick }
                ]}
              ]}
          ]
          }
        });
      }
    });

    var availableEngines = [
      { id: 'silero', value: 'Silero' }
    ];
    Object.keys(TTS_COQUI).forEach(function(tts) { 
      var curEngine = TTS_COQUI[tts];
      if (curEngine && curEngine.enabled) {
        availableEngines.push({ id: tts, value: curEngine.name });
      }
    });

    const isCoqui = IsItCoqui(APP_SETTINGS['app']['engine']);
    
    win = webix.ui({
      view: "window",
      id: "preferencesWindow",
      modal: true, close: true, move: true,
      position: "center", width: 600, height: 950,
      head: tr['Preferences'],
      body: {
        view: "form",
        elementsConfig: {
          labelWidth: 150
        },
        padding: 20,
        elements: [
          {
            view: "select", label: tr["InterfaceLanguage:"], name: "lang", value: APP_SETTINGS['app']['lang'],
            options: [
              { id: "", value: tr["Default"] },
              { id: "ru", value: TTS_LANGUAGES['ru']['name'] },
              { id: "en", value: TTS_LANGUAGES['en']['name'] }
            ]
          },
          /*{ view: "text", label: tr["OutputFolder:"], name: "output", value: APP_SETTINGS['app']['output'] },*/
          { view: "select", label: tr["Codec:"], name: "codec", options: "/formats", value: APP_SETTINGS['app']['codec'] },
          { view: "select", label: tr["Bitrate:"], name: "bitrate", options: ['32', '64', '128', '192', '320'], value: APP_SETTINGS['app']['bitrate'] },
          { view: "counter", label: tr["Sentence pause (ms):"], name:"pause-sentence", step: 50, value: APP_SETTINGS['app']['pause-sentence'], min: 0, max: 10000 },
          { view: "counter", label: tr["Paragraph pause (ms):"], name:"pause-paragraph", step: 50, value: APP_SETTINGS['app']['pause-paragraph'], min: 0, max: 10000 },
          {
            view: "select", label: tr["NamingFormat:"], name: "dirs", value: APP_SETTINGS['app']['dirs'],
            options: [
              { id: "single", value: tr["nf-single"] + "  (output/author - book.mp3)" },
              { id: "short", value: tr["nf-short"] + "  (output/author/book/1.mp3)" },
              { id: "full", value: tr["nf-full"] + "  (output/author/series/book/1.mp3)" }
            ]    
          },
          {
            view: "select", label: TT("TTS Engine:"), name: "engine", id: "engine", value: APP_SETTINGS['app']['engine'], options: availableEngines,
            // Key: react to changes
            on: { onChange: OnEngineChange }
          },
          ...(langCells.length > 0 ? [{
              view: "tabview", id: "silero-tab-view", cells: langCells, hidden: isCoqui
          }] : []),
          {
            id: "coqui-language-form",
            hidden: !isCoqui,
            rows: [
              { template: TT("TTS Engine:"), type: "section" },
              {
                view: "select", label: TT("Language:"), name: "coqui-language-select", id: "coqui-language-select", value: APP_SETTINGS['app']['lang'],
                options: [
                  { id: "en", value: TTS_LANGUAGES['en']['name'] }
                ],
                on: {
                  onChange: function(newv, oldv) {
                    const engine = $$("engine").getValue();
                    if (newv in APP_SETTINGS[engine]) {
                      const coquiVoiceSelect = $$("coqui-voice-select");
                      if (coquiVoiceSelect) {
                        coquiVoiceSelect.setValue(APP_SETTINGS[engine][newv].voice);
                      }
                    }
                  }
                }
              },
              {cols:[
                  { view: "select", label: TT("Voice:"), 
                    name: "coqui-voice-select", id: "coqui-voice-select", options: [],
                    value: APP_SETTINGS[Object.keys(TTS_COQUI)[0]]['en'].voice}, // Object.keys(TTS_COQUI)[0] -> xtts
                  { view: "icon", id: "coqui-voice-play", icon: "mdi mdi-play", click: PlayCoquiClick }
              ]}
            ]
          },
          { view: "button", value: tr["Install components and languages"], label: "", click: ShowInstallerWindow },
          ...(PASSWORD_LENGTH > 0 ? [{
              view: "text", type: "password", label: tr["password"], name: "preferencesPassword", id: "preferencesPassword", value: ""
          }] : []),
          {
            margin: 10,
            cols: [
              {
                view: "button", value: tr["Save"], css: "webix_primary",
                click: function () {
                  var values = {};
                  values['app'] = $$("preferencesWindow").getBody().getValues();
                  APP_SETTINGS['app'] = values['app']
                  TTS_LANG_LIST.forEach(function(langCode) {
                    var language = TTS_LANGUAGES[langCode];
                    if (language.enabled)
                    {
                      const comboId = language.type + "-" + langCode + "-voice";
                      const comboValue = $$(comboId).getValue();
                      if (!(language.type in values)) {
                        values[language.type] = {};
                      }
                      values[language.type][langCode] = {};

                      if ('langs' in language) {
                        sublang = $$(comboId + "-lang").getValue();
                        if (sublang)
                        {
                          values[language.type][langCode][sublang] = {};
                          values[language.type][langCode][sublang]['voice'] = comboValue;
                          APP_SETTINGS[language.type][langCode][sublang]['voice'] = comboValue;
                        }
                      } else {
                        values[language.type][langCode]['voice'] = comboValue;
                        APP_SETTINGS[language.type][langCode]['voice'] = comboValue;
                      }
                    }
                  });

                  if ('silero' != values['app']['engine'])
                  {
                    // Save Coqui
                    const engine = values['app']['engine'];
                    const coquiLang = $$("coqui-language-select").getValue();
                    const coquiVoice = $$("coqui-voice-select").getValue();

                    if (engine && coquiLang && coquiVoice)
                    {
                      if (!(engine in values)) {
                        values[engine] = {};
                      }
                      if (!(coquiLang in values[engine])) {
                        values[engine][coquiLang] = {};
                      }

                      values[engine][coquiLang]['voice'] = coquiVoice;
                      APP_SETTINGS[engine][coquiLang]['voice'] = coquiVoice;
                    }
                  }

                  // console.log(JSON.stringify(values));
                  // webix.message("Preferences saved: " + JSON.stringify(values));
                  webix.ajax().headers({
                    "Content-type":"application/json"
                  }).post("/preferences/save", values).then(function (data) {
                    j = data.json()
                    if (('error' in j) && j['error']) {
                      webix.message({ text: composeFailureText(j), type: "error" });
                    }
                    else {
                      // APP_SETTINGS = values;
                      $$("preferencesWindow").close();
                    }
                  });
                }
              },
              { view: "button", value: tr["Cancel"], click: function () { $$("preferencesWindow").close(); } }
            ]
          }
        ]
      }
    });
  }

  win.show(); // Show the existing or new window
  OnEngineChange(APP_SETTINGS['app']['engine']);
}