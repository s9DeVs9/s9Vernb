"""
Session and cookie management for S9Checker.
Handles pre-fetching cookies/CSRF tokens for platforms that require them.
"""

import aiohttp
import logging
from typing import Optional

from core.platforms import Platform, PLATFORMS

logger = logging.getLogger("S9Checker")


class SessionManager:
    """Manages HTTP sessions and caches cookies/CSRF tokens per platform."""

    def __init__(self):
        self._cookies_cache: dict[str, dict] = {}

    async def get_session_cookies(self, session: aiohttp.ClientSession,
                                  platform: Platform) -> dict:
        """
        Fetch initial cookies/CSRF tokens for platforms that need them.
        Results are cached so we only do this once per platform.
        """
        if not platform.requires_session or not platform.session_url:
            return {}
        if platform.name in self._cookies_cache:
            return self._cookies_cache[platform.name]
        try:
            async with session.get(platform.session_url,
                                   timeout=aiohttp.ClientTimeout(total=15)):
                pass
            cookies = {k: v for k, v in session.cookies.items()}
            self._cookies_cache[platform.name] = cookies
            return cookies
        except Exception:
            return {}

    async def prefetch_all(self, session: aiohttp.ClientSession,
                           platform_names: list[str]):
        """Pre-fetch cookies for all listed platforms that need a session."""
        for pname in platform_names:
            platform = PLATFORMS.get(pname)
            if platform and platform.requires_session:
                await self.get_session_cookies(session, platform)

    def clear(self):
        """Clear the cookies cache."""
        self._cookies_cache.clear()
