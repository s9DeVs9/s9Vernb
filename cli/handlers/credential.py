
import asyncio
import os

from core.display import C, type_line, SEPARATOR, print_banner
from core.platform_utils import clear_screen
from cli.prompts import safe_input, press_enter


def option_password_generator():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}PASSWORD GENERATOR{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.credential.password_generator import PasswordGenerator

    length_str = safe_input(f"{C.GRAY}Length (default 16): {C.RESET}").strip()
    length = int(length_str) if length_str.isdigit() else 16

    count_str = safe_input(f"{C.GRAY}Count (default 20): {C.RESET}").strip()
    count = int(count_str) if count_str.isdigit() else 20

    gen = PasswordGenerator(length=length)
    passwords = gen.generate_batch(count)

    print(f"\n  {C.DK_CYN}Generated {count} passwords:{C.RESET}\n")
    for pw in passwords:
        strength = gen.estimate_strength(pw)
        color = T.GREEN if strength["strength"] in ("STRONG", "VERY STRONG") else T.RED
        print(f"  {pw}  {C.GRAY}[{strength['strength']}]{C.RESET}")

    save = safe_input(f"\n{C.GRAY}Save to file? (y/n): {C.RESET}").lower()
    if save == "y":
        filepath = "generated_passwords.txt"
        with open(filepath, "w") as f:
            f.write("\n".join(passwords) + "\n")
        type_line(f"  {C.DK_CYN}Saved to {filepath}{C.RESET}")

    press_enter()


def option_wordlist_generator():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}CUSTOM WORDLIST GENERATOR{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.credential.wordlist_generator import WordlistGenerator

    gen = WordlistGenerator()

    print(f"  {C.DK_CYN}[1]{C.RESET} Generate from name")
    print(f"  {C.DK_CYN}[2]{C.RESET} Generate from domain")
    print(f"  {C.DK_CYN}[3]{C.RESET} Generate from multiple names")
    print()

    choice = safe_input(f"{C.GRAY}Choice: {C.RESET}").strip()

    if choice == "1":
        name = safe_input(f"{C.GRAY}Name: {C.RESET}").strip()
        if name:
            gen.generate_from_name(name)
    elif choice == "2":
        domain = safe_input(f"{C.GRAY}Domain (e.g. gmail.com): {C.RESET}").strip()
        if domain:
            gen.generate_from_domain(domain)
    elif choice == "3":
        names_str = safe_input(f"{C.GRAY}Names (comma-separated): {C.RESET}").strip()
        if names_str:
            names = [n.strip() for n in names_str.split(",")]
            gen.generate_from_names(names)

    use_leet = safe_input(f"{C.GRAY}Apply leet speak mutations? (y/n): {C.RESET}").lower()
    if use_leet == "y":
        gen.apply_leet()

    wordlist = gen.get_wordlist()
    print(f"\n  {C.DK_CYN}Generated {len(wordlist)} words{C.RESET}")
    for w in wordlist[:30]:
        print(f"    {w}")
    if len(wordlist) > 30:
        print(f"    {C.GRAY}... and {len(wordlist) - 30} more{C.RESET}")

    save = safe_input(f"\n{C.GRAY}Save to file? (y/n): {C.RESET}").lower()
    if save == "y":
        filepath = "generated_wordlist.txt"
        gen.save(filepath)
        type_line(f"  {C.DK_CYN}Saved {len(wordlist)} words to {filepath}{C.RESET}")

    press_enter()


def option_combolist_marketplace():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}COMBOLIST MARKETPLACE{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.credential.marketplace import Marketplace

    marketplace = Marketplace()

    query = safe_input(f"{C.GRAY}Search query (default: combolist): {C.RESET}").strip()
    if not query:
        query = "combolist"

    type_line(f"\n  {C.GRAY}Searching for '{query}'...{C.RESET}\n")

    async def _search():
        return await marketplace.search_all(query, max_results=10)

    results = asyncio.run(_search())

    if not results:
        type_line(f"  {C.DK_RED}No results found.{C.RESET}")
        press_enter()
        return

    print(f"  {C.DK_CYN}Found {len(results)} results:{C.RESET}\n")
    for i, r in enumerate(results, 1):
        print(f"    {C.DK_CYN}[{i}]{C.RESET} {r['name']}")
        print(f"        {C.GRAY}{r.get('description', 'No description')[:80]}{C.RESET}")
        print(f"        {r.get('url', '')}")
        if r.get("stars"):
            print(f"        {C.GRAY}Stars: {r['stars']}{C.RESET}")
        print()

    press_enter()
