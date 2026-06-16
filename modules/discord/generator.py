"""
Discord code generators — Nitro, Boost, Promo codes.
Generates random codes using Discord's known formats.
"""

import random
import string

# ── Character sets ───────────────────────────────────────────────────────────
# Discord gift codes use base-62 (a-z, A-Z, 0-9)
CODE_CHARS = string.ascii_letters + string.digits


# ── Nitro generators ────────────────────────────────────────────────────────
def generate_nitro_code(length: int = 16) -> str:
    """Generate a random Discord Nitro gift code."""
    return "".join(random.choices(CODE_CHARS, k=length))


def generate_nitro_url(code: str) -> str:
    """Wrap a code into a full Discord gift URL."""
    return f"https://discord.gift/{code}"


# ── Boost generators ────────────────────────────────────────────────────────
def generate_boost_code(length: int = 16) -> str:
    """Generate a random Discord Server Boost gift code."""
    return "".join(random.choices(CODE_CHARS, k=length))


def generate_boost_url(code: str) -> str:
    """Wrap a boost code into a full Discord gift URL."""
    return f"https://discord.gift/{code}"


# ── Promo code templates ────────────────────────────────────────────────────
PROMO_TEMPLATES = {
    "OperaGX": {
        "prefix": "opera",
        "length": 24,
        "description": "OperaGX x Discord Nitro promotion",
        "charset": string.ascii_lowercase + string.digits,
    },
    "PlayStation": {
        "prefix": "ps",
        "length": 20,
        "description": "PlayStation x Discord Nitro promotion",
        "charset": string.ascii_uppercase + string.digits,
    },
    "Xbox": {
        "prefix": "xb",
        "length": 20,
        "description": "Xbox x Discord Nitro promotion",
        "charset": string.ascii_uppercase + string.digits,
    },
    "EpicGames": {
        "prefix": "epic",
        "length": 24,
        "description": "Epic Games x Discord Nitro promotion",
        "charset": string.ascii_lowercase + string.digits,
    },
    "Samsung": {
        "prefix": "sam",
        "length": 20,
        "description": "Samsung x Discord Nitro promotion",
        "charset": string.ascii_lowercase + string.digits,
    },
    "Prime": {
        "prefix": "prime",
        "length": 24,
        "description": "Amazon Prime x Discord Nitro promotion",
        "charset": string.ascii_lowercase + string.digits,
    },
    "Generic": {
        "prefix": "",
        "length": 16,
        "description": "Generic Nitro promo code",
        "charset": CODE_CHARS,
    },
}


def generate_promo_code(promo_type: str = "Generic") -> str:
    """Generate a promo code for a specific promotion type."""
    template = PROMO_TEMPLATES.get(promo_type, PROMO_TEMPLATES["Generic"])
    prefix = template["prefix"]
    remaining = template["length"] - len(prefix)
    if remaining < 4:
        remaining = 12
    suffix = "".join(random.choices(template["charset"], k=remaining))
    return f"{prefix}{suffix}"
