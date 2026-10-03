"""The runtime environment, reduced to an allowlist (§17.5).

``SUPERVISOR_TOKEN`` is kept in parent memory only for configured helpers or
an explicit loading timer (D-176); the environment holds only :data:`ALLOWED_VARIABLES`.
Everything else is removed because it is not on the allowlist: the token
itself, the legacy ``HASSIO_TOKEN``, proxy variables, ``NETRC``, and CA
overrides such as ``REQUESTS_CA_BUNDLE`` and ``SSL_CERT_FILE``. Workers
inherit the reduced environment and never see the token (§18.1).
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

ALLOWED_VARIABLES: Final = ("PATH", "LANG", "LC_ALL", "TZ")

SUPERVISOR_TOKEN_VARIABLE: Final = "SUPERVISOR_TOKEN"  # noqa: S105 - a name, not a value


@dataclass(frozen=True, slots=True)
class ReducedEnvironment:
    """The allowlisted variables and, if kept, the Supervisor token.

    The token is excluded from ``repr`` so it cannot reach a log line.
    """

    variables: Mapping[str, str]
    supervisor_token: str | None = field(repr=False)
    removed: tuple[str, ...]
    """Names of the removed variables, sorted. Never their values."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "variables", MappingProxyType(dict(self.variables)))


def reduce_environment(
    environ: Mapping[str, str], *, keep_supervisor_token: bool
) -> ReducedEnvironment:
    """Split ``environ`` into the allowlisted variables and the token.

    The token is kept only if ``keep_supervisor_token`` is set (helpers or a
    loading timer are configured) and it is non-empty.
    """
    variables = {name: environ[name] for name in ALLOWED_VARIABLES if name in environ}
    token = environ.get(SUPERVISOR_TOKEN_VARIABLE) if keep_supervisor_token else None
    removed = tuple(sorted(name for name in environ if name not in variables))
    return ReducedEnvironment(
        variables=variables,
        supervisor_token=token or None,
        removed=removed,
    )


def apply_environment(target: MutableMapping[str, str], reduced: ReducedEnvironment) -> None:
    """Replace the contents of ``target`` (``os.environ`` in production) with
    the allowlisted variables only."""
    target.clear()
    target.update(reduced.variables)
