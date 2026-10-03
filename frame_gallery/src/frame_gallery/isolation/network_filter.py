"""Irreversible worker-only seccomp network guard (D-180).

Installed after no-new-privileges, before the lifeline thread or task input.
AppArmor remains required for files/execution; this is not a full sandbox.
Only little-endian native aarch64/x86_64 are supported. Reject other ABIs,
including x32, and alternate socket creation through io_uring.
"""

from __future__ import annotations

import errno
import os
import sys
from typing import Final

LD: Final = 0x20  # BPF_LD | BPF_W | BPF_ABS
EQ: Final = 0x15  # BPF_JMP | BPF_JEQ | BPF_K
GE: Final = 0x35  # BPF_JMP | BPF_JGE | BPF_K
AND: Final = 0x54  # BPF_ALU | BPF_AND | BPF_K
RET: Final = 0x06
ALLOW: Final = 0x7FFF0000
DENY: Final = 0x00050000 | errno.EPERM
ARCHES: Final = {
    "aarch64": (0xC00000B7, 198, 199, 117),
    "x86_64": (0xC000003E, 41, 53, 101),
}
type Instruction = tuple[int, int, int, int]


def program(machine: str, task: str) -> tuple[Instruction, ...]:
    """Independent BPF program from the Linux UAPI, not a copied example."""
    if machine not in ARCHES or task not in ("prepare", "inspect", "deliver"):
        raise ValueError("network_filter_target")
    arch, socket_nr, pair_nr, ptrace_nr = ARCHES[machine]
    rows: list[Instruction] = [
        (LD, 0, 0, 4),  # seccomp_data.arch
        (EQ, 1, 0, arch),
        (RET, 0, 0, DENY),
        (LD, 0, 0, 0),  # seccomp_data.nr
        (GE, 0, 1, 0x40000000),  # no x32/high-bit syscall alias
        (RET, 0, 0, DENY),
    ]
    for number in (pair_nr, ptrace_nr, 425, 438):  # socketpair, ptrace, io_uring, pidfd_getfd
        rows.extend(((EQ, 0, 1, number), (RET, 0, 0, DENY)))
    if task != "deliver":
        rows.extend(((EQ, 0, 1, socket_nr), (RET, 0, 0, DENY), (RET, 0, 0, ALLOW)))
    else:
        rows.extend(
            (
                (EQ, 1, 0, socket_nr),
                (RET, 0, 0, ALLOW),  # all other calls retain existing container/LSM policy
                (LD, 0, 0, 16),  # socket domain (low word, kernel takes int)
                (EQ, 1, 0, 2),  # AF_INET only
                (RET, 0, 0, DENY),
                (LD, 0, 0, 24),  # socket type
                (AND, 0, 0, 0xF),  # SOCK_TYPE_MASK; CLOEXEC/NONBLOCK remain valid
                (EQ, 1, 0, 1),  # SOCK_STREAM only
                (RET, 0, 0, DENY),
                (LD, 0, 0, 32),  # socket protocol
                (EQ, 2, 0, 0),  # default TCP
                (EQ, 1, 0, 6),  # explicit IPPROTO_TCP
                (RET, 0, 0, DENY),
                (RET, 0, 0, ALLOW),
            )
        )
    return tuple(rows)


def install(task: str) -> None:
    """Must run in a fresh Linux worker, never in the parent or test runner."""
    is_linux = sys.platform.startswith("linux")
    is_little = sys.byteorder == "little"
    if not is_linux or not is_little:
        raise ValueError("network_filter_platform")
    rows = program(os.uname().machine, task)
    import ctypes  # noqa: PLC0415 - worker-only kernel binding, never loaded in the parent

    class SockFilter(ctypes.Structure):
        _fields_ = [
            ("code", ctypes.c_ushort),
            ("jt", ctypes.c_ubyte),
            ("jf", ctypes.c_ubyte),
            ("k", ctypes.c_uint32),
        ]

    class SockProgram(ctypes.Structure):
        _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(SockFilter))]

    array = (SockFilter * len(rows))(*(SockFilter(*row) for row in rows))
    descriptor = SockProgram(len(rows), array)
    libc = ctypes.CDLL(None, use_errno=True)
    prctl = libc.prctl
    prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong]
    prctl.restype = ctypes.c_int
    # PR_SET_SECCOMP=22, SECCOMP_MODE_FILTER=2. NNP was already verified.
    if prctl(22, 2, ctypes.byref(descriptor), 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "network_filter_install")
