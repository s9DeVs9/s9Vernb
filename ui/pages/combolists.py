"""
Combolist manager page - load, preview, and manage combo lists.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os

from ui import theme as T
from ui.widgets import Card, AccentButton
from core.combolist import ComboList


class CombosPage:
    """Combolist manager with load, preview, stats, and filter."""

    def __init__(self, app):
        self.app = app
        self.frame = None
        self.current_combolist: ComboList | None = None
        self._build()

    def _build(self):
        self.frame = tk.Frame(self.app.page_container, bg=T.BG_MAIN)

        # Top row: Load + file info
        top_row = tk.Frame(self.frame, bg=T.BG_MAIN)
        top_row.pack(fill="x", pady=(0, 6))

        AccentButton(top_row, "\U0001f4c2  Load File", command=self._load_file,
                     bold=True).pack(side="left", padx=(0, 8))

        self.file_label = tk.Label(top_row, text="No file loaded",
                                   font=T.FONT_MONO, fg=T.FG2, bg=T.BG_MAIN)
        self.file_label.pack(side="left", padx=(0, 8))

        AccentButton(top_row, "\U0001f4be  Save", command=self._save_file).pack(side="right")

        # Stats row
        stats_card = Card(self.frame, title="STATS")
        stats_card.pack(fill="x", pady=(0, 6))

        stats_inner = tk.Frame(stats_card, bg=T.BG_CARD)
        stats_inner.pack(fill="x")

        self.stat_labels = {}
        for i, (key, label) in enumerate([("total", "Total"), ("domains", "Domains"),
                                           ("dups", "Removed Dups")]):
            col = tk.Frame(stats_inner, bg=T.BG_CARD)
            col.pack(side="left", fill="x", expand=True, padx=8)
            tk.Label(col, text=label, font=T.FONT_STAT_LABEL, fg=T.FG2,
                     bg=T.BG_CARD).pack()
            val_lbl = tk.Label(col, text="0", font=T.FONT_BOLD, fg=T.FG, bg=T.BG_CARD)
            val_lbl.pack()
            self.stat_labels[key] = val_lbl

        # Filter row
        filter_row = tk.Frame(self.frame, bg=T.BG_MAIN)
        filter_row.pack(fill="x", pady=(0, 6))

        tk.Label(filter_row, text="Filter domain:", font=T.FONT, fg=T.FG2,
                 bg=T.BG_MAIN).pack(side="left", padx=(0, 6))

        self.filter_entry = tk.Entry(filter_row, font=T.FONT_MONO, bg=T.INPUT_BG, fg=T.FG,
                                     insertbackground=T.FG, relief="flat", width=25,
                                     highlightbackground=T.BORDER, highlightthickness=1)
        self.filter_entry.pack(side="left", ipady=3, padx=(0, 8))
        self.filter_entry.bind("<Return>", lambda e: self._apply_filter())

        AccentButton(filter_row, "Apply", command=self._apply_filter).pack(side="left", padx=(0, 8))
        AccentButton(filter_row, "Clear", command=self._clear_filter).pack(side="left")

        # Domain breakdown
        self.domains_label = tk.Label(filter_row, text="", font=T.FONT_MONO, fg=T.FG2,
                                      bg=T.BG_MAIN, anchor="e")
        self.domains_label.pack(side="right")

        # Preview text area
        preview_card = Card(self.frame, title="PREVIEW")
        preview_card.pack(fill="both", expand=True)

        self.preview_text = tk.Text(preview_card, bg=T.INPUT_BG, fg=T.FG, font=T.FONT_MONO,
                                    wrap="none", highlightthickness=0, bd=0,
                                    state="disabled", padx=8, pady=4,
                                    insertbackground=T.FG, selectbackground=T.FG2)
        self.preview_text.pack(fill="both", expand=True, pady=(0, 2))

        # Scrollbar for preview
        scrollbar = tk.Scrollbar(self.preview_text)
        scrollbar.pack(side="right", fill="y")
        self.preview_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.preview_text.yview)

        # Color tags
        self.preview_text.tag_config("email", foreground=T.GREEN)
        self.preview_text.tag_config("password", foreground=T.FG2)
        self.preview_text.tag_config("separator", foreground=T.BORDER)

    def _load_file(self):
        filepath = filedialog.askopenfilename(
            title="Select combo list",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filepath:
            return

        cl = ComboList(name=os.path.basename(filepath))
        count = cl.load(filepath)

        if count == 0:
            try:
                messagebox.showwarning("Warning", "No valid combos found in file.")
            except (KeyboardInterrupt, tk.TclError):
                pass
            return

        self.current_combolist = cl
        self.app.combos = cl.combos
        self.app.combo_file = filepath

        # Update UI
        self.file_label.config(text=f"{os.path.basename(filepath)}  ({count} combos)")
        self._update_stats()
        self._update_preview()
        self._update_domains()

        if "dashboard" in self.app.pages:
            self.app.pages["dashboard"].log(f"\u2713 Loaded {count} combos from {os.path.basename(filepath)}")
            self.app.pages["dashboard"].set_combo_count(count)

    def _save_file(self):
        if not self.current_combolist:
            try:
                messagebox.showwarning("Warning", "No combolist loaded.")
            except (KeyboardInterrupt, tk.TclError):
                pass
            return

        filepath = filedialog.asksaveasfilename(
            title="Save combo list",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=self.current_combolist.name,
        )
        if filepath:
            self.current_combolist.save(filepath)
            self.file_label.config(text=f"{os.path.basename(filepath)}  ({len(self.current_combolist)} combos)")

    def _apply_filter(self):
        if not self.current_combolist:
            return
        domain = self.filter_entry.get().strip()
        if not domain:
            self._update_preview()
            return

        filtered = self.current_combolist.filter_by_domain(domain)
        self._display_combos(filtered.combos, f"Filtered: @{domain} ({len(filtered)} combos)")

    def _clear_filter(self):
        self.filter_entry.delete(0, "end")
        self._update_preview()

    def _update_stats(self):
        if not self.current_combolist:
            return
        stats = self.current_combolist.stats()
        self.stat_labels["total"].config(text=str(stats["total"]))
        self.stat_labels["domains"].config(text=str(stats["domains"]))
        self.stat_labels["dups"].config(text=str(stats["total"]))

    def _update_domains(self):
        if not self.current_combolist:
            return
        domains = self.current_combolist.get_domains()
        parts = [f"@{d}: {c}" for d, c in list(domains.items())[:4]]
        self.domains_label.config(text="  ".join(parts) if parts else "")

    def _update_preview(self):
        if not self.current_combolist:
            return
        self._display_combos(self.current_combolist.combos,
                             f"Preview ({len(self.current_combolist)} total)")

    def _display_combos(self, combos: list, title: str = ""):
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", "end")

        for i, (email, password) in enumerate(combos[:200]):
            line_num = f"{i + 1:>5}  "
            self.preview_text.insert("end", line_num, "separator")
            self.preview_text.insert("end", email, "email")
            self.preview_text.insert("end", ":", "separator")
            self.preview_text.insert("end", password, "password")
            self.preview_text.insert("end", "\n")

        if len(combos) > 200:
            self.preview_text.insert("end", f"\n  ... and {len(combos) - 200} more\n", "separator")

        self.preview_text.see("1.0")
        self.preview_text.config(state="disabled")

    def show(self, parent):
        self.frame.pack(in_=parent, fill="both", expand=True)

    def hide(self):
        self.frame.pack_forget()
