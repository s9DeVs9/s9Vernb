
import os
import sys
import asyncio

from core.display import C, type_line, SEPARATOR
from core.platform_utils import clear_screen
from cli.prompts import safe_input, press_enter
from core.config import RESULTS_DIR
from core.utils import parse_combolist, load_proxies


def option_launch_gui():
    type_line(f"\n  {C.DK_CYN}Initializing GUI...{C.RESET}", delay=0.03)
    try:
        from ui.app import App
        import customtkinter as ctk
        import tkinter as tk
        root = ctk.CTk()
        app = App(root)
        root.protocol("WM_DELETE_WINDOW", app._on_close)
        root.mainloop()
    except KeyboardInterrupt:
        type_line(f"\n  {C.DK_YEL}GUI interrupted.{C.RESET}")
    except tk.TclError:
        pass
    except Exception as e:
        type_line(f"  {C.DK_RED}Error: {e}{C.RESET}")


def option_manage_combolists():
    from core.display import print_banner
    from core.platform_utils import clear_screen
    from features.combolist.service import ComboList
    from features.combolist.utils import scan_combolists
    from core.config import COMBOLIST_DIR
    from cli.prompts import prompt
    import os

    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}COMBOLIST MANAGER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

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


def option_quick_check():
    from core.display import print_banner
    from core.platform_utils import clear_screen
    from core.platforms import PLATFORMS
    from features.combolist.service import ComboList
    from cli.prompts import prompt

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

    from core.checker import CredentialChecker
    from core.results import ResultsManager

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


def option_view_results():
    from core.display import print_banner
    from core.platform_utils import clear_screen

    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}RESULTS{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    import os
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


def option_settings():
    from core.display import print_banner
    from core.platform_utils import clear_screen

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
