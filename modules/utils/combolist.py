"""
Combolist manager for S9Checker.
Handles loading, saving, merging, deduplication, and filtering of combo lists.
Combos are stored as (email, password) tuples.
"""

import os
import time
import logging
from typing import Optional
from collections import Counter

from core.config import COMBOLIST_DIR, OUTPUT_ENCODING

logger = logging.getLogger("S9Checker")


class ComboList:
    """A named list of email:password combos with file persistence."""

    def __init__(self, name: str = "default", filepath: Optional[str] = None):
        self.name = name
        self.filepath = filepath
        self.combos: list[tuple[str, str]] = []
        self.created_at = time.time()
        self.metadata: dict = {}

    # -------------------------------------------------------------------
    # Loading
    # -------------------------------------------------------------------
    def load(self, filepath: str) -> int:
        """Load combos from a file. Returns count of loaded entries."""
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

    # -------------------------------------------------------------------
    # Saving
    # -------------------------------------------------------------------
    def save(self, filepath: Optional[str] = None) -> bool:
        """Save combos to a file."""
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

    # -------------------------------------------------------------------
    # Manipulation
    # -------------------------------------------------------------------
    def add(self, email: str, password: str) -> bool:
        """Add a single combo. Returns True if added, False if duplicate."""
        key = f"{email}:{password}"
        existing = {f"{e}:{p}" for e, p in self.combos}
        if key in existing:
            return False
        self.combos.append((email, password))
        return True

    def remove(self, email: str) -> int:
        """Remove all combos with this email. Returns count removed."""
        before = len(self.combos)
        self.combos = [(e, p) for e, p in self.combos if e != email]
        return before - len(self.combos)

    def merge(self, other: "ComboList") -> int:
        """Merge another ComboList into this one. Returns count of new entries added."""
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
        """Remove duplicate combos. Returns count removed."""
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
        """Return a new ComboList containing only combos with emails from this domain."""
        filtered = ComboList(name=f"{self.name}_{domain}")
        filtered.combos = [(e, p) for e, p in self.combos if e.lower().endswith(f"@{domain.lower()}")]
        return filtered

    def get_domains(self) -> dict[str, int]:
        """Return a dict of email domains and their counts."""
        domains = Counter()
        for email, _ in self.combos:
            if "@" in email:
                domain = email.split("@")[-1].lower()
                domains[domain] += 1
        return dict(domains.most_common())

    # -------------------------------------------------------------------
    # Stats & Preview
    # -------------------------------------------------------------------
    def stats(self) -> dict:
        """Return summary statistics."""
        domains = self.get_domains()
        return {
            "name": self.name,
            "total": len(self.combos),
            "unique": len(self.combos),  # Already deduplicated on load
            "domains": len(domains),
            "top_domains": dict(list(domains.items())[:5]),
            "filepath": self.filepath,
        }

    def preview(self, n: int = 10) -> list[tuple[str, str]]:
        """Return the first N combos for preview."""
        return self.combos[:n]

    def __len__(self):
        return len(self.combos)

    def __repr__(self):
        return f"ComboList(name={self.name!r}, combos={len(self.combos)})"


# -------------------------------------------------------------------
# Utility: scan a directory for combolist files
# -------------------------------------------------------------------
def scan_combolists(directory: str = COMBOLIST_DIR) -> list[str]:
    """Scan a directory for .txt files that look like combolists."""
    results = []
    if not os.path.isdir(directory):
        return results
    for fname in sorted(os.listdir(directory)):
        if fname.endswith(".txt"):
            results.append(os.path.join(directory, fname))
    return results
