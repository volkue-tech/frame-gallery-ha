"""Actual service entry + guarded Core reads + stores + captions, fake network only."""

from __future__ import annotations

import base64
import json
import signal
from collections import deque
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
from frame_gallery.store.artwork_bindings import BindingStore
from frame_gallery.store.delivery_associations import DeliveryAssociations
from frame_gallery.store.layout import StoreLayout
from frame_gallery.store.observer_targets import TargetStore
from frame_gallery.tv.port import target_fingerprint

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
    ],
)
def test_actual_entry_wake_never_sends_and_requires_new_validated_image(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    host, clock = Rig(tmp_path), FakeClock()
    scratch = tmp_path / "tmp"
    scratch.mkdir()
    paths = StoreLayout(data=host.data, media=host.media, tmp=scratch)
    (host.data / "options.json").write_text(
        json.dumps({"tv_host": str(HOST), "background_mode": True, "resume_state_entity": WAKE})
    )
    TargetStore(host.data).pin(HOST, DEVICE)
    archive = DeliveryAssociations(host.data)
    archive.remember(
        item(
            device_id=DEVICE,
            content_id="MY_TEST",
            target_sha256=target_fingerprint(HOST),
            reference_rgb=base64.b64encode(b"x" * 6912).decode(),
        ),
        deadline(),
    )
    store = BindingStore(host.data)
    owner = store.owner()
    preserved = {
        name: (host.data / "state" / name).read_bytes()
        for name in ("current.json", "observer-targets.json")
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
            if case == "wake_auth" and wake_reads > 1:
                return response({}, 401)
            if case == "stop_read" and wake_reads > 1:
                incoming.closed = True
            on = clock.elapsed in (5, 15)
            return response(
                {
                    "entity_id": WAKE,
                    "state": "on" if on else "off",
                    "last_changed": clock.utc_now().isoformat(),
                }
            )
        assert request.target == PATH
        if request.method == "POST":
            posts.append(json.loads(request.body or b""))
            if case == "publish_failure" and posts[-1]["state"] == "checking":
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

    def forbid_send() -> int:
        pytest.fail("resume must never invoke delivery")

    monkeypatch.setattr(entry, "DeliveryProcess", lambda *_a: SimpleNamespace(run=forbid_send))

    class Session:
        def __init__(self) -> None:
            self.starts: list[JsonObject] = []
            self.queue: deque[tuple[JsonObject, float]] = deque()

        def start(self, payload: JsonObject) -> None:
            self.starts.append(payload)
            assert payload["device_id"] == DEVICE
            assert payload["enroll_device"] is False
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

    def serve(controller: EventController, _read: Any, stopped: Any) -> None:
        controller.start()
        controller.tick()  # observed off, no network session
        assert not session.starts
        for _ in range(3):
            clock.advance(5)
            controller.tick()
        if case in {"known", "unknown", "mismatch", "other_tv", "tv_program"}:
            assert len(session.starts) == 2
        elif case == "auth":
            assert len(session.starts) == 1  # auth refusal never retried on next wake
        else:
            assert not session.starts
        if case == "known":
            assert any(
                p["state"] == "artwork" and p["attributes"]["artist"] == "An artist" for p in posts
            )
        else:
            assert not any("artist" in p["attributes"] for p in posts)
        if case == "wake_auth":
            assert wake_reads == 2
        if case in {"stop_read", "publish_failure"}:
            assert stopped()
        controller.stop()

    monkeypatch.setattr(entry, "serve", serve)
    assert entry.background_main() == (70 if case == "publish_failure" else 0)
    assert preserved == {name: (host.data / "state" / name).read_bytes() for name in preserved}
    assert (host.preview / "latest.jpg").read_bytes() == preview
    assert not any(task in {"send", "upload", "select"} for task, _ in host.executor.calls)
