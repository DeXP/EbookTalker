// // // About Windows // // //
function ShowAboutWindow(id, event) {
  let win = $$("aboutWindow");

  // If window doesn't exist, create it
  if (!win) {
    win = webix.ui({
      view: "window",
      id: "aboutWindow",
      modal: true, close: true, move: true, resize: true,
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