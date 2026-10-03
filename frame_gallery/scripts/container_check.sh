#!/usr/bin/env bash
# Build the app image for one architecture and check it (Phase 6; D-130, D-165).
#
#   scripts/container_check.sh aarch64|amd64 [--measure] [--no-build]
#
# 1. Builds the "runtime" (app) and "test" targets with Docker Buildx; amd64
#    runs under the emulation that Docker Desktop provides. A build without a
#    target, as the Supervisor makes one, must give the same image as
#    "runtime" (its layers, command, environment, and labels).
# 2. D-130 checks: (a) the Alpine and Python versions; (b) the container stops
#    when the app exits, with its exit status; (c) a stop request reaches the
#    app at once, and the app has the whole stop timeout; (d) SUPERVISOR_TOKEN
#    reaches the app.
# 3. The inventory of what the image ships (scripts/image_inventory.py, run
#    inside the app image): its Alpine packages, its Python distributions,
#    and Pillow's bundled libraries, each held to the wheel's RECORD; and
#    THIRD_PARTY_NOTICES.md must list all of it (H4).
# 4. A smoke run of the app itself: a local-media run without any network
#    (--network none), so the television step fails as "unreachable" without
#    a packet leaving the container.
# 5. The two test passes of D-165: the whole suite as a non-root user
#    (FRAME_GALLERY_REQUIRE_ISOLATION=user) and the root checks as root
#    (FRAME_GALLERY_REQUIRE_ISOLATION=root).
# 6. With --measure: scripts/measure_prepare.py as root, under the real
#    RLIMIT_AS (R-09).
#
# With --no-build (Phase 7: offline, with the images already built), step 1
# changes: nothing is built, and the script checks instead that both images
# exist, that the test image builds on the app image, and that the app image
# holds exactly this checkout's src/frame_gallery (otherwise they must be
# rebuilt). It lists every file in which the test image's copy differs from
# this checkout's build context, and fails if one of them is a build input.
# Whether a build without a target gives the app image is checked only when
# building. Nothing in this mode uses the network.
#
# Every container runs with --network none; the only network use is the
# build itself (the pinned base image, the Alpine package source for python3,
# and PyPI for the hash-pinned wheels). No host directory is mounted: inputs
# go in through stdin, and results come out on stdout. Each step's output is
# kept in ../build/container-checks/<arch>/ (git-ignored).
set -euo pipefail
cd "$(dirname "$0")/.."

ARCH=${1:?usage: container_check.sh aarch64|amd64 [--measure] [--no-build]}
shift
MEASURE=
NO_BUILD=
for option in "$@"; do
    case "$option" in
        --measure) MEASURE=1 ;;
        --no-build) NO_BUILD=1 ;;
        *) echo "unknown option: $option" >&2; exit 2 ;;
    esac
done
case "$ARCH" in
    aarch64) PLATFORM=linux/arm64 ;;
    amd64) PLATFORM=linux/amd64 ;;
    *) echo "unknown architecture: $ARCH" >&2; exit 2 ;;
esac
VERSION=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' src/frame_gallery/__init__.py)
APP=frame-gallery:dev-$ARCH
CHECKS=frame-gallery-checks:dev-$ARCH
OUT=../build/container-checks/$ARCH
mkdir -p "$OUT"
FAILED=0

note() { printf '== %s\n' "$*"; }
fail() { printf 'FAILED: %s\n' "$*"; FAILED=1; }
run() { docker run --rm --platform "$PLATFORM" --network none "$@"; }

# The files of a tree, as "<sha256> <path>" lines, without compiled files.
MANIFEST='import hashlib, os, sys
root = sys.argv[1]
for base, dirs, files in os.walk(root):
    dirs[:] = [name for name in dirs if name != "__pycache__"]
    for name in files:
        if not name.endswith((".pyc", ".pyo")):
            path = os.path.join(base, name)
            with open(path, "rb") as handle:
                digest = hashlib.sha256(handle.read()).hexdigest()
            print(digest, os.path.relpath(path, root))'
# The same for this checkout's build context: the allowlist of .dockerignore,
# without what its patterns leave out.
CONTEXT='import hashlib, os, sys
root = sys.argv[1]
with open(os.path.join(root, ".dockerignore")) as handle:
    allowed = [line[1:].rstrip("/") for line in handle.read().splitlines() if line.startswith("!")]
skipped = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")
def emit(path):
    with open(path, "rb") as handle:
        print(hashlib.sha256(handle.read()).hexdigest(), os.path.relpath(path, root))
for entry in allowed:
    top = os.path.join(root, entry)
    if os.path.isfile(top):
        emit(top)
    for base, dirs, files in os.walk(top):
        dirs[:] = [name for name in dirs if name not in skipped]
        for name in files:
            if not name.endswith((".pyc", ".pyo", ".pyd")) and not name.startswith(".coverage"):
                emit(os.path.join(base, name))'
sorted_by_path() { LC_ALL=C sort -k 2; }

if [ -z "$NO_BUILD" ]; then
    note "build ($PLATFORM, version $VERSION)"
    for target in runtime test; do
        tag=$APP
        [ "$target" = test ] && tag=$CHECKS
        docker buildx build --platform "$PLATFORM" --build-arg BUILD_ARCH="$ARCH" \
            --build-arg BUILD_VERSION="$VERSION" --target "$target" --load -t "$tag" . \
            > "$OUT/build-$target.log" 2>&1 || { tail -20 "$OUT/build-$target.log"; exit 1; }
    done
    docker buildx build --platform "$PLATFORM" --build-arg BUILD_ARCH="$ARCH" \
        --build-arg BUILD_VERSION="$VERSION" --load -t "$APP-default" . \
        > "$OUT/build-default.log" 2>&1 || fail "a build without a target"
    content() {
        docker image inspect "$1" --format \
            '{{json .RootFS.Layers}} {{json .Config.Cmd}} {{json .Config.Env}} {{json .Config.Labels}}'
    }
    [ "$(content "$APP-default")" = "$(content "$APP")" ] || fail "a build without a target is not the app"
    docker image rm "$APP-default" > /dev/null 2>&1 || true
else
    note "the images already built, without a build: $APP and $CHECKS"
    for image in "$APP" "$CHECKS"; do
        docker image inspect "$image" > /dev/null 2>&1 \
            || { echo "no image $image: build it first (without --no-build)" >&2; exit 1; }
    done
    layers() { docker image inspect "$1" --format '{{range .RootFS.Layers}}{{println .}}{{end}}'; }
    app_layers=$(layers "$APP")
    count=$(printf '%s\n' "$app_layers" | wc -l)
    [ "$(layers "$CHECKS" | head -n "$count")" = "$app_layers" ] \
        || fail "the test image does not build on the app image"
    run --entrypoint /opt/frame-gallery/bin/python "$APP" -I -c "$MANIFEST" \
        /opt/frame-gallery/lib/python3.14/site-packages/frame_gallery | sorted_by_path \
        > "$OUT/sources-app.txt"
    .venv/bin/python -I -c "$MANIFEST" src/frame_gallery | sorted_by_path > "$OUT/sources-src.txt"
    if cmp -s "$OUT/sources-src.txt" "$OUT/sources-app.txt"; then
        echo "the app image holds this checkout's src/frame_gallery ($(wc -l < "$OUT/sources-src.txt" | tr -d ' ') files)"
    else
        { diff "$OUT/sources-src.txt" "$OUT/sources-app.txt" || true; } | head -20
        fail "the app image does not hold this checkout's src/frame_gallery: rebuild it"
    fi
    run --entrypoint /opt/frame-gallery/bin/python "$CHECKS" -I -c "$MANIFEST" \
        /opt/frame-gallery-checks | sorted_by_path > "$OUT/sources-checks.txt"
    .venv/bin/python -I -c "$CONTEXT" . | sorted_by_path > "$OUT/sources-context.txt"
    { diff "$OUT/sources-context.txt" "$OUT/sources-checks.txt" || true; } \
        | sed -n 's/^[<>] [0-9a-f]* //p' | LC_ALL=C sort -u > "$OUT/sources-differ.txt"
    if [ -s "$OUT/sources-differ.txt" ]; then
        echo "the test image's copy differs from this checkout in:"
        sed 's/^/  /' "$OUT/sources-differ.txt"
        if grep -qE '^(src/|requirements/|Dockerfile$|\.dockerignore$|pyproject\.toml$|uv\.lock$)' \
            "$OUT/sources-differ.txt"; then
            fail "the test image was built from other build inputs: rebuild it"
        fi
    else
        echo "the test image holds this checkout's build context"
    fi
fi
docker image inspect "$APP" --format '{{json .Config.Labels}}' > "$OUT/labels.json"
grep -q "\"io.hass.arch\":\"$ARCH\"" "$OUT/labels.json" || fail "label io.hass.arch"
grep -q "\"io.hass.version\":\"$VERSION\"" "$OUT/labels.json" || fail "label io.hass.version"

note "(a) versions"
run --entrypoint /bin/sh "$APP" -c \
    'cat /etc/alpine-release; /opt/frame-gallery/bin/python -VV; apk info -v 2>/dev/null | sort' \
    > "$OUT/a-versions.txt"
head -2 "$OUT/a-versions.txt"
# The Alpine series of the base tag, and the pinned interpreter's version.
ALPINE=$(sed -n 's|^FROM ghcr.io/home-assistant/base:\([0-9]*\.[0-9]*\)-.*|\1|p' Dockerfile)
PYTHON=$(sed -n 's|.*apk add --no-cache python3=\([0-9.]*\)-r[0-9]*.*|\1|p' Dockerfile | sort -u)
sed -n 1p "$OUT/a-versions.txt" | grep -q "^${ALPINE//./\\.}\." || fail "(a) Alpine is not $ALPINE"
sed -n 2p "$OUT/a-versions.txt" | grep -q "^Python ${PYTHON//./\\.} " || fail "(a) Python is not $PYTHON"

note "inventory: Alpine packages, Python distributions, and Pillow's libraries"
run -i --entrypoint /opt/frame-gallery/bin/python "$APP" -I - < scripts/image_inventory.py \
    > "$OUT/inventory.json" || fail "inventory"
.venv/bin/python scripts/image_inventory.py --summary "$OUT/inventory.json" || fail "inventory"
.venv/bin/python scripts/image_inventory.py --notices "$OUT/inventory.json" ../THIRD_PARTY_NOTICES.md \
    || fail "the notices do not list what the image ships (H4)"

note "(b) the container stops with the app's exit status"
set +e
run "$APP" with-contenv /opt/frame-gallery/bin/python -I -c 'raise SystemExit(70)' > /dev/null 2>&1
status=$?
set -e
echo "exit status $status"
[ "$status" -eq 70 ] || fail "(b) exit status $status, expected 70"

note "(c) a stop request reaches the app at once and waits for it"
SCRIPT='import signal, sys, time
start = time.monotonic()
def stop(signum, frame):
    print(f"stop request after {time.monotonic() - start:.1f} s", flush=True)
    time.sleep(8)
    print(f"cleaned up after {time.monotonic() - start:.1f} s", flush=True)
    sys.exit(0)
signal.signal(signal.SIGTERM, stop)
print("ready", flush=True)
time.sleep(60)'
cid=$(docker run -d --platform "$PLATFORM" --network none "$APP" \
    with-contenv /opt/frame-gallery/bin/python -I -c "$SCRIPT")
sleep 3
started=$(date +%s)
docker stop -t 20 "$cid" > /dev/null
stopped=$(date +%s)
docker logs "$cid" > "$OUT/c-stop.txt" 2>&1
docker rm "$cid" > /dev/null
echo "docker stop took $((stopped - started)) s"
grep -E "stop request|cleaned up" "$OUT/c-stop.txt" || true
grep -q "cleaned up" "$OUT/c-stop.txt" || fail "(c) the app was killed before it cleaned up"
if grep -q "invalid number" "$OUT/c-stop.txt"; then
    fail "(c) signal forwarding emitted a shell warning"
fi

note "(d) SUPERVISOR_TOKEN reaches the app"
run -e SUPERVISOR_TOKEN=check-token-value "$APP" with-contenv /opt/frame-gallery/bin/python -I -c \
    'import os; print("SUPERVISOR_TOKEN visible:", os.environ.get("SUPERVISOR_TOKEN") == "check-token-value")' \
    > "$OUT/d-token.txt" 2>&1
grep "visible" "$OUT/d-token.txt"
grep -q "visible: True" "$OUT/d-token.txt" || fail "(d) token not visible"

note "smoke run: one local-media run without network"
data=fg-check-data-$ARCH
media=fg-check-media-$ARCH
docker volume rm -f "$data" "$media" > /dev/null 2>&1 || true
docker volume create "$data" > /dev/null
docker volume create "$media" > /dev/null
.venv/bin/python - <<'EOF' | run -i -v "$data:/data" -v "$media:/media" --entrypoint /bin/sh "$APP" -c \
    'mkdir -p /tmp/in /media/frame_gallery/library && tar -xf - -C /tmp/in \
     && cp /tmp/in/options.json /data/ && chmod 600 /data/options.json \
     && cp /tmp/in/harbour.jpg /media/frame_gallery/library/'
import io, json, sys, tarfile
from PIL import Image
buffer = io.BytesIO()
Image.new("RGB", (1920, 1080), (40, 90, 160)).save(buffer, "JPEG", quality=90)
files = {
    "harbour.jpg": buffer.getvalue(),
    "options.json": json.dumps({"tv_host": "10.0.0.5", "source": "local_media"}).encode(),
}
with tarfile.open(fileobj=sys.stdout.buffer, mode="w|") as archive:
    for name, data in files.items():
        info = tarfile.TarInfo(name)
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
EOF
run --tmpfs /tmp -v "$data:/data" -v "$media:/media" "$APP" > "$OUT/smoke.txt" 2>&1 || true
grep "frame_gallery" "$OUT/smoke.txt" || true
# Docker Desktop cannot load the Green's AppArmor policy. The shipped entry
# point must refuse this unprofiled container before any artwork I/O.
grep -q "outcome=internal_error exit=70" "$OUT/smoke.txt" || fail "unprofiled entry did not refuse"
# Exercise the internal test wiring separately; this is not a shipped CLI
# option or a way to disable the mandatory profile in the Home Assistant app.
run --tmpfs /tmp -v "$data:/data" -v "$media:/media" "$APP" \
    with-contenv /opt/frame-gallery/bin/python -I -B -c \
    'import os,sys; from frame_gallery.__main__ import run_app,Wiring; sys.exit(run_app(os.environ,sys.stderr,Wiring()))' \
    > "$OUT/smoke-test-wiring.txt" 2>&1 || true
grep -q "outcome=tv_unreachable exit=0" "$OUT/smoke-test-wiring.txt" || fail "test-wiring smoke run outcome"
run -v "$data:/data" --entrypoint /bin/sh "$APP" -c 'cat /data/state/last_run.json' \
    > "$OUT/smoke-last-run.json"
docker volume rm "$data" "$media" > /dev/null

note "D-165 user pass: the whole suite as a non-root user"
set +e
run --init --tmpfs /tmp:exec --user 1000:1000 --group-add 100 \
    -e FRAME_GALLERY_REQUIRE_ISOLATION=user --entrypoint /opt/frame-gallery/bin/python \
    "$CHECKS" -m pytest -q -p no:cacheprovider > "$OUT/user-pass.txt" 2>&1
status=$?
set -e
tail -6 "$OUT/user-pass.txt"
[ "$status" -eq 0 ] || fail "user pass"

note "D-165 root pass: the root checks as root"
set +e
run --init --tmpfs /tmp:exec -e FRAME_GALLERY_REQUIRE_ISOLATION=root \
    --entrypoint /opt/frame-gallery/bin/python "$CHECKS" \
    -m pytest -v -p no:cacheprovider tests/unit/isolation/test_root_isolation.py \
    > "$OUT/root-pass.txt" 2>&1
status=$?
set -e
grep -E "PASSED|FAILED|SKIPPED|ERROR" "$OUT/root-pass.txt" || true
[ "$status" -eq 0 ] || fail "root pass"

if [ -n "$MEASURE" ]; then
    note "R-09: worst-case preparation under the real RLIMIT_AS, as root"
    set +e
    run --init --tmpfs /tmp:exec,size=4g --entrypoint /opt/frame-gallery/bin/python "$CHECKS" \
        scripts/measure_prepare.py --repeat 2 --inspections 150 > "$OUT/measure.txt" 2>&1
    status=$?
    set -e
    cat "$OUT/measure.txt"
    [ "$status" -eq 0 ] || fail "measurement"
fi

if [ "$FAILED" -ne 0 ]; then
    echo "Some container checks failed (see $OUT)."
    exit 1
fi
echo "All container checks passed for $ARCH."
