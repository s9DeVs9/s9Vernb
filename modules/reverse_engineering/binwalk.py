"""Binwalk firmware analysis wrapper.

Provides firmware scanning, extraction, and comparison
using the binwalk firmware analysis tool.
"""

import asyncio
import shutil
from pathlib import Path


class ToolWrapper:
    NAME = "binwalk"
    BINARY = "binwalk"
    DESCRIPTION = "Binwalk firmware image analysis and extraction tool"

    def is_installed(self) -> bool:
        return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        return "Binwalk: firmware image scanning, extraction, and comparison"

    def build_command(self, **kwargs) -> list[str]:
        cmd = [self.BINARY]
        if "target" in kwargs:
            cmd.append(kwargs["target"])
        if kwargs.get("extract", False):
            cmd.append("-e")
        if kwargs.get("matryoshka", False):
            cmd.append("-M")
        if "directory" in kwargs:
            cmd.extend(["-C", kwargs["directory"]])
        if kwargs.get("quiet", False):
            cmd.append("-q")
        if "signature" in kwargs:
            cmd.extend(["-R", kwargs["signature"]])
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

    async def scan(self, target: str) -> dict:
        return await self.run(target=target, quiet=False)

    async def extract(self, target: str, directory: str = ".") -> dict:
        extract_dir = str(Path(directory).resolve())
        Path(extract_dir).mkdir(parents=True, exist_ok=True)
        return await self.run(
            target=target,
            extract=True,
            matryoshka=True,
            directory=extract_dir,
        )

    async def compare(self, target1: str, target2: str) -> dict:
        cmd1 = self.build_command(target=target1, quiet=True)
        cmd2 = self.build_command(target=target2, quiet=True)
        try:
            proc1 = await asyncio.create_subprocess_exec(
                *cmd1,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            proc2 = await asyncio.create_subprocess_exec(
                *cmd2,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out1, err1 = await proc1.communicate()
            out2, err2 = await proc2.communicate()
            output1 = out1.decode(errors="replace")
            output2 = out2.decode(errors="replace")
            return {
                "success": proc1.returncode == 0 and proc2.returncode == 0,
                "output": f"=== {target1} ===\n{output1}\n\n=== {target2} ===\n{output2}",
                "error": err1.decode(errors="replace") + err2.decode(errors="replace"),
            }
        except FileNotFoundError:
            return {"success": False, "output": "", "error": f"{self.BINARY} not found"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}

    async def signature_scan(self, target: str) -> dict:
        return await self.run(target=target, extra_args=["-R", ""])

    async def entropy(self, target: str) -> dict:
        return await self.run(target=target, extra_args=["-E"])
