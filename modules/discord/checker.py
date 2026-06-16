
import asyncio
import aiohttp
import time
import logging
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum

from modules.discord.generator import (
    generate_nitro_code, generate_nitro_url,
    generate_boost_code, generate_boost_url,
    generate_promo_code, PROMO_TEMPLATES,
)

logger = logging.getLogger("S9Checker")


class CodeStatus(str, Enum):
    VALID   = "valid"
    INVALID = "invalid"
    RATE    = "rate_limited"
    ERROR   = "error"


@dataclass
class CodeResult:
    code: str
    status: CodeStatus
    details: str = ""
    promo_type: str = ""


class DiscordChecker:

    DISCORD_GIFT_API = "https://discordapp.com/api/v9/entitlements/codes"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    def __init__(self,
                 progress_cb: Optional[Callable[[dict], Awaitable[None]]] = None,
                 proxy: Optional[str] = None,
                 delay: float = 0.5,
                 timeout: int = 10):
        self.progress_cb = progress_cb
        self.proxy = proxy
        self.delay = delay
        self.timeout = timeout
        self._stop = False
        self._results: list[CodeResult] = []
        self._stats = {"valid": 0, "invalid": 0, "rate": 0, "errors": 0}

    def stop(self):
        self._stop = True

    @property
    def stats(self):
        return dict(self._stats)

    @property
    def results(self):
        return list(self._results)

    async def _check_gift_code(self, session: aiohttp.ClientSession,
                               code: str) -> CodeResult:
        if self._stop:
            return CodeResult(code, CodeStatus.ERROR, "Stopped")

        url = f"{self.DISCORD_GIFT_API}?code={code}"
        headers = {"User-Agent": self.USER_AGENT}

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with session.get(url, headers=headers, timeout=timeout,
                                   proxy=self.proxy, allow_redirects=False) as resp:
                text = await resp.text()

                if resp.status == 200:
                    if "message" not in text or "Unknown" not in text:
                        return CodeResult(code, CodeStatus.VALID, "Gift code is valid!")
                elif resp.status == 429:
                    return CodeResult(code, CodeStatus.RATE, "Rate limited")
                elif resp.status == 404:
                    return CodeResult(code, CodeStatus.INVALID, "Code does not exist")

                return CodeResult(code, CodeStatus.INVALID, f"HTTP {resp.status}")

        except asyncio.TimeoutError:
            return CodeResult(code, CodeStatus.ERROR, "Timeout")
        except aiohttp.ClientError as e:
            return CodeResult(code, CodeStatus.ERROR, f"Connection error: {str(e)[:50]}")
        except Exception as e:
            return CodeResult(code, CodeStatus.ERROR, f"Error: {str(e)[:50]}")

    async def _check_promo_code(self, session: aiohttp.ClientSession,
                                code: str, promo_type: str) -> CodeResult:
        if self._stop:
            return CodeResult(code, CodeStatus.ERROR, "Stopped", promo_type)

        url = f"{self.DISCORD_GIFT_API}?code={code}"
        headers = {"User-Agent": self.USER_AGENT}

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with session.get(url, headers=headers, timeout=timeout,
                                   proxy=self.proxy, allow_redirects=False) as resp:
                text = await resp.text()

                if resp.status == 200:
                    return CodeResult(code, CodeStatus.VALID,
                                      "Promo code is valid!", promo_type)
                elif resp.status == 429:
                    return CodeResult(code, CodeStatus.RATE,
                                      "Rate limited", promo_type)
                elif resp.status == 404:
                    return CodeResult(code, CodeStatus.INVALID,
                                      "Code does not exist", promo_type)
                else:
                    return CodeResult(code, CodeStatus.INVALID,
                                      f"HTTP {resp.status}", promo_type)

        except asyncio.TimeoutError:
            return CodeResult(code, CodeStatus.ERROR, "Timeout", promo_type)
        except aiohttp.ClientError as e:
            return CodeResult(code, CodeStatus.ERROR,
                              f"Connection error: {str(e)[:50]}", promo_type)
        except Exception as e:
            return CodeResult(code, CodeStatus.ERROR,
                              f"Error: {str(e)[:50]}", promo_type)

    async def check_codes(self, codes: list[str], code_type: str = "gift",
                          promo_type: str = "Generic",
                          max_concurrent: int = 5,
                          progress_interval: float = 0.3):
        self._stop = False
        self._results = []
        self._stats = {"valid": 0, "invalid": 0, "rate": 0, "errors": 0}

        total = len(codes)
        completed = 0
        start_time = time.time()
        last_progress = start_time

        semaphore = asyncio.Semaphore(max_concurrent)
        connector = aiohttp.TCPConnector(limit=50, force_close=True, ssl=False)

        async with aiohttp.ClientSession(connector=connector) as session:

            async def _check_one(code: str):
                nonlocal completed, last_progress

                async with semaphore:
                    if code_type == "promo":
                        result = await self._check_promo_code(session, code, promo_type)
                    else:
                        result = await self._check_gift_code(session, code)

                    self._results.append(result)
                    if result.status == CodeStatus.VALID:
                        self._stats["valid"] += 1
                    elif result.status == CodeStatus.RATE:
                        self._stats["rate"] += 1
                    elif result.status == CodeStatus.ERROR:
                        self._stats["errors"] += 1
                    else:
                        self._stats["invalid"] += 1

                    completed += 1

                    now = time.time()
                    if now - last_progress >= progress_interval or completed == total:
                        elapsed = now - start_time
                        speed = completed / elapsed if elapsed > 0 else 0
                        info = {
                            "completed": completed,
                            "total": total,
                            "valid": self._stats["valid"],
                            "invalid": self._stats["invalid"],
                            "rate": self._stats["rate"],
                            "errors": self._stats["errors"],
                            "speed": round(speed, 1),
                            "elapsed": elapsed,
                            "percent": int(completed / total * 100) if total > 0 else 0,
                        }
                        if self.progress_cb:
                            try:
                                await self.progress_cb(info)
                            except Exception:
                                pass
                        last_progress = now

                    if self.delay > 0:
                        await asyncio.sleep(self.delay)

            tasks = [_check_one(code) for code in codes]
            await asyncio.gather(*tasks, return_exceptions=True)

        if self.progress_cb:
            elapsed = time.time() - start_time
            speed = completed / elapsed if elapsed > 0 else 0
            await self.progress_cb({
                "completed": completed,
                "total": total,
                "valid": self._stats["valid"],
                "invalid": self._stats["invalid"],
                "rate": self._stats["rate"],
                "errors": self._stats["errors"],
                "speed": round(speed, 1),
                "elapsed": elapsed,
                "percent": 100 if total > 0 else 0,
                "done": True,
            })

    async def generate_and_check(self, count: int, code_type: str = "gift",
                                 promo_type: str = "Generic",
                                 length: int = 16,
                                 max_concurrent: int = 5):
        codes = []
        for _ in range(count):
            if code_type == "promo":
                codes.append(generate_promo_code(promo_type))
            else:
                codes.append(generate_nitro_code(length))

        await self.check_codes(codes, code_type, promo_type, max_concurrent)
        return self._results
