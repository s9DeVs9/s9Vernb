
import random
import string

CODE_CHARS = string.ascii_letters + string.digits


def generate_nitro_code(length: int = 16) -> str:
    return "".join(random.choices(CODE_CHARS, k=length))


def generate_nitro_url(code: str) -> str:
    return f"https://discord.gift/{code}"


def generate_boost_code(length: int = 16) -> str:
    return "".join(random.choices(CODE_CHARS, k=length))


def generate_boost_url(code: str) -> str:
    return f"https://discord.gift/{code}"


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
    template = PROMO_TEMPLATES.get(promo_type, PROMO_TEMPLATES["Generic"])
    prefix = template["prefix"]
    remaining = template["length"] - len(prefix)
    if remaining < 4:
        remaining = 12
    suffix = "".join(random.choices(template["charset"], k=remaining))
    return f"{prefix}{suffix}"
