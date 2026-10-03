"""BPF decisions for both native ABIs; installation is mocked, never on pytest."""

from __future__ import annotations

import ctypes
import errno
import os
import sys
from types import SimpleNamespace
from typing import Any

import pytest

from frame_gallery.isolation import bootstrap
from frame_gallery.isolation import network_filter as nf
from tests.unit.isolation.test_bootstrap import FakeOs, config


class FilterLayout(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_ushort),
        ("jt", ctypes.c_ubyte),
        ("jf", ctypes.c_ubyte),
        ("k", ctypes.c_uint32),
    ]


class ProgramLayout(ctypes.Structure):
    _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(FilterLayout))]


def evaluate(
    rows: tuple[nf.Instruction, ...],
    arch: int,
    nr: int,
    domain: int = 2,
    kind: int = 1,
    protocol: int = 0,
) -> int:
    words = {0: nr, 4: arch, 16: domain, 24: kind, 32: protocol}
    accumulator = index = 0
    while True:
        code, yes, no, value = rows[index]
        index += 1
        if code == nf.LD:
            accumulator = words[value] & 0xFFFFFFFF
        elif code == nf.EQ:
            index += yes if accumulator == value else no
        elif code == nf.GE:
            index += yes if accumulator >= value else no
        elif code == nf.AND:
            accumulator &= value
        elif code == nf.RET:
            return value
        else:
            raise AssertionError(code)


@pytest.mark.parametrize("machine", nf.ARCHES)
@pytest.mark.parametrize("task", ["prepare", "inspect", "deliver"])
def test_all_native_network_decisions(machine: str, task: str) -> None:
    arch, socket_nr, pair_nr, ptrace_nr = nf.ARCHES[machine]
    rows = nf.program(machine, task)
    assert evaluate(rows, arch, 0) == nf.ALLOW
    assert evaluate(rows, arch ^ 1, 0) == nf.DENY
    assert evaluate(rows, arch, 0x40000000 | socket_nr) == nf.DENY
    for nr in (pair_nr, ptrace_nr, 425, 438):
        assert evaluate(rows, arch, nr) == nf.DENY
    for domain in (1, 2, 10, 16):
        for kind in (1, 2, 3, 1 | 0x80000, 1 | 0x800):
            for protocol in (0, 6, 17, 255):
                expected = (
                    nf.ALLOW
                    if task == "deliver" and domain == 2 and kind & 0xF == 1 and protocol in (0, 6)
                    else nf.DENY
                )
                assert evaluate(rows, arch, socket_nr, domain, kind, protocol) == expected


@pytest.mark.parametrize(("machine", "task"), [("armv7l", "prepare"), ("aarch64", "echo")])
def test_unknown_target_refuses(machine: str, task: str) -> None:
    with pytest.raises(ValueError, match="target"):
        nf.program(machine, task)


@pytest.mark.parametrize(("platform", "order"), [("darwin", "little"), ("linux", "big")])
def test_platform_refuses(platform: str, order: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.setattr(sys, "byteorder", order)
    with pytest.raises(ValueError, match="platform"):
        nf.install("prepare")


@pytest.mark.parametrize("result", [0, -1])
def test_exact_install_protocol(result: int, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(sys, "byteorder", "little")
    monkeypatch.setattr(os, "uname", lambda: SimpleNamespace(machine="aarch64"))
    seen: list[int] = []

    class Call:
        argtypes: object = None
        restype: object = None

        def __call__(self, option: int, mode: int, pointer: Any, a: int, b: int) -> int:
            assert (option, mode, a, b) == (22, 2, 0, 0)
            descriptor = ctypes.cast(pointer, ctypes.POINTER(ProgramLayout)).contents
            expected = nf.program("aarch64", "prepare")
            assert descriptor.len == len(expected)
            assert (
                tuple((v.code, v.jt, v.jf, v.k) for v in descriptor.filter[: descriptor.len])
                == expected
            )
            seen.append(1)
            return result

    call = Call()
    monkeypatch.setattr(ctypes, "CDLL", lambda *args, **kwargs: SimpleNamespace(prctl=call))
    monkeypatch.setattr(ctypes, "get_errno", lambda: errno.EPERM)
    if result:
        with pytest.raises(OSError, match="network_filter_install") as error:
            nf.install("prepare")
        assert error.value.errno == errno.EPERM
    else:
        nf.install("prepare")
    assert seen == [1]
    assert call.restype == ctypes.c_int


@pytest.mark.parametrize("error", [OSError(errno.EPERM, "probe"), ValueError("probe")])
def test_failed_guard_refuses_before_lifeline_or_request(
    error: Exception, monkeypatch: pytest.MonkeyPatch
) -> None:
    ops = FakeOs()
    monkeypatch.setattr(bootstrap, "confine", lambda parent, task: "frame_gallery//image_worker")

    def refuse(task: str) -> None:
        assert "prctl:no_new_privs" in ops.calls
        raise error

    monkeypatch.setattr(bootstrap, "install_network_filter", refuse)
    with pytest.raises(bootstrap.Refused, match="network_filter"):
        bootstrap.run(config(apparmor_profile="frame_gallery"), ops, lambda value: None)
    assert "lifeline" not in ops.calls
