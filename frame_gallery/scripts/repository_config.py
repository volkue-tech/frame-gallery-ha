"""Fail-closed host repository check; fixture tests also run in app-only containers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[2]
DECLARATION: Final = (
    "name: 'Frame Gallery'\n"
    "url: 'https://github.com/volkue-tech/frame-gallery-ha'\n"
    "maintainer: 'Alexander Wilke'\n"
)


def require_repository(text: str) -> None:
    if text != DECLARATION:
        raise ValueError("required own root repository metadata differs")


def main(root: Path = ROOT) -> int:
    descriptor = root / "repository.yaml"
    app = root / "frame_gallery"
    config = app / "config.yaml"
    try:
        if app.is_symlink() or any(
            path.is_symlink() or not path.is_file() for path in (descriptor, config)
        ):
            raise ValueError("repository/app descriptor missing or linked")
        require_repository(descriptor.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        sys.stderr.write("Actual root repository metadata rejected; no gate bypass.\n")
        return 1
    sys.stdout.write("Actual root repository metadata and app location accepted.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
