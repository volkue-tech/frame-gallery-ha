"""Install the real network filter in disposable Linux children, never pytest.

No connection, listener, packet, television or provider request is made. These
tests exercise the native kernel, not AppArmor attachment or a simulated BPF VM.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROBE = """
import ctypes
import json
import socket
import sys
sys.path.insert(0, sys.argv[2])
from frame_gallery.isolation.network_filter import install
libc = ctypes.CDLL(None, use_errno=True)
assert libc.prctl(38, 1, 0, 0, 0) == 0
install(sys.argv[1])
results = {}
for name, domain, kind in (
    ('tcp', socket.AF_INET, socket.SOCK_STREAM),
    ('udp', socket.AF_INET, socket.SOCK_DGRAM),
    ('ipv6', socket.AF_INET6, socket.SOCK_STREAM),
    ('unix', socket.AF_UNIX, socket.SOCK_STREAM),
):
    try:
        sock = socket.socket(domain, kind)
    except PermissionError:
        results[name] = False
    else:
        results[name] = True
        sock.close()
try:
    pair = socket.socketpair()
except PermissionError:
    results['pair'] = False
else:
    results['pair'] = True
    for sock in pair:
        sock.close()
print(json.dumps(results))
"""


@pytest.mark.skipif(sys.platform != "linux", reason="real Linux seccomp kernel required")
@pytest.mark.parametrize("task", ["prepare", "inspect", "deliver"])
def test_native_worker_network_filter(task: str) -> None:
    source = Path(__file__).resolve().parents[2] / "src"
    result = subprocess.run(  # noqa: S603 - fixed interpreter and own no-network probe
        [sys.executable, "-I", "-c", PROBE, task, str(source)],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    assert json.loads(result.stdout) == {
        "tcp": task == "deliver",
        "udp": False,
        "ipv6": False,
        "unix": False,
        "pair": False,
    }
