var userLang = navigator.language || navigator.userLanguage;
var locale = 'en';
var tr = {};
var trCat = NaN;

function TT(txt, cat, def) {
  if ((cat in tr) && (txt in tr[cat])) {
    return tr[cat][txt];
  } 
  if (txt in tr) {
    return tr[txt];
  }
  return def;
}

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
                template: "<img src='/static/book.png' style='width:200px; height:200px;'/>",
                width: 220,
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
                  { view: "textarea", height: 120,  id: "sysinfo_textarea", value: tr["Loading:"] + " " + tr["SystemInformation"] },
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

  webix.ajax().get("/sysinfo").then(function(data) {
    const sysInfoText = data.text(); // or data.json() if it's JSON
    const textarea = $$("sysinfo_textarea");
    if (textarea) {
      textarea.setValue(tr["SystemInformation"] + "\n\n" + sysInfoText);
    }
  }).fail(function(xhr) {
    webix.message({ type: "error", text: "Failed to load system info." });
  });
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
          {
            view: "tabview", cells: langCells
          },
          { view: "button", value: tr["Install components and languages"], label: "", click: ShowInstallerWindow },
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


// // Installer // //
function ShowInstallerWindow(id, event) {
    let win = $$("installerWindow");

    // If window doesn't exist, create a loading shell first
    if (!win) {
        win = webix.ui({
            view: "window",
            id: "installerWindow",
            modal: true,
            close: true,
            move: true,
            position: "center",
            width: 400,
            height: 200,
            head: "Loading...",
            body: {
                template: "<div style='text-align:center; padding:40px;'><span class='webix_icon wxi-spinner' style='font-size:24px;'></span><br>Loading components...</div>"
            }
        });
        win.show();

        // 🔹 Fetch items from Flask
        webix.ajax().get("/api/installer/items").then(response => {
            const items = response.json();
            win.close(); // close loader
            _createInstallerWindow(items); // create real UI
        }).catch(err => {
            win.close();
            webix.message({ type: "error", text: "Failed to load component list." });
        });
        return;
    }

    win.show();
}

// 🔹 Internal: create real installer window
function _createInstallerWindow(INSTALL_ITEMS) {
    // Group items
    const groups = {};
    INSTALL_ITEMS.forEach(item => {
        if (!groups[item.group]) groups[item.group] = [];
        groups[item.group].push(item);
    });
    const groupNames = Object.keys(groups);

    // State
    let selectedItem = null;
    let installing = false;
    let eventSource = null;

    // Helper: update description & items
    const updateGroupView = (groupName) => {
        const group = groups[groupName] || [];
        const descView = $$("installer_desc");
        const iconView = $$("installer_icon");
        const itemsView = $$("installer_items");

        if (groupName === "silero") {
            iconView.setHTML("🗣️");
            descView.setValue(
                "Voice models for text-to-speech. Each language model is ~100 MB. " +
                "Download only the languages you need."
            );
        } else {
            iconView.setHTML("📦");
            descView.setValue(`Components in "${groupName}" category.`);
        }

        // Radio items (no descriptions for Silero)
        const radios = group.map(item => ({
            template: `<label style="display:flex;align-items:center;margin:6px 0;">
                <input type="radio" name="installer_item" value="${item.name}" 
                    style="margin-right:8px;" ${selectedItem === item.name ? 'checked' : ''}>
                <span>${item.name}</span>
            </label>`,
            height: 30,
            css: "installer-item",
            click: () => {
                selectedItem = item.name;
                group.forEach(other => {
                    if (other !== item) {
                        const el = document.querySelector(`input[value="${other.name}"]`);
                        if (el) el.checked = false;
                    }
                });
            }
        }));

        itemsView.clearAll();
        itemsView.parse(radios);

        if (!selectedItem && group.length) {
            selectedItem = group[0].name;
            const firstRadio = document.querySelector('input[name="installer_item"]');
            if (firstRadio) firstRadio.checked = true;
        }
    };

    const setInstalling = (state) => {
        installing = state;
        $$("installer_install_btn").disable(state);
        const btn = $$("installer_action_btn");
        if (state) {
            btn.setValue("Cancel");
            btn.attachEvent("onItemClick", cancelInstall);
        } else {
            btn.setValue("Close");
            btn.attachEvent("onItemClick", () => $$("installerWindow")?.close());
        }
    };

    const startInstall = () => {
        if (!selectedItem) {
            webix.message({ type: "error", text: "Please select a component." });
            return;
        }

        setInstalling(true);
        $$("installer_progress").setValue(0);
        $$("installer_status").setValue(`Starting: ${selectedItem}...`);

        const item = INSTALL_ITEMS.find(i => i.name === selectedItem);
        eventSource = new EventSource(`/install/start?item=${encodeURIComponent(item.name)}`);

        // ✅ Enhanced onmessage (indeterminate + cleanup)
        eventSource.onmessage = (e) => {
            const data = JSON.parse(e.data);
            const progress = $$("installer_progress");
            const el = progress.$view.querySelector(".webix_progress_top");

            if (data.type === "progress") {
                progress.setValue(data.value / 100);
                if (el) el.style.transition = "width 0.3s";
            } else if (data.type === "indeterminate") {
                if (data.value) {
                    if (el) {
                        el.style.transition = "none";
                        let i = 0;
                        const anim = setInterval(() => {
                            if (!installing || !eventSource) {
                                clearInterval(anim);
                                return;
                            }
                            const pos = 20 + 60 * (1 + Math.sin(i++ / 10)) / 2;
                            el.style.width = pos + "%";
                        }, 120);
                        progress._indeterminateAnim = anim;
                    }
                } else {
                    if (progress._indeterminateAnim) {
                        clearInterval(progress._indeterminateAnim);
                        delete progress._indeterminateAnim;
                    }
                    if (el) {
                        el.style.transition = "width 0.3s";
                        el.style.width = "100%";
                    }
                    progress.setValue(1);
                }
            } else if (data.type === "message") {
                $$("installer_status").setValue(data.value);
            } else if (data.type === "done") {
                if (progress._indeterminateAnim) {
                    clearInterval(progress._indeterminateAnim);
                    delete progress._indeterminateAnim;
                }
                setInstalling(false);
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
                $$("installer_status").setValue(
                    data.value ? "✅ Installation completed successfully!" : "❌ Installation failed."
                );
                progress.setValue(data.value ? 1 : 0);
            }
        };

        eventSource.onerror = () => {
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
            setInstalling(false);
            $$("installer_status").setValue("❌ Connection lost.");
        };
    };

    const cancelInstall = () => {
        webix.confirm({
            text: "Cancel installation?",
            ok: "Yes", cancel: "No",
            callback: (r) => {
                if (r && eventSource) {
                    eventSource.close();
                    eventSource = null;
                    fetch("/install/cancel", { method: "POST" });
                    $$("installer_status").setValue("Cancelling…");
                }
            }
        });
    };

    // ✅ Create real window
    const win = webix.ui({
        view: "window",
        id: "installerWindow",
        modal: true,
        close: true,
        move: true,
        position: "center",
        width: 660,
        height: 520,
        head: "EbookTalker – Component Installer",
        body: {
            rows: [
                // Category selector (only if >1 group)
                ...(groupNames.length > 1 ? [{
                    view: "toolbar",
                    cols: [
                        { template: "Category:", width: 80 },
                        {
                            view: "richselect",
                            id: "installer_group_select",
                            value: groupNames[0],
                            options: groupNames,
                            width: 200,
                            on: { onChange: (v) => updateGroupView(v) }
                        },
                        {}
                    ]
                }] : []),

                // Description
                {
                    cols: [
                        { view: "label", id: "installer_icon", width: 30, css: { "font-size": "24px" } },
                        { view: "label", id: "installer_desc", css: { "line-height": "1.4" } }
                    ],
                    height: 60
                },

                // Items
                {
                    view: "scrollview",
                    id: "installer_items",
                    body: { view: "list", type: { height: "auto" }, autoheight: false },
                    height: 260
                },

                // Progress & status
                {
                    view: "template",
                    id: "installer_progress",
                    css: "installer-progress",
                    template: "<div class='installer-progress-bar'><div class='installer-progress-fill' style='width:0%'></div></div>",
                    height: 10,
                    value: 0,
                    on: {
                        onAfterRender: function() {
                            // Initialize fill reference
                            this.$view.querySelector(".installer-progress-fill").style.width = "0%";
                        }
                    }
                },
                { view: "label", id: "installer_status", height: 24, css: { "min-height": "24px" } },

                // Buttons
                {
                    view: "toolbar",
                    cols: [
                        {},
                        { view: "button", id: "installer_install_btn", value: "Install Selected", click: startInstall, width: 140 },
                        { view: "button", id: "installer_action_btn", value: "Close", click: () => win.close(), width: 100 }
                    ]
                }
            ]
        }
    });

    const initialGroup = groupNames[0] || "";
    updateGroupView(initialGroup);
    win.show();
}

function setProgress(percent) {
    const el = $$("installer_progress")?.$view?.querySelector(".installer-progress-fill");
    if (el) el.style.width = (percent * 100) + "%";
}


// // // // // MAIN UI // // // // //
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
