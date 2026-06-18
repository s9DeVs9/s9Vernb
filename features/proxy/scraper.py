
import asyncio
import aiohttp
import logging
import re
from typing import Any, Optional, cast

logger = logging.getLogger("S9Checker")


class ProxyScraper:

    SOURCES = [
        {
            "name": "Free Proxy List",
            "url": "https://www.free-proxy-list.net/",
            "type": "html",
        },
        {
            "name": "Geonode SOCKS5",
            "url": "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc&protocols=socks5",
            "type": "api",
        },
        {
            "name": "Geonode HTTP",
            "url": "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc&protocols=http",
            "type": "api",
        },
    ]

    def __init__(self, proxy: Optional[str] = None, timeout: int = 15):
        self.proxy = proxy
        self.timeout = timeout

    async def scrape_geonode(self, protocol: str = "http", limit: int = 50) -> list[dict]:
        url = (f"https://proxylist.geonode.com/api/proxy-list?"
               f"limit={limit}&page=1&sort_by=lastChecked&sort_type=desc"
               f"&protocols={protocol}")
        proxies = []
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, proxy=self.proxy, ssl=False) as resp:
                    if resp.status == 200:
                        data = cast(dict[str, Any], await resp.json())
                        for p in data.get("data", []):
                            proxies.append({
                                "ip": p.get("ip"),
                                "port": p.get("port"),
                                "protocol": p.get("protocols", [protocol])[0] if p.get("protocols") else protocol,
                                "country": p.get("country"),
                                "speed": p.get("speed"),
                                "last_checked": p.get("lastChecked"),
                            })
        except Exception as e:
            logger.error(f"Geonode scrape failed: {e}")
        return proxies

    async def scrape_proxyscrape(self, protocol: str = "http") -> list[dict]:
        url = f"https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text&timeout=5000&protocol={protocol}"
        proxies = []
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, proxy=self.proxy, ssl=False) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        for line in text.strip().split("\n"):
                            line = line.strip()
                            if not line:
                                continue
                            parts = line.split("://")
                            if len(parts) == 2:
                                proto = parts[0]
                                host_port = parts[1].split(":")
                                if len(host_port) == 2:
                                    proxies.append({
                                        "ip": host_port[0],
                                        "port": int(host_port[1]),
                                        "protocol": proto,
                                    })
                            elif ":" in line:
                                host_port = line.split(":")
                                if len(host_port) == 2:
                                    proxies.append({
                                        "ip": host_port[0],
                                        "port": int(host_port[1]),
                                        "protocol": protocol,
                                    })
        except Exception as e:
            logger.error(f"ProxyScrape failed: {e}")
        return proxies

    async def scrape_all(self, protocol: str = "http", limit: int = 50) -> list[dict]:
        results = await asyncio.gather(
            self.scrape_geonode(protocol, limit),
            self.scrape_proxyscrape(protocol),
            return_exceptions=True,
        )
        all_proxies = []
        for r in results:
            if isinstance(r, list):
                all_proxies.extend(r)
        seen = set()
        unique = []
        for p in all_proxies:
            key = f"{p['ip']}:{p['port']}"
            if key not in seen:
                seen.add(key)
                unique.append(p)
        return unique

    async def validate_proxy(self, proxy_dict: dict) -> dict:
        proto = proxy_dict.get("protocol", "http")
        ip = proxy_dict.get("ip", "")
        port = proxy_dict.get("port", 0)
        proxy_url = f"{proto}://{ip}:{port}"

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    "http://httpbin.org/ip",
                    proxy=proxy_url, ssl=False,
                ) as resp:
                    if resp.status == 200:
                        data = cast(dict[str, Any], await resp.json())
                        proxy_dict["working"] = True
                        proxy_dict["your_ip"] = data.get("origin")
                    else:
                        proxy_dict["working"] = False
        except Exception:
            proxy_dict["working"] = False

        return proxy_dict

    async def scrape_and_validate(self, protocol: str = "http",
                                   validate: bool = True) -> list[dict]:
        proxies = await self.scrape_all(protocol)
        if validate and proxies:
            tasks = [self.validate_proxy(p) for p in proxies[:30]]
            proxies = await asyncio.gather(*tasks)
            proxies = [p for p in proxies if p.get("working")]
        return proxies

    def format_proxy(self, proxy_dict: dict) -> str:
        proto = proxy_dict.get("protocol", "http")
        ip = proxy_dict.get("ip", "")
        port = proxy_dict.get("port", 0)
        user = proxy_dict.get("user", "")
        pwd = proxy_dict.get("pass", "")
        if user and pwd:
            return f"{proto}://{user}:{pwd}@{ip}:{port}"
        return f"{proto}://{ip}:{port}"

    def to_server_dict(self, proxy_dict: dict) -> dict:
        return {
            "host": proxy_dict.get("ip", ""),
            "port": proxy_dict.get("port", 0),
            "user": proxy_dict.get("user"),
            "pass": proxy_dict.get("pass"),
        }

    def to_server_list(self, proxy_list: list[dict]) -> list[dict]:
        return [self.to_server_dict(p) for p in proxy_list if p.get("ip") and p.get("port")]
