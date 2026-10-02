"""Root-only checks of the isolation (§11.3, D-163, D-164, D-165).

They run only as root on Linux, the Phase 6 container
(``FRAME_GALLERY_REQUIRE_ISOLATION=root`` makes a skip a failure). A root
parent drops every worker to 65534, and such a worker loads no test code, so
these tests run production tasks without the H2 guard. That is safe only
because each task here opens no socket: ``prepare`` and ``inspect`` work on
files, and the ``deliver`` request is refused before the library is loaded.
"""

from __future__ import annotations

import dataclasses
import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from frame_gallery.budget.clock import SystemClock
from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.filters import EffectiveFilters, FilterSet
from frame_gallery.domain import BLACK, FitMode, Size, SourceKey
from frame_gallery.imaging.contract import ImageFormat, PrepareRequest
from frame_gallery.isolation.executor import JsonObject, WorkerError, WorkerErrorKind
from frame_gallery.isolation.launch import PRODUCTION_TASKS, WORKER_ID
from frame_gallery.isolation.process import Launch, ProcessExecutor
from frame_gallery.providers.contract import DiscoveryContext
from frame_gallery.providers.local_media import LocalInspectionProbe, LocalMediaProvider
from frame_gallery.randomness import SeededRandomSource
from frame_gallery.store.workspace import HANDED_OVER_FILE, RunWorkspace
from tests.support.images import save_jpeg
from tests.support.processes import require


@pytest.fixture(autouse=True)
def _needs_root_on_linux() -> None:
    require("root")


def production_executor(*tasks: str) -> ProcessExecutor:
    """The production launch, limited to ``tasks``: no other production task
    can run here without the H2 guard."""
    launch = dataclasses.replace(
        Launch.production(), tasks={task: PRODUCTION_TASKS[task] for task in tasks}
    )
    assert launch.enforced
    return ProcessExecutor(launch, SystemClock())


@pytest.mark.parametrize("task", ["prepare", "inspect", "deliver"])
def test_a_production_worker_drops_to_65534(task: str) -> None:
    """The parent checks the worker's ready report (uid and gid 65534, no
    groups, every limit including RLIMIT_AS 1 GiB or 512 MiB) before it sends
    the request; the empty request then fails as a crash, not as an
    isolation failure."""
    with pytest.raises(WorkerError) as caught:
        production_executor(task).run(task, {}, timeout=10)
    assert caught.value.kind is WorkerErrorKind.CRASH


def test_the_dropped_worker_reads_in_and_writes_only_out() -> None:
    """D-164: the workspace below a root the worker can pass through, as
    production's /tmp; the worker reads a source in ``in/``, creates its
    output in ``out/``, and cannot create one in ``in/``."""
    anchor = Path(tempfile.mkdtemp(prefix="frame-gallery-root-test-", dir="/tmp"))
    anchor.chmod(0o711)  # mkdtemp makes it 0700; the worker needs to pass through
    workspace = RunWorkspace(anchor, worker_gid=WORKER_ID)
    try:
        paths = workspace.create()
        handed = paths.inbox / "source-0.bin"
        save_jpeg(Image.new("RGB", (768, 432), (200, 30, 30)), handed)
        handed.chmod(HANDED_OVER_FILE)
        executor = production_executor("prepare")

        def prepare(output: Path) -> JsonObject:
            request = PrepareRequest(
                source_path=str(handed),
                output_path=str(output),
                declared_format=ImageFormat.JPEG,
                fit_mode=FitMode.CONTAIN,
                background=BLACK,
                landscape_only=True,
                require_near_16_9=False,
                canvas=Size(384, 216),
            )
            return executor.run("prepare", request.to_json(), timeout=20)

        assert prepare(paths.outbox / "delivery-0.jpg")["status"] == "ok"
        assert (paths.outbox / "delivery-0.jpg").stat().st_uid == WORKER_ID
        refused = prepare(paths.inbox / "delivery-1.jpg")
        assert (refused["status"], refused["failure"], refused["detail"]) == (
            "failed",
            "io",
            "cannot create the output (EACCES)",
        )
    finally:
        workspace.remove()
        shutil.rmtree(anchor, ignore_errors=True)


def test_the_dropped_worker_inspects_a_file_only_root_can_read() -> None:
    """Phase 5 gate decision: the root parent opens each library file and
    passes the read-only descriptor, so the worker, at 65534, measures a file
    it could not open itself (a 0600 file in a 0700 folder)."""
    anchor = Path(tempfile.mkdtemp(prefix="frame-gallery-root-test-", dir="/tmp"))
    try:
        root = anchor / "library"
        root.mkdir(mode=0o700)
        path = save_jpeg(Image.new("RGB", (96, 54), (30, 120, 30)), root / "private.jpg")
        path.chmod(0o600)
        provider = LocalMediaProvider(
            root=root, preview_dir=anchor / "preview", preview_fingerprints=frozenset()
        )
        filters = EffectiveFilters(
            source=SourceKey.LOCAL_MEDIA,
            department=None,
            style=None,
            period=None,
            color=None,
            ignored=(),
            requested=FilterSet(source=SourceKey.LOCAL_MEDIA),
        )
        context = DiscoveryContext(
            deadline=Deadline.after(SystemClock(), 30.0, "discovery"),
            random=SeededRandomSource(1),
        )
        (candidate,) = provider.iter_candidates(filters, context)
        probe = LocalInspectionProbe(provider, production_executor("inspect"))
        assert probe.measure(candidate, context.deadline) == Size(96, 54)
        assert provider.report.counts == {}
    finally:
        shutil.rmtree(anchor, ignore_errors=True)
