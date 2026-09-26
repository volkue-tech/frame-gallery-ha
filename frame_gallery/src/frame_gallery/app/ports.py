"""The ports the runner depends on (§5, §20.2, D-107).

Phase 2 implements the runner against fakes of these ports. The persistent
store arrives in Phase 4, the provider adapters, the fetcher, and the helper
client in Phase 3, the television worker in Phase 5, and the options file
reader and container-network discovery in Phase 6.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from ipaddress import IPv4Network
from pathlib import Path
from typing import Protocol

from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.filters import FilterField
from frame_gallery.errors import FrameGalleryError
from frame_gallery.imaging.contract import DeliveryArtifact, ImageFormat
from frame_gallery.providers.contract import DimensionProbe, ImageRef, Provider
from frame_gallery.selection.exclusion import ExclusionStore


class OptionsSource(Protocol):
    def load(self, deadline: Deadline) -> Mapping[str, object]:
        """The raw options object. Raises ``ConfigError`` if it is unreadable."""
        ...


class NetworkInfo(Protocol):
    def container_networks(self) -> Sequence[IPv4Network]:
        """The container's own interface networks, including the Supervisor's
        internal network; the television address may not fall inside them."""
        ...


class StateStore(ExclusionStore, Protocol):
    """Lock, exclusions, pre-staged history, and the upload ledger (§13)."""

    def open(self, deadline: Deadline) -> None:
        """Take the non-blocking lock and sweep leftovers.

        Raises ``AlreadyRunning`` or ``StateError``.
        """
        ...

    def prestage_history(self, qualified_id: str, now: datetime) -> None:
        """Write and ``fsync`` the next history generation as a temporary file.

        Raises ``StateError``.
        """
        ...

    def discard_prestaged_history(self) -> None:
        """Remove the pre-staged generation, if any (best-effort, never raises)."""
        ...

    def commit_upload_intent(self, qualified_id: str, now: datetime) -> None:
        """Durably record an ``uncertain`` write-ahead intent. Raises ``StateError``."""
        ...

    def promote_upload(self, qualified_id: str, now: datetime) -> None:
        """Promote the intent to ``uploaded``. Raises ``StateError``."""
        ...

    def remove_upload_intent(self, qualified_id: str) -> None:
        """Remove the ``uncertain`` intent. Raises ``StateError``."""
        ...

    def record_history(self) -> None:
        """Rename the pre-staged generation into place. Raises ``StateError``."""
        ...

    def close(self) -> None:
        """Release the lock (never raises)."""
        ...


class HelperReader(Protocol):
    def read(
        self, helpers: Mapping[FilterField, str], deadline: Deadline
    ) -> Mapping[FilterField, str | None]:
        """The raw ``state`` of each configured helper, or ``None`` for each
        helper that could not be read. Never raises for a failed read.

        Home Assistant's ``unavailable`` and ``unknown`` states are returned as
        they are; the merge treats them like a failed read (B4)."""
        ...


@dataclass(frozen=True, slots=True)
class FetchedImage:
    path: Path
    size_bytes: int
    declared_format: ImageFormat
    """From the ``Content-Type`` header, or the file extension for local media."""


class ImageFetcher(Protocol):
    def fetch(self, ref: ImageRef, destination: Path, deadline: Deadline) -> FetchedImage:
        """Copy the rendition to ``destination``. Raises ``SourceError``,
        ``DeadlineExceeded``, or ``Cancelled``."""
        ...


@dataclass(frozen=True, slots=True)
class ProviderBinding:
    """A provider and, if its metadata may lack dimensions, its probe."""

    provider: Provider
    probe: DimensionProbe | None = None


@dataclass(frozen=True, slots=True)
class WorkspacePaths:
    root: Path
    inbox: Path
    """``in/``: downloads, read-only for the worker."""

    outbox: Path
    """``out/``: the worker's output."""


class Workspace(Protocol):
    def create(self) -> WorkspacePaths:
        """Create this run's private scratch directory. Raises ``StateError``."""
        ...

    def remove(self) -> None:
        """Remove the scratch directory (idempotent, never raises)."""
        ...


class PublishError(FrameGalleryError):
    """The preview could not be published."""


class PreviewPublisher(Protocol):
    def publish(self, artifact: DeliveryArtifact, deadline: Deadline) -> None:
        """Publish the delivery bytes atomically. Raises :class:`PublishError`."""
        ...


class RunRecords(Protocol):
    def write_current(self, record: Mapping[str, object], deadline: Deadline) -> None:
        """Write ``current.json``. Raises ``StateError``."""
        ...

    def write_last_run(self, record: Mapping[str, object], deadline: Deadline) -> None:
        """Write ``last_run.json``. Raises ``StateError``."""
        ...


class WatchdogControl(Protocol):
    def arm(self) -> None: ...

    def disarm(self) -> bool:
        """Stop the watchdog; ``False`` if it had already claimed a firing,
        which then completes (it emits the only summary line and exits 71)."""
        ...
