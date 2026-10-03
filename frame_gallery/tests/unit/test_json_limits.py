"""JSON byte bounds must not depend on CPython's parser recursion behaviour."""

from __future__ import annotations

import json

import pytest

from frame_gallery.json_limits import MAX_JSON_NESTING_DEPTH, check_json_nesting


@pytest.mark.parametrize(("opening", "closing"), [(b"[", b"]"), (b'{"a":', b"}")])
def test_exact_container_depth_is_accepted_and_next_level_is_refused(
    opening: bytes, closing: bytes
) -> None:
    maximum = opening * MAX_JSON_NESTING_DEPTH + b"0" + closing * MAX_JSON_NESTING_DEPTH
    check_json_nesting(maximum)
    assert json.loads(maximum) is not None
    with pytest.raises(ValueError, match="nested too deeply"):
        check_json_nesting(opening + maximum + closing)


@pytest.mark.parametrize(
    "value", ["[" * 100_000, "}" * 100_000, 'escaped " quote [', "backslash \\" + "[", "é[]{}"]
)
def test_string_contents_and_escapes_do_not_count_as_nesting(value: str) -> None:
    data = json.dumps({"value": value}, ensure_ascii=False).encode()
    check_json_nesting(data)
    assert json.loads(data) == {"value": value}


@pytest.mark.parametrize("data", [b"", b"0", b"true", b"null", b"{", b"}", b'"unclosed'])
def test_scanner_is_not_a_replacement_for_the_syntax_parser(data: bytes) -> None:
    check_json_nesting(data)
