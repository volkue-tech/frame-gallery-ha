from __future__ import annotations

import json
import stat
from ipaddress import IPv4Address
from pathlib import Path
from types import SimpleNamespace

import pytest

from frame_gallery.errors import StateError
from frame_gallery.store import observer_targets as module
from frame_gallery.store.observer_targets import FILE, SPEC, TargetStore

HOST = IPv4Address("192.168.1.20")
DEVICE = "a" * 64


def test_pins_are_atomic_bounded_persistent_and_not_auth_grants(tmp_path: Path) -> None:
    store = TargetStore(tmp_path)
    assert store.targets() == {}
    store.pin(HOST, DEVICE)
    path = tmp_path / "state" / FILE
    before = path.read_bytes()
    store.pin(HOST, DEVICE)
    assert path.read_bytes() == before
    assert TargetStore(tmp_path).targets() == {str(HOST): DEVICE}
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert list(path.parent.glob("*.tmp-*")) == []
    assert "token" not in before.decode()
    with pytest.raises(StateError, match="identity changed"):
        store.pin(HOST, "b" * 64)
    with pytest.raises(ValueError, match="invalid observer device"):
        store.pin(HOST, "bad")
    for value in range(31):
        store.pin(IPv4Address(f"10.0.0.{value + 1}"), DEVICE)
    with pytest.raises(StateError, match="capacity"):
        store.pin(IPv4Address("10.0.1.1"), DEVICE)
    assert len(store.targets()) == 32
    assert path.stat().st_size < module.MAX_BYTES
    assert store.targets()[str(HOST)] == DEVICE


@pytest.mark.parametrize(
    "targets",
    [
        None,
        [],
        {1: DEVICE},
        {str(HOST): 1},
        {str(HOST): "bad"},
        {"127.0.0.1": DEVICE},
        {f"10.0.0.{i}": DEVICE for i in range(33)},
    ],
)
def test_invalid_tables_are_not_adopted(targets: object) -> None:
    with pytest.raises(ValueError, match=r"invalid|loopback"):
        SPEC.parse({"targets": targets})


@pytest.mark.parametrize("problem", ["corrupt", "newer", "symlink", "oversize"])
def test_damaged_pins_stay_fail_closed_on_repeated_calls(tmp_path: Path, problem: str) -> None:
    store = TargetStore(tmp_path)
    store.pin(HOST, DEVICE)
    path = tmp_path / "state" / FILE
    original = path.read_text()
    path.with_suffix(".json.bak").write_text(original)  # Never fall back to old pins.
    if problem == "newer":
        raw = json.loads(original)
        raw["version"] = 2
        path.write_text(json.dumps(raw))
    elif problem == "symlink":
        elsewhere = tmp_path / "other"
        elsewhere.write_text(original)
        path.unlink()
        path.symlink_to(elsewhere)
    else:
        path.write_text("x" * (module.MAX_BYTES + 1) if problem == "oversize" else "damaged")
    for _ in range(2):
        with pytest.raises(StateError, match="pins"):
            store.targets()
        with pytest.raises(StateError, match="pins"):
            store.pin(HOST, DEVICE)
    assert path.exists()


def test_unreadable_pin_table_cannot_enroll(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module,
        "DocumentFile",
        lambda *_args: SimpleNamespace(
            load=lambda: SimpleNamespace(newer_version=None, unreadable=True)
        ),
    )
    with pytest.raises(StateError, match="unavailable"):
        TargetStore(tmp_path).targets()
