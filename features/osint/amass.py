from features.osint.base import ToolWrapper


class AmassWrapper(ToolWrapper):
    NAME = "amass"
    BINARY = "amass"
    DESCRIPTION = "Amass - subdomain enumeration using OSINT, DNS brute force, and web scraping"

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
