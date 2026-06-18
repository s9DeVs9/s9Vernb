
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog

from ui import theme as T
from ui.widgets import SlideButton


class ProxyDialog:

    def __init__(self, app, on_result=None):
        self.app = app
        self.on_result = on_result
        self.dialog = None
        self._proxy_file = None
        self._proxy_count = 0
        self._build()

    def _build(self):
        self.dialog = ctk.CTkToplevel(self.app.root)
        self.dialog.title("Proxy")
        self.dialog.geometry("420x320")
        self.dialog.configure(fg_color=T.BG_MAIN)
        self.dialog.transient(self.app.root)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        x = self.app.root.winfo_x() + (self.app.root.winfo_width() - 420) // 2
        y = self.app.root.winfo_y() + (self.app.root.winfo_height() - 320) // 2
        self.dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(self.dialog, text="Proxy Setup", font=T.FONT_TITLE,
                     text_color=T.FG).pack(pady=(20, 4))
        ctk.CTkLabel(self.dialog, text="Load real proxies from a file\n"
                     "Format: host:port or host:port:user:pass or socks5://user:pass@host:port",
                     font=T.FONT, text_color=T.FG2, justify="center").pack(pady=(0, 8))

        file_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        file_frame.pack(fill="x", padx=20, pady=(0, 4))

        self.file_entry = ctk.CTkEntry(file_frame, font=T.FONT_MONO,
                                       fg_color=T.INPUT_BG, text_color=T.FG,
                                       border_color=T.INPUT_BORDER,
                                       placeholder_text="No file selected",
                                       placeholder_text_color=T.FG3)
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        SlideButton(file_frame, "Browse", command=self._browse_file,
                    color=T.ACCENT, width=80).pack(side="left")

        self.status_label = ctk.CTkLabel(self.dialog, text="", font=T.FONT_MONO,
                                         text_color=T.FG3)
        self.status_label.pack(pady=(4, 8))

        btn_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        btn_frame.pack()

        self.start_btn = SlideButton(btn_frame, "Start with proxies",
                                     command=self._on_start,
                                     color=T.GREEN, width=160, bold=True)
        self.start_btn.pack(side="left", padx=8)

        SlideButton(btn_frame, "No proxy (direct)", command=self._on_no,
                    color=T.RED, width=140).pack(side="left", padx=8)

    def _browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Select proxy list",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filepath:
            return

        from core.utils import parse_proxy_line
        proxies = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parsed = parse_proxy_line(line)
                    if parsed:
                        proxies.append(parsed)
        except Exception as e:
            self.status_label.configure(text=f"Error: {e}", text_color=T.RED)
            return

        self._proxy_file = filepath
        self._proxy_count = len(proxies)
        self._proxies = proxies

        import os
        filename = os.path.basename(filepath)
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, filepath)
        self.status_label.configure(
            text=f"{self._proxy_count} proxies loaded from {filename}",
            text_color=T.GREEN if self._proxy_count > 0 else T.RED
        )

    def _on_start(self):
        if not self._proxy_count or not hasattr(self, '_proxies'):
            self.status_label.configure(text="Load a proxy file first", text_color=T.RED)
            return

        from features.proxy.server import RotationProxyServer

        server_port = 8888
        server = RotationProxyServer(self._proxies, port=server_port)
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
                text=f"{self._proxy_count} proxies active on :{server_port}",
                text_color=T.GREEN
            )

        self.status_label.configure(
            text=f"Server running on :{server_port} ({self._proxy_count} proxies)",
            text_color=T.GREEN
        )
        self.dialog.after(400, self.dialog.destroy)

        if self.on_result:
            self.on_result(proxy_url)

    def _on_no(self):
        self.dialog.destroy()
        if self.on_result:
            self.on_result(None)

    def show(self):
        self.dialog.wait_window()
