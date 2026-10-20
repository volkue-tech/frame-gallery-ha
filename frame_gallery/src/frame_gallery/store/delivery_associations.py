"""Per-device confirmed-upload metadata, independent of preview/history and mode."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

from frame_gallery.budget.deadline import Deadline
from frame_gallery.errors import StateError
from frame_gallery.imaging.reference import valid_reference
from frame_gallery.observer.model import Evidence, Observation
from frame_gallery.store.atomic import (
    Directory,
    DocumentFile,
    DocumentSpec,
    ReadFailure,
    encode_json,
    open_directory,
)
from frame_gallery.store.fields import parse_qualified_id, parse_timestamp
from frame_gallery.tv.identity import DEVICE_DIGEST
from frame_gallery.tv.port import CONTENT_ID_PATTERN

MAX_DELIVERIES: Final = 2048
MAX_BYTES: Final = 32 * 1024 * 1024
FILE: Final = "artwork-deliveries.json"
FORMAT: Final = "frame-gallery-confirmed-deliveries"


def _text(value: object, limit: int = 200) -> str:
    if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 for c in value):
        raise ValueError("invalid delivery association text")
    return value


@dataclass(frozen=True, slots=True)
class DeliveryAssociation:
    device_id: str
    content_id: str
    target_sha256: str
    jpeg_sha256: str
    work_id: str
    title: str
    artist: str
    source: str
    detail_url: str
    recorded_at: str
    reference_rgb: str | None = None
    image_rejected: bool = False

    @classmethod
    def from_json(cls, value: Mapping[str, object]) -> DeliveryAssociation:
        if set(value) != set(cls.__dataclass_fields__):
            raise ValueError("invalid delivery association fields")
        fields = {
            k: _text(value[k])
            for k in cls.__dataclass_fields__
            if k not in {"reference_rgb", "image_rejected"}
        }
        reference = value["reference_rgb"]
        if reference is not None and not valid_reference(reference):
            raise ValueError("invalid delivery image reference")
        assert reference is None or isinstance(reference, str)  # noqa: S101
        rejected = value["image_rejected"]
        if not isinstance(rejected, bool):
            raise ValueError("invalid delivery image rejection state")
        result = cls(**fields, reference_rgb=reference, image_rejected=rejected)
        if (
            any(
                DEVICE_DIGEST.fullmatch(v) is None
                for v in (result.device_id, result.target_sha256, result.jpeg_sha256)
            )
            or CONTENT_ID_PATTERN.fullmatch(result.content_id) is None
            or result.source != result.work_id.partition(":")[0]
        ):
            raise ValueError("invalid delivery association identity")
        parse_qualified_id(result.work_id)
        parse_timestamp(result.recorded_at)
        return result

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> DeliveryAssociation:
        metadata = record.get("attribution")
        if not isinstance(metadata, dict):
            raise ValueError("missing delivery metadata")
        work = parse_qualified_id(record.get("id"))
        return cls.from_json(
            {
                "device_id": record.get("tv_device_id"),
                "content_id": record.get("tv_content_id"),
                "target_sha256": record.get("tv_target_sha256"),
                "jpeg_sha256": record.get("sha256"),
                "work_id": work,
                "source": work.partition(":")[0],
                "title": metadata.get("title") or "",
                "artist": metadata.get("creator") or "",
                "detail_url": metadata.get("detail_url") or "",
                "recorded_at": record.get("delivered_at"),
                "reference_rgb": record.get("delivery_reference_rgb"),
                "image_rejected": False,
            }
        )

    def matches(self, observation: Observation) -> bool:
        # A send receipt is historical correspondence, not a fresh thumbnail.
        return (
            observation.evidence in {Evidence.SLIDESHOW, Evidence.CURRENT_STATE}
            and not self.image_rejected
            and self.device_id == observation.device_id
            and self.content_id == observation.content_id
        )


def _read(document: Mapping[str, object]) -> tuple[DeliveryAssociation, ...]:
    rows = document.get("deliveries")
    if not isinstance(rows, list) or len(rows) > MAX_DELIVERIES:
        raise ValueError("invalid delivery association count")
    result = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid delivery association")
        item = DeliveryAssociation.from_json(row)
        key = item.device_id, item.content_id
        if key in seen:
            raise ValueError("duplicate delivery association")
        seen.add(key)
        result.append(item)
    return tuple(result)


SPEC: Final = DocumentSpec(FORMAT, 1, MAX_BYTES, _read)


def _load(
    directory: Directory, document: DocumentFile[tuple[DeliveryAssociation, ...]]
) -> tuple[DeliveryAssociation, ...]:
    loaded = document.load()
    if loaded.newer_version is not None or loaded.unreadable:
        raise StateError("delivery associations cannot be read safely")
    if loaded.value is not None and not loaded.primary_valid:
        raise StateError("delivery associations need recovery; older backup is not current proof")
    if loaded.value is None and directory.read_bytes(FILE, MAX_BYTES) is not ReadFailure.MISSING:
        raise StateError("delivery associations are damaged; refusing replacement")
    return loaded.value or ()


class DeliveryAssociations:
    def __init__(self, data: Path) -> None:
        self._data = data

    def all(self) -> tuple[DeliveryAssociation, ...]:
        with open_directory(self._data, ("state",), create=True, mode=0o700) as directory:
            return _load(directory, DocumentFile(directory, FILE, SPEC, backup=True))

    def find(self, device_id: str, content_id: str) -> DeliveryAssociation | None:
        return next(
            (b for b in self.all() if (b.device_id, b.content_id) == (device_id, content_id)), None
        )

    def remember(self, item: DeliveryAssociation, deadline: Deadline) -> None:
        deadline.check()
        DeliveryAssociation.from_json(asdict(item))
        with open_directory(self._data, ("state",), create=True, mode=0o700) as directory:
            document = DocumentFile(directory, FILE, SPEC, backup=True)
            prior = [
                b
                for b in _load(directory, document)
                if (b.device_id, b.content_id) != (item.device_id, item.content_id)
            ]
            rows = [asdict(b) for b in (*prior[-(MAX_DELIVERIES - 1) :], item)]
            header = {"format": FORMAT, "version": 1, "deliveries": []}
            sizes = [len(encode_json(row, MAX_BYTES)) + 1 for row in rows]
            total = len(encode_json(header, MAX_BYTES)) + sum(sizes) - 1
            offset = 0
            while total > MAX_BYTES:
                total -= sizes[offset]
                offset += 1
            deadline.check()
            document.write({**header, "deliveries": rows[offset:]})
