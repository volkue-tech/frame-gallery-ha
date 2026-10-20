"""Regular entry/store/publisher wiring with synthetic I/O, never HA or TV access."""

from __future__ import annotations

import json
import signal
from collections import deque
from dataclasses import replace
from ipaddress import IPv4Address, IPv4Network, ip_address
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from tests.support.clock import FakeClock
from tests.support.net import FakeResolver, FakeTransport
from tests.unit.ha.test_current_artwork import response
from tests.unit.observer.test_backend import DEVICE, HOST, Rig
from tests.unit.observer.test_events import envelope
from tests.unit.observer.test_slideshow import rotation, selected

from frame_gallery import __main__ as entry
from frame_gallery.budget.deadline import Deadline
from frame_gallery.ha.current_artwork import OWNER_KEY, PATH
from frame_gallery.isolation.executor import JsonObject
from frame_gallery.isolation.process import Launch
from frame_gallery.observer import stream
from frame_gallery.observer.model import Action, Command
from frame_gallery.observer.stream import SLIDESHOW_POLICY, decode_event
from frame_gallery.store.artwork_bindings import BindingStore
from frame_gallery.store.delivery_associations import DeliveryAssociation, DeliveryAssociations
from frame_gallery.store.layout import StoreLayout
from frame_gallery.store.observer_targets import TargetStore
from frame_gallery.tv.port import target_fingerprint


@pytest.mark.parametrize("refresh", [False])
@pytest.mark.parametrize(
    ("gate", "fail_at", "failure_kind"),
    [
        ("reviewed_fixture", 0, 500),
        ("reviewed_fixture", 1, 500),
        ("reviewed_fixture", 4, 500),
        ("reviewed_fixture", 9, 500),
        ("reviewed_fixture", 4, 401),
        ("reviewed_fixture", 4, 403),
        ("reviewed_fixture", 4, "collision"),
        ("unreviewed", 0, 500),
        ("other_target", 0, 500),
        ("delivery_backed", 0, 500),
        ("delivery_backed", 4, 500),
        ("delivery_backed", 4, 401),
        ("delivery_backed", 4, "collision"),
    ],
)
def test_regular_entry_multiple_cycles_failures_and_no_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    gate: str,
    fail_at: int,
    failure_kind: int | str,
    refresh: bool,
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
                "current_state_refresh": refresh,
            }
        )
    )
    sentinel = host.data / "state" / "user-sentinel.txt"
    sentinel.write_bytes(b"preserve unrelated user state")
    TargetStore(host.data).pin(HOST, DEVICE)
    store = BindingStore(host.data)
    owner = store.owner()
    transport = FakeTransport(clock=clock)
    for index in range(1, 25):
        if index == fail_at:
            if failure_kind == "collision":
                transport.add(response({"attributes": {OWNER_KEY: "different-owner"}}))
            else:
                assert isinstance(failure_kind, int)
                transport.add(response({}, failure_kind))
            break
        transport.add(response({"attributes": {OWNER_KEY: owner}}), response({}))
    resolver = FakeResolver({"supervisor": (ip_address("172.30.32.2"),)})
    monkeypatch.setattr(entry, "_system_network", lambda: (resolver, transport))
    monkeypatch.setattr(
        entry,
        "ContainerNetworks",
        lambda: SimpleNamespace(
            container_networks=lambda: (IPv4Network("172.30.32.0/23"),),
        ),
    )
    monkeypatch.setattr(entry, "StoreLayout", lambda: paths)
    monkeypatch.setattr(entry, "SystemClock", lambda: clock)
    monkeypatch.setattr(entry, "configure_logging", lambda **_kw: None)
    monkeypatch.setattr(
        entry,
        "os",
        SimpleNamespace(
            environ={
                "PATH": "/usr/bin",
                "SUPERVISOR_TOKEN": "synthetic-service-token",
            }
        ),
    )
    monkeypatch.setattr(
        entry,
        "sys",
        SimpleNamespace(
            platform="darwin",
            stdin=SimpleNamespace(fileno=lambda: 123),
            stderr=None,
        ),
    )
    monkeypatch.setattr(Launch, "production", lambda: SimpleNamespace(enforced=True))
    monkeypatch.setattr(
        entry,
        "signal",
        SimpleNamespace(
            SIGTERM=signal.SIGTERM,
            signal=lambda *_a: signal.SIG_DFL,
        ),
    )
    # Test-only internal policy injection, never a shipped personal-device entry.
    monkeypatch.setattr(
        stream,
        "REVIEWED_POLICIES",
        {}
        if gate in {"unreviewed", "delivery_backed"}
        else {
            DEVICE: SLIDESHOW_POLICY,
        },
    )
    monkeypatch.setattr(entry, "ProcessExecutor", lambda *_a: host.executor)

    class Session:
        def __init__(self) -> None:
            self.starts: list[JsonObject] = []
            self.queue: deque[tuple[JsonObject, float]] = deque()

        def start(self, payload: JsonObject) -> None:
            self.starts.append(payload)
            assert payload["device_id"] == DEVICE
            assert payload["policy"] == replace(SLIDESHOW_POLICY, state_refresh=refresh).to_json()
            self.queue.append(
                (
                    {
                        "kind": "baseline",
                        "observation": dict(host.executor.result),
                    },
                    clock.monotonic(),
                )
            )

        def poll(self) -> tuple[JsonObject, float] | None:
            return self.queue.popleft() if self.queue else None

        def stop(self) -> None:
            self.queue.clear()

        def notify(self, body: JsonObject) -> None:
            change = decode_event(envelope(body), SLIDESHOW_POLICY)
            self.queue.append(
                (
                    {
                        "kind": "change",
                        "change": change.to_json(),
                    },
                    clock.monotonic(),
                )
            )

    session = Session()
    monkeypatch.setattr(entry, "SessionProcess", lambda *_a: session)
    sent: list[bool] = []

    def child(_environ: object, _stopping: Any) -> object:
        def send() -> int:
            sent.append(True)
            host.record["delivered_at"] = clock.utc_now().isoformat()
            if gate == "delivery_backed":
                host.record["tv_device_id"] = DEVICE
                DeliveryAssociations(host.data).remember(
                    DeliveryAssociation.from_record(host.record),
                    Deadline.after(clock, 5, "save receipt"),
                )
            if gate == "other_target":
                host.record["tv_target_sha256"] = target_fingerprint(IPv4Address("192.168.1.21"))
            host.save()
            return 0

        return SimpleNamespace(run=send)

    monkeypatch.setattr(entry, "DeliveryProcess", child)
    frozen: dict[str, bytes] = {}
    incoming = SimpleNamespace(closed=False)
    step = 0

    def receive(_timeout: float) -> Command | None:
        nonlocal step
        step += 1
        clock.advance(1)
        if step in {1, 10}:
            return Command(
                Action.REFRESH_CURRENT, f"refresh_{step:03d}", clock.utc_now().timestamp()
            )
        if step == 2:
            return Command(Action.NEW_ARTWORK, "request_001", clock.utc_now().timestamp())
        if step == 3:
            for name in ("current.json", "artwork-bindings.json"):
                file = host.data / "state" / name
                if file.exists():
                    frozen[name] = file.read_bytes()
            clock.advance(100)  # initial caption expires; listener must remain alive
        if step in {4, 6} and session.starts:
            clock.advance(600)
            content_id = "MY_UNKNOWN" if step == 4 else "MY_TEST"
            if refresh:
                session.queue.append(
                    ({"kind": "current_state", "content_id": content_id}, clock.monotonic())
                )
                return None
            bodies: tuple[JsonObject, ...] = (
                selected(content_id),
                rotation(content_id),
                {
                    "event": "art_mode_changed",
                    "status": "on",
                },
            )
            for body in bodies:
                session.notify(body)
        if step == 8:
            clock.advance(900)  # event lease cannot be renewed by a refresh
        if step == 9 and session.starts:
            session.notify({"event": "go_to_standby"})
        if step >= 11:
            incoming.closed = True
        assert step <= 11
        return None

    incoming.receive = receive
    monkeypatch.setattr(entry, "ServiceInput", lambda _fd: incoming)
    assert entry.background_main() == (70 if fail_at else 0)
    posts = [
        json.loads(call.request.body or b"{}")
        for call in transport.calls
        if call.request.method == "POST"
    ]
    assert all(call.request.target == PATH for call in transport.calls)
    assert all(call.request.method in {"GET", "POST"} for call in transport.calls)
    assert len(session.starts) == int(
        gate in {"reviewed_fixture", "delivery_backed"} and fail_at != 1
    )
    assert len(sent) == int(fail_at != 1)
    if fail_at:
        assert len(transport.calls) == (fail_at - 1) * 2 + 1  # no final-state retry
    elif gate in {"reviewed_fixture", "delivery_backed"}:
        captions = [post for post in posts if post["state"] == "artwork"]
        assert len(captions) == 2
        assert captions[0]["attributes"]["title"] == "Synthetic work"
        assert captions[1]["attributes"]["confirmation_method"] == (
            "current_state_read" if refresh else "slideshow_events"
        )
        assert captions[1]["attributes"]["artist"] == "Synthetic Artist"
        unknown = next(post for post in posts if post["state"] == "unidentified")
        assert "title" not in unknown["attributes"]
        assert "artist" not in unknown["attributes"]
        assert posts[-1]["state"] == "paused"
    else:
        assert all(post["state"] != "artwork" for post in posts)
    for name, data in frozen.items():
        assert (host.data / "state" / name).read_bytes() == data
    assert sentinel.read_bytes() == b"preserve unrelated user state"
    assert [name for name, _payload in host.executor.calls] in ([], ["verify_thumbnail"])
    assert not session.queue


def test_real_entry_wires_explicit_state_refresh_and_known_unknown_artwork(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test_regular_entry_multiple_cycles_failures_and_no_resume(
        tmp_path, monkeypatch, "delivery_backed", 0, 500, refresh=True
    )
