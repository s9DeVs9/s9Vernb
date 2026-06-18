
import asyncio
import aiohttp
import hashlib
import logging
import json
import os
import time
from typing import Any, Optional, cast
from datetime import datetime

logger = logging.getLogger("S9Checker")


class LeakMonitor:

    HIBP_API = "https://haveibeenpwned.com/api/v3"
    BREACHDIR_API = "https://breachdirectory.p.rapidapi.com"
    CHECKLEAKED_API = "https://checkleaked.cc/api"

    def __init__(self, proxy: Optional[str] = None, timeout: int = 15,
                 hibp_key: Optional[str] = None):
        self.proxy = proxy
        self.timeout = timeout
        self.hibp_key = hibp_key
        self._history_file = "leak_history.json"
        self._history: dict = self._load_history()

    def _load_history(self) -> dict:
        if os.path.exists(self._history_file):
            try:
                with open(self._history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"checks": []}

    def _save_history(self) -> None:
        try:
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    async def check_email(self, email: str) -> dict:
        result: dict = {
            "email": email,
            "timestamp": datetime.now().isoformat(),
            "breaches": [],
            "breach_count": 0,
            "pastes": [],
            "paste_count": 0,
            "sources": [],
            "error": "",
        }

        try:
            breaches = await self._hibp_breaches(email)
            if breaches:
                result["breaches"] = breaches
                result["breach_count"] = len(breaches)
                result["sources"].append("HIBP")
        except Exception as e:
            logger.debug(f"HIBP breach check failed: {e}")

        try:
            pastes = await self._hibp_pastes(email)
            if pastes:
                result["pastes"] = pastes
                result["paste_count"] = len(pastes)
                if "HIBP" not in result["sources"]:
                    result["sources"].append("HIBP")
        except Exception as e:
            logger.debug(f"HIBP paste check failed: {e}")

        self._history["checks"].append({
            "type": "email",
            "value": email,
            "timestamp": result["timestamp"],
            "breach_count": result["breach_count"],
        })
        self._save_history()

        return result

    async def check_password(self, password: str) -> dict:
        sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        result: dict = {
            "password_hash": sha1_hash[:10] + "...",
            "timestamp": datetime.now().isoformat(),
            "found": False,
            "count": 0,
            "sources": [],
            "error": "",
        }

        try:
            count = await self._check_password_hibp(prefix, suffix)
            if count > 0:
                result["found"] = True
                result["count"] = count
                result["sources"].append("HIBP")
        except Exception as e:
            logger.debug(f"HIBP password check failed: {e}")

        self._history["checks"].append({
            "type": "password",
            "value": sha1_hash[:10] + "...",
            "timestamp": result["timestamp"],
            "found": result["found"],
            "count": result["count"],
        })
        self._save_history()

        return result

    async def check_username(self, username: str) -> dict:
        result: dict = {
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "found_on": [],
            "error": "",
        }

        try:
            breaches = await self._hibp_breaches(f"{username}@placeholder.com")
            if breaches:
                result["found_on"].append("HIBP (email pattern)")
        except Exception:
            pass

        self._history["checks"].append({
            "type": "username",
            "value": username,
            "timestamp": result["timestamp"],
        })
        self._save_history()

        return result

    async def _hibp_breaches(self, email: str) -> list[dict]:
        url = f"{self.HIBP_API}/breachedaccount/{email}"
        headers = {
            "hibp-api-key": self.hibp_key or "",
            "User-Agent": "S9Checker-LeakMonitor",
        }
        params = {"truncateResponse": "false"}

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                url, headers=headers, params=params,
                proxy=self.proxy, ssl=False,
            ) as resp:
                if resp.status == 200:
                    data = cast(list[dict[str, Any]], await resp.json())
                    return [
                        {
                            "name": b.get("Name", ""),
                            "title": b.get("Title", ""),
                            "domain": b.get("Domain", ""),
                            "breach_date": b.get("BreachDate", ""),
                            "pwn_count": b.get("PwnCount", 0),
                            "data_classes": b.get("DataClasses", []),
                            "is_verified": b.get("IsVerified", False),
                        }
                        for b in data
                    ]
                elif resp.status == 404:
                    return []
                elif resp.status == 401:
                    logger.warning("HIBP API key required or invalid")
                    return []
                elif resp.status == 429:
                    retry = resp.headers.get("Retry-After", "60")
                    logger.warning(f"HIBP rate limited, retry after {retry}s")
                    return []
                return []

    async def _hibp_pastes(self, email: str) -> list[dict]:
        url = f"{self.HIBP_API}/pasteaccount/{email}"
        headers = {
            "hibp-api-key": self.hibp_key or "",
            "User-Agent": "S9Checker-LeakMonitor",
        }

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                url, headers=headers,
                proxy=self.proxy, ssl=False,
            ) as resp:
                if resp.status == 200:
                    data = cast(list[dict[str, Any]], await resp.json())
                    return [
                        {
                            "source": p.get("Source", ""),
                            "id": p.get("Id", ""),
                            "title": p.get("Title", ""),
                            "date": p.get("Date", ""),
                            "email_count": p.get("EmailCount", 0),
                        }
                        for p in data
                    ]
                return []

    async def _check_password_hibp(self, prefix: str, suffix: str) -> int:
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                url, proxy=self.proxy, ssl=False,
            ) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    for line in text.split("\n"):
                        parts = line.strip().split(":")
                        if len(parts) == 2 and parts[0] == suffix:
                            return int(parts[1])
                return 0

    def get_history(self) -> list[dict]:
        return self._history.get("checks", [])

    def clear_history(self) -> None:
        self._history = {"checks": []}
        self._save_history()
