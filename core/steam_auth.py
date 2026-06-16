
import aiohttp
import json
import time
import logging
from base64 import b64encode
from typing import Optional

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

from core.utils import ResultStatus

logger = logging.getLogger("S9Checker")


async def get_rsa_key(session: aiohttp.ClientSession,
                       username: str, proxy: Optional[str] = None) -> dict:
    data = {
        "username": username,
        "donotcache": str(int(time.time() * 1000)),
    }
    timeout = aiohttp.ClientTimeout(total=15)
    async with session.post(
        "https://steamcommunity.com/login/getrsakey/",
        data=data,
        timeout=timeout,
        proxy=proxy,
    ) as resp:
        return await resp.json(content_type=None)


def encrypt_password(rsa_data: dict, password: str) -> str:
    pub_mod = int(rsa_data["publickey_mod"], 16)
    pub_exp = int(rsa_data["publickey_exp"], 16)
    key = RSA.construct((pub_mod, pub_exp))
    cipher = PKCS1_v1_5.new(key)
    encrypted = cipher.encrypt(password.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def build_steam_payload(username: str, encrypted_password: str,
                         rsa_timestamp: str) -> dict:
    return {
        "username": username,
        "password": encrypted_password,
        "emailauth": "",
        "emailsteamid": "",
        "twofactorcode": "",
        "captchagid": "-1",
        "captcha_text": "",
        "loginfriendlyname": "python-steam",
        "rsatimestamp": rsa_timestamp,
        "remember_login": "true",
        "donotcache": str(int(time.time() * 1000)),
    }


def parse_steam_response(text: str) -> tuple[str, str]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return ResultStatus.ERROR, "Invalid JSON response"

    success = data.get("success", False)
    login_complete = data.get("login_complete", False)

    if success and login_complete:
        return ResultStatus.VALID, "Login successful"

    if data.get("captcha_needed"):
        return ResultStatus.BLOCKED, "Captcha required"

    if data.get("emailauth_needed"):
        return ResultStatus.BLOCKED, "SteamGuard email code required"

    if data.get("requires_twofactor"):
        return ResultStatus.BLOCKED, "SteamGuard 2FA required"

    message = data.get("message", "").lower()
    if "incorrect" in message or "invalid" in message:
        return ResultStatus.INVALID, f"Invalid credentials: {data.get('message', '')}"

    if "too many" in message:
        return ResultStatus.RATE_LIMITED, "Too many login failures"

    return ResultStatus.INVALID, data.get("message", "Login failed")
