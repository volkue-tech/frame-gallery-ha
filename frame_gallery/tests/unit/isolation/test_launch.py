"""The worker configuration and the shared tables (isolation/launch.py; D-163)."""

from __future__ import annotations

import dataclasses
import json
import os
import sys
from pathlib import Path

import pytest

from frame_gallery.isolation import process
from frame_gallery.isolation.launch import (
    IMAGE_LIMITS,
    MIB,
    PRODUCTION_TASKS,
    TELEVISION_LIMITS,
    WORKER_ENVIRONMENT,
    WORKER_ID,
    WORKER_UMASK,
    Channels,
    ExitCode,
    Limit,
    TaskEntry,
    WorkerConfig,
    ordered_limits,
)
from frame_gallery.isolation.process import BOOT, Launch

GIB = 1024 * MIB


def config(**changes: object) -> WorkerConfig:
    base = WorkerConfig(
        task="prepare",
        module="frame_gallery.imaging.worker_tasks",
        function="prepare_task",
        events=False,
        parent_pid=4321,
        identity=(WORKER_ID, WORKER_ID),
        require_pdeathsig=True,
        umask=WORKER_UMASK,
        limits=ordered_limits(IMAGE_LIMITS, skip=frozenset()),
        environment=WORKER_ENVIRONMENT,
        platform="linux",
        fds=Channels(5, 7, 9),
        log_level=20,
    )
    return dataclasses.replace(base, **changes)  # type: ignore[arg-type]


class TestWorkerConfig:
    def test_round_trip(self) -> None:
        original = config(extra_paths=("/project",), identity=None)
        assert WorkerConfig.from_json(original.to_json()) == original

    def test_it_is_compact_json_without_secrets(self) -> None:
        text = config().to_json()
        data = json.loads(text)
        assert data["limits"][-1] == ["RLIMIT_NPROC", 0]
        assert data["fds"] == [5, 7, 9]
        assert " " not in text.replace("/usr/local/bin:/usr/bin:/bin", "")

    def mutated(self, **changes: object) -> str:
        data = json.loads(config().to_json())
        data.update(changes)
        return json.dumps(data)

    @pytest.mark.parametrize(
        "changes",
        [
            {"task": "has space"},
            {"task": 5},
            {"module": "not..dotted"},
            {"module": "a." * 9 + "b"},
            {"function": "1abc"},
            {"events": 1},
            {"parent_pid": 0},
            {"parent_pid": True},
            {"identity": [0, 65534]},
            {"identity": [65534]},
            {"identity": "65534"},
            {"require_pdeathsig": "yes"},
            {"umask": 0o1000},
            {"limits": {"RLIMIT_AS": 1}},
            {"limits": [["RLIMIT_AS"]]},
            {"limits": [[5, 1]]},
            {"limits": [["RLIMIT_BOGUS", 1]]},
            {"limits": [["RLIMIT_AS", -1]]},
            {"limits": [["RLIMIT_AS", 1], ["RLIMIT_AS", 2]]},
            {"environment": ["PATH"]},
            {"environment": {"PATH": 1}},
            {"platform": "linux-5"},
            {"extra_paths": ["relative"]},
            {"extra_paths": "/project"},
            {"fds": [5, 7]},
            {"fds": [5, 5, 9]},
            {"fds": [1, 7, 9]},
            {"fds": "5,7,9"},
            {"log_level": 60},
        ],
    )
    def test_invalid_fields_are_refused(self, changes: dict[str, object]) -> None:
        with pytest.raises(ValueError, match="invalid worker configuration"):
            WorkerConfig.from_json(self.mutated(**changes))

    @pytest.mark.parametrize("text", ["[]", "{}", '{"task": "x"}', "not json"])
    def test_invalid_documents_are_refused(self, text: str) -> None:
        with pytest.raises(ValueError, match=r"."):
            WorkerConfig.from_json(text)

    def test_an_extra_field_is_refused(self) -> None:
        with pytest.raises(ValueError, match="invalid worker configuration"):
            WorkerConfig.from_json(self.mutated(unknown="x"))


def test_the_process_limit_comes_last_and_skipped_limits_are_left_out() -> None:
    limits = {Limit.PROCESSES: 0, Limit.CPU: 30, Limit.ADDRESS_SPACE: GIB}
    assert ordered_limits(limits, skip=frozenset()) == (
        (Limit.CPU, 30),
        (Limit.ADDRESS_SPACE, GIB),
        (Limit.PROCESSES, 0),
    )
    assert ordered_limits(limits, skip=frozenset({Limit.ADDRESS_SPACE})) == (
        (Limit.CPU, 30),
        (Limit.PROCESSES, 0),
    )


def test_the_production_tables() -> None:
    """Every field of the production launch is pinned here (D-163)."""
    assert {
        "prepare": TaskEntry(
            "frame_gallery.imaging.worker_tasks", "prepare_task", events=False, limits=IMAGE_LIMITS
        ),
        "inspect": TaskEntry(
            "frame_gallery.imaging.worker_tasks", "inspect_task", events=False, limits=IMAGE_LIMITS
        ),
        "deliver": TaskEntry(
            "frame_gallery.tv.samsung_task", "deliver_task", events=True, limits=TELEVISION_LIMITS
        ),
    } == PRODUCTION_TASKS
    assert IMAGE_LIMITS == {
        Limit.ADDRESS_SPACE: GIB,
        Limit.CPU: 30,
        Limit.FILE_SIZE: 16 * MIB,
        Limit.OPEN_FILES: 32,
        Limit.CORE: 0,
        Limit.PROCESSES: 0,
    }
    assert TELEVISION_LIMITS[Limit.ADDRESS_SPACE] == 512 * MIB
    assert TELEVISION_LIMITS[Limit.FILE_SIZE] == MIB
    assert WORKER_ENVIRONMENT == {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LC_ALL": "C.UTF-8",
        "TZ": "UTC",
    }
    assert (WORKER_ID, WORKER_UMASK) == (65534, 0o027)
    assert [code.value for code in ExitCode] == [70, 71, 72, 73, 75]


class TestProductionLaunch:
    def test_as_root_on_linux_everything_is_enforced(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(os, "geteuid", lambda: 0)
        monkeypatch.setattr(process, "_site_paths", lambda: ("/site",))
        monkeypatch.setattr(sys, "platform", "linux")
        launch = Launch.production()
        assert launch.identity == (WORKER_ID, WORKER_ID)
        assert launch.require_pdeathsig
        assert launch.skip_limits == frozenset()
        assert launch.enforced
        assert launch.tasks is PRODUCTION_TASKS
        assert (launch.extra_paths, dict(launch.extra_environment)) == ((), {})
        assert launch.site_paths == ("/site",)
        assert launch.python == sys.executable
        assert launch.source_root == str(process._source_root())

    def test_on_a_development_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(os, "geteuid", lambda: 501)
        monkeypatch.setattr(sys, "platform", "darwin")
        launch = Launch.production()
        assert launch.identity is None
        assert not launch.require_pdeathsig
        assert launch.skip_limits == {Limit.ADDRESS_SPACE}
        assert not launch.enforced

    def test_the_source_root_holds_the_package(self) -> None:
        assert (Path(process._source_root()) / "frame_gallery" / "__init__.py").is_file()


def test_boot_decides_nothing() -> None:
    """BOOT only extends the path and hands over (D-163)."""
    assert BOOT == (
        'import sys;a=sys.argv[2:];i=a.index("--");sys.path[:0]=a[:i];sys.path+=a[i+1:];'
        "from frame_gallery.isolation.worker_main import main;main(sys.argv[1])"
    )


def test_the_site_paths_are_this_interpreters() -> None:
    import sysconfig  # noqa: PLC0415

    paths = process._site_paths()
    assert paths[0] == sysconfig.get_path("purelib")
    assert set(paths) == {sysconfig.get_path("purelib"), sysconfig.get_path("platlib")}
    assert len(paths) == len(set(paths))


def test_distinct_site_paths_are_both_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    import sysconfig  # noqa: PLC0415

    monkeypatch.setattr(sysconfig, "get_path", lambda name: f"/lib/{name}")
    assert process._site_paths() == ("/lib/purelib", "/lib/platlib")
