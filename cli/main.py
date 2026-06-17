
import sys
import time

from core.platform_utils import setup_encoding, setup_console, clear_screen
from core.display import C, print_banner, print_menu, slow_type, type_line, type_text, BANNER_RAW
from cli.prompts import prompt

_first_run = True


def animated_startup():
    global _first_run
    clear_screen()

    slow_type(f"  {C.DK_MAG}S9Checker v2.0{C.RESET}", delay=0.01)
    time.sleep(0.05)
    type_line(f"  {C.GRAY}Initializing modules...{C.RESET}", delay=0.005)
    time.sleep(0.03)
    type_line(f"  {C.DK_CYN}>> Ready{C.RESET}", delay=0.008)
    time.sleep(0.1)
    clear_screen()

    for line in BANNER_RAW.split("\n"):
        if line.strip():
            type_text(f"{C.DK_MAG}{C.BOLD}{line}{C.RESET}", delay=0.003, end="\n")
            time.sleep(0.015)
        else:
            print()
    type_line(f"{C.GRAY}{C.DIM}                    v2.0{C.RESET}", delay=0.005)
    type_line(f"{C.DK_MAG}{'─' * 50}{C.RESET}", delay=0.002)
    time.sleep(0.05)

    from core.display import MENU_PAGE1
    print()
    for raw in MENU_PAGE1:
        line = raw.format(cyan=C.DK_CYN, bold=C.BOLD, reset=C.RESET)
        type_text(line, delay=0.003, end="\n")
        time.sleep(0.02)
    nav = f"\n  {C.DK_CYN}{C.BOLD}[N]{C.RESET} Next page    {C.DK_CYN}{C.BOLD}[0]{C.RESET} Exit"
    type_text(nav, delay=0.003, end="\n")
    print()

    _first_run = False


def option_about():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}ABOUT S9CHECKER{C.RESET}", delay=0.02)
    from core.display import SEPARATOR
    print(SEPARATOR)
    print()
    type_line(f"  {C.GRAY}S9Checker v2.0 — Multi-Platform Security Tool{C.RESET}", delay=0.01)
    print()
    print(f"  {C.DK_CYN}Discord:{C.RESET}  {C.DK_MAG}s9._.{C.RESET}")
    print(f"  {C.DK_CYN}GitHub:{C.RESET}   {C.DK_MAG}s9DeVs9{C.RESET}")
    print()
    print(f"  {C.GRAY}Built for authorized security testing only.{C.RESET}")
    print(f"  {C.GRAY}Unauthorized access to computer systems is illegal.{C.RESET}")
    from cli.prompts import press_enter
    press_enter()


def run_cli():
    global _first_run
    current_page = 1

    setup_encoding()
    setup_console()

    try:
        while True:
            if _first_run:
                animated_startup()
            else:
                clear_screen()
                print_banner()
                print_menu(current_page)

            choice = prompt()

            if choice.lower() == "n" and current_page < 5:
                current_page += 1
                continue
            elif choice.lower() == "b" and current_page > 1:
                current_page -= 1
                continue

            if current_page == 1:
                if choice == "1":
                    from cli.handlers.core import option_launch_gui
                    option_launch_gui()
                elif choice == "2":
                    from cli.handlers.core import option_manage_combolists
                    option_manage_combolists()
                elif choice == "3":
                    from cli.handlers.core import option_quick_check
                    option_quick_check()
                elif choice == "4":
                    from cli.handlers.core import option_view_results
                    option_view_results()
                elif choice == "5":
                    from cli.handlers.core import option_settings
                    option_settings()
                elif choice == "6":
                    from cli.handlers.proxy import option_proxy_generator
                    option_proxy_generator()
                elif choice == "7":
                    from cli.handlers.discord import option_nitro_generator
                    option_nitro_generator()
                elif choice == "8":
                    from cli.handlers.discord import option_boost_generator
                    option_boost_generator()
                elif choice == "9":
                    from cli.handlers.discord import option_promo_generator
                    option_promo_generator()
                elif choice == "10":
                    from cli.handlers.scraper import option_web_scraper
                    option_web_scraper()
                elif choice == "0":
                    type_line(f"\n  {C.DK_MAG}Goodbye!{C.RESET}", delay=0.04)
                    break
                else:
                    type_line(f"  {C.DK_RED}Invalid option. Try again.{C.RESET}")
                    time.sleep(0.8)

            elif current_page == 2:
                if choice == "11":
                    from cli.handlers.shell import option_reverse_shell
                    option_reverse_shell()
                elif choice == "12":
                    from features.osint.nmap import NmapWrapper
                    from cli.handlers.osint import option_osint_tool
                    option_osint_tool(NmapWrapper, "nmap")
                elif choice == "13":
                    from features.osint.masscan import MasscanWrapper
                    from cli.handlers.osint import option_osint_tool
                    option_osint_tool(MasscanWrapper, "masscan")
                elif choice == "14":
                    from features.osint.rustscan import RustscanWrapper
                    from cli.handlers.osint import option_osint_tool
                    option_osint_tool(RustscanWrapper, "rustscan")
                elif choice == "15":
                    from features.osint.amass import AmassWrapper
                    from cli.handlers.osint import option_osint_tool
                    option_osint_tool(AmassWrapper, "amass")
                elif choice == "16":
                    from features.osint.subfinder import SubfinderWrapper
                    from cli.handlers.osint import option_osint_tool
                    option_osint_tool(SubfinderWrapper, "subfinder")
                elif choice == "17":
                    from features.osint.httpx import HttpxWrapper
                    from cli.handlers.osint import option_osint_tool
                    option_osint_tool(HttpxWrapper, "httpx")
                elif choice == "18":
                    from features.osint.theharvester import TheHarvesterWrapper
                    from cli.handlers.osint import option_osint_tool
                    option_osint_tool(TheHarvesterWrapper, "theHarvester")
                elif choice == "19":
                    from features.exploit.searchsploit import SearchsploitWrapper
                    from cli.handlers.exploit import option_exploit_tool
                    option_exploit_tool(SearchsploitWrapper, "searchsploit")
                elif choice == "20":
                    from features.exploit.metasploit import MetasploitWrapper
                    from cli.handlers.exploit import option_exploit_tool
                    option_exploit_tool(MetasploitWrapper, "metasploit")
                elif choice == "0":
                    type_line(f"\n  {C.DK_MAG}Goodbye!{C.RESET}", delay=0.04)
                    break
                else:
                    type_line(f"  {C.DK_RED}Invalid option. Try again.{C.RESET}")
                    time.sleep(0.8)

            elif current_page == 3:
                if choice == "21":
                    from features.exploit.impacket import ImpacketWrapper
                    from cli.handlers.exploit import option_exploit_tool
                    option_exploit_tool(ImpacketWrapper, "impacket-secretsdump")
                elif choice == "22":
                    from features.exploit.responder import ResponderWrapper
                    from cli.handlers.exploit import option_exploit_tool
                    option_exploit_tool(ResponderWrapper, "responder")
                elif choice == "23":
                    from features.exploit.crackmapexec import CrackMapExecWrapper
                    from cli.handlers.exploit import option_exploit_tool
                    option_exploit_tool(CrackMapExecWrapper, "crackmapexec")
                elif choice == "24":
                    from features.exploit.bloodhound import BloodhoundWrapper
                    from cli.handlers.exploit import option_exploit_tool
                    option_exploit_tool(BloodhoundWrapper, "bloodhound")
                elif choice == "25":
                    from features.exploit.mimikatz import MimikatzWrapper
                    from cli.handlers.exploit import option_exploit_tool
                    option_exploit_tool(MimikatzWrapper, "mimikatz")
                elif choice == "26":
                    from features.exploit.hashcat import HashcatWrapper
                    from cli.handlers.exploit import option_exploit_tool
                    option_exploit_tool(HashcatWrapper, "hashcat")
                elif choice == "27":
                    from features.exploit.john import JohnWrapper
                    from cli.handlers.exploit import option_exploit_tool
                    option_exploit_tool(JohnWrapper, "john")
                elif choice == "28":
                    from features.exploit.hydra import HydraWrapper
                    from cli.handlers.exploit import option_exploit_tool
                    option_exploit_tool(HydraWrapper, "hydra")
                elif choice == "29":
                    from features.reverse_engineering.ghidra import GhidraWrapper
                    from cli.handlers.re import option_re_tool
                    option_re_tool(GhidraWrapper, "ghidra")
                elif choice == "30":
                    from features.reverse_engineering.radare2 import Radare2Wrapper
                    from cli.handlers.re import option_re_tool
                    option_re_tool(Radare2Wrapper, "radare2")
                elif choice == "0":
                    type_line(f"\n  {C.DK_MAG}Goodbye!{C.RESET}", delay=0.04)
                    break
                else:
                    type_line(f"  {C.DK_RED}Invalid option. Try again.{C.RESET}")
                    time.sleep(0.8)

            elif current_page == 4:
                if choice == "31":
                    from features.reverse_engineering.pwndbg import PwndbgWrapper
                    from cli.handlers.re import option_re_tool
                    option_re_tool(PwndbgWrapper, "gdb+pwndbg")
                elif choice == "32":
                    from features.reverse_engineering.binwalk import BinwalkWrapper
                    from cli.handlers.re import option_re_tool
                    option_re_tool(BinwalkWrapper, "binwalk")
                elif choice == "33":
                    from features.reverse_engineering.pwntools import PwntoolsWrapper
                    from cli.handlers.re import option_re_tool
                    option_re_tool(PwntoolsWrapper, "pwntools")
                elif choice.lower() == "a":
                    option_about()
                elif choice == "0":
                    type_line(f"\n  {C.DK_MAG}Goodbye!{C.RESET}", delay=0.04)
                    break
                else:
                    type_line(f"  {C.DK_RED}Invalid option. Try again.{C.RESET}")
                    time.sleep(0.8)

            elif current_page == 5:
                if choice == "34":
                    from cli.handlers.credential import option_password_generator
                    option_password_generator()
                elif choice == "35":
                    from cli.handlers.credential import option_wordlist_generator
                    option_wordlist_generator()
                elif choice == "36":
                    from cli.handlers.credential import option_combolist_marketplace
                    option_combolist_marketplace()
                elif choice == "37":
                    from cli.handlers.security import option_ip_geoloc
                    option_ip_geoloc()
                elif choice == "38":
                    from cli.handlers.security import option_email_osint
                    option_email_osint()
                elif choice == "39":
                    from cli.handlers.security import option_account_enum
                    option_account_enum()
                elif choice == "40":
                    from cli.handlers.security import option_nuclei_scan
                    option_nuclei_scan()
                elif choice == "41":
                    from cli.handlers.security import option_payload_tester
                    option_payload_tester()
                elif choice == "42":
                    from cli.handlers.security import option_session_validator
                    option_session_validator()
                elif choice == "43":
                    from cli.handlers.security import option_token_generator
                    option_token_generator()
                elif choice == "44":
                    from cli.handlers.automation import option_proxy_scraper
                    option_proxy_scraper()
                elif choice == "45":
                    from cli.handlers.automation import option_batch_runner
                    option_batch_runner()
                elif choice == "46":
                    from cli.handlers.rat import option_rat
                    option_rat()
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
