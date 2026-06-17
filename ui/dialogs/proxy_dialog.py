
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

from ui import theme as T
from ui.widgets import SlideButton


class ProxyDialog:

    def __init__(self, app, on_result=None):
        self.app = app
        self.on_result = on_result
        self.dialog = None
        self._build()

    def _build(self):
        self.dialog = ctk.CTkToplevel(self.app.root)
        self.dialog.title("Proxy")
        self.dialog.geometry("400x260")
        self.dialog.configure(fg_color=T.BG_MAIN)
        self.dialog.transient(self.app.root)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        x = self.app.root.winfo_x() + (self.app.root.winfo_width() - 400) // 2
        y = self.app.root.winfo_y() + (self.app.root.winfo_height() - 260) // 2
        self.dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(self.dialog, text="Use proxies?", font=T.FONT_TITLE,
                     text_color=T.FG).pack(pady=(20, 4))
        ctk.CTkLabel(self.dialog, text="Auto-generate proxies + rotation server",
                     font=T.FONT, text_color=T.FG2).pack(pady=(0, 4))

        self.status_label = ctk.CTkLabel(self.dialog, text="", font=T.FONT_MONO,
                                         text_color=T.FG3)
        self.status_label.pack(pady=(4, 8))

        btn_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(btn_frame, text="Yes, use proxies", font=T.FONT_BOLD,
                      fg_color=T.GREEN, hover_color=T.GREEN_DIM,
                      text_color="#000000", width=140,
                      command=self._on_yes).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="No, direct", font=T.FONT_BOLD,
                      fg_color=T.RED, hover_color=T.RED_DIM,
                      text_color="#000000", width=140,
                      command=self._on_no).pack(side="left", padx=8)

    def _on_yes(self):
        from features.proxy.utils import random_ip, random_port, random_user, random_pass
        from features.proxy.server import RotationProxyServer

        self.status_label.configure(text="Generating proxies...", text_color=T.ORANGE)
        self.dialog.update()

        proxies = []
        for _ in range(20):
            ip = random_ip()
            port = random_port()
            user = random_user()
            pw = random_pass()
            proxies.append({
                "host": ip, "port": port,
                "user": user, "pass": pw
            })

        server_port = 8888
        server = RotationProxyServer(proxies, port=server_port)
        try:
            server.start()
            self.app._proxy_server = server
        except OSError as e:
            self.status_label.configure(text=f"Failed: {e}", text_color=T.RED)
            return

        proxy_url = f"http://127.0.0.1:{server_port}"

        settings = self.app.pages.get("settings")
        if settings:
            settings.proxy_entry.delete(0, "end")
            settings.proxy_entry.insert(0, proxy_url)
            settings.proxy_status.configure(
                text=f"20 proxies active on :{server_port}",
                text_color=T.GREEN
            )

        self.status_label.configure(
            text=f"\u2713 Server running on :{server_port}",
            text_color=T.GREEN
        )
        self.dialog.after(600, self.dialog.destroy)

        if self.on_result:
            self.on_result(proxy_url)

    def _on_no(self):
        self.dialog.destroy()
        if self.on_result:
            self.on_result(None)

    def show(self):
        self.dialog.wait_window()
