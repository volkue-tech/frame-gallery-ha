"""Host-only checks of real workflow defaults; pure validators also run in Linux tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ("validate.yml", "publish.yml")
BASH_DEFAULT = "\ndefaults:\n  run:\n    shell: bash\n"
PUBLISHER_REF_GATE = (
    "    if: github.repository == 'volkue-tech/frame-gallery-ha' && "
    "(github.ref == 'refs/heads/main' || github.ref == 'refs/heads/codex/commons-default')\n"
)
PUBLISHER_CERTIFICATE = (
    '--certificate-identity "https://github.com/volkue-tech/frame-gallery-ha/'
    '.github/workflows/publish.yml@${GITHUB_REF}"'
)


def require_publisher_ref(text: str) -> None:
    """D-203: only the named own refs; signatures identify the actual ref."""
    if PUBLISHER_REF_GATE not in text or PUBLISHER_CERTIFICATE not in text:
        raise ValueError("publisher ref gate or certificate identity differs")


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
            if name == "publish.yml":
                require_publisher_ref(path.read_text())
    except (OSError, UnicodeError, ValueError):
        sys.stderr.write("Actual workflow defaults rejected; no gate bypass.\n")
        return 1
    sys.stdout.write("Both actual workflows preserve Bash pipefail defaults.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
