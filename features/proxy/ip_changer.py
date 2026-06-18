
import asyncio
import aiohttp
import json
import logging
from typing import Any, Optional, cast

logger = logging.getLogger("S9Checker")


class IPChanger:

    CHECK_URLS = [
        "https://api.ipify.org?format=json",
        "https://icanhazip.com",
        "https://ifconfig.me/ip",
        "https://ipinfo.io/ip",
    ]

    def __init__(self, proxy: Optional[str] = None, timeout: int = 10):
        self.proxy = proxy
        self.timeout = timeout
        self._current_proxy: Optional[str] = None

    async def get_current_ip(self) -> str:
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for url in self.CHECK_URLS:
                try:
                    async with session.get(
                        url, proxy=self.proxy, ssl=False,
                        headers={"User-Agent": "S9Checker"},
                    ) as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            text = text.strip()
                            if text.startswith("{"):
                                data = cast(dict[str, Any], json.loads(text))
                                return data.get("ip", text)
                            return text
                except Exception:
                    continue
        return "unknown"

    async def get_ip_via_proxy(self, proxy_url: str) -> str:
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for url in self.CHECK_URLS:
                try:
                    async with session.get(
                        url, proxy=proxy_url, ssl=False,
                        headers={"User-Agent": "S9Checker"},
                    ) as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            text = text.strip()
                            if text.startswith("{"):
                                data = cast(dict[str, Any], json.loads(text))
                                return data.get("ip", text)
                            return text
                except Exception:
                    continue
        return "unknown"

    async def test_proxy(self, proxy_url: str) -> dict:
        result: dict = {
            "proxy": proxy_url,
            "ip": "unknown",
            "working": False,
            "latency": 0.0,
            "error": "",
        }

        import time
        start = time.time()
        try:
            ip = await self.get_ip_via_proxy(proxy_url)
            elapsed = time.time() - start
            result["ip"] = ip
            result["working"] = ip != "unknown"
            result["latency"] = round(elapsed, 3)
        except Exception as e:
            result["error"] = str(e)[:100]

        return result

    async def scrape_and_test_proxies(self, proxy_type: str = "http",
                                       count: int = 30) -> list[dict]:
        from features.proxy.scraper import ProxyScraper

        scraper = ProxyScraper(timeout=self.timeout)
        proxies = await scraper.scrape_all(proxy_type)
        if not proxies:
            return []

        tested = []
        valid = []
        for p in proxies[:count]:
            proto = p.get("protocol", proxy_type)
            ip = p.get("ip", "")
            port = p.get("port", 0)
            if not ip or not port:
                continue

            user = p.get("user", "")
            pwd = p.get("pass", "")
            if user and pwd:
                proxy_url = f"{proto}://{user}:{pwd}@{ip}:{port}"
            else:
                proxy_url = f"{proto}://{ip}:{port}"

            result = await self.test_proxy(proxy_url)
            result["source"] = p
            tested.append(result)
            if result["working"]:
                valid.append(result)

        return valid

    def set_proxy(self, proxy_url: Optional[str]) -> None:
        self._current_proxy = proxy_url

    @property
    def current_proxy(self) -> Optional[str]:
        return self._current_proxy
