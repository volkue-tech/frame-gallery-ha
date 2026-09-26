"""The summary line and log-safe text (§19).

Every run ends with exactly one summary line, including a watchdog
termination (§4.3). Text that comes from providers, files, or the television
is untrusted: :func:`sanitize_for_log` keeps it on one line and bounded, so
it can neither forge log lines nor reorder the display with bidi controls,
and it redacts secrets before it cuts (§19; H3).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from typing import Final

from frame_gallery.logs.redact import active_redactor

ELLIPSIS: Final = "\u2026"

_OUTCOME: Final = re.compile(r"[a-z_]{1,40}")

_INVISIBLE_CONTROLS: Final = frozenset(
    "\u061c\u200e\u200f"  # ALM, LRM, RLM
    "\u2028\u2029"  # line and paragraph separators
    "\u202a\u202b\u202c\u202d\u202e"  # LRE, RLE, PDF, LRO, RLO
    "\u2066\u2067\u2068\u2069"  # LRI, RLI, FSI, PDI
)


def _clean_character(character: str) -> str:
    if character in _INVISIBLE_CONTROLS:
        return " "
    category = unicodedata.category(character)
    if category == "Cc":
        return " "
    if category == "Cs":
        # A lone surrogate (valid in a JSON string) cannot be written as UTF-8.
        return "\ufffd"
    return character


def sanitize_for_log(text: str, *, max_length: int = 200) -> str:
    """Untrusted text made safe for one log line.

    Control characters (category ``Cc``), line separators, and bidi controls
    become spaces; whitespace runs collapse to one space; the result is
    stripped and cut to ``max_length`` characters, ending in "…" when cut.

    With an active redactor (:func:`~frame_gallery.logs.redact.set_active_redactor`),
    the text is redacted before it is cleaned and again before it is cut, so
    a cut never leaves a fragment of a secret for the formatter to miss, and
    cleaning cannot turn text into a secret that passes unredacted (§19; H3).
    """
    if max_length < 1:
        msg = f"max_length must be at least 1, got {max_length!r}"
        raise ValueError(msg)
    redactor = active_redactor()
    if redactor is not None:
        text = redactor.redact(text)
    cleaned = "".join(_clean_character(character) for character in text)
    collapsed = " ".join(cleaned.split())
    if redactor is not None:
        collapsed = redactor.redact(collapsed)
    if len(collapsed) <= max_length:
        return collapsed
    return collapsed[: max_length - 1].rstrip() + ELLIPSIS


def _redacted(text: str) -> str:
    redactor = active_redactor()
    return text if redactor is None else redactor.redact(text)


def _clean_ignored(item: str) -> str:
    # Removing spaces and commas can join the pieces of a secret: redact again.
    return _redacted(sanitize_for_log(item).replace(" ", "").replace(",", ""))


def format_summary(
    *,
    outcome: str,
    exit_code: int,
    elapsed_s: float,
    ignored: Sequence[str] = (),
    hint: str | None = None,
) -> str:
    """``outcome=<name> exit=<code> elapsed=<s> [ignored_filters=<filters>] [hint=...]``.

    The key is ``ignored_filters``, as D-124 and §9.2 name it and as in
    ``last_run.json``. ``outcome`` must match ``[a-z_]{1,40}``. The ignored
    filters are sanitized, stripped of spaces and commas, and comma-joined;
    the hint is sanitized, stripped of double quotes, and quoted. Each is
    redacted again after it is stripped, because stripping can join the
    pieces of a secret. Empty parts are omitted.
    """
    if _OUTCOME.fullmatch(outcome) is None:
        msg = "outcome must match [a-z_]{1,40}"
        raise ValueError(msg)
    parts = [f"outcome={outcome}", f"exit={exit_code}", f"elapsed={max(0.0, elapsed_s):.1f}"]
    names = [name for name in (_clean_ignored(item) for item in ignored) if name]
    if names:
        parts.append("ignored_filters=" + ",".join(names))
    if hint:
        cleaned_hint = _redacted(sanitize_for_log(hint).replace('"', ""))
        if cleaned_hint:
            parts.append(f'hint="{cleaned_hint}"')
    return " ".join(parts)
