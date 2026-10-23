"""Actual service entry + guarded Core reads + stores + captions, fake network only."""

from __future__ import annotations

import base64
import json
import signal
from collections import deque
from datetime import UTC, datetime
from ipaddress import IPv4Network, ip_address
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from tests.support.clock import FakeClock
from tests.support.net import FakeResolver, FakeResponse, FakeTransport
from tests.unit.ha.test_current_artwork import response
from tests.unit.observer.test_backend import DEVICE, HOST, Rig
from tests.unit.observer.test_delivery_attribution import deadline
from tests.unit.store.test_delivery_associations import item

from frame_gallery import __main__ as entry
from frame_gallery.ha.current_artwork import OWNER_KEY, PATH
from frame_gallery.isolation.executor import JsonObject
from frame_gallery.isolation.process import Launch
from frame_gallery.net.wire import WireRequest
from frame_gallery.observer.event_controller import EventController
from frame_gallery.observer.model import Action, Command
from frame_gallery.observer.service import serve as actual_serve
from frame_gallery.observer.wake import CachedStateStopMonitor, WakeEvent
from frame_gallery.store.artwork_bindings import BindingStore
from frame_gallery.store.delivery_associations import DeliveryAssociations
from frame_gallery.store.layout import StoreLayout
from frame_gallery.store.observer_targets import TargetStore
from frame_gallery.tv.port import target_fingerprint
from frame_gallery.tv.token_store import TokenStore

WAKE = "media_player.existing_samsung"


@pytest.mark.parametrize(
    "case",
    [
        "known",
        "unknown",
        "mismatch",
        "other_tv",
        "tv_program",
        "auth",
        "wake_auth",
        "publish_failure",
        "stop_read",
        "no_pin",
        "no_archive",
        "other_target",
        "corrupt_token",
        "tokenless",
    ],
)
@pytest.mark.parametrize("initial", [False, True])
def test_actual_entry_saved_resume_cannot_start_a_tv_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    initial: bool,
) -> None:
    _check_actual_entry(tmp_path, monkeypatch, case, initial)


def _check_actual_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    initial: bool,
    startup_send: bool = False,
    standby: bool = False,
) -> None:
    host, clock = Rig(tmp_path), FakeClock()
    scratch = tmp_path / "tmp"
    scratch.mkdir()
    paths = StoreLayout(data=host.data, media=host.media, tmp=scratch)
    (host.data / "options.json").write_text(
        json.dumps(
            {
                "tv_host": str(HOST),
                "background_mode": True,
                "resume_state_entity": None if case == "unconfigured" else WAKE,
                "current_state_refresh": True,
                "standby_resume": standby,
            }
        )
    )
    if case != "no_pin":
        TargetStore(host.data).pin(HOST, DEVICE)
    archive = DeliveryAssociations(host.data)
    if case != "no_archive":
        archive.remember(
            item(
                device_id=DEVICE,
                content_id="MY_TEST",
                target_sha256="f" * 64 if case == "other_target" else target_fingerprint(HOST),
                reference_rgb=base64.b64encode(b"x" * 6912).decode(),
            ),
            deadline(),
        )
    if case in {"budget_corrupt", "budget_limited"}:
        attempts = [clock.utc_now().timestamp() - 5] if case == "budget_limited" else "bad"
        (host.data / "state/standby-resume-budget.json").write_text(
            json.dumps(
                {
                    "format": "frame-gallery-standby-budget",
                    "version": 1,
                    "attempts": attempts,
                    "auth_blocked": False,
                }
            )
        )
    if case == "corrupt_token":
        (host.data / "tv/192-168-1-20.token").write_text("invalid!")
    elif case == "tokenless":
        TokenStore(host.data, HOST).remove()
    store = BindingStore(host.data)
    owner = store.owner()
    preserved = {
        name: (host.data / "state" / name).read_bytes()
        for name in ("current.json", "observer-targets.json")
        if (host.data / "state" / name).exists()
    }
    preview = (host.preview / "latest.jpg").read_bytes()
    incoming = SimpleNamespace(closed=False, receive=lambda _timeout: None)
    posts: list[dict[str, Any]] = []
    wake_reads = 0

    def reply(request: WireRequest) -> FakeResponse:
        nonlocal wake_reads
        assert request.host == "supervisor"  # no possible TV network route
        if request.target.endswith("/" + WAKE):
            wake_reads += 1
            if case == "wake_auth" and wake_reads >= (1 if initial else 2):
                return response({}, 401)
            if case == "stop_read" and wake_reads >= (1 if initial else 2):
                incoming.closed = True
            on = (
                (initial or clock.elapsed >= 35) if standby else initial or clock.elapsed in (5, 15)
            )
            return response(
                {
                    "entity_id": WAKE,
                    "state": "on" if on else "off",
                    "last_changed": (
                        datetime.fromtimestamp(clock.utc_now().timestamp() - 14400, UTC).isoformat()
                        if initial
                        else datetime.fromtimestamp(
                            clock.utc_now().timestamp() - clock.elapsed + (35 if on else 0), UTC
                        ).isoformat()
                        if standby
                        else clock.utc_now().isoformat()
                    ),
                }
            )
        assert request.target == PATH
        if request.method == "POST":
            posts.append(json.loads(request.body or b""))
            if case == "publish_failure":
                return response({}, 500)
            return response({})
        return response({"attributes": {OWNER_KEY: owner}})

    transport = FakeTransport(handler=reply)
    monkeypatch.setattr(
        entry,
        "_system_network",
        lambda: (FakeResolver(default=(ip_address("172.30.32.2"),)), transport),
    )
    monkeypatch.setattr(
        entry,
        "ContainerNetworks",
        lambda: SimpleNamespace(container_networks=lambda: (IPv4Network("172.30.32.0/23"),)),
    )
    monkeypatch.setattr(entry, "StoreLayout", lambda: paths)
    monkeypatch.setattr(entry, "SystemClock", lambda: clock)
    monkeypatch.setattr(entry, "configure_logging", lambda **_kw: None)
    monkeypatch.setattr(
        entry,
        "os",
        SimpleNamespace(environ={"SUPERVISOR_TOKEN": "synthetic-only", "PATH": "/usr/bin"}),
    )
    monkeypatch.setattr(
        entry,
        "sys",
        SimpleNamespace(platform="darwin", stdin=SimpleNamespace(fileno=lambda: 123), stderr=None),
    )
    monkeypatch.setattr(
        entry, "signal", SimpleNamespace(SIGTERM=signal.SIGTERM, signal=lambda *_a: signal.SIG_DFL)
    )
    monkeypatch.setattr(Launch, "production", lambda: SimpleNamespace(enforced=True))
    monkeypatch.setattr(entry, "ProcessExecutor", lambda *_a: host.executor)

    sends = 0

    def forbid_send() -> int:
        nonlocal sends
        if not startup_send:
            pytest.fail("resume must never invoke delivery")
        sends += 1
        clock.advance(10)
        return 0  # no_match/unchanged receipt, not a fresh delivery grant

    monkeypatch.setattr(entry, "DeliveryProcess", lambda *_a: SimpleNamespace(run=forbid_send))

    class Session:
        def __init__(self) -> None:
            self.starts: list[JsonObject] = []
            self.queue: deque[tuple[JsonObject, float]] = deque()

        def start(self, payload: JsonObject) -> None:
            self.starts.append(payload)
            policy = payload.get("policy", {})
            assert isinstance(policy, dict)
            assert policy.get("state_refresh", False) is False
            assert payload["device_id"] == DEVICE
            assert payload["enroll_device"] is False
            assert payload["tokenless_grant"] is (case == "tokenless")
            baseline = dict(host.executor.result)
            if case == "unknown":
                baseline["content_id"] = "MY_UNKNOWN"
            elif case == "other_tv":
                baseline["device_id"] = "f" * 64
            elif case in {"tv_program", "auth"}:
                baseline = {
                    "status": "tv_in_use" if case == "tv_program" else "not_authorized",
                    "device_id": None,
                    "content_id": None,
                    "thumbnail_sha256": None,
                }
            host.executor.matched = case != "mismatch"
            self.queue.append(({"kind": "baseline", "observation": baseline}, clock.monotonic()))

        def poll(self) -> tuple[JsonObject, float] | None:
            return self.queue.popleft() if self.queue else None

        def stop(self) -> None:
            self.queue.clear()

    session = Session()
    monkeypatch.setattr(entry, "SessionProcess", lambda *_a: session)
    monkeypatch.setattr(entry, "ServiceInput", lambda _fd: incoming)

    def serve_standby(controller: EventController) -> None:
        controller.start()
        controller.tick()
        for _ in range(10):
            clock.advance(5)
            controller.tick()
        denied = {
            "no_pin",
            "no_archive",
            "other_target",
            "corrupt_token",
            "wake_auth",
            "stop_read",
            "publish_failure",
            "unconfigured",
            "budget_corrupt",
            "budget_limited",
        }
        expected = 0 if initial or case in denied else 1
        assert len(session.starts) == expected
        assert not controller.resume()  # a consumed grant cannot be reused directly
        for _ in range(20):
            clock.advance(5)
            controller.tick()
        assert len(session.starts) == expected
        if case == "auth" and not initial:
            saved_budget = json.loads((host.data / "state/standby-resume-budget.json").read_text())
            assert saved_budget["auth_blocked"] is True
        if not initial and case in {"known", "tokenless"}:
            assert any(p["state"] == "artwork" for p in posts)
        elif case in {"unknown", "other_tv", "mismatch", "tv_program", "auth"}:
            assert not any("artist" in p["attributes"] for p in posts)
        controller.stop()
        if case not in {"publish_failure"}:
            assert posts[-1]["attributes"]["status_reason"] == "service_stopped"

    def serve(controller: EventController, _read: Any, stopped: Any) -> None:
        if standby:
            serve_standby(controller)
            return
        if startup_send:
            issued = False

            def receive(timeout: float) -> Command | None:
                nonlocal issued
                clock.advance(timeout)
                if not issued and clock.elapsed >= 2:
                    issued = True
                    return Command(
                        Action.NEW_ARTWORK, "startup_send_001", clock.utc_now().timestamp()
                    )
                if clock.elapsed >= 30:
                    incoming.closed = True
                return None

            actual_serve(controller, receive, stopped)
            assert sends == 1
            assert not session.starts  # neither pre-send initial nor no_match retry
            assert not any("artist" in p["attributes"] for p in posts)
            return
        controller.start()
        controller.tick()
        if not initial:
            assert not session.starts  # observed off, no initial request
        for _ in range(3):
            clock.advance(5)
            controller.tick()
        # D-247: saved experimental options and even an intact archive do not
        # make HA on a sufficient authorization to open another Art socket.
        assert not session.starts
        assert not controller.resume()
        assert not any("artist" in p["attributes"] for p in posts)
        if case == "wake_auth":
            assert wake_reads == (1 if initial else 2)
        if case in {"stop_read", "publish_failure"}:
            assert stopped()
        if initial and case in {"known", "tokenless"}:
            clock.advance(90)  # Static Art Mode is not a renewing pixel proof.
            controller.tick()
            assert not session.starts
            assert "artist" not in posts[-1]["attributes"]
        controller.stop()

    monkeypatch.setattr(entry, "serve", serve)
    assert entry.background_main() == (70 if case == "publish_failure" else 0)
    assert preserved == {name: (host.data / "state" / name).read_bytes() for name in preserved}
    assert (host.preview / "latest.jpg").read_bytes() == preview
    assert not any(task in {"send", "upload", "select"} for task, _ in host.executor.calls)


def test_actual_entry_startup_send_consumes_automatic_read_even_on_no_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _check_actual_entry(tmp_path, monkeypatch, case="known", initial=True, startup_send=True)


@pytest.mark.parametrize(
    "case",
    [
        "known",
        "unknown",
        "mismatch",
        "other_tv",
        "tv_program",
        "auth",
        "wake_auth",
        "publish_failure",
        "stop_read",
        "no_pin",
        "no_archive",
        "other_target",
        "corrupt_token",
        "tokenless",
        "unconfigured",
        "budget_corrupt",
        "budget_limited",
    ],
)
@pytest.mark.parametrize("initial", [False, True])
def test_actual_entry_new_consent_one_settled_standby_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    initial: bool,
) -> None:
    _check_actual_entry(tmp_path, monkeypatch, case=case, initial=initial, standby=True)


def test_production_resume_hook_stays_denied_even_if_a_monitor_emits_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Independent second barrier: even a broken/replaced monitor cannot make
    # the production controller call HostObserver.prepare_resume/open a socket.
    monkeypatch.setattr(CachedStateStopMonitor, "poll", lambda _self: WakeEvent.RESUME)
    _check_actual_entry(tmp_path, monkeypatch, case="known", initial=True)
