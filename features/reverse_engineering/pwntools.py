from features.reverse_engineering.base import ToolWrapper


class PwntoolsWrapper(ToolWrapper):
    NAME = "pwntools"
    BINARY = "python3"
    DESCRIPTION = "Pwntools CTF framework and exploit development library"

    def is_installed(self) -> bool:
        import shutil
        try:
            result = __import__("pwn")
            return True
        except ImportError:
            return shutil.which(self.BINARY) is not None

    def get_help(self) -> str:
        return "Pwntools: CTF framework and exploit development library for Python"

    def build_command(self, **kwargs) -> list[str]:
        cmd = [self.BINARY]
        if "script" in kwargs:
            cmd.append(kwargs["script"])
        cmd.extend(kwargs.get("extra_args", []))
        return cmd

    async def run_exploit(self, target: str, exploit_script: str) -> dict:
        from pathlib import Path
        script_path = exploit_script
        if not Path(exploit_script).exists():
            return {
                "success": False,
                "output": "",
                "error": f"Exploit script not found: {exploit_script}",
            }
        env_setup = f"import os; os.environ['TARGET'] = '{target}'; "
        cmd = [self.BINARY, "-c", f"{env_setup}exec(open('{script_path}').read())"]
        import asyncio
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
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}

    async def test_local(self, exploit_script: str, target_binary: str) -> dict:
        import tempfile
        from pathlib import Path
        script_content = f"""
from pwn import *
context.log_level = 'debug'
context.arch = '{self._detect_arch(target_binary)}'
p = process('{target_binary}')
exec(open('{exploit_script}').read())
p.interactive()
"""
        tmp_script = tempfile.mktemp(suffix=".py")
        Path(tmp_script).write_text(script_content)
        result = await self.run(script=tmp_script)
        Path(tmp_script).unlink(missing_ok=True)
        return result

    async def generate_template(self, template_type: str = "basic") -> dict:
        templates = {
            "basic": '''#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

def exploit():
    p = process('./binary')
    p.interactive()

if __name__ == '__main__':
    exploit()
''',
            "ret2libc": '''#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

def exploit():
    p = process('./binary')
    elf = ELF('./binary')
    libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

    offset = 72


    p.interactive()

if __name__ == '__main__':
    exploit()
''',
            "rop": '''#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

def exploit():
    p = process('./binary')
    elf = ELF('./binary')

    rop = ROP(elf)
    offset = 72

    payload = flat(b'A' * offset, rop.find_gadget(['pop rdi', 'ret'])[0], next(elf.search(b'/bin/sh')), rop.find_gadget(['ret'])[0], elf.sym.system)

    p.sendline(payload)
    p.interactive()

if __name__ == '__main__':
    exploit()
''',
        }
        script = templates.get(template_type, templates["basic"])
        return {"success": True, "output": script, "error": ""}

    def _detect_arch(self, binary_path: str) -> str:
        try:
            import subprocess
            result = subprocess.run(
                ["file", binary_path],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = result.stdout.lower()
            if "x86-64" in output or "x86_64" in output:
                return "amd64"
            elif "80386" in output or "x86" in output:
                return "i386"
            elif "aarch64" in output or "arm64" in output:
                return "aarch64"
            elif "arm" in output:
                return "arm"
        except Exception:
            pass
        return "amd64"
