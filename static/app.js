var userLang = navigator.language || navigator.userLanguage; 
var localeJson = 'en.json';
var tr = {};

if (userLang.toLowerCase().startsWith('ru')) {
  localeJson = 'ru.json';
  webix.i18n.setLocale("ru-RU");
}

function readablizeBytes(bytes) {
  var s = [tr["byte"], tr["KB"], tr["MB"], tr["GB"], tr["TB"], tr["PB"]];
  var e = Math.floor(Math.log(bytes) / Math.log(1024));
  return (bytes / Math.pow(1024, e)).toFixed(1) + " " + s[e];
}

function ConstructUI(tr) {
  webix.ui({
    rows: [
      {
        view: "toolbar",
        css: "webix_dark",
        paddingX: 17,
        elements: [
          { view: "icon", icon: "mdi mdi-book-open-page-variant" },
          { view: "label", label: tr["appTitle"] },
          {},
          { view: "icon", icon: "mdi mdi-help-circle-outline" }
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
                          { view: "label", name: "processBookLabel", label: "нет" }
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
              { template: tr["addFB2toQueue"], type: "section" },
              { view: "text", label: tr["url"], name: "url", id: "url", value: "" },
              { view: "text", label: tr["password"], name: "password", id: "password", value: "" },
              {
                cols: [
                  {},
                  //{ view: "button", css: "webix_danger", value: "Cancel", width: 150 },
                  {
                    view: "button", css: "webix_primary", value: tr["add"], width: 150,
                    click: function () {
                      error = '';
                      url = $$("processForm").getValues().url;
                      password = $$("processForm").getValues().password;
                      if (!password || (password.length < 5)){
                        error = tr["passwordTooShort"];
                      }
                      if (!url || (url.length < 5)){
                        error = tr["noURLforDownload"];
                      }
                      if (error) {
                        webix.message({ text: error, type:"error" });
                      } else {
                        // Submit
                        $$("processForm").setValues({url: ''}, true);
                        webix.ajax().get("/queue/add", { password:password, url:url }).then(function(data){
                          j = data.json()
                          if (('error' in j) && j['error'])
                          {
                            webix.message({ text: error, type:"error" });
                          }
                          else
                          {
                            $$("queue").clearAll();
                            $$("queue").load("/queue/list");
                          }
                        });
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
  if ("sectionTitle" in data) {
    sectionTitle = data["sectionTitle"];
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


webix.ajax("/static/i18n/" + localeJson).then(function (data) {
  tr = data.json();
  document.title = tr['appTitle'];
  ConstructUI(tr);

  UpdateAjaxCall();

  setInterval(function () {
    UpdateAjaxCall();
  }, 3000);
});
