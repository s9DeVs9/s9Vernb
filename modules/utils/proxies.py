
import logging

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


def load_proxies(filepath: str) -> list:
    proxies = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    proxies.append(line)
        logger.info(f"Loaded {len(proxies)} proxies")
    except FileNotFoundError:
        logger.warning(f"Proxy file not found: {filepath}")
    return proxies
