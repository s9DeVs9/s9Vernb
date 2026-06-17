
from features.osint.base import ToolWrapper


class NmapWrapper(ToolWrapper):
    NAME = "nmap"
    BINARY = "nmap"
    DESCRIPTION = "Nmap - network exploration and security auditing utility"

    def get_help(self) -> str:
        if not self.is_installed():
            return "nmap is not installed. Install from https://nmap.org/download.html"
        return "Nmap - Network Mapper for host discovery, port scanning, and service detection"

    def build_command(
        self,
        target: str,
        ports: str = "",
        scan_type: str = "",
        extra_args: list[str] | None = None,
    ) -> list[str]:
        cmd = [self.BINARY]
        if scan_type:
            cmd.append(f"-{scan_type}")
        if ports:
            cmd.extend(["-p", ports])
        cmd.append(target)
        if extra_args:
            cmd.extend(extra_args)
        return cmd
