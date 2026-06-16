
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys

from ui import theme as T
from ui.widgets import Card, SlideButton


class ResultsPage:

    def __init__(self, app):
        self.app = app
        self.frame = None
        self.current_filter = "all"
        self._build()

    def _build(self):
        self.frame = ctk.CTkFrame(self.app.page_container, fg_color=T.BG_MAIN)

        tab_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        tab_row.pack(fill="x", pady=(0, 8))

        self.tab_buttons = {}
        filters = [("all", "All"), ("valid", "Valid"), ("errors", "Errors")]
        for key, label in filters:
            btn = SlideButton(tab_row, label,
                              command=lambda k=key: self._set_filter(k),
                              color=T.FG if key == "all" else T.FG2,
                              width=90)
            btn.pack(side="left", padx=(0, 6))
            self.tab_buttons[key] = btn

        SlideButton(tab_row, "\U0001f4e5  Export", command=self._export,
                    color=T.CYAN, width=110).pack(side="right")

        SlideButton(tab_row, "\U0001f4c2  Open Folder", command=self._open_folder,
                    color=T.FG2, width=120).pack(side="right", padx=(0, 8))

        results_card = Card(self.frame, title="RESULTS")
        results_card.pack(fill="both", expand=True, pady=(0, 10))

        self.results_text = ctk.CTkTextbox(results_card, font=T.FONT_MONO,
                                            fg_color=T.INPUT_BG, text_color=T.FG,
                                            border_color=T.INPUT_BORDER,
                                            border_width=1, corner_radius=4,
                                            wrap="word")
        self.results_text.pack(fill="both", expand=True, pady=(4, 4))

    def _set_filter(self, filter_name):
        self.current_filter = filter_name
        self._load_file()

    def _load_file(self):
        file_map = {
            "all": "results.txt",
            "valid": "hits.txt",
            "errors": "results.txt",
        }
        filename = file_map.get(self.current_filter, "results.txt")
        filepath = os.path.join("results", filename)

        self.results_text.delete("1.0", "end")

        if not os.path.exists(filepath):
            self.results_text.insert("end", "No results yet. Run a test first.\n")
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if self.current_filter == "errors" and "VALID" in line:
                        continue
                    self.results_text.insert("end", line + "\n")
        except Exception as e:
            self.results_text.insert("end", f"Error reading file: {e}\n")

        self.results_text.see("end")

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

    def _export(self):
        results_dir = "results"
        if not os.path.exists(results_dir):
            try:
                messagebox.showinfo("Export", "No results to export.")
            except (KeyboardInterrupt, tk.TclError):
                pass
            return

        filepath = filedialog.asksaveasfilename(
            title="Export results",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile="results_export.txt"
        )
        if not filepath:
            return

        results_file = os.path.join(results_dir, "results.txt")
        if not os.path.exists(results_file):
            return

        try:
            with open(results_file, "r", encoding="utf-8") as f:
                content = f.read()
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            try:
                messagebox.showinfo("Export", f"Results exported to:\n{filepath}")
            except (KeyboardInterrupt, tk.TclError):
                pass
        except Exception as e:
            try:
                messagebox.showerror("Export Error", f"Failed to export:\n{e}")
            except (KeyboardInterrupt, tk.TclError):
                pass

    def refresh(self):
        if self.current_filter:
            self._load_file()

    def show(self, parent):
        self.frame.pack(in_=parent, fill="both", expand=True)
        self._load_file()

    def hide(self):
        self.frame.pack_forget()
