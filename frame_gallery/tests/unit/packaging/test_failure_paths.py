"""The failure-path runs of the app image (``scripts/failure_paths.py``, Phase 7).

The script drives Docker; these tests replace it with a recorder, so they
hold the scenarios, the inputs, the checks, and the containers' isolation
(no network, no host directory) to the specification without running one."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tarfile
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest
from PIL import Image

from frame_gallery.store.history import parse_history
from frame_gallery.store.upload_ledger import QUARANTINE_PERIOD, LedgerState, parse_ledger

PROJECT: Final = Path(__file__).resolve().parents[3]
NOW: Final = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)


def _script() -> ModuleType:
    path = PROJECT / "scripts" / "failure_paths.py"
    spec = importlib.util.spec_from_file_location("failure_paths", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


paths: Any = _script()
SCENARIOS: Final = {scenario.name: scenario for scenario in paths.scenarios(NOW)}
STATE: Final = paths.STATE


class FakeDocker:
    """Records every command and answers it like Docker would."""

    def __init__(self, run_output: Callable[[Any], str], snapshot: dict[str, Any]) -> None:
        self.commands: list[list[str]] = []
        self.inputs: list[bytes | None] = []
        self.run_output = run_output
        self.snapshot = snapshot
        self.listening = True
        self.scenario: Any = None

    def __call__(self, arguments: Sequence[str], stdin: bytes | None = None) -> Any:
        command = list(arguments)
        self.commands.append(command)
        self.inputs.append(stdin)
        if command[:1] == ["logs"]:
            output = "listening\naccepted 8002\n" if self.listening else ""
            return paths.Completed(0, output)
        if paths.RUN_APP in command:
            return paths.Completed(0, self.run_output(self.scenario))
        if paths.SNAPSHOT in command:
            return paths.Completed(0, json.dumps(self.snapshot))
        return paths.Completed(0, "")


def _summary(outcome: str, hint: str | None = None, elapsed: str = "1.2") -> str:
    line = "2026-10-03T12:00:00Z ERROR frame_gallery.run: "
    line += f"outcome={outcome} exit=0 elapsed={elapsed}"
    return line + (f' hint="{hint}"' if hint is not None else "")


def _as_specified(scenario: Any) -> str:
    """The output of a run that behaves as the specification says."""
    hint = scenario.hint.value if scenario.hint is not None else None
    lines = [_summary(scenario.outcome.value, hint), "tmp-left=0"]
    if scenario.reaches_tv:
        lines.insert(0, "frame_gallery.run: television result: status=unreachable markers=none")
    return "\n".join(lines) + "\n"


def _snapshot(scenario: Any) -> dict[str, Any]:
    """What such a run leaves in /data and /media."""
    hint = scenario.hint.value if scenario.hint is not None else None
    found: dict[str, Any] = {
        f"{STATE}/last_run.json": {
            "json": {"outcome": scenario.outcome.value, "hint": hint},
            "sha256": "0" * 64,
        },
        "/media/frame_gallery/preview": {"directory": True},
    }
    for name, content in scenario.state.items():
        digest = paths.hashlib.sha256(content).hexdigest()
        if name == scenario.quarantined:
            found[f"{STATE}/quarantine/20261003T120000Z-0123abcd-{name}"] = {"sha256": digest}
        elif name == paths.LEDGER_FILE and scenario.reaches_tv:
            found[f"{STATE}/{name}"] = {"json": {"entries": []}, "sha256": "1" * 64}
        else:
            found[f"{STATE}/{name}"] = {"sha256": digest}
    return found


def _observed(scenario: Any, **changes: Any) -> Any:
    values: dict[str, Any] = {
        "status": 0,
        "output": _as_specified(scenario),
        "snapshot": _snapshot(scenario),
        "accepted": 2 if scenario.silent_tv else None,
    }
    values.update(changes)
    return paths.Observed(**values)


# --- the scenarios and their inputs -------------------------------------------


def test_the_scenarios_cover_the_phase_7_paths() -> None:
    """TASKS Phase 7: no result, timeout, corrupt history, failed download,
    failed decode, and the upload ledger; a failed upload after
    upload_started is left to the suite (E7-E10)."""
    assert {scenario.path for scenario in SCENARIOS.values()} == {
        "no result",
        "timeout",
        "corrupt history",
        "failed download",
        "failed decode",
        "upload ledger",
    }
    assert len(SCENARIOS) == 10
    for scenario in SCENARIOS.values():
        assert scenario.outcome.value in {
            "no_match",
            "image_failed",
            "source_failed",
            "tv_unreachable",
        }
        # A run that reaches the television (and only such a run) has a work.
        assert scenario.reaches_tv <= bool(scenario.library)


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_the_inputs_have_exact_modes_and_stay_below_data_and_media(name: str) -> None:
    scenario = SCENARIOS[name]
    with tarfile.open(fileobj=io.BytesIO(paths.setup_archive(scenario))) as archive:
        members = {member.name: member for member in archive.getmembers()}
        options = archive.extractfile("data/options.json")
        assert options is not None
        assert json.loads(options.read()) == {"tv_host": "10.0.0.5", "source": scenario.source}
    assert members["data/options.json"].mode == 0o600
    for member_name, member in members.items():
        assert member_name.split("/", 1)[0] in {"data", "media"}
        assert ".." not in member_name.split("/")
        assert (member.uid, member.gid) == (0, 0)
        if member_name.startswith("data/state"):
            assert member.mode == (0o700 if member.isdir() else 0o600)
        if member_name.startswith("media/"):
            assert member.mode == (0o755 if member.isdir() else 0o644)
    assert {name.rsplit("/", 1)[-1] for name in members if "/library/" in name} == set(
        scenario.library
    )


def test_the_tar_filter_keeps_the_modes(tmp_path: Path) -> None:
    """The setup extracts with the "tar" filter, which keeps a directory's 0700
    (the "data" filter would not)."""
    archive_bytes = paths.setup_archive(SCENARIOS["ledger-uncertain"])
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r|") as archive:
        archive.extractall(tmp_path, filter="tar")
    assert (tmp_path / "data" / "state").stat().st_mode & 0o777 == 0o700
    assert (tmp_path / "data" / "options.json").stat().st_mode & 0o777 == 0o600
    assert "filter='tar'" in paths.SETUP


def test_the_state_documents_are_valid_and_name_the_library_work() -> None:
    work = paths.local_id(SCENARIOS["ledger-uncertain"].library["harbour.jpg"])
    backup = SCENARIOS["damaged-history-with-backup"].state["history.json.bak"]
    (sent,) = parse_history(json.loads(backup))
    assert sent.qualified_id == work
    with pytest.raises(ValueError, match="Expecting"):
        json.loads(SCENARIOS["damaged-history"].state["history.json"])
    ledgers = {
        name: parse_ledger(json.loads(SCENARIOS[name].state["upload_ledger.json"]))
        for name in ("ledger-uncertain", "ledger-uploaded", "ledger-quarantine-over")
    }
    for (entry,) in ledgers.values():
        assert entry.qualified_id == work
    assert ledgers["ledger-uncertain"][0].excludes(NOW)
    assert ledgers["ledger-uploaded"][0].state is LedgerState.UPLOADED
    assert not ledgers["ledger-quarantine-over"][0].excludes(NOW)
    assert NOW - ledgers["ledger-quarantine-over"][0].at > QUARANTINE_PERIOD


def test_the_broken_jpeg_has_its_header_and_fails_only_when_decoded() -> None:
    """The failed-decode path: inspection reads the header, preparation fails."""
    broken = SCENARIOS["broken-jpeg"].library["broken.jpg"]
    with Image.open(io.BytesIO(broken)) as image:
        assert image.size == (1920, 1080)
        with pytest.raises(OSError, match="truncated"):
            image.load()


def test_the_other_images_are_landscape_and_portrait() -> None:
    with Image.open(io.BytesIO(SCENARIOS["portrait-only"].library["tower.jpg"])) as image:
        assert image.size == (1080, 1920)
    with Image.open(io.BytesIO(SCENARIOS["silent-tv"].library["harbour.jpg"])) as image:
        assert image.size == (1920, 1080)


# --- the checks -----------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_a_run_as_specified_passes(name: str) -> None:
    scenario = SCENARIOS[name]
    assert paths.evaluate(scenario, _observed(scenario)) == []


def test_each_deviation_is_reported() -> None:
    tv = SCENARIOS["silent-tv"]
    nothing = SCENARIOS["empty-library"]
    damaged = SCENARIOS["damaged-history-with-backup"]
    ledger = SCENARIOS["ledger-quarantine-over"]

    def problems(scenario: Any, **changes: Any) -> list[str]:
        result: list[str] = paths.evaluate(scenario, _observed(scenario, **changes))
        assert result, changes
        return result

    output = _as_specified(nothing)
    assert problems(nothing, output=output + output) == ["2 summary lines, expected exactly one"]
    assert (
        "expected outcome=no_match"
        in problems(nothing, output=output.replace("no_match", "source_failed"))[0]
    )
    assert "exit 0 (container 1)" in problems(nothing, status=1)[0]
    slow = _summary("no_match", nothing.hint.value, elapsed="70.1") + "\ntmp-left=0\n"
    assert "more than 70 s" in problems(nothing, output=slow)[0]
    assert "(F2)" in problems(nothing, output=output.replace("tmp-left=0", "tmp-left=1"))[0]
    assert "(C7)" in problems(nothing, output="frame_gallery.run: television: x\n" + output)[0]
    assert (
        "before upload_started"
        in problems(tv, output=_as_specified(tv).replace("markers=none", "markers=upload_started"))[
            0
        ]
    )
    assert "accepted no connection" in problems(tv, accepted=0)[0]

    snapshot = _snapshot(nothing)
    del snapshot[f"{STATE}/last_run.json"]
    assert "no readable last_run.json" in problems(nothing, snapshot=snapshot)
    snapshot = _snapshot(nothing)
    snapshot[f"{STATE}/last_run.json"]["json"]["outcome"] = "delivered"
    assert "last_run.json says delivered" in problems(nothing, snapshot=snapshot)[0]
    snapshot = _snapshot(nothing) | {f"{STATE}/history.json.tmp-0123456789abcdef": {}}
    assert "(F2)" in problems(nothing, snapshot=snapshot)[0]
    snapshot = _snapshot(nothing) | {"/media/frame_gallery/preview/latest.jpg": {}}
    assert "a preview was published" in problems(nothing, snapshot=snapshot)[0]
    snapshot = _snapshot(nothing) | {f"{STATE}/history.json": {}}
    assert "(E4)" in problems(nothing, snapshot=snapshot)[0]

    snapshot = _snapshot(damaged) | {f"{STATE}/history.json": {"sha256": "2" * 64}}
    assert "still in place" in problems(damaged, snapshot=snapshot)[0]
    snapshot = {
        path: entry for path, entry in _snapshot(damaged).items() if "/quarantine/" not in path
    }
    assert "(F5)" in problems(damaged, snapshot=snapshot)[0]
    snapshot = _snapshot(damaged)
    snapshot[f"{STATE}/history.json.bak"] = {"sha256": "3" * 64}
    assert problems(damaged, snapshot=snapshot) == ["history.json.bak changed"]

    work = paths.local_id(ledger.library["harbour.jpg"])
    snapshot = _snapshot(ledger)
    snapshot[f"{STATE}/upload_ledger.json"]["json"] = {
        "entries": [{"id": work, "state": "uncertain", "at": NOW.isoformat()}]
    }
    assert "still names the work" in problems(ledger, snapshot=snapshot)[0]
    snapshot = _snapshot(tv) | {
        f"{STATE}/upload_ledger.json": {"json": {"entries": [{"id": work}]}}
    }
    assert "still names the work" in problems(tv, snapshot=snapshot)[0]


def test_a_document_without_entries_names_no_work() -> None:
    assert paths._ids(None) == set()
    assert paths._ids({"entries": "none"}) == set()
    assert paths._ids({"entries": [{"id": "local:fp:00"}, "odd"]}) == {"local:fp:00"}


# --- the runs ---------------------------------------------------------------------


def _main(docker: FakeDocker, tmp_path: Path, arch: str = "aarch64") -> int:
    original = paths.run_scenario

    def tracked(scenario: Any, *args: Any) -> Any:
        docker.scenario = scenario
        return original(scenario, *args)

    paths.run_scenario = tracked
    try:
        result: int = paths.main([arch], docker, lambda: NOW, lambda _: None, tmp_path)
    finally:
        paths.run_scenario = original
    return result


def test_every_container_is_offline_and_mounts_no_host_directory(tmp_path: Path) -> None:
    docker = FakeDocker(_as_specified, {})
    _main(docker, tmp_path)
    runs = [command for command in docker.commands if command[0] == "run"]
    assert runs
    for command in runs:
        network = command[command.index("--network") + 1]
        assert network in {"none", "container:fg-paths-aarch64-tv"}
        assert command[command.index("--platform") + 1] == "linux/arm64"
        assert "--privileged" not in command
        for index, value in enumerate(command):
            if value == "-v":
                assert command[index + 1].split(":", 1)[0] in {
                    "fg-paths-aarch64-data",
                    "fg-paths-aarch64-media",
                }
        if "NET_ADMIN" in command:  # only the silent television's helper
            assert network == "none"
            assert "-d" in command
        if network.startswith("container:"):
            assert paths.RUN_APP in command
    app_runs = [command for command in runs if paths.RUN_APP in command]
    assert len(app_runs) == len(SCENARIOS)
    assert sum("NET_ADMIN" in command for command in runs) == 1
    assert all("--tmpfs" in command for command in app_runs)
    # Every volume and the helper are removed again.
    removals = [command for command in docker.commands if command[:2] == ["volume", "rm"]]
    assert len(removals) == 2 * len(SCENARIOS)
    assert docker.commands.count(["rm", "-f", "fg-paths-aarch64-tv"]) == len(SCENARIOS) + 1


def test_main_reports_every_scenario_as_specified(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    by_name = {scenario.name: _snapshot(scenario) for scenario in SCENARIOS.values()}

    class Matching(FakeDocker):
        def __call__(self, arguments: Sequence[str], stdin: bytes | None = None) -> Any:
            self.snapshot = by_name[self.scenario.name] if self.scenario else {}
            return super().__call__(arguments, stdin)

    docker = Matching(_as_specified, {})
    assert _main(docker, tmp_path, "amd64") == 0
    report = json.loads((tmp_path / "amd64.json").read_text())
    assert [entry["scenario"] for entry in report] == list(SCENARIOS)
    assert all(entry["problems"] == [] for entry in report)
    assert report[-1]["accepted_connections"] == 1
    assert capsys.readouterr().out.count("as specified") == len(SCENARIOS)


def test_main_fails_on_a_deviation_and_without_the_image(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    docker = FakeDocker(lambda _: "no summary\n", {})
    assert _main(docker, tmp_path) == 1
    assert capsys.readouterr().out.count("NOT AS SPECIFIED") == len(SCENARIOS)

    def missing(arguments: Sequence[str], stdin: bytes | None = None) -> Any:
        return paths.Completed(1, "No such image")

    assert paths.main(["aarch64"], missing, lambda: NOW, lambda _: None, tmp_path) == 2
    assert "run scripts/container_check.sh" in capsys.readouterr().err


def test_a_failed_setup_or_snapshot_or_helper_is_reported() -> None:
    scenario = SCENARIOS["silent-tv"]

    def failing(word: str) -> Callable[..., Any]:
        def docker(arguments: Sequence[str], stdin: bytes | None = None) -> Any:
            if word in arguments:
                return paths.Completed(125, "it broke")
            if arguments[:1] == ["logs"]:
                return paths.Completed(0, "listening\n")
            return paths.Completed(0, "{}")

        return docker

    assert paths.run_scenario(scenario, "aarch64", failing(paths.SETUP))[1] == [
        "the setup failed: it broke"
    ]
    assert paths.run_scenario(scenario, "aarch64", failing(paths.SNAPSHOT))[1] == [
        "no snapshot: it broke"
    ]
    assert paths.run_scenario(scenario, "aarch64", failing("NET_ADMIN"))[1] == [
        "the silent television did not start: it broke"
    ]
    silent = FakeDocker(_as_specified, {})
    silent.listening = False
    sleeps: list[float] = []
    assert paths.run_scenario(scenario, "aarch64", silent, sleeps.append)[1] == [
        "the silent television did not listen in time"
    ]
    assert sum(sleeps) == pytest.approx(paths.HELPER_START_S)
    assert silent.commands[-2] == ["rm", "-f", "fg-paths-aarch64-tv"]


def test_docker_is_run_with_fixed_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    class Result:
        returncode = 3
        stdout = b"out\xff"

    def run(command: list[str], **options: Any) -> Result:
        calls.append((command, options))
        return Result()

    monkeypatch.setattr(paths.subprocess, "run", run)
    assert paths.run_docker(["volume", "ls"], b"in") == paths.Completed(3, "out�")
    command, options = calls[0]
    assert command == ["docker", "volume", "ls"]
    assert options["input"] == b"in"
    assert options["stderr"] is paths.subprocess.STDOUT
    assert options["check"] is False
    assert "shell" not in options
