
import shutil
import asyncio
import logging

logger = logging.getLogger("S9Checker")


class ToolWrapper:
    NAME = "httpx"
    BINARY = "httpx"
    DESCRIPTION = "httpx - fast and multi-purpose HTTP toolkit for probing web servers"

    def is_installed(self) -> bool:
        return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        if not self.is_installed():
            return "httpx is not installed. Install from https://github.com/projectdiscovery/httpx"
        return "httpx - A fast and multi-purpose HTTP toolkit that allows running multiple probes"

    def build_command(
        self,
        targets: str | list[str] = "",
        status_code: bool = True,
        tech_detect: bool = False,
        follow_redirects: bool = False,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        cmd = [self.BINARY, "-silent"]

        if status_code:
            cmd.append("-status-code")
        if tech_detect:
            cmd.append("-tech-detect")
        if follow_redirects:
            cmd.append("-follow-redirects")

        if isinstance(targets, list):
            cmd.extend(["-l", "-"])
        elif targets:
            cmd.extend(["-l", targets])

        if extra_args:
            cmd.extend(extra_args)
        return cmd

    async def run(
        self,
        targets: str | list[str] = "",
        status_code: bool = True,
        tech_detect: bool = False,
        follow_redirects: bool = False,
        extra_args: list[str] | None = None,
        timeout: int = 300,
    ) -> dict:
        if not self.is_installed():
            return {"success": False, "output": "", "error": "httpx is not installed"}

        cmd = self.build_command(targets, status_code, tech_detect, follow_redirects, extra_args)
        logger.info(f"Running httpx: {' '.join(cmd)}")

        stdin_data = None
        if isinstance(targets, list) and targets:
            stdin_data = "\n".join(targets).encode()

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if stdin_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=stdin_data), timeout=timeout
            )
            output = stdout.decode(errors="replace")
            error = stderr.decode(errors="replace")
            return {
                "success": proc.returncode == 0,
                "output": output,
                "error": error,
            }
        except asyncio.TimeoutError:
            proc.kill()
            return {"success": False, "output": "", "error": "httpx probe timed out"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
