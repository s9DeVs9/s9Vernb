
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import asyncio
import threading
import os
import logging
import queue

from core.platforms import PLATFORMS
from core.checker import CredentialChecker
from core.results import ResultsManager
from core.utils import parse_combolist
from ui import theme as T
from ui.widgets import SidebarButton

logger = logging.getLogger("S9Checker")


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
        self._closing = False
        self._poll_after_id = None
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
        if self._closing:
            return
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
        try:
            if not self._closing:
                self._poll_after_id = self.root.after(50, self._poll_ui_queue)
        except tk.TclError:
            pass

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

        def on_result(proxy_url):
            result["proxy"] = proxy_url

        from ui.dialogs.proxy_dialog import ProxyDialog
        dialog = ProxyDialog(self, on_result=on_result)
        dialog.show()
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
        if self._closing:
            return
        self._closing = True

        if self._proxy_server:
            self._proxy_server.stop()
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self.running:
            try:
                if messagebox.askokcancel("Quit", "A test is running. Quit anyway?"):
                    self.stop_test()
                else:
                    self._closing = False
                    return
            except (KeyboardInterrupt, tk.TclError):
                pass

        try:
            if hasattr(self, '_poll_after_id') and self._poll_after_id:
                self.root.after_cancel(self._poll_after_id)
        except tk.TclError:
            pass
        try:
            self.root.after_cancel("all")
        except tk.TclError:
            pass
        try:
            self.root.withdraw()
            self.root.destroy()
        except tk.TclError:
            pass
