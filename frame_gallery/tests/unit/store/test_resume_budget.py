"""Durable deny-before-I/O; no recovery from a stale budget backup."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from frame_gallery.errors import StateError
from frame_gallery.observer.model import StatusReason
from frame_gallery.store.atomic import Directory
from frame_gallery.store.resume_budget import FILE, FORMAT, ResumeBudget


def document(attempts: object = None, **changes: object) -> dict[str, object]:
    return dict(
        {
            "format": FORMAT,
            "version": 1,
            "attempts": [] if attempts is None else attempts,
            "auth_blocked": False,
        },
        **changes,
    )


def write(tmp_path: Path, value: object) -> Path:
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    path = state / FILE
    path.write_text(json.dumps(value))
    return path


def test_reservations_survive_restart_and_success_does_not_clear_limits(tmp_path: Path) -> None:
    for index in range(6):
        assert ResumeBudget(tmp_path).reserve(1000 + index * 60) is None
    assert ResumeBudget(tmp_path).reserve(1360) is StatusReason.RATE_LIMITED
    assert ResumeBudget(tmp_path).reserve(1359) is StatusReason.RATE_LIMITED
    assert ResumeBudget(tmp_path).reserve(4599) is StatusReason.RATE_LIMITED
    assert ResumeBudget(tmp_path).reserve(4600) is None
    assert ResumeBudget(tmp_path).reserve(4659) is StatusReason.RATE_LIMITED
    budget = ResumeBudget(tmp_path)
    budget.block_auth()
    assert ResumeBudget(tmp_path).reserve(4660) is StatusReason.TV_AUTHORIZATION
    assert ResumeBudget(tmp_path).clear_auth()
    assert ResumeBudget(tmp_path).reserve(4659) is StatusReason.RATE_LIMITED
    assert ResumeBudget(tmp_path).reserve(4660) is None


@pytest.mark.parametrize(
    "value",
    [
        [],
        {},
        document(version=True),
        document(version=2),
        document(format="other"),
        document(auth_blocked=1),
        document(attempts="bad"),
        document(attempts=[True]),
        document(attempts=[float("inf")]),
        document(attempts=[-1]),
        document(attempts=[1, 1]),
        document(attempts=[2, 1]),
        document(attempts=list(range(7))),
        document(extra=True),
    ],
)
def test_invalid_primary_never_falls_back_or_repairs(tmp_path: Path, value: object) -> None:
    path = write(tmp_path, value)
    before = path.read_bytes()
    path.with_suffix(".json.bak").write_text(json.dumps(document()))
    budget = ResumeBudget(tmp_path)
    assert budget.reserve(1000) is StatusReason.BUDGET_UNAVAILABLE
    assert not budget.clear_auth()
    budget.block_auth()
    assert path.read_bytes() == before


@pytest.mark.parametrize("now", [float("nan"), float("inf"), -1, True, 253402300800])
def test_invalid_clock_denies_without_creating_budget(tmp_path: Path, now: float) -> None:
    assert ResumeBudget(tmp_path).reserve(now) is StatusReason.BUDGET_UNAVAILABLE
    assert not (tmp_path / "state" / FILE).exists()


def test_backwards_clock_does_not_modify_a_structurally_valid_budget(tmp_path: Path) -> None:
    path = write(tmp_path, document(attempts=[1001]))
    before = path.read_bytes()
    assert ResumeBudget(tmp_path).reserve(1000) is StatusReason.BUDGET_UNAVAILABLE
    assert ResumeBudget(tmp_path).clear_auth()
    assert path.read_bytes() == before


@pytest.mark.parametrize("kind", ["symlink", "fifo", "oversize", "directory", "bad_json"])
def test_nonregular_or_damaged_budget_denies(tmp_path: Path, kind: str) -> None:

    path = write(tmp_path, document())
    path.unlink()
    if kind == "symlink":
        target = tmp_path / "foreign"
        target.write_text(json.dumps(document()))
        path.symlink_to(target)
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    else:
        path.write_bytes(b"x" * (2049 if kind == "oversize" else 2))
    assert ResumeBudget(tmp_path).reserve(1000) is StatusReason.BUDGET_UNAVAILABLE


def test_write_failure_readback_and_auth_latch_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    budget = ResumeBudget(tmp_path)

    def fail(*_a: object, **_kw: object) -> None:
        raise StateError("synthetic full disk")

    monkeypatch.setattr(Directory, "write", fail)
    assert budget.reserve(1000) is StatusReason.BUDGET_UNAVAILABLE
    budget.block_auth()
    monkeypatch.undo()
    assert budget.clear_auth()
    monkeypatch.setattr(Directory, "write", lambda *_a, **_kw: None)
    assert budget.reserve(1000) is StatusReason.BUDGET_UNAVAILABLE


def test_blocked_budget_write_error_never_clears_latch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    budget = ResumeBudget(tmp_path)
    budget.block_auth()
    monkeypatch.setattr(budget, "_write", lambda *_a, **_kw: (_ for _ in ()).throw(OSError("test")))
    assert not budget.clear_auth()
    assert ResumeBudget(tmp_path).reserve(1000) is StatusReason.TV_AUTHORIZATION
