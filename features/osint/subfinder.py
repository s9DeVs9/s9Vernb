from features.osint.base import ToolWrapper


class SubfinderWrapper(ToolWrapper):
    NAME = "subfinder"
    BINARY = "subfinder"
    DESCRIPTION = "Subfinder - fast passive subdomain enumeration tool"

    def get_help(self) -> str:
        if not self.is_installed():
            return "subfinder is not installed. Install from https://github.com/projectdiscovery/subfinder"
        return "Subfinder - a subdomain discovery tool that uses passive online sources"

    def build_command(
        self,
        domain: str,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        cmd = [
            self.BINARY,
            "-d", domain,
            "-silent",
        ]
        if extra_args:
            cmd.extend(extra_args)
        return cmd
