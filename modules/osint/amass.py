"""
Amass subdomain enumeration wrapper.

Wraps the Amass tool to provide subdomain discovery through
active and passive enumeration techniques. Uses OSINT sources,
brute forcing, and DNS resolution to map attack surfaces.

Requires: amass (https://github.com/owasp-amass/amass)
"""

import shutil
import asyncio
import logging

logger = logging.getLogger("S9Checker")


class ToolWrapper:
    NAME = "amass"
    BINARY = "amass"
    DESCRIPTION = "Amass - subdomain enumeration using OSINT, DNS brute force, and web scraping"

    def is_installed(self) -> bool:
        return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        if not self.is_installed():
            return "amass is not installed. Install from https://github.com/owasp-amass/amass"
        return "Amass - In-depth attack surface mapping and asset discovery"

    def build_command(
        self,
        domain: str,
        enum_type: str = "passive",
        extra_args: list[str] | None = None,
    ) -> list[str]:
        cmd = [self.BINARY, "enum"]
        if enum_type == "passive":
            cmd.append("-passive")
        elif enum_type == "active":
            cmd.extend(["-active"])
        cmd.extend(["-d", domain])
        if extra_args:
            cmd.extend(extra_args)
        return cmd

    async def run(
        self,
        domain: str,
        enum_type: str = "passive",
        extra_args: list[str] | None = None,
        timeout: int = 600,
    ) -> dict:
        if not self.is_installed():
            return {"success": False, "output": "", "error": "amass is not installed"}

        cmd = self.build_command(domain, enum_type, extra_args)
        logger.info(f"Running amass: {' '.join(cmd)}")

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
            return {"success": False, "output": "", "error": "amass enumeration timed out"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
