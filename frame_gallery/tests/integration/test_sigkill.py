"""E9 with a real SIGKILL (§12.4, §13.6, §14, §20.1).

A child process runs the runner over the real store and kills itself with
SIGKILL at one point: after the intent was committed, after the ``uploaded``
promotion, or inside the promotion write, before its rename. Nothing in the
child gets to clean up: the pre-staged history, the temporary ledger file,
the run directory, and the lock file stay as a power cut would leave them
(the kernel releases the lock itself). The next run, in this process, must
take the lock, sweep the leftovers, and not upload the work again.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from frame_gallery.app.outcomes import Outcome
from tests.support.persistent import PersistentRig

PROJECT = Path(__file__).resolve().parents[2]

CHILD = textwrap.dedent(
    """
    import os
    import sys
    from pathlib import Path

    from frame_gallery.store.atomic import Directory
    from frame_gallery.tv.port import Marker
    from tests.support.persistent import PersistentRig, kill_self

    root, point = Path(sys.argv[1]), sys.argv[2]
    rig = PersistentRig(root)
    h = rig.harness()
    store = h.state_store

    if point == "after_intent":
        commit = store.commit_upload_intent

        def commit_then_die(qualified_id, now):
            commit(qualified_id, now)
            kill_self()

        store.commit_upload_intent = commit_then_die
    elif point == "after_uploaded":
        h.tv.during = lambda marker: kill_self() if marker is Marker.UPLOADED else None
    elif point == "after_selected":
        h.tv.during = lambda marker: kill_self() if marker is Marker.SELECTED else None
    elif point == "inside_promotion":
        real_commit = Directory.commit

        def commit(directory, staged, *, refresh_backup):
            if staged.name == "upload_ledger.json" and "tv.marker:uploaded" in h.events:
                kill_self()
            real_commit(directory, staged, refresh_backup=refresh_backup)

        Directory.commit = commit
    else:
        raise SystemExit(f"unknown point {point}")
    h.run()
    raise SystemExit("the child was not killed")
    """
)


def run_child(root: Path, point: str) -> None:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": os.pathsep.join([str(PROJECT / "src"), str(PROJECT)]),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    completed = subprocess.run(  # noqa: S603 - our own interpreter and script
        [sys.executable, "-c", CHILD, str(root), point],
        cwd=PROJECT,
        env=env,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == -signal.SIGKILL, completed.stderr.decode()


@pytest.mark.parametrize(
    ("point", "state", "leftover"),
    [
        ("after_intent", "uncertain", "history.json.tmp-"),
        ("after_uploaded", "uploaded", "history.json.tmp-"),
        ("after_selected", "uploaded", "history.json.tmp-"),
        ("inside_promotion", "uncertain", "upload_ledger.json.tmp-"),
    ],
)
def test_a_killed_run_is_never_uploaded_again(
    tmp_path: Path, point: str, state: str, leftover: str
) -> None:
    root = tmp_path / "rig"
    run_child(root, point)
    rig = PersistentRig(root)
    assert rig.ledger() == {"aic:1001": state}
    assert rig.history() == []
    assert not rig.preview_file.exists()
    left = rig.leftovers()
    assert any(name.startswith(leftover) for name in left)
    assert any(name.startswith("run-") for name in left)

    next_run = rig.harness(days=1)
    result = next_run.run()
    assert result.outcome is Outcome.DELIVERED
    assert result.delivered_id == "aic:1002"  # the lock was free; the work stays excluded
    assert rig.leftovers() == []  # the sweep removed what the kill left

    later = rig.harness(days=31).run()
    # An uncertain upload is quarantined for 30 days; a confirmed one forever.
    assert later.delivered_id == ("aic:1001" if state == "uncertain" else "aic:1003")
