import customtkinter as ctk
from CTkTable import CTkTable

class ScrollableCTkTable(ctk.CTkFrame):
    def __init__(self, parent, headers, rows=None, wraplength=200, **kwargs):
        super().__init__(parent, **kwargs)
        self.headers = headers
        self._current_table = None
        self._wraplength = wraplength  # store as private attr to avoid confusion

        # Vertical scrollable frame (no horizontal)
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            orientation="vertical",  # ← vertical scrolling
            # height will be constrained by parent grid; no need to fix it
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.update_table(rows or [])


    def update_table(self, new_rows):
        # Safely destroy old table after current events
        if self._current_table:
            self.after(10, self._current_table.destroy)
            self._current_table = None

        all_data = [self.headers] + new_rows
        if not all_data or not all_data[0]:
            return

        # Create new table with default font, small padding, and wrap
        self._current_table = CTkTable(
            master=self.scrollable_frame,
            values=all_data,
            wraplength=self._wraplength,
            padx=1,
            pady=1,
        )
        self._current_table.pack(fill="both", expand=True)