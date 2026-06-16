
import shutil
import asyncio
import logging

logger = logging.getLogger("S9Checker")


class ToolWrapper:
    NAME = "subfinder"
    BINARY = "subfinder"
    DESCRIPTION = "Subfinder - fast passive subdomain enumeration tool"

    def is_installed(self) -> bool:
        return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        if not self.is_installed():
            return "subfinder is not installed. Install from https://github.com/projectdiscovery/subfinder"
        return "Subfinder - a subdomain discovery tool that uses passive online sources"

    def build_command(
        self,
        domain: str,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        cmd = [
            self.BINARY,
            "-d", domain,
            "-silent",
        ]
        if extra_args:
            cmd.extend(extra_args)
        return cmd

    async def run(
        self,
        domain: str,
        extra_args: list[str] | None = None,
        timeout: int = 300,
    ) -> dict:
        if not self.is_installed():
            return {"success": False, "output": "", "error": "subfinder is not installed"}

        cmd = self.build_command(domain, extra_args)
        logger.info(f"Running subfinder: {' '.join(cmd)}")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            output = stdout.decode(errors="replace")
            error = stderr.decode(errors="replace")
            return {
                "success": proc.returncode == 0,
                "output": output,
                "error": error,
            }
        except asyncio.TimeoutError:
            proc.kill()
            return {"success": False, "output": "", "error": "subfinder timed out"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
