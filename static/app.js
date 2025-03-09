webix.i18n.setLocale("ru-RU");

function readablizeBytes(bytes) {
  var s = ['байт', 'КБ', 'МБ', 'ГБ', 'TБ', 'ПБ'];
  var e = Math.floor(Math.log(bytes) / Math.log(1024));
  return (bytes / Math.pow(1024, e)).toFixed(1) + " " + s[e];
}

webix.ui({
  rows: [
    {
      view: "toolbar",
      css: "webix_dark",
      paddingX: 17,
      elements: [
        { view: "icon", icon: "mdi mdi-book-open-page-variant" },
        { view: "label", label: "Читалка FB2 в голос" },
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
            { template: "Книга в процессе", type: "section" },
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
                        { view: "label", label: "В процессе:", width: 130 },
                        { view: "label", name: "processBookLabel", label: "нет" }
                      ]
                    },
                    {
                      cols: [
                        { view: "label", label: "Глава:", width: 130 },
                        { view: "label", name: "processBookSection", label: "" }
                      ]
                    },
                    {
                      cols: [
                        { view: "label", label: "Читаю:", width: 130 },
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
            { template: "Очередь книг на конвертацию:", type: "section" },
            {
              view: "datatable", id: "queue", name: "queue",
              columns: [
                { id: "firstName", header: "Имя" },
                { id: "lastName", header: "Фамилия" },
                { id: "title", header: "Название", fillspace: 2 },
                { id: "seqNumber", header: "№", width: 30 },
                { id: "sequence", header: "Цикл", fillspace: 1 },
                { id: "size", header: "Размер", format: readablizeBytes },
                {
                  id: "datetime", header: "Добавлено", width: 200,
                  format: function (timestamp) { return webix.i18n.fullDateFormatStr(new Date(timestamp * 1000)); }
                },
              ],
              url: "/queue/list"
            }
          ]
        },

        {
          rows: [
            { template: "Добавить FB2 в очередь", type: "section" },
            { view: "text", label: "URL", name: "url", id: "url", value: "" },
            { view: "text", label: "Пароль", name: "password", id: "password", value: "" },
            {
              cols: [
                {},
                //{ view: "button", css: "webix_danger", value: "Cancel", width: 150 },
                {
                  view: "button", css: "webix_primary", value: "Добавить", width: 150,
                  click: function () {
                    error = '';
                    url = $$("processForm").getValues().url;
                    password = $$("processForm").getValues().password;
                    if (!password || (password.length < 5)){
                      error = 'Пароль должен содержать больше 5 символов';
                    }
                    if (!url || (url.length < 5)){
                      error = 'Введите ссылку для скачивания';
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


function updateTick(data) {
  data = data.json();

  bookName = 'нет';
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


UpdateAjaxCall();

setInterval(function () {
  UpdateAjaxCall();
}, 3000);
