
import asyncio
import os

from core.display import C, type_line, SEPARATOR, print_banner
from core.platform_utils import clear_screen
from cli.prompts import safe_input, press_enter


def option_proxy_scraper():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}PROXY SCRAPER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.proxy.scraper import ProxyScraper

    print(f"  {C.DK_CYN}[1]{C.RESET} HTTP proxies")
    print(f"  {C.DK_CYN}[2]{C.RESET} SOCKS5 proxies")
    print()
    choice = safe_input(f"{C.GRAY}Proxy type: {C.RESET}").strip()
    protocol = "socks5" if choice == "2" else "http"

    validate_str = safe_input(f"{C.GRAY}Validate proxies? (y/n, default y): {C.RESET}").strip().lower()
    validate = validate_str != "n"

    scraper = ProxyScraper()
    type_line(f"\n  {C.GRAY}Scraping {protocol} proxies...{C.RESET}\n")

    proxies = asyncio.run(scraper.scrape_and_validate(protocol, validate))

    if not proxies:
        type_line(f"  {C.DK_RED}No working proxies found.{C.RESET}")
        press_enter()
        return

    print(f"  {C.DK_CYN}Found {len(proxies)} working proxies:{C.RESET}\n")
    for p in proxies[:30]:
        print(f"  {p.get('ip')}:{p.get('port')}  {C.GRAY}({p.get('protocol', '?')}, {p.get('country', '?')}){C.RESET}")

    save = safe_input(f"\n{C.GRAY}Save to file? (y/n): {C.RESET}").lower()
    if save == "y":
        filepath = f"scraped_{protocol}_proxies.txt"
        with open(filepath, "w") as f:
            for p in proxies:
                f.write(scraper.format_proxy(p) + "\n")
        type_line(f"  {C.DK_CYN}Saved to {filepath}{C.RESET}")

    press_enter()


def option_batch_runner():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}BATCH RUNNER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    from features.automation.batch_runner import BatchRunner, BatchStep

    target = safe_input(f"{C.GRAY}Target (IP/domain): {C.RESET}").strip()
    if not target:
        type_line(f"  {C.DK_RED}No target provided.{C.RESET}")
        press_enter()
        return

    print(f"\n  {C.GRAY}Available tools:{C.RESET}")
    tools = [
        ("Nmap", "features.osint.nmap", "NmapWrapper"),
        ("Masscan", "features.osint.masscan", "MasscanWrapper"),
        ("RustScan", "features.osint.rustscan", "RustscanWrapper"),
        ("httpx", "features.osint.httpx", "HttpxWrapper"),
        ("Subfinder", "features.osint.subfinder", "SubfinderWrapper"),
        ("Nuclei", "features.security.nuclei", "NucleiWrapper"),
    ]
    for i, (name, _, _) in enumerate(tools, 1):
        print(f"    {C.DK_CYN}[{i}]{C.RESET} {name}")

    sel = safe_input(f"\n{C.GRAY}Tools (comma-separated numbers): {C.RESET}").strip()
    try:
        indices = [int(x.strip()) - 1 for x in sel.split(",")]
    except (ValueError, IndexError):
        type_line(f"  {C.DK_RED}Invalid selection.{C.RESET}")
        press_enter()
        return

    runner = BatchRunner()
    for idx in indices:
        if 0 <= idx < len(tools):
            name, module_path, class_name = tools[idx]
            import importlib
            mod = importlib.import_module(module_path)
            tool_class = getattr(mod, class_name)
            runner.add_step(name, tool_class)

    if not runner.steps:
        type_line(f"  {C.DK_RED}No tools selected.{C.RESET}")
        press_enter()
        return

    type_line(f"\n  {C.GRAY}Running {len(runner.steps)} tools on {target}...{C.RESET}\n")

    async def _progress(info):
        step = info.get("step", "")
        current = info.get("current", 0)
        total = info.get("total", 0)
        print(f"  [{current}/{total}] {step}...")

    results = asyncio.run(runner.run(target, _progress))

    summary = runner.summary()
    print(f"\n  {C.DK_CYN}Batch Complete:{C.RESET}")
    print(f"  Success: {summary['success']}/{summary['total']}")
    print(f"  Time:    {summary['total_time']}s")

    save = safe_input(f"\n{C.GRAY}Save results? (y/n): {C.RESET}").lower()
    if save == "y":
        filepath = f"batch_results_{target}.txt"
        runner.save_results(filepath)
        type_line(f"  {C.DK_CYN}Saved to {filepath}{C.RESET}")

    press_enter()
