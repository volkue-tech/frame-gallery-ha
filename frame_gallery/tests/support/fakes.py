"""Fakes of the runner's ports (§20.2).

Every fake appends to one shared :class:`Events` log, so tests can assert the
order of operations across ports. Fakes advance the :class:`FakeClock` to
simulate slow operations; nothing waits in real time.
"""

from __future__ import annotations

import io
import shutil
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from functools import cache
from ipaddress import IPv4Network
from pathlib import Path

from PIL import Image

from frame_gallery.app.ports import FetchedImage, ProviderBinding
from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.filters import EffectiveFilters, FilterField
from frame_gallery.domain import CANVAS, Size, SourceKey, WorkspacePaths
from frame_gallery.errors import PublishError, StateError
from frame_gallery.imaging.contract import (
    ColourHandling,
    DeliveryArtifact,
    ImageFormat,
    PrepareRequest,
    PrepareResult,
    PrepareStatus,
)
from frame_gallery.isolation.executor import JsonObject, WorkerError
from frame_gallery.providers.contract import (
    Attribution,
    Candidate,
    Capabilities,
    DiscoveryContext,
    ImageRef,
    ImageRefKind,
)
from frame_gallery.providers.rights import RightsBasis
from frame_gallery.selection.exclusion import ExclusionSet
from frame_gallery.tv.port import (
    DeliveryRequest,
    DeliveryResult,
    DeliveryStatus,
    Marker,
    MarkerEvent,
    MarkerSink,
)
from tests.support.clock import FakeClock

TEST_TV_HOST = "192.168.1.20"


def observe(
    deadlines: dict[str, Deadline], remaining: dict[str, float], key: str, deadline: Deadline
) -> None:
    """Record a deadline and the time it had left when a port received it."""
    deadlines[key] = deadline
    remaining[key] = deadline.remaining()


DEFAULT_SIZE = Size(1920, 1080)


class Events(list[str]):
    """The ordered log of port calls."""

    def index_of(self, event: str) -> int:
        return self.index(event)

    def before(self, first: str, second: str) -> bool:
        return self.index(first) < self.index(second)


@cache
def canvas_jpeg_bytes() -> bytes:
    """A real 3840x2160 baseline JPEG, as the prepare task would write it."""
    buffer = io.BytesIO()
    Image.new("RGB", (CANVAS.width, CANVAS.height), (40, 90, 160)).save(buffer, "JPEG", quality=90)
    return buffer.getvalue()


@cache
def source_jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 36), (200, 120, 40)).save(buffer, "JPEG", quality=90)
    return buffer.getvalue()


def make_candidate(
    native_id: str,
    *,
    size: Size | None = DEFAULT_SIZE,
    provider_key: str = "aic",
    rights: RightsBasis = RightsBasis.CC0,
    title: str | None = "Synthetic Study",
) -> Candidate:
    return Candidate(
        provider_key=provider_key,
        native_id=native_id,
        rights_basis=rights,
        rights_field="is_public_domain",
        attribution=Attribution(title=title, creator="Test Painter", date_text="1901"),
        dims=size,
    )


class FakeOptionsSource:
    def __init__(
        self,
        raw: Mapping[str, object],
        events: Events,
        clock: FakeClock,
        *,
        delay_s: float = 0.0,
        error: BaseException | None = None,
    ) -> None:
        self.raw = dict(raw)
        self.events = events
        self.clock = clock
        self.delay_s = delay_s
        self.error = error
        self.deadline: Deadline | None = None

    def load(self, deadline: Deadline) -> Mapping[str, object]:
        self.events.append("options.load")
        self.deadline = deadline
        self.clock.advance(self.delay_s)
        if self.error is not None:
            raise self.error
        return self.raw


class FakeNetworkInfo:
    def __init__(self, networks: Sequence[IPv4Network] = (IPv4Network("172.30.32.0/23"),)) -> None:
        self.networks = tuple(networks)

    def container_networks(self) -> Sequence[IPv4Network]:
        return self.networks


@dataclass
class FakeStateStore:
    """History and ledger held in memory, with injectable failures."""

    events: Events
    clock: FakeClock
    exclusions: ExclusionSet = field(default_factory=ExclusionSet)
    fail: dict[str, BaseException] = field(default_factory=dict)
    """Method name -> exception to raise instead of acting."""

    delays: dict[str, float] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    ledger: dict[str, str] = field(default_factory=dict)
    prestaged: str | None = None
    opened: bool = False
    closed: bool = False
    deadlines: dict[str, Deadline] = field(default_factory=dict)

    def _call(self, name: str, detail: str = "") -> None:
        self.events.append(f"state.{name}" + (f":{detail}" if detail else ""))
        self.clock.advance(self.delays.get(name, 0.0))
        error = self.fail.get(name)
        if error is not None:
            raise error

    def open(self, deadline: Deadline) -> None:
        self.deadlines["open"] = deadline
        self._call("open")
        self.opened = True

    def load_exclusions(self, now: datetime) -> ExclusionSet:
        """The configured exclusions plus this fake's own history and ledger."""
        self._call("load_exclusions")
        uploaded = {qid for qid, state in self.ledger.items() if state == "uploaded"}
        uncertain = {qid for qid, state in self.ledger.items() if state == "uncertain"}
        return ExclusionSet(
            history=self.exclusions.history | frozenset(self.history),
            uploaded=self.exclusions.uploaded | frozenset(uploaded),
            uncertain=self.exclusions.uncertain | frozenset(uncertain),
        )

    def prestage_history(self, qualified_id: str, now: datetime) -> None:
        self._call("prestage", qualified_id)
        self.prestaged = qualified_id

    def discard_prestaged_history(self) -> None:
        self.events.append("state.discard_prestaged")
        self.prestaged = None

    def commit_upload_intent(self, qualified_id: str, now: datetime) -> None:
        self._call("commit_intent", qualified_id)
        self.ledger[qualified_id] = "uncertain"

    def promote_upload(self, qualified_id: str, now: datetime) -> None:
        self._call("promote", qualified_id)
        self.ledger[qualified_id] = "uploaded"

    def remove_upload_intent(self, qualified_id: str) -> None:
        self._call("remove_intent", qualified_id)
        self.ledger.pop(qualified_id, None)

    def record_history(self) -> None:
        self._call("record_history")
        if self.prestaged is None:
            raise StateError("nothing pre-staged")
        self.history.append(self.prestaged)
        self.prestaged = None

    def close(self) -> None:
        self.events.append("state.close")
        self.closed = True


class FakeHelperReader:
    def __init__(
        self,
        events: Events,
        values: Mapping[FilterField, str | None] | None = None,
        error: BaseException | None = None,
    ) -> None:
        self.events = events
        self.values = dict(values or {})
        self.error = error
        self.requested: dict[FilterField, str] = {}
        self.deadline: Deadline | None = None

    def read(
        self, helpers: Mapping[FilterField, str], deadline: Deadline
    ) -> Mapping[FilterField, str | None]:
        self.events.append("helpers.read")
        self.deadline = deadline
        self.requested = dict(helpers)
        if self.error is not None:
            raise self.error
        return {field_: self.values.get(field_) for field_ in helpers}


class FakeProvider:
    """Yields the given candidates lazily; can advance time or raise mid-stream."""

    def __init__(
        self,
        events: Events,
        clock: FakeClock,
        candidates: Sequence[Candidate] = (),
        *,
        key: str = "aic",
        source: SourceKey = SourceKey.ART_INSTITUTE_CHICAGO,
        per_candidate_s: float = 0.0,
        raise_at: int | None = None,
        error: BaseException | None = None,
        call_error: BaseException | None = None,
    ) -> None:
        self.events = events
        self.clock = clock
        self.candidates = list(candidates)
        self._key = key
        self.source = source
        self.per_candidate_s = per_candidate_s
        self.raise_at = raise_at
        self.error = error
        self.call_error = call_error
        self.pulled = 0
        self.contexts: list[DiscoveryContext] = []
        self.filters: list[EffectiveFilters] = []
        self.on_context: Callable[[DiscoveryContext], None] | None = None
        """Called with each discovery context, for example to add notes."""

    @property
    def key(self) -> str:
        return self._key

    def capabilities(self) -> Capabilities:
        return Capabilities(source=self.source, provider_key=self._key, dims_in_metadata=True)

    def iter_candidates(
        self, filters: EffectiveFilters, ctx: DiscoveryContext
    ) -> Iterator[Candidate]:
        self.events.append("provider.iter")
        self.contexts.append(ctx)
        self.filters.append(filters)
        if self.on_context is not None:
            self.on_context(ctx)
        if self.call_error is not None:
            raise self.call_error
        return self._generate()

    def _generate(self) -> Iterator[Candidate]:
        for index, candidate in enumerate(self.candidates):
            if self.raise_at is not None and index == self.raise_at and self.error is not None:
                raise self.error
            self.clock.advance(self.per_candidate_s)
            self.pulled += 1
            yield candidate
        if (
            self.raise_at is not None
            and self.raise_at >= len(self.candidates)
            and self.error is not None
        ):
            raise self.error

    def full_ref(self, candidate: Candidate) -> ImageRef:
        return ImageRef(
            kind=ImageRefKind.REMOTE,
            location=f"https://images.example.invalid/{candidate.native_id}.jpg",
        )


@dataclass
class FakeFetcher:
    """Writes a small JPEG, or fails, per candidate native id (from the URL)."""

    events: Events
    clock: FakeClock
    failures: dict[str, BaseException] = field(default_factory=dict)
    payloads: dict[str, bytes] = field(default_factory=dict)
    declared: dict[str, ImageFormat] = field(default_factory=dict)
    delay_s: float = 0.0
    consume_deadline: bool = False
    deadlines: list[Deadline] = field(default_factory=list)

    def fetch(self, ref: ImageRef, destination: Path, deadline: Deadline) -> FetchedImage:
        native_id = ref.location.rsplit("/", 1)[-1].removesuffix(".jpg")
        self.events.append(f"fetch:{native_id}")
        self.deadlines.append(deadline)
        if self.consume_deadline:
            self.clock.advance_to(deadline.expires_at)
        else:
            self.clock.advance(self.delay_s)
        error = self.failures.get(native_id)
        if error is not None:
            raise error
        data = self.payloads.get(native_id, source_jpeg_bytes())
        destination.write_bytes(data)
        return FetchedImage(
            path=destination,
            size_bytes=len(data),
            declared_format=self.declared.get(native_id, ImageFormat.JPEG),
        )


PrepareBehaviour = Callable[[PrepareRequest], JsonObject]


@dataclass
class FakeExecutor:
    """Pretends to run ``prepare``: writes a real canvas JPEG and reports OK.

    ``behaviours`` (consumed in call order) can replace a call's result or raise.
    """

    events: Events
    clock: FakeClock
    behaviours: list[PrepareBehaviour | BaseException | None] = field(default_factory=list)
    oriented_size: Size = DEFAULT_SIZE
    delay_s: float = 0.0
    consume_timeout: bool = False
    timeouts: list[float] = field(default_factory=list)
    terminated: int = 0

    def run(self, task: str, payload: JsonObject, *, timeout: float) -> JsonObject:
        self.events.append(f"executor.run:{task}")
        self.timeouts.append(timeout)
        request = PrepareRequest.from_json(payload)
        if self.consume_timeout:
            self.clock.advance(timeout)
        else:
            self.clock.advance(self.delay_s)
        behaviour = self.behaviours.pop(0) if self.behaviours else None
        if isinstance(behaviour, BaseException):
            raise behaviour
        if behaviour is not None:
            return behaviour(request)
        Path(request.output_path).write_bytes(canvas_jpeg_bytes())
        return self.ok_result().to_json()

    def ok_result(self) -> PrepareResult:
        return PrepareResult(
            status=PrepareStatus.OK,
            source_size=self.oriented_size,
            oriented_size=self.oriented_size,
            orientation=1,
            output_bytes=len(canvas_jpeg_bytes()),
            jpeg_quality=90,
            colour=ColourHandling.ASSUMED_SRGB,
        )

    def terminate_all(self) -> None:
        self.events.append("executor.terminate_all")
        self.terminated += 1


class FakeTelevision:
    """Emits scripted markers, then returns a status or raises.

    ``during`` is called after each marker with the marker, so a test can
    request a stop or raise at an exact point.
    """

    def __init__(
        self,
        events: Events,
        clock: FakeClock,
        *,
        markers: Sequence[Marker] = (
            Marker.CONNECTED,
            Marker.UPLOAD_STARTED,
            Marker.UPLOADED,
            Marker.SELECTED,
        ),
        status: DeliveryStatus = DeliveryStatus.OK,
        error: BaseException | None = None,
        during: Callable[[Marker], None] | None = None,
        report_markers: bool = True,
        delay_s: float = 0.0,
        detail: str = "",
    ) -> None:
        self.events = events
        self.clock = clock
        self.markers = list(markers)
        self.status = status
        self.error = error
        self.during = during
        self.report_markers = report_markers
        self.delay_s = delay_s
        self.detail = detail
        self.requests: list[DeliveryRequest] = []
        self.payloads: list[bytes] = []

    def deliver(self, request: DeliveryRequest, on_marker: MarkerSink) -> DeliveryResult:
        self.events.append("tv.deliver")
        self.requests.append(request)
        self.payloads.append(request.jpeg_path.read_bytes())
        self.clock.advance(self.delay_s)
        seen: list[Marker] = []
        for marker in self.markers:
            content_id = "MY_F0001" if marker is Marker.UPLOADED else None
            self.events.append(f"tv.marker:{marker.value}")
            on_marker(MarkerEvent(marker, content_id))
            seen.append(marker)
            if self.during is not None:
                self.during(marker)
            if request.stop_requested():
                # As the port requires: kill the worker, return the markers seen.
                self.events.append("tv.stopped")
                return DeliveryResult(
                    status=DeliveryStatus.UNREACHABLE,
                    markers_seen=tuple(seen) if self.report_markers else (),
                    detail="stopped",
                )
        if self.error is not None:
            raise self.error
        return DeliveryResult(
            status=self.status,
            markers_seen=tuple(self.markers) if self.report_markers else (),
            detail=self.detail,
        )


class FakeWorkspace:
    def __init__(self, root: Path, events: Events, *, error: BaseException | None = None) -> None:
        self.root = root / "run"
        self.events = events
        self.error = error
        self.created = 0
        self.removed = 0
        self.remove_error: BaseException | None = None

    def create(self) -> WorkspacePaths:
        self.events.append("workspace.create")
        if self.error is not None:
            raise self.error
        self.created += 1
        inbox, outbox = self.root / "in", self.root / "out"
        inbox.mkdir(parents=True)
        outbox.mkdir()
        return WorkspacePaths(root=self.root, inbox=inbox, outbox=outbox)

    def remove(self) -> None:
        self.events.append("workspace.remove")
        self.removed += 1
        if self.remove_error is not None:
            raise self.remove_error
        shutil.rmtree(self.root, ignore_errors=True)


class FakePreview:
    def __init__(self, events: Events, *, error: BaseException | None = None) -> None:
        self.events = events
        self.error = error
        self.published: list[bytes] = []
        self.artifacts: list[DeliveryArtifact] = []
        self.deadline: Deadline | None = None

    def publish(self, artifact: DeliveryArtifact, deadline: Deadline) -> None:
        self.events.append("preview.publish")
        self.deadline = deadline
        deadline.check()  # a store honours its deadline
        if self.error is not None:
            raise self.error
        self.artifacts.append(artifact)
        self.published.append(artifact.path.read_bytes())


class FakeRecords:
    def __init__(
        self,
        events: Events,
        clock: FakeClock,
        *,
        current_error: BaseException | None = None,
        last_run_error: BaseException | None = None,
        consume_deadline: bool = False,
    ) -> None:
        self.events = events
        self.clock = clock
        self.current_error = current_error
        self.last_run_error = last_run_error
        self.consume_deadline = consume_deadline
        self.current: list[Mapping[str, object]] = []
        self.last_run: list[Mapping[str, object]] = []
        self.deadlines: dict[str, Deadline] = {}
        self.remaining: dict[str, float] = {}

    def write_current(self, record: Mapping[str, object], deadline: Deadline) -> None:
        self.events.append("records.current")
        observe(self.deadlines, self.remaining, "current", deadline)
        deadline.check()  # a store honours its deadline
        if self.current_error is not None:
            raise self.current_error
        self.current.append(dict(record))

    def write_last_run(self, record: Mapping[str, object], deadline: Deadline) -> None:
        self.events.append("records.last_run")
        observe(self.deadlines, self.remaining, "last_run", deadline)
        deadline.check()  # a store honours its deadline
        if self.consume_deadline:
            self.clock.advance_to(deadline.expires_at)
        if self.last_run_error is not None:
            raise self.last_run_error
        self.last_run.append(dict(record))


class FakeCacheWriter:
    """A provider's metadata cache as the runner sees it."""

    def __init__(self, events: Events, *, error: BaseException | None = None) -> None:
        self.events = events
        self.error = error
        self.deadlines: list[Deadline] = []

    def flush(self, deadline: Deadline) -> None:
        self.events.append("cache.flush")
        self.deadlines.append(deadline)
        if self.error is not None:
            raise self.error


class FakeWatchdog:
    def __init__(self, events: Events) -> None:
        self.events = events
        self.armed = False
        self.disarmed = False
        self.fired = False
        """Set by a test to simulate a watchdog that claimed the run first."""

    def arm(self) -> None:
        self.events.append("watchdog.arm")
        self.armed = True

    def disarm(self) -> bool:
        self.events.append("watchdog.disarm")
        self.disarmed = True
        return not self.fired


def binding(provider: FakeProvider) -> ProviderBinding:
    return ProviderBinding(provider=provider)


__all__ = [
    "TEST_TV_HOST",
    "Events",
    "FakeCacheWriter",
    "FakeExecutor",
    "FakeFetcher",
    "FakeHelperReader",
    "FakeNetworkInfo",
    "FakeOptionsSource",
    "FakePreview",
    "FakeProvider",
    "FakeRecords",
    "FakeStateStore",
    "FakeTelevision",
    "FakeWatchdog",
    "FakeWorkspace",
    "PublishError",
    "WorkerError",
    "binding",
    "canvas_jpeg_bytes",
    "make_candidate",
    "source_jpeg_bytes",
]
