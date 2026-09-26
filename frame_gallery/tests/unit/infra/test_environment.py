"""The allowlisted runtime environment (§17.5). Plain dicts only, never ``os.environ``."""

from __future__ import annotations

import dataclasses

import pytest

from frame_gallery.app.environment import (
    ALLOWED_VARIABLES,
    ReducedEnvironment,
    apply_environment,
    reduce_environment,
)

TOKEN = "supervisor-token-value-0123456789"  # noqa: S105 - a test value

ENVIRON = {
    "PATH": "/usr/local/bin:/usr/bin",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "TZ": "UTC",
    "SUPERVISOR_TOKEN": TOKEN,
    "HASSIO_TOKEN": "legacy-token-value",
    "HTTP_PROXY": "http://10.0.0.5:3128",
    "https_proxy": "http://10.0.0.5:3128",
    "NO_PROXY": "localhost",
    "ALL_PROXY": "socks5://10.0.0.5:1080",
    "NETRC": "/root/.netrc",
    "REQUESTS_CA_BUNDLE": "/etc/custom/ca.pem",
    "SSL_CERT_FILE": "/etc/custom/ca.pem",
    "SSL_CERT_DIR": "/etc/custom/certs",
    "CURL_CA_BUNDLE": "/etc/custom/ca.pem",
    "PYTHONPATH": "/somewhere",
    "HOME": "/root",
    "path": "/lowercase/is/another/variable",
}


def test_the_allowlist() -> None:
    assert ALLOWED_VARIABLES == ("PATH", "LANG", "LC_ALL", "TZ")


def test_only_allowlisted_variables_are_kept() -> None:
    reduced = reduce_environment(ENVIRON, keep_supervisor_token=True)
    assert dict(reduced.variables) == {
        "PATH": "/usr/local/bin:/usr/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TZ": "UTC",
    }


def test_removed_lists_sorted_names_only() -> None:
    reduced = reduce_environment(ENVIRON, keep_supervisor_token=True)
    expected = sorted(set(ENVIRON) - set(ALLOWED_VARIABLES))
    assert list(reduced.removed) == expected
    assert "SUPERVISOR_TOKEN" in reduced.removed
    assert "HASSIO_TOKEN" in reduced.removed
    assert TOKEN not in reduced.removed


def test_the_token_is_kept_in_memory_when_helpers_are_configured() -> None:
    reduced = reduce_environment(ENVIRON, keep_supervisor_token=True)
    assert reduced.supervisor_token == TOKEN
    assert "SUPERVISOR_TOKEN" not in reduced.variables


def test_the_token_is_dropped_without_helpers() -> None:
    reduced = reduce_environment(ENVIRON, keep_supervisor_token=False)
    assert reduced.supervisor_token is None
    assert "SUPERVISOR_TOKEN" in reduced.removed


@pytest.mark.parametrize("environ", [{"SUPERVISOR_TOKEN": ""}, {"PATH": "/bin"}])
def test_a_missing_or_empty_token_is_none(environ: dict[str, str]) -> None:
    assert reduce_environment(environ, keep_supervisor_token=True).supervisor_token is None


def test_the_legacy_token_is_never_used() -> None:
    reduced = reduce_environment({"HASSIO_TOKEN": "legacy-token-value"}, keep_supervisor_token=True)
    assert reduced.supervisor_token is None
    assert reduced.removed == ("HASSIO_TOKEN",)


def test_missing_allowlisted_variables_are_not_invented() -> None:
    reduced = reduce_environment({"PATH": "/bin"}, keep_supervisor_token=False)
    assert dict(reduced.variables) == {"PATH": "/bin"}
    assert reduced.removed == ()


def test_the_repr_never_shows_the_token() -> None:
    reduced = reduce_environment(ENVIRON, keep_supervisor_token=True)
    assert TOKEN not in repr(reduced)
    assert TOKEN not in str(reduced)
    assert "supervisor_token" not in repr(reduced)


def test_the_variables_are_read_only() -> None:
    reduced = reduce_environment(ENVIRON, keep_supervisor_token=False)
    with pytest.raises(TypeError):
        reduced.variables["PATH"] = "/evil"  # type: ignore[index]
    with pytest.raises(dataclasses.FrozenInstanceError):
        reduced.supervisor_token = "x"  # type: ignore[misc]  # noqa: S105


def test_direct_construction_copies_the_variables() -> None:
    source = {"PATH": "/bin"}
    reduced = ReducedEnvironment(variables=source, supervisor_token=None, removed=())
    source["PATH"] = "/changed"
    assert reduced.variables == {"PATH": "/bin"}
    with pytest.raises(TypeError):
        reduced.variables["TZ"] = "UTC"  # type: ignore[index]


def test_reduction_does_not_modify_its_input() -> None:
    environ = dict(ENVIRON)
    reduce_environment(environ, keep_supervisor_token=True)
    assert environ == ENVIRON


def test_apply_replaces_the_target_contents() -> None:
    target = dict(ENVIRON)
    reduced = reduce_environment(target, keep_supervisor_token=True)
    apply_environment(target, reduced)
    assert target == {
        "PATH": "/usr/local/bin:/usr/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TZ": "UTC",
    }
    assert TOKEN not in target.values()
    assert reduced.supervisor_token == TOKEN


def test_apply_to_an_empty_reduction_clears_everything() -> None:
    target = {"SUPERVISOR_TOKEN": TOKEN, "HOME": "/root"}
    apply_environment(target, reduce_environment({}, keep_supervisor_token=True))
    assert target == {}
