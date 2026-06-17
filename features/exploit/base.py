
import asyncio
import shutil
import logging

logger = logging.getLogger("S9Checker")


class ToolWrapper:
    NAME = ""
    BINARY = ""
    DESCRIPTION = ""

    def is_installed(self) -> bool:
        return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        if not self.is_installed():
            return f"{self.BINARY} is not installed or not in PATH"
        return f"{self.NAME} - {self.DESCRIPTION}"

    def build_command(self, **kwargs) -> list[str]:
        raise NotImplementedError

    async def run(self, **kwargs) -> dict:
        if not self.is_installed():
            return {"success": False, "output": "", "error": f"{self.BINARY} is not installed"}

        cmd = self.build_command(**kwargs)
        logger.info(f"Running {self.NAME}: {' '.join(cmd)}")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=kwargs.get("timeout", 300))
            return {
                "success": proc.returncode == 0,
                "output": stdout.decode(errors="replace"),
                "error": stderr.decode(errors="replace"),
            }
        except asyncio.TimeoutError:
            proc.kill()
            return {"success": False, "output": "", "error": f"{self.NAME} timed out"}
        except FileNotFoundError:
            return {"success": False, "output": "", "error": f"{self.BINARY} not found in PATH"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
