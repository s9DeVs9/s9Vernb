
from features.osint.base import ToolWrapper


class NucleiWrapper(ToolWrapper):
    NAME = "nuclei"
    BINARY = "nuclei"
    DESCRIPTION = "Nuclei - fast vulnerability scanner based on customizable YAML templates"

    def get_help(self) -> str:
        if not self.is_installed():
            return "nuclei is not installed. Install from https://github.com/projectdiscovery/nuclei"
        return "Nuclei - vulnerability scanner with community templates"

    def build_command(
        self,
        target: str = "",
        templates: str = "",
        severity: str = "",
        rate_limit: int = 150,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        cmd = [self.BINARY]
        if target:
            cmd.extend(["-u", target])
        if templates:
            cmd.extend(["-t", templates])
        if severity:
            cmd.extend(["-severity", severity])
        cmd.extend(["-rate-limit", str(rate_limit)])
        if extra_args:
            cmd.extend(extra_args)
        return cmd
