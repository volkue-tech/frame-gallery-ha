"""Actual shell failure propagation for the declared native CI/publisher defaults."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from scripts import ci_defaults


@pytest.mark.parametrize("name", ci_defaults.WORKFLOWS)
def test_host_gate_checks_both_actual_workflows_and_refuses_missing_default(
    name: str, tmp_path: Path
) -> None:
    directory = tmp_path / ".github/workflows"
    directory.mkdir(parents=True)
    for workflow in ci_defaults.WORKFLOWS:
        text = "name: fixture\n" + ci_defaults.BASH_DEFAULT
        if workflow == "publish.yml":
            text += ci_defaults.PUBLISHER_REF_GATE + ci_defaults.PUBLISHER_CERTIFICATE
        (directory / workflow).write_text(text)
    assert ci_defaults.main(tmp_path) == 0
    (directory / name).write_text("name: fixture\n")
    assert ci_defaults.main(tmp_path) == 1


@pytest.mark.parametrize("extra", ["    shell: sh\n", "continue-on-error: true\n"])
def test_shell_override_or_error_suppression_is_refused(extra: str) -> None:
    with pytest.raises(ValueError, match="fail-closed"):
        ci_defaults.require_bash("name: fixture\n" + ci_defaults.BASH_DEFAULT + extra)


def test_missing_or_linked_actual_workflow_fails_the_host_gate(tmp_path: Path) -> None:
    assert ci_defaults.main(tmp_path) == 1
    directory = tmp_path / ".github/workflows"
    directory.mkdir(parents=True)
    (directory / "validate.yml").symlink_to(tmp_path / "missing")
    assert ci_defaults.main(tmp_path) == 1


def test_check_script_runs_the_actual_host_declaration_gate() -> None:
    project = Path(__file__).resolve().parents[3]
    assert '"$BIN/python" scripts/ci_defaults.py' in (project / "scripts/check.sh").read_text()


def test_publisher_certificate_matches_the_narrow_approved_ref_gate() -> None:
    ci_defaults.require_publisher_ref(
        ci_defaults.PUBLISHER_REF_GATE + ci_defaults.PUBLISHER_CERTIFICATE
    )


@pytest.mark.parametrize("change", ["repo", "arbitrary_ref", "certificate"])
def test_publisher_ref_and_signature_policy_changes_are_refused(change: str) -> None:
    text = ci_defaults.PUBLISHER_REF_GATE + ci_defaults.PUBLISHER_CERTIFICATE
    if change == "repo":
        text = text.replace("volkue-tech/frame-gallery-ha", "another-owner/project")
    elif change == "arbitrary_ref":
        text = text.replace("refs/heads/codex/commons-curated", "refs/heads/arbitrary")
    else:
        text = text.replace("${GITHUB_REF}", "refs/heads/main")
    with pytest.raises(ValueError, match="publisher ref gate"):
        ci_defaults.require_publisher_ref(text)


@pytest.mark.parametrize("code", [0, 7])
def test_tee_preserves_test_failure_under_the_declared_shell(code: int) -> None:
    # Fixed synthetic command, no repository command, network or credential.
    process = subprocess.run(  # noqa: S603 -- fixed test shell, synthetic exit only
        [
            "/bin/bash",
            "--noprofile",
            "--norc",
            "-eo",
            "pipefail",
            "-c",
            f"(exit {code}) | tee /dev/null\nprintf 'after-gate'",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert process.returncode == code
    assert process.stdout == ("after-gate" if code == 0 else "")


def test_unspecified_github_shell_is_an_effective_negative_control() -> None:
    process = subprocess.run(
        ["/bin/bash", "-e", "-c", "(exit 7) | tee /dev/null\nprintf 'after-gate'"],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert process.returncode == 0
    assert process.stdout == "after-gate"
