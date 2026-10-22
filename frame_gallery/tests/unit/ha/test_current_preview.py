"""Preview availability is an acknowledged two-phase operation, not artwork proof."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from frame_gallery.budget.deadline import Deadline
from frame_gallery.observer.model import Evidence, Observation, Status
from frame_gallery.store.current_preview import NEUTRAL_JPEG, CurrentPreview
from frame_gallery.store.preview_cache import PreviewCache
from tests.unit.ha.test_current_artwork import OWNER, Rig, response
from tests.unit.store.test_current_preview import encoded
from tests.unit.store.test_delivery_associations import item


def observation() -> Observation:
    return Observation(Status.UNIDENTIFIED, "a" * 64, "MY_F0001", None, Evidence.CURRENT_STATE)


def test_preview_changes_only_after_acknowledged_invalidation(tmp_path: Path) -> None:
    rig = Rig()
    PreviewCache(tmp_path).remember(item(), encoded(), Deadline.after(rig.clock, 5, "cache"))
    target = tmp_path / "frame_gallery/preview/current.jpg"
    target.parent.mkdir(parents=True)
    target.write_bytes(NEUTRAL_JPEG)
    current = CurrentPreview(tmp_path, tmp_path)
    rig.transport.add(response({}, 404), response({}), response({}))

    def prepare(binding: object, deadline: Deadline) -> str | None:
        assert len(rig.transport.calls) == 2
        first = json.loads(rig.transport.calls[-1].request.body or b"")
        assert first["attributes"]["preview_available"] is False
        assert first["attributes"]["title"] == "A title"
        return current.publish(item(), deadline)

    assert rig.client.publish(
        OWNER, observation(), item(), Deadline.after(rig.clock, 2, "test"), prepare_preview=prepare
    )
    final = json.loads(rig.transport.calls[-1].request.body or b"")
    assert final["attributes"]["preview_available"] is True
    assert final["attributes"]["preview_sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert [c.request.method for c in rig.transport.calls] == ["GET", "POST", "POST"]


@pytest.mark.parametrize("status", [401, 403, 500])
def test_failed_invalidation_never_touches_current_file(status: int) -> None:
    rig = Rig()
    calls: list[object] = []
    rig.transport.add(response({}, 404), response({}, status))
    assert not rig.client.publish(
        OWNER,
        observation(),
        item(),
        Deadline.after(rig.clock, 2, "test"),
        prepare_preview=lambda *_args: calls.append(True),
    )
    assert not calls


def test_final_state_failure_leaves_acknowledged_preview_hidden() -> None:
    rig = Rig()
    rig.transport.add(response({}, 404), response({}), response({}, 500))
    assert not rig.client.publish(
        OWNER,
        observation(),
        item(),
        Deadline.after(rig.clock, 2, "test"),
        prepare_preview=lambda *_args: "f" * 64,
    )
    first = json.loads(rig.transport.calls[1].request.body or b"")
    assert first["state"] == "artwork"
    assert first["attributes"]["preview_available"] is False
    assert "preview_sha256" not in first["attributes"]


def test_absent_cache_keeps_correct_metadata_without_extra_post(tmp_path: Path) -> None:
    rig = Rig()
    rig.transport.add(response({}, 404), response({}))
    assert rig.client.publish(
        OWNER,
        observation(),
        item(),
        Deadline.after(rig.clock, 2, "test"),
        prepare_preview=CurrentPreview(tmp_path, tmp_path).publish,
    )
    body = json.loads(rig.transport.calls[-1].request.body or b"")
    assert body["state"] == "artwork"
    assert body["attributes"]["title"] == "A title"
    assert body["attributes"]["preview_available"] is False
    assert len(rig.transport.calls) == 2


@pytest.mark.parametrize("has_binding", [True, False])
def test_unbound_or_bad_digest_never_advertised(has_binding: bool) -> None:
    rig = Rig()
    rig.transport.add(response({}, 404), response({}))
    assert not rig.client.publish(
        OWNER,
        observation(),
        item() if has_binding else None,
        Deadline.after(rig.clock, 2, "test"),
        prepare_preview=lambda *_args: "bad" if has_binding else "a" * 64,
    )
    assert len(rig.transport.calls) == 2
