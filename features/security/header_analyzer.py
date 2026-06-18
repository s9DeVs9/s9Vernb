
import asyncio
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger("S9Checker")


SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "description": "Force HTTPS connections",
        "severity": "high",
        "weight": 15,
    },
    "Content-Security-Policy": {
        "description": "Prevent XSS and injection attacks",
        "severity": "critical",
        "weight": 20,
    },
    "X-Frame-Options": {
        "description": "Prevent clickjacking",
        "severity": "high",
        "weight": 10,
    },
    "X-Content-Type-Options": {
        "description": "Prevent MIME type sniffing",
        "severity": "medium",
        "weight": 8,
    },
    "X-XSS-Protection": {
        "description": "XSS filter (legacy browsers)",
        "severity": "low",
        "weight": 3,
    },
    "Referrer-Policy": {
        "description": "Control referrer information leakage",
        "severity": "medium",
        "weight": 7,
    },
    "Permissions-Policy": {
        "description": "Control browser feature access",
        "severity": "medium",
        "weight": 7,
    },
    "Cross-Origin-Opener-Policy": {
        "description": "Isolate browsing context",
        "severity": "low",
        "weight": 5,
    },
    "Cross-Origin-Resource-Policy": {
        "description": "Control cross-origin resource loading",
        "severity": "low",
        "weight": 5,
    },
    "Cross-Origin-Embedder-Policy": {
        "description": "Enable cross-origin isolation",
        "severity": "low",
        "weight": 5,
    },
}

INSECURE_PATTERNS = {
    "X-Frame-Options": ["DENY", "SAMEORIGIN"],
    "X-Content-Type-Options": ["nosniff"],
    "X-XSS-Protection": ["1; mode=block"],
    "Referrer-Policy": [
        "no-referrer", "strict-origin", "strict-origin-when-cross-origin",
        "same-origin", "no-referrer-when-downgrade",
    ],
}


class HeaderAnalyzer:

    def __init__(self, proxy: Optional[str] = None, timeout: int = 15):
        self.proxy = proxy
        self.timeout = timeout

    async def analyze(self, url: str) -> dict:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        result: dict = {
            "url": url,
            "headers": {},
            "security_headers": {},
            "missing_headers": [],
            "insecure_headers": [],
            "score": 0,
            "max_score": 100,
            "grade": "",
            "recommendations": [],
            "error": "",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    url, proxy=self.proxy, ssl=False,
                    allow_redirects=True,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                ) as resp:
                    result["headers"] = dict(resp.headers)
                    result["status_code"] = resp.status
                    result["final_url"] = str(resp.url)

                    self._check_security_headers(result)
                    self._check_insecure_values(result)
                    self._calculate_score(result)
                    self._generate_recommendations(result)

        except aiohttp.ClientError as e:
            result["error"] = f"Connection error: {str(e)[:100]}"
        except asyncio.TimeoutError:
            result["error"] = "Request timed out"
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)[:100]}"

        return result

    def _check_security_headers(self, result: dict) -> None:
        headers = {k.lower(): k for k in result["headers"]}
        for header_name, info in SECURITY_HEADERS.items():
            if header_name.lower() in headers:
                real_name = headers[header_name.lower()]
                value = result["headers"][real_name]
                result["security_headers"][header_name] = {
                    "present": True,
                    "value": value,
                    "severity": info["severity"],
                    "description": info["description"],
                }
            else:
                result["missing_headers"].append({
                    "name": header_name,
                    "severity": info["severity"],
                    "description": info["description"],
                })

    def _check_insecure_values(self, result: dict) -> None:
        headers_lower = {k.lower(): v for k, v in result["headers"].items()}
        for header_name, valid_values in INSECURE_PATTERNS.items():
            value = headers_lower.get(header_name.lower(), "")
            if value and not any(v.lower() in value.lower() for v in valid_values):
                result["insecure_headers"].append({
                    "name": header_name,
                    "value": value,
                    "expected": valid_values,
                })

    def _calculate_score(self, result: dict) -> None:
        total_weight = sum(info["weight"] for info in SECURITY_HEADERS.values())
        earned = 0

        for header_name, info in SECURITY_HEADERS.items():
            if header_name in result["security_headers"]:
                val = result["security_headers"][header_name]["value"]
                if header_name in INSECURE_PATTERNS:
                    if any(v.lower() in val.lower() for v in INSECURE_PATTERNS[header_name]):
                        earned += info["weight"]
                    else:
                        earned += info["weight"] * 0.5
                else:
                    earned += info["weight"]

        penalty = len(result["insecure_headers"]) * 3
        earned = max(0, earned - penalty)

        result["score"] = int((earned / total_weight) * 100) if total_weight > 0 else 0

        score = result["score"]
        if score >= 90:
            result["grade"] = "A+"
        elif score >= 80:
            result["grade"] = "A"
        elif score >= 70:
            result["grade"] = "B"
        elif score >= 60:
            result["grade"] = "C"
        elif score >= 40:
            result["grade"] = "D"
        else:
            result["grade"] = "F"

    def _generate_recommendations(self, result: dict) -> None:
        for missing in result["missing_headers"]:
            result["recommendations"].append(
                f"Add {missing['name']}: {missing['description']}"
            )
        for insecure in result["insecure_headers"]:
            result["recommendations"].append(
                f"Fix {insecure['name']}: current value '{insecure['value']}' "
                f"should be one of: {', '.join(insecure['expected'][:2])}"
            )
