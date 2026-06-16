
import customtkinter as ctk
import tkinter as tk

from ui import theme as T
from ui.widgets import SlideButton
from core.platforms import PLATFORMS


class PlatformsPage:

    def __init__(self, app):
        self.app = app
        self.frame = None
        self.platform_cards = {}
        self._build()

    def _build(self):
        self.frame = ctk.CTkFrame(self.app.page_container, fg_color=T.BG_MAIN)

        btn_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 8))
        SlideButton(btn_row, "Select All", command=self._select_all,
                    color=T.GREEN, width=110).pack(side="left", padx=(0, 8))
        SlideButton(btn_row, "Deselect All", command=self._deselect_all,
                    color=T.RED, width=110).pack(side="left")

        grid = ctk.CTkFrame(self.frame, fg_color="transparent")
        grid.pack(fill="both", expand=True)

        platform_names = sorted(PLATFORMS.keys())
        cols = 3
        for i, pname in enumerate(platform_names):
            r, c = divmod(i, cols)
            grid.columnconfigure(c, weight=1)

            card_frame = ctk.CTkFrame(grid, fg_color=T.BG_CARD,
                                       border_color=T.BORDER,
                                       border_width=1,
                                       corner_radius=T.CARD_CORNER_RADIUS,
                                       cursor="hand2")
            card_frame.grid(row=r, column=c, sticky="nsew", padx=(0, 8), pady=(0, 8))

            accent_bar = ctk.CTkFrame(card_frame, fg_color=T.GREEN,
                                       height=3, corner_radius=1)
            accent_bar.pack(fill="x")

            inner = ctk.CTkFrame(card_frame, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=10)

            indicator = ctk.CTkLabel(inner, text="\u2713", font=("Consolas", 14, "bold"),
                                     text_color=T.GREEN, width=24)
            indicator.pack(side="left")

            info_frame = ctk.CTkFrame(inner, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True)

            name_label = ctk.CTkLabel(info_frame, text=pname, font=T.FONT_BOLD,
                                       text_color=T.FG, anchor="w")
            name_label.pack(fill="x")

            p = PLATFORMS[pname]
            rate_text = f"{p.rate_limit_per_sec} req/s | max {p.max_concurrent}"
            rate_label = ctk.CTkLabel(info_frame, text=rate_text, font=T.FONT_MONO,
                                       text_color=T.FG2, anchor="w")
            rate_label.pack(fill="x")

            selected = ctk.BooleanVar(value=True)
            self.platform_cards[pname] = (card_frame, accent_bar, indicator, selected)

            toggle_cmd = lambda e, name=pname: self._toggle_platform(name)
            for widget in [card_frame, accent_bar, inner, indicator,
                           info_frame, name_label, rate_label]:
                widget.bind("<Button-1>", toggle_cmd)

    def _toggle_platform(self, name):
        card_frame, accent_bar, indicator, var = self.platform_cards[name]
        var.set(not var.get())
        if var.get():
            accent_bar.configure(fg_color=T.GREEN)
            indicator.configure(text_color=T.GREEN, text="\u2713")
            card_frame.configure(border_color=T.GREEN)
        else:
            accent_bar.configure(fg_color=T.BORDER)
            indicator.configure(text_color=T.FG3, text="")
            card_frame.configure(border_color=T.BORDER)

    def _select_all(self):
        for name in self.platform_cards:
            card_frame, accent_bar, indicator, var = self.platform_cards[name]
            var.set(True)
            accent_bar.configure(fg_color=T.GREEN)
            indicator.configure(text_color=T.GREEN, text="\u2713")
            card_frame.configure(border_color=T.GREEN)

    def _deselect_all(self):
        for name in self.platform_cards:
            card_frame, accent_bar, indicator, var = self.platform_cards[name]
            var.set(False)
            accent_bar.configure(fg_color=T.BORDER)
            indicator.configure(text_color=T.FG3, text="")
            card_frame.configure(border_color=T.BORDER)

    def get_selected(self):
        return {name for name, (_, _, _, var) in self.platform_cards.items() if var.get()}

    def show(self, parent):
        self.frame.pack(in_=parent, fill="both", expand=True)

    def hide(self):
        self.frame.pack_forget()
