r"""Redaction of secrets from log text (§18.1, §19; acceptance H3).

Two layers apply, in this order:

1. **Known values.** Every registered secret (the Supervisor token, the
   television token) is replaced wherever it appears, longest first, also in
   its percent-encoded and JSON-escaped forms.
2. **Token patterns.**

   - After an authorization-type key (``Authorization``,
     ``Proxy-Authorization``, ``Cookie``, ``Set-Cookie``), the whole rest of
     the value: a complete quoted string, or else everything up to the end of
     the line. Only a known scheme word (``Bearer``, ``Basic``, ``Digest``,
     ``Negotiate``, ``Token``) stays visible.
   - The value of any other credential-named key (``token=...``,
     ``"password": "..."``, ``secret_key: ...``, ``session=...``, and
     camelCase keys such as ``accessToken`` or ``clientSecret``): a complete
     quoted string, also with a ``b``, ``u``, ``rb`` or ``br`` prefix, or else
     everything up to whitespace or one of ``"',;&``.
   - Keys and values are also recognised as ``('key', 'value')`` pairs (header
     tuples), as escaped JSON inside a JSON string (``{\"token\": \"...\"}``),
     and in a percent-encoded query (``%3Ftoken%3D...``, ending at ``%26``).
   - ``Bearer <token>`` anywhere, and JWT-shaped strings.

Ordinary text stays readable: words that merely contain a key name
(``token_rejected``, ``tokenCount``), SHA-256 fingerprints (also after the word
"Bearer"), and qualified identifiers such as ``aic:1234`` or
``local:fp:<hex>`` are not touched. Within one line, the text after an
authorization-type key cannot be told apart from its value, so it is redacted
too: over-redaction is preferred to a leak.

:func:`~frame_gallery.logs.setup.configure_logging` also makes its redactor
the process's *active* redactor. :func:`~frame_gallery.logs.summary.sanitize_for_log`
applies it before truncating, because a secret cut at the boundary would no
longer match the known-value layer.
"""

from __future__ import annotations

import json
import re
import threading
from collections.abc import Iterable
from typing import Final

REDACTED: Final = "[REDACTED]"

MIN_SECRET_LENGTH: Final = 6
"""Shorter values are ignored: they are too likely to occur in ordinary text,
and redacting them would hide more than it protects."""


def _alternatives(names: Iterable[str]) -> str:
    return "|".join(re.escape(name) for name in sorted(names, key=lambda name: (-len(name), name)))


_BEARER: Final = re.compile(
    r"\b(?P<scheme>bearer)(?P<space>\s+)[A-Za-z0-9\-._~+/]++=*+(?![A-Za-z0-9\-._~+/])", re.I
)
"""RFC 6750 ``b64token`` after the ``Bearer`` scheme. Its ``=`` padding ends
the token, so ``Bearer sha256=<hex>`` is ordinary text, not a token."""

_HEADER_KEYS: Final = ("authorization", "cookie")
"""Keys whose whole value is credential material. Prefixed words are included,
so these also cover ``Proxy-Authorization`` and ``Set-Cookie``."""

_CREDENTIAL_KEYS: Final = (
    "apikey",
    "auth",
    "credential",
    "credentials",
    "passphrase",
    "passwd",
    "password",
    "pwd",
    "secret",
    "session",
    "session_id",
    "session-id",
    "sessionid",
    "token",
)
"""Credential key names. Any word ending in ``_key`` or ``-key`` (``api_key``,
``secret_key``, ``private_key``, ``X-Api-Key``) is one too."""

_CAMEL_CASE_SUFFIXES: Final = (
    "Credential",
    "Credentials",
    "Key",
    "Passphrase",
    "Passwd",
    "Password",
    "Pwd",
    "Secret",
    "Token",
)
"""The last word of a camelCase or PascalCase credential key (``accessToken``,
``clientSecret``, ``apiKey``). The match is case-sensitive: the suffix must
start a new word, so ``monkey`` or ``tokenCount`` are not keys."""

_KEY_START: Final = r"(?:(?<![A-Za-z0-9])|(?<=%[0-9A-Fa-f]{2}))"
"""A key is never part of a longer word; a percent-encoded character before it
(``%3Ftoken``) counts as a word boundary."""

_PREFIX_WORD: Final = r"(?:[A-Za-z0-9]+[_-])"
"""A word joined to a key with "_" or "-" (client_secret, X-Auth-Token)."""

_CAMEL_CASE_KEY: Final = (
    rf"(?-i:[A-Za-z][a-z0-9]*(?:[A-Z][a-z0-9]*){{0,4}}?(?:{_alternatives(_CAMEL_CASE_SUFFIXES)}))"
)
"""Up to five words, then a credential suffix (``myOAuthAccessToken``)."""

_KEY_CLOSING_QUOTE: Final = r"\\{0,8}[\"']"
"""The closing quote of a quoted key, also escaped (JSON inside a JSON string)."""

_SEPARATOR: Final = (
    r"(?P<separator>"
    rf"(?:{_KEY_CLOSING_QUOTE})?[ \t]*[=:][ \t]*"
    r"|(?P<percent>%3D)"
    rf"|{_KEY_CLOSING_QUOTE}[ \t]*,[ \t]*(?P<pair>)"
    r")"
)
"""Between a key and its value, one of:

- an optional closing quote of a JSON or repr key, then "=" or ":";
- a percent-encoded "=" (``%3D``): the value then also ends at ``%26``;
- the closing quote of a key, then "," (a ``('key', 'value')`` pair): the
  value must then be quoted."""

_SCHEME: Final = r"(?:bearer|basic|digest|negotiate|token)[ \t]+"
"""An HTTP authorization scheme; it stays visible, its credentials do not."""

_PLAIN_BODY: Final = r"(?:\\.|(?!(?P=quote))[^\\\r\n])+"
"""The text of a quoted value: escape pairs, and characters other than its quote."""

_ESCAPED_BODY: Final = (
    r"(?:(?:\\\\\\\\)*+\\\\\\(?P=quote)"
    r"|(?:\\\\\\\\)++"
    r"|(?!\\(?P=quote))\\[^\r\n]"
    r"|(?!(?P=quote))[^\\\r\n])+"
)
r"""The text of a value opened by an escaped quote (``\"``: JSON inside a
JSON string). It ends at the matching ``\"``, or at an unescaped quote (the
end of the outer string). Inside it, ``\\\"`` is an escaped quote and
``\\\\`` an escaped backslash of the inner JSON. Deeper nesting is redacted
to the end of the outer string: more than the value, never less."""


def _key_value_pattern(key: str, unquoted_value: str) -> re.Pattern[str]:
    """``key``, a separator, then a quoted string or an unquoted value.

    A quoted value (optionally ``b``/``u``/``rb``/``br``-prefixed, and
    optionally opened by an escaped quote) runs to its closing quote, which
    stays in the text, or to the end of the line. After a pair separator
    (``'key', 'value'``) only a quoted value counts.
    """
    return re.compile(
        rf"(?P<key>{key}){_SEPARATOR}"
        r"(?:(?P<open>(?:[bu]|rb|br)?(?P<escape>\\++)?(?P<quote>[\"']))"
        rf"(?P<quoted_scheme>{_SCHEME})?(?(escape){_ESCAPED_BODY}|{_PLAIN_BODY})"
        rf"|(?(pair)(?!))(?P<scheme>{_SCHEME})?{unquoted_value})",
        re.I,
    )


_HEADER_VALUE: Final = _key_value_pattern(
    key=rf"{_KEY_START}{_PREFIX_WORD}{{0,4}}(?:{_alternatives(_HEADER_KEYS)})",
    unquoted_value=r"\S(?:[^\r\n]*\S)?",
)

_KEY_VALUE: Final = _key_value_pattern(
    key=(
        rf"{_KEY_START}(?:{_PREFIX_WORD}{{0,4}}"
        rf"(?:{_alternatives(_CREDENTIAL_KEYS)}|{_CAMEL_CASE_KEY})"
        rf"|{_PREFIX_WORD}{{1,4}}key)"
    ),
    # An escaped quote opens a quoted value, never an unquoted one. After a
    # percent-encoded "=", "%26" (a percent-encoded "&") ends the value.
    unquoted_value=r"(?!\\++[\"'])(?:(?(percent)(?!%26))[^\s\"',;&])+",
)

_JWT: Final = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*")


def _redact_value(match: re.Match[str]) -> str:
    scheme = match["quoted_scheme"] or match["scheme"] or ""
    return f"{match['key']}{match['separator']}{match['open'] or ''}{scheme}{REDACTED}"


_UNRESERVED: Final = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-~")


def _percent_encoded(value: str) -> str:
    """``value`` percent-encoded as in a URL query (RFC 3986 unreserved kept).

    A local encoder keeps the logging package free of ``urllib`` (D-107).
    """
    return "".join(
        chr(byte) if chr(byte) in _UNRESERVED else f"%{byte:02X}" for byte in value.encode()
    )


class Redactor:
    """Replaces secrets and token patterns in text. Safe to share between threads."""

    def __init__(self, secrets: Iterable[str] = ()) -> None:
        self._lock = threading.Lock()
        self._secrets: frozenset[str] = frozenset()
        self._secret_pattern: re.Pattern[str] | None = None
        for secret in secrets:
            self.add_secret(secret)

    def add_secret(self, value: str) -> None:
        """Register a secret value; values shorter than 6 characters are ignored."""
        if len(value) < MIN_SECRET_LENGTH:
            return
        forms = {value, _percent_encoded(value), json.dumps(value)[1:-1]}
        with self._lock:
            secrets = self._secrets | forms
            ordered = sorted(secrets, key=lambda secret: (-len(secret), secret))
            # One alternation, longest first: a replacement is never re-matched.
            self._secret_pattern = re.compile("|".join(re.escape(secret) for secret in ordered))
            self._secrets = secrets

    def redact(self, text: str) -> str:
        """``text`` with every registered secret and token pattern replaced."""
        pattern = self._secret_pattern
        if pattern is not None:
            text = pattern.sub(REDACTED, text)
        # Header values first: their schemes and credentials may contain
        # spaces, which would stop the narrower patterns part-way.
        text = _HEADER_VALUE.sub(_redact_value, text)
        text = _KEY_VALUE.sub(_redact_value, text)
        text = _BEARER.sub(rf"\g<scheme>\g<space>{REDACTED}", text)
        return _JWT.sub(REDACTED, text)


class _ActiveRedactor:
    """The slot behind :func:`set_active_redactor`; one reference, set atomically."""

    __slots__ = ("redactor",)

    def __init__(self) -> None:
        self.redactor: Redactor | None = None


_ACTIVE: Final = _ActiveRedactor()


def set_active_redactor(redactor: Redactor | None) -> None:
    """Make ``redactor`` the process's active redactor; ``None`` removes it.

    :func:`~frame_gallery.logs.setup.configure_logging` installs its redactor
    here, and :func:`~frame_gallery.logs.summary.sanitize_for_log` applies it
    to the full text before it truncates (§19; H3).
    """
    _ACTIVE.redactor = redactor


def active_redactor() -> Redactor | None:
    """The redactor :func:`set_active_redactor` installed, if any."""
    return _ACTIVE.redactor
