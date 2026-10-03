"""Fail-closed transitions, including OS refusal and short writes."""

from __future__ import annotations

import io
import sys
from collections.abc import Buffer
from pathlib import Path

import pytest

from frame_gallery.isolation import apparmor as aa
from frame_gallery.isolation import bootstrap
from tests.unit.isolation.test_bootstrap import FakeOs, config


@pytest.mark.parametrize(
    "name", ["frame_gallery", "local_frame_gallery_dev", "0123abcd_frame_gallery"]
)
def test_parent_names(name: str) -> None:
    assert aa.valid_parent(name)


@pytest.mark.parametrize(
    "name",
    [
        "unconfined",
        "docker-default",
        "x_frame_gallery",
        "frame_gallery//tv_worker",
        "frame_gallery\n",
    ],
)
def test_other_names(name: str) -> None:
    assert not aa.valid_parent(name)


def test_read_is_bounded_and_removes_kernel_terminators(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "current"
    path.write_bytes(b"frame_gallery (enforce)\n\x00")
    monkeypatch.setattr(aa, "CURRENT", path)
    assert aa.read_current() == "frame_gallery (enforce)"
    path.write_bytes(b"a" * 2048)
    assert len(aa.read_current()) == 1025


def test_development_and_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    assert aa.parent_profile() is None
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(aa, "read_current", lambda: "docker-default (enforce)")
    assert aa.parent_profile() is None
    monkeypatch.setattr(aa, "read_current", lambda: "frame_gallery (enforce)")
    assert aa.parent_profile() == "frame_gallery"
    monkeypatch.setattr(aa, "read_current", lambda: "frame_gallery (complain)")
    with pytest.raises(aa.ProfileError, match="parent_not_enforced"):
        aa.parent_profile()


@pytest.mark.parametrize("error", [OSError(), UnicodeError()])
def test_missing_interface(monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
    monkeypatch.setattr(sys, "platform", "linux")

    def failed() -> str:
        raise error

    monkeypatch.setattr(aa, "read_current", failed)
    assert aa.parent_profile() is None


@pytest.mark.parametrize(
    ("task", "child"),
    [("prepare", "image_worker"), ("inspect", "image_worker"), ("deliver", "tv_worker")],
)
def test_transition(task: str, child: str, monkeypatch: pytest.MonkeyPatch) -> None:
    target = f"frame_gallery//{child}"
    readings = iter(["frame_gallery (enforce)", f"{target} (enforce)"])
    calls: list[str] = []
    monkeypatch.setattr(aa, "read_current", lambda: next(readings))
    monkeypatch.setattr(aa, "change_profile", calls.append)
    assert aa.confine("frame_gallery", task) == target
    assert calls == [target]
    assert aa.confine(None, task) is None


@pytest.mark.parametrize(
    ("parent", "task"), [("unconfined", "prepare"), ("frame_gallery", "unknown")]
)
def test_invalid_target(parent: str, task: str) -> None:
    with pytest.raises(aa.ProfileError, match="transition_target"):
        aa.confine(parent, task)


@pytest.mark.parametrize(
    ("labels", "reason"),
    [
        (["frame_gallery (complain)"], "origin"),
        (["frame_gallery (enforce)", "frame_gallery (enforce)"], "not_enforced"),
        (["frame_gallery (enforce)", "frame_gallery//image_worker (complain)"], "not_enforced"),
    ],
)
def test_wrong_labels(labels: list[str], reason: str, monkeypatch: pytest.MonkeyPatch) -> None:
    readings = iter(labels)
    monkeypatch.setattr(aa, "read_current", lambda: next(readings))
    monkeypatch.setattr(aa, "change_profile", lambda target: None)
    with pytest.raises(aa.ProfileError, match=reason):
        aa.confine("frame_gallery", "prepare")


@pytest.mark.parametrize("error", [PermissionError(), UnicodeError()])
def test_transition_os_failure(monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
    monkeypatch.setattr(aa, "read_current", lambda: "frame_gallery (enforce)")

    def failed(target: str) -> None:
        raise error

    monkeypatch.setattr(aa, "change_profile", failed)
    with pytest.raises(aa.ProfileError, match="transition_failed"):
        aa.confine("frame_gallery", "prepare")


def test_write_protocol(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "current"
    monkeypatch.setattr(aa, "CURRENT", path)
    aa.change_profile("frame_gallery//image_worker")
    assert path.read_bytes() == b"changeprofile frame_gallery//image_worker"


def test_short_write(monkeypatch: pytest.MonkeyPatch) -> None:
    class Short(io.BytesIO):
        def write(self, value: Buffer, /) -> int:
            return 1

    monkeypatch.setattr(Path, "open", lambda *args, **kwargs: Short())
    with pytest.raises(aa.ProfileError, match="short_write"):
        aa.change_profile("frame_gallery//image_worker")


def test_bootstrap_switches_before_privilege_drop(monkeypatch: pytest.MonkeyPatch) -> None:
    ops = FakeOs()

    def switch(parent: str | None, task: str) -> str:
        assert ops.geteuid() == 0
        assert ops.calls == []
        return "frame_gallery//image_worker"

    monkeypatch.setattr(bootstrap, "confine", switch)
    monkeypatch.setattr(bootstrap, "install_network_filter", lambda task: None)
    report = bootstrap.run(config(apparmor_profile="frame_gallery"), ops, lambda value: None)
    assert report["apparmor_profile"] == "frame_gallery//image_worker"


def test_bootstrap_refuses_before_reading_artwork(monkeypatch: pytest.MonkeyPatch) -> None:
    ops = FakeOs()

    def refused(parent: str | None, task: str) -> str:
        raise aa.ProfileError("test")

    monkeypatch.setattr(bootstrap, "confine", refused)
    with pytest.raises(bootstrap.Refused, match="apparmor:test"):
        bootstrap.run(config(apparmor_profile="frame_gallery"), ops, lambda value: None)
    assert ops.calls == []
