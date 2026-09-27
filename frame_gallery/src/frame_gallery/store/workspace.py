"""The run's scratch space (§13.1, §14, §11.3; D-155, D-164).

``/tmp/frame-gallery/run-<16 hex digits>/{in,out}`` on the container's
RAM-backed ``/tmp``. The root must belong to this process's user. Every
directory is created with mode 0700, without following a symbolic link, and
then handed to the worker's group, if there is one:

====================  ======  ============  =======================================
directory             mode    group         the worker may
====================  ======  ============  =======================================
``frame-gallery/``    0710    worker        pass through
``run-*/``            0710    worker        pass through
``in/``               2750    worker        read the sources the parent put there
``out/``              2770    worker        create ``delivery-*.jpg``
====================  ======  ============  =======================================

The group is set before the mode (a chown by a non-root user clears the
setgid bit), and each directory's owner, group, and mode are then checked, so
a mistake fails here, with a clear message, and not as ``EACCES`` inside the
worker. The setgid bit gives every file created below the worker's group.
Without a worker group (a development host, where the worker keeps the
developer's identity), every directory stays 0700.

The runner removes the run directory on every path (``finally``), and the
startup sweep removes any run directory that a killed run left behind.
"""

from __future__ import annotations

import contextlib
import logging
import os
import re
import stat
from pathlib import Path
from typing import Final

from frame_gallery.domain import WorkspacePaths
from frame_gallery.errors import StateError
from frame_gallery.store import atomic
from frame_gallery.store.atomic import Directory, errno_name, open_directory

WORKSPACE_DIRECTORY: Final = "frame-gallery"
RUN_NAME: Final = re.compile(r"run-[0-9a-f]{16}")
INBOX: Final = "in"
OUTBOX: Final = "out"

PRIVATE: Final = 0o700
PASS_THROUGH: Final = 0o710
INBOX_MODE: Final = 0o2750
OUTBOX_MODE: Final = 0o2770
HANDED_OVER_FILE: Final = 0o640
"""The mode of every file the parent puts into ``in/`` for the worker."""

_log = logging.getLogger("frame_gallery.store")


class RunWorkspace:
    """The ``Workspace`` port. One instance serves one run.

    ``worker_gid`` is the group of the unprivileged worker (65534 when the
    parent is root), or ``None`` when the worker keeps this process's
    identity."""

    def __init__(self, tmp_root: Path, *, worker_gid: int | None = None) -> None:
        self._tmp_root = tmp_root
        self._worker_gid = worker_gid
        self._paths: WorkspacePaths | None = None

    def _mode(self, shared: int) -> int:
        return PRIVATE if self._worker_gid is None else shared

    def _hand_over(self, directory: Directory, mode: int) -> None:
        """Group first, then mode, then check all three. Raises ``OSError``
        and ``StateError``."""
        if self._worker_gid is not None:
            os.fchown(directory.fd, -1, self._worker_gid)
        os.fchmod(directory.fd, mode)
        info = os.fstat(directory.fd)
        wanted_gid = info.st_gid if self._worker_gid is None else self._worker_gid
        if (info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode)) != (
            os.geteuid(),
            wanted_gid,
            mode,
        ):
            msg = f"{directory.label} did not take owner, group, and mode {mode:o}"
            raise StateError(msg)

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
                self._hand_over(root, self._mode(PASS_THROUGH))
                os.mkdir(name, PRIVATE, dir_fd=root.fd)
            except OSError as exc:
                msg = f"{root.label}: cannot create the run directory ({errno_name(exc)})"
                raise StateError(msg) from None
            try:
                with root.child(name) as run:
                    self._hand_over(run, self._mode(PASS_THROUGH))
                    for child, mode in ((INBOX, INBOX_MODE), (OUTBOX, OUTBOX_MODE)):
                        os.mkdir(child, PRIVATE, dir_fd=run.fd)
                        with run.child(child) as directory:
                            self._hand_over(directory, self._mode(mode))
            except (OSError, StateError) as exc:
                with contextlib.suppress(OSError):
                    root.remove(name)  # never leave a half-made run directory behind
                msg = f"{root.label}: cannot create the run directory ({exc})"
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
