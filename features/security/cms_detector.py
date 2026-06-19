
import asyncio
import aiohttp
import logging
import re
from typing import Optional
from urllib.parse import urljoin

logger = logging.getLogger("S9Checker")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

CMS_SIGNATURES = {
    "WordPress": {
        "headers": {"x-powered-by": "WordPress", "x-generator": "WordPress"},
        "html_patterns": [
            "wp-content/", "wp-includes/", "wp-json/", "wp-login.php",
            'name="generator" content="WordPress',
            "/wp-admin/", "wordpress",
        ],
        "cookies": ["wordpress_logged_in", "wp-settings", "wordpress_test_cookie"],
        "paths": ["/wp-login.php", "/wp-admin/", "/xmlrpc.php", "/wp-json/"],
        "meta_patterns": ['content="WordPress'],
    },
    "Joomla": {
        "headers": {"x-content-encoded-by": "Joomla!"},
        "html_patterns": [
            "/media/joomla/", "/components/com_", "/modules/mod_",
            'name="generator" content="Joomla',
            "/administrator/", "joomla",
        ],
        "cookies": ["joomla_"],
        "paths": ["/administrator/", "/administrator/index.php"],
        "meta_patterns": ['content="Joomla'],
    },
    "Drupal": {
        "headers": {"x-generator": "Drupal", "x-drupal-cache": "HIT"},
        "html_patterns": [
            "sites/default/files/", "drupal.js", "drupal.css",
            'name="generator" content="Drupal',
            "/core/misc/drupal.js", "Drupal.settings",
        ],
        "cookies": ["SESS", "SSESS", "Drupalvisitor"],
        "paths": ["/user/login", "/node/", "/admin/content"],
        "meta_patterns": ['content="Drupal'],
    },
    "Magento": {
        "headers": {},
        "html_patterns": [
            "Mage.Cookies", "magento", "/skin/frontend/",
            "/static/frontend/", "requirejs/mage/",
            "Mage.prototype", "X-Magento",
        ],
        "cookies": ["frontend", "frontend_cid"],
        "paths": ["/admin/", "/customer/account/login/"],
        "meta_patterns": [],
    },
    "PrestaShop": {
        "headers": {},
        "html_patterns": [
            "prestashop", "/themes/", "prestashop.css",
            'content="PrestaShop', "/modules/prestashop/",
            "prestashop.images",
        ],
        "cookies": ["PrestaShop", "prestashop"],
        "paths": ["/admin/", "/connexion"],
        "meta_patterns": ['content="PrestaShop'],
    },
    "OpenCart": {
        "headers": {},
        "html_patterns": [
            "opencart", "catalog/view/theme/",
            "/catalog/controller/", "OpenCart",
        ],
        "cookies": ["PHPSESSID"],
        "paths": ["/admin/", "/admin/index.php"],
        "meta_patterns": [],
    },
    "Shopify": {
        "headers": {"x-shopify-stage": "production"},
        "html_patterns": [
            "cdn.shopify.com", "Shopify.theme",
            "shopify-payment-button", "myshopify.com",
            "shopify-section",
        ],
        "cookies": ["_shopify_"],
        "paths": [],
        "meta_patterns": [],
    },
    "Wix": {
        "headers": {},
        "html_patterns": [
            "wix.com", "static.wixstatic.com", "X-Wix",
            "wix-html-apps", "_wix",
        ],
        "cookies": ["_wixUID", "_wixBrowserSSID"],
        "paths": [],
        "meta_patterns": [],
    },
    "Squarespace": {
        "headers": {},
        "html_patterns": [
            "squarespace.com", "static.squarespace.com",
            "squarespace-cdn",
        ],
        "cookies": ["ss_cookie", "crumb"],
        "paths": [],
        "meta_patterns": [],
    },
    "TYPO3": {
        "headers": {"x-powered-by": "TYPO3"},
        "html_patterns": [
            "typo3", "typo3conf/", "typo3temp/",
            "fileadmin/", "t3jquery",
        ],
        "cookies": ["fe_typo_user"],
        "paths": ["/typo3/", "/typo3/install/"],
        "meta_patterns": [],
    },
    "Ghost": {
        "headers": {},
        "html_patterns": [
            "ghost-url", "ghost.min.css", "/ghost/",
            'content="Ghost',
        ],
        "cookies": [],
        "paths": ["/ghost/"],
        "meta_patterns": ['content="Ghost'],
    },
    "Hugo": {
        "headers": {},
        "html_patterns": [
            "powered by hugo", "hugo-static",
        ],
        "cookies": [],
        "paths": [],
        "meta_patterns": ['content="Hugo'],
    },
    "Jekyll": {
        "headers": {},
        "html_patterns": [
            "jekyll", "jekyll-theme",
        ],
        "cookies": [],
        "paths": [],
        "meta_patterns": ['content="Jekyll'],
    },
    "Laravel": {
        "headers": {},
        "html_patterns": [
            "laravel", "csrf-token",
        ],
        "cookies": ["laravel_session"],
        "paths": [],
        "meta_patterns": [],
    },
    "Django": {
        "headers": {"x-frame-options": "DENY"},
        "html_patterns": [
            "django", "csrfmiddlewaretoken",
        ],
        "cookies": ["csrftoken", "sessionid", "django"],
        "paths": ["/admin/"],
        "meta_patterns": [],
    },
    "Flask": {
        "headers": {},
        "html_patterns": [],
        "cookies": ["session=ey"],
        "paths": [],
        "meta_patterns": [],
    },
    "Ruby on Rails": {
        "headers": {"x-powered-by": "Phusion Passenger"},
        "html_patterns": [
            "csrf-token", "authenticity_token",
        ],
        "cookies": ["_session_id"],
        "paths": [],
        "meta_patterns": [],
    },
    "Next.js": {
        "headers": {"x-powered-by": "Next.js"},
        "html_patterns": [
            "_next/", "__next", "next/static",
        ],
        "cookies": [],
        "paths": [],
        "meta_patterns": [],
    },
    "Nuxt.js": {
        "headers": {},
        "html_patterns": [
            "_nuxt/", "__nuxt", "nuxt",
        ],
        "cookies": [],
        "paths": [],
        "meta_patterns": [],
    },
    "Plesk": {
        "headers": {},
        "html_patterns": [
            "plesk", "PleskPanel",
        ],
        "cookies": [],
        "paths": ["/modules/"],
        "meta_patterns": [],
    },
    "cPanel": {
        "headers": {},
        "html_patterns": [
            "cPanel", "WHM",
        ],
        "cookies": [],
        "paths": ["/cpanel", "/whm"],
        "meta_patterns": [],
    },
    "phpBB": {
        "headers": {},
        "html_patterns": [
            "phpBB", "phpbb",
        ],
        "cookies": ["phpbb3_"],
        "paths": ["/forum/", "/community/"],
        "meta_patterns": [],
    },
    "vBulletin": {
        "headers": {},
        "html_patterns": [
            "vBulletin", "vbulletin",
        ],
        "cookies": ["bbuserid", "bbpassword"],
        "paths": ["/forum/"],
        "meta_patterns": [],
    },
}


class CMSDetector:

    def __init__(self, proxy: Optional[str] = None, timeout: int = 15):
        self.proxy = proxy
        self.timeout = timeout

    async def detect(self, url: str) -> dict:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        result = {
            "url": url,
            "detected_cms": [],
            "primary_cms": "Unknown",
            "confidence": "none",
            "technologies": [],
            "headers_checked": {},
            "html_checked": [],
            "cookies_found": [],
            "paths_checked": [],
            "error": "",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    url, proxy=self.proxy, ssl=False,
                    allow_redirects=True,
                    headers={"User-Agent": USER_AGENT},
                ) as resp:
                    html = await resp.text()
                    headers = dict(resp.headers)
                    cookies = list(resp.cookies.keys()) if resp.cookies else []

                    result["headers_checked"] = headers
                    result["status_code"] = resp.status

                    self._check_headers(headers, result)
                    self._check_html(html, result)
                    self._check_cookies(cookies, result)
                    self._check_meta(html, result)

                    await self._check_paths(session, url, result)

                    self._determine_primary(result)

        except aiohttp.ClientError as e:
            result["error"] = f"Connection error: {str(e)[:100]}"
        except asyncio.TimeoutError:
            result["error"] = "Request timed out"
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)[:100]}"

        return result

    def _check_headers(self, headers: dict, result: dict) -> None:
        headers_lower = {k.lower(): v for k, v in headers.items()}
        for cms_name, sig in CMS_SIGNATURES.items():
            for header_key, header_val in sig["headers"].items():
                if header_key.lower() in headers_lower:
                    actual_val = headers_lower[header_key.lower()]
                    if header_val.lower() in actual_val.lower() or not header_val:
                        result["detected_cms"].append({
                            "cms": cms_name,
                            "method": "header",
                            "detail": f"{header_key}: {actual_val[:80]}",
                            "confidence": "high",
                        })

    def _check_html(self, html: str, result: dict) -> None:
        html_lower = html.lower()
        for cms_name, sig in CMS_SIGNATURES.items():
            for pattern in sig["html_patterns"]:
                if pattern.lower() in html_lower:
                    result["html_checked"].append({
                        "cms": cms_name,
                        "pattern": pattern,
                    })
                    existing = [d for d in result["detected_cms"] if d["cms"] == cms_name]
                    if not existing:
                        result["detected_cms"].append({
                            "cms": cms_name,
                            "method": "html",
                            "detail": f"Pattern: {pattern[:60]}",
                            "confidence": "medium",
                        })
                    break

    def _check_cookies(self, cookies: list, result: dict) -> None:
        for cms_name, sig in CMS_SIGNATURES.items():
            for cookie_prefix in sig["cookies"]:
                for cookie in cookies:
                    if cookie.lower().startswith(cookie_prefix.lower()):
                        result["cookies_found"].append(cookie)
                        existing = [d for d in result["detected_cms"] if d["cms"] == cms_name]
                        if not existing:
                            result["detected_cms"].append({
                                "cms": cms_name,
                                "method": "cookie",
                                "detail": f"Cookie: {cookie}",
                                "confidence": "low",
                            })

    def _check_meta(self, html: str, result: dict) -> None:
        for cms_name, sig in CMS_SIGNATURES.items():
            for pattern in sig["meta_patterns"]:
                if pattern.lower() in html.lower():
                    existing = [d for d in result["detected_cms"] if d["cms"] == cms_name]
                    for item in existing:
                        if item["method"] == "meta":
                            break
                    else:
                        result["detected_cms"].append({
                            "cms": cms_name,
                            "method": "meta",
                            "detail": f"Meta: {pattern[:60]}",
                            "confidence": "medium",
                        })

    async def _check_paths(self, session: aiohttp.ClientSession, base_url: str, result: dict) -> None:
        paths_to_check = []
        for cms_name, sig in CMS_SIGNATURES.items():
            for path in sig["paths"]:
                paths_to_check.append((cms_name, path))

        for cms_name, path in paths_to_check:
            try:
                test_url = urljoin(base_url, path)
                timeout = aiohttp.ClientTimeout(total=8)
                async with session.get(
                    test_url, proxy=self.proxy, ssl=False,
                    allow_redirects=False, timeout=timeout,
                    headers={"User-Agent": USER_AGENT},
                ) as resp:
                    if resp.status in (200, 301, 302, 403):
                        result["paths_checked"].append({
                            "path": path,
                            "status": resp.status,
                            "cms": cms_name,
                        })
                        existing = [d for d in result["detected_cms"] if d["cms"] == cms_name]
                        if not existing:
                            result["detected_cms"].append({
                                "cms": cms_name,
                                "method": "path",
                                "detail": f"{path} -> {resp.status}",
                                "confidence": "medium",
                            })
            except Exception:
                pass

    def _determine_primary(self, result: dict) -> None:
        if not result["detected_cms"]:
            result["primary_cms"] = "Unknown"
            result["confidence"] = "none"
            return

        cms_scores = {}
        for detection in result["detected_cms"]:
            cms = detection["cms"]
            conf = detection["confidence"]
            if cms not in cms_scores:
                cms_scores[cms] = 0
            if conf == "high":
                cms_scores[cms] += 3
            elif conf == "medium":
                cms_scores[cms] += 2
            elif conf == "low":
                cms_scores[cms] += 1

        sorted_cms = sorted(cms_scores.items(), key=lambda x: x[1], reverse=True)
        result["primary_cms"] = sorted_cms[0][0]
        score = sorted_cms[0][1]
        if score >= 5:
            result["confidence"] = "high"
        elif score >= 3:
            result["confidence"] = "medium"
        else:
            result["confidence"] = "low"

        result["detected_cms"] = sorted(
            result["detected_cms"],
            key=lambda x: cms_scores.get(x["cms"], 0),
            reverse=True,
        )
