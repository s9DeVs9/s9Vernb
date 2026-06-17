
import asyncio

from core.display import C, type_line, SEPARATOR, print_banner
from core.platform_utils import clear_screen
from cli.prompts import safe_input, press_enter


def option_web_scraper():
    clear_screen()
    print_banner()
    type_line(f"  {C.DK_MAG}{C.BOLD}WEBSITE SCRAPER / CLONER{C.RESET}", delay=0.02)
    print(SEPARATOR)
    print()

    url = safe_input(f"{C.GRAY}Enter website URL: {C.RESET}").strip()
    if not url:
        return

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    output_dir = safe_input(f"{C.GRAY}Output directory (default: scraped_site): {C.RESET}")
    if not output_dir:
        output_dir = "scraped_site"

    download_assets = safe_input(f"{C.GRAY}Download CSS/JS/images? (y/n, default y): {C.RESET}").lower() != "n"

    type_line(f"\n  {C.GRAY}Scraping {url}...{C.RESET}\n")

    from features.scraper.service import WebScraper

    async def _scrape():
        scraper = WebScraper(output_dir=output_dir)
        summary = await scraper.scrape(url, download_assets=download_assets)

        if "error" in summary:
            type_line(f"  {C.DK_RED}Error: {summary['error']}{C.RESET}")
        else:
            type_line(f"\n  {C.DK_CYN}{C.BOLD}SCRAPING COMPLETE{C.RESET}")
            print(f"    HTML files:  {C.DK_CYN}{summary['html']}{C.RESET}")
            print(f"    CSS files:   {C.DK_CYN}{summary['css']}{C.RESET}")
            print(f"    JS files:    {C.DK_CYN}{summary['js']}{C.RESET}")
            print(f"    Images:      {C.DK_CYN}{summary['images']}{C.RESET}")
            print(f"\n  {C.GRAY}Saved to: {output_dir}/{C.RESET}")

    try:
        asyncio.run(_scrape())
    except KeyboardInterrupt:
        type_line(f"\n  {C.DK_YEL}Scraping interrupted.{C.RESET}")
    press_enter()
