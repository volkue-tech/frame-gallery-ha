"""Session-local image proof, conservative freshness and no ID-only attribution."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol

from frame_gallery.errors import StateError
from frame_gallery.isolation.executor import JsonObject
from frame_gallery.observer.model import (
    FRESH_S,
    SLIDESHOW_FRESH_S,
    Evidence,
    Observation,
    SessionFailure,
    Status,
)
from frame_gallery.observer.slideshow import IncompleteSequence, SlideshowSequence
from frame_gallery.observer.stream import QUERY_S, Change, EventPolicy, reviewed_policy
from frame_gallery.tv.port import CONTENT_ID_PATTERN

_log = logging.getLogger(__name__)


class SessionPort(Protocol):
    def start(self, payload: JsonObject) -> None: ...
    def poll(self) -> tuple[JsonObject, float] | None: ...
    def stop(self) -> None: ...


class SnapshotSource(Protocol):
    @property
    def device_id(self) -> str | None: ...
    def session_request(self) -> JsonObject | Observation: ...
    def accept_snapshot(self, result: JsonObject) -> Observation: ...
    def accept_slideshow(self, content_id: str) -> Observation: ...
    def accept_current_state(self, content_id: str) -> Observation: ...


class EventBackend:
    def __init__(
        self,
        observer: SnapshotSource,
        session: SessionPort,
        now: Callable[[], float],
        policy: Callable[[str | None], EventPolicy | None] = reviewed_policy,
    ) -> None:
        self._observer, self._session, self._now, self._policy = observer, session, now, policy
        self._baseline: Observation | None = None
        self._confirmed_at: float | None = None
        self._allow_query = False
        self._pending_at: float | None = None
        self._slideshow: SlideshowSequence | None = None
        self._slideshow_enabled = False
        self._fresh_s = FRESH_S
        self._resync_reported = False
        self._state_refresh = False

    def start(self) -> Observation:
        self.stop()
        policy = self._policy(self._observer.device_id)
        if policy is None:
            return Observation(Status.VALIDATION_REQUIRED)
        try:
            request = self._observer.session_request()
        except (StateError, OSError, ValueError):
            return self._unavailable(SessionFailure.CONTRACT)
        if isinstance(request, Observation):
            return request
        self._allow_query = policy.current_id_once
        self._slideshow_enabled = policy.slideshow
        self._state_refresh = policy.state_refresh
        self._session.start({**request, "policy": policy.to_json()})
        return Observation(Status.CHECKING)

    def stop(self) -> None:
        self._session.stop()
        self._baseline, self._confirmed_at = None, None
        self._allow_query, self._pending_at = False, None
        self._slideshow, self._slideshow_enabled, self._fresh_s = None, False, FRESH_S
        self._resync_reported = False
        self._state_refresh = False

    def _unavailable(self, reason: SessionFailure) -> Observation:
        _log.warning("event session stopped: reason=%s; no reconnect", reason.value)
        return Observation(Status.UNAVAILABLE)

    def _unconfirmed(self) -> Observation:
        self._confirmed_at = None
        if not self._resync_reported:
            _log.warning(
                "event sequence incomplete; caption cleared; awaiting a full sequence "
                "on the same connection (no query or reconnect)"
            )
            self._resync_reported = True
        return Observation(Status.CHECKING)

    def update(self) -> Observation | None:
        """Drain bounded events; receipt time, never a publication heartbeat, ages proof."""
        expired = self._expired()
        if expired is not None:
            return expired
        seen: Observation | None = None
        for _ in range(64):
            item = self._session.poll()
            if item is None:
                return seen
            value, received_at = item
            try:
                result = self._consume(value, received_at)
            except (ValueError, StateError, OSError):
                return self._unavailable(SessionFailure.CONTRACT)
            if result is not None:
                seen = result
                if result.status not in {Status.ARTWORK, Status.UNIDENTIFIED}:
                    return seen
        return self._unavailable(SessionFailure.QUEUE)  # flood/coalescing bound

    def _expired(self) -> Observation | None:
        if self._confirmed_at is not None and self._now() - self._confirmed_at >= self._fresh_s:
            if not self._slideshow_enabled:
                return Observation(Status.PAUSED)
            self._confirmed_at = None
            return Observation(Status.CHECKING)  # clear metadata, keep receive-only session
        if self._slideshow is not None and self._slideshow.expire(self._now()):
            return self._unconfirmed()
        if self._pending_at is not None and self._now() - self._pending_at >= QUERY_S:
            return Observation(Status.PAUSED)
        return None

    def _consume(self, value: JsonObject, received_at: float) -> Observation | None:
        kind = value.get("kind")
        if kind in ("waiting_art", "state_checking", "current_state"):
            return self._consume_current_state(value, received_at)
        if kind in ("querying", "current_id"):
            return self._consume_query(value, received_at)
        if kind == "baseline" and set(value) == {"kind", "observation"}:
            raw = value["observation"]
            if (
                self._baseline is not None
                or self._pending_at is not None
                or not isinstance(raw, dict)
            ):
                raise ValueError("unexpected baseline")
            return self._accept(raw, received_at)
        if kind == "change" and set(value) == {"kind", "change"}:
            raw = value["change"]
            if (self._baseline is None and not self._state_refresh) or not isinstance(raw, dict):
                raise ValueError("event before baseline")
            return self._consume_change(Change.from_json(raw), received_at)
        if kind == "end" and set(value) in ({"kind", "status"}, {"kind", "status", "reason"}):
            if not isinstance(value["status"], str) or value["status"] not in {
                "paused",
                "unavailable",
                "not_authorized",
            }:
                raise ValueError("unexpected session end")
            reason = SessionFailure.END
            if "reason" in value:
                if value["status"] != "unavailable" or not isinstance(value["reason"], str):
                    raise ValueError("invalid session reason")
                reason = SessionFailure(value["reason"])
            if value["status"] == "unavailable":
                return self._unavailable(reason)
            return Observation(Status(str(value["status"])))
        raise ValueError("unexpected session event")

    def _consume_current_state(self, value: JsonObject, at: float) -> Observation | None:
        if not self._state_refresh or not 0 <= self._now() - at < FRESH_S:
            raise ValueError("unapproved or stale state read")
        if value == {"kind": "waiting_art"} and self._baseline is None:
            return Observation(Status.TV_IN_USE)
        if value == {"kind": "state_checking"}:
            if self._confirmed_at is None or self._baseline is None:
                return None
            self._confirmed_at = None
            self._slideshow = SlideshowSequence(str(self._baseline.content_id), at)
            return Observation(Status.CHECKING)
        content_id = value.get("content_id")
        if (
            self._baseline is None
            or set(value) != {"kind", "content_id"}
            or value["kind"] != "current_state"
            or not isinstance(content_id, str)
            or CONTENT_ID_PATTERN.fullmatch(content_id) is None
        ):
            raise ValueError("invalid current state record")
        seen = self._observer.accept_current_state(content_id)
        if (
            seen.device_id != self._baseline.device_id
            or seen.content_id != content_id
            or seen.evidence is not Evidence.CURRENT_STATE
        ):
            raise ValueError("state read lookup changed identity")
        self._confirmed_at, self._fresh_s = at, FRESH_S
        self._slideshow = SlideshowSequence(content_id, at)
        self._resync_reported = False
        return seen

    def _consume_change(self, change: Change, received_at: float) -> Observation | None:
        if change.kind == "standby":
            return Observation(Status.PAUSED)
        if change == Change("mode", "off"):
            self._confirmed_at = None
            return Observation(Status.TV_IN_USE)
        if self._state_refresh:
            # Mode on is a read hint to the worker, never a new image proof.
            return None if change == Change("mode", "on") else self._unconfirmed()
        assert self._baseline is not None  # noqa: S101
        if self._slideshow is not None:
            return self._consume_slideshow(change, received_at)
        if change.kind in {"selected", "rotation"}:
            raise ValueError("unexpected slideshow change without policy")
        if change.kind == "invalidate" or (
            change.kind == "content" and change.value != self._baseline.content_id
        ):
            return Observation(Status.PAUSED)
        return None  # duplicates never re-publish/freshen old artwork

    def _consume_slideshow(self, change: Change, received_at: float) -> Observation | None:
        assert self._slideshow is not None  # noqa: S101
        try:
            content_id = self._slideshow.consume(change, received_at, self._now())
        except IncompleteSequence:
            return self._unconfirmed()
        if change.kind in {"selected", "invalidate"}:
            self._confirmed_at = None
            return Observation(Status.CHECKING)
        if content_id is None:
            return None
        seen = self._observer.accept_slideshow(content_id)
        if (
            self._baseline is None
            or seen.device_id != self._baseline.device_id
            or seen.content_id != content_id
            or seen.evidence is not Evidence.SLIDESHOW
        ):
            raise ValueError("slideshow lookup changed identity")
        self._confirmed_at, self._fresh_s = received_at, SLIDESHOW_FRESH_S
        return seen

    def _consume_query(self, value: JsonObject, received_at: float) -> Observation:
        kind = value.get("kind")
        if kind == "querying" and set(value) == {"kind"}:
            if not self._allow_query or self._baseline is None or self._pending_at is not None:
                raise ValueError("unexpected event query")
            self._baseline, self._confirmed_at = None, None
            if not 0 <= self._now() - received_at < QUERY_S:
                return Observation(Status.PAUSED)
            self._pending_at = received_at
            return Observation(Status.CHECKING)
        if kind == "current_id" and set(value) == {"kind", "content_id"}:
            content_id = value["content_id"]
            if (
                self._pending_at is None
                or not isinstance(content_id, str)
                or CONTENT_ID_PATTERN.fullmatch(content_id) is None
                or not self._pending_at <= received_at <= self._now()
            ):
                raise ValueError("unexpected event query ID")
            return Observation(Status.PAUSED)  # ID alone is not artist/image proof
        raise ValueError("unexpected event query record")

    def _accept(self, raw: JsonObject, received_at: float) -> Observation:
        seen = self._observer.accept_snapshot(raw)
        if seen.status not in {Status.ARTWORK, Status.UNIDENTIFIED}:
            return seen
        if not 0 <= self._now() - received_at < FRESH_S:
            return Observation(Status.PAUSED)
        self._baseline, self._confirmed_at = seen, received_at
        if self._slideshow_enabled:
            self._slideshow = SlideshowSequence(str(seen.content_id), received_at)
        return seen
