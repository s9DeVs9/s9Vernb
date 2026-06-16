"""
Reusable custom widgets for S9Checker UI.
Minimal black & glass aesthetic.
"""

import tkinter as tk
from ui import theme as T


class Card(tk.Frame):
    """Card with dark background and subtle border."""

    def __init__(self, parent, title=None, border_color=None, **kw):
        super().__init__(parent, bg=T.BG_CARD, highlightbackground=border_color or T.BORDER,
                         highlightthickness=T.CARD_BORDER_WIDTH, bd=0, **kw)
        self.configure(padx=T.CARD_PAD_X, pady=T.CARD_PAD_Y)
        if title:
            bar = tk.Frame(self, bg=border_color or T.ACCENT, height=1)
            bar.pack(fill="x", pady=(0, 0))
            tk.Label(self, text=f"  {title}", font=T.FONT_SUB, fg=T.FG2,
                     bg=T.BG_CARD, anchor="w").pack(fill="x", pady=(4, 2))


class StatCard(tk.Frame):
    """Stat card with large number and colored top border."""

    def __init__(self, parent, label, value="0", color=T.ACCENT, **kw):
        super().__init__(parent, bg=T.BG_CARD, highlightbackground=color,
                         highlightthickness=2, bd=0, **kw)
        self.configure(pady=6, padx=8)
        tk.Label(self, text=label, font=T.FONT_STAT_LABEL, fg=T.FG2,
                 bg=T.BG_CARD).pack()
        self.val_label = tk.Label(self, text=value, font=T.FONT_STAT, fg=color,
                                   bg=T.BG_CARD)
        self.val_label.pack()

    def set_value(self, value):
        self.val_label.config(text=str(value))


class AccentButton(tk.Canvas):
    """Rounded button with hover effect using Canvas."""

    def __init__(self, parent, text, command=None, color=T.FG, bold=False, **kw):
        super().__init__(parent, bg=T.BG_MAIN, highlightthickness=0, bd=0, **kw)
        self._command = command
        self._color = color
        self._enabled = True
        self._hover = False
        self._corner = 4
        self.configure(height=28)

        self._text_id = self.create_text(0, 0, text=text,
                                          font=T.FONT_BOLD if bold else T.FONT,
                                          fill=color, anchor="center")

        self.bind("<Configure>", self._on_resize)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self):
        self.delete("bg")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return
        bg = T.BG_CARD_HOVER if self._hover else T.BG_CARD
        r = self._corner
        self._rounded_rect(1, 1, w - 2, h - 2, r, fill=bg, outline=T.BORDER, width=1, tag="bg")
        self.tag_lower("bg")
        self.coords(self._text_id, w // 2, h // 2)

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kw)

    def _on_resize(self, e):
        self._draw()

    def _on_enter(self, e):
        if self._enabled:
            self._hover = True
            self._draw()
            self.configure(cursor="hand2")

    def _on_leave(self, e):
        self._hover = False
        self._draw()

    def _on_click(self, e):
        if self._enabled and self._command:
            self._command()

    def disable(self):
        self._enabled = False
        self.itemconfig(self._text_id, fill=T.FG2)
        self.configure(cursor="")

    def enable(self):
        self._enabled = True
        self.itemconfig(self._text_id, fill=self._color)
        self.configure(cursor="hand2")


class SidebarButton(tk.Frame):
    """Icon button for the sidebar navigation with active indicator."""

    def __init__(self, parent, icon, tooltip="", command=None, **kw):
        super().__init__(parent, bg=T.BG_DARK, cursor="hand2", **kw)
        self._command = command
        self._active = False

        self._icon_label = tk.Label(self, text=icon, font=T.FONT_SIDEBAR,
                                    fg=T.FG2, bg=T.BG_DARK, width=2, pady=6)
        self._icon_label.pack()

        # Active indicator bar (white line on the left)
        self._indicator = tk.Frame(self, bg=T.BG_DARK, width=3)
        self._indicator.place(x=0, y=4, relheight=0.92)

        self.bind("<Button-1>", self._on_click)
        self._icon_label.bind("<Button-1>", self._on_click)

    def _on_click(self, e):
        if self._command:
            self._command()

    def set_active(self, active: bool):
        self._active = active
        if active:
            self._icon_label.configure(fg=T.ACCENT, bg=T.BG_CARD)
            self.configure(bg=T.BG_CARD)
            self._indicator.configure(bg=T.ACCENT)
        else:
            self._icon_label.configure(fg=T.FG2, bg=T.BG_DARK)
            self.configure(bg=T.BG_DARK)
            self._indicator.configure(bg=T.BG_DARK)
