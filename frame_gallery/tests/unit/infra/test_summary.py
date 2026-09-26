"""The summary line and log-safe text (§19; H3)."""

from __future__ import annotations

import pytest

from frame_gallery.logs.redact import REDACTED, Redactor, active_redactor, set_active_redactor
from frame_gallery.logs.summary import ELLIPSIS, format_summary, sanitize_for_log

LINE_SEPARATOR = chr(0x2028)
PARAGRAPH_SEPARATOR = chr(0x2029)
BIDI_CONTROLS = [chr(code) for code in (*range(0x202A, 0x202F), *range(0x2066, 0x206A))]
BIDI_MARKS = [chr(0x200E), chr(0x200F), chr(0x061C)]

SECRET_64 = "sv-4f9Qm7Rt2Vx9Lp4Hs8Kd3Nf6Wb1Yc5Jg0ZeTu8Ao3Ib6Gh1Wn5Rk2Ey7Dp0Mx"  # noqa: S105 - a test value
FILLER = "the television refused the request because " * 10

# --- sanitize_for_log ------------------------------------------------------


def test_sanitize_keeps_ordinary_text() -> None:
    text = "Caf" + chr(0xE9) + " " + chr(0x65E5) + chr(0x672C) + " - Water Lilies (1906)"
    assert sanitize_for_log(text) == text


@pytest.mark.parametrize(
    "control",
    ["\x00", "\x07", "\x1b", "\n", "\r", "\t", "\x0b", "\x0c", "\x7f", "\x85", "\x9b"],
)
def test_sanitize_replaces_c0_and_c1_controls(control: str) -> None:
    assert sanitize_for_log(f"a{control}b") == "a b"


def test_sanitize_prevents_forged_log_lines() -> None:
    text = "title\n2026-01-01T00:00:00Z ERROR frame_gallery: forged"
    assert "\n" not in sanitize_for_log(text)


@pytest.mark.parametrize("separator", [LINE_SEPARATOR, PARAGRAPH_SEPARATOR])
def test_sanitize_replaces_unicode_line_separators(separator: str) -> None:
    assert sanitize_for_log(f"a{separator}b") == "a b"


@pytest.mark.parametrize("control", BIDI_CONTROLS + BIDI_MARKS)
def test_sanitize_replaces_bidi_controls(control: str) -> None:
    assert sanitize_for_log(f"abc{control}def") == "abc def"


def test_sanitize_replaces_lone_surrogates() -> None:
    assert sanitize_for_log("a" + chr(0xD800) + "b") == "a" + chr(0xFFFD) + "b"


def test_sanitize_collapses_and_strips_whitespace() -> None:
    assert sanitize_for_log("  a \t\n  b" + chr(0xA0) + " c  ") == "a b c"


def test_sanitize_keeps_text_at_the_limit() -> None:
    assert sanitize_for_log("x" * 200) == "x" * 200


def test_sanitize_truncates_with_an_ellipsis() -> None:
    result = sanitize_for_log("x" * 300)
    assert len(result) == 200
    assert result == "x" * 199 + ELLIPSIS
    assert chr(0x2026) == ELLIPSIS


def test_sanitize_truncates_after_collapsing() -> None:
    assert sanitize_for_log("a" + " " * 50 + "b", max_length=3) == "a b"


def test_sanitize_does_not_end_a_cut_on_a_space() -> None:
    assert sanitize_for_log("abcd efgh", max_length=6) == "abcd" + ELLIPSIS


def test_sanitize_with_the_smallest_limit() -> None:
    assert sanitize_for_log("abc", max_length=1) == ELLIPSIS
    assert sanitize_for_log("a", max_length=1) == "a"


@pytest.mark.parametrize("max_length", [0, -1])
def test_sanitize_requires_a_positive_limit(max_length: int) -> None:
    with pytest.raises(ValueError, match="max_length"):
        sanitize_for_log("abc", max_length=max_length)


def test_sanitize_of_only_controls_is_empty() -> None:
    assert sanitize_for_log("\n\r\t\x00") == ""


# --- sanitize_for_log with an active redactor (§19; H3) ----------------------


def _fragments(secret: str, size: int = 6) -> list[str]:
    """Every ``size``-character piece of ``secret``; a leaked prefix contains one."""
    return [secret[start : start + size] for start in range(len(secret) - size + 1)]


def test_the_test_secret_is_64_characters() -> None:
    assert len(SECRET_64) == 64
    assert not any(fragment in FILLER for fragment in _fragments(SECRET_64))


def test_sanitize_without_an_active_redactor_does_not_redact() -> None:
    assert active_redactor() is None
    assert sanitize_for_log(f"token={SECRET_64}") == f"token={SECRET_64}"


@pytest.mark.parametrize("offset", range(200 - 64, 199))
def test_a_secret_straddling_the_cut_is_never_left_in_part(offset: int) -> None:
    set_active_redactor(Redactor([SECRET_64]))
    text = FILLER[:offset] + SECRET_64 + " while pairing with the television" * 8
    assert offset < 199 < offset + len(SECRET_64)  # unredacted, the cut splits the secret
    result = sanitize_for_log(text)
    assert len(result) <= 200
    assert result.endswith(ELLIPSIS)
    assert not any(fragment in result for fragment in _fragments(SECRET_64))


def test_a_secret_before_the_cut_is_redacted_whole() -> None:
    set_active_redactor(Redactor([SECRET_64]))
    result = sanitize_for_log(f"refused {SECRET_64}\n" + "x" * 300)
    assert result.startswith(f"refused {REDACTED} x")


def test_sanitize_redacts_before_cleaning() -> None:
    # Cleaning turns the tab into a space: only the raw text still holds the
    # registered value.
    secret = "pass\tphrase-4711"  # noqa: S105 - a test value
    set_active_redactor(Redactor([secret]))
    assert sanitize_for_log(f"login with {secret} failed") == f"login with {REDACTED} failed"


def test_sanitize_redacts_again_after_cleaning() -> None:
    # Only the cleaned text holds the registered value, and it straddles the cut.
    secret = "open sesame-token-42"  # noqa: S105 - a test value
    set_active_redactor(Redactor([secret]))
    result = sanitize_for_log("x" * 190 + " open\nsesame-token-42 tail")
    assert not any(fragment in result for fragment in _fragments(secret))
    assert result == "x" * 190 + " [REDACTE" + ELLIPSIS


def test_sanitize_applies_token_patterns_before_the_cut() -> None:
    # Unredacted, the cut falls inside the credential.
    set_active_redactor(Redactor())
    result = sanitize_for_log("x" * 165 + " Authorization: SAMSUNG abcdefghijklmnopqrstuvwxyz")
    assert result == "x" * 165 + " Authorization: " + REDACTED


def test_the_summary_hint_is_redacted() -> None:
    set_active_redactor(Redactor([SECRET_64]))
    line = format_summary(outcome="no_match", exit_code=0, elapsed_s=1.0, hint=f"k {SECRET_64}")
    assert line == f'outcome=no_match exit=0 elapsed=1.0 hint="k {REDACTED}"'


# --- format_summary --------------------------------------------------------


def test_summary_minimal() -> None:
    assert format_summary(outcome="delivered", exit_code=0, elapsed_s=41.26) == (
        "outcome=delivered exit=0 elapsed=41.3"
    )


def test_summary_with_every_part() -> None:
    line = format_summary(
        outcome="no_match",
        exit_code=0,
        elapsed_s=12.04,
        ignored=("style", "color"),
        hint="filters too restrictive",
    )
    assert line == (
        "outcome=no_match exit=0 elapsed=12.0 ignored_filters=style,color "
        'hint="filters too restrictive"'
    )


def test_summary_watchdog_line() -> None:
    line = format_summary(outcome="watchdog_termination", exit_code=71, elapsed_s=130.0)
    assert line == "outcome=watchdog_termination exit=71 elapsed=130.0"


def test_summary_sanitizes_ignored_filters() -> None:
    line = format_summary(
        outcome="delivered",
        exit_code=0,
        elapsed_s=1.0,
        ignored=("de part\nment", "a,b", "   ", "\x00", "sty le"),
    )
    assert line == "outcome=delivered exit=0 elapsed=1.0 ignored_filters=department,ab,style"


def test_summary_omits_ignored_when_every_item_is_empty() -> None:
    line = format_summary(outcome="delivered", exit_code=0, elapsed_s=1.0, ignored=(" ", "\n"))
    assert line == "outcome=delivered exit=0 elapsed=1.0"


def test_summary_sanitizes_the_hint() -> None:
    line = format_summary(
        outcome="no_match", exit_code=0, elapsed_s=2.0, hint='say "hi"\nexit=70 outcome=x'
    )
    assert line == 'outcome=no_match exit=0 elapsed=2.0 hint="say hi exit=70 outcome=x"'
    assert line.count('"') == 2


@pytest.mark.parametrize("hint", [None, "", "\n\t", '""'])
def test_summary_omits_an_empty_hint(hint: str | None) -> None:
    line = format_summary(outcome="no_match", exit_code=0, elapsed_s=2.0, hint=hint)
    assert line == "outcome=no_match exit=0 elapsed=2.0"


@pytest.mark.parametrize(
    ("elapsed", "text"), [(0.0, "0.0"), (0.06, "0.1"), (-0.4, "0.0"), (float("nan"), "0.0")]
)
def test_summary_elapsed_is_never_negative(elapsed: float, text: str) -> None:
    line = format_summary(outcome="cancelled", exit_code=0, elapsed_s=elapsed)
    assert line == f"outcome=cancelled exit=0 elapsed={text}"


@pytest.mark.parametrize(
    "outcome", ["", "No_Match", "no-match", "no match", "a" * 41, "delivered\n", "x1"]
)
def test_summary_rejects_an_invalid_outcome(outcome: str) -> None:
    with pytest.raises(ValueError, match="outcome"):
        format_summary(outcome=outcome, exit_code=0, elapsed_s=0.0)


def test_summary_accepts_the_longest_outcome() -> None:
    line = format_summary(outcome="a" * 40, exit_code=70, elapsed_s=0.0)
    assert line == f"outcome={'a' * 40} exit=70 elapsed=0.0"


# --- format_summary with an active redactor (§19; H3) -----------------------

TV_TOKEN = "13962738"  # noqa: S105 - a test value


def test_joining_the_ignored_filters_cannot_form_a_registered_secret() -> None:
    set_active_redactor(Redactor([TV_TOKEN]))
    line = format_summary(
        outcome="no_match",
        exit_code=0,
        elapsed_s=1.0,
        ignored=("1396 2738", "13962,738", "style=cubism(other_source)"),
    )
    assert TV_TOKEN not in line
    assert line == (
        f"outcome=no_match exit=0 elapsed=1.0 "
        f"ignored_filters={REDACTED},{REDACTED},style=cubism(other_source)"
    )


def test_joining_the_ignored_filters_cannot_form_a_credential() -> None:
    set_active_redactor(Redactor())
    line = format_summary(
        outcome="no_match", exit_code=0, elapsed_s=1.0, ignored=("tok en=abcdef",)
    )
    assert "abcdef" not in line
    assert line == f"outcome=no_match exit=0 elapsed=1.0 ignored_filters=token={REDACTED}"


@pytest.mark.parametrize(
    ("hint", "expected"),
    [
        ('tok"en=abcdef', f"token={REDACTED}"),
        ('see 1396"2738', f"see {REDACTED}"),
    ],
)
def test_removing_quotes_from_the_hint_cannot_form_a_secret(hint: str, expected: str) -> None:
    set_active_redactor(Redactor([TV_TOKEN]))
    line = format_summary(outcome="no_match", exit_code=0, elapsed_s=1.0, hint=hint)
    assert "abcdef" not in line
    assert TV_TOKEN not in line
    assert line == f'outcome=no_match exit=0 elapsed=1.0 hint="{expected}"'


@pytest.mark.parametrize(
    "hint",
    [
        None,
        "filters too restrictive",
        "nothing new left for these filters",
        "search limits reached",
        "accept the connection prompt on your TV, then start the app again",
        "paired; start the app again",
        "the upload may have reached the TV",
        "stored on the TV and may be displayed",
    ],
)
def test_ordinary_summary_lines_are_not_redacted(hint: str | None) -> None:
    ignored = (
        "department=cma_prints(other_source)",
        "style=impressionism(unsupported_by_source)",
        "color=red(unsupported_by_source)",
    )
    plain = format_summary(
        outcome="delivered_with_warnings", exit_code=0, elapsed_s=41.26, ignored=ignored, hint=hint
    )
    set_active_redactor(Redactor([SECRET_64, TV_TOKEN]))
    redacted = format_summary(
        outcome="delivered_with_warnings", exit_code=0, elapsed_s=41.26, ignored=ignored, hint=hint
    )
    assert redacted == plain
    assert REDACTED not in redacted
