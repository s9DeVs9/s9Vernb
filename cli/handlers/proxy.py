
import os
import sys
import asyncio
import random

from core.display import C, type_line, type_text, SEPARATOR, print_banner
from core.platform_utils import clear_screen
from cli.prompts import prompt, safe_input, press_enter
from features.proxy.utils import random_ip, random_port, random_user, random_pass


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
    print(f"  {C.DK_CYN}[6]{C.RESET} Start rotation proxy server")
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
    elif choice == "6":
        _start_proxy_rotation_server()
    else:
        type_line(f"  {C.DK_RED}Invalid option.{C.RESET}")
        press_enter()


def _gen_random_ips():
    count_str = safe_input(f"{C.GRAY}How many IPs? (default 20): {C.RESET}")
    count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 20

    type_line(f"\n  {C.GRAY}Generating {count} random IPs...{C.RESET}\n")

    ips = [random_ip() for _ in range(count)]
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
        ip = random_ip()
        port = random_port()
        user = random_user()
        pw = random_pass()
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
        ip = random_ip()
        port = random_port()
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
        ip = random_ip()
        port = random_port()
        fmt = random.choice(formats)

        if fmt == "socks5":
            user = random_user()
            pw = random_pass(8)
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

    from core.utils import load_proxies
    proxies = load_proxies(filepath)

    if not proxies:
        type_line(f"  {C.DK_RED}No valid proxies found.{C.RESET}")
        press_enter()
        return

    type_line(f"\n  {C.GRAY}Loaded {len(proxies)} valid proxies from {filepath}{C.RESET}")
    print(f"\n  {C.GRAY}Preview (first 5):{C.RESET}")
    for p in proxies[:5]:
        auth = f" {C.GRAY}{p['user']}:{p['pass']}{C.RESET}" if p.get("user") else ""
        print(f"    {C.DK_CYN}{p['host']}:{p['port']}{C.RESET}{auth}")

    press_enter()


def _start_proxy_rotation_server():
    from features.proxy.server import RotationProxyServer
    from core.utils import load_proxies

    filepath = safe_input(f"{C.GRAY}Proxy file path: {C.RESET}").strip().strip('"')
    if not filepath or not os.path.exists(filepath):
        type_line(f"  {C.DK_RED}File not found.{C.RESET}")
        press_enter()
        return

    proxies = load_proxies(filepath)

    if not proxies:
        type_line(f"  {C.DK_RED}No valid proxies found.{C.RESET}")
        press_enter()
        return

    port_str = safe_input(f"{C.GRAY}Local server port (default 8888): {C.RESET}")
    listen_port = int(port_str) if port_str.isdigit() and int(port_str) > 0 else 8888

    type_line(f"\n  {C.DK_CYN}Starting rotation proxy server...{C.RESET}")
    type_line(f"  {C.GRAY}Proxies loaded: {len(proxies)}{C.RESET}")
    type_line(f"  {C.GRAY}Listening on: 127.0.0.1:{listen_port}{C.RESET}")
    type_line(f"  {C.GRAY}Press Ctrl+C to stop{C.RESET}\n")

    server = RotationProxyServer(proxies, port=listen_port)
    try:
        server.start()
    except OSError as e:
        type_line(f"  {C.DK_RED}Failed to bind: {e}{C.RESET}")
        press_enter()
        return

    type_line(f"  {C.DK_CYN}Server running on 127.0.0.1:{listen_port}{C.RESET}")
    type_line(f"  {C.GRAY}Use this as your proxy: 127.0.0.1:{listen_port}{C.RESET}\n")

    import time
    import threading

    running = [True]

    def _status_printer():
        while running[0]:
            time.sleep(5)
            if running[0]:
                stats = server.stats
                print(f"  {C.GRAY}[stats] requests={stats['requests']} errors={stats['errors']}{C.RESET}")

    status_thread = threading.Thread(target=_status_printer, daemon=True)
    status_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        running[0] = False
        server.stop()
        stats = server.stats
        type_line(f"\n  {C.DK_MAG}Server stopped.{C.RESET}")
        type_line(f"  {C.GRAY}Total requests: {stats['requests']} | Errors: {stats['errors']}{C.RESET}")

    press_enter()
