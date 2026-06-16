"""
Platforms page - select which platforms to test against.
Displays clickable cards for each platform in a grid layout.
"""

import tkinter as tk

from ui import theme as T
from ui.widgets import Card, AccentButton
from core.platforms import PLATFORMS


class PlatformsPage:
    """Platform selection page with a grid of toggle cards."""

    def __init__(self, app):
        self.app = app
        self.frame = None
        self.platform_cards = {}
        self._build()

    def _build(self):
        self.frame = tk.Frame(self.app.page_container, bg=T.BG_MAIN)

        # Select All / Deselect All buttons
        btn_row = tk.Frame(self.frame, bg=T.BG_MAIN)
        btn_row.pack(fill="x", pady=(0, 8))
        AccentButton(btn_row, "Select All", command=self._select_all).pack(side="left", padx=(0, 8))
        AccentButton(btn_row, "Deselect All", command=self._deselect_all).pack(side="left")

        # Grid of platform cards (3 columns)
        grid = tk.Frame(self.frame, bg=T.BG_MAIN)
        grid.pack(fill="x")

        platform_names = sorted(PLATFORMS.keys())
        cols = 3
        for i, pname in enumerate(platform_names):
            r, c = divmod(i, cols)
            card_frame = tk.Frame(grid, bg=T.BG_CARD, highlightbackground=T.BORDER,
                                  highlightthickness=1, bd=0, cursor="hand2")
            card_frame.grid(row=r, column=c, sticky="nsew", padx=(0, 8), pady=(0, 8))
            grid.columnconfigure(c, weight=1)

            # Accent bar at top when selected
            accent_bar = tk.Frame(card_frame, bg=T.GREEN, height=2)
            accent_bar.pack(fill="x")

            # Inner content
            inner = tk.Frame(card_frame, bg=T.BG_CARD)
            inner.pack(fill="x", padx=12, pady=10)

            indicator = tk.Label(inner, text="\u2713", font=("Consolas", 12, "bold"),
                                 fg=T.GREEN, bg=T.BG_CARD, width=2)
            indicator.pack(side="left")

            info_frame = tk.Frame(inner, bg=T.BG_CARD)
            info_frame.pack(side="left", fill="x", expand=True)

            name_label = tk.Label(info_frame, text=pname, font=T.FONT_BOLD,
                                  fg=T.FG, bg=T.BG_CARD, anchor="w")
            name_label.pack(fill="x")

            p = PLATFORMS[pname]
            rate_text = f"{p.rate_limit_per_sec} req/s | max {p.max_concurrent}"
            rate_label = tk.Label(info_frame, text=rate_text, font=T.FONT_MONO, fg=T.FG2,
                                  bg=T.BG_CARD, anchor="w")
            rate_label.pack(fill="x")

            selected = tk.BooleanVar(value=True)
            self.platform_cards[pname] = (card_frame, accent_bar, indicator, selected)

            # Bind click to ALL child widgets so clicks anywhere on the card work
            toggle_cmd = lambda e, name=pname: self._toggle_platform(name)
            for widget in [card_frame, accent_bar, inner, indicator,
                           info_frame, name_label, rate_label]:
                widget.bind("<Button-1>", toggle_cmd)

    def _toggle_platform(self, name):
        """Toggle a platform's selected state."""
        card_frame, accent_bar, indicator, var = self.platform_cards[name]
        var.set(not var.get())
        if var.get():
            accent_bar.configure(bg=T.GREEN)
            indicator.configure(fg=T.GREEN, text="\u2713")
            card_frame.configure(highlightbackground=T.GREEN)
        else:
            accent_bar.configure(bg=T.BORDER)
            indicator.configure(fg=T.FG2, text="")
            card_frame.configure(highlightbackground=T.BORDER)

    def _select_all(self):
        for name in self.platform_cards:
            card_frame, accent_bar, indicator, var = self.platform_cards[name]
            var.set(True)
            accent_bar.configure(bg=T.GREEN)
            indicator.configure(fg=T.GREEN, text="\u2713")
            card_frame.configure(highlightbackground=T.GREEN)

    def _deselect_all(self):
        for name in self.platform_cards:
            card_frame, accent_bar, indicator, var = self.platform_cards[name]
            var.set(False)
            accent_bar.configure(bg=T.BORDER)
            indicator.configure(fg=T.FG2, text="")
            card_frame.configure(highlightbackground=T.BORDER)

    def get_selected(self) -> set:
        return {name for name, (_, _, _, var) in self.platform_cards.items() if var.get()}

    def show(self, parent):
        self.frame.pack(in_=parent, fill="both", expand=True)

    def hide(self):
        self.frame.pack_forget()
