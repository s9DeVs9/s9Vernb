"""
Dashboard page - the main view of S9Checker.
Compact layout: Stats → Progress → File → Buttons → Log(expand)
Buttons are always visible above the expandable log area.
"""

import tkinter as tk
from tkinter import filedialog
from datetime import timedelta

from ui import theme as T
from ui.widgets import Card, StatCard, AccentButton


class DashboardPage:
    """Dashboard with stats, progress, file input, live log, and controls."""

    def __init__(self, app):
        self.app = app
        self.frame = None
        self._build()

    def _build(self):
        self.frame = tk.Frame(self.app.page_container, bg=T.BG_MAIN)

        # Row 1: 5 stat cards (compact)
        stats_row = tk.Frame(self.frame, bg=T.BG_MAIN)
        stats_row.pack(fill="x", pady=(0, 6))

        self.stat_valid = StatCard(stats_row, "VALID", "0", T.GREEN)
        self.stat_valid.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.stat_invalid = StatCard(stats_row, "INVALID", "0", T.RED)
        self.stat_invalid.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.stat_errors = StatCard(stats_row, "ERRORS", "0", T.ORANGE)
        self.stat_errors.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.stat_speed = StatCard(stats_row, "SPEED", "0/s", T.FG)
        self.stat_speed.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.stat_time = StatCard(stats_row, "TIME", "0:00", T.FG2)
        self.stat_time.pack(side="left", fill="x", expand=True)

        # Row 2: Progress bar (compact)
        progress_card = Card(self.frame, title="PROGRESS")
        progress_card.pack(fill="x", pady=(0, 6))

        self.progress_canvas = tk.Canvas(progress_card, bg=T.INPUT_BG, height=22,
                                         highlightthickness=0, bd=0)
        self.progress_canvas.pack(fill="x", padx=0, pady=(0, 2))
        self._draw_progress(0)

        # Row 3: File selector (compact)
        file_card = Card(self.frame, title="COMBO FILE")
        file_card.pack(fill="x", pady=(0, 6))

        file_row = tk.Frame(file_card, bg=T.BG_CARD)
        file_row.pack(fill="x", pady=(0, 4))

        self.file_entry = tk.Entry(file_row, font=T.FONT_MONO, bg=T.INPUT_BG, fg=T.FG,
                                   insertbackground=T.FG, relief="flat",
                                   highlightbackground=T.BORDER, highlightthickness=1)
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=3)

        AccentButton(file_row, "Browse", command=self._browse_file).pack(side="left")

        self.combo_count_label = tk.Label(file_card, text="0 combos loaded",
                                          font=T.FONT, fg=T.FG2, bg=T.BG_CARD, anchor="w")
        self.combo_count_label.pack(fill="x", pady=(0, 2))

        # Row 4: Control buttons (ALWAYS visible, above the log)
        btn_frame = tk.Frame(self.frame, bg=T.BG_MAIN)
        btn_frame.pack(fill="x", pady=(4, 6))

        self.start_btn = AccentButton(btn_frame, "\u25b6  Start Test",
                                      command=self.app.start_test, color=T.GREEN, bold=True)
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = AccentButton(btn_frame, "\u23f9  Stop",
                                     command=self.app.stop_test, color=T.RED)
        self.stop_btn.pack(side="left", padx=(0, 8))

        AccentButton(btn_frame, "\U0001f4c1  Export", command=self._export).pack(side="left", padx=(0, 8))

        # Row 5: Live log (takes remaining space)
        log_card = Card(self.frame, title="LIVE LOG")
        log_card.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_card, bg=T.INPUT_BG, fg=T.FG, font=T.FONT_MONO,
                                wrap="word", highlightthickness=0, bd=0,
                                state="disabled", padx=8, pady=4,
                                insertbackground=T.FG, selectbackground=T.FG2)
        self.log_text.pack(fill="both", expand=True, pady=(0, 2))

        for tag, color in [("valid", T.GREEN), ("invalid", T.RED),
                           ("error", T.ORANGE), ("rate_limited", T.PURPLE),
                           ("info", T.FG), ("dim", T.FG2)]:
            self.log_text.tag_config(tag, foreground=color)

    def show(self, parent):
        self.frame.pack(in_=parent, fill="both", expand=True)

    def hide(self):
        self.frame.pack_forget()

    def log(self, message, tag="info"):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def set_combo_count(self, count):
        self.combo_count_label.config(text=f"{count} combos loaded")

    def set_status(self, text, color=T.FG):
        pass

    def set_buttons(self, running):
        if running:
            self.start_btn.disable()
            self.stop_btn.enable()
        else:
            self.start_btn.enable()
            self.stop_btn.disable()

    def update_progress(self, info):
        pct = info.get("percent", 0)
        self._draw_progress(pct)
        self.stat_valid.set_value(info.get("valid", 0))
        self.stat_invalid.set_value(info.get("invalid", 0))
        self.stat_errors.set_value(info.get("errors", 0))
        self.stat_speed.set_value(f"{info.get('speed', 0)}/s")
        elapsed = info.get("elapsed", 0)
        td = timedelta(seconds=int(elapsed))
        self.stat_time.set_value(str(td))

    def _draw_progress(self, percent):
        c = self.progress_canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 2:
            w = 700

        c.create_rectangle(0, 0, w, h, fill=T.INPUT_BG, outline="")

        if percent > 0:
            bar_w = int(w * min(percent, 100) / 100)
            for i in range(bar_w):
                ratio = i / max(w, 1)
                v = int(0x44 + (0xff - 0x44) * ratio)
                color = f"#{v:02x}{v:02x}{v:02x}"
                c.create_line(i, 1, i, h - 1, fill=color)

        txt_color = T.FG if percent > 30 else T.FG2
        c.create_text(w // 2, h // 2, text=f"{percent}%", fill=txt_color,
                      font=T.FONT_BOLD, anchor="center")

    def _browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select combo list",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, filename)
            self.app.load_combos(filename)

    def _export(self):
        import os, sys
        results_dir = "results"
        if not os.path.exists(results_dir):
            return
        if sys.platform == "win32":
            os.startfile(results_dir)
        elif sys.platform == "darwin":
            os.system(f"open {results_dir}")
        else:
            os.system(f"xdg-open {results_dir}")
