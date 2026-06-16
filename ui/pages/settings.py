"""
Settings page - configure proxy, concurrency, delay, and timeout behavior.
"""

import tkinter as tk

from ui import theme as T
from ui.widgets import Card


class SettingsPage:
    """Settings page with proxy, performance, and behavior options."""

    def __init__(self, app):
        self.app = app
        self.frame = None
        self._build()

    def _build(self):
        self.frame = tk.Frame(self.app.page_container, bg=T.BG_MAIN)

        # --- Network card ---
        net_card = Card(self.frame, title="NETWORK")
        net_card.pack(fill="x", pady=(0, 10))

        row = tk.Frame(net_card, bg=T.BG_CARD)
        row.pack(fill="x", pady=(0, 4))

        tk.Label(row, text="Proxy:", font=T.FONT, fg=T.FG2, bg=T.BG_CARD).pack(
            side="left", padx=(0, 6))

        self.proxy_entry = tk.Entry(row, font=T.FONT_MONO, bg=T.INPUT_BG, fg=T.FG,
                                    insertbackground=T.FG, relief="flat", width=40,
                                    highlightbackground=T.BORDER, highlightthickness=1)
        self.proxy_entry.pack(side="left", ipady=4)

        tk.Label(row, text="(socks5://host:port or http://host:port)",
                 font=T.FONT_MONO, fg=T.FG2, bg=T.BG_CARD).pack(side="left", padx=(10, 0))

        # --- Performance card ---
        perf_card = Card(self.frame, title="PERFORMANCE")
        perf_card.pack(fill="x", pady=(0, 10))

        row2 = tk.Frame(perf_card, bg=T.BG_CARD)
        row2.pack(fill="x", pady=(0, 4))

        tk.Label(row2, text="Concurrency:", font=T.FONT, fg=T.FG2, bg=T.BG_CARD).pack(
            side="left", padx=(0, 6))
        self.concurrency_spin = tk.Spinbox(row2, from_=1, to=50, width=5, font=T.FONT_MONO,
                                           bg=T.INPUT_BG, fg=T.FG,
                                           buttonbackground=T.BG_CARD, relief="flat",
                                           highlightbackground=T.BORDER, highlightthickness=1)
        self.concurrency_spin.pack(side="left", padx=(0, 20))
        self.concurrency_spin.delete(0, "end")
        self.concurrency_spin.insert(0, "10")

        tk.Label(row2, text="Delay (s):", font=T.FONT, fg=T.FG2, bg=T.BG_CARD).pack(
            side="left", padx=(0, 6))
        self.delay_spin = tk.Spinbox(row2, from_=0.0, to=5.0, increment=0.1, width=5,
                                     font=T.FONT_MONO, bg=T.INPUT_BG, fg=T.FG,
                                     buttonbackground=T.BG_CARD, relief="flat",
                                     highlightbackground=T.BORDER, highlightthickness=1)
        self.delay_spin.pack(side="left", padx=(0, 20))
        self.delay_spin.delete(0, "end")
        self.delay_spin.insert(0, "0.3")

        # --- Behavior card ---
        behavior_card = Card(self.frame, title="BEHAVIOR")
        behavior_card.pack(fill="x", pady=(0, 10))

        row3 = tk.Frame(behavior_card, bg=T.BG_CARD)
        row3.pack(fill="x", pady=(0, 4))

        self.ignore_timeout_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row3, text="Ignore timeouts (treat timeout as error instead)",
                       variable=self.ignore_timeout_var, font=T.FONT, fg=T.FG,
                       bg=T.BG_CARD, selectcolor=T.BG_CARD,
                       activebackground=T.BG_CARD, activeforeground=T.FG).pack(side="left")

    def get_proxy(self):
        val = self.proxy_entry.get().strip()
        return val if val else None

    def get_concurrency(self):
        return int(self.concurrency_spin.get())

    def get_delay(self):
        return float(self.delay_spin.get())

    def get_ignore_timeouts(self):
        return self.ignore_timeout_var.get()

    def show(self, parent):
        self.frame.pack(in_=parent, fill="both", expand=True)

    def hide(self):
        self.frame.pack_forget()
