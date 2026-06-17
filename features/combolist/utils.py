
import os
import logging

from core.config import COMBOLIST_DIR

logger = logging.getLogger("S9Checker")


def scan_combolists(directory: str = COMBOLIST_DIR) -> list[str]:
    results = []
    if not os.path.isdir(directory):
        return results
    for fname in sorted(os.listdir(directory)):
        if fname.endswith(".txt"):
            results.append(os.path.join(directory, fname))
    return results
