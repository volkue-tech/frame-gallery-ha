"""The runner over the real store in a temporary directory (§20.1, integration).

The state store, workspace, preview, and run records are the real Phase 4
implementations below temporary ``data``, ``media``, and ``tmp`` anchors. The
provider, fetcher, executor, and television stay fakes, and the fake
television emits its progress markers (E7-E10). Each call of
:meth:`PersistentRig.harness` builds fresh ports over the same directories, as
a new process would.
"""

from __future__ import annotations

import json
import os
import signal
from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path

from frame_gallery.providers.contract import Candidate
from frame_gallery.store.atomic import TEMPORARY_NAME
from frame_gallery.store.layout import StoreLayout
from frame_gallery.store.workspace import RUN_NAME
from tests.support.clock import FAKE_EPOCH, FakeClock
from tests.support.fakes import make_candidate
from tests.unit.app.harness import Harness

DAY = timedelta(days=1)


class ProcessKilled(BaseException):
    """Simulates a kill inside the process: no ``except Exception`` catches it."""


def kill_self() -> None:
    """A real SIGKILL of the current process (used in child processes only)."""
    os.kill(os.getpid(), signal.SIGKILL)


class PersistentRig:
    def __init__(self, root: Path, candidates: Sequence[Candidate] | None = None) -> None:
        self.root = root
        self.layout = StoreLayout(data=root / "data", media=root / "media", tmp=root / "tmp")
        for anchor in (self.layout.data, self.layout.media, self.layout.tmp):
            anchor.mkdir(parents=True, exist_ok=True)
        self.candidates = (
            list(candidates)
            if candidates is not None
            else [make_candidate(number) for number in ("1001", "1002", "1003")]
        )
        self.runs = 0

    def harness(self, *, days: float = 0) -> Harness:
        """A new run, ``days`` after the first one, over the same directories."""
        clock = FakeClock(wall_start=FAKE_EPOCH + days * DAY)
        self.runs += 1
        return Harness(
            self.root / f"harness-{self.runs}",
            candidates=self.candidates,
            clock=clock,
            state_store=self.layout.state_store(clock),
            workspace_port=self.layout.workspace(),
            preview_port=self.layout.preview(),
            records_port=self.layout.records(clock),
        )

    # ------------------------------------------------------------ inspection

    @property
    def state(self) -> Path:
        return self.layout.data / "state"

    @property
    def preview_file(self) -> Path:
        return self.layout.media / "frame_gallery" / "preview" / "latest.jpg"

    def _document(self, name: str) -> dict[str, object] | None:
        path = self.state / name
        if not path.exists():
            return None
        loaded = json.loads(path.read_text())
        assert isinstance(loaded, dict)
        return loaded

    def _entries(self, name: str) -> list[dict[str, str]]:
        document = self._document(name)
        if document is None:
            return []
        entries = document["entries"]
        assert isinstance(entries, list)
        return entries

    def history(self) -> list[str]:
        return [entry["id"] for entry in self._entries("history.json")]

    def ledger(self) -> dict[str, str]:
        return {entry["id"]: entry["state"] for entry in self._entries("upload_ledger.json")}

    def current(self) -> dict[str, object] | None:
        return self._document("current.json")

    def last_run(self) -> dict[str, object]:
        document = self._document("last_run.json")
        assert document is not None
        return document

    def leftovers(self) -> list[str]:
        """Temporary files and run directories that a sweep would remove."""
        found: list[str] = []
        for directory in (
            self.state,
            self.layout.data / "cache",
            self.layout.media / "frame_gallery" / "preview",
        ):
            if directory.is_dir():
                found += [p.name for p in directory.iterdir() if TEMPORARY_NAME.fullmatch(p.name)]
        runs = self.layout.tmp / "frame-gallery"
        if runs.is_dir():
            found += [p.name for p in runs.iterdir() if RUN_NAME.fullmatch(p.name)]
        return sorted(found)
