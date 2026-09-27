"""E7-E10 with the process-based television worker (§12.4, §13.6, §14; D-141, D-162, D-163).

The runner works over the real store, as in test_state_scenarios.py, but the
television is the real Samsung adapter over the real process executor: every
delivery runs in a worker process, with the production delivery logic over
the stand-in of the library (``fake_deliver`` in tests/support/worker_tasks.py,
behind the H2 guard). The markers therefore cross the real pipe. The
stand-in is scripted through ``fake-tv.json`` in the rig's ``tmp``.

The SIGKILL scenarios kill the runner's own process while its worker runs:
the worker must die with it (its lifeline), and the next run must not upload
the work again.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import textwrap
import time
from ipaddress import IPv4Address
from pathlib import Path

import pytest

from frame_gallery.app.outcomes import Hint, Outcome
from frame_gallery.tv.port import (
    DeliveryRequest,
    DeliveryResult,
    Marker,
    MarkerEvent,
    MarkerSink,
)
from frame_gallery.tv.samsung import SamsungTelevision
from frame_gallery.tv.token_store import TokenStore
from tests.support.fakes import TEST_TV_HOST
from tests.support.persistent import PersistentRig
from tests.support.processes import worker_executor
from tests.unit.app.harness import Harness

PROJECT = Path(__file__).resolve().parents[2]
HOST = IPv4Address(TEST_TV_HOST)


@pytest.fixture
def rig(tmp_path: Path) -> PersistentRig:
    return PersistentRig(tmp_path / "rig")


def with_worker(rig: PersistentRig, h: Harness, **script: object) -> Harness:
    (rig.layout.tmp / "fake-tv.json").write_text(json.dumps(script))
    h.tv = SamsungTelevision(worker_executor(), TokenStore(rig.layout.data, HOST))  # type: ignore[assignment]
    return h


def calls(rig: PersistentRig) -> list[str]:
    loaded = json.loads((rig.layout.tmp / "fake-tv-calls.json").read_text())
    assert isinstance(loaded, list)
    return loaded


def test_a_delivery_through_the_worker(rig: PersistentRig) -> None:
    """E1, E10: the markers cross the pipe; history, ledger, preview, and
    token follow the selection."""
    h = with_worker(rig, rig.harness())
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert rig.history() == ["aic:1001"]
    assert rig.ledger() == {"aic:1001": "uploaded"}
    assert rig.preview_file.exists()
    assert TokenStore(rig.layout.data, HOST).load() == "12345678"
    made = calls(rig)
    assert made[-1] == "shutdown"
    assert any(call.startswith("select:MY_F0042:True") for call in made)
    assert rig.leftovers() == []


def test_e7_selection_refused(rig: PersistentRig) -> None:
    result = with_worker(rig, rig.harness(), select="refused").run()
    assert result.outcome is Outcome.TV_REJECTED
    assert rig.ledger() == {"aic:1001": "uploaded"}
    assert rig.history() == []
    assert not rig.preview_file.exists()
    assert rig.current() is None  # E10
    assert rig.harness(days=45).run().delivered_id == "aic:1002"


def test_e8_connection_lost_during_selection(rig: PersistentRig) -> None:
    result = with_worker(rig, rig.harness(), select="lost").run()
    assert result.outcome is Outcome.TV_UNREACHABLE
    assert result.hint == Hint.STORED_ON_TV
    assert rig.ledger() == {"aic:1001": "uploaded"}
    assert rig.current() is None
    assert rig.harness(days=45).run().delivered_id == "aic:1002"


def test_a_lost_upload_is_quarantined(rig: PersistentRig) -> None:
    result = with_worker(rig, rig.harness(), upload="lost").run()
    assert result.outcome is Outcome.TV_UNREACHABLE
    assert result.hint == Hint.UPLOAD_MAY_HAVE_REACHED_TV
    assert rig.ledger() == {"aic:1001": "uncertain"}
    assert rig.harness(days=1).run().delivered_id == "aic:1002"


def test_a_rejected_token_is_removed_and_the_intent_too(rig: PersistentRig) -> None:
    TokenStore(rig.layout.data, HOST).install("87654321")
    result = with_worker(rig, rig.harness(), open=["unauthorized"]).run()
    assert result.outcome is Outcome.TV_NOT_AUTHORIZED
    assert TokenStore(rig.layout.data, HOST).load() is None
    assert rig.ledger() == {}


def test_a_stop_request_during_the_upload_kills_the_worker(rig: PersistentRig) -> None:
    """D-141: a SIGTERM during the delivery is deferred; the adapter polls it,
    kills its worker (which hangs in the upload), keeps the markers already
    sent, and the run is cancelled with the upload in quarantine."""
    h = with_worker(rig, rig.harness(), upload="hang", hang_s=60)
    deliver = h.tv.deliver

    def stopping_deliver(request: DeliveryRequest, on_marker: MarkerSink) -> DeliveryResult:
        def take(event: MarkerEvent) -> None:
            on_marker(event)
            if event.marker is Marker.UPLOAD_STARTED:
                h.cancellation.request_stop()  # deferred: the adapter polls it

        return deliver(request, take)

    h.tv.deliver = stopping_deliver  # type: ignore[method-assign]
    started = time.monotonic()
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert time.monotonic() - started < 20
    assert rig.ledger() == {"aic:1001": "uncertain"}
    worker = int((rig.layout.tmp / "fake-tv-worker.pid").read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(worker, 0)  # killed and reaped before deliver returned


CHILD = textwrap.dedent(
    """
    import sys
    from ipaddress import IPv4Address
    from pathlib import Path

    from frame_gallery.tv.port import Marker
    from frame_gallery.tv.samsung import SamsungTelevision
    from frame_gallery.tv.token_store import TokenStore
    from tests.support.fakes import TEST_TV_HOST
    from tests.support.persistent import PersistentRig, kill_self
    from tests.support.processes import worker_executor

    root, point = Path(sys.argv[1]), sys.argv[2]
    rig = PersistentRig(root)
    h = rig.harness()
    television = SamsungTelevision(
        worker_executor(), TokenStore(rig.layout.data, IPv4Address(TEST_TV_HOST))
    )
    deliver = television.deliver
    marker = {"after_uploaded": Marker.UPLOADED, "after_selected": Marker.SELECTED}[point]

    def killing_deliver(request, on_marker):
        def take(event):
            on_marker(event)
            if event.marker is marker:
                kill_self()

        return deliver(request, take)

    television.deliver = killing_deliver
    h.tv = television
    h.run()
    raise SystemExit("the child was not killed")
    """
)


@pytest.mark.parametrize("point", ["after_uploaded", "after_selected"])
def test_e9_the_runner_killed_while_its_worker_runs(rig: PersistentRig, point: str) -> None:
    (rig.layout.tmp / "fake-tv.json").write_text(json.dumps({"select": "hang", "hang_s": 60}))
    if point == "after_selected":
        (rig.layout.tmp / "fake-tv.json").write_text(json.dumps({}))
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": os.pathsep.join([str(PROJECT / "src"), str(PROJECT)]),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    completed = subprocess.run(  # noqa: S603 - our own interpreter and script
        [sys.executable, "-c", CHILD, str(rig.root), point],
        cwd=PROJECT,
        env=env,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == -signal.SIGKILL, completed.stderr.decode()
    worker = int((rig.layout.tmp / "fake-tv-worker.pid").read_text())
    deadline = time.monotonic() + 10
    while True:  # the orphaned worker ends with its parent (its lifeline)
        try:
            os.kill(worker, 0)
        except ProcessLookupError:
            break
        assert time.monotonic() < deadline, "the television worker outlived the runner"
        time.sleep(0.05)
    assert rig.ledger() == {"aic:1001": "uploaded"}
    assert rig.history() == []
    next_run = rig.harness(days=1)
    assert next_run.run().delivered_id == "aic:1002"
    assert rig.leftovers() == []
