"""Run the app image through its failure paths, offline (Phase 7).

    .venv/bin/python scripts/failure_paths.py aarch64|amd64

Each scenario prepares the app's ``/data`` and ``/media`` in new Docker
volumes, runs the image's own command once, as the Supervisor starts it (the
base image's s6-overlay init, the root parent, workers at 65534, a RAM-backed
``/tmp``), and checks what the specification says about that path: the
outcome and hint of the summary line and of ``last_run.json``, the exit
status, whether the television step ran, the upload ledger, the history and
its quarantine, that nothing was published, and that no temporary file is
left in ``/data``, ``/media``, or ``/tmp`` (ACCEPTANCE_TESTS C5, C7, C11, E4,
F2, F5).

The paths are those of the Phase 7 task that a run reaches without a
network: no result, a timeout, corrupt history, a failed download, a failed
decode, a delivery that fails before the upload, and the upload ledger. A
failed upload after ``upload_started`` needs a television that takes the
upload; the test suite covers it (E7-E10, and the unchanged library against
a scripted television).

Every container runs without a network (``--network none``), and no host
directory is mounted: the inputs go in through stdin. The silent television
is a listener on a second loopback address that a helper container adds in
its own network namespace (``NET_ADMIN``, for that container only); the app's
container joins that namespace, which has no other interface, so nothing
leaves this machine.

The images must exist (``scripts/container_check.sh`` builds them). The
results go to ``../build/failure-paths/<arch>.json`` (git-ignored). The exit
status is 1 if any scenario did not behave as the specification says.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import random
import re
import subprocess
import sys
import tarfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from frame_gallery.app.outcomes import Hint, Outcome
from frame_gallery.fingerprint import fingerprint_bytes
from frame_gallery.store.atomic import BACKUP_SUFFIX, QUARANTINE_DIRECTORY
from frame_gallery.store.history import HISTORY_FILE, HistoryEntry, history_document
from frame_gallery.store.records import LAST_RUN_FILE, STATE_DIRECTORY
from frame_gallery.store.upload_ledger import (
    LEDGER_FILE,
    QUARANTINE_PERIOD,
    LedgerEntry,
    LedgerState,
    ledger_document,
)

PROJECT: Final = Path(__file__).resolve().parents[1]
RESULTS: Final = PROJECT.parent / "build" / "failure-paths"
PLATFORMS: Final = {"aarch64": "linux/arm64", "amd64": "linux/amd64"}
TV_HOST: Final = "10.0.0.5"
"""A private address (D-125) that no container network here uses."""
PYTHON: Final = "/opt/frame-gallery/bin/python"
STATE: Final = f"/data/{STATE_DIRECTORY}"
LIBRARY: Final = "media/frame_gallery/library"
PREVIEW: Final = "/media/frame_gallery/preview"
NO_MATCH_BOUND_S: Final = 70.0
"""C11: a run that finds nothing ends within 70 s."""
RUN_BOUND_S: Final = 120.0
"""C5: the total deadline (D-114)."""
HELPER_START_S: Final = 30.0
TELEVISION_STEP: Final = "frame_gallery.run: television"
NO_MARKER: Final = "markers=none"

# The image's own command (the Dockerfile's CMD), then the number of entries
# that the run left in its workspace root (F2). /tmp is a RAM-backed tmpfs.
RUN_APP: Final = (
    f"with-contenv {PYTHON} -I -B -m frame_gallery; status=$?; "
    'echo "tmp-left=$(ls -A /tmp/frame-gallery 2>/dev/null | wc -l)"; exit $status'
)
# The "tar" filter keeps the archive's modes and its owner, root.
SETUP: Final = (
    "import sys, tarfile\n"
    "with tarfile.open(fileobj=sys.stdin.buffer, mode='r|') as archive:\n"
    "    archive.extractall('/', filter='tar')\n"
)
SNAPSHOT: Final = """
import hashlib, json, os, stat
found = {}
for top in ("/data", "/media"):
    for base, dirs, names in os.walk(top):
        for name in dirs + names:
            path = os.path.join(base, name)
            info = os.lstat(path)
            entry = {"mode": stat.S_IMODE(info.st_mode), "directory": stat.S_ISDIR(info.st_mode)}
            if stat.S_ISREG(info.st_mode):
                with open(path, "rb") as handle:
                    content = handle.read()
                entry["sha256"] = hashlib.sha256(content).hexdigest()
                if name.endswith(".json") and "/quarantine/" not in path:
                    try:
                        entry["json"] = json.loads(content)
                    except ValueError:
                        entry["json"] = None
            found[path] = entry
print(json.dumps(found, sort_keys=True))
"""
# The silent television: it accepts every connection on the TV's two ports
# and never sends a byte.
SILENT_TV: Final = f"""
import select, socket
servers = []
for port in (8001, 8002):
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("{TV_HOST}", port))
    server.listen(8)
    servers.append(server)
print("listening", flush=True)
held = []
while True:
    for server in select.select(servers, [], [])[0]:
        connection, _ = server.accept()
        held.append(connection)
        print("accepted", server.getsockname()[1], flush=True)
"""
SUMMARY: Final = re.compile(
    r"outcome=(?P<outcome>[a-z_]+) exit=(?P<exit>\d+) elapsed=(?P<elapsed>\d+\.\d)"
    r"(?: ignored_filters=\S+)?(?: hint=\"(?P<hint>[^\"]*)\")?$",
    re.MULTILINE,
)
TMP_LEFT: Final = re.compile(r"^tmp-left=\s*(\d+)\s*$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class Completed:
    status: int
    output: str


Docker = Callable[[Sequence[str], bytes | None], Completed]


def run_docker(arguments: Sequence[str], stdin: bytes | None = None) -> Completed:
    """One ``docker`` command; its stdout and stderr together, as text."""
    command = ["docker", *arguments]
    result = subprocess.run(  # noqa: S603 - fixed arguments, no shell
        command, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
    )
    return Completed(result.returncode, result.stdout.decode(errors="replace"))


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    path: str
    """The Phase 7 path that the scenario exercises."""
    outcome: Outcome
    hint: Hint | None = None
    source: str = "local_media"
    library: Mapping[str, bytes] = field(default_factory=dict)
    state: Mapping[str, bytes] = field(default_factory=dict)
    """Files for ``/data/state``, by name."""
    reaches_tv: bool = False
    """The run commits an upload intent and fails before ``upload_started``."""
    quarantined: str | None = None
    """The state file that the run must move into the quarantine."""
    silent_tv: bool = False


# --- the inputs ------------------------------------------------------------------


def _jpeg(size: tuple[int, int], seed: int, *, noise: bool = False) -> bytes:
    """A generated JPEG; with ``noise``, its scan data is large."""
    rng = random.Random(seed)  # noqa: S311 - test pixels, not a secret
    if noise:
        image = Image.frombytes("RGB", size, rng.randbytes(size[0] * size[1] * 3))
    else:
        image = Image.new("RGB", size, (rng.randrange(256), rng.randrange(256), rng.randrange(256)))
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=90)
    return buffer.getvalue()


def local_id(data: bytes) -> str:
    """The local library's identifier of a file (D-118)."""
    return f"local:fp:{fingerprint_bytes(data)}"


def _document(value: Mapping[str, object]) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode()


def _history(*entries: HistoryEntry) -> bytes:
    return _document(history_document(entries))


def _ledger(*entries: LedgerEntry) -> bytes:
    return _document(ledger_document(entries))


def scenarios(now: datetime) -> tuple[Scenario, ...]:
    """The scenarios, in the order they run."""
    landscape = _jpeg((1920, 1080), 1)
    work = local_id(landscape)
    broken = _jpeg((1920, 1080), 2, noise=True)
    broken = broken[: len(broken) // 2]  # cut inside the scan data, after the header
    damaged = b'{"format": "frame-gallery-history", "version": 1, "entries": [{'
    hour_ago = now - timedelta(hours=1)
    quarantine_over = now - QUARANTINE_PERIOD - timedelta(days=1)
    harbour = {"harbour.jpg": landscape}
    return (
        Scenario("empty-library", "no result", Outcome.NO_MATCH, Hint.LIBRARY_EMPTY),
        Scenario(
            "portrait-only",
            "no result",
            Outcome.NO_MATCH,
            Hint.FILTERS_TOO_RESTRICTIVE,
            library={"tower.jpg": _jpeg((1080, 1920), 3)},
        ),
        Scenario(
            "broken-jpeg", "failed decode", Outcome.IMAGE_FAILED, library={"broken.jpg": broken}
        ),
        Scenario(
            "damaged-history",
            "corrupt history",
            Outcome.TV_UNREACHABLE,
            library=harbour,
            state={HISTORY_FILE: damaged},
            reaches_tv=True,
            quarantined=HISTORY_FILE,
        ),
        Scenario(
            "damaged-history-with-backup",
            "corrupt history",
            Outcome.NO_MATCH,
            Hint.NOTHING_NEW,
            library=harbour,
            state={
                HISTORY_FILE: damaged,
                HISTORY_FILE + BACKUP_SUFFIX: _history(HistoryEntry(work, hour_ago)),
            },
            quarantined=HISTORY_FILE,
        ),
        Scenario(
            "ledger-uncertain",
            "upload ledger",
            Outcome.NO_MATCH,
            Hint.NOTHING_NEW,
            library=harbour,
            state={LEDGER_FILE: _ledger(LedgerEntry(work, LedgerState.UNCERTAIN, hour_ago))},
        ),
        Scenario(
            "ledger-uploaded",
            "upload ledger",
            Outcome.NO_MATCH,
            Hint.NOTHING_NEW,
            library=harbour,
            state={
                LEDGER_FILE: _ledger(
                    LedgerEntry(work, LedgerState.UPLOADED, now - timedelta(days=400))
                )
            },
        ),
        Scenario(
            "ledger-quarantine-over",
            "upload ledger",
            Outcome.TV_UNREACHABLE,
            library=harbour,
            state={LEDGER_FILE: _ledger(LedgerEntry(work, LedgerState.UNCERTAIN, quarantine_over))},
            reaches_tv=True,
        ),
        Scenario(
            "museum-unreachable",
            "failed download",
            Outcome.SOURCE_FAILED,
            source="art_institute_chicago",
        ),
        Scenario(
            "silent-tv",
            "timeout",
            Outcome.TV_UNREACHABLE,
            library=harbour,
            reaches_tv=True,
            silent_tv=True,
        ),
    )


def setup_archive(scenario: Scenario) -> bytes:
    """The scenario's ``/data`` and ``/media`` as a tar stream (root, exact modes)."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:

        def add(name: str, mode: int, content: bytes | None = None) -> None:
            info = tarfile.TarInfo(name)
            info.mode = mode
            if content is None:
                info.type = tarfile.DIRTYPE
                archive.addfile(info)
            else:
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))

        options = {"tv_host": TV_HOST, "source": scenario.source}
        add("data/options.json", 0o600, _document(options))
        if scenario.state:
            add(STATE.lstrip("/"), 0o700)
            for name, content in scenario.state.items():
                add(f"{STATE.lstrip('/')}/{name}", 0o600, content)
        if scenario.library:
            add("media/frame_gallery", 0o755)
            add(LIBRARY, 0o755)
            for name, content in scenario.library.items():
                add(f"{LIBRARY}/{name}", 0o644, content)
    return buffer.getvalue()


# --- the checks ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Observed:
    status: int
    output: str
    snapshot: Mapping[str, Mapping[str, object]]
    accepted: int | None = None
    """Connections the silent television accepted, if it ran."""


def _ids(document: object) -> set[object]:
    """The identifiers in a ledger or history document."""
    entries = document.get("entries") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        return set()
    return {entry.get("id") for entry in entries if isinstance(entry, dict)}


def _run_problems(scenario: Scenario, observed: Observed) -> list[str]:
    """The summary line, the exit status, the run record, /tmp, and the TV step."""
    summaries = list(SUMMARY.finditer(observed.output))
    if len(summaries) != 1:
        return [f"{len(summaries)} summary lines, expected exactly one"]
    summary = summaries[0]
    problems: list[str] = []
    hint = scenario.hint.value if scenario.hint is not None else None
    if summary["outcome"] != scenario.outcome.value or summary["hint"] != hint:
        problems.append(f"expected outcome={scenario.outcome.value} with hint {hint!r}")
    if summary["exit"] != "0" or observed.status != 0:
        problems.append(f"exit {summary['exit']} (container {observed.status}), expected 0")
    bound = NO_MATCH_BOUND_S if scenario.outcome is Outcome.NO_MATCH else RUN_BOUND_S
    if float(summary["elapsed"]) > bound:
        problems.append(f"elapsed {summary['elapsed']} s, more than {bound:.0f} s (C5, C11)")
    left = TMP_LEFT.search(observed.output)
    if left is None or left[1] != "0":
        problems.append("the workspace root in /tmp is not empty after the run (F2)")
    last_run = observed.snapshot.get(f"{STATE}/{LAST_RUN_FILE}", {}).get("json")
    if not isinstance(last_run, dict):
        problems.append("no readable last_run.json")
    elif (last_run.get("outcome"), last_run.get("hint")) != (scenario.outcome.value, hint):
        problems.append(f"last_run.json says {last_run.get('outcome')} / {last_run.get('hint')!r}")
    if scenario.reaches_tv:
        if NO_MARKER not in observed.output:
            problems.append("the television step did not end before upload_started")
    elif TELEVISION_STEP in observed.output:
        problems.append("the television step ran, although nothing was deliverable (C7)")
    if scenario.silent_tv and not observed.accepted:
        problems.append("the silent television accepted no connection")
    return problems


def _state_problems(scenario: Scenario, snapshot: Mapping[str, Mapping[str, object]]) -> list[str]:
    """What the run left in /data and /media."""
    problems: list[str] = []
    for path, entry in snapshot.items():
        if ".tmp-" in path.rsplit("/", 1)[-1]:
            problems.append(f"a temporary file is left: {path} (F2)")
        if path.startswith(f"{PREVIEW}/") and not entry.get("directory"):
            problems.append(f"a preview was published: {path}")
    history = f"{STATE}/{HISTORY_FILE}"
    if history in snapshot and HISTORY_FILE not in scenario.state:
        problems.append("a history was written, although nothing was delivered (E4)")
    for name, content in scenario.state.items():
        path = f"{STATE}/{name}"
        digest = hashlib.sha256(content).hexdigest()
        if name == scenario.quarantined:
            moved = [
                entry.get("sha256")
                for found, entry in snapshot.items()
                if found.startswith(f"{STATE}/{QUARANTINE_DIRECTORY}/") and found.endswith(name)
            ]
            if path in snapshot:
                problems.append(f"the damaged {name} is still in place, or was written again")
            if moved != [digest]:
                problems.append(f"the quarantine does not hold the damaged {name} (F5)")
        elif name != LEDGER_FILE or not scenario.reaches_tv:
            if snapshot.get(path, {}).get("sha256") != digest:
                problems.append(f"{name} changed")
    if scenario.reaches_tv:
        work = local_id(next(iter(scenario.library.values())))
        if work in _ids(snapshot.get(f"{STATE}/{LEDGER_FILE}", {}).get("json")):
            problems.append("the ledger still names the work after a delivery that failed (E4)")
    return problems


def evaluate(scenario: Scenario, observed: Observed) -> list[str]:
    """What the run did against what the specification says (empty: as specified)."""
    return _run_problems(scenario, observed) + _state_problems(scenario, observed.snapshot)


# --- the runs --------------------------------------------------------------------


def _run(platform: str, network: str) -> list[str]:
    return ["run", "--rm", "--platform", platform, "--network", network]


def _start_silent_tv(
    docker: Docker, helper: str, platform: str, image: str, sleep: Callable[[float], None]
) -> str | None:
    """Start the helper; ``None`` once it listens, otherwise what went wrong."""
    detached = ["run", "-d", "--name", helper, "--platform", platform, "--network", "none"]
    command = f'ip address add {TV_HOST}/32 dev lo && exec {PYTHON} -I -c "$1"'
    shell = ["--cap-add", "NET_ADMIN", "--entrypoint", "/bin/sh", image, "-c", command]
    started = docker([*detached, *shell, "silent-tv", SILENT_TV], None)
    if started.status != 0:
        return f"the silent television did not start: {started.output.strip()[-200:]}"
    for _ in range(int(HELPER_START_S / 0.25)):
        if "listening" in docker(["logs", helper], None).output:
            return None
        sleep(0.25)
    return "the silent television did not listen in time"


def run_scenario(
    scenario: Scenario, arch: str, docker: Docker, sleep: Callable[[float], None] = time.sleep
) -> tuple[Observed | None, list[str]]:
    """Run one scenario in new volumes, which it removes again."""
    platform = PLATFORMS[arch]
    image = f"frame-gallery:dev-{arch}"
    data, media = f"fg-paths-{arch}-data", f"fg-paths-{arch}-media"
    helper = f"fg-paths-{arch}-tv"
    docker(["rm", "-f", helper], None)
    docker(["volume", "rm", "-f", data, media], None)
    for volume in (data, media):
        docker(["volume", "create", volume], None)
    mounts = ["-v", f"{data}:/data", "-v", f"{media}:/media"]
    readonly = ["-v", f"{data}:/data:ro", "-v", f"{media}:/media:ro"]
    python = ["--entrypoint", PYTHON, image, "-I", "-c"]
    try:
        setup = docker(
            [*_run(platform, "none"), "-i", *mounts, *python, SETUP], setup_archive(scenario)
        )
        if setup.status != 0:
            return None, [f"the setup failed: {setup.output.strip()[-200:]}"]
        network = "none"
        if scenario.silent_tv:
            failure = _start_silent_tv(docker, helper, platform, image, sleep)
            if failure is not None:
                return None, [failure]
            network = f"container:{helper}"
        tmpfs = ["--tmpfs", "/tmp"]  # noqa: S108 - the container's RAM-backed /tmp (tmpfs: true)
        run = docker(
            [*_run(platform, network), *tmpfs, *mounts, image, "/bin/sh", "-c", RUN_APP], None
        )
        accepted = None
        if scenario.silent_tv:
            accepted = docker(["logs", helper], None).output.count("accepted ")
        snapshot = docker([*_run(platform, "none"), *readonly, *python, SNAPSHOT], None)
        if snapshot.status != 0:
            return None, [f"no snapshot: {snapshot.output.strip()[-200:]}"]
        observed = Observed(run.status, run.output, json.loads(snapshot.output), accepted)
        return observed, evaluate(scenario, observed)
    finally:
        if scenario.silent_tv:
            docker(["rm", "-f", helper], None)
        docker(["volume", "rm", "-f", data, media], None)


def main(
    argv: Sequence[str] | None = None,
    docker: Docker = run_docker,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    sleep: Callable[[float], None] = time.sleep,
    results: Path = RESULTS,
) -> int:
    parser = argparse.ArgumentParser(description="Run the app image through its failure paths.")
    parser.add_argument("arch", choices=sorted(PLATFORMS))
    arch = parser.parse_args(argv).arch
    if docker(["image", "inspect", f"frame-gallery:dev-{arch}"], None).status != 0:
        sys.stderr.write(f"no image frame-gallery:dev-{arch}: run scripts/container_check.sh\n")
        return 2
    report: list[dict[str, object]] = []
    for scenario in scenarios(now()):
        observed, problems = run_scenario(scenario, arch, docker, sleep)
        found = SUMMARY.search(observed.output) if observed is not None else None
        line = found[0] if found is not None else "no summary line"
        verdict = "as specified" if not problems else "NOT AS SPECIFIED"
        sys.stdout.write(f"{scenario.name:<28} {scenario.path:<16} {verdict}: {line}\n")
        for problem in problems:
            sys.stdout.write(f"    {problem}\n")
        report.append(
            {
                "scenario": scenario.name,
                "path": scenario.path,
                "expected": {
                    "outcome": scenario.outcome.value,
                    "hint": scenario.hint.value if scenario.hint is not None else None,
                },
                "summary": line,
                "accepted_connections": observed.accepted if observed is not None else None,
                "problems": problems,
                "output": observed.output if observed is not None else None,
            }
        )
    results.mkdir(parents=True, exist_ok=True)
    (results / f"{arch}.json").write_text(json.dumps(report, indent=2) + "\n")
    return 1 if any(entry["problems"] for entry in report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
