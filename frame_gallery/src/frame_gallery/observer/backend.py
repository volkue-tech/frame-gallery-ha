"""Isolated TV observation and image-verified binding capture.

No credentials or high-resolution image bytes are retained. Enrollment is allowed
only following a fresh successful explicit delivery in the opted-in service.
"""

from __future__ import annotations

import base64
import hashlib
import os
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import UTC, datetime
from ipaddress import IPv4Address
from pathlib import Path
from typing import cast

from frame_gallery.budget.clock import SystemClock
from frame_gallery.budget.deadline import Deadline
from frame_gallery.errors import StateError
from frame_gallery.isolation.executor import Executor, JsonObject, WorkerError
from frame_gallery.observer.model import DEVICE_ID, READ_S, Evidence, Observation, Status
from frame_gallery.observer.stream import SLIDESHOW_POLICY, EventPolicy, reviewed_policy
from frame_gallery.store.artwork_bindings import Binding, BindingStore
from frame_gallery.store.atomic import ReadFailure, decode_json, open_directory
from frame_gallery.store.delivery_associations import DeliveryAssociation, DeliveryAssociations
from frame_gallery.store.observer_targets import MAX_TARGETS, TargetStore
from frame_gallery.tv.port import CONTENT_ID_PATTERN, target_fingerprint
from frame_gallery.tv.token_store import TokenStore


class HostObserver:
    def __init__(
        self,
        executor: Executor,
        data: Path,
        media: Path,
        host: IPv4Address,
        *,
        device_id: str | None = None,
        tokenless_grant: bool = False,
        stopped: Callable[[], bool] = lambda: False,
        current_state_refresh: bool = False,
    ) -> None:
        self._executor, self._data, self._media, self._host = executor, data, media, host
        self._device, self._stopped = device_id, stopped
        # Only a reviewed identity/channel policy can select this mode. It is
        # neither a user option nor a retry after a stored-token rejection.
        self._tokenless = tokenless_grant
        self._bindings = BindingStore(data)
        self._delivery_device: str | None = None
        self._targets = TargetStore(data)
        self._enroll = False
        self._state_refresh = current_state_refresh
        self._preview_proof: tuple[Observation, DeliveryAssociation] | None = None

    def delivery_snapshot(self) -> bytes | None:
        """A bounded before/after receipt; exit 0 alone also includes no_match.

        Distinguish a missing record from an unreadable one. If the initial
        snapshot fails, the explicit delivery still runs but cannot arm reads.
        """
        try:
            with open_directory(self._data, ("state",)) as directory:
                raw = directory.read_bytes("current.json", 16 * 1024)
            if raw is ReadFailure.MISSING:
                return b""
            return raw if isinstance(raw, bytes) else None
        except StateError:
            return None

    def after_delivery(self, before: bytes | None) -> bool:
        """Grant one service session; the caller must have observed send success.

        No network I/O here. Do not recover a damaged pin table into enrollment,
        or infer a tokenless grant during ordinary reads after token rejection.
        """
        self._device, self._enroll, self._tokenless = None, False, False
        self._delivery_device = None
        self._preview_proof = None
        try:
            after = self.delivery_snapshot()
            record = self._current(after) if after else None
            content_id = None if record is None else record.get("tv_content_id")
            if (
                before is None
                or not after
                or before == after
                or record is None
                or not isinstance(content_id, str)
                or CONTENT_ID_PATTERN.fullmatch(content_id) is None
                or record.get("tv_target_sha256") != target_fingerprint(self._host)
            ):
                return False
            targets = self._targets.targets()
            delivered_device = record.get("tv_device_id")
            if delivered_device is not None:
                if (
                    not isinstance(delivered_device, str)
                    or DEVICE_ID.fullmatch(delivered_device) is None
                ):
                    return False
                association = DeliveryAssociations(self._data).find(delivered_device, content_id)
                if (
                    association is None
                    or association.image_rejected
                    or (
                        association.target_sha256 != record["tv_target_sha256"]
                        or association.jpeg_sha256 != record.get("sha256")
                        or association.work_id != record.get("id")
                    )
                ):
                    return False
                self._targets.pin(self._host, delivered_device, confirmed_delivery=True)
                self._device = self._delivery_device = delivered_device
            else:
                self._device = targets.get(str(self._host))
            if self._device is None and len(targets) >= MAX_TARGETS:
                return False
            self._tokenless = TokenStore(self._data, self._host).load_for_observation() is None
            self._enroll = self._device is None
        except StateError:
            return False
        return True

    def event_policy(self, device_id: str | None) -> EventPolicy | None:
        """Consume one delivery or opted-in HA grant, not the saved pin alone."""
        granted, self._delivery_device = self._delivery_device, None
        if device_id is not None and device_id == granted:
            return replace(SLIDESHOW_POLICY, state_refresh=self._state_refresh)
        return reviewed_policy(device_id)

    def prepare_resume(self) -> bool:
        """Local-only validation AFTER a consumed experimental initial-on/edge grant.

        No enrollment, repinning, send or new binding. The caller, not stored
        metadata alone, must supply the separately accepted initial-on/edge gate.
        """
        self._device, self._delivery_device = None, None
        self._enroll, self._tokenless = False, False
        self._preview_proof = None
        try:
            device = self._targets.targets().get(str(self._host))
            if device is None:
                return False
            target = target_fingerprint(self._host)
            archived = DeliveryAssociations(self._data).all()
            if not any(a.device_id == device and a.target_sha256 == target for a in archived):
                return False
            self._tokenless = TokenStore(self._data, self._host).load_for_observation() is None
        except StateError:
            return False
        self._device = self._delivery_device = device
        return True

    def read(self) -> Observation:
        payload = self.session_request()
        if isinstance(payload, Observation):
            return payload
        try:
            result = self._executor.run(
                "observe", payload, timeout=READ_S, should_stop=self._stopped
            )
            return self.accept_snapshot(result)
        except (WorkerError, ValueError, StateError, OSError):
            return Observation(Status.UNAVAILABLE)

    @property
    def device_id(self) -> str | None:
        return self._device

    def session_request(self) -> JsonObject | Observation:
        """Local validation only; never starts a worker or contacts a TV."""
        self._preview_proof = None
        if self._device is None and not self._enroll:
            return Observation(Status.VALIDATION_REQUIRED)
        try:
            token = (
                None
                if self._tokenless
                else TokenStore(self._data, self._host).load_for_observation()
            )
        except StateError:
            return Observation(Status.NOT_AUTHORIZED)
        if token is None and not self._tokenless:
            return Observation(Status.NOT_AUTHORIZED)
        return {
            "host": str(self._host),
            "token": token,
            "device_id": self._device,
            "tokenless_grant": self._tokenless,
            "enroll_device": self._enroll,
        }

    def accept_snapshot(self, result: JsonObject) -> Observation:
        """Accept initial byte proof once; events cannot manufacture a digest."""
        self._preview_proof = None
        result = dict(result)
        thumbnail = result.pop("thumbnail", None)
        observation = Observation.from_json(result)
        if observation.evidence is not Evidence.THUMBNAIL:
            raise ValueError("snapshot cannot supply slideshow evidence")
        if self._device is not None and observation.device_id not in (None, self._device):
            raise ValueError("observation belongs to another TV")
        if observation.content_id is not None and not _thumbnail_matches(observation, thumbnail):
            raise ValueError("inconsistent observed thumbnail")
        if self._enroll and observation.device_id is not None:
            self._targets.pin(self._host, observation.device_id)
            self._device, self._enroll = observation.device_id, False
        if observation.content_id is not None:
            self._capture(observation, cast(str, thumbnail), self._bindings.resolve(observation))
        return observation

    def preview_association(
        self, observation: Observation, caption: Binding | DeliveryAssociation | None
    ) -> DeliveryAssociation | None:
        """Select cached upload bytes only with this session's exact image proof.

        A thumbnail caption remains a Binding: this does not turn an upload
        receipt into thumbnail evidence or infer image identity from metadata.
        The already received thumbnail must have matched this exact receipt's
        reference, and replacing that receipt invalidates the in-memory grant.
        """
        proof = self._preview_proof
        if proof is None or proof[0] != observation:
            self._preview_proof = None
            return (
                caption
                if isinstance(caption, DeliveryAssociation) and caption.matches(observation)
                else None
            )
        seen, delivered = proof
        if (
            not isinstance(caption, Binding)
            or not caption.matches(seen)
            or seen.device_id != self._device
            or any(
                getattr(caption, name) != getattr(delivered, name)
                for name in ("work_id", "title", "artist", "source", "detail_url")
            )
        ):
            self._preview_proof = None
            return None
        try:
            current = DeliveryAssociations(self._data).find(
                delivered.device_id, delivered.content_id
            )
        except (StateError, OSError):
            current = None
        if current != delivered:
            self._preview_proof = None
            return None
        return delivered

    def accept_slideshow(self, content_id: str) -> Observation:
        """Local lookup ONLY after a corroborated triple on the pinned session.

        The saved digest identifies the previously verified association; it is
        not a claim of a newly downloaded thumbnail. Never create a binding.
        """
        if self._device is None or CONTENT_ID_PATTERN.fullmatch(content_id) is None:
            raise ValueError("missing slideshow identity")
        if DeliveryAssociations(self._data).find(self._device, content_id) is not None:
            return Observation(
                Status.UNIDENTIFIED, self._device, content_id, None, Evidence.SLIDESHOW
            )
        binding = next(
            (
                b
                for b in self._bindings.all()
                if b.device_id == self._device and b.content_id == content_id
            ),
            None,
        )
        return Observation(
            Status.UNIDENTIFIED,
            self._device,
            content_id,
            None if binding is None else binding.thumbnail_sha256,
            Evidence.SLIDESHOW,
        )

    def accept_current_state(self, content_id: str) -> Observation:
        """Pinned-device lookup after a coherent fresh same-socket state read."""
        return replace(self.accept_slideshow(content_id), evidence=Evidence.CURRENT_STATE)

    def _capture(
        self,
        observation: Observation,
        thumbnail: str,
        existing: Binding | DeliveryAssociation | None,
    ) -> None:
        archived = DeliveryAssociations(self._data)
        try:
            delivered = archived.find(observation.device_id or "", observation.content_id or "")
        except (StateError, OSError):
            if existing is None:
                raise
            return  # The optional preview read cannot invalidate an already verified caption.
        if delivered is not None and delivered.reference_rgb is not None:
            try:
                verified = self._executor.run(
                    "verify_thumbnail",
                    {"reference_rgb": delivered.reference_rgb, "thumbnail": thumbnail},
                    timeout=5.0,
                    should_stop=self._stopped,
                )
            except (WorkerError, ValueError, StateError, OSError):
                if existing is None:
                    raise
                return  # No new image proof; keep the prior exact-thumbnail caption only.
            matched = verified == {"matched": True}
            if delivered.image_rejected == matched:
                archived.remember(
                    replace(delivered, image_rejected=not matched),
                    Deadline.after(SystemClock(), 2.0, "association verification"),
                )
            if matched and existing is None:
                self._bindings.remember(
                    Binding.from_json(
                        {
                            "device_id": observation.device_id,
                            "content_id": observation.content_id,
                            "thumbnail_sha256": observation.thumbnail_sha256,
                            "work_id": delivered.work_id,
                            "title": delivered.title,
                            "artist": delivered.artist,
                            "source": delivered.source,
                            "detail_url": delivered.detail_url,
                            "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
                        }
                    )
                )
            if matched:
                self._preview_proof = (observation, replace(delivered, image_rejected=False))
            return
        if existing is None:
            self._capture_legacy(observation, thumbnail)

    def _capture_legacy(self, observation: Observation, thumbnail: str) -> None:
        record = self._current()
        if (
            record is None
            or record.get("tv_content_id") != observation.content_id
            or record.get("tv_target_sha256") != target_fingerprint(self._host)
        ):
            return
        metadata = record.get("attribution")
        sha256 = record.get("sha256")
        if not isinstance(metadata, dict) or not isinstance(sha256, str):
            return
        with open_directory(self._media, ("frame_gallery", "preview")) as directory:
            fd = os.open(
                "latest.jpg",
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                dir_fd=directory.fd,
            )
        try:
            verified = self._executor.run(
                "verify_thumbnail",
                {"fd": fd, "sha256": sha256, "thumbnail": thumbnail},
                timeout=5.0,
                files=(fd,),
                should_stop=self._stopped,
            )
        finally:
            os.close(fd)
        if verified != {"matched": True}:
            return
        fields: dict[str, object] = {
            "device_id": observation.device_id,
            "content_id": observation.content_id,
            "thumbnail_sha256": observation.thumbnail_sha256,
            "work_id": record.get("id"),
            "title": metadata.get("title") or "",
            "artist": metadata.get("creator") or "",
            "source": str(record.get("id", "")).partition(":")[0],
            "detail_url": metadata.get("detail_url") or "",
            "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        self._bindings.remember(Binding.from_json(fields))

    def _current(self, raw: bytes | None = None) -> Mapping[str, object] | None:
        try:
            if raw is None:
                with open_directory(self._data, ("state",)) as directory:
                    value = directory.read_bytes("current.json", 16 * 1024)
                if isinstance(value, ReadFailure):
                    return None
                raw = value
            record = decode_json(raw)
            if (
                not isinstance(record, dict)
                or record.get("format") != "frame-gallery-current"
                or record.get("version") != 1
            ):
                return None
            return record
        except (StateError, ValueError):
            return None


def _thumbnail_matches(observation: Observation, thumbnail: object) -> bool:
    if not isinstance(thumbnail, str) or len(thumbnail) > 56 * 1024:
        return False
    raw = base64.b64decode(thumbnail, validate=True)
    return (
        0 < len(raw) <= 40 * 1024
        and hashlib.sha256(raw).hexdigest() == observation.thumbnail_sha256
    )
