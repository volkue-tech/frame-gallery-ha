from __future__ import annotations

import json
import signal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from tests.support.clock import FakeClock

from frame_gallery import __main__ as entry
from frame_gallery.errors import AlreadyRunning, StateError
from frame_gallery.isolation.apparmor import ProfileError
from frame_gallery.isolation.process import Launch
from frame_gallery.observer.event_controller import EventController
from frame_gallery.observer.model import Action, Command, Observation, Status
from frame_gallery.store.layout import StoreLayout


def layout(root: Path) -> StoreLayout:
    for name in ("data", "media", "tmp"):
        (root / name).mkdir()
    result = StoreLayout(data=root / "data", media=root / "media", tmp=root / "tmp")
    (result.data / "options.json").write_text(
        json.dumps({"tv_host": "192.168.1.20", "background_mode": True})
    )
    return result


def test_main_dispatch_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        entry, "OptionsFile", lambda _data: SimpleNamespace(background_mode=lambda: True)
    )
    monkeypatch.setattr(entry, "background_main", lambda: 42)
    assert entry.main() == 42


@pytest.mark.parametrize("has_token", [False, True])
@pytest.mark.parametrize("refuse", [False, True])
@pytest.mark.parametrize("auth_failure", [False, True])
@pytest.mark.parametrize("platform", ["darwin", "linux"])
@pytest.mark.parametrize("send_result", [0, 70, "stop", "no_match", "cleanup_failed"])
def test_background_entry_waits_for_explicit_successful_send_before_reading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    has_token: bool,
    refuse: bool,
    auth_failure: bool,
    platform: str,
    send_result: int | str,
) -> None:
    paths, clock = layout(tmp_path), FakeClock()
    state_dir = paths.data / "state"
    state_dir.mkdir()
    leftover = state_dir / "observer-targets.json.tmp-0123456789abcdef"
    leftover.write_bytes(b"interrupted atomic write")
    (state_dir / "keep.txt").write_bytes(b"preserve")
    state_closed: list[bool] = []
    if send_result == "cleanup_failed":

        def refuse_cleanup(_deadline: object) -> None:
            raise (StateError("synthetic") if has_token else AlreadyRunning())

        monkeypatch.setattr(
            StoreLayout,
            "state_store",
            lambda _self, _clock: SimpleNamespace(
                open=refuse_cleanup, close=lambda: state_closed.append(True)
            ),
        )
    environ = {"PATH": "/usr/bin", "HTTP_PROXY": "must-go-away"}
    if has_token:
        environ["SUPERVISOR_TOKEN"] = "synthetic-token-not-real"  # noqa: S105
    monkeypatch.setattr(entry, "StoreLayout", lambda: paths)
    monkeypatch.setattr(entry, "SystemClock", lambda: clock)
    monkeypatch.setattr(entry, "os", SimpleNamespace(environ=environ))
    monkeypatch.setattr(
        entry,
        "sys",
        SimpleNamespace(platform=platform, stdin=SimpleNamespace(fileno=lambda: 123), stderr=None),
    )
    monkeypatch.setattr(
        Launch,
        "production",
        lambda: SimpleNamespace(enforced=True, apparmor_profile="frame_gallery"),
    )
    monkeypatch.setattr(entry, "configure_logging", lambda **_kwargs: None)
    monkeypatch.setattr(
        entry, "ContainerNetworks", lambda: SimpleNamespace(container_networks=lambda: ())
    )
    monkeypatch.setattr(entry, "_system_network", lambda: (None, None))
    published: list[Observation] = []

    class Publisher:
        authorization_refused = False

        def __init__(self, **_kwargs: object) -> None:
            pass

        def publish(
            self,
            _owner: str,
            seen: Observation,
            _binding: object,
            _deadline: object,
            **_kwargs: object,
        ) -> bool:
            published.append(seen)
            self.authorization_refused = refuse and auth_failure
            return not refuse

    monkeypatch.setattr(entry, "CurrentArtworkPublisher", Publisher)
    closed: list[bool] = []
    reads: list[bool] = []

    def read(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        reads.append(True)
        return Observation(Status.TV_IN_USE).to_json()

    monkeypatch.setattr(
        entry,
        "ProcessExecutor",
        lambda *_args: SimpleNamespace(run=read, terminate_all=lambda: closed.append(True)),
    )
    received = SimpleNamespace(closed=False, receive=lambda _timeout: None)
    monkeypatch.setattr(entry, "ServiceInput", lambda _fd: received)
    sent: list[bool] = []

    def child(values: dict[str, str], stopping: Any) -> object:
        assert "HTTP_PROXY" not in values
        assert ("SUPERVISOR_TOKEN" in values) is has_token
        assert not stopping()

        def send() -> int:
            sent.append(True)
            if send_result == "stop":
                received.closed = True
                return 0
            if send_result == "no_match":
                return 0
            assert isinstance(send_result, int)
            if send_result == 0:
                (paths.data / "state" / "current.json").write_text(
                    json.dumps(
                        {
                            "format": "frame-gallery-current",
                            "version": 1,
                            "tv_content_id": "MY_TEST",
                        }
                    )
                )
            return send_result

        return SimpleNamespace(run=send)

    monkeypatch.setattr(entry, "DeliveryProcess", child)
    signals: list[Any] = []

    def handler(_number: object, callback: Any) -> Any:
        signals.append(callback)
        return signal.SIG_DFL

    monkeypatch.setattr(entry, "signal", SimpleNamespace(SIGTERM=signal.SIGTERM, signal=handler))

    def serve(controller: EventController, _receive: Any, stopped: Any) -> None:
        assert not stopped()
        controller.start()
        clock.advance(60)
        controller.tick()
        assert reads == sent == []
        controller.command(Command(Action.NEW_ARTWORK, "request_123", clock.utc_now().timestamp()))
        controller.command(
            Command(Action.REFRESH_CURRENT, "refresh_123", clock.utc_now().timestamp())
        )
        if has_token:
            received.closed = True
        else:
            signals[0](signal.SIGTERM, None)
        assert stopped()
        controller.stop()

    monkeypatch.setattr(entry, "serve", serve)
    if send_result == "cleanup_failed":
        assert entry.background_main() == 70
        assert sent == reads == []
        assert published == []
        assert state_closed == [True]
        assert leftover.exists()
        assert closed == [True]
        return
    assert entry.background_main() == (70 if refuse else 0)
    assert sent == ([] if refuse else [True])
    # No real device-event profile is approved: even a successful explicit
    # delivery cannot silently restore the old short-lived polling path.
    assert reads == []
    assert published[-1].status is (Status.VALIDATION_REQUIRED if refuse else Status.PAUSED)
    if refuse:
        assert len(published) == 1  # no retry even for non-auth publication failure
    assert "SUPERVISOR_TOKEN" not in environ
    assert closed == [True]
    assert signals[-1] == signal.SIG_DFL
    assert not leftover.exists()
    assert (state_dir / "keep.txt").read_bytes() == b"preserve"


@pytest.mark.parametrize("problem", ["options", "profile", "isolation", "apparmor"])
def test_background_entry_refuses_invalid_or_unconfined_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, problem: str
) -> None:
    paths = layout(tmp_path)
    monkeypatch.setattr(entry, "StoreLayout", lambda: paths)
    monkeypatch.setattr(
        entry, "ContainerNetworks", lambda: SimpleNamespace(container_networks=lambda: ())
    )
    monkeypatch.setattr(entry, "sys", SimpleNamespace(platform="linux"))
    if problem == "options":
        (paths.data / "options.json").write_text("bad")

    def launch() -> object:
        if problem == "profile":
            raise ProfileError("synthetic refusal")
        return SimpleNamespace(
            enforced=problem != "isolation",
            apparmor_profile=None if problem == "apparmor" else "frame_gallery",
        )

    monkeypatch.setattr(Launch, "production", launch)
    assert entry.background_main() == 70
