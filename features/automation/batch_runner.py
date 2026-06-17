
import asyncio
import logging
import time
from typing import Optional, Callable

logger = logging.getLogger("S9Checker")


class BatchStep:

    def __init__(self, name: str, tool_class, kwargs: dict | None = None):
        self.name = name
        self.tool_class = tool_class
        self.kwargs = kwargs or {}


class BatchRunner:

    def __init__(self, steps: list[BatchStep] | None = None):
        self.steps = steps or []
        self._results: list[dict] = []
        self._stop = False

    def add_step(self, name: str, tool_class, kwargs: dict | None = None):
        self.steps.append(BatchStep(name, tool_class, kwargs))

    def stop(self):
        self._stop = True

    async def run(self, target: str,
                   progress_callback: Callable | None = None) -> list[dict]:
        self._stop = False
        self._results = []
        total = len(self.steps)

        for i, step in enumerate(self.steps):
            if self._stop:
                break

            if progress_callback:
                await progress_callback({
                    "current": i + 1,
                    "total": total,
                    "step": step.name,
                    "percent": int((i / total) * 100),
                })

            logger.info(f"[Batch] Step {i + 1}/{total}: {step.name}")

            try:
                tool = step.tool_class()
                kwargs = dict(step.kwargs) if step.kwargs else {}
                kwargs["target"] = target

                start_time = time.time()
                result = await tool.run(**kwargs)
                elapsed = time.time() - start_time

                self._results.append({
                    "step": step.name,
                    "success": result.get("success", False),
                    "output": result.get("output", ""),
                    "error": result.get("error", ""),
                    "elapsed": round(elapsed, 2),
                })

                logger.info(f"[Batch] {step.name}: {'OK' if result.get('success') else 'FAILED'}")

            except Exception as e:
                self._results.append({
                    "step": step.name,
                    "success": False,
                    "output": "",
                    "error": str(e),
                    "elapsed": 0,
                })
                logger.error(f"[Batch] {step.name}: {e}")

        if progress_callback:
            await progress_callback({
                "current": total,
                "total": total,
                "step": "DONE",
                "percent": 100,
            })

        return self._results

    def get_results(self) -> list[dict]:
        return self._results

    def summary(self) -> dict:
        total = len(self._results)
        success = sum(1 for r in self._results if r.get("success"))
        failed = total - success
        total_time = sum(r.get("elapsed", 0) for r in self._results)
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "total_time": round(total_time, 2),
        }

    def save_results(self, filepath: str) -> int:
        with open(filepath, "w", encoding="utf-8") as f:
            for r in self._results:
                status = "OK" if r.get("success") else "FAIL"
                f.write(f"[{status}] {r['step']} ({r.get('elapsed', 0)}s)\n")
                if r.get("output"):
                    for line in r["output"].split("\n")[:50]:
                        f.write(f"  {line}\n")
                if r.get("error"):
                    f.write(f"  ERROR: {r['error']}\n")
                f.write("\n")
        return len(self._results)
