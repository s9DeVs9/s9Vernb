
import asyncio
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger("S9Checker")


PLATFORMS = [
    {
        "name": "Instagram",
        "url": "https://www.instagram.com/{username}/",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "social",
    },
    {
        "name": "Twitter/X",
        "url": "https://x.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "social",
    },
    {
        "name": "TikTok",
        "url": "https://www.tiktok.com/@{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "social",
    },
    {
        "name": "YouTube",
        "url": "https://www.youtube.com/@{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "video",
    },
    {
        "name": "Reddit",
        "url": "https://www.reddit.com/user/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "social",
    },
    {
        "name": "Pinterest",
        "url": "https://www.pinterest.com/{username}/",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "social",
    },
    {
        "name": "LinkedIn",
        "url": "https://www.linkedin.com/in/{username}/",
        "check_type": "status",
        "found_codes": [200, 302],
        "not_found_codes": [404],
        "category": "professional",
    },
    {
        "name": "GitHub",
        "url": "https://github.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "dev",
    },
    {
        "name": "GitLab",
        "url": "https://gitlab.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "dev",
    },
    {
        "name": "Twitch",
        "url": "https://www.twitch.tv/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "streaming",
    },
    {
        "name": "Steam",
        "url": "https://steamcommunity.com/id/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "gaming",
    },
    {
        "name": "DeviantArt",
        "url": "https://www.deviantart.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "art",
    },
    {
        "name": "Tumblr",
        "url": "https://{username}.tumblr.com/",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "social",
    },
    {
        "name": "Medium",
        "url": "https://medium.com/@{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "blogging",
    },
    {
        "name": "Spotify",
        "url": "https://open.spotify.com/user/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "music",
    },
    {
        "name": "SoundCloud",
        "url": "https://soundcloud.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "music",
    },
    {
        "name": "Flickr",
        "url": "https://www.flickr.com/people/{username}/",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "photo",
    },
    {
        "name": "VK",
        "url": "https://vk.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "social",
    },
    {
        "name": "Telegram",
        "url": "https://t.me/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "messaging",
    },
    {
        "name": "Keybase",
        "url": "https://keybase.io/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "crypto",
    },
    {
        "name": "About.me",
        "url": "https://about.me/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "personal",
    },
    {
        "name": "Patreon",
        "url": "https://www.patreon.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "creator",
    },
    {
        "name": "Blogger",
        "url": "https://{username}.blogspot.com/",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "blogging",
    },
    {
        "name": "WordPress.com",
        "url": "https://{username}.wordpress.com/",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "blogging",
    },
    {
        "name": "HackerOne",
        "url": "https://hackerone.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "security",
    },
    {
        "name": "Bugcrowd",
        "url": "https://bugcrowd.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "security",
    },
    {
        "name": "LeetCode",
        "url": "https://leetcode.com/{username}/",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "dev",
    },
    {
        "name": "HackerRank",
        "url": "https://www.hackerrank.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "dev",
    },
    {
        "name": "Codeforces",
        "url": "https://codeforces.com/profile/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "dev",
    },
    {
        "name": "Replit",
        "url": "https://replit.com/@{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "dev",
    },
    {
        "name": "Fiverr",
        "url": "https://www.fiverr.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "freelance",
    },
    {
        "name": "Upwork",
        "url": "https://www.upwork.com/freelancers/~{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "freelance",
    },
    {
        "name": "Etsy",
        "url": "https://www.etsy.com/people/@{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "shop",
    },
    {
        "name": "Gravatar",
        "url": "https://en.gravatar.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "identity",
    },
    {
        "name": "Roblox",
        "url": "https://www.roblox.com/user.aspx?username={username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "gaming",
    },
    {
        "name": "Minecraft",
        "url": "https://namemc.com/profile/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "gaming",
    },
    {
        "name": "Chess.com",
        "url": "https://www.chess.com/member/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "gaming",
    },
    {
        "name": "Duolingo",
        "url": "https://www.duolingo.com/profile/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "education",
    },
    {
        "name": "Kaggle",
        "url": "https://www.kaggle.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "data",
    },
    {
        "name": "ProductHunt",
        "url": "https://www.producthunt.com/@{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "tech",
    },
    {
        "name": "Dribbble",
        "url": "https://dribbble.com/{username}",
        "check_type": "status",
        "found_codes": [200],
        "not_found_codes": [404],
        "category": "design",
    },
]


class SocialMediaScanner:

    def __init__(self, proxy: Optional[str] = None, timeout: int = 10):
        self.proxy = proxy
        self.timeout = timeout

    async def scan(self, username: str, platforms: Optional[list[str]] = None,
                   max_concurrent: int = 20) -> dict:
        targets = PLATFORMS
        if platforms:
            targets = [p for p in PLATFORMS if p["name"].lower() in
                       [x.lower() for x in platforms]]

        result: dict = {
            "username": username,
            "found": [],
            "not_found": [],
            "errors": [],
            "total_scanned": len(targets),
        }

        semaphore = asyncio.Semaphore(max_concurrent)
        connector = aiohttp.TCPConnector(limit=max_concurrent, ssl=False)

        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self._check_platform(session, semaphore, username, p)
                     for p in targets]
            outcomes = await asyncio.gather(*tasks, return_exceptions=True)

            for outcome in outcomes:
                if isinstance(outcome, Exception):
                    result["errors"].append(str(outcome)[:100])
                elif outcome:
                    if result["found"]:
                        result["found"].append(outcome)
                    else:
                        result["not_found"].append(outcome)

        return result

    async def _check_platform(self, session: aiohttp.ClientSession,
                               semaphore: asyncio.Semaphore,
                               username: str, platform: dict) -> dict:
        url = platform["url"].format(username=username)
        info = {
            "name": platform["name"],
            "url": url,
            "category": platform["category"],
            "found": False,
            "status_code": 0,
            "redirect_url": "",
        }

        try:
            async with semaphore:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with session.get(
                    url, timeout=timeout, proxy=self.proxy, ssl=False,
                    allow_redirects=False,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                ) as resp:
                    info["status_code"] = resp.status
                    if resp.status in platform["found_codes"]:
                        info["found"] = True
                    elif resp.status in (301, 302, 303, 307, 308):
                        info["redirect_url"] = resp.headers.get("Location", "")
                    elif resp.status not in platform["not_found_codes"]:
                        if resp.status < 400:
                            info["found"] = True
        except asyncio.TimeoutError:
            info["status_code"] = 0
        except aiohttp.ClientError:
            info["status_code"] = 0
        except Exception:
            info["status_code"] = 0

        return info
