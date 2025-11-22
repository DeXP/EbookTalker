// // // Preferences // // //
function PlayClick(id, event) {
  const sp = id.split("-");
  const tts = sp[0];
  const lang = sp[1];
  const comboId = tts + "-" + lang + "-voice"
  const voice = $$(comboId).getValue();

  this.disable();  // Disable button during playback
  const audio = new Audio("/example?tts=" + tts + "&lang=" + lang + "&voice=" + voice);
  
  audio.onended = () => this.enable(); // Re-enable when done
  audio.play().catch(e => {
    this.enable();
    webix.message("Error: " + e.message);
  });
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
        langCells.push({
          header: language.name,
          body: {
            id: curId,
            view:"form", 
            elements:[
              {cols:[
                  { view: "select", label: tr["Voice:"], 
                    name: comboId, id: comboId, options: "/voices?lang=" + langCode, 
                    value: APP_SETTINGS['silero'][langCode]["voice"] },
                  { view: "icon", id: curId + "-play", icon: "mdi mdi-play", click: PlayClick }
              ]}
          ]
          }
        });
    }
    });
    
    win = webix.ui({
      view: "window",
      id: "preferencesWindow",
      modal: true, close: true, move: true,
      position: "center", width: 600, height: 550,
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
          {
            view: "select", label: tr["NamingFormat:"], name: "dirs", value: APP_SETTINGS['app']['dirs'],
            options: [
              { id: "single", value: tr["nf-single"] + "  (output/author - book.mp3)" },
              { id: "short", value: tr["nf-short"] + "  (output/author/book/1.mp3)" },
              { id: "full", value: tr["nf-full"] + "  (output/author/series/book/1.mp3)" }
            ]    
          },
          ...(langCells.length > 0 ? [{
              view: "tabview", cells: langCells
          }] : []),
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
                  TTS_LANG_LIST.forEach(function(langCode) {
                    var language = TTS_LANGUAGES[langCode];
                    var comboId = language.type + "-" + langCode + "-voice";
                    if (!(language.type in values)) {
                      values[language.type] = {};
                    }
                    values[language.type][langCode] = {};
                    values[language.type][langCode]['voice'] = $$(comboId).getValue();
                  });

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
                      APP_SETTINGS = values;
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
}