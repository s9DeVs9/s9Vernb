"""
Results page - view saved results from previous test runs.
"""

import tkinter as tk
import os
import sys

from ui import theme as T
from ui.widgets import Card, AccentButton


class ResultsPage:
    """Results viewer with tabs for different result files."""

    def __init__(self, app):
        self.app = app
        self.frame = None
        self.current_filter = "all"
        self._build()

    def _build(self):
        self.frame = tk.Frame(self.app.page_container, bg=T.BG_MAIN)

        # Filter tabs
        tab_row = tk.Frame(self.frame, bg=T.BG_MAIN)
        tab_row.pack(fill="x", pady=(0, 8))

        self.tab_buttons = {}
        filters = [("all", "All"), ("valid", "Valid"), ("results", "Results")]
        for key, label in filters:
            btn = AccentButton(tab_row, label,
                               command=lambda k=key: self._set_filter(k),
                               color=T.FG if key == "all" else T.FG2)
            btn.pack(side="left", padx=(0, 6))
            self.tab_buttons[key] = btn

        AccentButton(tab_row, "\U0001f4c1  Open Folder",
                     command=self._open_folder).pack(side="right")

        # Results text area
        results_card = Card(self.frame, title="RESULTS")
        results_card.pack(fill="both", expand=True, pady=(0, 10))

        self.results_text = tk.Text(results_card, bg=T.INPUT_BG, fg=T.FG, font=T.FONT_MONO,
                                    wrap="word", highlightthickness=0, bd=0,
                                    state="disabled", padx=10, pady=6,
                                    insertbackground=T.FG, selectbackground=T.FG2)
        self.results_text.pack(fill="both", expand=True, pady=(0, 4))

        for tag, color in [("valid", T.GREEN), ("invalid", T.RED),
                           ("error", T.ORANGE), ("info", T.FG)]:
            self.results_text.tag_config(tag, foreground=color)

    def _set_filter(self, filter_name):
        self.current_filter = filter_name
        for key, btn in self.tab_buttons.items():
            if key == filter_name:
                btn.itemconfig(btn._text_id, fill=T.FG)
            else:
                btn.itemconfig(btn._text_id, fill=T.FG2)
        self._load_file()

    def _load_file(self):
        file_map = {
            "all": "results.txt",
            "valid": "hits.txt",
            "results": "results.txt",
        }
        filename = file_map.get(self.current_filter, "results.txt")
        filepath = os.path.join("results", filename)

        self.results_text.config(state="normal")
        self.results_text.delete("1.0", "end")

        if not os.path.exists(filepath):
            self.results_text.insert("end", "No results yet. Run a test first.\n", "info")
            self.results_text.config(state="disabled")
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if "VALID" in line:
                        tag = "valid"
                    elif "INVALID" in line:
                        tag = "invalid"
                    elif "ERROR" in line or "TIMEOUT" in line:
                        tag = "error"
                    else:
                        tag = "info"
                    self.results_text.insert("end", line + "\n", tag)
        except Exception as e:
            self.results_text.insert("end", f"Error reading file: {e}\n", "error")

        self.results_text.see("end")
        self.results_text.config(state="disabled")

    def _open_folder(self):
        results_dir = "results"
        if not os.path.exists(results_dir):
            return
        if sys.platform == "win32":
            os.startfile(results_dir)
        elif sys.platform == "darwin":
            os.system(f"open {results_dir}")
        else:
            os.system(f"xdg-open {results_dir}")

    def refresh(self):
        if self.current_filter:
            self._load_file()

    def show(self, parent):
        self.frame.pack(in_=parent, fill="both", expand=True)
        self._load_file()

    def hide(self):
        self.frame.pack_forget()
