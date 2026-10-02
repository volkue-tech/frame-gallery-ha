#!/usr/bin/env bash
# Build the app image for one architecture and check it (Phase 6; D-130, D-165).
#
#   scripts/container_check.sh aarch64|amd64 [--measure]
#
# 1. Builds the "runtime" (app) and "test" targets with Docker Buildx; amd64
#    runs under the emulation that Docker Desktop provides.
# 2. D-130 checks: (a) the Alpine and Python versions; (b) the container stops
#    when the app exits, with its exit status; (c) a stop request reaches the
#    app at once, and the app has the whole stop timeout; (d) SUPERVISOR_TOKEN
#    reaches the app.
# 3. The inventory of what the image ships (scripts/image_inventory.py, run
#    inside the app image): its Alpine packages, its Python distributions,
#    and Pillow's bundled libraries, each held to the wheel's RECORD.
# 4. A smoke run of the app itself: a local-media run without any network
#    (--network none), so the television step fails as "unreachable" without
#    a packet leaving the container.
# 5. The two test passes of D-165: the whole suite as a non-root user
#    (FRAME_GALLERY_REQUIRE_ISOLATION=user) and the root checks as root
#    (FRAME_GALLERY_REQUIRE_ISOLATION=root).
# 6. With --measure: scripts/measure_prepare.py as root, under the real
#    RLIMIT_AS (R-09).
#
# Every container runs with --network none; the only network use is the
# build itself (the pinned base image, the Alpine package source for python3,
# and PyPI for the hash-pinned wheels). No host directory is mounted: inputs
# go in through stdin, and results come out on stdout. Each step's output is
# kept in ../build/container-checks/<arch>/ (git-ignored).
set -euo pipefail
cd "$(dirname "$0")/.."

ARCH=${1:?usage: container_check.sh aarch64|amd64 [--measure]}
MEASURE=${2:-}
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

note "build ($PLATFORM, version $VERSION)"
for target in runtime test; do
    tag=$APP
    [ "$target" = test ] && tag=$CHECKS
    docker buildx build --platform "$PLATFORM" --build-arg BUILD_ARCH="$ARCH" \
        --build-arg BUILD_VERSION="$VERSION" --target "$target" --load -t "$tag" . \
        > "$OUT/build-$target.log" 2>&1 || { tail -20 "$OUT/build-$target.log"; exit 1; }
done
docker image inspect "$APP" --format '{{json .Config.Labels}}' > "$OUT/labels.json"
grep -q "\"io.hass.arch\":\"$ARCH\"" "$OUT/labels.json" || fail "label io.hass.arch"
grep -q "\"io.hass.version\":\"$VERSION\"" "$OUT/labels.json" || fail "label io.hass.version"

note "(a) versions"
run --entrypoint /bin/sh "$APP" -c \
    'cat /etc/alpine-release; /opt/frame-gallery/bin/python -VV; apk info -v 2>/dev/null | sort' \
    > "$OUT/a-versions.txt"
head -2 "$OUT/a-versions.txt"

note "inventory: Alpine packages, Python distributions, and Pillow's libraries"
run -i --entrypoint /opt/frame-gallery/bin/python "$APP" -I - < scripts/image_inventory.py \
    > "$OUT/inventory.json" || fail "inventory"
.venv/bin/python scripts/image_inventory.py --summary "$OUT/inventory.json" || fail "inventory"

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
grep -q "outcome=tv_unreachable exit=0" "$OUT/smoke.txt" || fail "smoke run outcome"
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

if [ "$MEASURE" = --measure ]; then
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
