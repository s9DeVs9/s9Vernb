
import sys
import asyncio
import os

from core.display import C, type_line, type_text, SEPARATOR, print_banner
from core.platform_utils import clear_screen
from cli.prompts import prompt, safe_input, press_enter


def option_nitro_generator():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}DISCORD NITRO GENERATOR + CHECKER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.discord.generator import generate_nitro_code, generate_nitro_url
    from features.discord.checker import DiscordChecker

    print(f"  {C.DK_CYN}[1]{C.RESET} Generate codes only")
    print(f"  {C.DK_CYN}[2]{C.RESET} Generate + Check codes")
    print(f"  {C.DK_CYN}[3]{C.RESET} Check codes from file")
    print(f"  {C.DK_CYN}[B]{C.RESET} Back to menu")
    print()

    choice = prompt()

    if choice in ("b", ""):
        return

    if choice == "1":
        _nitro_generate_only(generate_nitro_code, generate_nitro_url)
    elif choice == "2":
        _nitro_generate_and_check(generate_nitro_code, generate_nitro_url, DiscordChecker)
    elif choice == "3":
        _nitro_check_from_file(generate_nitro_url, DiscordChecker)


def _nitro_generate_only(generate_nitro_code, generate_nitro_url):
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


def _nitro_generate_and_check(generate_nitro_code, generate_nitro_url, DiscordChecker):
    count_str = safe_input(f"{C.GRAY}How many codes to generate + check? (default 20): {C.RESET}")
    count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 20
    length_str = safe_input(f"{C.GRAY}Code length (16-24, default 16): {C.RESET}")
    length = int(length_str) if length_str.isdigit() and 16 <= int(length_str) <= 24 else 16
    delay_str = safe_input(f"{C.GRAY}Delay between checks in seconds (default 0.5): {C.RESET}")
    delay = float(delay_str) if delay_str.replace(".", "").isdigit() else 0.5

    codes = [generate_nitro_code(length) for _ in range(count)]
    type_line(f"\n  {C.GRAY}Generated {count} codes. Starting check...{C.RESET}\n")

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
        _print_discord_results(stats, checker.results, generate_nitro_url)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        type_line(f"\n  {C.DK_YEL}Check interrupted.{C.RESET}")
    press_enter()


def _nitro_check_from_file(generate_nitro_url, DiscordChecker):
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
        _print_discord_results(stats, checker.results, generate_nitro_url)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        type_line(f"\n  {C.DK_YEL}Check interrupted.{C.RESET}")
    press_enter()


def _print_discord_results(stats, results, generate_nitro_url):
    from features.discord.checker import CodeStatus

    type_line(f"\n  {C.DK_CYN}{C.BOLD}DONE{C.RESET} - "
              f"{C.DK_CYN}{stats['valid']} valid{C.RESET} / "
              f"{C.GRAY}{stats['invalid']} invalid{C.RESET} / "
              f"{C.DK_RED}{stats['errors']} errors{C.RESET}")

    if results:
        type_line(f"\n  {C.DK_CYN}{C.BOLD}ALL CHECKED CODES:{C.RESET}")
        for r in results:
            url = generate_nitro_url(r.code)
            if r.status.value == "valid":
                print(f"    {C.DK_CYN}[VALID]{C.RESET}   {url}")
            elif r.status.value == "rate_limited":
                print(f"    {C.DK_YEL}[RATE]{C.RESET}    {url}")
            elif r.status.value == "error":
                print(f"    {C.DK_RED}[ERROR]{C.RESET}   {url}")
            else:
                print(f"    {C.GRAY}[INVALID]{C.RESET} {url}")


def option_boost_generator():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}DISCORD BOOST GENERATOR + CHECKER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.discord.generator import generate_nitro_code, generate_nitro_url
    from features.discord.checker import DiscordChecker

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
            _print_discord_results(stats, checker.results, generate_nitro_url)

        try:
            asyncio.run(_run())
        except KeyboardInterrupt:
            type_line(f"\n  {C.DK_YEL}Check interrupted.{C.RESET}")
        press_enter()


def option_promo_generator():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}NITRO PROMO CODES (OperaGX, etc.){C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.discord.generator import PROMO_TEMPLATES, generate_promo_code
    from features.discord.checker import DiscordChecker

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
                _print_promo_results(stats, checker.results)

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


def _print_promo_results(stats, results):
    from features.discord.checker import CodeStatus

    type_line(f"\n  {C.DK_CYN}{C.BOLD}DONE{C.RESET} - "
              f"{C.DK_CYN}{stats['valid']} valid{C.RESET} / "
              f"{C.GRAY}{stats['invalid']} invalid{C.RESET} / "
              f"{C.DK_RED}{stats['errors']} errors{C.RESET}")

    if results:
        type_line(f"\n  {C.DK_CYN}{C.BOLD}ALL CHECKED CODES:{C.RESET}")
        for r in results:
            if r.status.value == "valid":
                print(f"    {C.DK_CYN}[VALID]{C.RESET}   {r.code}")
            elif r.status.value == "rate_limited":
                print(f"    {C.DK_YEL}[RATE]{C.RESET}    {r.code}")
            elif r.status.value == "error":
                print(f"    {C.DK_RED}[ERROR]{C.RESET}   {r.code}")
            else:
                print(f"    {C.GRAY}[INVALID]{C.RESET} {r.code}")
