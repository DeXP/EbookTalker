// Global state shared across calls
let INSTALLER_WINDOW = null;
let INSTALLER_STATE = {
    installing: false,
    selectedItem: null,
    eventSource: null,
    items: INSTALL_ITEMS,
    groups: null
};

// Set progress (0–1)
function setProgressValue(percent01) {
    const prog = $$("installer_progress");
    if (!prog) return;
    const el = prog.$view.querySelector(".webix_progress_inner");
    if (el) {
        el.style.width = (percent01 * 100) + "%";
    }
}

// Clean up SSE & anim
function cleanupInstaller() {
    const { eventSource } = INSTALLER_STATE;
    if (eventSource) {
        eventSource.close();
        INSTALLER_STATE.eventSource = null;
    }
    const el = $$("installer_progress")?.$view?.querySelector(".webix_progress_inner");
    if (el?._anim) {
        clearInterval(el._anim);
        delete el._anim;
    }
}

// Shared: set UI installing state
function setInstalling(state, c = 'install') {
    INSTALLER_STATE.installing = state;
    const installBtn = $$("installer_install_btn");
    const actionBtn = $$("installer_action_btn");

    if (installBtn) installBtn.disable(state);
    if (actionBtn) {
        actionBtn.setValue(state ? TT("Cancel", c) : TT("Close", c));
        var onClickHandlers = actionBtn.hasEvent('onItemClick');
        if (onClickHandlers) actionBtn.detachEvent(onClickHandlers);
        actionBtn.attachEvent("onItemClick", state ? cancelInstall : () => INSTALLER_WINDOW?.close());
    }
}

// Shared: cancel handler
function cancelInstall() {
    webix.confirm({
        text: TT("Are you sure you want to cancel?", 'install'),
        ok: TT("Yes"), cancel: TT("No"),
        callback: (r) => {
            if (r && INSTALLER_STATE.eventSource) {
                cleanupInstaller();
                fetch("/install/cancel", { method: "POST" }).catch(console.warn);
                if ($$("installer_status")) {
                    $$("installer_status").setValue(TT("Cancelling... cleaning up.", 'install'));
                }
            }
        }
    });
}

// Shared: SSE message handler
function handleSSEMessage(e, c = 'install') {
    try {
        const data = JSON.parse(e.data);
        if (data.type === "ping" || data.type === "heartbeat") return;

        if (data.type === "progress") {
            setProgressValue(data.value / 100);
        } else if (data.type === "indeterminate") {
            const el = $$("installer_progress")?.$view?.querySelector(".webix_progress_inner");
            if (el) {
                if (data.value) {
                    if (el._anim) clearInterval(el._anim);
                    let pos = 20;
                    let dir = 1;
                    el._anim = setInterval(() => {
                        pos += dir * 2;
                        if (pos >= 80) dir = -1;
                        if (pos <= 20) dir = 1;
                        el.style.width = pos + "%";
                    }, 80);
                } else {
                    if (el._anim) clearInterval(el._anim);
                    delete el._anim;
                    el.style.width = "100%";
                }
            }
        } else if (data.type === "message") {
            if ($$("installer_status")) {
                $$("installer_status").setValue(TT(data.value, c));
            }
        } else if (data.type === "done") {
            cleanupInstaller();
            setInstalling(false, c);
            const msg = data.value
                ? "✅ " + TT("Installation completed successfully!", c)
                : "❌ " + TT("Installation failed. See log for details.", c);
            if ($$("installer_status")) {
                $$("installer_status").setValue(msg);
            }
            setProgressValue(data.value ? 1 : 0);
        }
    } catch (err) {
        console.error("[Installer] SSE parse error:", err, e.data);
    }
}

// Shared: error handler
function handleSSError() {
    cleanupInstaller();
    setInstalling(false, 'install');
    if ($$("installer_status")) {
        $$("installer_status").setValue("❌ " + TT("Connection lost.", 'install'));
    }
}

// Create window (if not exists)
function ensureInstallerWindow(items) {
    if (INSTALLER_WINDOW) return INSTALLER_WINDOW;

    const c = 'install';
    INSTALLER_STATE.items = items;

    // Group items
    const groups = {};
    items.forEach(item => {
        if (!groups[item.group]) groups[item.group] = [];
        groups[item.group].push(item);
    });
    INSTALLER_STATE.groups = groups;
    const groupNames = Object.keys(groups);

    // Helper: update group view
    const updateGroupView = (groupName) => {
        const group = groups[groupName] || [];
        const descView = $$("installer_desc");
        const itemsView = $$("installer_items_list");

        const icon = TT(`${groupName}-icon`, c, "📦");
        const text = TT(`${groupName}-text`, c, "");
        descView.setHTML(`<span style="font-size:20px">${icon}</span> ${text}`);

        const radios = group.map(item => {
            let title = item.name;
            if (item.subtitle) title += ` - ${item.subtitle}`;
            if (item.size) title += `   [${readablizeBytes(item.size)}]`;
            return {
                name: item.name,
                title: title,
                description: item.description || "",
                selected: INSTALLER_STATE.selectedItem === item.name
            };
        });

        itemsView.clearAll();
        itemsView.parse(radios);

        if (!INSTALLER_STATE.selectedItem && group.length) {
            INSTALLER_STATE.selectedItem = group[0].name;
            webix.delay(() => {
                const first = document.querySelector('input[name="installer_item"]');
                if (first) first.checked = true;
            });
        }
    };

    // Create UI
    INSTALLER_WINDOW = webix.ui({
        view: "window",
        id: "installerWindow",
        modal: true,
        close: true,
        move: true,
        resize: true,
        position: "center",
        width: 660,
        height: 520,
        head: TT("appTitle") + ": " + TT("Component Installer", c),
        body: {
            rows: [
                ...(groupNames.length > 1 ? [{
                    view: "toolbar",
                    cols: [
                        {
                            view: "richselect",
                            label: TT("Category:", c),
                            id: "installer_group_select",
                            value: groupNames[0],
                            options: groupNames,
                            width: 200,
                            on: { onChange: v => updateGroupView(v) }
                        },
                        {}
                    ]
                }] : []),

                { id: "installer_desc", template: "Install", autoheight: true, borderless: true },

                {
                    view: "list",
                    id: "installer_items_list",
                    height: 260,
                    scroll: true,
                    type: { height: "auto" },
                    template: webix.template(function(obj) {
                        let descHtml = obj.description
                            ? `<div style="font-size:13px;margin-top:2px;line-height:1.4;">– ${obj.description}</div>`
                            : "";
                        return `
                            <div style="padding:6px 10px 6px 4px;">
                                <label style="display:flex;align-items:flex-start;cursor:pointer;">
                                    <input type="radio" name="installer_item" value="${obj.name}"
                                        ${obj.selected ? "checked" : ""}
                                        style="margin:4px 8px 0 0;transform:scale(1.1);cursor:pointer;">
                                    <div>
                                        <div style="font-weight:500;font-size:14px;line-height:1.3;">${obj.title}</div>
                                        ${descHtml}
                                    </div>
                                </label>
                            </div>
                        `;
                    }),
                    on: {
                        onItemClick: function(id) {
                            const item = this.getItem(id);
                            INSTALLER_STATE.selectedItem = item.name;
                            this.data.each(o => o.selected = (o.name === item.name));
                            this.refresh();
                        }
                    }
                },

                {
                    view: "template",
                    id: "installer_progress",
                    height: 10,
                    css: { "padding": "0", "margin": "0 10px" },
                    template: "<div class='webix_progress_outer'><div class='webix_progress_inner' style='width:0%;'></div></div>"
                },
                { view: "label", id: "installer_status", height: 24, css: { "min-height": "24px" } },

                {
                    view: "toolbar",
                    cols: [
                        {},
                        { view: "button", id: "installer_install_btn", value: TT("Install Selected", c), width: 240 },
                        { view: "button", id: "installer_action_btn", value: TT("Close", c), width: 200 }
                    ]
                }
            ]
        }
    });

    // Initial setup
    const initialGroup = groupNames[0] || "";
    updateGroupView(initialGroup.id);

    // Attach Install button (deferred to avoid overwrite)
    webix.delay(() => {
        const btn = $$("installer_install_btn");
        if (btn) {
            btn.attachEvent("onItemClick", () => {
                const selectedItem = INSTALLER_STATE.selectedItem;
                if (!selectedItem) {
                    webix.message({ type: "error", text: TT("Please select a component to install.", c) });
                    return;
                }
                startInstallForItem(selectedItem);
            });
        }
    });

    return INSTALLER_WINDOW;
}

// 🔹 Start install for a specific item (shared logic)
function startInstallForItem(itemName, c = 'install') {
    const item = INSTALLER_STATE.items.find(i => i.name === itemName);
    if (!item) {
        webix.message({ type: "error", text: `Item not found: ${itemName}` });
        return;
    }

    INSTALLER_STATE.selectedItem = itemName;
    setInstalling(true, c);
    setProgressValue(0);
    if ($$("installer_status")) {
        $$("installer_status").setValue(`Starting: ${itemName}...`);
    }

    cleanupInstaller(); // just in case

    const es = new EventSource(`/install/start?item=${encodeURIComponent(itemName)}`);
    INSTALLER_STATE.eventSource = es;

    es.onmessage = e => handleSSEMessage(e, c);
    es.onerror = handleSSError;
}

// ✅ PUBLIC: Manual install (user-triggered)
function ShowInstallerWindow() {
    ensureInstallerWindow(INSTALL_ITEMS).show();
}

// ✅ PUBLIC: Auto-start install (backend-triggered)
// Call this from your polling logic: ShowInstallerForAutoStart("Español")
function ShowInstallerForAutoStart(itemName) {
    if (!INSTALLER_STATE.items) {
        // Fetch items first, then auto-start
        webix.ajax().get("/install/items").then(res => {
            const items = res.json();
            ensureInstallerWindow(items);
            // Start immediately after window created
            webix.delay(() => startInstallForItem(itemName, 'install'));
            INSTALLER_WINDOW.show();
        }).catch(err => {
            webix.message({ type: "error", text: TT("Failed to prepare installer.", 'install') });
        });
    } else {
        ensureInstallerWindow(INSTALLER_STATE.items);
        startInstallForItem(itemName, 'install');
        INSTALLER_WINDOW.show();
    }
}

// 🧹 Optional: cleanup on unload
window.addEventListener("beforeunload", cleanupInstaller);