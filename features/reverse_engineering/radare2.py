from features.reverse_engineering.base import ToolWrapper


class Radare2Wrapper(ToolWrapper):
    NAME = "radare2"
    BINARY = "r2"
    DESCRIPTION = "Radare2 reverse engineering framework"

    def get_help(self) -> str:
        return "Radare2: reverse engineering framework for binary analysis and exploitation"

    def build_command(self, **kwargs) -> list[str]:
        cmd = [self.BINARY, "-q"]
        if kwargs.get("write_mode", False):
            cmd.append("-w")
        if "r2_command" in kwargs:
            cmd.extend(["-c", kwargs["r2_command"]])
        if "target" in kwargs:
            cmd.append(kwargs["target"])
        cmd.extend(kwargs.get("extra_args", []))
        return cmd

    async def analyze(self, target: str) -> dict:
        return await self.run(target=target, r2_command="aaa")

    async def disassemble(self, target: str, count: int = 100) -> dict:
        return await self.run(target=target, r2_command=f"pd {count}")

    async def strings(self, target: str) -> dict:
        return await self.run(target=target, r2_command="iz")

    async def run_command(self, target: str, r2_command: str) -> dict:
        return await self.run(target=target, r2_command=r2_command)

    async def info(self, target: str) -> dict:
        return await self.run(target=target, r2_command="i")

    async def symbols(self, target: str) -> dict:
        return await self.run(target=target, r2_command="is")

    async def imports(self, target: str) -> dict:
        return await self.run(target=target, r2_command="ii")

    async def hexdump(self, target: str, address: str = "0", length: int = 64) -> dict:
        return await self.run(target=target, r2_command=f"s {address}; px {length}")
