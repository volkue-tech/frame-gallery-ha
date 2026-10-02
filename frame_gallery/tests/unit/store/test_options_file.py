"""The options file the Supervisor writes (store/options_file.py; §15.1, §17.5)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.config.options import HELPER_OPTION_NAMES, ConfigError
from frame_gallery.store.options_file import MAX_OPTIONS_BYTES, OPTIONS_NAME, OptionsFile
from tests.support.clock import FakeClock


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def deadline(clock: FakeClock, seconds: float = 10.0) -> Deadline:
    return Deadline(clock, clock.monotonic() + seconds, "configure")


def write(data: Path, content: bytes | str) -> Path:
    data.mkdir(exist_ok=True)
    path = data / OPTIONS_NAME
    path.write_bytes(content.encode() if isinstance(content, str) else content)
    return path


def message(error: pytest.ExceptionInfo[ConfigError]) -> str:
    (issue,) = error.value.issues
    assert issue.option == "options"
    return issue.message


def test_the_supervisor_options_are_returned_as_written(tmp_path: Path, clock: FakeClock) -> None:
    options = {"tv_host": "10.0.0.5", "source": "local_media", "landscape_only": False}
    write(tmp_path, json.dumps(options))
    assert OptionsFile(tmp_path).load(deadline(clock)) == options


def test_the_file_is_read_once(tmp_path: Path, clock: FakeClock) -> None:
    path = write(tmp_path, '{"tv_host": "10.0.0.5"}')
    source = OptionsFile(tmp_path)
    first = source.load(deadline(clock))
    path.write_text('{"tv_host": "10.0.0.6"}')
    assert source.load(deadline(clock)) is first


def test_a_missing_file_tells_the_user_to_save_the_options(
    tmp_path: Path, clock: FakeClock
) -> None:
    with pytest.raises(ConfigError) as error:
        OptionsFile(tmp_path).load(deadline(clock))
    assert "Configuration tab" in message(error)


def test_a_failure_is_remembered(tmp_path: Path, clock: FakeClock) -> None:
    source = OptionsFile(tmp_path)
    with pytest.raises(ConfigError):
        source.load(deadline(clock))
    write(tmp_path, '{"tv_host": "10.0.0.5"}')
    with pytest.raises(ConfigError):
        source.load(deadline(clock))


def test_a_missing_data_directory_is_unreadable(tmp_path: Path, clock: FakeClock) -> None:
    with pytest.raises(ConfigError) as error:
        OptionsFile(tmp_path / "absent").load(deadline(clock))
    assert message(error) == "The options file cannot be read."


def test_a_symbolic_link_is_not_followed(tmp_path: Path, clock: FakeClock) -> None:
    target = tmp_path / "elsewhere.json"
    target.write_text('{"tv_host": "10.0.0.5"}')
    data = tmp_path / "data"
    data.mkdir()
    (data / OPTIONS_NAME).symlink_to(target)
    with pytest.raises(ConfigError) as error:
        OptionsFile(data).load(deadline(clock))
    assert message(error) == "The options file is not a regular file."


def test_an_oversize_file_is_refused(tmp_path: Path, clock: FakeClock) -> None:
    padding = " " * MAX_OPTIONS_BYTES
    write(tmp_path, '{"tv_host": "10.0.0.5"}' + padding)
    with pytest.raises(ConfigError) as error:
        OptionsFile(tmp_path).load(deadline(clock))
    assert message(error) == "The options file is larger than 64 KiB."


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads files of any mode")
def test_an_unreadable_file_is_reported(tmp_path: Path, clock: FakeClock) -> None:
    path = write(tmp_path, '{"tv_host": "10.0.0.5"}')
    path.chmod(0)
    with pytest.raises(ConfigError) as error:
        OptionsFile(tmp_path).load(deadline(clock))
    assert message(error) == "The options file cannot be read."


@pytest.mark.parametrize(
    "content",
    [b"{", b'{"tv_host": NaN}', b'{"x": 1e400}', b"\xff\xfe{}", b""],
    ids=["truncated", "nan", "infinite", "not-utf8", "empty"],
)
def test_text_that_is_not_strict_json_is_refused(
    tmp_path: Path, clock: FakeClock, content: bytes
) -> None:
    write(tmp_path, content)
    with pytest.raises(ConfigError) as error:
        OptionsFile(tmp_path).load(deadline(clock))
    assert message(error) == "The options file is not valid JSON."


@pytest.mark.parametrize("content", ["[]", '"tv_host"', "null", "3"])
def test_a_document_that_is_not_an_object_is_refused(
    tmp_path: Path, clock: FakeClock, content: str
) -> None:
    write(tmp_path, content)
    with pytest.raises(ConfigError) as error:
        OptionsFile(tmp_path).load(deadline(clock))
    assert "does not hold an object" in message(error)


def test_an_expired_deadline_stops_the_read(tmp_path: Path, clock: FakeClock) -> None:
    write(tmp_path, '{"tv_host": "10.0.0.5"}')
    expired = deadline(clock, 1.0)
    clock.advance(2.0)
    with pytest.raises(DeadlineExceeded):
        OptionsFile(tmp_path).load(expired)


@pytest.mark.parametrize("name", HELPER_OPTION_NAMES)
def test_any_set_helper_counts_as_configured(tmp_path: Path, name: str) -> None:
    write(tmp_path, json.dumps({"tv_host": "10.0.0.5", name: "input_select.frame_gallery"}))
    assert OptionsFile(tmp_path).helpers_configured()


@pytest.mark.parametrize("value", [None, ""])
def test_unset_helpers_do_not_count(tmp_path: Path, value: str | None) -> None:
    options = {"tv_host": "10.0.0.5", **dict.fromkeys(HELPER_OPTION_NAMES, value)}
    write(tmp_path, json.dumps(options))
    assert not OptionsFile(tmp_path).helpers_configured()


def test_an_invalid_helper_value_still_counts(tmp_path: Path) -> None:
    """The parser rejects it later (config_invalid); until then the token is kept."""
    write(tmp_path, json.dumps({"tv_host": "10.0.0.5", "color_helper": 3}))
    assert OptionsFile(tmp_path).helpers_configured()


def test_no_helper_is_configured_without_a_readable_file(tmp_path: Path) -> None:
    assert not OptionsFile(tmp_path).helpers_configured()


def test_the_helper_names_follow_the_filter_fields() -> None:
    assert HELPER_OPTION_NAMES == (
        "source_helper",
        "department_helper",
        "style_helper",
        "color_helper",
    )
