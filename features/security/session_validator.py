
import asyncio
import aiohttp
import logging
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger("S9Checker")


class SessionValidator:

    def __init__(self, proxy: Optional[str] = None, timeout: int = 15):
        self.proxy = proxy
        self.timeout = timeout

    async def validate_cookie(self, url: str, cookie_name: str,
                               cookie_value: str) -> dict:
        cookies = {cookie_name: cookie_value}
        return await self._test_session(url, cookies)

    async def validate_header(self, url: str, header_name: str,
                               header_value: str) -> dict:
        headers = {header_name: header_value}
        return await self._test_session(url, headers=headers)

    async def validate_token(self, url: str, token: str,
                              scheme: str = "Bearer") -> dict:
        headers = {"Authorization": f"{scheme} {token}"}
        return await self._test_session(url, headers=headers)

    async def _test_session(self, url: str, cookies: dict | None = None,
                             headers: dict | None = None) -> dict:
        result = {
            "url": url,
            "valid": False,
            "status_code": 0,
            "redirect_url": "",
            "content_length": 0,
            "error": "",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    url, cookies=cookies, headers=headers,
                    proxy=self.proxy, ssl=False, allow_redirects=False,
                ) as resp:
                    result["status_code"] = resp.status
                    text = await resp.text()
                    result["content_length"] = len(text)
                    result["redirect_url"] = resp.headers.get("Location", "")

                    login_indicators = ["login", "signin", "auth", "session expired",
                                        "please log in", "unauthorized"]
                    text_lower = text.lower()
                    has_login = any(ind in text_lower for ind in login_indicators)

                    if resp.status in (200, 301, 302) and not has_login:
                        result["valid"] = True
                    elif resp.status in (401, 403):
                        result["valid"] = False
                    else:
                        result["valid"] = not has_login

        except Exception as e:
            result["error"] = str(e)

        return result

    async def compare_sessions(self, url: str, cookie_name: str,
                                valid_value: str, test_value: str) -> dict:
        valid_result = await self.validate_cookie(url, cookie_name, valid_value)
        test_result = await self.validate_cookie(url, cookie_name, test_value)

        return {
            "url": url,
            "valid_session": valid_result,
            "test_session": test_result,
            "is_valid": test_result.get("valid", False),
            "matches_valid": (valid_result.get("status_code") == test_result.get("status_code")
                              and abs(valid_result.get("content_length", 0) -
                                      test_result.get("content_length", 0)) < 500),
        }
