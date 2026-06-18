from __future__ import annotations
import os
import re
import asyncio
import aiohttp
import logging
from urllib.parse import urljoin, urlparse
from typing import Optional
from pathlib import Path

logger = logging.getLogger("S9Checker")


class WebScraper:

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    def __init__(self,
                 output_dir: str = "scraped_site",
                 proxy: Optional[str] = None,
                 timeout: int = 30):
        self.output_dir = output_dir
        self.proxy = proxy
        self.timeout = timeout
        self._downloaded = set()
        self._session = None

    async def _fetch(self, url: str) -> tuple[int, str]:
        headers = {"User-Agent": self.USER_AGENT}
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        try:
            async with self._session.get(url, headers=headers, timeout=timeout,
                                         proxy=self.proxy, ssl=False) as resp:
                text = await resp.text()
                return resp.status, text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return 0, ""

    async def _fetch_binary(self, url: str) -> tuple[int, bytes]:
        headers = {"User-Agent": self.USER_AGENT}
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        try:
            async with self._session.get(url, headers=headers, timeout=timeout,
                                         proxy=self.proxy, ssl=False) as resp:
                data = await resp.read()
                return resp.status, data
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return 0, b""

    def _save_file(self, filepath: str, content: str | bytes):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        mode = "wb" if isinstance(content, bytes) else "w"
        encoding = None if isinstance(content, bytes) else "utf-8"
        with open(filepath, mode, encoding=encoding) as f:
            f.write(content)

    def _url_to_filepath(self, url: str, base_url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if not path:
            path = "index.html"

        if "." not in os.path.basename(path):
            if "css" in url:
                path += ".css"
            elif "js" in url:
                path += ".js"
            elif any(ext in url for ext in [".png", ".jpg", ".gif", ".svg", ".ico"]):
                path += ".png"
            else:
                path += ".html"

        return os.path.join(self.output_dir, path)

    def _extract_css_urls(self, css_content: str, base_url: str) -> list[str]:
        urls = []
        url_pattern = r'url\(["\']?([^"\')\s]+)["\']?\)'
        for match in re.finditer(url_pattern, css_content):
            url = match.group(1)
            if url.startswith(("http://", "https://")):
                urls.append(url)
            elif url.startswith("//"):
                urls.append("https:" + url)
            elif url.startswith("/"):
                parsed = urlparse(base_url)
                urls.append(f"{parsed.scheme}://{parsed.netloc}{url}")
            else:
                urls.append(urljoin(base_url, url))

        import_pattern = r'@import\s+["\']([^"\']+)["\']'
        for match in re.finditer(import_pattern, css_content):
            url = match.group(1)
            if url.startswith(("http://", "https://")):
                urls.append(url)
            else:
                urls.append(urljoin(base_url, url))

        return urls

    def _extract_html_resources(self, html: str, base_url: str) -> dict:
        resources = {"css": [], "js": [], "images": []}

        css_pattern = r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\']'
        for match in re.finditer(css_pattern, html, re.IGNORECASE):
            url = match.group(1)
            if url.startswith(("http://", "https://")):
                resources["css"].append(url)
            elif url.startswith("//"):
                resources["css"].append("https:" + url)
            else:
                resources["css"].append(urljoin(base_url, url))

        js_pattern = r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']'
        for match in re.finditer(js_pattern, html, re.IGNORECASE):
            url = match.group(1)
            if url.startswith(("http://", "https://")):
                resources["js"].append(url)
            elif url.startswith("//"):
                resources["js"].append("https:" + url)
            else:
                resources["js"].append(urljoin(base_url, url))

        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        for match in re.finditer(img_pattern, html, re.IGNORECASE):
            url = match.group(1)
            if url.startswith(("http://", "https://")):
                resources["images"].append(url)
            elif url.startswith("//"):
                resources["images"].append("https:" + url)
            elif url.startswith("data:"):
                continue
            else:
                resources["images"].append(urljoin(base_url, url))

        return resources

    async def scrape(self, url: str, download_assets: bool = True) -> dict:
        self._downloaded = set()
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        connector = aiohttp.TCPConnector(limit=20, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            self._session = session

            status, html = await self._fetch(url)
            if status != 200:
                return {"error": f"HTTP {status}", "html": 0, "css": 0, "js": 0, "images": 0}

            html_path = os.path.join(self.output_dir, "index.html")
            self._save_file(html_path, html)

            summary = {"html": 1, "css": 0, "js": 0, "images": 0}

            if not download_assets:
                return summary

            resources = self._extract_html_resources(html, url)

            for css_url in resources["css"][:50]:
                if css_url in self._downloaded:
                    continue
                self._downloaded.add(css_url)

                css_status, css_content = await self._fetch(css_url)
                if css_status == 200 and css_content:
                    css_path = self._url_to_filepath(css_url, base_url)
                    self._save_file(css_path, css_content)
                    summary["css"] += 1

                    nested_urls = self._extract_css_urls(css_content, css_url)
                    for nested_url in nested_urls[:30]:
                        if nested_url in self._downloaded:
                            continue
                        self._downloaded.add(nested_url)

                        nested_status, nested_content = await self._fetch_binary(nested_url)
                        if nested_status == 200 and nested_content:
                            nested_path = self._url_to_filepath(nested_url, base_url)
                            self._save_file(nested_path, nested_content)
                            if "css" in nested_url:
                                summary["css"] += 1
                            else:
                                summary["images"] += 1

            for js_url in resources["js"][:50]:
                if js_url in self._downloaded:
                    continue
                self._downloaded.add(js_url)

                js_status, js_content = await self._fetch(js_url)
                if js_status == 200 and js_content:
                    js_path = self._url_to_filepath(js_url, base_url)
                    self._save_file(js_path, js_content)
                    summary["js"] += 1

            for img_url in resources["images"][:100]:
                if img_url in self._downloaded:
                    continue
                self._downloaded.add(img_url)

                img_status, img_data = await self._fetch_binary(img_url)
                if img_status == 200 and img_data:
                    img_path = self._url_to_filepath(img_url, base_url)
                    self._save_file(img_path, img_data)
                    summary["images"] += 1

            self._session = None
            return summary
