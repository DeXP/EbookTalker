# ui/desktop.py
import os
import sys
import queue
import threading
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from helpers import DownloadItem
from helpers.detection import detect_nvidia_gpu
from helpers.downloader import DownloaderCore
from helpers.translation import T

class EbookTalkerInstallerUI(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTkToplevel, var: dict, items: list[DownloadItem], preselect_name: str = None):
        super().__init__(parent)
        T.Cat("install")
        self.parent = parent
        self.var = var
        self.torchGroup = var['torch']['cpu'].group

        self.title(T.T("appTitle") + ": " + T.C("Component Installer"))
        # self.geometry("680x560")
        self.geometry(parent.get_child_geometry(width=680, height=560))
        self.minsize(650, 440)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Filter items
        self.items = []
        for item in items:
            if item.group == self.torchGroup:
                if self.should_show_torch_group():
                    self.items.append(item)
            else:
                self.items.append(item)

        # Group
        self.groups = {}
        for item in self.items:
            self.groups.setdefault(item.group, []).append(item)

        self.selected_item = None
        self.worker_thread = None
        self.cancel_event = None
        self.status_queue = queue.Queue()
        self.installing = False
        self.indeterminate_mode = False

        if preselect_name:
            for item in self.items:
                if item.name == preselect_name:
                    self.selected_item = item
                    break

        self.setup_ui()
        self.after(50, self.process_queue)


    def should_show_torch_group(self) -> bool:
        return sys.platform == "win32"


    def setup_ui(self):
        T.Cat("install")
        self.selector_frame = None
        if len(self.groups) > 1:
            self.selector_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.selector_frame.pack(pady=(15, 10), padx=20, fill="x")
            ctk.CTkLabel(self.selector_frame, text=T.C("Category:")).pack(side="left", padx=(0, 10))
            # set default group?
            self.group_var = ctk.StringVar()
            self.group_combo = ctk.CTkComboBox(
                self.selector_frame,
                values=list(self.groups.keys()),
                variable=self.group_var,
                command=self.on_group_change,
                width=220,
                state="readonly"
            )
            self.group_combo.pack(side="left")

        self.desc_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.desc_frame.pack(pady=(0, 15), padx=20, fill="x")
        self.icon_label = ctk.CTkLabel(self.desc_frame, text="📦", font=("Segoe UI", 24))
        self.icon_label.pack(side="left", padx=(0, 15))
        self.desc_text = ctk.CTkLabel(self.desc_frame, text="", wraplength=520, justify="left")
        self.desc_text.pack(side="left", fill="x", expand=True)

        self.item_frame = ctk.CTkScrollableFrame(self, width=640, height=240)
        self.item_frame.pack(pady=5, padx=20, fill="both", expand=True)

        self.item_var = ctk.StringVar()
        self.radio_buttons = []

        groups = list(self.groups.keys())
        if groups:
            initial_group = groups[0]
            if self.selected_item:
                initial_group = self.selected_item.group
            if len(self.groups) > 1 and self.selector_frame:
                self.group_var.set(initial_group)
                self.group_combo.set(initial_group)
            self.update_group_view(initial_group)
            if initial_group == self.torchGroup:
                self.auto_select_torch()

        self.setup_remaining_ui()

    def on_group_change(self, choice: str):
        self.update_group_view(choice)
        if choice == self.torchGroup:
            self.auto_select_torch()

    def auto_select_torch(self):
        gpu = detect_nvidia_gpu()
        target = self.var['torch'].get(gpu, self.var['torch']['cpu'])       
        for item in self.groups.get(self.torchGroup, []):
            if item.name == target.name:
                self.item_var.set(item.name)
                self.selected_item = item
                break

    def update_group_view(self, group: str):
        for rb in self.radio_buttons:
            rb.destroy()
        self.radio_buttons.clear()

        self.icon_label.configure(text=T.C(f"{group}-icon", default="📦"))
        self.desc_text.configure(text=T.C(f"{group}-text", default=''))

        for item in self.groups.get(group, []):
            title = f"{item.name} - {item.subtitle}" if item.subtitle else item.name
            if item.size:
                title = f"{title}   [{T.SizeFormat(item.size)}]"
            rb = ctk.CTkRadioButton(self.item_frame, text=title, variable=self.item_var, value=item.name, command=self.on_item_select)
            rb.pack(anchor="w", padx=10, pady=(5, 2))
            self.radio_buttons.append(rb)
            if item.description:
                desc = ctk.CTkLabel(self.item_frame, text=f"   – {item.description}", text_color="gray", wraplength=500)
                desc.pack(anchor="w", padx=30, pady=(0, 4))
                self.radio_buttons.append(desc)

        current = self.item_var.get()
        if not current and self.groups.get(group):
            first_item = self.groups[group][0]
            self.item_var.set(first_item.name)
            self.selected_item = first_item

    def on_item_select(self):
        name = self.item_var.get()
        for item in self.items:
            if item.name == name:
                self.selected_item = item
                break

    def on_close(self):
        self.destroy()

    def set_installing(self, installing: bool):
        T.Cat("install")
        self.installing = installing
        state = "disabled" if installing else "normal"
        self.install_btn.configure(state=state)
        if len(self.groups) > 1 and self.group_combo:
            self.group_combo.configure(state=state)
        for rb in self.radio_buttons:
            if isinstance(rb, ctk.CTkRadioButton):
                rb.configure(state=state)
        if installing:
            self.action_btn.configure(text=T.C("Cancel"), command=self.request_cancel)
        else:
            self.action_btn.configure(text=T.C("Exit"), command=self.destroy)

    def start_install(self):
        if not self.selected_item:
            CTkMessagebox(master=self, title="No Selection", message="Please select a component to install.", icon="warning")
            return
        self.set_installing(True)
        self.progress.set(0)
        self.indeterminate_mode = False
        self.status_label.configure(text=f"Starting: {self.selected_item.name}...")
        self.cancel_event = threading.Event()
        self.worker_thread = threading.Thread(target=self._install_worker, args=(self.selected_item,), daemon=True)
        self.worker_thread.start()

    def _install_worker(self, item: DownloadItem):
        downloader = DownloaderCore(item, self.cancel_event, self.status_queue)
        success = downloader.run()
        self.status_queue.put(("done", success))

    def request_cancel(self):
        T.Cat("install")
        msg = CTkMessagebox(master=self, title=T.C("Cancel?"), message=T.C("Are you sure you want to cancel?"), icon="question", option_1="No", option_2="Yes")
        if msg.get() == "Yes":
            self.request_cancel_nowait()

    def request_cancel_nowait(self):
        if self.cancel_event:
            self.cancel_event.set()
        self.status_label.configure(text=T.T("Cancelling... cleaning up.", "install"))

    def setup_remaining_ui(self):
        self.progress = ctk.CTkProgressBar(self, mode="determinate", height=10)
        self.progress.set(0)
        self.progress.pack(pady=(15, 5), padx=30, fill="x")
        self.status_label = ctk.CTkLabel(self, text="", wraplength=600, height=24)
        self.status_label.pack(pady=(0, 10))
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 20))
        self.install_btn = ctk.CTkButton(button_frame, text=T.C("Install Selected"), command=self.start_install)
        self.install_btn.pack(side="left", padx=10)
        self.action_btn = ctk.CTkButton(button_frame, text=T.C("Exit"), command=self.destroy)
        self.action_btn.pack(side="left", padx=10)

    def process_queue(self):
        T.Cat("install")
        try:
            while True:
                msg_type, value = self.status_queue.get_nowait()
                if msg_type == "message":
                    self.status_label.configure(text=T.C(str(value)))
                elif msg_type == "progress":
                    if not self.indeterminate_mode:
                        self.progress.set(float(value) / 100.0)
                elif msg_type == "indeterminate":
                    enable = bool(value)
                    self.indeterminate_mode = enable
                    if enable:
                        self.progress.configure(mode="indeterminate")
                        self.progress.start()
                    else:
                        self.progress.stop()
                        self.progress.configure(mode="determinate")
                        self.progress.set(1.0)
                elif msg_type == "done":
                    self.set_installing(False)
                    if value and not (self.cancel_event and self.cancel_event.is_set()):
                        self.status_label.configure(text=T.C("Installation completed successfully!"))
                    elif not value and not (self.cancel_event and self.cancel_event.is_set()):
                        self.status_label.configure(text=T.C("Installation failed. See log for details."))
                    break
        except queue.Empty:
            pass
        self.after(50, self.process_queue)

    def run(self):
        self.mainloop()
