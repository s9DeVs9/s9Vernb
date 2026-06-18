
import customtkinter as ctk
import tkinter as tk
from ui import theme as T


class Card(ctk.CTkFrame):

    def __init__(self, parent, title=None, border_color=None, **kw):
        super().__init__(parent, fg_color=T.BG_CARD,
                         border_color=border_color or T.BORDER,
                         border_width=T.CARD_BORDER_WIDTH,
                         corner_radius=T.CARD_CORNER_RADIUS, **kw)
        if title:
            bar = ctk.CTkFrame(self, fg_color=border_color or T.ACCENT,
                               height=2, corner_radius=1)
            bar.pack(fill="x", padx=T.CARD_PAD_X, pady=(T.CARD_PAD_Y, 4))
            ctk.CTkLabel(self, text=f"  {title}", font=T.FONT_SUB,
                         text_color=T.FG2, anchor="w").pack(
                             fill="x", padx=T.CARD_PAD_X, pady=(2, 4))


class StatCard(ctk.CTkFrame):

    def __init__(self, parent, label, value="0", color=T.ACCENT, **kw):
        super().__init__(parent, fg_color=T.BG_CARD,
                         border_color=color, border_width=2,
                         corner_radius=T.CARD_CORNER_RADIUS, **kw)
        ctk.CTkLabel(self, text=label, font=T.FONT_STAT_LABEL,
                     text_color=T.FG2).pack(pady=(8, 0))
        self.val_label = ctk.CTkLabel(self, text=value, font=T.FONT_STAT,
                                       text_color=color)
        self.val_label.pack(pady=(2, 8))

    def set_value(self, value):
        self.val_label.configure(text=str(value))


class SlideButton(ctk.CTkFrame):

    def __init__(self, parent, text, command=None, color=T.ACCENT,
                 hover_color=None, width=140, height=32, bold=False, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._command = command
        self._color = color
        self._hover_color = hover_color or T.ACCENT_HOVER
        self._enabled = True
        self._slide_pos = 0
        self._anim_id = None

        self.configure(width=width, height=height)
        self.pack_propagate(False)

        self._canvas = tk.Canvas(self, bg=T.BG_CARD, highlightthickness=0,
                                  bd=0, width=width, height=height)
        self._canvas.pack(fill="both", expand=True)

        font = T.FONT_BOLD if bold else T.FONT
        self._text_id = self._canvas.create_text(
            width // 2, height // 2, text=text, font=font,
            fill=color, anchor="center"
        )

        self._canvas.bind("<Enter>", self._on_enter)
        self._canvas.bind("<Leave>", self._on_leave)
        self._canvas.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

        self._draw_bg()

    def _draw_bg(self):
        w = max(self._canvas.winfo_width(), 2)
        h = max(self._canvas.winfo_height(), 2)
        self._canvas.delete("bg")
        self._canvas.delete("slide")

        r = T.BUTTON_CORNER_RADIUS
        self._rounded_rect(0, 0, w, h, r, fill=T.BG_CARD,
                           outline=T.BORDER, tags="bg")

        if self._slide_pos > 0:
            slide_w = int(w * self._slide_pos / 100)
            if slide_w > 0:
                self._rounded_rect(0, 0, slide_w, h, r,
                                   fill=self._color, outline="", tags="slide")
                self._canvas.tag_lower("slide", "bg")
                self._canvas.tag_lower("bg")

        if self._slide_pos > 50:
            self._canvas.itemconfig(self._text_id, fill="#ffffff")
        else:
            self._canvas.itemconfig(self._text_id, fill=self._color)
        self._canvas.tag_raise(self._text_id)

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return self._canvas.create_polygon(points, smooth=True, **kw)

    def _on_enter(self, e):
        if self._enabled:
            self._canvas.configure(cursor="hand2")
            self._start_slide(100)

    def _on_leave(self, e):
        self._canvas.configure(cursor="")
        self._start_slide(0)

    def _on_click(self, e):
        if self._enabled and self._command:
            self._command()

    def _start_slide(self, target):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None
        self._animate_slide(target)

    def _animate_slide(self, target):
        try:
            diff = target - self._slide_pos
            if abs(diff) < 2:
                self._slide_pos = target
                self._draw_bg()
                return
            self._slide_pos += diff * 0.25
            self._draw_bg()
            self._anim_id = self.after(16, lambda: self._animate_slide(target))
        except tk.TclError:
            pass

    def disable(self):
        self._enabled = False
        self._canvas.itemconfig(self._text_id, fill=T.FG3)
        self._canvas.configure(cursor="")

    def enable(self):
        self._enabled = True
        self._canvas.itemconfig(self._text_id, fill=self._color)
        self._canvas.configure(cursor="hand2")


class SidebarButton(ctk.CTkFrame):

    def __init__(self, parent, icon, label="", command=None, **kw):
        super().__init__(parent, fg_color=T.BG_SIDEBAR, corner_radius=0, **kw)
        self._command = command
        self._active = False

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=4)

        self._icon_label = ctk.CTkLabel(inner, text=icon, font=T.FONT_SIDEBAR_ICON,
                                         text_color=T.FG2, width=30, anchor="w")
        self._icon_label.pack(side="left")

        self._text_label = ctk.CTkLabel(inner, text=label, font=T.FONT_SIDEBAR,
                                         text_color=T.FG2, anchor="w")
        self._text_label.pack(side="left", padx=(4, 0))

        self._indicator = ctk.CTkFrame(self, fg_color=T.BG_SIDEBAR,
                                        width=3, corner_radius=2)
        self._indicator.place(x=0, rely=0.1, relheight=0.8)

        self.bind("<Button-1>", self._on_click)
        inner.bind("<Button-1>", self._on_click)
        self._icon_label.bind("<Button-1>", self._on_click)
        self._text_label.bind("<Button-1>", self._on_click)

    def _on_click(self, e):
        if self._command:
            self._command()

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.configure(fg_color=T.BG_CARD)
            self._icon_label.configure(text_color=T.ACCENT)
            self._text_label.configure(text_color=T.FG)
            self._indicator.configure(fg_color=T.ACCENT)
        else:
            self.configure(fg_color=T.BG_SIDEBAR)
            self._icon_label.configure(text_color=T.FG2)
            self._text_label.configure(text_color=T.FG2)
            self._indicator.configure(fg_color=T.BG_SIDEBAR)
