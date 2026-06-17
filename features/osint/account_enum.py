
import asyncio
import time
import logging
from typing import Optional

from core.platforms import PLATFORMS, Platform
from core.session import SessionManager
from core.utils import ResultStatus

logger = logging.getLogger("S9Checker")


class AccountEnumerator:

    def __init__(self, proxy: Optional[str] = None, timeout: int = 15):
        self.proxy = proxy
        self.timeout = timeout
        self._session_mgr = SessionManager()

    async def _measure_response(self, session, platform: Platform, email: str) -> dict:
        import aiohttp
        from urllib.parse import urlencode

        fake_password = "EnumTestPass123!"

        try:
            await self._session_mgr.get_session_cookies(session, platform)
            payload = platform.build_payload(email, fake_password)
            headers = dict(platform.headers)

            if platform.auth_type == "json":
                import json
                data = json.dumps(payload)
                headers["Content-Type"] = "application/json"
            else:
                data = urlencode(payload)
                headers["Content-Type"] = "application/x-www-form-urlencoded"

            start = time.time()
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with session.request(
                platform.method, platform.login_url,
                data=data, headers=headers, timeout=timeout,
                proxy=self.proxy, ssl=False, allow_redirects=False,
            ) as resp:
                text = await resp.text()
                elapsed = time.time() - start
                return {
                    "status": resp.status,
                    "elapsed": elapsed,
                    "text_length": len(text),
                    "text_snippet": text[:200],
                }
        except Exception as e:
            return {"status": 0, "elapsed": 0, "error": str(e)}

    async def enumerate(self, email: str, platform_names: list[str] | None = None,
                        samples: int = 5) -> dict:
        if not platform_names:
            platform_names = list(PLATFORMS.keys())

        results = {}
        connector = aiohttp.TCPConnector(limit=10, ssl=False)

        async with aiohttp.ClientSession(connector=connector) as session:
            for pname in platform_names:
                platform = PLATFORMS.get(pname)
                if not platform:
                    continue

                timings = []
                for _ in range(samples):
                    r = await self._measure_response(session, platform, email)
                    if r.get("elapsed", 0) > 0:
                        timings.append(r["elapsed"])
                    await asyncio.sleep(0.5)

                if timings:
                    avg_time = sum(timings) / len(timings)
                    results[pname] = {
                        "avg_response_time": round(avg_time, 3),
                        "samples": len(timings),
                        "platform_url": platform.login_url,
                    }
                else:
                    results[pname] = {
                        "avg_response_time": 0,
                        "samples": 0,
                        "error": "All requests failed",
                    }

        return {"email": email, "platforms": results}
