var userLang = navigator.language || navigator.userLanguage;
var locale = 'en';
var tr = {};

if (userLang.toLowerCase().startsWith('ru')) {
  locale = 'ru';
}

if (('app' in APP_SETTINGS) && ('lang' in APP_SETTINGS['app']) && APP_SETTINGS['app']['lang']) {
  locale = APP_SETTINGS['app']['lang'];
}

if ('ru' == locale) {
  webix.i18n.setLocale("ru-RU");
}

function readablizeBytes(bytes) {
  var s = [tr["byte"], tr["KB"], tr["MB"], tr["GB"], tr["TB"], tr["PB"]];
  var e = Math.floor(Math.log(bytes) / Math.log(1024));
  return (bytes / Math.pow(1024, e)).toFixed(1) + " " + s[e];
}

function composeFailureText(j) {
  if (('error' in j) && j['error']) {
    errorIndex = j['error'];
    errorText = (errorIndex in tr["error"])? tr["error"][errorIndex]: tr["error"]["unknown-error"];
    return (('failure' in j) && j['failure'])? errorText + ': ' + j['failure']: errorText;
  };
  return '';
}

function ShowAboutWindow(id, event) {
  let win = $$("aboutWindow");

  // If window doesn't exist, create it
  if (!win) {
    win = webix.ui({
      view: "window",
      id: "aboutWindow",
      modal: true, close: true, move: true,
      position: "center", width: 940, height: 660,
      head: tr["appTitle"],
      body: {
        view: "form",
        padding: 20,
        elements: [
          {
            view: "layout",
            type: "line",
            cols: [
              {
                view: "template",
                template: "<img src='/static/default-cover.png' style='width:400px; height:400px;'/>",
                width: 420,
                borderless: true
              },
              {
                view: "form",
                borderless: true,
                rows: [
                  { view: "label", label: tr["appDescription"] },
                  { view: "label", label: tr["silero-line"] },
                  { view: "label", label: tr["appVersion"] + ": " + APP_VERSION },
                  { view: "label", label: tr["appAuthor-line"] },
                  { view: "label", label: tr["appBetaTesters-line"] },
                  { view: "button", value: tr["appLink"], click: "window.open('" + tr["appLink"] + "')" },
                  { view: "textarea", height: 120, value: tr["SystemInformation"] + "\n\n" + SYS_INFO },
                  { view: "button", value: tr["OK"], css: "webix_primary", click: function () { $$("aboutWindow").close(); } }
                ]
              }
            ]
          }
        ]
      }
    })
  }

  win.show(); // Show the existing or new window
}

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
    });
    
    win = webix.ui({
      view: "window",
      id: "preferencesWindow",
      modal: true, close: true, move: true,
      position: "center", width: 600, height: 500,
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
          {
            view: "tabview", cells: langCells
          },
          { view: "text", type: "password", label: tr["password"], name: "preferencesPassword", id: "preferencesPassword", value: "" },
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


function ConstructUI(tr) {
  webix.ui({
    rows: [
      {
        view: "toolbar",
        css: "webix_dark",
        paddingX: 17,
        elements: [
          { view: "icon", icon: "mdi mdi-book-open-page-variant", click: ShowAboutWindow },
          { view: "label", label: tr["appTitle"] + " (" + APP_VERSION + ")" },
          {},
          { view: "icon", icon: "mdi mdi-cog", click: ShowPreferencesWindow },
          { view: "icon", icon: "mdi mdi-help-circle-outline", click: ShowAboutWindow }
        ]
      },
      {
        view: "form", id: "processForm",
        elementsConfig: {
          labelWidth: 130
        },
        elements: [
          {
            rows: [
              { template: tr["bookInProcess"], type: "section" },
              //{ view:"select", id:"lang", label:"Язык", value:"ru", options:"/langs" },
              //{ view:"select", id:"voice", label:"Голос", value:"xenia", options:"/voices" },
              {
                cols: [
                  {
                    view: "button", name: "coverButton", id: "coverButton", type: "image", image: "/process/cover", label: "", width: 150
                  },
                  {
                    rows: [
                      {
                        cols: [
                          { view: "label", label: tr["inProcess:"], width: 130 },
                          { view: "label", name: "processBookLabel", label: tr["emptyBookName"] }
                        ]
                      },
                      {
                        cols: [
                          { view: "label", label: tr["chapter:"], width: 130 },
                          { view: "label", name: "processBookSection", label: "" }
                        ]
                      },
                      {
                        cols: [
                          { view: "label", label: tr["reading:"], width: 130 },
                          { view: "label", name: "processSentenceText", label: "..." }
                        ]
                      },
                      { view: "label", label: "", id: "processPercent" },
                    ]
                  }
                ]
              },
            ]
          },

          {
            rows: [
              { template: tr["queueForConversion:"], type: "section" },
              {
                view: "datatable", id: "queue", name: "queue",
                columns: [
                  { id: "firstName", header: tr["firstName"] },
                  { id: "lastName", header: tr["lastName"] },
                  { id: "title", header: tr["title"], fillspace: 2 },
                  { id: "seqNumber", header: tr["seqNumber"], width: 30 },
                  { id: "sequence", header: tr["sequence"], fillspace: 1 },
                  { id: "size", header: tr["size"], format: readablizeBytes },
                  {
                    id: "datetime", header: tr["datetime"], width: 200,
                    format: function (timestamp) { return webix.i18n.fullDateFormatStr(new Date(timestamp * 1000)); }
                  },
                ],
                url: "/queue/list"
              }
            ]
          },

          {
            rows: [
              { template: tr["addBookToQueue"], type: "section" },
              {
                view:"uploader",
                id: "uploader",
                link: "uploaderList",
                value: tr["chooseEbookFile"],
                upload:"/queue/upload",
                autosend: false,
                multiple: true,
                css: "webix_secondary",
                datatype:"json",
                on: {
                  onFileUpload: function(file) {
                    $$("queue").clearAll();
                    $$("queue").load("/queue/list");
                    // $$("uploader").files.clearAll();
                  },
                  onFileUploadError: function(file, response) {
                    webix.message({ type: "error", text: tr["error"]["uploadFailed."] + composeFailureText(response) });
                  }
                }
              },
              { view:"list",  id:"uploaderList", type:"uploader", autoheight:true, borderless:true },
              { view: "label", label: tr["or/and"] },
              { view: "text", label: tr["url"], name: "url", id: "url", value: "" },
              { view: "text", type: "password", label: tr["password"], name: "password", id: "password", value: "" },
              {
                cols: [
                  {},
                  //{ view: "button", css: "webix_danger", value: "Cancel", width: 150 },
                  {
                    view: "button", css: "webix_primary", value: tr["addBookToQueue"], width: 250,
                    click: function () {     
                      const uploader = $$("uploader");
                      const url = $$("processForm").getValues().url;
                      const password = $$("processForm").getValues().password;

                      const urlSet = (url && (url.length >= 5));
                      const fileSet = (uploader.files.data && uploader.files.data.count() > 0);
                      const passwordSet = (password && (password.length >= PASSWORD_LENGTH));
                      
                      if (passwordSet && (urlSet || fileSet)) {

                        if (urlSet) {
                          // Submit URL
                          webix.ajax().get("/queue/add", { password: password, url: url }).then(function (data) {
                            j = data.json()
                            if (('error' in j) && j['error']) {
                              webix.message({ text: composeFailureText(j), type: "error" });
                            }
                            else {
                              $$("processForm").setValues({ url: '' }, true);
                              $$("queue").clearAll();
                              $$("queue").load("/queue/list");
                            }
                          });
                        }

                        if (fileSet) {
                          // Submit file
                          uploader.files.data.each(function(obj){
                            //add file specific additional parameters
                            obj.formData = { password:password };
                          });
                          $$("uploader").send();
                        }

                      } else {
                        error = '';
                        if (!urlSet || !fileSet) {
                          error = tr["error"]["pleaseChooseAFileToProcess"];
                        }
                        if (!passwordSet) {
                          error = tr["error"]["passwordTooShort"].replace("##", PASSWORD_LENGTH);
                        }
                        webix.message({ text: error, type: "error" });
                      }
                    }
                  }
                ]
              }
            ]
          }

        ]
      }
    ]
  });

  webix.extend($$("processPercent"), webix.ProgressBar);
}


function updateTick(data) {
  data = data.json();

  bookName = "...";
  if ("bookName" in data) {
    bookName = data['bookName'];
  }

  prevBookName = $$("processForm").getValues().processBookLabel;
  if (bookName != prevBookName) {
    console.log(prevBookName);
    console.log(bookName);
    $$("queue").clearAll();
    $$("queue").load("/queue/list");

    $$("coverButton").image = "/process/cover?book=" + bookName;
    $$("coverButton").refresh();
  }

  sentenceText = '...';
  if ("sentenceText" in data) {
    sentenceText = data["sentenceText"];
  }

  sectionTitle = ''
  if ("rawSectionTitle" in data) {
    sectionTitle = data["rawSectionTitle"];
  }

  perc = 0.0;
  if (("totalSentences" in data) && ("sentenceNumber" in data)) {
    perc = data['sentenceNumber'] / (data['totalSentences'] + 1);

    $$("processPercent").showProgress({
      type: "bottom",
      position: perc
    });
  }
  // console.log(perc)

  $$("processForm").setValues({
    processBookLabel: bookName,
    processSentenceText: sentenceText,
    processBookSection: sectionTitle
  }, true);
}


function UpdateAjaxCall() {
  webix.ajax("/process").then(function (data) {
    updateTick(data);
  });
}


webix.ajax("/static/i18n/" + locale + ".json").then(function (data) {
  tr = data.json();
  document.title = tr['appTitle'];
  ConstructUI(tr);

  UpdateAjaxCall();

  setInterval(function () {
    UpdateAjaxCall();
  }, 3000);
});
