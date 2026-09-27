"""The run's private scratch space (§13.1, §14).

``/tmp/frame-gallery/run-<16 hex digits>/{in,out}`` on the container's
RAM-backed ``/tmp``. The root must belong to this process's user and is kept
at mode 0700; the run directory and its two subdirectories are created with
mode 0700, without following a symbolic link. The runner removes the run
directory on every path (``finally``), and the startup sweep removes any run
directory that a killed run left behind.

Phase 5 gives ``in/`` and ``out/`` the modes that the unprivileged worker
needs (§11.3).
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Final

from frame_gallery.domain import WorkspacePaths
from frame_gallery.errors import StateError
from frame_gallery.store import atomic
from frame_gallery.store.atomic import errno_name, open_directory

WORKSPACE_DIRECTORY: Final = "frame-gallery"
RUN_NAME: Final = re.compile(r"run-[0-9a-f]{16}")
INBOX: Final = "in"
OUTBOX: Final = "out"

_log = logging.getLogger("frame_gallery.store")


class RunWorkspace:
    """The ``Workspace`` port. One instance serves one run."""

    def __init__(self, tmp_root: Path) -> None:
        self._tmp_root = tmp_root
        self._paths: WorkspacePaths | None = None

    def create(self) -> WorkspacePaths:
        """Create this run's scratch directory (once). Raises ``StateError``."""
        if self._paths is not None:
            return self._paths
        name = f"run-{atomic.new_token()}"
        with open_directory(
            self._tmp_root, (WORKSPACE_DIRECTORY,), create=True, mode=0o700
        ) as root:
            try:
                info = os.fstat(root.fd)
                if info.st_uid != os.geteuid():
                    msg = f"{root.label} belongs to another user"
                    raise StateError(msg)
                os.fchmod(root.fd, 0o700)
                os.mkdir(name, 0o700, dir_fd=root.fd)
                with root.child(name) as run:
                    os.mkdir(INBOX, 0o700, dir_fd=run.fd)
                    os.mkdir(OUTBOX, 0o700, dir_fd=run.fd)
            except OSError as exc:
                msg = f"{root.label}: cannot create the run directory ({errno_name(exc)})"
                raise StateError(msg) from None
        path = self._tmp_root / WORKSPACE_DIRECTORY / name
        self._paths = WorkspacePaths(root=path, inbox=path / INBOX, outbox=path / OUTBOX)
        return self._paths

    def remove(self) -> None:
        """Remove the run directory and everything in it (idempotent, never raises)."""
        paths, self._paths = self._paths, None
        if paths is None:
            return
        try:
            with open_directory(self._tmp_root, (WORKSPACE_DIRECTORY,)) as root:
                root.remove(paths.root.name)
        except (OSError, StateError) as exc:
            _log.warning("the run directory could not be removed: %s", exc)
