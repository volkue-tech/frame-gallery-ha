"""Optional attribution: bounded helper state and preview publication ordering."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from frame_gallery.app.artwork_info import artwork_info
from frame_gallery.app.outcomes import Outcome
from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.options import ConfigError, parse_options
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY
from frame_gallery.errors import PublishError
from frame_gallery.imaging.contract import DeliveryArtifact
from frame_gallery.providers.contract import Attribution
from frame_gallery.tv.port import DeliveryStatus, Marker
from tests.support.fakes import make_candidate
from tests.unit.app.harness import Harness

HELPER = "input_text.frame_gallery_artwork"


@pytest.mark.parametrize(
    ("provider", "museum"),
    [
        ("aic", "Art Institute of Chicago"),
        ("cma", "Cleveland Museum of Art"),
        ("local", "Local images"),
        ("other", ""),
    ],
)
def test_labels_only_come_from_known_provider_keys(provider: str, museum: str) -> None:
    candidate = replace(
        make_candidate("1"),
        provider_key=provider,
        attribution=Attribution(
            title="Test title", creator="Test artist", credit_line="Not a museum"
        ),
    )
    assert json.loads(artwork_info(candidate)) == {
        "title": "Test title",
        "artist": "Test artist",
        "museum": museum,
    }


@pytest.mark.parametrize(
    ("title", "artist"),
    [
        (None, None),
        ("", ""),
        (" ", "\n\t"),
        ('"' * 300, "\\" * 300),
        ("🎨" * 300, "É" * 300),
        ("x" * 400, "y" * 400),
        ("short", '"' * 300),
        ('"' * 300, "short"),
        ("a\ud800b\u202ec\x00d", "<script>**literal**</script>"),
    ],
)
def test_metadata_is_plain_bounded_round_trip_text(title: str | None, artist: str | None) -> None:
    candidate = replace(make_candidate("1"), attribution=Attribution(title=title, creator=artist))
    value = artwork_info(candidate)
    assert len(value) <= 255
    assert value.encode("utf-8").decode("utf-8") == value
    data = json.loads(value)
    assert set(data) == {"title", "artist", "museum"}
    assert all(isinstance(text, str) for text in data.values())
    assert all("\n" not in text for text in data.values())
    if title is None or not title.strip():
        assert data["title"] == ""
    if artist is None or not artist.strip():
        assert data["artist"] == ""
    if title == "a\ud800b\u202ec\x00d":
        assert data["title"] == "a b c d"
        assert data["artist"] == artist  # escaping belongs to the card, not invented metadata


@pytest.mark.parametrize("value", [None, "", HELPER])
def test_optional_helper_configuration(value: str | None) -> None:
    options = parse_options(
        {"tv_host": "10.0.0.5", "artwork_info_helper": value},
        vocabulary=BUILTIN_VOCABULARY,
        excluded_networks=(),
    )
    assert options.artwork_info_helper == (value or None)


@pytest.mark.parametrize(
    "value",
    [
        True,
        123,
        "sensor.x",
        "input_text.X",
        "input_text.x,input_text.y",
        "input_text.x\n",
        "input_text." + "x" * 65,
    ],
)
def test_other_targets_are_rejected(value: object) -> None:
    with pytest.raises(ConfigError, match="artwork_info_helper"):
        parse_options(
            {"tv_host": "10.0.0.5", "artwork_info_helper": value},
            vocabulary=BUILTIN_VOCABULARY,
            excluded_networks=(),
        )


def test_filter_helpers_cannot_be_overwritten() -> None:
    with pytest.raises(ConfigError, match="dedicated"):
        parse_options(
            {"tv_host": "10.0.0.5", "artwork_info_helper": HELPER, "source_helper": HELPER},
            vocabulary=BUILTIN_VOCABULARY,
            excluded_networks=(),
        )


def test_no_extra_work_without_the_option(tmp_path: Path) -> None:
    h = Harness(tmp_path)
    h.write_artwork_info = lambda *_args: pytest.fail("metadata must stay optional")
    assert h.run().outcome is Outcome.DELIVERED
    assert h.preview.published == h.tv.payloads


@pytest.mark.parametrize("failure", ["none", "clear", "preview", "write", "expired"])
def test_clear_preview_write_order_and_failure_safety(tmp_path: Path, failure: str) -> None:
    candidate = replace(
        make_candidate("1"), attribution=Attribution(title="New work", creator="New artist")
    )
    h = Harness(tmp_path, candidates=[candidate])
    h.options.raw["artwork_info_helper"] = HELPER
    calls: list[tuple[str, str, Deadline]] = []
    helper_state = ["Previous artwork"]
    if failure == "preview":
        h.preview.error = PublishError("injected preview failure")
    if failure == "expired":
        original_publish = h.preview.publish

        def slow_publish(artifact: DeliveryArtifact, deadline: Deadline) -> None:
            h.clock.advance(2.1)
            original_publish(artifact, deadline)

        h.preview.publish = slow_publish  # type: ignore[method-assign]

    def write(entity: str, value: str, deadline: Deadline) -> bool:
        calls.append((entity, value, deadline))
        h.events.append("info.write" if value else "info.clear")
        if (
            (failure == "clear" and not value)
            or (failure == "write" and value)
            or deadline.expired()
        ):
            return False
        helper_state[0] = value
        return True

    h.write_artwork_info = write
    result = h.run()
    assert "state.record_history" in h.events
    assert h.records.current
    assert all(entity == HELPER for entity, _value, _deadline in calls)
    assert calls[0][1] == ""
    if failure == "clear":
        assert helper_state == ["Previous artwork"]
        assert not h.preview.published
        assert "preview.publish" not in h.events
    elif failure == "preview":
        assert helper_state == [""]
        assert len(calls) == 1
    else:
        assert h.preview.published == h.tv.payloads
        assert h.events.before("info.clear", "preview.publish")
        assert h.events.before("preview.publish", "info.write")
        assert calls[0][2] is calls[1][2]  # one shared budget, not two restarted budgets
        assert (helper_state == [""]) == (failure in ("write", "expired"))
        if failure == "none":
            assert json.loads(helper_state[0])["title"] == "New work"
    assert result.outcome is (
        Outcome.DELIVERED if failure == "none" else Outcome.DELIVERED_WITH_WARNINGS
    )


def test_no_match_and_failed_tv_preserve_metadata(tmp_path: Path) -> None:
    for index, no_match in enumerate((True, False)):
        directory = tmp_path / str(index)
        directory.mkdir()
        h = Harness(directory, candidates=[] if no_match else None)
        h.options.raw["artwork_info_helper"] = HELPER
        h.write_artwork_info = lambda *_args: pytest.fail("old metadata must not be touched")
        if not no_match:
            h.tv.status = DeliveryStatus.UNREACHABLE
            h.tv.markers = []
        result = h.run()
        assert result.outcome in (Outcome.NO_MATCH, Outcome.TV_UNREACHABLE)
        assert not h.preview.published


def test_missing_publisher_retains_the_previous_preview(tmp_path: Path) -> None:
    h = Harness(tmp_path)
    h.options.raw["artwork_info_helper"] = HELPER
    assert h.run().outcome is Outcome.DELIVERED_WITH_WARNINGS
    assert not h.preview.published


def test_stop_after_tv_selection_leaves_existing_information_untouched(tmp_path: Path) -> None:
    h = Harness(tmp_path)
    h.options.raw["artwork_info_helper"] = HELPER
    h.write_artwork_info = lambda *_args: pytest.fail("stopped publication must not clear metadata")

    def stop_after_selected(marker: Marker) -> None:
        if marker is Marker.SELECTED:
            h.cancellation.request_stop()

    h.tv.during = stop_after_selected
    result = h.run()
    assert result.outcome is Outcome.DELIVERED_WITH_WARNINGS
    assert h.state.history
    assert not h.preview.published
    assert h.records.last_run
