
from core.display import C


def prompt():
    try:
        return input(f"\n  {C.DK_MAG}{C.BOLD}>>{C.RESET} ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return ""


def safe_input(label):
    try:
        return input(f"  {C.DK_MAG}{C.BOLD}>{C.RESET} {label}").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return ""


def press_enter():
    try:
        input(f"\n  {C.DK_MAG}{C.DIM}[ Enter ]{C.RESET}")
    except (KeyboardInterrupt, EOFError):
        print()
