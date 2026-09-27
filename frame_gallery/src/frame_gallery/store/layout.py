"""Where the store keeps its files (§13.1).

The production anchors are the container's ``/data``, ``/media``, and the
RAM-backed ``/tmp``; tests pass temporary anchors. Every directory below an
anchor is opened without following a symbolic link. The entry point (Phase 6)
builds the store's ports from one layout.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from frame_gallery.budget.clock import Clock
from frame_gallery.store.cache import CACHE_DIRECTORY, FileMetadataCache
from frame_gallery.store.preview import PREVIEW_NAMES, PREVIEW_PARTS, PreviewStore
from frame_gallery.store.records import RunRecordStore
from frame_gallery.store.state import STATE_DIRECTORY, FileStateStore
from frame_gallery.store.sweep import StartupSweep, SweepTarget
from frame_gallery.store.workspace import WORKSPACE_DIRECTORY, RunWorkspace

CACHE_PARTS: Final = (CACHE_DIRECTORY,)
TOKEN_PARTS: Final = ("tv",)


@dataclass(frozen=True, slots=True)
class StoreLayout:
    data: Path = field(default=Path("/data"))
    media: Path = field(default=Path("/media"))
    tmp: Path = field(default=Path("/tmp"))  # noqa: S108 - the container's RAM-backed /tmp

    def startup_sweep(self) -> StartupSweep:
        """The sweep of the state, cache, token, and preview directories and
        of leftover run directories (§14)."""
        return StartupSweep(
            temporary_files=(
                SweepTarget(self.data, (STATE_DIRECTORY,)),
                SweepTarget(self.data, CACHE_PARTS),
                SweepTarget(self.data, TOKEN_PARTS),
                SweepTarget(self.media, PREVIEW_PARTS),
            ),
            run_directories=SweepTarget(self.tmp, (WORKSPACE_DIRECTORY,)),
        )

    def state_store(self, clock: Clock) -> FileStateStore:
        return FileStateStore(self.data, clock=clock, sweep=self.startup_sweep())

    def workspace(self) -> RunWorkspace:
        return RunWorkspace(self.tmp)

    def metadata_cache(self, provider_key: str, clock: Clock) -> FileMetadataCache:
        """The provider's cache; pass it to the adapter and to its binding."""
        return FileMetadataCache(self.data, provider_key, clock=clock)

    def preview(self, names: Sequence[str] = PREVIEW_NAMES) -> PreviewStore:
        """The preview publisher; Phase 8 fixes the names (D-140)."""
        return PreviewStore(self.media, names=names)

    def records(self, clock: Clock) -> RunRecordStore:
        return RunRecordStore(self.data, clock=clock)
