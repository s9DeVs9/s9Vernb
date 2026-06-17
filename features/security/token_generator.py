
import json
import time
import hmac
import hashlib
import base64
import logging
from typing import Optional

logger = logging.getLogger("S9Checker")


class TokenGenerator:

    def __init__(self):
        pass

    def _b64url_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    def _b64url_decode(self, s: str) -> bytes:
        padding = 4 - len(s) % 4
        s += "=" * padding
        return base64.urlsafe_b64decode(s)

    def generate_jwt(self, payload: dict, secret: str,
                      algorithm: str = "HS256",
                      expires_in: int = 3600) -> str:
        header = {"alg": algorithm, "typ": "JWT"}

        now = int(time.time())
        full_payload = {
            "iat": now,
            "exp": now + expires_in,
            **payload,
        }

        header_b64 = self._b64url_encode(json.dumps(header).encode())
        payload_b64 = self._b64url_encode(json.dumps(full_payload).encode())
        signing_input = f"{header_b64}.{payload_b64}"

        if algorithm == "HS256":
            signature = hmac.new(secret.encode(), signing_input.encode(),
                                 hashlib.sha256).digest()
        elif algorithm == "HS512":
            signature = hmac.new(secret.encode(), signing_input.encode(),
                                 hashlib.sha512).digest()
        else:
            signature = hmac.new(secret.encode(), signing_input.encode(),
                                 hashlib.sha256).digest()

        signature_b64 = self._b64url_encode(signature)
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def decode_jwt(self, token: str) -> dict:
        parts = token.split(".")
        if len(parts) != 3:
            return {"error": "Invalid token format (expected 3 parts)"}

        try:
            header = json.loads(self._b64url_decode(parts[0]))
            payload = json.loads(self._b64url_decode(parts[1]))
            return {"header": header, "payload": payload, "valid_format": True}
        except Exception as e:
            return {"error": f"Failed to decode: {e}", "valid_format": False}

    def validate_jwt(self, token: str, secret: str,
                      algorithm: str = "HS256") -> dict:
        parts = token.split(".")
        if len(parts) != 3:
            return {"valid": False, "error": "Invalid token format"}

        signing_input = f"{parts[0]}.{parts[1]}"

        if algorithm == "HS256":
            expected_sig = hmac.new(secret.encode(), signing_input.encode(),
                                    hashlib.sha256).digest()
        elif algorithm == "HS512":
            expected_sig = hmac.new(secret.encode(), signing_input.encode(),
                                    hashlib.sha512).digest()
        else:
            expected_sig = hmac.new(secret.encode(), signing_input.encode(),
                                    hashlib.sha256).digest()

        expected_b64 = self._b64url_encode(expected_sig)
        signature_valid = hmac.compare_digest(parts[2], expected_b64)

        decoded = self.decode_jwt(token)
        payload = decoded.get("payload", {})
        expired = payload.get("exp", 0) < time.time()

        return {
            "valid": signature_valid and not expired,
            "signature_valid": signature_valid,
            "expired": expired,
            "payload": payload,
        }

    def generate_api_key(self, length: int = 32) -> str:
        import secrets
        return secrets.token_urlsafe(length)

    def generate_session_token(self, length: int = 64) -> str:
        import secrets
        return secrets.token_hex(length // 2)

    def generate_random_secret(self, length: int = 64) -> str:
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))
