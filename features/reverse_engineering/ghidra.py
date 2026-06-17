
from features.reverse_engineering.base import ToolWrapper


class GhidraWrapper(ToolWrapper):
    NAME = "ghidra"
    BINARY = "ghidra"
    DESCRIPTION = "Ghidra - software reverse engineering framework by NSA"

    def get_help(self) -> str:
        if not self.is_installed():
            return "ghidra is not installed. Download from https://ghidra-sre.org/"
        return "Ghidra - reverse engineering framework for decompilation and analysis"

    def build_command(self, **kwargs) -> list[str]:
        cmd = [self.BINARY]
        script = kwargs.get("script")
        if script:
            cmd.extend(["-scriptPath", script])
        project = kwargs.get("project")
        if project:
            cmd.extend(["-import", project])
        cmd.extend(kwargs.get("extra_args", []))
        return cmd
