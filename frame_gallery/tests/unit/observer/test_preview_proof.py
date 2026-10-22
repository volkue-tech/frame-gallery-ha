"""Fresh thumbnail proof may select exact cached upload bytes, never metadata alone."""

from __future__ import annotations

import base64
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

import pytest
from tests.unit.observer.test_backend import DEVICE, HOST, THUMBNAIL_HASH, Executor
from tests.unit.store.test_current_preview import deadline, encoded
from tests.unit.store.test_delivery_associations import item

from frame_gallery.errors import StateError
from frame_gallery.isolation.executor import WorkerError
from frame_gallery.observer.backend import HostObserver
from frame_gallery.observer.model import Evidence, Observation, Status
from frame_gallery.store.artwork_bindings import Binding, BindingStore
from frame_gallery.store.current_preview import NEUTRAL_JPEG, CurrentPreview
from frame_gallery.store.delivery_associations import DeliveryAssociation, DeliveryAssociations
from frame_gallery.store.preview_cache import PreviewCache


class Rig:
    def __init__(self, root: Path, *, reference: bool = True, cached: bool = True) -> None:
        self.data, self.media = root / "data", root / "media"
        self.data.mkdir()
        self.media.mkdir()
        self.entry = item(
            device_id=DEVICE,
            reference_rgb=base64.b64encode(b"x" * 6912).decode() if reference else None,
        )
        self.archive = DeliveryAssociations(self.data)
        self.archive.remember(self.entry, deadline())
        if cached:
            PreviewCache(self.data).remember(self.entry, encoded(), deadline())
        self.executor = Executor()
        self.observer = HostObserver(self.executor, self.data, self.media, HOST, device_id=DEVICE)
        self.seen = Observation(Status.UNIDENTIFIED, DEVICE, self.entry.content_id, THUMBNAIL_HASH)
        fields = {
            name: getattr(self.entry, name)
            for name in (
                "device_id",
                "content_id",
                "work_id",
                "title",
                "artist",
                "source",
                "detail_url",
                "recorded_at",
            )
        }
        self.binding = Binding.from_json(dict(fields, thumbnail_sha256=THUMBNAIL_HASH))

    def accept(self) -> Observation:
        return self.observer.accept_snapshot(dict(self.seen.to_json(), thumbnail="eA=="))

    def selected(self) -> DeliveryAssociation | None:
        return self.observer.preview_association(
            self.seen, BindingStore(self.data).resolve(self.seen)
        )


@pytest.mark.parametrize("old_binding", [False, True])
def test_initial_thumbnail_selects_cached_exact_upload_without_changing_caption_proof(
    tmp_path: Path,
    old_binding: bool,
) -> None:
    rig = Rig(tmp_path)
    if old_binding:
        BindingStore(rig.data).remember(rig.binding)
    assert rig.observer.preview_association(rig.seen, rig.binding) is None
    assert rig.accept() == rig.seen
    caption = BindingStore(rig.data).resolve(rig.seen)
    assert isinstance(caption, Binding)
    assert not rig.entry.matches(rig.seen)  # Upload evidence is still not thumbnail evidence.
    assert rig.selected() == rig.entry
    current = CurrentPreview(rig.data, rig.media)
    assert current.publish(rig.selected(), deadline()) is not None
    assert (rig.media / "frame_gallery/preview/current.jpg").read_bytes() == base64.b64decode(
        encoded()
    )
    assert [task for task, _ in rig.executor.calls] == ["verify_thumbnail"]


def test_old_matching_binding_cannot_select_new_same_work_different_crop(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    BindingStore(rig.data).remember(rig.binding)
    # Same work/title/TV/ID but a replaced upload whose actual image is different.
    rig.entry = replace(rig.entry, jpeg_sha256="e" * 64)
    rig.archive.remember(rig.entry, deadline())
    PreviewCache(rig.data).remember(rig.entry, encoded("red"), deadline())
    rig.executor.matched = False
    rig.accept()
    assert rig.selected() is None
    assert BindingStore(rig.data).resolve(rig.seen) is None
    rejected = rig.archive.find(DEVICE, rig.entry.content_id)
    assert rejected is not None
    assert rejected.image_rejected
    assert [task for task, _ in rig.executor.calls] == ["verify_thumbnail"]


@pytest.mark.parametrize(
    "change",
    [
        {"device_id": "d" * 64},
        {"content_id": "MY_OTHER"},
        {"thumbnail_sha256": "f" * 64},
        {"work_id": "commons:124"},
        {"title": "Other title"},
        {"artist": "Other artist"},
        {"source": "aic"},
        {"detail_url": "https://example.test/other"},
    ],
)
def test_preview_proof_refuses_conflicting_caption_identity(
    tmp_path: Path, change: dict[str, str]
) -> None:
    rig = Rig(tmp_path)
    rig.accept()
    wrong = Binding.from_json(dict(asdict(rig.binding), **change))
    assert rig.observer.preview_association(rig.seen, wrong) is None


@pytest.mark.parametrize(
    "change",
    [
        {"jpeg_sha256": "e" * 64},
        {"image_rejected": True},
        {"reference_rgb": None},
    ],
)
def test_delayed_receipt_replacement_invalidates_exact_proof(
    tmp_path: Path, change: dict[str, object]
) -> None:
    rig = Rig(tmp_path)
    rig.accept()
    rig.archive.remember(
        DeliveryAssociation.from_json(dict(asdict(rig.entry), **change)), deadline()
    )
    assert rig.selected() is None


@pytest.mark.parametrize(
    "reset", ["delivery", "resume", "session", "pause", "different", "slideshow"]
)
def test_proof_is_only_valid_for_its_current_session(tmp_path: Path, reset: str) -> None:
    rig = Rig(tmp_path)
    rig.accept()
    assert rig.selected() == rig.entry
    if reset == "delivery":
        rig.observer.after_delivery(None)
    elif reset == "resume":
        rig.observer.prepare_resume()
    elif reset == "session":
        rig.observer.session_request()
    elif reset == "pause":
        assert rig.observer.preview_association(Observation(Status.PAUSED), None) is None
    elif reset == "different":
        assert (
            rig.observer.preview_association(replace(rig.seen, content_id="MY_OTHER"), None) is None
        )
    else:
        slideshow = replace(rig.seen, evidence=Evidence.SLIDESHOW, thumbnail_sha256=None)
        assert rig.observer.preview_association(slideshow, rig.entry) == rig.entry
    assert rig.observer.preview_association(rig.seen, rig.binding) is None


@pytest.mark.parametrize(("reference", "cached"), [(False, True), (True, False)])
def test_legacy_binding_or_missing_cache_remains_caption_only(
    tmp_path: Path,
    reference: bool,
    cached: bool,
) -> None:
    rig = Rig(tmp_path, reference=reference, cached=cached)
    BindingStore(rig.data).remember(rig.binding)
    rig.accept()
    assert isinstance(BindingStore(rig.data).resolve(rig.seen), Binding)
    current = CurrentPreview(rig.data, rig.media)
    assert current.publish(rig.selected(), deadline()) is None
    assert (rig.media / "frame_gallery/preview/current.jpg").read_bytes() == NEUTRAL_JPEG


def test_optional_preview_verification_failure_keeps_previously_verified_caption(
    tmp_path: Path,
) -> None:
    rig = Rig(tmp_path)
    BindingStore(rig.data).remember(rig.binding)
    rig.executor.failure = True
    assert rig.accept() == rig.seen
    assert BindingStore(rig.data).resolve(rig.seen) == rig.binding
    assert rig.selected() is None


def test_unverified_initial_image_does_not_hide_verification_failure(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.executor.failure = True
    with pytest.raises(WorkerError):
        rig.accept()
    assert rig.selected() is None


@pytest.mark.parametrize("existing", [False, True])
def test_second_archive_read_failure_is_optional_only_with_prior_caption(
    tmp_path: Path, existing: bool
) -> None:
    rig = Rig(tmp_path)
    if existing:
        BindingStore(rig.data).remember(rig.binding)
    # The first lookup established a valid caption; only the added preview read fails.
    with patch.object(DeliveryAssociations, "find", side_effect=[rig.entry, StateError("read")]):
        if existing:
            assert rig.accept() == rig.seen
        else:
            with pytest.raises(StateError):
                rig.accept()
    assert BindingStore(rig.data).resolve(rig.seen) == (rig.binding if existing else None)
    assert rig.selected() is None


def test_optional_publication_proof_read_failure_withholds_image_not_caption(
    tmp_path: Path,
) -> None:
    rig = Rig(tmp_path)
    rig.accept()
    caption = BindingStore(rig.data).resolve(rig.seen)
    assert isinstance(caption, Binding)
    with patch.object(DeliveryAssociations, "find", side_effect=StateError("read")):
        assert rig.observer.preview_association(rig.seen, caption) is None
    assert rig.observer.preview_association(rig.seen, caption) is None
    assert BindingStore(rig.data).resolve(rig.seen) == caption


def test_invalid_snapshot_and_unrelated_delivery_caption_cannot_reuse_proof(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.accept()
    with pytest.raises(ValueError, match="inconsistent observed thumbnail"):
        rig.observer.accept_snapshot(dict(rig.seen.to_json(), thumbnail="eQ=="))
    assert rig.selected() is None
    assert rig.observer.preview_association(rig.seen, rig.entry) is None


def test_changed_pinned_device_invalidates_thumbnail_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig = Rig(tmp_path)
    rig.accept()
    monkeypatch.setattr(rig.observer, "_device", "d" * 64)
    assert rig.selected() is None
