"""Redaction of secrets and token patterns (§18.1, §19; acceptance H3)."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from urllib.parse import quote

import pytest

from frame_gallery.logs.redact import MIN_SECRET_LENGTH, REDACTED, Redactor
from frame_gallery.logs.setup import RedactingFormatter
from frame_gallery.logs.summary import format_summary

SECRET = "s3cr3t-supervisor-token-9f8e7d"  # noqa: S105 - a test value
JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJmcmFtZS1nYWxsZXJ5LXRlc3QifQ"
    ".c2lnbmF0dXJlLW9mLXRoZS10ZXN0LWp3dA"
)
SHA256 = hashlib.sha256(b"frame gallery test image").hexdigest()


# --- registered secrets -----------------------------------------------------


def test_a_registered_secret_is_replaced_everywhere() -> None:
    redactor = Redactor([SECRET])
    text = f"first {SECRET}, again:{SECRET}."
    assert redactor.redact(text) == f"first {REDACTED}, again:{REDACTED}."


def test_add_secret_registers_later_values() -> None:
    redactor = Redactor()
    assert redactor.redact(f"x {SECRET}") == f"x {SECRET}"
    redactor.add_secret(SECRET)
    assert redactor.redact(f"x {SECRET}") == f"x {REDACTED}"


def test_the_longest_secret_wins() -> None:
    redactor = Redactor(["abcdef", "abcdefghij"])
    assert redactor.redact("abcdefghij abcdef") == f"{REDACTED} {REDACTED}"


def test_short_values_are_ignored() -> None:
    assert MIN_SECRET_LENGTH == 6
    redactor = Redactor(["", "abc", "12345"])
    assert redactor.redact("abc 12345 text") == "abc 12345 text"
    redactor.add_secret("123456")
    assert redactor.redact("abc 123456 text") == f"abc {REDACTED} text"


def test_a_replacement_is_never_matched_again() -> None:
    redactor = Redactor(["REDACTED", "[REDACTED]x"])
    assert redactor.redact("a REDACTED b") == f"a {REDACTED} b"


def test_special_characters_in_secrets_are_literal() -> None:
    secret = "a.b*c+d?(e)"  # noqa: S105 - a test value
    redactor = Redactor([secret])
    assert redactor.redact(f"<{secret}> aXbbcd") == f"<{REDACTED}> aXbbcd"


def test_the_percent_encoded_form_is_replaced() -> None:
    secret = "p@ss/w0rd+x y"  # noqa: S105 - a test value
    redactor = Redactor([secret])
    encoded = quote(secret, safe="")
    assert encoded != secret
    assert redactor.redact(f"GET /api?x={encoded} HTTP/1.1") == (f"GET /api?x={REDACTED} HTTP/1.1")


def test_the_json_escaped_form_is_replaced() -> None:
    secret = 'to"ken' + chr(92) + "val" + chr(0xE9)
    redactor = Redactor([secret])
    escaped = json.dumps({"k": secret})
    assert secret not in escaped
    assert redactor.redact(escaped) == '{"k": "' + REDACTED + '"}'


# --- token patterns ---------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Bearer abc.def-ghi_jkl~mno+pq/r==", f"Bearer {REDACTED}"),
        ("bearer xyz123", f"bearer {REDACTED}"),
        ("BEARER\txyz123 next", f"BEARER\t{REDACTED} next"),
        ("header Authorization: Bearer tok3n", f"header Authorization: Bearer {REDACTED}"),
    ],
)
def test_bearer_tokens(text: str, expected: str) -> None:
    assert Redactor().redact(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("token=abc123", f"token={REDACTED}"),
        ("Token = abc123 next", f"Token = {REDACTED} next"),
        ("?access_token=abc&x=1", f"?access_token={REDACTED}&x=1"),
        ("refresh_token: abc", f"refresh_token: {REDACTED}"),
        ("password = hunter2, next", f"password = {REDACTED}, next"),
        ("PASSWD=x;y", f"PASSWD={REDACTED};y"),
        ("secret:abc", f"secret:{REDACTED}"),
        (
            "api_key=k1 apikey=k2 api-key: k3",
            f"api_key={REDACTED} apikey={REDACTED} api-key: {REDACTED}",
        ),
        ("Api-Key=k1", f"Api-Key={REDACTED}"),
        ("authorization=abc", f"authorization={REDACTED}"),
        ('{"password": "hunter2"}', f'{{"password": "{REDACTED}"}}'),
        ("{'token': 'abc'}", f"{{'token': '{REDACTED}'}}"),
        ("client_secret=xyz", f"client_secret={REDACTED}"),
        ("X-Auth-Token: xyz", f"X-Auth-Token: {REDACTED}"),
        ("Authorization: Basic dXNlcjpwYXNz", f"Authorization: Basic {REDACTED}"),
        ("Authorization: Digest abc", f"Authorization: Digest {REDACTED}"),
        ("token=[REDACTED]", f"token={REDACTED}"),
    ],
)
def test_credential_values(text: str, expected: str) -> None:
    assert Redactor().redact(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # An unknown scheme is redacted together with its credentials.
        ("Authorization: SAMSUNG abcdefgh", f"Authorization: {REDACTED}"),
        ("authorization=Custom k=v, n=1", f"authorization={REDACTED}"),
        # A known scheme stays visible; everything after it does not.
        ("Authorization: Bearer abc def", f"Authorization: Bearer {REDACTED}"),
        ("Authorization: Token abc", f"Authorization: Token {REDACTED}"),
        (
            'Authorization: Digest username="u", response="abc"',
            f"Authorization: Digest {REDACTED}",
        ),
        ("Proxy-Authorization: Negotiate YII= more", f"Proxy-Authorization: Negotiate {REDACTED}"),
        ("proxy-authorization: Samsung abc", f"proxy-authorization: {REDACTED}"),
        # The value ends at the end of the line ...
        ("Authorization: Samsung abc\nHost: tv", f"Authorization: {REDACTED}\nHost: tv"),
        ("Authorization: Samsung abc  \r\nHost: tv", f"Authorization: {REDACTED}  \r\nHost: tv"),
        # ... or at the closing quote.
        (
            "{'Authorization': 'SAMSUNG abc def', 'Host': 'tv'}",
            f"{{'Authorization': '{REDACTED}', 'Host': 'tv'}}",
        ),
        ('{"Authorization": "Basic dXNlcjpwYXNz"}', f'{{"Authorization": "Basic {REDACTED}"}}'),
        ("{b'Authorization': b'Samsung abc'}", f"{{b'Authorization': b'{REDACTED}'}}"),
        # Within one line, text after the value cannot be told apart from it.
        (f"Authorization: {REDACTED} (retrying)", f"Authorization: {REDACTED}"),
        ("Authorization: Bearer", f"Authorization: {REDACTED}"),
        # Cookies are credentials as a whole.
        ("Cookie: theme=dark; session=abc", f"Cookie: {REDACTED}"),
        ("Set-Cookie: sid=abc; Path=/; HttpOnly", f"Set-Cookie: {REDACTED}"),
    ],
)
def test_authorization_type_values_are_redacted_whole(text: str, expected: str) -> None:
    assert Redactor().redact(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("secret_key=abcdefgh", f"secret_key={REDACTED}"),
        ("private_key=abcdefgh", f"private_key={REDACTED}"),
        ("access_key: abcdefgh", f"access_key: {REDACTED}"),
        ("aws-secret-access-key=abc", f"aws-secret-access-key={REDACTED}"),
        ("X-Api-Key: abc", f"X-Api-Key: {REDACTED}"),
        ("auth=abcdefgh", f"auth={REDACTED}"),
        ("auth=token_rejected", f"auth={REDACTED}"),
        ("X-Auth: abc", f"X-Auth: {REDACTED}"),
        ("credentials=abc", f"credentials={REDACTED}"),
        ("credential: abc", f"credential: {REDACTED}"),
        ("pwd=hunter2", f"pwd={REDACTED}"),
        ("passphrase: correct-horse", f"passphrase: {REDACTED}"),
        ("session=abc123&x=1", f"session={REDACTED}&x=1"),
        ("sessionid=abc123", f"sessionid={REDACTED}"),
        ("session_id=abc session-id=def", f"session_id={REDACTED} session-id={REDACTED}"),
    ],
)
def test_more_credential_key_names(text: str, expected: str) -> None:
    assert Redactor().redact(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("{'token': b'raw-bytes-token-123'}", f"{{'token': b'{REDACTED}'}}"),
        ('{"access_token": "tok en with space"}', f'{{"access_token": "{REDACTED}"}}'),
        ("password=u'hunter 2'", f"password=u'{REDACTED}'"),
        ("secret_key=rb'x y', n=1", f"secret_key=rb'{REDACTED}', n=1"),
        ("token=BR'a b'", f"token=BR'{REDACTED}'"),
        ("token=B'a b'", f"token=B'{REDACTED}'"),
        ('password: "a\\"b c" next', f'password: "{REDACTED}" next'),
        ("{'password': 'it\\'s me'}", f"{{'password': '{REDACTED}'}}"),
        ("token='a \"b\" c'", f"token='{REDACTED}'"),
        ("token: 'Bearer abc def'", f"token: 'Bearer {REDACTED}'"),
        ('"password": "cut off at the end', f'"password": "{REDACTED}'),
        ('"password": "line one\nline two"', f'"password": "{REDACTED}\nline two"'),
        ("token=bad'", f"token={REDACTED}'"),
        ('"password": ""', '"password": ""'),
    ],
)
def test_quoted_and_prefixed_values_are_redacted_whole(text: str, expected: str) -> None:
    assert Redactor().redact(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        f"id {JWT} end",
        f"jwt={JWT}",
        f"{JWT}",
    ],
)
def test_jwt_shaped_strings(text: str) -> None:
    redacted = Redactor().redact(text)
    assert JWT not in redacted
    assert "eyJ" not in redacted
    assert REDACTED in redacted


def test_a_jwt_without_a_signature() -> None:
    assert Redactor().redact("eyJhbGciOiJub25lIn0.eyJzdWIiOiIxIn0.") == REDACTED


@pytest.mark.parametrize(
    "text",
    [
        "token_rejected",
        "reason=token_rejected",
        "status: token_rejected",
        "tv_not_authorized: token_rejected",
        "the token was rejected",
        "tokens=3",
        "token-type: bearer",
        f"sha256={SHA256}",
        f"fingerprint {SHA256}",
        "aic:1234",
        "cma:98765",
        f"local:fp:{SHA256}",
        "selected aic:1234 (Water Lilies)",
        "KeyError('password')",
        "password",
        "secret_santa",
        "outcome=no_match exit=0 elapsed=12.0",
        "eyJ alone is not a JWT",
        "key=department",
        "monkey=3",
        "keyboard: x",
        "sessions=3",
        "session_count=3",
        "cookies=2",
        "oauth=1",
        "authors=3",
        "Authorization",
        "unauthorized: token_rejected",
        f"session_sha256={SHA256}",
    ],
)
def test_ordinary_text_is_untouched(text: str) -> None:
    assert Redactor([SECRET]).redact(text) == text


def test_redaction_is_idempotent() -> None:
    redactor = Redactor([SECRET])
    samples = [
        f"Authorization: Bearer {SECRET}",
        f"token={SECRET}&password=x",
        f"{JWT} and {SECRET}",
        "Authorization: Basic dXNlcjpwYXNz",
        f"Authorization: SAMSUNG {SECRET} extra\nnext line",
        "{'Authorization': 'Negotiate a b', 'token': b'raw bytes'}",
        '{"access_token": "tok en", "secret_key": "k"}',
        "Cookie: a=b; c=d",
    ]
    for sample in samples:
        once = redactor.redact(sample)
        assert redactor.redact(once) == once
        assert SECRET not in once


@pytest.mark.parametrize(
    "text",
    [
        "a_" * 20_000 + "=" + "x-" * 20_000 + "Bearer " * 5_000,
        "authorization: " * 10_000,
        "token='" + "\\x" * 20_000,
        "a_" * 10_000 + "key " + "Cookie:" * 10_000,
        "token=" * 20_000,
    ],
)
def test_pathological_input_is_linear_enough(text: str) -> None:
    started = time.perf_counter()
    Redactor([SECRET]).redact(text)
    assert time.perf_counter() - started < 2.0


# --- header tuples, escaped JSON, camelCase, percent-encoding ---------------

VALUE = "s3cr3tV4lue"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "[('Authorization', 'Basic dXNlcjpwYXNz'), ('Host', 'tv')]",
            f"[('Authorization', 'Basic {REDACTED}'), ('Host', 'tv')]",
        ),
        ("[('X-Api-Key', 'k3yv4lue99')]", f"[('X-Api-Key', '{REDACTED}')]"),
        ("(('token', 'tv-t0ken-777'),)", f"(('token', '{REDACTED}'),)"),
        ("('Authorization', 'SAMSUNG abc def')", f"('Authorization', '{REDACTED}')"),
        ('[("Cookie", "sid=abc; theme=dark")]', f'[("Cookie", "{REDACTED}")]'),
        ("(b'password', b'hunter 2')", f"(b'password', b'{REDACTED}')"),
        ("('access_token' ,  'abc')", f"('access_token' ,  '{REDACTED}')"),
        (
            "[('token', 'a'), ('secret', 'b')]",
            f"[('token', '{REDACTED}'), ('secret', '{REDACTED}')]",
        ),
    ],
)
def test_key_value_pairs_as_tuples(text: str, expected: str) -> None:
    assert Redactor().redact(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "('Host', 'tv')",
        "KeyError('token')",
        "('token', 3)",
        "('token', '')",
        "('Authorization', '')",
        "token, 'abc'",
        "a token, 'quoted' text",
    ],
)
def test_a_pair_needs_a_quoted_key_and_a_quoted_value(text: str) -> None:
    assert Redactor().redact(text) == text


TV_EVENT = '{"event": "ms.channel.connect", "data": "{\\"token\\": \\"13962738\\"}"}'


def test_json_inside_a_json_string() -> None:
    assert Redactor().redact(TV_EVENT) == (
        '{"event": "ms.channel.connect", "data": "{\\"token\\": \\"' + REDACTED + '\\"}"}'
    )


@pytest.mark.parametrize(
    ("inner", "visible"),
    [
        ({"token": VALUE, "name": "Living Room"}, "Living Room"),
        ({"password": 'ab"cd\\' + VALUE, "x": 1}, '\\"x\\": 1'),
        ({"password": VALUE + "\\", "x": 1}, '\\"x\\": 1'),
        ({"accessToken": VALUE + "\\\\", "x": 1}, '\\"x\\": 1'),
        ({"Authorization": "Basic " + VALUE, "x": 1}, '\\"Authorization\\": \\"Basic '),
        ({"secret": "line\n" + VALUE, "x": 1}, '\\"x\\": 1'),
    ],
)
def test_escaped_json_values_end_at_their_escaped_quote(
    inner: dict[str, object], visible: str
) -> None:
    text = json.dumps(json.dumps(inner))
    redacted = Redactor().redact(text)
    assert VALUE not in redacted
    assert REDACTED in redacted
    assert visible in redacted
    assert Redactor().redact(redacted) == redacted


@pytest.mark.parametrize(
    "text",
    [
        json.dumps(json.dumps(json.dumps({"token": VALUE}))),
        json.dumps(json.dumps(json.dumps({"password": 'a"b\\' + VALUE, "x": 1}))),
        '{\\"token\\": \\"' + VALUE,
        "{\\'token\\': \\'" + VALUE + "\\'}",
        "token=\\\\\\\\\\\\\\\\" + VALUE + '"',
    ],
)
def test_deeper_or_unusual_escaping_never_leaks(text: str) -> None:
    redacted = Redactor().redact(text)
    assert VALUE not in redacted
    assert REDACTED in redacted


def test_an_empty_escaped_value_is_left_alone() -> None:
    text = json.dumps(json.dumps({"password": ""}))
    assert Redactor().redact(text) == text


@pytest.mark.parametrize(
    "key",
    [
        "accessToken",
        "clientSecret",
        "refreshToken",
        "authToken",
        "idToken",
        "apiKey",
        "sessionId",
        "sessionToken",
        "AccessToken",
        "myOAuthAccessToken",
        "userPassword",
        "dbPasswd",
        "walletPassphrase",
        "adminPwd",
        "awsCredentials",
        "gcpCredential",
        "privateKey",
        "x-accessToken",
    ],
)
@pytest.mark.parametrize(
    ("template", "expected"),
    [
        ("{key}=" + VALUE, "{key}=" + REDACTED),
        ('{{"{key}": "' + VALUE + '"}}', '{{"{key}": "' + REDACTED + '"}}'),
        ('"{key}":"' + VALUE + '"', '"{key}":"' + REDACTED + '"'),
        ("{key}: " + VALUE, "{key}: " + REDACTED),
    ],
)
def test_camel_case_keys(key: str, template: str, expected: str) -> None:
    text = template.format(key=key)
    assert Redactor().redact(text) == expected.format(key=key)


@pytest.mark.parametrize(
    "text",
    [
        "accessTokens=3",
        "tokenCount=3",
        "maxTokens: 5",
        "keyboardLayout: de",
        "monkeyKing=1",
        "isSecretive=1",
        "contentId=MY-F0012",
        "imageId: 42",
        "hotkey=F5",
        "Tokenizer: bpe",
        "turkey: roasted",
        "Keynote: x",
        "ACCESSTOKENS=3",
    ],
)
def test_camel_case_boundaries_keep_ordinary_words(text: str) -> None:
    assert Redactor().redact(text) == text


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("next=%2Fcb%3Ftoken%3D" + VALUE, "next=%2Fcb%3Ftoken%3D" + REDACTED),
        (
            "next=%2Fcb%3Ftoken%3d" + VALUE + "%26x%3D1",
            "next=%2Fcb%3Ftoken%3d" + REDACTED + "%26x%3D1",
        ),
        (
            "next=%2Fcb%3Faccess_token%3Dab%2Bcd" + VALUE + "%26state%3Dxyz",
            "next=%2Fcb%3Faccess_token%3D" + REDACTED + "%26state%3Dxyz",
        ),
        ("r=%3FaccessToken%3D" + VALUE, "r=%3FaccessToken%3D" + REDACTED),
        ("r=%3Fx%3D1%26password%3D" + VALUE, "r=%3Fx%3D1%26password%3D" + REDACTED),
        # In a value that is not itself percent-encoded, "%26" is part of it.
        ("token=ab%26" + VALUE, "token=" + REDACTED),
        ("?next=/cb?token%3D" + VALUE + "&x=1", "?next=/cb?token%3D" + REDACTED + "&x=1"),
    ],
)
def test_percent_encoded_separators(text: str, expected: str) -> None:
    assert Redactor().redact(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "%2Ftokens%3D3",
        "%3Ftoken_count%3D2",
        "100%25token",
        "%3Fnext%3D%2Fhome",
    ],
)
def test_percent_encoded_ordinary_text_is_untouched(text: str) -> None:
    assert Redactor().redact(text) == text


# --- the standalone Bearer pattern ------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        f"Bearer sha256={SHA256}",
        f"bearer sha256={SHA256} x",
        "Bearer abc==def",
        f"chosen: aic:1 (strict) The Standard Bearer sha256={SHA256}",
    ],
)
def test_padding_must_end_a_bearer_token(text: str) -> None:
    assert Redactor().redact(text) == text


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Bearer abc==", f"Bearer {REDACTED}"),
        ("Bearer abc= next", f"Bearer {REDACTED} next"),
        ("Bearer abc=,x", f"Bearer {REDACTED},x"),
        ('"Bearer abc="', f'"Bearer {REDACTED}"'),
        ("Bearer a+b/c", f"Bearer {REDACTED}"),
        ("Bearer abc:def", f"Bearer {REDACTED}:def"),
    ],
)
def test_bearer_tokens_with_padding(text: str, expected: str) -> None:
    assert Redactor().redact(text) == expected


# --- over-redaction guard: the runner's ordinary log lines -------------------

SUPERVISOR = "5f1c2e9a7b3d4c6e8f0a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6"
TV_TOKEN = "13962738"  # noqa: S105 - a test value
QUALIFIED_IDS = (
    "aic:27992",
    "aic:6565-a",
    "cma:94979",
    "cma:1953.424",
    f"local:fp:{SHA256}",
)
STAGES = (
    "configure",
    "resolve_filters",
    "select",
    "attempt",
    "pre_stage",
    "deliver",
    "record",
    "publish",
    "finish",
)
DECISIONS = (
    "duplicate",
    "excluded",
    "rights_rejected",
    "dims_unavailable",
    "dims_unavailable:allowance",
    "probe_not_found",
    "probe_failed",
    "inspection_failed",
    "fallback_offered",
    "rejected:too_small",
    "rejected:not_landscape",
    "rejected:not_near_16_9",
    "shortlisted:strict",
    "shortlisted:first_eligible",
    "shortlisted:fallback",
)
BASES = ("strict", "first_eligible", "fallback")
DOWNLOAD_FAILURES = (
    "transport",
    "timeout",
    "http_error",
    "stopped",
    "not_found",
    "over_cap",
    "unexpected_format",
)
PREPARE_FAILURES = (
    "timeout",
    "crash",
    "memory",
    "protocol",
    "unknown_task",
    "format_mismatch",
    "limits",
    "decode",
    "unsupported_mode",
    "render",
    "encode",
    "output_too_large",
    "io",
)
REJECTIONS = ("too_small", "not_landscape", "not_near_16_9")
ATTRIBUTIONS = (
    "Claude Monet. Water Lilies. 1906",
    "Rembrandt van Rijn. The Standard Bearer. 1636",
    "The Standard Bearer",
    "Unknown. Token of Friendship. c. 1850",
    "Jan Steen. The Key: a Study. 1660",
    "Katsushika Hokusai. Under the Wave off Kanagawa (Kanagawa oki nami ura). 1830/33",
    "(no attribution)",
)
DISCOVERY_ENDS = (
    "shortlist_full",
    "exhausted",
    "deadline",
    "candidate_allowance",
    "provider_error",
)
STATUSES = (
    "none",
    "ok",
    "unreachable",
    "not_authorized",
    "unsupported",
    "refused",
    "protocol",
    "insufficient_time",
)
MARKERS = (
    "none",
    "connected",
    "connected,upload_started",
    "connected,upload_started,uploaded",
    "connected,upload_started,uploaded,selected",
)
OUTCOMES = (
    ("delivered", 0),
    ("delivered_with_warnings", 0),
    ("delivered_unrecorded", 0),
    ("no_match", 0),
    ("config_invalid", 64),
    ("already_running", 0),
    ("state_error", 70),
    ("source_failed", 69),
    ("image_failed", 65),
    ("tv_unreachable", 69),
    ("tv_not_authorized", 77),
    ("tv_rejected", 76),
    ("deadline_exceeded", 75),
    ("cancelled", 0),
    ("internal_error", 70),
    ("watchdog_termination", 71),
)
HINTS = (
    None,
    "filters too restrictive",
    "nothing new left for these filters",
    "search limits reached",
    "accept the connection prompt on your TV, then start the app again",
    "paired; start the app again",
    "the upload may have reached the TV",
    "stored on the TV and may be displayed",
)
HELPER_WARNINGS = (
    "could not be read",
    "is unavailable in Home Assistant",
    "does not name a source (art_institute_chicago, cleveland_museum_of_art, or local_media)",
    "matches no key, label, or alias of this option",
)


def _runner_lines() -> list[str]:
    """The runner's log lines (``app/runner.py``) with realistic values."""
    lines = [f"stage {stage}" for stage in STAGES]
    lines += [
        "another run is in progress",
        (
            "start: source=art_institute_chicago (static) "
            "filters=department=aic_painting_and_sculpture_of_europe(helper), color=red(static) "
            "ignored=style=cma_prints(other_source)"
        ),
        (
            "start: source=local_media (helper) filters=none "
            "ignored=department=aic_prints(unsupported_by_source), "
            "style=impressionism(unsupported_by_source), color=blue(unsupported_by_source)"
        ),
        "start: source=cleveland_museum_of_art (static) filters=none ignored=none",
        "filter department=cma_prints ignored for art_institute_chicago: other_source",
        "filter color=red ignored for cleveland_museum_of_art: unsupported_by_source",
        "helper values could not be applied; using the static options",
        "the run's time budget ran out (content_window)",
        "not enough time left for the television; the TV was not contacted",
        "the television step ran out of time",
        "the television step failed unexpectedly",
        "television: art mode image selected (content id MY-F0012)",
        "the television reported selected without uploaded",
        "stop requested: the preview was not updated",
        (
            "option fit_mode: The fit mode must be contain (shows the whole artwork) or cover "
            "(fills the screen and may crop)."
        ),
        (
            "option background_color: The background colour must have the form #RRGGBB, "
            "such as #000000."
        ),
        (
            "option department_helper: The helper must be an entity ID of an input_select, "
            "select, or input_text helper, such as input_select.frame_gallery "
            "(lowercase letters, digits, and underscores)."
        ),
        "option log_level: The log level must be info or debug.",
        "option options: The options must be an object of option names and values.",
    ]
    lines += [
        f"{field}_helper {reason}; using the static value"
        for field in ("source", "department", "style", "color")
        for reason in HELPER_WARNINGS
    ]
    lines += [
        f"selection: 3 shortlisted ({end}); seen=40 excluded=2 evaluated=10 probes=3 inspections=1"
        for end in DISCOVERY_ENDS
    ]
    lines += [
        f"television result: status={status} markers={markers}"
        for status in STATUSES
        for markers in MARKERS
    ]
    for qid in QUALIFIED_IDS:
        lines += [f"candidate {qid}: {decision}" for decision in DECISIONS]
        lines += [f"shortlisted {qid} ({basis}, 3840x2160)" for basis in BASES]
        lines += [f"download of {qid} failed: {kind}" for kind in DOWNLOAD_FAILURES]
        lines += [f"preparing {qid} failed: {kind}" for kind in PREPARE_FAILURES]
        lines += [f"{qid} does not qualify after all: {rule}" for rule in REJECTIONS]
        lines += [
            f"download of {qid} ran out of time",
            f"{qid} is not the declared image format",
            f"preparing {qid} returned an invalid result",
            f"the prepared image for {qid} is invalid: not a baseline JPEG",
            f"{qid} stays in the upload quarantine",
            f"the confirmed upload of {qid} could not be recorded: disk full",
            f"the upload intent for {qid} could not be removed; it stays in quarantine: disk full",
        ]
        for basis in BASES:
            for attribution in ATTRIBUTIONS:
                lines.append(f"chosen: {qid} ({basis}) sha256={SHA256} {attribution}")
                lines.append(f"chosen: {qid} ({basis}) {attribution} sha256={SHA256}")
    for outcome, exit_code in OUTCOMES:
        for hint in HINTS:
            lines.append(
                format_summary(
                    outcome=outcome,
                    exit_code=exit_code,
                    elapsed_s=41.26,
                    ignored=(
                        "department=cma_prints(other_source)",
                        "style=impressionism(unsupported_by_source)",
                    ),
                    hint=hint,
                )
            )
    return lines


RUNNER_LINES = _runner_lines()


def test_the_runner_line_sample_is_broad() -> None:
    assert len(RUNNER_LINES) > 500
    assert len(set(RUNNER_LINES)) == len(RUNNER_LINES)


def test_the_runners_ordinary_lines_are_untouched() -> None:
    redactor = Redactor([SUPERVISOR, TV_TOKEN])
    changed = [line for line in RUNNER_LINES if redactor.redact(line) != line]
    assert changed == []


def test_the_runners_ordinary_lines_pass_the_formatter_untouched() -> None:
    formatter = RedactingFormatter(Redactor([SUPERVISOR, TV_TOKEN]))
    for line in RUNNER_LINES:
        record = logging.makeLogRecord(
            {"name": "frame_gallery.app.runner", "levelname": "INFO", "msg": "%s", "args": (line,)}
        )
        assert formatter.format(record).endswith(f" INFO frame_gallery.app.runner: {line}")


# --- new patterns: pathological input ---------------------------------------

BIG = 200_000


def _filled(unit: str) -> str:
    """``unit`` repeated to at least ``BIG`` characters."""
    return unit * (BIG // len(unit) + 1)


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(_filled("('token', "), id="tuple-keys"),
        pytest.param("'token', '" + "a" * BIG, id="tuple-unterminated"),
        pytest.param("('token', '" + _filled("\\'"), id="tuple-escapes"),
        pytest.param("'Authorization'," + " " * BIG + "x", id="tuple-spaces"),
        pytest.param('\\"token\\": \\"' + "\\" * BIG, id="escaped-backslash-run"),
        pytest.param('\\"token\\": \\"' + "\\" * BIG + '"', id="escaped-backslash-quote"),
        pytest.param('\\"token\\": \\"' + _filled("\\\\\\\\x"), id="escaped-fours"),
        pytest.param('\\"token\\": \\"' + _filled('\\\\\\"'), id="escaped-threes"),
        pytest.param("token" + "\\" * BIG + '"', id="escaped-key-close"),
        pytest.param(_filled('\\"token\\": '), id="escaped-keys"),
        pytest.param("token=" + "\\" * BIG + "x", id="unquoted-backslashes"),
        pytest.param("a" + "B" * BIG + "Token=x", id="camel-capitals"),
        pytest.param(_filled("aB") + "=x", id="camel-humps"),
        pytest.param(_filled("accessToken"), id="camel-keys"),
        pytest.param("%41" + "a" * BIG, id="camel-after-percent"),
        pytest.param(_filled("aBcDeFgHiJ "), id="camel-words"),
        pytest.param(_filled("token%3D"), id="percent-keys"),
        pytest.param("token%3D" + _filled("%2"), id="percent-value"),
        pytest.param(_filled("%3F") + "token%3Dx", id="percent-run"),
        pytest.param(_filled("%3Ftoken"), id="percent-no-separator"),
        pytest.param("Bearer " + "a" * BIG + "=" * 1_000 + "b", id="bearer-padding"),
        pytest.param("Bearer " + _filled("a="), id="bearer-pairs"),
        pytest.param(_filled("bearer a= "), id="bearer-repeated"),
        pytest.param("Bearer " + " " * BIG + "=", id="bearer-spaces"),
    ],
)
def test_pathological_input_for_the_new_patterns_is_fast(text: str) -> None:
    assert len(text) >= BIG
    started = time.perf_counter()
    Redactor([SECRET]).redact(text)
    assert time.perf_counter() - started < 1.0
