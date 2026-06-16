"""GDB + pwndbg debugger wrapper.

Provides debugging, core dump analysis, and memory inspection
using GDB with pwndbg extensions.
"""

import asyncio
import shutil
import tempfile
from pathlib import Path


class ToolWrapper:
    NAME = "pwndbg"
    BINARY = "gdb"
    DESCRIPTION = "GDB with pwndbg extension for exploit development and debugging"

    def is_installed(self) -> bool:
        return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        return "GDB + pwndbg: debugger for exploit development and binary analysis"

    def build_command(self, **kwargs) -> list[str]:
        cmd = [self.BINARY, "-q"]
        base_exes = [
            "set pagination off",
            "set confirm off",
            "set disable-randomization on",
        ]
        for setting in base_exes:
            cmd.extend(["-ex", setting])
        if "target" in kwargs:
            cmd.append(kwargs["target"])
        if "commands" in kwargs:
            for c in kwargs["commands"]:
                cmd.extend(["-ex", c])
        if "batch" in kwargs and kwargs["batch"]:
            cmd.append("-batch")
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

    async def debug(self, target: str, commands: list[str] | None = None) -> dict:
        cmds = commands or ["info registers", "bt"]
        return await self.run(target=target, commands=cmds, batch=True)

    async def coredump_analysis(self, core_file: str, binary: str = "") -> dict:
        cmds = [
            "bt full",
            "info registers",
            "info proc mappings",
            "set print pretty on",
        ]
        kwargs = {"commands": cmds, "batch": True}
        if binary:
            kwargs["target"] = binary
            cmds.insert(0, f"core-file {core_file}")
        else:
            kwargs["target"] = core_file
        return await self.run(**kwargs)

    async def dump_memory(self, target: str, address: str, length: str) -> dict:
        dump_file = tempfile.mktemp(suffix=".bin")
        cmds = [
            f"dump binary memory {dump_file} {address} {address}+{length}",
            f"shell ls -la {dump_file}",
        ]
        result = await self.run(target=target, commands=cmds, batch=True)
        result["dump_file"] = dump_file
        return result

    async def examine_memory(self, target: str, address: str, fmt: str = "x", count: int = 16) -> dict:
        return await self.run(
            target=target,
            commands=[f"examine/{fmt}{count} {address}"],
            batch=True,
        )

    async def backtrace(self, target: str) -> dict:
        return await self.run(
            target=target,
            commands=["bt full", "info args", "info locals"],
            batch=True,
        )

    async def run_script(self, target: str, gdb_script: str) -> dict:
        script_path = tempfile.mktemp(suffix=".gdb")
        Path(script_path).write_text(gdb_script)
        result = await self.run(
            target=target,
            commands=[f"source {script_path}"],
            batch=True,
        )
        Path(script_path).unlink(missing_ok=True)
        return result
