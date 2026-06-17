from features.osint.base import ToolWrapper


class TheHarvesterWrapper(ToolWrapper):
    NAME = "theharvester"
    BINARY = "theHarvester"
    DESCRIPTION = "theHarvester - email, subdomain, and name harvester for OSINT"

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
