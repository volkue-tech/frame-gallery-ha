#!/usr/bin/env bash
# The quality gates (ARCHITECTURE.md §20.4). Run from anywhere.
set -euo pipefail
cd "$(dirname "$0")/.."

BIN=.venv/bin

echo "== ruff"
"$BIN/ruff" check src tests scripts
"$BIN/ruff" format --check src tests scripts

echo "== mypy (strict)"
"$BIN/mypy"
echo "== mypy (strict, as on Linux: the container's platform)"
"$BIN/mypy" --platform linux

echo "== pytest (branch coverage)"
"$BIN/pytest" -q -p no:cacheprovider \
    --cov --cov-branch --cov-report=term-missing:skip-covered --cov-fail-under=90

echo "== 100 % line and branch coverage where the architecture requires it"
"$BIN/coverage" report --fail-under=100 --include='src/frame_gallery/budget/*,src/frame_gallery/store/*,src/frame_gallery/ha/*,src/frame_gallery/net/*,src/frame_gallery/selection/*,src/frame_gallery/isolation/*,src/frame_gallery/providers/*,src/frame_gallery/app/outcomes.py,src/frame_gallery/app/runner.py,src/frame_gallery/imaging/worker_tasks.py,src/frame_gallery/imaging/source_scan.py,src/frame_gallery/imaging/jpeg_header.py,src/frame_gallery/tv/*'

echo "All gates passed."
