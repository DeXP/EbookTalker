import customtkinter as ctk
from CTkTable import CTkTable

class ScrollableCTkTable(ctk.CTkFrame):
    def __init__(self, parent, headers, rows=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.headers = headers
        self._current_table = None
        self.scrollable_frame = ctk.CTkScrollableFrame(self, orientation="vertical")
        self.scrollable_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.update_table(rows or [])


    def update_table(self, new_rows):
        # Destroy old table if exists
        if self._current_table:
            self._current_table.destroy()

        # Build full data: header + rows
        all_data = [self.headers] + new_rows

        # Create new table with exact dimensions
        self._current_table = CTkTable(
            master=self.scrollable_frame,
            values=all_data,
            wraplength=320,  # prevents overly wide columns
            padx=1,
            pady=1,
        )
        self._current_table.pack(fill="both", expand=True)