
import os
import sys
import io


def setup_encoding():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def check_os() -> str:
    if os.name == "nt":
        return "windows"
    return "posix"


def is_windows() -> bool:
    return os.name == "nt"


def is_posix() -> bool:
    return os.name == "posix"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def setup_console():
    if is_windows():
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass
