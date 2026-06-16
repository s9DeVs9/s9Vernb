"""Radare2 reverse engineering tool wrapper.

Provides binary analysis, disassembly, and string extraction
using the radare2 framework's command-line interface.
"""

import asyncio
import shutil


class ToolWrapper:
    NAME = "radare2"
    BINARY = "r2"
    DESCRIPTION = "Radare2 reverse engineering framework"

    def is_installed(self) -> bool:
        return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        return "Radare2: reverse engineering framework for binary analysis and exploitation"

    def build_command(self, **kwargs) -> list[str]:
        cmd = [self.BINARY, "-q"]
        if kwargs.get("write_mode", False):
            cmd.append("-w")
        if "r2_command" in kwargs:
            cmd.extend(["-c", kwargs["r2_command"]])
        if "target" in kwargs:
            cmd.append(kwargs["target"])
        cmd.extend(kwargs.get("extra_args", []))
        return cmd

    async def run(self, **kwargs) -> dict:
        cmd = self.build_command(**kwargs)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            return {
                "success": proc.returncode == 0,
                "output": stdout.decode(errors="replace"),
                "error": stderr.decode(errors="replace"),
            }
        except FileNotFoundError:
            return {"success": False, "output": "", "error": f"{self.BINARY} not found"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}

    async def analyze(self, target: str) -> dict:
        return await self.run(target=target, r2_command="aaa")

    async def disassemble(self, target: str, count: int = 100) -> dict:
        return await self.run(target=target, r2_command=f"pd {count}")

    async def strings(self, target: str) -> dict:
        return await self.run(target=target, r2_command="iz")

    async def run_command(self, target: str, r2_command: str) -> dict:
        return await self.run(target=target, r2_command=r2_command)

    async def info(self, target: str) -> dict:
        return await self.run(target=target, r2_command="i")

    async def symbols(self, target: str) -> dict:
        return await self.run(target=target, r2_command="is")

    async def imports(self, target: str) -> dict:
        return await self.run(target=target, r2_command="ii")

    async def hexdump(self, target: str, address: str = "0", length: int = 64) -> dict:
        return await self.run(target=target, r2_command=f"s {address}; px {length}")
