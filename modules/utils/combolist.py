
import os
import time
import logging
from typing import Optional
from collections import Counter

from core.config import COMBOLIST_DIR, OUTPUT_ENCODING

logger = logging.getLogger("S9Checker")


class ComboList:

    def __init__(self, name: str = "default", filepath: Optional[str] = None):
        self.name = name
        self.filepath = filepath
        self.combos: list[tuple[str, str]] = []
        self.created_at = time.time()
        self.metadata: dict = {}

    def load(self, filepath: str) -> int:
        self.filepath = filepath
        self.combos = []
        seen = set()

        try:
            with open(filepath, "r", encoding=OUTPUT_ENCODING, errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or ":" not in line:
                        continue
                    parts = line.split(":", 1)
                    if len(parts) != 2:
                        continue
                    email, password = parts[0].strip(), parts[1].strip()
                    if not email or not password:
                        continue
                    key = f"{email}:{password}"
                    if key not in seen:
                        seen.add(key)
                        self.combos.append((email, password))
        except Exception as e:
            logger.error(f"Failed to load combolist: {e}")
            return 0

        logger.info(f"Loaded {len(self.combos)} combos from {os.path.basename(filepath)}")
        return len(self.combos)

    def save(self, filepath: Optional[str] = None) -> bool:
        target = filepath or self.filepath
        if not target:
            logger.error("No filepath specified for save")
            return False

        try:
            os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
            with open(target, "w", encoding=OUTPUT_ENCODING) as f:
                for email, password in self.combos:
                    f.write(f"{email}:{password}\n")
            self.filepath = target
            logger.info(f"Saved {len(self.combos)} combos to {target}")
            return True
        except Exception as e:
            logger.error(f"Failed to save combolist: {e}")
            return False

    def add(self, email: str, password: str) -> bool:
        key = f"{email}:{password}"
        existing = {f"{e}:{p}" for e, p in self.combos}
        if key in existing:
            return False
        self.combos.append((email, password))
        return True

    def remove(self, email: str) -> int:
        before = len(self.combos)
        self.combos = [(e, p) for e, p in self.combos if e != email]
        return before - len(self.combos)

    def merge(self, other: "ComboList") -> int:
        existing = {f"{e}:{p}" for e, p in self.combos}
        added = 0
        for email, password in other.combos:
            key = f"{email}:{password}"
            if key not in existing:
                self.combos.append((email, password))
                existing.add(key)
                added += 1
        return added

    def deduplicate(self) -> int:
        seen = set()
        unique = []
        for email, password in self.combos:
            key = f"{email}:{password}"
            if key not in seen:
                seen.add(key)
                unique.append((email, password))
        removed = len(self.combos) - len(unique)
        self.combos = unique
        return removed

    def filter_by_domain(self, domain: str) -> "ComboList":
        filtered = ComboList(name=f"{self.name}_{domain}")
        filtered.combos = [(e, p) for e, p in self.combos if e.lower().endswith(f"@{domain.lower()}")]
        return filtered

    def get_domains(self) -> dict[str, int]:
        domains = Counter()
        for email, _ in self.combos:
            if "@" in email:
                domain = email.split("@")[-1].lower()
                domains[domain] += 1
        return dict(domains.most_common())

    def stats(self) -> dict:
        domains = self.get_domains()
        return {
            "name": self.name,
            "total": len(self.combos),
            "unique": len(self.combos),
            "domains": len(domains),
            "top_domains": dict(list(domains.items())[:5]),
            "filepath": self.filepath,
        }

    def preview(self, n: int = 10) -> list[tuple[str, str]]:
        return self.combos[:n]

    def __len__(self):
        return len(self.combos)

    def __repr__(self):
        return f"ComboList(name={self.name!r}, combos={len(self.combos)})"


def scan_combolists(directory: str = COMBOLIST_DIR) -> list[str]:
    results = []
    if not os.path.isdir(directory):
        return results
    for fname in sorted(os.listdir(directory)):
        if fname.endswith(".txt"):
            results.append(os.path.join(directory, fname))
    return results
