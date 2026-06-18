
import asyncio
import os
from typing import Any, cast

from core.display import C, type_line, SEPARATOR, print_banner
from core.platform_utils import clear_screen
from cli.prompts import safe_input, press_enter


def option_ip_geoloc():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}IP GEOLOCATION{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.osint.ip_geoloc import IPGeolocator

    ip = safe_input(f"{C.GRAY}IP address: {C.RESET}").strip()
    if not ip:
        type_line(f"  {C.DK_RED}No IP provided.{C.RESET}")
        press_enter()
        return

    locator = IPGeolocator()
    type_line(f"\n  {C.GRAY}Looking up {ip}...{C.RESET}\n")

    result: dict[str, Any] = asyncio.run(locator.lookup(ip))

    if "error" in result:
        type_line(f"  {C.DK_RED}Error: {result['error']}{C.RESET}")
    else:
        print(f"  {C.DK_CYN}IP:{C.RESET}         {result.get('ip')}")
        print(f"  {C.DK_CYN}Country:{C.RESET}     {result.get('country')} ({result.get('country_code')})")
        print(f"  {C.DK_CYN}Region:{C.RESET}      {result.get('region')}")
        print(f"  {C.DK_CYN}City:{C.RESET}        {result.get('city')}")
        print(f"  {C.DK_CYN}ZIP:{C.RESET}         {result.get('zip')}")
        print(f"  {C.DK_CYN}Timezone:{C.RESET}   {result.get('timezone')}")
        print(f"  {C.DK_CYN}ISP:{C.RESET}        {result.get('isp')}")
        print(f"  {C.DK_CYN}Org:{C.RESET}        {result.get('org')}")
        print(f"  {C.DK_CYN}AS:{C.RESET}         {result.get('as')}")
        print(f"  {C.DK_CYN}Lat/Lon:{C.RESET}    {result.get('latitude')}, {result.get('longitude')}")
        print(f"  {C.DK_CYN}Mobile:{C.RESET}     {result.get('mobile')}")
        print(f"  {C.DK_CYN}Proxy:{C.RESET}      {result.get('proxy')}")
        print(f"  {C.DK_CYN}Hosting:{C.RESET}    {result.get('hosting')}")

    press_enter()


def option_email_osint():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}EMAIL OSINT{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.osint.email_osint import EmailOSINT

    email = safe_input(f"{C.GRAY}Target email: {C.RESET}").strip()
    if not email:
        type_line(f"  {C.DK_RED}No email provided.{C.RESET}")
        press_enter()
        return

    osint = EmailOSINT()
    type_line(f"\n  {C.GRAY}Searching for {email}...{C.RESET}\n")

    result: dict[str, Any] = asyncio.run(osint.full_lookup(email))

    print(f"  {C.DK_CYN}Email:{C.RESET} {result.get('email')}\n")
    for r in result.get("results", []):
        service = r.get("service", "?")
        if r.get("exists") or r.get("found") or r.get("breached"):
            print(f"  {C.CYAN}[+]{C.RESET} {service}: ", end="")
            if r.get("username"):
                print(f"Found - {r['username']} ({r.get('profile', '')})")
            elif r.get("breached"):
                print(f"Found in {r.get('breach_count', 0)} breaches")
                for b in r.get("breaches", [])[:5]:
                    print(f"      {C.DK_RED}- {b}{C.RESET}")
            elif r.get("url"):
                print(f"Found - {r['url']}")
            else:
                print("Found")
        else:
            print(f"  {C.GRAY}[-]{C.RESET} {service}: Not found")

    press_enter()


def option_account_enum():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}ACCOUNT ENUMERATION{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.osint.account_enum import AccountEnumerator
    from core.platforms import PLATFORMS

    email = safe_input(f"{C.GRAY}Target email: {C.RESET}").strip()
    if not email:
        type_line(f"  {C.DK_RED}No email provided.{C.RESET}")
        press_enter()
        return

    print(f"\n  {C.GRAY}Available platforms:{C.RESET}")
    names = sorted(PLATFORMS.keys())
    for i, name in enumerate(names[:15], 1):
        print(f"    {C.DK_CYN}[{i:2d}]{C.RESET} {name}")

    sel = safe_input(f"\n{C.GRAY}Platforms (comma-separated, or 'all'): {C.RESET}").strip()
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



def option_nuclei_scan():
    from cli.handlers.osint import option_osint_tool
    from features.security.nuclei import NucleiWrapper
    option_osint_tool(NucleiWrapper, "nuclei")


def option_apikey_scanner():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}API KEY LEAKS SCANNER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.security.apikey_scanner import APIKeyScanner

    print(f"  {C.DK_CYN}[1]{C.RESET} Scan a file")
    print(f"  {C.DK_CYN}[2]{C.RESET} Scan a directory")
    print(f"  {C.DK_CYN}[3]{C.RESET} Scan text input")
    print()
    choice = safe_input(f"{C.GRAY}Choice: {C.RESET}").strip()

    scanner = APIKeyScanner()

    if choice == "1":
        filepath = safe_input(f"{C.GRAY}File path: {C.RESET}").strip().strip('"')
        if not filepath or not os.path.exists(filepath):
            type_line(f"  {C.DK_RED}File not found.{C.RESET}")
            press_enter()
            return
        type_line(f"\n  {C.GRAY}Scanning {filepath}...{C.RESET}\n")
        findings = scanner.scan_file(filepath)
    elif choice == "2":
        dirpath = safe_input(f"{C.GRAY}Directory path: {C.RESET}").strip().strip('"')
        if not dirpath or not os.path.isdir(dirpath):
            type_line(f"  {C.DK_RED}Directory not found.{C.RESET}")
            press_enter()
            return
        type_line(f"\n  {C.GRAY}Scanning {dirpath}...{C.RESET}\n")
        findings = scanner.scan_directory(dirpath)
    elif choice == "3":
        type_line(f"\n  {C.GRAY}Paste text (empty line to finish):{C.RESET}")
        lines = []
        while True:
            line = safe_input("")
            if not line:
                break
            lines.append(line)
        text = "\n".join(lines)
        findings = scanner.scan_text(text)
    else:
        type_line(f"  {C.DK_RED}Invalid choice.{C.RESET}")
        press_enter()
        return

    if not findings:
        type_line(f"  {C.CYAN}No API keys or secrets found.{C.RESET}")
        press_enter()
        return

    critical = [f for f in findings if f["severity"] == "critical"]
    high = [f for f in findings if f["severity"] == "high"]
    medium = [f for f in findings if f["severity"] == "medium"]
    low = [f for f in findings if f["severity"] == "low"]

    print(f"  {C.DK_RED}{C.BOLD}Found {len(findings)} potential leaks:{C.RESET}")
    if critical:
        print(f"    {C.DK_RED}{len(critical)} CRITICAL{C.RESET}")
    if high:
        print(f"    {C.DK_YEL}{len(high)} HIGH{C.RESET}")
    if medium:
        print(f"    {C.DK_CYN}{len(medium)} MEDIUM{C.RESET}")
    if low:
        print(f"    {C.GRAY}{len(low)} LOW{C.RESET}")
    print()

    for f in findings[:30]:
        sev_color = (C.DK_RED if f["severity"] == "critical" else
                     C.DK_YEL if f["severity"] == "high" else
                     C.DK_CYN if f["severity"] == "medium" else C.GRAY)
        print(f"    {sev_color}[{f['severity'].upper()}]{C.RESET} {C.DK_CYN}{f['name']}{C.RESET}")
        print(f"      {C.GRAY}File: {f['file']}:{f['line']}{C.RESET}")
        print(f"      {C.GRAY}Value: {f['value']}{C.RESET}")

    if len(findings) > 30:
        print(f"\n    {C.GRAY}... and {len(findings) - 30} more{C.RESET}")

    save = safe_input(f"\n{C.GRAY}Save report to file? (y/n): {C.RESET}").lower()
    if save == "y":
        import json
        filepath = "apikey_leaks_report.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(findings, f, indent=2, ensure_ascii=False)
        type_line(f"  {C.DK_CYN}Report saved to {filepath}{C.RESET}")

    press_enter()


def option_link_tracker():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}LINK TRACKER / INFO HARVESTER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.security.link_tracker import LinkTracker

    print(f"  {C.GRAY}Generate tracking links that collect visitor information.{C.RESET}")
    print(f"  {C.GRAY}When a victim clicks the link, their data is captured.{C.RESET}")
    print()
    print(f"  {C.DK_CYN}[1]{C.RESET} Create a tracking link")
    print(f"  {C.DK_CYN}[2]{C.RESET} Start tracker server & view stats")
    print(f"  {C.DK_CYN}[3]{C.RESET} View collected data")
    print()
    choice = safe_input(f"{C.GRAY}Choice: {C.RESET}").strip()

    tracker = LinkTracker()

    if choice == "1":
        label = safe_input(f"{C.GRAY}Link label (optional): {C.RESET}").strip()
        redirect = safe_input(f"{C.GRAY}Redirect URL (default: https://google.com): {C.RESET}").strip()
        if not redirect:
            redirect = "https://google.com"
        port_str = safe_input(f"{C.GRAY}Server port (default 8899): {C.RESET}").strip()
        port = int(port_str) if port_str.isdigit() else 8899
        tracker.port = port

        link_id = tracker.create_link(label, redirect)

        ip = safe_input(f"{C.GRAY}Your server IP (default 127.0.0.1): {C.RESET}").strip()
        if not ip:
            ip = "127.0.0.1"

        url = tracker.get_link_url(link_id, ip)
        print(f"\n  {C.CYAN}{C.BOLD}Tracking link created!{C.RESET}")
        print(f"  {C.DK_CYN}Link ID:{C.RESET}  {link_id}")
        print(f"  {C.DK_CYN}URL:{C.RESET}     {C.DK_MAG}{url}{C.RESET}")
        print(f"  {C.DK_CYN}Redirect:{C.RESET} {redirect}")
        print(f"\n  {C.GRAY}Start the server (option 2) before sharing the link.{C.RESET}")

    elif choice == "2":
        port_str = safe_input(f"{C.GRAY}Server port (default 8899): {C.RESET}").strip()
        port = int(port_str) if port_str.isdigit() else 8899
        tracker.port = port

        type_line(f"\n  {C.GRAY}Starting tracker server on port {port}...{C.RESET}")
        type_line(f"  {C.GRAY}Press Ctrl+C to stop.{C.RESET}\n")

        try:
            asyncio.run(tracker.start())
        except KeyboardInterrupt:
            tracker.stop()
            filepath = tracker.save_results()
            type_line(f"\n  {C.DK_CYN}Results saved to {filepath}{C.RESET}")

    elif choice == "3":
        visits = tracker.get_visits()
        if not visits:
            type_line(f"  {C.GRAY}No visits recorded yet.{C.RESET}")
            press_enter()
            return

        print(f"\n  {C.DK_CYN}Recorded visits: {len(visits)}{C.RESET}\n")
        for v in visits[-20:]:
            data = v.get("data", {})
            ip = v.get("ip", "?")
            ua = data.get("user_agent", "?")[:50]
            link_id = v.get("link_id", "?")
            ts = v.get("timestamp", "?")[:19]
            print(f"    {C.DK_CYN}[{ts}]{C.RESET} {C.CYAN}{ip}{C.RESET} via {link_id}")
            print(f"      {C.GRAY}UA: {ua}{C.RESET}")
            if data.get("platform"):
                print(f"      {C.GRAY}OS: {data['platform']} | Screen: {data.get('screen_width')}x{data.get('screen_height')}{C.RESET}")
            print()

    press_enter()


def option_social_media_scan():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}SOCIAL MEDIA SCANNER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.osint.social_media import SocialMediaScanner

    username = safe_input(f"{C.GRAY}Username to search: {C.RESET}").strip()
    if not username:
        type_line(f"  {C.DK_RED}No username provided.{C.RESET}")
        press_enter()
        return

    scanner = SocialMediaScanner()
    type_line(f"\n  {C.GRAY}Scanning {username} across 40+ platforms...{C.RESET}\n")

    result: dict[str, Any] = asyncio.run(scanner.scan(username))

    found = result.get("found", [])
    not_found = result.get("not_found", [])
    total = result.get("total_scanned", 0)

    print(f"  {C.DK_CYN}Results for:{C.RESET} {C.CYAN}{username}{C.RESET}")
    print(f"  {C.DK_CYN}Scanned:{C.RESET}    {total} platforms")
    print(f"  {C.CYAN}{C.BOLD}Found:{C.RESET}      {len(found)}")
    print(f"  {C.GRAY}Not found:{C.RESET} {len(not_found)}")
    print()

    if found:
        print(f"  {C.CYAN}{C.BOLD}FOUND ({len(found)}):{C.RESET}")
        for f in found:
            cat = f.get("category", "")
            print(f"    {C.CYAN}[+]{C.RESET} {f['name']:<20} {C.DK_CYN}{cat:<12}{C.RESET} {C.GRAY}{f['url']}{C.RESET}")
        print()

    if not_found:
        print(f"  {C.GRAY}NOT FOUND ({len(not_found)}):{C.RESET}")
        names = [f["name"] for f in not_found]
        for i in range(0, len(names), 4):
            chunk = names[i:i+4]
            print(f"    {C.GRAY}{', '.join(chunk)}{C.RESET}")

    save = safe_input(f"\n{C.GRAY}Save results? (y/n): {C.RESET}").lower()
    if save == "y":
        import json
        filepath = f"social_media_{username}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        type_line(f"  {C.DK_CYN}Results saved to {filepath}{C.RESET}")

    press_enter()


def option_leak_monitor():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}DATA LEAK MONITOR{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.security.leak_monitor import LeakMonitor

    print(f"  {C.DK_CYN}[1]{C.RESET} Check email for breaches")
    print(f"  {C.DK_CYN}[2]{C.RESET} Check password exposure")
    print(f"  {C.DK_CYN}[3]{C.RESET} Check username")
    print(f"  {C.DK_CYN}[4]{C.RESET} View check history")
    print(f"  {C.DK_CYN}[5]{C.RESET} Clear history")
    print()
    choice = safe_input(f"{C.GRAY}Choice: {C.RESET}").strip()

    monitor = LeakMonitor()

    if choice == "1":
        email = safe_input(f"{C.GRAY}Email to check: {C.RESET}").strip()
        if not email:
            type_line(f"  {C.DK_RED}No email provided.{C.RESET}")
            press_enter()
            return

        type_line(f"\n  {C.GRAY}Checking {email} for breaches...{C.RESET}\n")
        result: dict[str, Any] = asyncio.run(monitor.check_email(email))

        breaches = result.get("breaches", [])
        pastes = result.get("pastes", [])
        count = result.get("breach_count", 0)

        if count == 0 and not pastes:
            print(f"  {C.CYAN}No breaches found for {email}{C.RESET}")
        else:
            if count > 0:
                print(f"  {C.DK_RED}{C.BOLD}Found in {count} breach(es):{C.RESET}\n")
                for b in breaches[:15]:
                    verified = "verified" if b.get("is_verified") else "unverified"
                    print(f"    {C.DK_RED}[BREACH]{C.RESET} {C.DK_CYN}{b['name']}{C.RESET} ({verified})")
                    print(f"      Date: {b.get('breach_date', '?')} | Records: {b.get('pwn_count', 0):,}")
                    classes = ", ".join(b.get("data_classes", [])[:5])
                    print(f"      {C.GRAY}Data: {classes}{C.RESET}")
                    print()

            if pastes:
                print(f"  {C.DK_YEL}{C.BOLD}Found in {len(pastes)} paste(s):{C.RESET}\n")
                for p in pastes[:10]:
                    print(f"    {C.DK_YEL}[PASTE]{C.RESET} {p.get('source', '?')} - {p.get('title', '?')}")
                    print(f"      {C.GRAY}Date: {p.get('date', '?')}{C.RESET}")

    elif choice == "2":
        password = safe_input(f"{C.GRAY}Password to check: {C.RESET}")
        if not password:
            type_line(f"  {C.DK_RED}No password provided.{C.RESET}")
            press_enter()
            return

        type_line(f"\n  {C.GRAY}Checking password exposure...{C.RESET}\n")
        result: dict[str, Any] = asyncio.run(monitor.check_password(password))

        if result.get("found"):
            count = result.get("count", 0)
            print(f"  {C.DK_RED}{C.BOLD}Password found in {count:,} data breach(es)!{C.RESET}")
            print(f"  {C.GRAY}This password has been compromised and should NOT be used.{C.RESET}")
        else:
            print(f"  {C.CYAN}Password not found in any known data breach.{C.RESET}")

    elif choice == "3":
        username = safe_input(f"{C.GRAY}Username to check: {C.RESET}").strip()
        if not username:
            type_line(f"  {C.DK_RED}No username provided.{C.RESET}")
            press_enter()
            return

        type_line(f"\n  {C.GRAY}Checking {username}...{C.RESET}\n")
        result: dict[str, Any] = asyncio.run(monitor.check_username(username))

        found_on = result.get("found_on", [])
        if found_on:
            print(f"  {C.DK_YEL}Found on: {', '.join(found_on)}{C.RESET}")
        else:
            print(f"  {C.CYAN}No results found for {username}{C.RESET}")

    elif choice == "4":
        history = monitor.get_history()
        if not history:
            type_line(f"  {C.GRAY}No check history.{C.RESET}")
            press_enter()
            return

        print(f"\n  {C.DK_CYN}Check History ({len(history)} entries):{C.RESET}\n")
        for h in history[-20:]:
            ts = h.get("timestamp", "?")[:19]
            check_type = h.get("type", "?")
            value = h.get("value", "?")
            extra = ""
            if "breach_count" in h:
                extra = f" | breaches: {h['breach_count']}"
            if "found" in h:
                extra = f" | found: {h['found']}"
            print(f"    {C.DK_CYN}[{ts}]{C.RESET} {check_type}: {value}{C.GRAY}{extra}{C.RESET}")

    elif choice == "5":
        monitor.clear_history()
        type_line(f"  {C.CYAN}History cleared.{C.RESET}")

    press_enter()


def option_nuclei_scan():
    from cli.handlers.osint import option_osint_tool
    from features.security.nuclei import NucleiWrapper
    option_osint_tool(NucleiWrapper, "nuclei")


def option_payload_tester():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}PAYLOAD TESTER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.security.payload_tester import PayloadTester

    url = safe_input(f"{C.GRAY}Target URL (with param): {C.RESET}").strip()
    if not url or "?" not in url:
        type_line(f"  {C.DK_RED}URL must include a query parameter (e.g. http://site.com/?q=test){C.RESET}")
        press_enter()
        return

    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    params = list(parse_qs(parsed.query).keys())
    if not params:
        type_line(f"  {C.DK_RED}No parameters found in URL.{C.RESET}")
        press_enter()
        return

    print(f"\n  {C.GRAY}Parameters found: {', '.join(params)}{C.RESET}")
    param = safe_input(f"{C.GRAY}Parameter to test: {C.RESET}").strip()
    if not param:
        param = params[0]

    print(f"\n  {C.DK_CYN}[1]{C.RESET} XSS payloads")
    print(f"  {C.DK_CYN}[2]{C.RESET} SQL Injection payloads")
    print()
    choice = safe_input(f"{C.GRAY}Payload type: {C.RESET}").strip()

    tester = PayloadTester()

    if choice == "2":
        type_line(f"\n  {C.GRAY}Testing SQLi payloads...{C.RESET}\n")
        results = asyncio.run(tester.test_sqli(url, param))
    else:
        type_line(f"\n  {C.GRAY}Testing XSS payloads...{C.RESET}\n")
        results = asyncio.run(tester.test_xss(url, param))

    reflected = [r for r in results if r.get("reflected")]
    print(f"  {C.DK_CYN}Tested {len(results)} payloads, {len(reflected)} reflected{C.RESET}\n")
    for r in reflected:
        print(f"  {C.CYAN}[REFLECTED]{C.RESET} {r['payload'][:60]}")

    press_enter()


def option_session_validator():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}SESSION VALIDATOR{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.security.session_validator import SessionValidator

    url = safe_input(f"{C.GRAY}Target URL: {C.RESET}").strip()
    if not url:
        type_line(f"  {C.DK_RED}No URL provided.{C.RESET}")
        press_enter()
        return

    print(f"\n  {C.DK_CYN}[1]{C.RESET} Cookie")
    print(f"  {C.DK_CYN}[2]{C.RESET} Bearer token")
    print(f"  {C.DK_CYN}[3]{C.RESET} Custom header")
    choice = safe_input(f"{C.GRAY}Auth type: {C.RESET}").strip()

    validator = SessionValidator()
    result: dict[str, Any] = {}

    if choice == "2":
        token = safe_input(f"{C.GRAY}Bearer token: {C.RESET}").strip()
        result = asyncio.run(validator.validate_token(url, token))
    elif choice == "3":
        header = safe_input(f"{C.GRAY}Header name: {C.RESET}").strip()
        value = safe_input(f"{C.GRAY}Header value: {C.RESET}").strip()
        result = asyncio.run(validator.validate_header(url, header, value))
    else:
        name = safe_input(f"{C.GRAY}Cookie name: {C.RESET}").strip()
        value = safe_input(f"{C.GRAY}Cookie value: {C.RESET}").strip()
        result = asyncio.run(validator.validate_cookie(url, name, value))

    print(f"\n  {C.DK_CYN}Results:{C.RESET}")
    print(f"  Valid:    {C.CYAN if result.get('valid') else C.DK_RED}{result.get('valid')}{C.RESET}")
    print(f"  Status:   {result.get('status_code')}")
    print(f"  Length:   {result.get('content_length')}")
    if result.get("redirect_url"):
        print(f"  Redirect: {result.get('redirect_url')}")
    if result.get("error"):
        print(f"  Error:    {result.get('error')}")

    press_enter()


def option_token_generator():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}TOKEN GENERATOR{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.security.token_generator import TokenGenerator

    gen = TokenGenerator()
    result: dict[str, Any] = {}

    print(f"  {C.DK_CYN}[1]{C.RESET} Generate JWT")
    print(f"  {C.DK_CYN}[2]{C.RESET} Decode JWT")
    print(f"  {C.DK_CYN}[3]{C.RESET} Validate JWT")
    print(f"  {C.DK_CYN}[4]{C.RESET} Generate API key")
    print(f"  {C.DK_CYN}[5]{C.RESET} Generate random secret")
    print()
    choice = safe_input(f"{C.GRAY}Choice: {C.RESET}").strip()

    if choice == "1":
        secret = safe_input(f"{C.GRAY}Secret key: {C.RESET}").strip()
        payload_str = safe_input(f"{C.GRAY}Payload (JSON, or Enter for default): {C.RESET}").strip()
        import json
        payload = json.loads(payload_str) if payload_str else {"sub": "user123"}
        token = gen.generate_jwt(payload, secret)
        type_line(f"\n  {C.DK_CYN}Token:{C.RESET}")
        print(f"  {token}")

    elif choice == "2":
        token = safe_input(f"{C.GRAY}JWT token: {C.RESET}").strip()
        result = gen.decode_jwt(token)
        if "error" in result:
            type_line(f"  {C.DK_RED}{result['error']}{C.RESET}")
        else:
            print(f"\n  {C.DK_CYN}Header:{C.RESET}  {json.dumps(result['header'], indent=2)}")
            print(f"  {C.DK_CYN}Payload:{C.RESET} {json.dumps(result['payload'], indent=2)}")

    elif choice == "3":
        token = safe_input(f"{C.GRAY}JWT token: {C.RESET}").strip()
        secret = safe_input(f"{C.GRAY}Secret key: {C.RESET}").strip()
        result = gen.validate_jwt(token, secret)
        print(f"\n  Valid:      {result.get('valid')}")
        print(f"  Signature:  {result.get('signature_valid')}")
        print(f"  Expired:    {result.get('expired')}")

    elif choice == "4":
        key = gen.generate_api_key()
        type_line(f"\n  {C.DK_CYN}API Key:{C.RESET} {key}")

    elif choice == "5":
        secret = gen.generate_random_secret()
        type_line(f"\n  {C.DK_CYN}Secret:{C.RESET} {secret}")

    press_enter()
