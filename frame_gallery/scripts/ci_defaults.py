"""Host-only checks of real workflow defaults; pure validators also run in Linux tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ("validate.yml", "publish.yml")
BASH_DEFAULT = "\ndefaults:\n  run:\n    shell: bash\n"


def require_bash(text: str) -> None:
    if BASH_DEFAULT not in text or text.count("shell:") != 1 or "continue-on-error:" in text:
        raise ValueError("workflow must preserve fail-closed Bash defaults")


def main(root: Path = ROOT) -> int:
    try:
        for name in WORKFLOWS:
            path = root / ".github/workflows" / name
            if path.is_symlink():
                raise ValueError("workflow must not be a symlink")
            require_bash(path.read_text())
    except (OSError, UnicodeError, ValueError):
        sys.stderr.write("Actual workflow defaults rejected; no gate bypass.\n")
        return 1
    sys.stdout.write("Both actual workflows preserve Bash pipefail defaults.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
