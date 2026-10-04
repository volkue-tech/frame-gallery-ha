# Development

All commands run from this directory (`frame_gallery/`). The environment is managed with `uv` 0.12.19 (D-128), pinned in `pyproject.toml` (`required-version`).

## Environment

`uv` never downloads Python interpreters for this project (`python-downloads = "never"`), so a local CPython 3.12, 3.13, or 3.14 must be available. Point `UV_PYTHON` at it if it is not on `PATH`.

```bash
uv sync --locked
```

The lock (`uv.lock`) pins every package with hashes. It covers macOS (development) and Linux (the container) only.

## Quality gates (§20.4)

```bash
scripts/check.sh
```

The script runs, and fails on the first failure:

1. `ruff check` and `ruff format --check`;
2. `mypy` in strict mode, over `src` and `tests`, twice: for this host, and as on Linux (`mypy --platform linux`, the container's platform; D-163);
3. `pytest` with branch coverage: at least 90 % overall, and 100 % of lines and branches for the modules the architecture requires (§20.4): `budget`, `ha` (the helper reader), `net` (the whole package, including the real transport), `selection`, `store` (including the upload ledger), `isolation` (including the process executor, the worker bootstrap, and the worker's entry), `providers`, `tv` (the Samsung adapter, the television worker task, and the pairing-token store), the outcome classification and the runner, and the imaging worker tasks with their header pre-scan and JPEG header parser.

`mypy` runs in strict mode over `src` and `tests`, with no per-module relaxations. The worker's own code (`isolation/bootstrap.py`, `isolation/worker_main.py`, `isolation/process.py`, `tv/samsung_task.py`) may not exclude any line from coverage: every branch is reached in-process through injected seams, and real workers show the behaviour.

Tests never use the network (acceptance item `H2`). For the whole session, collection included, `tests/conftest.py` installs the guard of `tests/support/h2.py`, which makes these raise: `connect`, `connect_ex`, `sendto`, and `sendmsg` on `socket.socket`; `socket.create_connection`; and `getaddrinfo`, `gethostbyname`, `gethostbyname_ex`, `gethostbyaddr`, and `getnameinfo` on both `socket` and `_socket`. Every task a test runs in a worker process (`tests/support/worker_tasks.py`) installs the same guard first; `tests/support/h2.py` lists the processes that are not guarded and why.

The architecture boundary test enforces the import rules of D-107, D-145, D-147, D-160, D-162, and D-163, and proves with self-tests that each of its detectors fires:

- `net/transport.py` is the only module that may import `ssl`, `http.client`, `urllib3`, and `certifi`, and only the entry point may import it; the gateway and the adapters are tested against the fakes in `tests/support/net.py`.
- `socket` is allowed there and in `tv/samsung_task.py` (the television worker's connect guard, D-162).
- `samsungtvws`, `websocket`, and `requests` only in `tv/samsung_task.py`, which the parent reaches only through the executor's lazy import.
- `subprocess` and `select` only in `isolation/process.py`, which only the entry point may import; `ctypes` only in `isolation/bootstrap.py`; the worker's modules (`isolation/bootstrap.py`, `isolation/worker_main.py`) only in the worker (D-163).

Tests never use the real project contact in a header: they pass a placeholder identity (D-119).

## Worker processes

`tests/unit/isolation/` and `tests/integration/test_process_television.py` start real worker processes through the process executor (`tests/support/processes.py`). Their test tasks reach the worker through an extra path, which a worker that drops privileges refuses, so these tests need a non-root parent; a root run skips them. `tests/unit/isolation/test_root_isolation.py` holds the checks that need root (the drop to 65534, the hand-over of the workspace), and some checks need Linux (`RLIMIT_AS`, threads under `RLIMIT_NPROC` 0, the parent-death signal). On a development host these are skipped. A container run names its mode, so that a skip of what the mode promises fails instead (D-165):

```bash
FRAME_GALLERY_REQUIRE_ISOLATION=user .venv/bin/pytest   # as a non-root user, on Linux
FRAME_GALLERY_REQUIRE_ISOLATION=root .venv/bin/pytest tests/unit/isolation/test_root_isolation.py   # as root, on Linux
```

`scripts/measure_prepare.py` measures the worst-case preparation time and peak memory in real workers (R-09), and with `--inspections N` the cost of N local-media inspections, in batches of up to 16 files per worker. It uses no network; as root, its workers drop to 65534, and only on Linux is `RLIMIT_AS` enforced. On Linux each worker reports its own peaks from `/proc/self/status` (`VmHWM`, `VmPeak`).

The state tests run the runner over the real store in temporary directories (`tests/support/persistent.py`). `tests/integration/test_sigkill.py` also starts child processes of the same interpreter that kill themselves with SIGKILL at chosen points, so the next run can be checked against exactly what a killed process leaves behind (D-159). They need a POSIX system and nothing outside the test's temporary directory.

## Filter vocabulary

`VOCABULARY.md` documents the shipped vocabulary (keys, labels, aliases, and the values the adapters send) and the capability matrix. `tests/unit/config/test_builtin_vocabulary.py` fails if the document and the code drift apart, so change both together.

## Runtime requirements

`requirements/runtime.txt` is exported from the lock, with hashes, as the record of the runtime packages for any platform:

```bash
uv export --locked --no-dev --no-emit-project --format requirements-txt -o requirements/runtime.txt
```

The container installs `requirements/image-runtime.txt` instead, and its test stage `requirements/image-test.txt`. `scripts/image_requirements.py` writes both from the lock: for each package, the one wheel that pip installs for CPython 3.14 on `musllinux_1_2` (`aarch64` and `x86_64`), with its hash (D-167). A test fails when they differ from the lock:

```bash
.venv/bin/python scripts/image_requirements.py           # write both files
.venv/bin/python scripts/image_requirements.py --check   # exit 1 if they differ
```

Regenerate all three whenever `uv.lock` changes. Pillow and `samsungtvws` are upgraded only in dedicated commits, with the full test suite and an updated inventory (D-128).

## Corresponding-source packages and library replacement

The root `SOURCE_AND_REBUILD.md` documents the supplied source archive layout,
upstream build inputs, library replacement and developer local installation.
From a clean committed checkout with the retained public archives, assemble a
new uniquely named offline source package:

```bash
.venv/bin/python scripts/source_bundle.py --output-name frame-gallery-sources-candidate.tar
```

The script checks all fixed manifests, bounds and SHA256s, takes the clean Git
snapshot, refuses to overwrite output, and verifies every packed member. It
executes/extracts no upstream source and makes no network request. The result
remains in ignored `build/source-packages/`; it is not automatically published or
declared legally cleared. Match its commit to the final image's build commit.

## App files

`config.yaml` and `translations/en.yaml` are generated by `scripts/app_config.py` from the app's own option definitions and vocabulary. `scripts/app_images.py` copies the approved transparent `assets/brand/frame-gallery-mark.png` master byte-for-byte to `icon.png` and `logo.png`; the brand folder records its independent AI-assisted provenance and prompts. Tests fail when an exported file differs from its source, including alpha. Change the authoritative definition/master and regenerate; do not edit the output files by hand.

## Installing a local development copy

*The supervised Phase 8 installation on Green and local/Cleveland TV deliveries succeeded on 2026-10-03; Chicago returned HTTP 403 and dashboard freshness remains unverified (`PHASE8_REPORT.md` at the repository root).* Until images are published (Phase 9), Home Assistant builds the app on the device from this folder's `Dockerfile`; the build needs the network sources named below, and it produces the last stage, `runtime` (the app image).

1. Copy this folder, without `.venv` and caches, into the local apps folder of Home Assistant (`/addons`), for example through a file-share app, so that `/addons/frame_gallery/config.yaml` exists.
2. In **Settings → Apps → App store → ⋮ → Check for updates**, reload the store; the app appears under the local apps, with the ID `local_frame_gallery`.
3. Install it, then continue with `DOCS.md` (*Installation*, step 3).

On the tested Terminal & SSH version, the local app directory is
`/local_apps`, not `/addons`. Verify the available mount before copying;
creating an unmounted `/addons` directory would not install an app. The live
test uses the separate development name/slug **Frame Gallery (Test)** /
`frame_gallery_dev` and its corresponding AppArmor profile name, giving
`local_frame_gallery_dev`; it does not replace another app.

When transferring a tar archive from macOS, suppress AppleDouble metadata:
use `COPYFILE_DISABLE=1 tar --exclude='._*' ...`, inspect the archive listing,
and verify its SHA256 before extraction. Otherwise tar can add `._*.py`
files that `compileall` rejects as Python containing NUL bytes. Do not copy
`.venv`, caches, credentials, or unrelated files.

## The container image (Phase 6)

The committed `license_bundle/` mechanically mirrors the public repository's
`LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md` and `LICENSES/`; it contains no
source archives, runtime data or credentials. After editing these originals,
run `.venv/bin/python scripts/license_bundle.py` and commit the regenerated
payload. `scripts/check.sh` checks it without changing files. Supervisor can
build directly from the committed context, without a local pre-build script.
The image keeps the original bytes in `/usr/share/frame-gallery/licenses/`;
container validation checks every file against the checkout manifest as UID
65534. This distribution step does not complete the separate corresponding-source
and licence-applicability release gates.

The image is built with Docker Buildx; on this host, Docker Desktop provides it, and `amd64` runs under Rosetta. The build reaches only the pinned base image (`ghcr.io`), the Alpine package source for `python3`, and PyPI for the hash-pinned wheels (approved on 2026-10-02); every other network use needs its own approval. `scripts/container_check.sh` builds the app image and the test image for one architecture and checks them:

```bash
scripts/container_check.sh aarch64 --measure   # the Green's architecture, with the measurement
scripts/container_check.sh amd64
```

It first checks that a build without a target, as the Supervisor makes one, gives the app image. Then it runs, each in a container with `--network none`: the D-130 checks (a)–(d); the inventory (`scripts/image_inventory.py`, inside the app image: its Alpine packages, what the base image installs outside apk, its Python distributions, Pillow's bundled libraries held to the wheel's `RECORD`, and any wheel file, of which there must be none; D-171), and `THIRD_PARTY_NOTICES.md` must list all of it (`--notices`, H4); a smoke run of the app on one library file; the two test passes of D-165 (the whole suite as user 1000, and the root checks as root); and with `--measure`, `scripts/measure_prepare.py` as root under the real `RLIMIT_AS`. No host directory is mounted: inputs go in on stdin, and every result is kept in `../build/container-checks/<arch>/` (git-ignored). The script exits 1 if any check fails. Measure only on the native architecture: under Rosetta every `amd64` process carries about 278 MiB more address space, so the heaviest case then fails the 1 GiB limit (D-170).

**Without a build** (Phase 7, D-173): `--no-build` checks the images already built and uses no network at all. It requires that the app image holds exactly this checkout's `src/frame_gallery` (otherwise rebuild), lists every file in which the test image's copy differs from the checkout, and fails if one of them is a build input; the rest is the same.

```bash
scripts/container_check.sh aarch64 --no-build --measure
scripts/container_check.sh amd64 --no-build
```

**Failure paths** (Phase 7, D-173): `scripts/failure_paths.py` runs the app image's own command through 10 scenarios (no result, a failed decode, corrupt history, the upload ledger, a museum without a network, and a silent television), each on new Docker volumes, with `--network none` and no host directory, and checks what the specification says about each path. The silent television is a helper container that adds a second loopback address in its own network namespace (`NET_ADMIN`, that container only); the app's container joins that namespace. Results go to `../build/failure-paths/<arch>.json`; the script exits 1 if a scenario deviates.

```bash
.venv/bin/python scripts/failure_paths.py aarch64
```
