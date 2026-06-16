
import shutil
import asyncio
import logging

logger = logging.getLogger("S9Checker")


class ToolWrapper:
    NAME = "rustscan"
    BINARY = "rustscan"
    DESCRIPTION = "RustScan - faster port scanner written in Rust, integrates with Nmap"

    def is_installed(self) -> bool:
        return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        if not self.is_installed():
            return "rustscan is not installed. Install via cargo install rustscan"
        return "RustScan - A port scanner written in Rust that automatically pipes results to Nmap"

    def build_command(
        self,
        target: str,
        ports: str = "",
        batch_size: int = 4500,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        cmd = [
            self.BINARY,
            "-a", target,
            "--batch-size", str(batch_size),
        ]
        if ports:
            cmd.extend(["-p", ports])
        if extra_args:
            cmd.extend(extra_args)
        return cmd

    async def run(
        self,
        target: str,
        ports: str = "",
        batch_size: int = 4500,
        extra_args: list[str] | None = None,
        timeout: int = 300,
    ) -> dict:
        if not self.is_installed():
            return {"success": False, "output": "", "error": "rustscan is not installed"}

        cmd = self.build_command(target, ports, batch_size, extra_args)
        logger.info(f"Running rustscan: {' '.join(cmd)}")

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
            return {"success": False, "output": "", "error": "rustscan timed out"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
