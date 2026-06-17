
import asyncio
import os

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

    result = asyncio.run(locator.lookup(ip))

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

    result = asyncio.run(osint.full_lookup(email))

    print(f"  {C.DK_CYN}Email:{C.RESET} {result.get('email')}\n")
    for r in result.get("results", []):
        service = r.get("service", "?")
        if r.get("exists") or r.get("found") or r.get("breached"):
            print(f"  {C.GREEN}[+]{C.RESET} {service}: ", end="")
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

    enumerator = AccountEnumerator()
    type_line(f"\n  {C.GRAY}Enumerating {email} on {len(selected)} platforms...{C.RESET}\n")

    result = asyncio.run(enumerator.enumerate(email, selected))

    print(f"  {C.DK_CYN}Results for {email}:{C.RESET}\n")
    for pname, info in result.get("platforms", {}).items():
        avg = info.get("avg_response_time", 0)
        samples = info.get("samples", 0)
        print(f"    {pname:<25} avg: {avg:.3f}s  ({samples} samples)")

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
        print(f"  {C.GREEN}[REFLECTED]{C.RESET} {r['payload'][:60]}")

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
    print(f"  Valid:    {C.GREEN if result.get('valid') else C.DK_RED}{result.get('valid')}{C.RESET}")
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
