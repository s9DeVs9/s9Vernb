
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import timedelta
import os
import json
import csv

from ui import theme as T
from ui.widgets import Card, StatCard, SlideButton


class DashboardPage:

    def __init__(self, app):
        self.app = app
        self.frame = None
        self._build()

    def _build(self):
        self.frame = ctk.CTkFrame(self.app.page_container, fg_color=T.BG_MAIN)

        stats_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 8))

        self.stat_valid = StatCard(stats_row, "VALID", "0", T.GREEN)
        self.stat_valid.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.stat_invalid = StatCard(stats_row, "INVALID", "0", T.RED)
        self.stat_invalid.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.stat_errors = StatCard(stats_row, "ERRORS", "0", T.ORANGE)
        self.stat_errors.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.stat_speed = StatCard(stats_row, "SPEED", "0/s", T.CYAN)
        self.stat_speed.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.stat_time = StatCard(stats_row, "TIME", "0:00", T.FG2)
        self.stat_time.pack(side="left", fill="x", expand=True)

        progress_card = Card(self.frame, title="PROGRESS")
        progress_card.pack(fill="x", pady=(0, 8))

        self.progress_bar = ctk.CTkProgressBar(progress_card, height=22,
                                                progress_color=T.ACCENT,
                                                fg_color=T.INPUT_BG,
                                                corner_radius=4)
        self.progress_bar.pack(fill="x", pady=(4, 2))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(progress_card, text="0%", font=T.FONT_BOLD,
                                            text_color=T.FG2)
        self.progress_label.pack()

        file_card = Card(self.frame, title="COMBO FILE")
        file_card.pack(fill="x", pady=(0, 8))

        file_row = ctk.CTkFrame(file_card, fg_color="transparent")
        file_row.pack(fill="x", pady=(0, 4))

        self.file_entry = ctk.CTkEntry(file_row, font=T.FONT_MONO,
                                        fg_color=T.INPUT_BG, text_color=T.FG,
                                        border_color=T.INPUT_BORDER,
                                        placeholder_text="No file selected",
                                        placeholder_text_color=T.FG3)
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        SlideButton(file_row, "Browse", command=self._browse_file,
                    color=T.ACCENT, width=100).pack(side="left")

        self.combo_count_label = ctk.CTkLabel(file_card, text="0 combos loaded",
                                               font=T.FONT, text_color=T.FG2, anchor="w")
        self.combo_count_label.pack(fill="x", pady=(0, 2))

        btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(4, 8))

        self.start_btn = SlideButton(btn_frame, "\u25b6  Start Test",
                                      command=self.app.start_test,
                                      color=T.GREEN, width=160, bold=True)
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = SlideButton(btn_frame, "\u23f9  Stop",
                                     command=self.app.stop_test,
                                     color=T.RED, width=120)
        self.stop_btn.pack(side="left", padx=(0, 8))

        SlideButton(btn_frame, "\U0001f4e5  Export", command=self._export,
                    color=T.CYAN, width=120).pack(side="left", padx=(0, 8))

        log_card = Card(self.frame, title="LIVE LOG")
        log_card.pack(fill="both", expand=True)

        log_header = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header.pack(fill="x", pady=(4, 2))

        self.log_text = ctk.CTkTextbox(log_card, font=T.FONT_MONO,
                                        fg_color=T.INPUT_BG, text_color=T.FG,
                                        border_color=T.INPUT_BORDER,
                                        border_width=1, corner_radius=4,
                                        wrap="word")
        self.log_text.pack(fill="both", expand=True, pady=(0, 4))

        SlideButton(log_header, "Clear", command=self._clear_log,
                    color=T.FG3, width=70).pack(side="right")

        self.status_label = ctk.CTkLabel(self.frame, text="", font=T.FONT_BOLD,
                                          text_color=T.FG2)
        self.status_label.pack(fill="x", pady=(4, 0))

    def show(self, parent):
        self.frame.pack(in_=parent, fill="both", expand=True)

    def hide(self):
        self.frame.pack_forget()

    def log(self, message, tag="info"):
        color_map = {
            "valid": T.GREEN,
            "invalid": T.RED,
            "error": T.ORANGE,
            "rate_limited": T.PURPLE,
            "info": T.FG,
            "dim": T.FG2,
        }
        color = color_map.get(tag, T.FG)
        self.log_text.configure(text_color=T.FG)
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def _clear_log(self):
        self.log_text.delete("1.0", "end")

    def set_combo_count(self, count):
        self.combo_count_label.configure(text=f"{count} combos loaded")

    def set_status(self, text, color=T.FG):
        self.status_label.configure(text=text, text_color=color)

    def set_buttons(self, running):
        if running:
            self.start_btn.disable()
            self.stop_btn.enable()
        else:
            self.start_btn.enable()
            self.stop_btn.disable()

    def update_progress(self, info):
        pct = info.get("percent", 0) / 100.0
        self.progress_bar.set(min(pct, 1.0))
        self.progress_label.configure(text=f"{int(pct * 100)}%")

        self.stat_valid.set_value(info.get("valid", 0))
        self.stat_invalid.set_value(info.get("invalid", 0))
        self.stat_errors.set_value(info.get("errors", 0))
        self.stat_speed.set_value(f"{info.get('speed', 0)}/s")
        elapsed = info.get("elapsed", 0)
        td = timedelta(seconds=int(elapsed))
        self.stat_time.set_value(str(td))

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
        results_dir = "results"
        if not os.path.exists(results_dir):
            try:
                messagebox.showinfo("Export", "No results to export. Run a test first.")
            except (KeyboardInterrupt, tk.TclError):
                pass
            return

        filepath = filedialog.asksaveasfilename(
            title="Export results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("Text files", "*.txt")],
            initialfile="results_export"
        )
        if not filepath:
            return

        results_file = os.path.join(results_dir, "results.txt")
        if not os.path.exists(results_file):
            try:
                messagebox.showinfo("Export", "No results to export.")
            except (KeyboardInterrupt, tk.TclError):
                pass
            return

        try:
            with open(results_file, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]

            if filepath.endswith(".json"):
                records = []
                for line in lines:
                    parts = line.split(" -> ")
                    if len(parts) >= 2:
                        meta = parts[0].strip("[]")
                        status = parts[1].split(" | ")[0]
                        details = parts[1].split(" | ")[1] if " | " in parts[1] else ""
                        email_pass = meta.split("] ", 1)
                        platform = email_pass[0] if len(email_pass) > 0 else ""
                        creds = email_pass[1] if len(email_pass) > 1 else ""
                        email = creds.split(":")[0] if ":" in creds else creds
                        password = creds.split(":")[1] if ":" in creds else ""
                        records.append({
                            "platform": platform, "email": email,
                            "password": password, "status": status,
                            "details": details
                        })
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=2, ensure_ascii=False)

            elif filepath.endswith(".csv"):
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Platform", "Email", "Password", "Status", "Details"])
                    for line in lines:
                        parts = line.split(" -> ")
                        if len(parts) >= 2:
                            meta = parts[0].strip("[]")
                            status = parts[1].split(" | ")[0]
                            details = parts[1].split(" | ")[1] if " | " in parts[1] else ""
                            email_pass = meta.split("] ", 1)
                            platform = email_pass[0] if len(email_pass) > 0 else ""
                            creds = email_pass[1] if len(email_pass) > 1 else ""
                            email = creds.split(":")[0] if ":" in creds else creds
                            password = creds.split(":")[1] if ":" in creds else ""
                            writer.writerow([platform, email, password, status, details])
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")

            try:
                messagebox.showinfo("Export", f"Exported {len(lines)} results to:\n{filepath}")
            except (KeyboardInterrupt, tk.TclError):
                pass
        except Exception as e:
            try:
                messagebox.showerror("Export Error", f"Failed to export:\n{e}")
            except (KeyboardInterrupt, tk.TclError):
                pass
