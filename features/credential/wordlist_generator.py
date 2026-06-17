
import random
import string
import itertools


class WordlistGenerator:

    LEET_MAP = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}

    def __init__(self):
        self.words: list[str] = []
        self._seen: set[str] = set()

    def _add(self, word: str):
        w = word.strip()
        if w and w not in self._seen:
            self._seen.add(w)
            self.words.append(w)

    def generate_from_name(self, name: str, years: list[str] | None = None) -> list[str]:
        name = name.strip().lower()
        if not name:
            return []

        base_words = [name, name.capitalize(), name.upper()]
        separators = ["", ".", "_", "-", "@"]
        suffixes = ["", "123", "1234", "!", "!!", "1", "01", "007", "12", "69"]
        years = years or ["2024", "2025", "2026"]

        for base in base_words:
            for sep in separators:
                for suffix in suffixes:
                    self._add(f"{base}{sep}{suffix}")

        for base in base_words:
            for year in years:
                self._add(f"{base}{year}")
                self._add(f"{base}_{year}")

        for base in base_words:
            self._add(f"{base}!")
            self._add(f"{base}1!")
            self._add(f"{base}@")
            self._add(f"{base}#")

        return self.words

    def generate_from_domain(self, domain: str) -> list[str]:
        domain = domain.strip().lower()
        if not domain:
            return []

        parts = domain.replace(".", " ").split()
        for part in parts:
            if len(part) > 2:
                self.generate_from_name(part)

        admin_words = ["admin", "root", "test", "user", "guest"]
        for admin in admin_words:
            self._add(f"{admin}@{domain}")
            self._add(f"{admin}123")
            self._add(f"{admin}!")

        return self.words

    def generate_from_names(self, names: list[str]) -> list[str]:
        for name in names:
            self.generate_from_name(name)
        return self.words

    def apply_leet(self) -> list[str]:
        leet_words = []
        for word in list(self.words):
            leet = ""
            for c in word:
                leet += self.LEET_MAP.get(c, c)
            if leet != word:
                leet_words.append(leet)
                self._add(leet)
        return leet_words

    def apply_mutations(self, words: list[str] | None = None) -> list[str]:
        source = words or list(self.words)
        mutations = []
        for word in source:
            mutations.append(word[::-1])
            mutations.append(word * 2)
            mutations.append(word.capitalize() + "1")
        for m in mutations:
            self._add(m)
        return self.words

    def get_wordlist(self) -> list[str]:
        return list(self.words)

    def save(self, filepath: str) -> int:
        with open(filepath, "w", encoding="utf-8") as f:
            for w in self.words:
                f.write(w + "\n")
        return len(self.words)
