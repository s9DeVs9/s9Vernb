from features.osint.base import ToolWrapper


class MasscanWrapper(ToolWrapper):
    NAME = "masscan"
    BINARY = "masscan"
    DESCRIPTION = "Masscan - fastest Internet port scanner, transmits 10M+ packets/sec"

    def get_help(self) -> str:
        if not self.is_installed():
            return "masscan is not installed. Install from https://github.com/robertdavidgraham/masscan"
        return "Masscan - TCP port scanner, transmits SYN packets asynchronously"

    def build_command(
        self,
        target: str,
        ports: str = "1-65535",
        rate: int = 10000,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        cmd = [
            self.BINARY,
            target,
            "-p", ports,
            "--rate", str(rate),
        ]
        if extra_args:
            cmd.extend(extra_args)
        return cmd
