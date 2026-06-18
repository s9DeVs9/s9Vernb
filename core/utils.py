
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger("S9Checker")


class ResultStatus:
    VALID = "VALID"
    INVALID = "INVALID"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    BLOCKED = "BLOCKED"
    RATE_LIMITED = "RATE_LIMITED"


def parse_combolist(filepath: str) -> list:
    combos = []
    seen = set()
    line_count = 0

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            line_count += 1
            if not line or ":" not in line:
                continue

            parts = line.split(":", 1)
            if len(parts) != 2:
                continue

            email, password = parts[0].strip(), parts[1].strip()
            if not email or not password or "@" not in email:
                continue

            key = f"{email}:{password}"
            if key in seen:
                continue
            seen.add(key)
            combos.append((email, password))

    logger.info(f"Parsed {len(combos)} unique combos from {line_count} lines")
    return combos


def parse_proxy_line(line: str) -> dict | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    if "://" in line:
        try:
            parsed = urlparse(line)
            host = parsed.hostname
            port = parsed.port
            user = parsed.username or None
            pwd = parsed.password or None
            if host and port:
                return {"host": host, "port": port, "user": user, "pass": pwd}
        except Exception:
            pass
        return None

    parts = line.split(":")
    if len(parts) < 2:
        return None

    try:
        host = parts[0].strip()
        port = int(parts[1].strip())
        user = parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
        pwd = parts[3].strip() if len(parts) > 3 and parts[3].strip() else None
        if host and 1 <= port <= 65535:
            return {"host": host, "port": port, "user": user, "pass": pwd}
    except (ValueError, IndexError):
        pass
    return None


def load_proxies(filepath: str) -> list:
    proxies = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parsed = parse_proxy_line(line)
                if parsed:
                    proxies.append(parsed)
        logger.info(f"Loaded {len(proxies)} proxies from {filepath}")
    except FileNotFoundError:
        logger.warning(f"Proxy file not found: {filepath}")
    return proxies
