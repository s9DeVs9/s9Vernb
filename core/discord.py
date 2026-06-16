"""
Discord Nitro / Boost / Promo code generator and checker for S9Checker.
Generates random codes and validates them against Discord's API.

Code formats:
  - Nitro Gift:   https://discord.gift/XXXXXXXXXXXXXXXX (16-24 chars)
  - Nitro Promo:  Specific codes from partner promotions (OperaGX, etc.)
  - Server Boost: Gift links for server boosts
"""

import asyncio
import aiohttp
import random
import string
import time
import logging
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("S9Checker")


# ── Status enum ──────────────────────────────────────────────────────────────
class CodeStatus(str, Enum):
    VALID   = "valid"
    INVALID = "invalid"
    RATE    = "rate_limited"
    ERROR   = "error"


# ── Result dataclass ─────────────────────────────────────────────────────────
@dataclass
class CodeResult:
    code: str
    status: CodeStatus
    details: str = ""
    promo_type: str = ""


# ── Character sets ───────────────────────────────────────────────────────────
# Discord gift codes use base-62 (a-z, A-Z, 0-9)
CODE_CHARS = string.ascii_letters + string.digits


# ── Code generators ──────────────────────────────────────────────────────────
def generate_nitro_code(length: int = 16) -> str:
    """Generate a random Discord Nitro gift code."""
    return "".join(random.choices(CODE_CHARS, k=length))


def generate_nitro_url(code: str) -> str:
    """Wrap a code into a full Discord gift URL."""
    return f"https://discord.gift/{code}"


# ── Known promo code prefixes/patterns ───────────────────────────────────────
PROMO_TEMPLATES = {
    "OperaGX": {
        "prefix": "opera",
        "length": 24,
        "description": "OperaGX x Discord Nitro promotion",
        "charset": string.ascii_lowercase + string.digits,
    },
    "PlayStation": {
        "prefix": "ps",
        "length": 20,
        "description": "PlayStation x Discord Nitro promotion",
        "charset": string.ascii_uppercase + string.digits,
    },
    "Xbox": {
        "prefix": "xb",
        "length": 20,
        "description": "Xbox x Discord Nitro promotion",
        "charset": string.ascii_uppercase + string.digits,
    },
    "EpicGames": {
        "prefix": "epic",
        "length": 24,
        "description": "Epic Games x Discord Nitro promotion",
        "charset": string.ascii_lowercase + string.digits,
    },
    "Samsung": {
        "prefix": "sam",
        "length": 20,
        "description": "Samsung x Discord Nitro promotion",
        "charset": string.ascii_lowercase + string.digits,
    },
    "Prime": {
        "prefix": "prime",
        "length": 24,
        "description": "Amazon Prime x Discord Nitro promotion",
        "charset": string.ascii_lowercase + string.digits,
    },
    "Generic": {
        "prefix": "",
        "length": 16,
        "description": "Generic Nitro promo code",
        "charset": CODE_CHARS,
    },
}


def generate_promo_code(promo_type: str = "Generic") -> str:
    """Generate a promo code for a specific promotion type."""
    template = PROMO_TEMPLATES.get(promo_type, PROMO_TEMPLATES["Generic"])
    prefix = template["prefix"]
    remaining = template["length"] - len(prefix)
    if remaining < 4:
        remaining = 12
    suffix = "".join(random.choices(template["charset"], k=remaining))
    return f"{prefix}{suffix}"


# ── Checker class ────────────────────────────────────────────────────────────
class DiscordChecker:
    """
    Async Discord code checker.
    Validates Nitro gift codes, promo codes, and boost links
    against Discord's API endpoints.
    """

    DISCORD_GIFT_API = "https://discordapp.com/api/v9/entitlements/codes"
    DISCORD_PROMO_API = "https://discord.com/api/v9/promotions"
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

    # ── Check a single gift code ────────────────────────────────────────
    async def _check_gift_code(self, session: aiohttp.ClientSession,
                               code: str) -> CodeResult:
        """Check a single Discord gift code."""
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
                    # Check if code is actually valid
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

    # ── Check a promo code ──────────────────────────────────────────────
    async def _check_promo_code(self, session: aiohttp.ClientSession,
                                code: str, promo_type: str) -> CodeResult:
        """
        Check a Discord promo code.
        Promo codes are validated using the same gift code endpoint
        since they follow the same format.
        """
        if self._stop:
            return CodeResult(code, CodeStatus.ERROR, "Stopped", promo_type)

        # Use the gift code endpoint - promo codes are gift codes
        url = f"{self.DISCORD_GIFT_API}?code={code}"
        headers = {"User-Agent": self.USER_AGENT}

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with session.get(url, headers=headers, timeout=timeout,
                                   proxy=self.proxy, allow_redirects=False) as resp:
                text = await resp.text()

                if resp.status == 200:
                    # Valid promo code
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

    # ── Batch checker ───────────────────────────────────────────────────
    async def check_codes(self, codes: list[str], code_type: str = "gift",
                          promo_type: str = "Generic",
                          max_concurrent: int = 5,
                          progress_interval: float = 0.3):
        """
        Check a list of codes.
        code_type: 'gift' | 'promo'
        """
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

        # Final update
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

    # ── Generate and check in batch ─────────────────────────────────────
    async def generate_and_check(self, count: int, code_type: str = "gift",
                                 promo_type: str = "Generic",
                                 length: int = 16,
                                 max_concurrent: int = 5):
        """Generate random codes and check them immediately."""
        codes = []
        for _ in range(count):
            if code_type == "promo":
                codes.append(generate_promo_code(promo_type))
            else:
                codes.append(generate_nitro_code(length))

        await self.check_codes(codes, code_type, promo_type, max_concurrent)
        return self._results
