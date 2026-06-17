from features.osint.base import ToolWrapper


class RustscanWrapper(ToolWrapper):
    NAME = "rustscan"
    BINARY = "rustscan"
    DESCRIPTION = "RustScan - faster port scanner written in Rust, integrates with Nmap"

    def get_help(self) -> str:
        if not self.is_installed():
            return "rustscan is not installed. Install via cargo install rustscan"
        return "RustScan - A port scanner written in Rust that automatically pipes results to Nmap"

    def build_command(
        self,
        target: str,
        ports: str = "",
        batch_size: int = 4500,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        cmd = [
            self.BINARY,
            "-a", target,
            "--batch-size", str(batch_size),
        ]
        if ports:
            cmd.extend(["-p", ports])
        if extra_args:
            cmd.extend(extra_args)
        return cmd
