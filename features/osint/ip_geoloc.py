
import asyncio
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger("S9Checker")


class IPGeolocator:

    API_URL = "http://ip-api.com/json/{ip}?fields=66846719"

    def __init__(self, proxy: Optional[str] = None, timeout: int = 10):
        self.proxy = proxy
        self.timeout = timeout

    async def lookup(self, ip: str) -> dict:
        url = self.API_URL.format(ip=ip)
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, proxy=self.proxy, ssl=False) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "success":
                            return {
                                "ip": data.get("query"),
                                "country": data.get("country"),
                                "country_code": data.get("countryCode"),
                                "region": data.get("regionName"),
                                "city": data.get("city"),
                                "zip": data.get("zip"),
                                "latitude": data.get("lat"),
                                "longitude": data.get("lon"),
                                "timezone": data.get("timezone"),
                                "isp": data.get("isp"),
                                "org": data.get("org"),
                                "as": data.get("as"),
                                "asname": data.get("asname"),
                                "reverse": data.get("reverse"),
                                "mobile": data.get("mobile"),
                                "proxy": data.get("proxy"),
                                "hosting": data.get("hosting"),
                            }
                        return {"error": data.get("message", "Lookup failed")}
                    return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"error": str(e)}

    async def lookup_batch(self, ips: list[str]) -> list[dict]:
        results = []
        for ip in ips:
            result = await self.lookup(ip)
            results.append(result)
            await asyncio.sleep(1.5)
        return results
