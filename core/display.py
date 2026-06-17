
import sys
import time

from core.platform_utils import is_posix


if is_posix():
    class C:
        RESET   = "\033[0m"
        BOLD    = "\033[1m"
        DIM     = "\033[2m"
        ITALIC  = "\033[3m"
        UNDERL  = "\033[4m"

        BLACK   = "\033[30m"
        DK_RED  = "\033[31m"
        DK_MAG  = "\033[35m"
        DK_CYN  = "\033[36m"
        GRAY    = "\033[37m"

        RED     = "\033[91m"
        MAGENTA = "\033[95m"
        CYAN    = "\033[96m"
        WHITE   = "\033[97m"
        YELLOW  = "\033[93m"

        DK_YEL  = "\033[33m"
else:
    class C:
        RESET   = ""
        BOLD    = ""
        DIM     = ""
        ITALIC  = ""
        UNDERL  = ""

        BLACK   = ""
        DK_RED  = ""
        DK_MAG  = ""
        DK_CYN  = ""
        GRAY    = ""

        RED     = ""
        MAGENTA = ""
        CYAN    = ""
        WHITE   = ""
        YELLOW  = ""

        DK_YEL  = ""


def type_text(text, delay=0.005, end="\n"):
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


def type_line(text, delay=0.008):
    type_text(text, delay=delay, end="\n")


def slow_type(text, delay=0.06):
    type_text(text, delay=delay, end="\n")


BANNER_RAW = r"""
         __   __  __                        __
       /'_ `\/\ \/\ \                      /\ \
  ____/\ \L\ \ \ \ \ \     __   _ __    ___\ \ \____
 /',__\ \___, \ \ \ \ \  /'__`\/\`'__\/' _ `\ \ __`\
/\__, `\/__,/\ \ \ \_/ \/\  __/\ \ \/ /\ \/\ \ \ \L\ \
/\____/    \ \_\ `\___/\ \____\\ \_\ \ \_\ \_\ \_,__/
 \/___/      \/_/`\/__/  \/____/ \/_/  \/_/\/_/\/___/"""


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

MENU_PAGE5 = [
    "  {cyan}{bold}[34]{reset} Password Generator",
    "  {cyan}{bold}[35]{reset} Custom Wordlist Generator",
    "  {cyan}{bold}[36]{reset} Combolist Marketplace",
    "  {cyan}{bold}[37]{reset} IP Geolocation",
    "  {cyan}{bold}[38]{reset} Email OSINT",
    "  {cyan}{bold}[39]{reset} Account Enumeration",
    "  {cyan}{bold}[40]{reset} Nuclei Scanner",
    "  {cyan}{bold}[41]{reset} Payload Tester (XSS/SQLi)",
    "  {cyan}{bold}[42]{reset} Session Validator",
    "  {cyan}{bold}[43]{reset} Token Generator (JWT)",
    "  {cyan}{bold}[44]{reset} Proxy Scraper",
    "  {cyan}{bold}[45]{reset} Batch Runner",
    "  {cyan}{bold}[46]{reset} Remote Access Tool (RAT)",
]

SEPARATOR = f"{C.DK_MAG}{'─' * 50}{C.RESET}"


def fmt_banner():
    return (
        f"{C.DK_MAG}{C.BOLD}{BANNER_RAW}{C.RESET}\n"
        f"{C.GRAY}{C.DIM}                    v2.0{C.RESET}\n"
        f"{C.DK_MAG}{'─' * 50}{C.RESET}"
    )


def fmt_menu(page=1):
    pages = {1: MENU_PAGE1, 2: MENU_PAGE2, 3: MENU_PAGE3, 4: MENU_PAGE4, 5: MENU_PAGE5}
    items = pages.get(page, MENU_PAGE1)
    lines = []
    for raw in items:
        line = raw.format(
            cyan=C.DK_CYN, bold=C.BOLD, reset=C.RESET
        )
        lines.append(line)

    nav_parts = []
    if page > 1:
        nav_parts.append(f"{C.DK_CYN}{C.BOLD}[B]{C.RESET} Back")
    if page < 5:
        nav_parts.append(f"{C.DK_CYN}{C.BOLD}[N]{C.RESET} Next page")
    nav_parts.append(f"{C.DK_CYN}{C.BOLD}[0]{C.RESET} Exit")

    lines.append(f"\n  {'    '.join(nav_parts)}")

    return "\n".join(lines)


def print_banner():
    print(fmt_banner())


def print_menu(page=1):
    print()
    print(fmt_menu(page))
    print()
