"""
Nmap network scanner wrapper.

Wraps the nmap tool to provide port scanning, service detection,
and OS fingerprinting capabilities for network reconnaissance.
Supports SYN scans, version detection, and aggressive scans.

Requires: nmap (https://nmap.org)
"""

import shutil
import asyncio
import logging

logger = logging.getLogger("S9Checker")


class ToolWrapper:
    NAME = "nmap"
    BINARY = "nmap"
    DESCRIPTION = "Nmap network scanner for port discovery, service detection, and OS fingerprinting"

    def is_installed(self) -> bool:
        return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        if not self.is_installed():
            return "nmap is not installed. Install from https://nmap.org"
        return "Nmap - Network exploration tool and security / port scanner"

    def build_command(
        self,
        target: str,
        ports: str = "",
        scan_type: str = "-sS",
        extra_args: list[str] | None = None,
    ) -> list[str]:
        cmd = [self.BINARY, scan_type]
        if ports:
            cmd.extend(["-p", ports])
        if extra_args:
            cmd.extend(extra_args)
        cmd.append(target)
        return cmd

    async def run(
        self,
        target: str,
        ports: str = "",
        scan_type: str = "-sS",
        extra_args: list[str] | None = None,
        timeout: int = 300,
    ) -> dict:
        if not self.is_installed():
            return {"success": False, "output": "", "error": "nmap is not installed"}

        cmd = self.build_command(target, ports, scan_type, extra_args)
        logger.info(f"Running nmap: {' '.join(cmd)}")

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
            return {"success": False, "output": "", "error": "nmap scan timed out"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
