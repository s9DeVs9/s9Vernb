
import asyncio
import aiohttp
import logging
import os
from typing import Optional

logger = logging.getLogger("S9Checker")


class Marketplace:

    SOURCES = [
        {
            "name": "GitHub - Combolist Collections",
            "url": "https://api.github.com/search/repositories?q=combo+list+credentials&sort=updated&per_page=5",
            "type": "github",
        },
    ]

    def __init__(self, proxy: Optional[str] = None, timeout: int = 15):
        self.proxy = proxy
        self.timeout = timeout

    async def search_github(self, query: str = "combolist", max_results: int = 10) -> list[dict]:
        url = f"https://api.github.com/search/repositories?q={query}+credentials&sort=updated&per_page={max_results}"
        results = []

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, proxy=self.proxy, ssl=False) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for repo in data.get("items", [])[:max_results]:
                            results.append({
                                "name": repo.get("full_name", ""),
                                "description": repo.get("description", ""),
                                "url": repo.get("html_url", ""),
                                "stars": repo.get("stargazers_count", 0),
                                "updated": repo.get("updated_at", ""),
                                "size_kb": repo.get("size", 0),
                            })
        except Exception as e:
            logger.error(f"GitHub search failed: {e}")

        return results

    async def search_all(self, query: str = "combolist", max_results: int = 10) -> list[dict]:
        results = []
        github = await self.search_github(query, max_results)
        results.extend(github)
        return results

    async def download_file(self, url: str, output_path: str) -> bool:
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, proxy=self.proxy, ssl=False) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(content)
                        logger.info(f"Downloaded {len(content)} bytes to {output_path}")
                        return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
        return False

    def filter_combos(self, combos: list[str], domain: str = "",
                      min_length: int = 5) -> list[str]:
        filtered = []
        for line in combos:
            line = line.strip()
            if not line or ":" not in line:
                continue
            parts = line.split(":", 1)
            if len(parts) != 2:
                continue
            email, password = parts
            if len(password) < min_length:
                continue
            if domain and not email.lower().endswith(f"@{domain.lower()}"):
                continue
            filtered.append(line)
        return filtered
