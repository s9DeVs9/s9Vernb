"""
Main application window for S9Checker.
Glass effect: blurred desktop background with dark overlay panels.
Custom titlebar with Alt+Tab support via Windows API.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import asyncio
import threading
import time
import os
import sys
import logging
import platform as _platform

from core import (
    PLATFORMS, CredentialChecker, ResultsManager,
    parse_combolist, load_proxies, ResultStatus
)
from ui import theme as T
from ui.glass import capture_desktop_blur
from ui.widgets import SidebarButton, AccentButton

logger = logging.getLogger("S9Checker")

# Windows API constants for Alt+Tab fix
GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000


def _fix_alt_tab(root):
    """Re-add window to taskbar/Alt+Tab after overrideredirect(True)."""
    if _platform.system() != "Windows":
        return
    try:
        import ctypes
        root.update_idletasks()
        # Get the HWND (window handle)
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        if not hwnd:
            return
        # Add WS_EX_APPWINDOW, remove WS_EX_TOOLWINDOW
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = style | WS_EX_APPWINDOW
        style = style & ~0x00000080  # Remove WS_EX_TOOLWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        # Force window to show in taskbar
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception as e:
        logger.debug(f"Alt+Tab fix skipped: {e}")


class App:
    """Main application window with glass background and page routing."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("S9Checker v2.0")
        self.root.geometry(f"{T.WINDOW_WIDTH}x{T.WINDOW_HEIGHT}")
        self.root.configure(bg="#000000")
        self.root.minsize(T.WINDOW_MIN_W, T.WINDOW_MIN_H)

        # Remove native titlebar for glass effect
        self.root.overrideredirect(True)

        # Center window on screen
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - T.WINDOW_WIDTH) // 2
        y = (sh - T.WINDOW_HEIGHT) // 2
        self.root.geometry(f"{T.WINDOW_WIDTH}x{T.WINDOW_HEIGHT}+{x}+{y}")

        # Fix Alt+Tab (must be after geometry set)
        _fix_alt_tab(self.root)

        # Application state
        self.combos = []
        self.combo_file = ""
        self.selected_platforms = set(PLATFORMS.keys())
        self.running = False
        self._checker = None
        self._results_mgr = None
        self._thread = None
        self._loop = None
        self._drag_data = {"x": 0, "y": 0}
        self._glass_img = None
        self.stats = {"completed": 0, "total": 0, "valid": 0, "invalid": 0,
                      "errors": 0, "speed": 0.0, "elapsed": 0.0, "percent": 0}

        # Capture desktop blur BEFORE showing
        self._glass_img = capture_desktop_blur(
            self.root, radius=T.GLASS_BLUR_RADIUS, tint=T.GLASS_TINT
        )

        # Build layout
        self._build_glass_background()
        self._build_titlebar()
        self._build_sidebar()
        self._build_content_area()

        # Set up async event loop
        self._loop = asyncio.new_event_loop()
        self._async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._async_thread.start()

        # Page routing
        self.pages = {}
        self.current_page = None
        self._register_pages()
        self.show_page("dashboard")

    # -------------------------------------------------------------------
    # Glass background
    # -------------------------------------------------------------------
    def _build_glass_background(self):
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        if self._glass_img:
            self.canvas.create_image(0, 0, image=self._glass_img, anchor="nw")

        self.canvas.create_rectangle(0, 0, 9999, 9999, fill="#000000",
                                     stipple="gray25", outline="")

    # -------------------------------------------------------------------
    # Custom titlebar
    # -------------------------------------------------------------------
    def _build_titlebar(self):
        self.titlebar = tk.Frame(self.canvas, bg=T.BG_DARK, height=T.TITLEBAR_HEIGHT)
        self.canvas.create_window(
            0, 0, window=self.titlebar, anchor="nw",
            width=T.WINDOW_WIDTH, height=T.TITLEBAR_HEIGHT
        )

        tk.Label(self.titlebar, text="  S9Checker v2.0", font=T.FONT_BOLD,
                 fg=T.FG2, bg=T.BG_DARK).pack(side="left")

        # Close
        close_btn = tk.Label(self.titlebar, text=" \u2715 ", font=T.FONT_BOLD,
                             fg=T.FG2, bg=T.BG_DARK, cursor="hand2", padx=8)
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self._on_close())
        close_btn.bind("<Enter>", lambda e: close_btn.configure(fg=T.RED, bg="#1a1a1a"))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(fg=T.FG2, bg=T.BG_DARK))

        # Minimize
        min_btn = tk.Label(self.titlebar, text=" \u2014 ", font=T.FONT_BOLD,
                           fg=T.FG2, bg=T.BG_DARK, cursor="hand2", padx=8)
        min_btn.pack(side="right")
        min_btn.bind("<Button-1>", lambda e: self._minimize())
        min_btn.bind("<Enter>", lambda e: min_btn.configure(fg=T.FG, bg="#1a1a1a"))
        min_btn.bind("<Leave>", lambda e: min_btn.configure(fg=T.FG2, bg=T.BG_DARK))

        # Drag
        self.titlebar.bind("<Button-1>", self._start_drag)
        self.titlebar.bind("<B1-Motion>", self._on_drag)

    def _start_drag(self, e):
        self._drag_data["x"] = e.x_root - self.root.winfo_x()
        self._drag_data["y"] = e.y_root - self.root.winfo_y()

    def _on_drag(self, e):
        x = e.x_root - self._drag_data["x"]
        y = e.y_root - self._drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def _minimize(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.after(100, self._restore_override)

    def _restore_override(self):
        def on_map(e):
            self.root.overrideredirect(True)
            self.root.after(10, lambda: _fix_alt_tab(self.root))
            self.root.unbind("<Map>")
        self.root.bind("<Map>", on_map)

    # -------------------------------------------------------------------
    # Sidebar
    # -------------------------------------------------------------------
    def _build_sidebar(self):
        self.sidebar = tk.Frame(self.canvas, bg=T.BG_DARK, width=T.SIDEBAR_WIDTH)
        self.canvas.create_window(
            0, T.TITLEBAR_HEIGHT, window=self.sidebar, anchor="nw",
            width=T.SIDEBAR_WIDTH, height=T.WINDOW_HEIGHT - T.TITLEBAR_HEIGHT
        )

        tk.Label(self.sidebar, text="CC", font=("Consolas", 12, "bold"),
                 fg=T.ACCENT, bg=T.BG_DARK, pady=12).pack()
        tk.Frame(self.sidebar, bg=T.BORDER, height=1).pack(fill="x", padx=10, pady=4)

        self.sidebar_buttons = {}
        nav_items = [
            ("dashboard", "\u25a3", "Dashboard"),
            ("combos",    "\u2630", "Combos"),
            ("platforms", "\u25a2", "Platforms"),
            ("settings",  "\u2699", "Settings"),
            ("results",   "\u25b6", "Results"),
        ]

        for page_name, icon, tooltip in nav_items:
            btn = SidebarButton(self.sidebar, icon, tooltip,
                                command=lambda p=page_name: self.show_page(p))
            btn.pack(fill="x", pady=2)
            self.sidebar_buttons[page_name] = btn

    # -------------------------------------------------------------------
    # Content area
    # -------------------------------------------------------------------
    def _build_content_area(self):
        content_w = T.WINDOW_WIDTH - T.SIDEBAR_WIDTH
        content_h = T.WINDOW_HEIGHT - T.TITLEBAR_HEIGHT

        self.content_frame = tk.Frame(self.canvas, bg=T.BG_MAIN)
        self.canvas.create_window(
            T.SIDEBAR_WIDTH, T.TITLEBAR_HEIGHT, window=self.content_frame,
            anchor="nw", width=content_w, height=content_h
        )

        self.header_frame = tk.Frame(self.content_frame, bg=T.BG_MAIN, height=44)
        self.header_frame.pack(fill="x", padx=20, pady=(10, 6))
        self.header_frame.pack_propagate(False)

        self.header_title = tk.Label(self.header_frame, text="Dashboard",
                                     font=T.FONT_TITLE, fg=T.FG, bg=T.BG_MAIN)
        self.header_title.pack(side="left")

        tk.Frame(self.content_frame, bg=T.BORDER, height=1).pack(fill="x", padx=20)

        self.page_container = tk.Frame(self.content_frame, bg=T.BG_MAIN)
        self.page_container.pack(fill="both", expand=True, padx=20, pady=12)

    # -------------------------------------------------------------------
    # Page routing
    # -------------------------------------------------------------------
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
        self.header_title.config(text=titles.get(name, name))

    # -------------------------------------------------------------------
    # Async event loop
    # -------------------------------------------------------------------
    def _run_async_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _async_progress_callback(self, info: dict):
        self.stats.update(info)
        self.root.after(0, lambda i=info: self._on_progress(i))

    def _on_progress(self, info):
        if "dashboard" in self.pages:
            self.pages["dashboard"].update_progress(info)

    # -------------------------------------------------------------------
    # Test control
    # -------------------------------------------------------------------
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
            self.pages["dashboard"].log(f"\u25b6 Starting: {len(self.combos)} combos x "
                                        f"{len(self.selected_platforms)} platforms = {total} requests")

        self._thread = threading.Thread(target=self._run_async_test, daemon=True)
        self._thread.start()

    def _run_async_test(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self._checker.run_test(self.combos, list(self.selected_platforms))
            )
        except Exception as e:
            logger.error(f"Test error: {e}")
            self.root.after(0, lambda e=e: self._log_error(str(e)))
        finally:
            self.root.after(0, self._on_test_complete)

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
                messagebox.showerror("Error", f"Cannot load file: {e}")
            except (KeyboardInterrupt, tk.TclError):
                pass
            self.combos = []

    def _on_close(self):
        if self.running:
            try:
                if not messagebox.askyesno("Confirm", "A test is running. Quit anyway?"):
                    return
            except (KeyboardInterrupt, tk.TclError):
                pass
            self._checker.stop()
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        self.root.quit()
        self.root.after(100, self.root.destroy)
