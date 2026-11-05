"""Select an SSH agent without starting a process or trusting stale paths."""
import os
import socket
import struct
from pathlib import Path


def agent_responds(path: str) -> bool:
    if not path:
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(0.3)
            client.connect(path)
            client.sendall(b"\x00\x00\x00\x01\x0b")  # SSH_AGENTC_REQUEST_IDENTITIES
            response = b""
            while len(response) < 5:
                chunk = client.recv(5 - len(response))
                if not chunk:
                    return False
                response += chunk
            length = struct.unpack(">I", response[:4])[0]
            return 5 <= length <= 1024 * 1024 and response[4] == 12
    except (OSError, ValueError):
        return False


def select_agent() -> bool:
    """Export the socket and return whether a responsive external agent is selected."""
    current = os.environ.get("SSH_AUTH_SOCK", "")
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    managed = str(Path(runtime) / "shade-raid-ssh/agent.socket") if runtime and os.path.isabs(runtime) else ""
    if current and current != managed and agent_responds(current):
        return True
    if managed:
        os.environ["SSH_AUTH_SOCK"] = managed
    else:
        os.environ.pop("SSH_AUTH_SOCK", None)
    return False
