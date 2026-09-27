"""History and the shared field rules (store/history.py, store/fields.py, §13.3)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from frame_gallery.domain import QUALIFIED_ID_MAX_LENGTH, is_qualified_id
from frame_gallery.store.atomic import DocumentFile, Origin, Quarantine, open_directory
from frame_gallery.store.fields import parse_qualified_id, parse_timestamp, timestamp_text
from frame_gallery.store.history import (
    HISTORY_FILE,
    HISTORY_SPEC,
    MAX_BYTES,
    MAX_ENTRIES,
    HistoryEntry,
    append_bounded,
    history_document,
    parse_history,
)

T0 = datetime(2026, 9, 27, 12, 0, 0, tzinfo=UTC)


def entry(number: int, *, minutes: int = 0) -> HistoryEntry:
    return HistoryEntry(f"aic:{number}", T0 + timedelta(minutes=minutes))


class TestFields:
    def test_timestamps_are_utc_with_whole_seconds(self) -> None:
        moment = datetime(2026, 9, 27, 14, 30, 5, 999_000, tzinfo=timezone(timedelta(hours=2)))
        assert timestamp_text(moment) == "2026-09-27T12:30:05+00:00"

    def test_a_naive_timestamp_is_refused(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            timestamp_text(datetime(2026, 9, 27))  # noqa: DTZ001 - the point of the test

    def test_timestamps_round_trip(self) -> None:
        assert parse_timestamp(timestamp_text(T0)) == T0
        assert parse_timestamp("2026-09-27T14:00:00+02:00") == T0

    @pytest.mark.parametrize(
        "value",
        [None, 12, "", "yesterday", "2026-09-27", "2026-09-27T12:00:00", "2" * 41],
    )
    def test_invalid_timestamps_are_refused(self, value: object) -> None:
        with pytest.raises(ValueError, match=r"."):
            parse_timestamp(value)

    @pytest.mark.parametrize(
        "value",
        [
            "0001-01-01T00:00:00+05:00",
            "9999-12-31T23:00:00-05:00",
            "9999-12-31T00:00:00+00:00",
            "1999-12-31T23:59:59+00:00",
            "9000-01-01T00:00:00+00:00",
        ],
    )
    def test_timestamps_out_of_range_are_refused(self, value: str) -> None:
        """Review finding: dates at the limits of datetime overflowed later."""
        with pytest.raises(ValueError, match="out of range"):
            parse_timestamp(value)

    def test_the_range_limits(self) -> None:
        assert parse_timestamp("2000-01-01T00:00:00+00:00").year == 2000
        assert parse_timestamp("8999-12-31T23:59:59+00:00").year == 8999

    @pytest.mark.parametrize("value", ["aic:1", "cma:94979", "local:fp:" + "a" * 64])
    def test_qualified_identifiers_are_accepted(self, value: str) -> None:
        assert parse_qualified_id(value) == value
        assert is_qualified_id(value)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            "",
            "aic",
            "aic:",
            ":1",
            "AIC:1",
            "a:1",
            "aic:1 2",
            "aic:-1",
            "aic:" + "1" * (QUALIFIED_ID_MAX_LENGTH - 3),
        ],
    )
    def test_invalid_identifiers_are_refused(self, value: object) -> None:
        assert not is_qualified_id(value)
        with pytest.raises(ValueError, match="invalid identifier"):
            parse_qualified_id(value)

    def test_the_longest_identifier_is_accepted(self) -> None:
        assert is_qualified_id("aic:" + "1" * (QUALIFIED_ID_MAX_LENGTH - 4))


class TestHistoryDocument:
    def test_the_documented_format(self) -> None:
        document = history_document([entry(1), entry(2, minutes=1)])
        assert document == {
            "format": "frame-gallery-history",
            "version": 1,
            "entries": [
                {"id": "aic:1", "at": "2026-09-27T12:00:00+00:00"},
                {"id": "aic:2", "at": "2026-09-27T12:01:00+00:00"},
            ],
        }
        assert parse_history(document) == (entry(1), entry(2, minutes=1))

    def test_a_repeated_identifier_keeps_its_last_position(self) -> None:
        document = history_document([entry(1), entry(2, minutes=1), entry(1, minutes=2)])
        assert parse_history(document) == (entry(2, minutes=1), entry(1, minutes=2))

    def test_unknown_fields_are_ignored(self) -> None:
        document = history_document([entry(1)])
        document["note"] = "from a later build"
        entries = document["entries"]
        assert isinstance(entries, list)
        entries[0]["extra"] = True
        assert parse_history(document) == (entry(1),)

    @pytest.mark.parametrize(
        ("entries", "message"),
        [
            (None, "entries is not a list"),
            ({"id": "aic:1"}, "entries is not a list"),
            (["aic:1"], "an entry is not an object"),
            ([{"id": "aic 1", "at": "2026-09-27T12:00:00+00:00"}], "invalid identifier"),
            ([{"id": "aic:1"}], "invalid timestamp"),
            ([{"id": "aic:1", "at": "2026-09-27T12:00:00"}], "time zone"),
        ],
    )
    def test_invalid_content_is_refused(self, entries: object, message: str) -> None:
        with pytest.raises(ValueError, match=message):
            parse_history({"format": "frame-gallery-history", "version": 1, "entries": entries})

    def test_more_entries_than_the_bound_are_refused(self) -> None:
        entries = [{"id": f"aic:{n}", "at": "2026-09-27T12:00:00+00:00"} for n in range(20_001)]
        with pytest.raises(ValueError, match="more than 20000 entries"):
            parse_history({"entries": entries})


class TestBounds:
    def test_the_bounds_are_the_documented_ones(self) -> None:
        assert MAX_ENTRIES == 20_000
        assert MAX_BYTES == 5 * 1024 * 1024
        assert HISTORY_SPEC.max_bytes == MAX_BYTES

    def test_append_keeps_order_and_moves_a_repeat_to_the_end(self) -> None:
        entries = (entry(1), entry(2), entry(3))
        assert append_bounded(entries, entry(2, minutes=5)) == (
            entry(1),
            entry(3),
            entry(2, minutes=5),
        )

    def test_the_oldest_go_first_at_the_entry_bound(self) -> None:
        entries = tuple(entry(n) for n in range(5))
        result = append_bounded(entries, entry(99), max_entries=3)
        assert [e.qualified_id for e in result] == ["aic:3", "aic:4", "aic:99"]

    def test_a_single_entry_bound_keeps_only_the_new_entry(self) -> None:
        result = append_bounded((entry(1), entry(2)), entry(3), max_entries=1)
        assert result == (entry(3),)

    def test_the_oldest_go_first_at_the_byte_bound(self) -> None:
        entries = tuple(entry(n) for n in range(10, 20))
        one = len(json.dumps(history_document([entry(10)]), separators=(",", ":")))
        per_entry = len(json.dumps(history_document([entry(10), entry(11)]), separators=(",", ":")))
        per_entry -= one
        limit = one + 3 * per_entry
        result = append_bounded(entries, entry(99), max_bytes=limit)
        assert [e.qualified_id for e in result] == ["aic:17", "aic:18", "aic:19", "aic:99"]
        encoded = json.dumps(history_document(result), separators=(",", ":"))
        assert len(encoded) == limit

    def test_the_new_entry_is_kept_even_alone_over_the_byte_bound(self) -> None:
        assert append_bounded((entry(1),), entry(2), max_bytes=10) == (entry(2),)

    def test_a_full_history_of_the_longest_identifiers_fits_the_byte_bound(self) -> None:
        """20 000 entries of 200-character identifiers stay under 5 MiB, so the
        entry bound is the one that binds in practice."""
        long_id = "cma:" + "9" * (QUALIFIED_ID_MAX_LENGTH - 4)
        entries = [HistoryEntry(f"{long_id[:-5]}{n:05d}", T0) for n in range(MAX_ENTRIES)]
        result = append_bounded(entries[:-1], entries[-1])
        assert len(result) == MAX_ENTRIES
        encoded = json.dumps(history_document(result), separators=(",", ":")).encode()
        assert len(encoded) <= MAX_BYTES


class TestHistoryFile:
    def test_restart_reads_what_was_written(self, tmp_path: Path) -> None:
        """F4: history survives a restart (a new process opens the same file)."""
        with open_directory(tmp_path, ("state",), create=True) as directory:
            DocumentFile(directory, HISTORY_FILE, HISTORY_SPEC, backup=True).write(
                history_document([entry(1), entry(2)])
            )
        with open_directory(tmp_path, ("state",)) as directory:
            result = DocumentFile(directory, HISTORY_FILE, HISTORY_SPEC, backup=True).load()
        assert result.origin is Origin.PRIMARY
        assert result.value == (entry(1), entry(2))

    def test_a_corrupt_history_is_recovered_from_its_backup(self, tmp_path: Path) -> None:
        """F5: a corrupt history is quarantined and recovered, without a crash."""
        with open_directory(tmp_path, ("state",), create=True) as directory:
            file = DocumentFile(directory, HISTORY_FILE, HISTORY_SPEC, backup=True)
            file.write(history_document([entry(1)]))
            file.write(history_document([entry(1), entry(2)]))
        (tmp_path / "state" / HISTORY_FILE).write_bytes(b'{"format": "frame-gallery-hist')
        with open_directory(tmp_path, ("state",)) as directory:
            quarantine = Quarantine(directory, lambda: T0)
            result = DocumentFile(
                directory, HISTORY_FILE, HISTORY_SPEC, backup=True, quarantine=quarantine
            ).load()
        assert result.origin is Origin.BACKUP
        assert result.value == (entry(1),)
        assert len(list((tmp_path / "state" / "quarantine").iterdir())) == 1
