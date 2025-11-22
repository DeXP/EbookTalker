var userLang = navigator.language || navigator.userLanguage;
var locale = 'en';
var tr = {};

function TT(txt, cat = '', def = '') {
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
              ...(PASSWORD_LENGTH > 0 ? [{
                  view: "text", type: "password", label: tr["password"], name: "password", id: "password", value: ""
              }] : []),
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
                      const passwordSet = (PASSWORD_LENGTH == 0) || (password && (password.length >= PASSWORD_LENGTH));
                      
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
                          error = TT("pleaseChooseAFileToProcess", "error");
                        }
                        if (!passwordSet) {
                          error = TT("passwordTooShort", "error").replace("##", PASSWORD_LENGTH);
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
