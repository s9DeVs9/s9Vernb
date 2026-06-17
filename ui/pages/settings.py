
import customtkinter as ctk
import tkinter as tk

from ui import theme as T
from ui.widgets import Card, SlideButton


class SettingsPage:

    def __init__(self, app):
        self.app = app
        self.frame = None
        self._build()

    def _build(self):
        self.frame = ctk.CTkFrame(self.app.page_container, fg_color=T.BG_MAIN)

        net_card = Card(self.frame, title="NETWORK")
        net_card.pack(fill="x", pady=(0, 10))

        row = ctk.CTkFrame(net_card, fg_color="transparent")
        row.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(row, text="Proxy:", font=T.FONT,
                     text_color=T.FG2).pack(side="left", padx=(0, 8))

        self.proxy_entry = ctk.CTkEntry(row, font=T.FONT_MONO,
                                         fg_color=T.INPUT_BG, text_color=T.FG,
                                         border_color=T.INPUT_BORDER,
                                         placeholder_text="socks5://host:port",
                                         placeholder_text_color=T.FG3,
                                         width=320)
        self.proxy_entry.pack(side="left")

        ctk.CTkLabel(row, text="(socks5://host:port or http://host:port)",
                     font=T.FONT_MONO, text_color=T.FG3).pack(side="left", padx=(12, 0))

        perf_card = Card(self.frame, title="PERFORMANCE")
        perf_card.pack(fill="x", pady=(0, 10))

        row2 = ctk.CTkFrame(perf_card, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(row2, text="Concurrency:", font=T.FONT,
                     text_color=T.FG2).pack(side="left", padx=(0, 8))
        self.concurrency_spin = ctk.CTkSlider(row2, from_=1, to=50,
                                               number_of_steps=49,
                                               progress_color=T.ACCENT,
                                               button_color=T.ACCENT,
                                               button_hover_color=T.ACCENT_HOVER,
                                               fg_color=T.INPUT_BORDER,
                                               width=160)
        self.concurrency_spin.set(10)
        self.concurrency_spin.pack(side="left", padx=(0, 8))

        self.concurrency_label = ctk.CTkLabel(row2, text="10", font=T.FONT_MONO,
                                               text_color=T.FG, width=30)
        self.concurrency_label.pack(side="left", padx=(0, 24))

        ctk.CTkLabel(row2, text="Delay (s):", font=T.FONT,
                     text_color=T.FG2).pack(side="left", padx=(0, 8))
        self.delay_spin = ctk.CTkSlider(row2, from_=0.0, to=5.0,
                                         number_of_steps=50,
                                         progress_color=T.ACCENT,
                                         button_color=T.ACCENT,
                                         button_hover_color=T.ACCENT_HOVER,
                                         fg_color=T.INPUT_BORDER,
                                         width=160)
        self.delay_spin.set(0.3)
        self.delay_spin.pack(side="left", padx=(0, 8))

        self.delay_label = ctk.CTkLabel(row2, text="0.3", font=T.FONT_MONO,
                                         text_color=T.FG, width=30)
        self.delay_label.pack(side="left")

        self.concurrency_spin.configure(command=self._on_concurrency_change)
        self.delay_spin.configure(command=self._on_delay_change)

        behavior_card = Card(self.frame, title="BEHAVIOR")
        behavior_card.pack(fill="x", pady=(0, 10))

        row3 = ctk.CTkFrame(behavior_card, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 4))

        self.ignore_timeout_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(row3, text="Ignore timeouts (treat timeout as error instead)",
                      variable=self.ignore_timeout_var, font=T.FONT,
                      text_color=T.FG, progress_color=T.ACCENT,
                      button_color=T.FG, button_hover_color=T.ACCENT_HOVER,
                      fg_color=T.INPUT_BORDER).pack(side="left")

        proxy_card = Card(self.frame, title="PROXY ROTATION")
        proxy_card.pack(fill="x", pady=(0, 10))

        proxy_info = ctk.CTkFrame(proxy_card, fg_color="transparent")
        proxy_info.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(proxy_info, text="Auto-generate proxies + rotation server",
                     font=T.FONT, text_color=T.FG2).pack(side="left")

        SlideButton(proxy_info, "Generate Proxies", command=self._open_proxy_generator,
                    color=T.PURPLE, width=160).pack(side="right")

        self.proxy_status = ctk.CTkLabel(proxy_card, text="No proxies configured",
                                          font=T.FONT_MONO, text_color=T.FG3, anchor="w")
        self.proxy_status.pack(fill="x")

    def _on_concurrency_change(self, value):
        self.concurrency_label.configure(text=str(int(value)))

    def _on_delay_change(self, value):
        self.delay_label.configure(text=f"{value:.1f}")

    def _open_proxy_generator(self):
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title("Proxy Generator")
        dialog.geometry("400x320")
        dialog.configure(fg_color=T.BG_MAIN)
        dialog.transient(self.frame.winfo_toplevel())
        dialog.grab_set()
        dialog.resizable(False, False)

        ctk.CTkLabel(dialog, text="Generate Proxies", font=T.FONT_TITLE,
                     text_color=T.FG).pack(pady=(20, 12))

        type_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        type_frame.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(type_frame, text="Type:", font=T.FONT,
                     text_color=T.FG2).pack(side="left", padx=(0, 8))
        proxy_type = ctk.CTkOptionMenu(type_frame, values=["SOCKS5", "HTTP", "Mixed"],
                                        fg_color=T.INPUT_BG, button_color=T.ACCENT,
                                        button_hover_color=T.ACCENT_HOVER,
                                        dropdown_fg_color=T.BG_CARD,
                                        font=T.FONT, width=140)
        proxy_type.set("SOCKS5")
        proxy_type.pack(side="left")

        count_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        count_frame.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(count_frame, text="Count:", font=T.FONT,
                     text_color=T.FG2).pack(side="left", padx=(0, 8))
        count_entry = ctk.CTkEntry(count_frame, font=T.FONT_MONO,
                                    fg_color=T.INPUT_BG, text_color=T.FG,
                                    border_color=T.INPUT_BORDER, width=80)
        count_entry.insert(0, "20")
        count_entry.pack(side="left")

        status_label = ctk.CTkLabel(dialog, text="", font=T.FONT_MONO,
                                     text_color=T.FG2)
        status_label.pack(pady=(8, 4))

        def generate():
            from features.proxy.utils import random_ip, random_port, random_user, random_pass
            _random_ip = random_ip
            _random_port = random_port
            _random_user = random_user
            _random_pass = random_pass
            import random

            count_str = count_entry.get().strip()
            count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 20
            ptype = proxy_type.get()

            proxies = []
            for _ in range(count):
                ip = _random_ip()
                port = _random_port()
                if ptype == "SOCKS5":
                    user = _random_user()
                    pw = _random_pass()
                    proxies.append(f"{ip}:{port}:{user}:{pw}")
                elif ptype == "HTTP":
                    proxies.append(f"{ip}:{port}")
                else:
                    fmt = random.choice(["socks5", "http", "bare"])
                    if fmt == "socks5":
                        proxies.append(f"socks5://{_random_user()}:{_random_pass()}@{ip}:{port}")
                    elif fmt == "http":
                        proxies.append(f"http://{ip}:{port}")
                    else:
                        proxies.append(f"{ip}:{port}")

            filepath = f"generated_{ptype.lower()}_proxies.txt"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(proxies) + "\n")

            status_label.configure(text=f"\u2713 Generated {count} {ptype} proxies -> {filepath}",
                                    text_color=T.GREEN)
            self.proxy_status.configure(
                text=f"{count} {ptype} proxies ready ({filepath})",
                text_color=T.GREEN
            )

        SlideButton(dialog, "Generate", command=generate,
                    color=T.GREEN, width=120).pack(pady=(8, 4))

    def get_proxy(self):
        val = self.proxy_entry.get().strip()
        return val if val else None

    def get_concurrency(self):
        try:
            val = int(self.concurrency_spin.get())
            return max(1, min(50, val))
        except (ValueError, TypeError):
            return 10

    def get_delay(self):
        try:
            val = float(self.delay_spin.get())
            return max(0.0, min(5.0, val))
        except (ValueError, TypeError):
            return 0.3

    def get_ignore_timeouts(self):
        return self.ignore_timeout_var.get()

    def show(self, parent):
        self.frame.pack(in_=parent, fill="both", expand=True)

    def hide(self):
        self.frame.pack_forget()
