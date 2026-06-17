
import random
import string


class PasswordGenerator:

    def __init__(self,
                 length: int = 16,
                 uppercase: bool = True,
                 lowercase: bool = True,
                 digits: bool = True,
                 symbols: bool = True,
                 exclude_ambiguous: bool = False):
        self.length = max(4, min(128, length))
        self.uppercase = uppercase
        self.lowercase = lowercase
        self.digits = digits
        self.symbols = symbols
        self.exclude_ambiguous = exclude_ambiguous

    def _get_charset(self) -> str:
        chars = ""
        if self.uppercase:
            chars += string.ascii_uppercase
        if self.lowercase:
            chars += string.ascii_lowercase
        if self.digits:
            chars += string.digits
        if self.symbols:
            chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        if self.exclude_ambiguous:
            ambiguous = "Il1O0o"
            chars = "".join(c for c in chars if c not in ambiguous)
        return chars

    def generate_one(self) -> str:
        charset = self._get_charset()
        if not charset:
            return ""
        password = []
        if self.uppercase:
            password.append(random.choice(string.ascii_uppercase))
        if self.lowercase:
            password.append(random.choice(string.ascii_lowercase))
        if self.digits:
            password.append(random.choice(string.digits))
        if self.symbols:
            password.append(random.choice("!@#$%^&*()-_=+[]{}|;:,.<>?"))
        while len(password) < self.length:
            password.append(random.choice(charset))
        random.shuffle(password)
        return "".join(password[:self.length])

    def generate_batch(self, count: int = 100) -> list[str]:
        return [self.generate_one() for _ in range(max(1, count))]

    def estimate_strength(self, password: str) -> dict:
        pool = 0
        if any(c in string.ascii_uppercase for c in password):
            pool += 26
        if any(c in string.ascii_lowercase for c in password):
            pool += 26
        if any(c in string.digits for c in password):
            pool += 10
        if any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password):
            pool += 24
        entropy = len(password) * (pool.bit_length() if pool > 0 else 0)
        if entropy < 40:
            strength = "WEAK"
        elif entropy < 60:
            strength = "FAIR"
        elif entropy < 80:
            strength = "STRONG"
        else:
            strength = "VERY STRONG"
        return {
            "length": len(password),
            "pool_size": pool,
            "entropy_bits": entropy,
            "strength": strength,
        }
