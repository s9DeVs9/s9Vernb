
import asyncio
import shutil
from pathlib import Path


class ToolWrapper:
    NAME = "ghidra"
    BINARY = "analyzeHeadless"
    DESCRIPTION = "Ghidra reverse engineering platform headless analysis"

    def is_installed(self) -> bool:
        return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        return "Ghidra headless analyzer for reverse engineering and decompilation"

    def build_command(self, **kwargs) -> list[str]:
        cmd = [self.BINARY]
        if "project_dir" in kwargs:
            cmd.append(kwargs["project_dir"])
        if "project_name" in kwargs:
            cmd.append(kwargs["project_name"])
        if "target" in kwargs:
            cmd.extend(["-import", kwargs["target"]])
        if "delete_project" in kwargs and kwargs["delete_project"]:
            cmd.append("-deleteProject")
        if "post_script" in kwargs:
            cmd.extend(["-postScript", kwargs["post_script"]])
        if "pre_script" in kwargs:
            cmd.extend(["-preScript", kwargs["pre_script"]])
        if "script_args" in kwargs:
            for arg in kwargs["script_args"]:
                cmd.extend(["-scriptPath", arg])
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

    async def analyze(self, target: str, project_dir: str) -> dict:
        project_name = Path(target).stem + "_project"
        project_path = str(Path(project_dir) / project_name)
        return await self.run(
            target=target,
            project_dir=project_path,
            project_name=project_name,
            post_script="ghidra_analysis.py",
            delete_project=False,
        )

    async def decompile(self, target: str, function_name: str) -> dict:
        script_content = f"""
from ghidra.app.decompiler import DecompInterface
target_func = getGlobalFunctions("{function_name}")[0]
decomp = DecompInterface()
decomp.openProgram(currentProgram)
results = decomp.decompileFunction(target_func, 0, None)
print(results.getDecompiledFunction().getC())
"""
        script_path = "/tmp/decompile_script.py"
        Path(script_path).write_text(script_content)
        return await self.run(
            target=target,
            project_dir="/tmp/ghidra_proj",
            project_name="decompile_project",
            post_script=script_path,
            delete_project=True,
        )

    async def export(self, target: str, format: str = "binary") -> dict:
        export_formats = {
            "binary": "ExportTool",
            "gdt": "ExportTool",
            "skeleton": "ExportTool",
        }
        return await self.run(
            target=target,
            project_dir="/tmp/ghidra_proj",
            project_name="export_project",
            extra_args=["-export", format],
            delete_project=True,
        )
