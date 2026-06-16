
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os

from ui import theme as T
from ui.widgets import Card, SlideButton
from core.combolist import ComboList


class CombosPage:

    def __init__(self, app):
        self.app = app
        self.frame = None
        self.current_combolist = None
        self._build()

    def _build(self):
        self.frame = ctk.CTkFrame(self.app.page_container, fg_color=T.BG_MAIN)

        top_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 8))

        SlideButton(top_row, "\U0001f4c2  Load File", command=self._load_file,
                    color=T.ACCENT, width=130, bold=True).pack(side="left", padx=(0, 8))

        self.file_label = ctk.CTkLabel(top_row, text="No file loaded",
                                        font=T.FONT_MONO, text_color=T.FG2, anchor="w")
        self.file_label.pack(side="left", padx=(0, 8))

        SlideButton(top_row, "\U0001f4be  Save", command=self._save_file,
                    color=T.FG2, width=90).pack(side="right")

        stats_card = Card(self.frame, title="STATS")
        stats_card.pack(fill="x", pady=(0, 8))

        stats_inner = ctk.CTkFrame(stats_card, fg_color="transparent")
        stats_inner.pack(fill="x")

        self.stat_labels = {}
        for key, label in [("total", "Total"), ("domains", "Domains"),
                           ("unique", "Unique")]:
            col = ctk.CTkFrame(stats_inner, fg_color="transparent")
            col.pack(side="left", fill="x", expand=True, padx=8)
            ctk.CTkLabel(col, text=label, font=T.FONT_STAT_LABEL,
                         text_color=T.FG2).pack()
            val_lbl = ctk.CTkLabel(col, text="0", font=T.FONT_BOLD,
                                    text_color=T.FG)
            val_lbl.pack()
            self.stat_labels[key] = val_lbl

        filter_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        filter_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(filter_row, text="Filter domain:", font=T.FONT,
                     text_color=T.FG2).pack(side="left", padx=(0, 8))

        self.filter_entry = ctk.CTkEntry(filter_row, font=T.FONT_MONO,
                                         fg_color=T.INPUT_BG, text_color=T.FG,
                                         border_color=T.INPUT_BORDER,
                                         placeholder_text="gmail.com",
                                         placeholder_text_color=T.FG3,
                                         width=200)
        self.filter_entry.pack(side="left", padx=(0, 8))
        self.filter_entry.bind("<Return>", lambda e: self._apply_filter())

        SlideButton(filter_row, "Apply", command=self._apply_filter,
                    color=T.ACCENT, width=80).pack(side="left", padx=(0, 8))
        SlideButton(filter_row, "Clear", command=self._clear_filter,
                    color=T.FG3, width=80).pack(side="left")

        self.domains_label = ctk.CTkLabel(filter_row, text="", font=T.FONT_MONO,
                                           text_color=T.FG2, anchor="e")
        self.domains_label.pack(side="right")

        preview_card = Card(self.frame, title="PREVIEW")
        preview_card.pack(fill="both", expand=True)

        self.preview_text = ctk.CTkTextbox(preview_card, font=T.FONT_MONO,
                                            fg_color=T.INPUT_BG, text_color=T.FG,
                                            border_color=T.INPUT_BORDER,
                                            border_width=1, corner_radius=4,
                                            wrap="none")
        self.preview_text.pack(fill="both", expand=True, pady=(4, 4))

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

        self.file_label.configure(text=f"{os.path.basename(filepath)}  ({count} combos)")
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
            self.file_label.configure(text=f"{os.path.basename(filepath)}  ({len(self.current_combolist)} combos)")

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
        self.stat_labels["total"].configure(text=str(stats["total"]))
        self.stat_labels["domains"].configure(text=str(stats["domains"]))
        self.stat_labels["unique"].configure(text=str(stats.get("unique", stats["total"])))

    def _update_domains(self):
        if not self.current_combolist:
            return
        domains = self.current_combolist.get_domains()
        parts = [f"@{d}: {c}" for d, c in list(domains.items())[:4]]
        self.domains_label.configure(text="  ".join(parts) if parts else "")

    def _update_preview(self):
        if not self.current_combolist:
            return
        self._display_combos(self.current_combolist.combos,
                             f"Preview ({len(self.current_combolist)} total)")

    def _display_combos(self, combos, title=""):
        self.preview_text.delete("1.0", "end")

        for i, (email, password) in enumerate(combos[:200]):
            line_num = f"{i + 1:>5}  "
            self.preview_text.insert("end", line_num)
            self.preview_text.insert("end", email)
            self.preview_text.insert("end", ":")
            self.preview_text.insert("end", password + "\n")

        if len(combos) > 200:
            self.preview_text.insert("end", f"\n  ... and {len(combos) - 200} more\n")

        self.preview_text.see("1.0")

    def show(self, parent):
        self.frame.pack(in_=parent, fill="both", expand=True)

    def hide(self):
        self.frame.pack_forget()
