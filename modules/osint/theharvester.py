
import shutil
import asyncio
import logging

logger = logging.getLogger("S9Checker")


class ToolWrapper:
    NAME = "theharvester"
    BINARY = "theHarvester"
    DESCRIPTION = "theHarvester - email, subdomain, and name harvester for OSINT"

    def is_installed(self) -> bool:
        return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        if not self.is_installed():
            return "theHarvester is not installed. Install from https://github.com/laramies/theHarvester"
        return "theHarvester - E-mails, subdomains and IPs Harvester"

    def build_command(
        self,
        domain: str,
        source: str = "google",
        limit: int = 500,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        cmd = [
            self.BINARY,
            "-d", domain,
            "-b", source,
            "-l", str(limit),
        ]
        if extra_args:
            cmd.extend(extra_args)
        return cmd

    async def run(
        self,
        domain: str,
        source: str = "google",
        limit: int = 500,
        extra_args: list[str] | None = None,
        timeout: int = 300,
    ) -> dict:
        if not self.is_installed():
            return {"success": False, "output": "", "error": "theHarvester is not installed"}

        cmd = self.build_command(domain, source, limit, extra_args)
        logger.info(f"Running theHarvester: {' '.join(cmd)}")

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
            return {"success": False, "output": "", "error": "theHarvester scan timed out"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
