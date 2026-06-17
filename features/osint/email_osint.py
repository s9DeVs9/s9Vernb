
import asyncio
import aiohttp
import hashlib
import logging
from typing import Optional

logger = logging.getLogger("S9Checker")


class EmailOSINT:

    def __init__(self, proxy: Optional[str] = None, timeout: int = 15):
        self.proxy = proxy
        self.timeout = timeout

    async def check_gravatar(self, email: str) -> dict:
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, proxy=self.proxy, ssl=False) as resp:
                    return {"service": "Gravatar", "exists": resp.status == 200,
                            "url": f"https://gravatar.com/{email_hash}"}
        except Exception as e:
            return {"service": "Gravatar", "exists": False, "error": str(e)}

    async def check_hibp(self, email: str, api_key: str = "") -> dict:
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        headers = {"hibp-api-key": api_key, "User-Agent": "S9Checker"} if api_key else {}
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers, proxy=self.proxy, ssl=False) as resp:
                    if resp.status == 200:
                        breaches = await resp.json()
                        return {"service": "HaveIBeenPwned", "breached": True,
                                "breach_count": len(breaches),
                                "breaches": [b.get("Name") for b in breaches[:10]]}
                    elif resp.status == 404:
                        return {"service": "HaveIBeenPwned", "breached": False, "breach_count": 0}
                    return {"service": "HaveIBeenPwned", "error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"service": "HaveIBeenPwned", "error": str(e)}

    async def check_github(self, email: str) -> dict:
        url = f"https://api.github.com/search/users?q={email}+in:email"
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, proxy=self.proxy, ssl=False) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        users = data.get("items", [])
                        for user in users:
                            if user.get("email", "").lower() == email.lower():
                                return {"service": "GitHub", "found": True,
                                        "username": user.get("login"),
                                        "profile": user.get("html_url")}
                        return {"service": "GitHub", "found": False}
                    return {"service": "GitHub", "error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"service": "GitHub", "error": str(e)}

    async def full_lookup(self, email: str) -> dict:
        results = await asyncio.gather(
            self.check_gravatar(email),
            self.check_github(email),
            return_exceptions=True,
        )
        return {
            "email": email,
            "results": [r for r in results if isinstance(r, dict)],
        }
