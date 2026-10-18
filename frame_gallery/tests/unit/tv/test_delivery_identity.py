"""An actual delivery learns device identity without a second capability GET."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from frame_gallery.isolation.executor import JsonObject
from frame_gallery.tv.identity import device_digest
from frame_gallery.tv.samsung import _EventRelay
from tests.unit.tv.test_samsung_task import Rig


@pytest.mark.parametrize(
    "info",
    [
        None,
        [],
        {},
        {"device": None},
        {"device": {"id": None}},
        {"device": {"id": " "}},
        {"device": {"id": "x" * 129}},
        {"device": {"id": "bad\nidentity"}},
    ],
)
def test_missing_identity_never_falls_back_to_ip_or_model(info: object) -> None:
    assert device_digest(info) is None


def test_identity_normalizes_only_case_and_surrounding_space() -> None:
    assert (
        device_digest({"device": {"id": " UUID:Test-TV "}})
        == hashlib.sha256(b"uuid:test-tv").hexdigest()
    )


def test_existing_support_read_is_captured_once_and_method_restored(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    original = rig.library.art_class
    reads = []
    rest = SimpleNamespace()

    def read_info() -> dict[str, dict[str, str]]:
        reads.append(True)
        return {"device": {"id": "uuid:test-tv", "FrameTVSupport": "true"}}

    rest.rest_device_info = read_info

    def art_class(*args: Any, **kwargs: Any) -> Any:
        art = original(*args, **kwargs)
        art._get_rest_api = lambda: rest
        return art

    object.__setattr__(rig.library, "art_class", art_class)
    assert rig.run()["status"] == "ok"
    assert len(reads) == 1
    assert rest.rest_device_info is read_info
    digest = device_digest(read_info())
    assert digest is not None
    assert 'event:{"device_id": "' + digest + '"}' in rig.events


def test_legacy_transport_without_cached_rest_getter_still_delivers(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    original = rig.library.art_class

    def art_class(*args: Any, **kwargs: Any) -> Any:
        art = original(*args, **kwargs)
        art._get_rest_api = None
        art.supported = lambda: True
        return art

    object.__setattr__(rig.library, "art_class", art_class)
    assert rig.run()["status"] == "ok"
    assert not any('"device_id"' in event for event in rig.events)


def test_relay_accepts_only_one_valid_identity_before_other_events() -> None:
    relay = _EventRelay(lambda _: None, lambda _: None)
    relay({"device_id": "a" * 64})
    assert relay.device_id == "a" * 64
    with pytest.raises(ValueError, match="identity"):
        relay({"device_id": "b" * 64})
    with pytest.raises(ValueError, match="identity"):
        _EventRelay(lambda _: None, lambda _: None)({"device_id": "an IP is not an identity"})


@pytest.mark.parametrize(
    "first", [{"token": "12345678"}, {"marker": "connected", "content_id": None}]
)
def test_late_device_identity_cannot_rebind_in_progress_upload(first: JsonObject) -> None:
    relay = _EventRelay(lambda _: None, lambda _: None)
    relay(first)
    with pytest.raises(ValueError, match="identity"):
        relay({"device_id": "a" * 64})
