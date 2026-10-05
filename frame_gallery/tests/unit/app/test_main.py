"""The entry point's production wiring (``frame_gallery.__main__``; §4, §17.5).

``run_app`` runs with temporary ``/data``, ``/media``, and ``/tmp`` anchors.
The parts that would start worker processes or reach a network are replaced
through :class:`Wiring`: the in-process executor runs the real image tasks,
a fake transport answers the synthesized museum API, and a fake television
emits its markers. Nothing here touches the network (H2).
"""

from __future__ import annotations

import fcntl
import io
import json
import logging
import os
import signal
import sys
import threading
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import replace
from ipaddress import IPv4Network, ip_address
from pathlib import Path

import pytest
from PIL import Image

from frame_gallery import __main__ as entry
from frame_gallery.app.networks import ContainerNetworks
from frame_gallery.app.signals import CancellationController
from frame_gallery.budget.clock import Clock
from frame_gallery.isolation.apparmor import ProfileError
from frame_gallery.isolation.executor import EventSink, JsonObject, StopCheck
from frame_gallery.isolation.in_process import (
    InProcessExecutor,
    default_event_tasks,
    default_tasks,
)
from frame_gallery.isolation.process import Launch
from frame_gallery.net.wire import Resolver, Transport, WireRequest
from frame_gallery.providers.commons_catalog import CATALOG
from frame_gallery.randomness import SeededRandomSource
from frame_gallery.store.layout import StoreLayout
from frame_gallery.tv.port import Marker
from tests.support.clock import FakeClock
from tests.support.commons import CommonsSite
from tests.support.commons import record as commons_record
from tests.support.fakes import Events, FakeTelevision
from tests.support.museums import AicMuseum, aic_image_id, aic_record
from tests.support.net import (
    TEST_IDENTITY,
    FakeResolver,
    FakeResponse,
    FakeTransport,
    image_response,
    json_response,
)

SUPERVISOR_NETWORK = IPv4Network("172.30.32.0/23")
SUPERVISOR_ADDRESS = ip_address("172.30.32.2")
TOKEN = "supervisor-token-0123456789abcdef"  # noqa: S105 - a fake token
LEGACY = "legacy-token-0123456789abcdef"


class StaticNetworks:
    def __init__(self, *networks: IPv4Network) -> None:
        self.networks = tuple(networks)

    def container_networks(self) -> tuple[IPv4Network, ...]:
        return self.networks


class RecordingExecutor(InProcessExecutor):
    """The in-process executor with the production image tasks; the
    watchdog's kill is recorded."""

    def __init__(self, clock: Clock) -> None:
        super().__init__(default_tasks(), clock, event_tasks=default_event_tasks())
        self.tasks: list[str] = []
        self.terminated = 0

    def run(
        self,
        task: str,
        payload: JsonObject,
        *,
        timeout: float,
        on_event: EventSink | None = None,
        should_stop: StopCheck | None = None,
        files: Sequence[int] = (),
    ) -> JsonObject:
        self.tasks.append(task)
        return super().run(
            task,
            payload,
            timeout=timeout,
            on_event=on_event,
            should_stop=should_stop,
            files=files,
        )

    def terminate_all(self) -> None:
        self.terminated += 1


class Rig:
    def __init__(self, tmp_path: Path) -> None:
        for name in ("data", "media", "tmp"):
            (tmp_path / name).mkdir()
        self.layout = StoreLayout(
            data=tmp_path / "data", media=tmp_path / "media", tmp=tmp_path / "tmp"
        )
        self.clock = FakeClock()
        self.events = Events()
        self.tv = FakeTelevision(self.events, self.clock)
        self.executors: list[RecordingExecutor] = []
        self.launches: list[Launch] = []
        self.resolver = FakeResolver({"supervisor": (SUPERVISOR_ADDRESS,)})
        self.transport = FakeTransport(clock=self.clock, handler=self.route)
        self.museum: AicMuseum | None = None
        self.helper_state = "cleveland_museum_of_art"
        self.environ: dict[str, str] = {
            "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "SUPERVISOR_TOKEN": TOKEN,
            "HASSIO_TOKEN": LEGACY,
            "HTTPS_PROXY": "http://proxy.invalid:3128",
            "SSL_CERT_FILE": "/etc/elsewhere.pem",
        }
        self.stream = io.StringIO()
        self.wiring = entry.Wiring(
            layout=self.layout,
            clock=self.clock,
            random=lambda: SeededRandomSource(5),
            networks=StaticNetworks(SUPERVISOR_NETWORK),
            launch=self.launch,
            executor=self.executor,
            network=self.network,
            television=lambda executor, layout: self.tv,
            identity=lambda: TEST_IDENTITY,
            require_isolation=False,
        )

    def launch(self) -> Launch:
        launch = Launch.production()
        self.launches.append(launch)
        return launch

    def executor(
        self, launch: Launch, clock: Clock, controller: CancellationController
    ) -> RecordingExecutor:
        executor = RecordingExecutor(clock)
        self.executors.append(executor)
        return executor

    def network(self) -> tuple[Resolver, Transport]:
        return self.resolver, self.transport

    def route(self, request: WireRequest) -> FakeResponse:
        if request.host == "supervisor":
            body = json.dumps({"entity_id": "input_select.x", "state": self.helper_state})
            return FakeResponse(
                status=200,
                headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
                body=body.encode(),
            )
        if request.host == "www.artic.edu":
            return image_response(jpeg((1686, 948)))
        assert self.museum is not None, f"unexpected request to {request.host}"
        return self.museum(request)

    def options(self, **options: object) -> None:
        document = {"tv_host": "10.0.0.5", **options}
        (self.layout.data / "options.json").write_text(json.dumps(document))

    def library_image(self, name: str, size: tuple[int, int]) -> None:
        library = self.layout.media / "frame_gallery" / "library"
        library.mkdir(parents=True, exist_ok=True)
        (library / name).write_bytes(jpeg(size))

    def run(self, **changes: object) -> int:
        wiring = replace(self.wiring, **changes)  # type: ignore[arg-type]
        return entry.run_app(self.environ, self.stream, wiring)

    @property
    def output(self) -> str:
        return self.stream.getvalue()

    @property
    def summary_lines(self) -> list[str]:
        return [line for line in self.output.splitlines() if " outcome=" in line]


def jpeg(size: tuple[int, int]) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (200, 120, 40)).save(buffer, "JPEG", quality=85)
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def _restore_process_state() -> Iterator[None]:
    """``run_app`` installs a SIGTERM handler and configures the root logger."""
    handler = signal.getsignal(signal.SIGTERM)
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    app_level = logging.getLogger("frame_gallery").level
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, handler)
        root.handlers[:] = handlers
        root.setLevel(level)
        logging.getLogger("frame_gallery").setLevel(app_level)


@pytest.fixture
def rig(tmp_path: Path) -> Rig:
    return Rig(tmp_path)


# ------------------------------------------------------------- a whole run


def test_a_local_media_run_delivers_through_the_production_wiring(rig: Rig) -> None:
    rig.options(source="local_media")
    rig.library_image("harbour.jpg", (1920, 1080))
    assert rig.run() == 0
    assert rig.summary_lines[-1].split(": ", 1)[1].startswith("outcome=delivered exit=0")
    (request,) = rig.tv.requests
    assert str(request.tv_host) == "10.0.0.5"
    preview = rig.layout.media / "frame_gallery" / "preview" / "latest.jpg"
    assert preview.read_bytes() == rig.tv.payloads[0]
    history = json.loads((rig.layout.data / "state" / "history.json").read_text())
    (recorded,) = history["entries"]
    assert recorded["id"].startswith("local:fp:")
    assert rig.executors[0].tasks == ["inspect", "prepare"]
    assert not list((rig.layout.tmp / "frame-gallery").iterdir())  # workspace removed
    assert "storage: bucket=scratch status=ok files=0 bytes=0" in rig.output
    assert "run_directories=0" in rig.output
    assert rig.output.splitlines()[-1].split(": ", 1)[1].startswith("outcome=delivered")


def test_the_library_warning_counts_the_last_inspection_batch(rig: Rig) -> None:
    """Both files form one batch, inspected after the scan has ended; the
    wiring still logs the broken one in the aggregated warning (§9.3)."""
    rig.options(source="local_media")
    rig.library_image("harbour.jpg", (1920, 1080))
    library = rig.layout.media / "frame_gallery" / "library"
    (library / "broken.jpg").write_bytes(b"\xff\xd8\xff\xe0 not a real JPEG")
    assert rig.run() == 0
    assert "local library: 1 entries skipped (unreadable=1)" in rig.output


def test_a_second_start_changes_no_state(rig: Rig) -> None:
    """While another run holds the state lock, a damaged current.json stays
    where it is: the early read of the preview fingerprints changes nothing."""
    rig.options(source="local_media")
    state = rig.layout.data / "state"
    state.mkdir(mode=0o700)
    (state / "current.json").write_text("{damaged")
    lock = os.open(state / ".lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)  # the other run
        assert rig.run() == 0
    finally:
        os.close(lock)
    assert "outcome=already_running" in rig.output
    assert (state / "current.json").read_text() == "{damaged"
    assert not (state / "quarantine").exists()


def test_the_environment_is_reduced_before_anything_runs(rig: Rig) -> None:
    rig.options(source="local_media")
    rig.run()
    assert rig.environ == {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
    assert TOKEN not in rig.output
    assert LEGACY not in rig.output


def test_the_supervisor_token_is_used_only_for_configured_helpers(rig: Rig) -> None:
    rig.museum = None
    rig.helper_state = "local_media"
    rig.options(source="art_institute_chicago", source_helper="input_select.frame_source")
    rig.run()
    (call,) = [c for c in rig.transport.calls if c.request.host == "supervisor"]
    assert call.request.headers["Authorization"] == f"Bearer {TOKEN}"
    assert call.request.target == "/core/api/states/input_select.frame_source"
    assert "source=local_media (helper)" in rig.output
    assert TOKEN not in rig.output


def test_without_helpers_no_supervisor_request_is_made(rig: Rig) -> None:
    rig.options(source="local_media")
    rig.run()
    assert not [c for c in rig.transport.calls if c.request.host == "supervisor"]
    assert not rig.resolver.calls


def test_optional_artwork_information_is_wired_to_preview_only_and_keeps_token_private(
    rig: Rig,
) -> None:
    helper = "input_text.frame_gallery_artwork"
    rig.options(source="local_media", artwork_info_helper=helper)
    rig.library_image("Synthetic landscape.jpg", (3840, 2160))
    assert rig.run() == 0
    calls = rig.transport.calls
    assert len(calls) == 3
    assert calls[0].request.target == "/core/api/states/" + helper
    for call in calls[1:]:
        assert call.request.target == "/core/api/services/input_text/set_value"
        assert call.request.headers["Authorization"] == f"Bearer {TOKEN}"
    assert json.loads(calls[1].request.body or b"")["value"] == ""
    info = json.loads(json.loads(calls[2].request.body or b"")["value"])
    assert info == {"title": "Synthetic landscape", "artist": "", "museum": "Local images"}
    preview = rig.layout.media / "frame_gallery" / "preview" / "latest.jpg"
    assert preview.read_bytes() == rig.tv.payloads[0]
    previous = preview.read_bytes()
    current = (rig.layout.data / "state" / "current.json").read_bytes()
    rig.environ["SUPERVISOR_TOKEN"] = TOKEN
    assert rig.run() == 0  # no-match must not clear the previous helper
    assert len(rig.transport.calls) == 3
    assert preview.read_bytes() == previous
    assert (rig.layout.data / "state" / "current.json").read_bytes() == current
    assert TOKEN not in rig.output
    assert "SUPERVISOR_TOKEN" not in rig.environ


@pytest.mark.parametrize("deliver", [False, True])
def test_explicit_loading_timer_uses_only_the_guarded_completion_service(
    rig: Rig, deliver: bool
) -> None:
    rig.options(source="local_media", loading_timer="timer.frame_gallery_test_run")
    if deliver:
        rig.library_image("synthetic.jpg", (3840, 2160))
    assert rig.run() == 0
    (call,) = rig.transport.calls
    assert call.request.target == "/core/api/services/timer/cancel"
    assert call.request.method == "POST"
    assert json.loads(call.request.body or b"") == {"entity_id": "timer.frame_gallery_test_run"}
    assert call.request.headers["Authorization"] == f"Bearer {TOKEN}"
    assert rig.environ == {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
    assert TOKEN not in rig.output
    assert "loading timer completion acknowledged" in rig.output


def test_the_museum_wiring_uses_the_identity_and_the_file_cache(rig: Rig) -> None:
    museum = AicMuseum()
    museum.records = [aic_record(n, date_start=1500 + n) for n in range(1, 4)]
    museum.sizes = {aic_image_id(n): (3840, 2160) for n in range(1, 4)}
    rig.museum = museum
    rig.options(source="art_institute_chicago")
    assert rig.run() == 0
    assert rig.summary_lines[-1].split(": ", 1)[1].startswith("outcome=delivered")
    assert all(
        call.request.headers["User-Agent"] == TEST_IDENTITY.user_agent
        for call in rig.transport.calls
    )
    cache = json.loads((rig.layout.data / "cache" / "aic.json").read_text())
    assert cache["provider"] == "aic"


def test_commons_production_wiring_delivers_two_distinct_works_and_cleans_up(rig: Rig) -> None:
    site = CommonsSite(records={work.page_id: commons_record(work) for work in CATALOG})

    def route(request: WireRequest) -> FakeResponse:
        if request.host in {"upload.wikimedia.org", "thumb.wikimedia.org"}:
            return image_response(jpeg((3840, 2160)))
        return site(request)

    rig.transport.handler = route
    rig.options(source="wikimedia_commons")
    for _ in range(2):
        assert rig.run() == 0
        assert "outcome=delivered " in rig.summary_lines[-1]
    history = json.loads((rig.layout.data / "state" / "history.json").read_text())
    ids = [item["id"] for item in history["entries"]]
    assert len(ids) == len(set(ids)) == 2
    assert all(value.startswith("commons:") for value in ids)
    preview = rig.layout.media / "frame_gallery" / "preview" / "latest.jpg"
    assert preview.read_bytes() == rig.tv.payloads[-1]
    assert len(rig.tv.payloads) == 2
    assert not list((rig.layout.tmp / "frame-gallery").iterdir())
    assert "run_directories=0" in rig.output
    assert not (rig.layout.data / "cache" / "commons.json").exists()
    assert {path.name for path in preview.parent.iterdir()} == {"latest.jpg"}


def test_commons_landscape_fallback_preserves_edges_and_publishes_caption(rig: Rig) -> None:
    site = CommonsSite(records={work.page_id: commons_record(work) for work in CATALOG})
    for row in site.records.values():
        assert isinstance(row, dict)
        infos = row["imageinfo"]
        assert isinstance(infos, list)
        infos[0]["thumbheight"] = 2560
    captions: list[dict[str, str]] = []

    def route(request: WireRequest) -> FakeResponse:
        if request.host == "supervisor":
            if request.method == "GET":
                return json_response({"state": "", "attributes": {"max": 255}})
            assert request.body is not None
            body = json.loads(request.body)
            assert body["entity_id"] == "input_text.frame_gallery_artwork"
            if body["value"]:
                captions.append(json.loads(body["value"]))
            return FakeResponse(status=200)
        if request.host in {"upload.wikimedia.org", "thumb.wikimedia.org"}:
            return image_response(jpeg((3840, 2560)))
        return site(request)

    rig.transport.handler = route
    rig.options(source="wikimedia_commons", artwork_info_helper="input_text.frame_gallery_artwork")
    assert rig.run() == 0
    assert "outcome=delivered " in rig.summary_lines[-1]
    assert len(site.queries) == 10  # finite full search, then existing safe fallback
    assert len(captions) == 1
    assert captions[0]["museum"] == "Wikimedia Commons"
    current = json.loads((rig.layout.data / "state" / "current.json").read_text())
    work = next(work for work in CATALOG if "commons:" + str(work.page_id) == current["id"])
    assert captions[0]["artist"] == work.artist
    assert captions[0]["title"] == work.title
    with Image.open(io.BytesIO(rig.tv.payloads[-1])) as image:
        assert image.size == (3840, 2160)
        assert image.getpixel((0, 1080)) == (0, 0, 0)
        assert image.getpixel((3839, 1080)) == (0, 0, 0)
        assert image.getpixel((1920, 1080)) != (0, 0, 0)
    assert not list((rig.layout.tmp / "frame-gallery").iterdir())


def test_the_log_level_option_reaches_the_app_loggers(rig: Rig) -> None:
    rig.options(source="local_media", log_level="debug")
    rig.library_image("a.jpg", (1920, 1080))
    rig.run()
    assert " DEBUG frame_gallery." in rig.output


def test_invalid_options_end_the_run_as_config_invalid(rig: Rig) -> None:
    (rig.layout.data / "options.json").write_text("[]")
    assert rig.run() == 0
    assert "outcome=config_invalid" in rig.summary_lines[-1]
    assert not rig.tv.requests


# ------------------------------------------------------------- refusals


def test_the_app_refuses_to_run_without_isolation(rig: Rig) -> None:
    rig.options(source="local_media")
    code = rig.run(
        require_isolation=True, launch=lambda: replace(Launch.production(), identity=None)
    )
    assert code == 70
    assert rig.summary_lines[-1].split(": ", 1)[1].startswith("outcome=internal_error exit=70")
    assert "the workers cannot be isolated here" in rig.output
    assert not rig.executors
    assert not (rig.layout.data / "state").exists()
    assert rig.environ == {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}


def test_an_isolated_launch_is_accepted(rig: Rig) -> None:
    rig.options(source="local_media")
    enforced = replace(
        Launch.production(),
        identity=(65534, 65534),
        require_pdeathsig=True,
        skip_limits=frozenset(),
    )
    assert enforced.enforced
    rig.run(require_isolation=True, launch=lambda: enforced)
    assert rig.executors


def test_unreadable_container_networks_end_the_run_as_config_invalid(rig: Rig) -> None:
    rig.options(source="local_media", source_helper="input_select.frame_source")
    networks = ContainerNetworks(rig.layout.data / "no-route-table", platform="linux")
    assert rig.run(networks=networks) == 0
    assert "outcome=config_invalid" in rig.summary_lines[-1]
    assert "could not read the container's own networks" in rig.output
    assert not [c for c in rig.transport.calls if c.request.host == "supervisor"]


# ------------------------------------------------------------- the watchdog


def test_a_run_claimed_by_the_watchdog_waits_for_its_exit(rig: Rig) -> None:
    """The watchdog emits the only summary line; ``run_app`` then waits for
    the exit instead of emitting its own (§4.3, §19)."""
    exited = threading.Event()
    codes: list[int] = []

    def exit_process(code: int) -> None:
        codes.append(code)
        exited.set()

    def jump_past_the_cap(marker: Marker) -> None:
        if marker is Marker.UPLOAD_STARTED:
            rig.clock.advance(200.0)
            assert exited.wait(5.0)

    def nap(seconds: float) -> bool:
        del seconds
        return exited.wait(0.001)

    rig.tv.during = jump_past_the_cap
    rig.options(source="local_media")
    rig.library_image("a.jpg", (1920, 1080))
    rig.run(watchdog_exit=exit_process, watchdog_wait=nap)
    assert codes == [71]
    assert [line.split(": ", 1)[1] for line in rig.summary_lines] == [
        "outcome=watchdog_termination exit=71 elapsed=200.0"
    ]
    assert rig.executors[0].terminated == 2  # the watchdog's kill, then CLEANUP's


# ------------------------------------------------------------- the module


def test_the_production_wiring_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    wiring = entry.Wiring()
    assert wiring.layout == StoreLayout()
    assert wiring.watchdog_wait is None
    assert wiring.require_isolation is sys.platform.startswith("linux")
    resolver, transport = wiring.network()
    assert type(resolver).__name__ == "SystemResolver"
    assert type(transport).__name__ == "Urllib3Transport"
    launch = replace(Launch.production(), identity=None)
    executor = wiring.executor(launch, FakeClock(), CancellationController())
    assert type(executor).__name__ == "ProcessExecutor"
    television = wiring.television(executor, StoreLayout())
    assert type(television).__name__ == "HostTelevision"


def test_main_runs_the_production_wiring(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[Mapping[str, str], object, entry.Wiring]] = []

    def fake_run_app(environ: Mapping[str, str], stream: object, wiring: entry.Wiring) -> int:
        seen.append((environ, stream, wiring))
        return 7

    monkeypatch.setattr(entry, "run_app", fake_run_app)
    assert entry.main() == 7
    ((environ, stream, wiring),) = seen
    assert environ is os.environ
    assert stream is sys.stderr
    assert wiring == entry.Wiring(
        clock=wiring.clock,
        networks=wiring.networks,
        require_isolation=wiring.require_isolation,
        require_apparmor=True,
    )


def test_missing_app_profile_refuses_before_network(rig: Rig) -> None:
    rig.wiring = replace(
        rig.wiring,
        require_apparmor=True,
        launch=lambda: replace(Launch.production(), apparmor_profile=None),
    )
    assert rig.run() == 70
    assert rig.executors == []
    assert "no artwork was sent" in rig.stream.getvalue()


def test_complain_profile_refuses_before_network(rig: Rig) -> None:
    def complain() -> Launch:
        raise ProfileError("parent_not_enforced")

    rig.wiring = replace(rig.wiring, launch=complain)
    assert rig.run() == 70
    assert rig.executors == []


def test_importing_the_entry_point_has_no_side_effects() -> None:
    """§11.3: the module defines things and runs nothing when imported."""
    assert signal.getsignal(signal.SIGTERM) is not None
    assert callable(entry.main)
