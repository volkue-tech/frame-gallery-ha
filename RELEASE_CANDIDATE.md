# Release-candidate report: Frame Gallery 0.1.0.dev0

Phase 7, offline release validation (`TASKS.md`). Written by Claude on 2026-10-03, for the Phase 7 gate, where Codex reviews it and the user decides on the supervised live test (Phase 8).

**The release candidate** is commit `f42f72a` (code, tests, and scripts). This report and the status documents follow it in a documentation-only commit. The version is `0.1.0.dev0`, and `config.yaml` says `stage: experimental`.

**Verdict.** The release candidate passes every offline check that Phase 7 names, on both architectures. No finding needed a change of the app's code. It is ready for the supervised live test on the Home Assistant Green (Phase 8), once the user approves that test. It is **not** ready for a release: the prerequisites in section 6 are open, among them the release-blocking preview freshness (G5), which only the live test can prove.

## 1. Scope and conditions

- The user authorized Phase 7 on 2026-10-03, after the Phase 6 gate: offline validation with the existing local environments and container images, failure-path tests, and this report; no new features; no additional review loops without a concrete finding.
- Nothing was built, pulled, downloaded, installed, pushed, or published. Nothing contacted the Home Assistant Green, the television, a provider API, or GitHub. Every container ran with `--network none`. The one exception to a container's own empty network is the silent television of section 3.4: a helper container's network namespace, which also has no interface but loopback. Docker Desktop was still running from Phase 6; as approved then, it may contact Docker's own servers, for example to look for updates.
- **Environment.** macOS 27.0.1 on Apple silicon; Docker Engine 29.8.0 (Docker Desktop), where `amd64` runs under Rosetta; the project environment `frame_gallery/.venv` with CPython 3.12.14. The images are `frame-gallery:dev-aarch64` and `frame-gallery-checks:dev-aarch64`, and `frame-gallery:dev-amd64` and `frame-gallery-checks:dev-amd64`: built by `scripts/container_check.sh` in Phase 6 on 2026-10-02, with Alpine 3.24.1 and Python 3.14.8.

## 2. The images hold the release candidate

The images were not rebuilt. `scripts/container_check.sh <arch> --no-build` (added in this phase) proves instead, for each architecture, that they hold the release candidate:

- the app image holds exactly the release candidate's `src/frame_gallery`, file by file (90 files, SHA-256 manifests);
- the test image builds on that app image (its layers start with the app image's);
- the app image's layers start with the pinned base image's (`ghcr.io/home-assistant/base:3.24-2026.08.0@sha256:93ef…f6f5`), so the image derives from that base alone;
- the test image's copy of the build context differs from the release candidate only in documentation, tests, and scripts added or changed since Phase 6 (`DOCS.md`, `scripts/container_check.sh`, `scripts/failure_paths.py`, `scripts/image_inventory.py`, and three test files), and in no build input.

The test passes inside the images therefore ran the Phase 6 suite (4 562 tests) against the release candidate's code. The tests added since run on the host (section 3.1).

## 3. Results

### 3.1 Quality gates on the host

`frame_gallery/scripts/check.sh`, at the release candidate:

- Ruff check and format: clean (219 files).
- `mypy --strict` over `src`, `tests`, and `scripts`, for this host and as on Linux: clean (219 files).
- pytest: **4 600 passed**, 8 skipped (the Linux-only and root-only checks, which run in the container passes below); **100 % line and branch coverage** overall (8 940 statements, 1 894 branches); the architecture's 100 % gate passes (7 323 statements, 1 584 branches).

### 3.2 Timing

The suite checks every time bound in two ways. With an injected clock it checks the budget's exact arithmetic: the 120 s table (C5), `no_match` by 70 s (C11), and the watchdog at `T` + 10 s. With the real clock, on scaled-down limits, it checks what processes and sockets do: the process executor's kill timer, its stop poll, and the bounded drain after a timeout; the gateway's limits against a dripping peer; and the pairing deadline against the unchanged library. A targeted run of the ten files that hold these tests, at the release candidate: **725 passed**, 3 skipped (the Linux-only checks, which pass in both images), in 15.5 s; the slowest real-time case took 1.5 s.

Measured on the real image (3.3, 3.4):

| Bound | Limit | Measured |
| --- | --- | --- |
| Preparing a worst legal source, under the real 1 GiB limit (`aarch64`) | 15 s (§7.2, D-121) | 1.41 s at most |
| A run that finds nothing (C11) | 70 s | 0.2 s at most |
| Any run (C5) | 120 s | 7.3 s at most (a museum that cannot be resolved) |
| A television that never answers | the 40 s DELIVER phase | 5.3 s (`aarch64`), 5.7 s (`amd64`) |
| A stop request (D-130 c) | the 20 s stop timeout of `config.yaml` | the app had its 8 s to clean up; the stop took 11 s (`aarch64`) and 12 s (`amd64`) |
| 150 local inspections | — | 0.59 s, in 10 workers |

The Green is several times slower than this host; Phase 8 measures there (R-09).

### 3.3 Container checks of the existing images

`scripts/container_check.sh aarch64 --no-build --measure` and `scripts/container_check.sh amd64 --no-build`; every container with `--network none`, no host directory mounted.

| Check | `aarch64` (native) | `amd64` (Rosetta) |
| --- | --- | --- |
| The app image holds the release candidate's `src/frame_gallery` | 90 of 90 files | 90 of 90 files |
| D-130 (a) versions | Alpine 3.24.1, Python 3.14.8 | Alpine 3.24.1, Python 3.14.8 |
| Inventory | 61 Alpine packages, 11 Python distributions, 21 Pillow libraries as in `RECORD`, no wheel | the same |
| The notices list everything the image ships (H4, new) | yes | yes |
| D-130 (b) exit status | 70 came through as 70 | 70 came through as 70 |
| D-130 (c) stop request | at 3.0 s, cleaned up at 11.0 s; the stop took 11 s | at 2.6 s, cleaned up at 10.6 s; the stop took 12 s |
| D-130 (d) `SUPERVISOR_TOKEN` | visible | visible |
| Smoke run (one library file, no network) | `tv_unreachable`, exit 0 | `tv_unreachable`, exit 0 |
| D-165 user pass (uid 1000) | 4 562 passed, 5 root-only skipped | 4 562 passed, 5 root-only skipped |
| D-165 root pass | 5 of 5 passed | 5 of 5 passed |
| Worst case under the real 1 GiB `RLIMIT_AS`, as root (R-09) | 13 of 13 cases succeed, 2 runs each; heaviest: the progressive CMYK panorama in `cover`, 765.5 MiB of address space, 753.8 MiB resident, 1.34–1.38 s | not run: under Rosetta every process carries about 278 MiB more address space (D-170); the native measurement is a Phase 9 prerequisite |
| 150 local inspections | 10 workers, 0.59 s | — |

The figures repeat Phase 6's (D-170) to within about 1 MiB.

### 3.4 Failure paths through the real image

`frame_gallery/.venv/bin/python frame_gallery/scripts/failure_paths.py <arch>` (added in this phase) runs the image's own command once per scenario, as the Supervisor starts it: under s6-overlay, with the root parent, workers at 65534, and a RAM-backed `/tmp`, on `/data` and `/media` prepared in new Docker volumes. Besides the outcome, each scenario checks the exit status (0), exactly one summary line, `last_run.json`, the time bound (70 s for `no_match`, 120 s otherwise), that `/tmp/frame-gallery` is empty afterwards and no temporary file is left in `/data` or `/media` (F2), that nothing was published, that no history was written (E4), and whether the television step ran (C7).

Every scenario behaved as specified, on both architectures (`build/failure-paths/<arch>.json` holds each run's log):

| Scenario | Path | Prepared | Expected | `aarch64` | `amd64` |
| --- | --- | --- | --- | --- | --- |
| `empty-library` | no result | an empty library | `no_match`, "no usable JPEG or PNG images in /media/frame_gallery/library" (§9.3) | as specified, 0.0 s | as specified, 0.0 s |
| `portrait-only` | no result | one portrait JPEG | `no_match`, "filters too restrictive" (C2) | as specified, 0.1 s | as specified, 0.2 s |
| `broken-jpeg` | failed decode | a JPEG cut inside its scan data: the header passes the inspection, the decoding fails | `image_failed` | as specified, 0.1 s | as specified, 0.3 s |
| `damaged-history` | corrupt history | an unreadable `history.json` and no backup | moved into the quarantine with a warning; the run goes on, and without a network ends `tv_unreachable` (F5) | as specified, 0.3 s | as specified, 0.7 s |
| `damaged-history-with-backup` | corrupt history | the same, and a `.bak` that holds the only work | quarantined; the backup still excludes the work: `no_match`, "nothing new left for these filters" (F5, C3) | as specified, 0.0 s | as specified, 0.0 s |
| `ledger-uncertain` | upload ledger | an `uncertain` intent of an hour ago for the only work | excluded during its 30 days: `no_match`, "nothing new left for these filters" (E9) | as specified, 0.0 s | as specified, 0.0 s |
| `ledger-uploaded` | upload ledger | an `uploaded` entry of 400 days ago | excluded for good: `no_match`, "nothing new left for these filters" (E7, E8) | as specified, 0.0 s | as specified, 0.0 s |
| `ledger-quarantine-over` | upload ledger | an `uncertain` intent of 31 days ago | offered again; the delivery fails before `upload_started`, and its new intent is removed: `tv_unreachable`, no ledger entry left (§13.6) | as specified, 0.3 s | as specified, 0.7 s |
| `museum-unreachable` | failed download | the Art Institute as the source, without a network | `source_failed`, after at most one retry (C8) | as specified, 7.3 s | as specified, 7.1 s |
| `silent-tv` | timeout | a television that accepts the connection and never answers | the 5 s limit ends the REST check: `tv_unreachable`, no upload intent left (E3, E4) | as specified, 5.3 s, 1 connection | as specified, 5.7 s, 1 connection |

The times are the `elapsed` values of the summary lines. In the runs that reached the television, the log shows that it failed before `upload_started` (`markers=none`).

### 3.5 Failure paths in the test suite

The paths that need a television which takes the upload are covered by the suite, which ran on the host (3.1) and, in its Phase 6 form, inside both images (3.3):

| Path | Tests (selection) |
| --- | --- |
| Failed upload after `upload_started` | `test_process_television.py`: `test_a_lost_upload_is_quarantined`, `test_e7_selection_refused`, `test_e8_connection_lost_during_selection`, `test_a_stop_request_during_the_upload_kills_the_worker`, with the process-based television worker; `test_samsung_task.py` and `test_samsung_real_library.py` (the unchanged `samsungtvws` 3.0.6 against a scripted television) |
| Upload ledger | `test_state_scenarios.py`: E7, E8, E9 (three kill points), a failed promotion, an uncertain upload, `upload_started` without `uploaded`, a stop after `upload_started`; `test_sigkill.py` and `test_e9_the_runner_killed_while_its_worker_runs` (a real SIGKILL) |
| Timeouts | the process executor's kill timer and stop poll with real workers (`test_process_executor.py`), the watchdog (`test_watchdog.py`), the runner's deadlines (`test_runner.py`, `test_runner_edges.py`), the gateway's time bounds over a real socket pair (`test_transport.py`), the pairing deadline (`test_samsung_real_library.py`) |
| Failed download | `test_fetching.py` (the local copy and the remote fetcher), the runner's attempt loop (`test_runner.py`), the contract suite's 404 and 410 cases |
| Failed decode | `test_prepare_failures.py`, `test_jpeg_header.py`, the pre-scan |
| Corrupt history | `test_state_scenarios.py::test_a_corrupt_history_is_recovered_and_the_run_continues`, the store's reader tests |
| No result | the outcome rules (`test_outcomes.py`) and the runner (`test_runner.py`, C7, C11) |

### 3.6 Provenance (H5)

Checked on the release candidate's tracked files (251) and on each of the 72 commits of `main` up to it:

- The names of the excluded predecessor projects, and the other identifiers `LEGAL_BOUNDARIES.md` and `AGENTS.md` name, appear only in those two files and in `CLAUDE.md`, which state the boundary, and in every one of the 72 commits nowhere else.
- Each of these commits is authored and committed by Alexander Wilke `<volkue@gmail.com>`. No file was ever deleted from `main`.
- The only files with binary content are `icon.png` and `logo.png`, which `scripts/app_images.py` draws; a test redraws them and compares every pixel.
- No source, test, or script carries a third-party copyright or licence header; the only hits for "Copyright" are a museum's rights status in synthesized test records. Nothing is vendored: every third-party package is installed unmodified from PyPI.
- The museum fixtures are synthesized (`tests/support/museums.py`); nothing was recorded from a live API.
- The app images derive from the pinned Home Assistant base alone (section 2). The local Docker store also holds images of unrelated work; they were neither inspected nor used.

### 3.7 Licences and notices (H4, H6)

- `scripts/image_inventory.py --notices` (added in this phase, now part of `container_check.sh`) holds `THIRD_PARTY_NOTICES.md` to the image's own inventory: all 61 Alpine packages with their versions and apk's licence fields, all 11 Python distributions with their versions, all 21 libraries in `pillow.libs`, and the components outside apk are listed, on both architectures. A test also holds the notices to `requirements/image-runtime.txt`, without the image.
- The project licence, Apache-2.0, is approved (D-102); it covers the project's own code only. The `LICENSE` file is added when publication is prepared (Phase 9). No file of the release candidate claims another licence for the project's code.
- The image is not free of GPL components, and the documents say so: `samsungtvws` (`LGPL-3.0`), Pillow's fribidi-shim (`LGPL-2.1-or-later`), and Alpine packages under the GPL (BusyBox, bash, readline, gdbm, and others).
- Still open, for the qualified licence review (a release prerequisite): the licence texts and the corresponding sources (D-135); the licences of s6-overlay, tempio with its 11 Go modules, and bashio, which the image does not carry (R-33); the form of libmd's "Public Domain" part; AOMedia's patent licence for aom; libjpeg-turbo's zlib text; GCC's runtime-library exception.

## 4. Acceptance items after Phase 7

"Offline" means verified by the test suite or by the image checks above; "live" means it needs the supervised test or the release.

| Items | After Phase 7 | Still needed |
| --- | --- | --- |
| A1, A2, A3 | — | live: the public repository and published images (Phase 9); a discovery and installation on the Green (Phase 8) |
| A4 | offline: both images built from the same sources and checked (D-170, section 2) | the native `amd64` measurement (Phase 9) |
| A5, A6 | offline: the documentation and the generated translations, tested against the app's parser | live review (Phase 8) |
| B1 | offline: `tv_host` has no default, and the app checks it again | live (Phase 8) |
| B2 to B8 | offline: unit, contract, and integration tests | — |
| C1 to C11 | offline; C2, C3, C7, C8, and C11 also through the real image (3.4) | C9 and C10 against the real museums (Phase 8) |
| D1 to D8 | offline; D7 also under the real memory limit (3.3) | — |
| E1, E2 | offline: the unchanged library against a scripted television | live (Phase 8) |
| E3, E4 | offline, and through the real image: a silent television ends within its bounds, and failed deliveries leave no history and no upload intent (3.4) | live (Phase 8) |
| E5 to E10 | offline: integration tests with the process-based television worker and a real SIGKILL | the normal path live (Phase 8) |
| F1, F3, F6, F7 | offline | F1 live (Phase 8) |
| F2, F5 | offline, and through the real image (3.4) | — |
| F4 | offline | restarts live (Phase 8); an upgrade with the first release |
| G1 | offline: the draft card, script, timer, and automation in `DOCS.md`, tested | the entity IDs (Phase 8) and the public slug (Phase 9) |
| G2, G3, G4 | G4's time bounds offline | live (Phase 8) |
| **G5** | — | **release-blocking:** the preview freshness, proven in repeated live tests (Phase 8) |
| G6 | offline: the documentation, tested | live (Phase 8) |
| H1 | offline: 100 % line and branch coverage | — |
| H2 | offline: the socket guard; every container without a network | — |
| H3 | offline: the redaction tests, in the parent and the workers | — |
| H4 | offline: the notices list everything the image ships (3.7) | the licence texts and the corresponding sources (Phase 9) |
| H5 | offline: the provenance review (3.6) | — |
| H6 | Apache-2.0 approved (D-102) | the `LICENSE` file before publication (Phase 9) |
| H7 | no live run so far | the user's approval at this gate |

## 5. Known limitations

These are documented for users in `frame_gallery/DOCS.md`:

- very old works can come back once they leave the 20 000-entry history (R-29);
- an uncertain upload keeps its work out for 30 days (R-24);
- Art Institute images are enlarged up to about 2.3 times (R-19);
- the Art Institute offers only the period filter, Cleveland department and period, and no source a style or colour filter;
- TVs whose art API reports 0.97 are refused (D-162);
- the connection to the TV is not certificate-checked until the pinning decision (R-03);
- another client's upload at the same moment could be selected instead (R-30);
- old artworks stay on the TV;
- the AppArmor profile runs in complain mode until it is enforced in Phase 9.

Not in the user documentation, because users never meet it: under emulation, a failed allocation inside the JPEG decoder is reported as `decode`, not `memory` (R-09, D-170).

## 6. Open before a release

| Prerequisite | When |
| --- | --- |
| **Preview freshness** (G5, release-blocking): one refresh mechanism, proven in repeated live tests (D-140, R-07) | Phase 8 |
| The live checks of Phase 8: installation (Q-21), connectivity without `host_network` (Q-16), pairing, upload, and selection against the real TV, the art API version (D-162), the TV's certificate for the pinning decision (R-03), the entity IDs of the dashboard, a backup without `tv/`, the measurement on the Green (R-09), and the AppArmor complain log | Phase 8 |
| The native `amd64` worst-case measurement under the real `RLIMIT_AS`, before an `amd64` version is published | Phase 9 at the latest |
| The qualified licence review (D-135), with R-33 and the open items of 3.7 | Phase 9 |
| The `LICENSE` file, and notices with the full licence texts and the corresponding sources of the copyleft components | Phase 9 |
| The AppArmor profile enforced, the per-worker child profiles (R-31), and the isolation verified in an approved live re-check | Phase 9 |
| The final name (D-101) and the repository URL (Q-13), which also replaces the contact in the User-Agent (D-119) | Phase 9 |
| CI on Python 3.12 to 3.14, signed multi-architecture images, the one-click link, release notes, and `stage` raised only after Phase 8 | Phase 9 |

## 7. Notes for Phase 8

- The live test needs the user's explicit approval (H7). It is also the first live request to a museum, and the first time the project contact is sent (Q-22).
- Until images are published, the Supervisor builds the app on the Green from the Dockerfile. That build needs the base image, Alpine's package source, and PyPI, and it fails once Alpine replaces `python3` 3.14.8-r0 (R-32). Whether the pin still resolves can only be checked with network access, which needs its own approval; the install route (Q-21) decides whether it matters.
- If the development installation is removed after the test, Phase 8 confirms that its `/data` goes with it (D-172).

## 8. Observations

- **A silent television ends after one attempt.** In the scenario `silent-tv`, the television accepts the TCP connection and never answers. The worker's REST check (`supported()`) gives up after 5 s, and the run ends as `tv_unreachable` in 5.3 s, without a second connection. That is within the policy (§7.4, D-115: at most one television reconnect, which the worker uses for opening the art channel). The wording of D-162 point 4 ("any other failure before `connected` is retried once") can be read to include the REST check; the code and the task's own documentation do not retry it. A clarification of D-162 is proposed (D-173); no code change is proposed.
- **A museum that cannot be resolved** ends as `source_failed` after 7.1 to 7.3 s, which fits two name resolutions of at most 3 s each and one retry after 1 s (D-147, D-115); the log names the failed resolution.
- **The test copy in the images is the Phase 6 one.** The tests added since (the failure-path driver, the notices check, the "Starting over" text) ran on the host only; the next image build includes them.

## 9. How to reproduce

From `frame_gallery/`, with the images of Phase 6 present and Docker running:

```text
scripts/check.sh
scripts/container_check.sh aarch64 --no-build --measure
scripts/container_check.sh amd64 --no-build
.venv/bin/python scripts/failure_paths.py aarch64
.venv/bin/python scripts/failure_paths.py amd64
```

The outputs go to `build/container-checks/<arch>/` and `build/failure-paths/` beside the app directory (both git-ignored).
