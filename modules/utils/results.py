
import asyncio
import time
import logging
import os

from core.utils import ResultStatus

logger = logging.getLogger("S9Checker")


class ResultsManager:

    def __init__(self, output_dir: str = "."):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.results = []
        self.valid = []
        self.invalid = []
        self.errors = []
        self._lock = asyncio.Lock()

    async def add_result(self, email: str, password: str, platform: str,
                         status: str, details: str = ""):
        result = {
            "email": email,
            "password": password,
            "platform": platform,
            "status": status,
            "details": details,
            "timestamp": time.time(),
        }
        async with self._lock:
            self.results.append(result)

            if status == ResultStatus.VALID:
                self.valid.append(result)
                self._append_file("hits.txt", f"[{platform}] {email}:{password} -> VALID\n")
                self._append_file(
                    f"hits_{platform.lower().replace(' ', '_').replace('+', 'p')}.txt",
                    f"{email}:{password}\n"
                )
            elif status in (ResultStatus.INVALID,):
                self.invalid.append(result)
            else:
                self.errors.append(result)

            self._append_file(
                "results.txt",
                f"[{platform}] {email}:{password} -> {status}"
                f"{' | ' + details if details else ''}\n"
            )

    def _append_file(self, filename: str, line: str):
        try:
            with open(f"{self.output_dir}/{filename}", "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            logger.error(f"Failed to write to {filename}: {e}")

    def get_stats(self) -> dict:
        return {
            "total": len(self.results),
            "valid": len(self.valid),
            "invalid": len(self.invalid),
            "errors": len(self.errors),
        }
