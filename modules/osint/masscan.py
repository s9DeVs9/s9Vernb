"""
Masscan fast port scanner wrapper.

Wraps masscan to provide ultra-fast port scanning capabilities.
Masscan can scan the entire Internet in under 5 minutes using
asynchronous SYN packets and custom TCP/IP stacks.

Requires: masscan (https://github.com/robertdavidgraham/masscan)
"""

import shutil
import asyncio
import logging

logger = logging.getLogger("S9Checker")


class ToolWrapper:
    NAME = "masscan"
    BINARY = "masscan"
    DESCRIPTION = "Masscan - fastest Internet port scanner, transmits 10M+ packets/sec"

    def is_installed(self) -> bool:
        return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        if not self.is_installed():
            return "masscan is not installed. Install from https://github.com/robertdavidgraham/masscan"
        return "Masscan - TCP port scanner, transmits SYN packets asynchronously"

    def build_command(
        self,
        target: str,
        ports: str = "1-65535",
        rate: int = 10000,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        cmd = [
            self.BINARY,
            target,
            "-p", ports,
            "--rate", str(rate),
        ]
        if extra_args:
            cmd.extend(extra_args)
        return cmd

    async def run(
        self,
        target: str,
        ports: str = "1-65535",
        rate: int = 10000,
        extra_args: list[str] | None = None,
        timeout: int = 600,
    ) -> dict:
        if not self.is_installed():
            return {"success": False, "output": "", "error": "masscan is not installed"}

        cmd = self.build_command(target, ports, rate, extra_args)
        logger.info(f"Running masscan: {' '.join(cmd)}")

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
            return {"success": False, "output": "", "error": "masscan scan timed out"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
