"""The TV-upload exclusion ledger (store/upload_ledger.py, §13.6, D-137)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from frame_gallery.store.upload_ledger import (
    LEDGER_SPEC,
    MAX_BYTES,
    MAX_ENTRIES,
    QUARANTINE_PERIOD,
    LedgerEntry,
    LedgerState,
    bounded,
    excluded_ids,
    ledger_document,
    parse_ledger,
    promoted,
    pruned,
    with_intent,
    without_intent,
)

T0 = datetime(2026, 9, 27, 12, 0, 0, tzinfo=UTC)
UPLOADED = LedgerState.UPLOADED
UNCERTAIN = LedgerState.UNCERTAIN


def at(days: float = 0) -> datetime:
    return T0 + timedelta(days=days)


def uploaded(number: int, days: float = 0) -> LedgerEntry:
    return LedgerEntry(f"cma:{number}", UPLOADED, at(days))


def uncertain(number: int, days: float = 0) -> LedgerEntry:
    return LedgerEntry(f"cma:{number}", UNCERTAIN, at(days))


def ids(entries: tuple[LedgerEntry, ...]) -> list[str]:
    return [e.qualified_id for e in entries]


class TestDocument:
    def test_the_documented_format(self) -> None:
        document = ledger_document([uploaded(1), uncertain(2, days=1)])
        assert document == {
            "format": "frame-gallery-upload-ledger",
            "version": 1,
            "entries": [
                {"id": "cma:1", "state": "uploaded", "at": "2026-09-27T12:00:00+00:00"},
                {"id": "cma:2", "state": "uncertain", "at": "2026-09-28T12:00:00+00:00"},
            ],
        }
        assert parse_ledger(document) == (uploaded(1), uncertain(2, days=1))

    def test_the_bounds_are_the_documented_ones(self) -> None:
        assert MAX_ENTRIES == 20_000
        assert MAX_BYTES == 5 * 1024 * 1024
        assert LEDGER_SPEC.max_bytes == MAX_BYTES
        assert timedelta(days=30) == QUARANTINE_PERIOD

    @pytest.mark.parametrize(
        ("first", "second", "kept"),
        [
            (uncertain(1, days=1), uploaded(1), uploaded(1)),
            (uploaded(1), uncertain(1, days=1), uploaded(1)),
            (uncertain(1), uncertain(1, days=1), uncertain(1, days=1)),
            (uncertain(1, days=1), uncertain(1), uncertain(1, days=1)),
        ],
    )
    def test_a_repeated_identifier_keeps_its_strongest_entry(
        self, first: LedgerEntry, second: LedgerEntry, kept: LedgerEntry
    ) -> None:
        document = ledger_document([first, uncertain(2), second])
        assert parse_ledger(document) == (uncertain(2), kept)

    @pytest.mark.parametrize(
        ("entries", "message"),
        [
            ("x", "entries is not a list"),
            ([1], "an entry is not an object"),
            ([{"id": "cma:1", "at": "2026-09-27T12:00:00+00:00"}], "invalid state"),
            ([{"id": "cma:1", "state": 1, "at": "2026-09-27T12:00:00+00:00"}], "invalid state"),
            (
                [{"id": "cma:1", "state": "selected", "at": "2026-09-27T12:00:00+00:00"}],
                "invalid state",
            ),
            ([{"id": "cma 1", "state": "uploaded", "at": "2026-09-27T12:00:00+00:00"}], "id"),
            ([{"id": "cma:1", "state": "uploaded", "at": "soon"}], "timestamp"),
        ],
    )
    def test_invalid_content_is_refused(self, entries: object, message: str) -> None:
        with pytest.raises(ValueError, match=message):
            parse_ledger({"entries": entries})

    def test_more_entries_than_the_bound_are_refused(self) -> None:
        entry = {"id": "cma:1", "state": "uploaded", "at": "2026-09-27T12:00:00+00:00"}
        with pytest.raises(ValueError, match="more than 20000"):
            parse_ledger({"entries": [entry] * 20_001})


class TestExclusion:
    def test_uploaded_always_excludes(self) -> None:
        assert uploaded(1).excludes(at(10_000))

    def test_uncertain_excludes_for_exactly_the_quarantine_period(self) -> None:
        entry = uncertain(1)
        assert entry.excludes(at(29.999))
        assert not entry.excludes(at(30))
        assert entry.excludes(at(-5))  # a clock that went back keeps the quarantine

    def test_excluded_ids_split_by_state(self) -> None:
        entries = (uploaded(1), uncertain(2, days=-10), uncertain(3, days=-31))
        assert excluded_ids(entries, T0) == (frozenset({"cma:1"}), frozenset({"cma:2"}))


class TestTransitions:
    def test_pruning_drops_works_in_history_and_expired_intents(self) -> None:
        entries = (uploaded(1), uploaded(2), uncertain(3, days=-31), uncertain(4, days=-1))
        result = pruned(entries, history={"cma:2", "cma:4"}, now=T0)
        assert result == (uploaded(1),)

    def test_an_intent_is_added_at_the_end(self) -> None:
        assert with_intent((uploaded(1),), "cma:2", T0) == (uploaded(1), uncertain(2))

    def test_an_intent_refreshes_an_older_intent(self) -> None:
        result = with_intent((uncertain(2, days=-3), uploaded(1)), "cma:2", T0)
        assert result == (uploaded(1), uncertain(2))

    def test_an_intent_never_downgrades_an_upload(self) -> None:
        entries = (uploaded(2, days=-3), uncertain(1))
        assert with_intent(entries, "cma:2", T0) == entries

    def test_promotion_replaces_the_intent(self) -> None:
        result = promoted((uncertain(2, days=-1), uploaded(1)), "cma:2", T0)
        assert result == (uploaded(1), uploaded(2))

    def test_promotion_without_an_intent_adds_the_upload(self) -> None:
        assert promoted((), "cma:2", T0) == (uploaded(2),)

    def test_removal_takes_only_the_intent(self) -> None:
        assert without_intent((uncertain(2), uploaded(1)), "cma:2") == (uploaded(1),)
        assert without_intent((uploaded(2),), "cma:2") == (uploaded(2),)
        assert without_intent((uploaded(1),), "cma:9") == (uploaded(1),)


class TestBounds:
    def test_within_the_bounds_nothing_changes(self) -> None:
        entries = (uploaded(1), uncertain(2))
        assert bounded(entries, keep="cma:2") == entries

    def test_the_kept_entry_alone_is_never_dropped(self) -> None:
        assert bounded((uncertain(2),), keep="cma:2", max_entries=0) == (uncertain(2),)

    def test_the_oldest_uploaded_entries_go_first(self) -> None:
        entries = (
            uncertain(1, days=-40),
            uploaded(2, days=-5),
            uploaded(3, days=-9),
            uploaded(4, days=-1),
            uncertain(5),
        )
        result = bounded(entries, keep="cma:5", max_entries=3)
        assert ids(result) == ["cma:1", "cma:4", "cma:5"]

    def test_then_the_oldest_uncertain_entries(self) -> None:
        entries = (uncertain(1, days=-2), uploaded(2), uncertain(3, days=-9), uncertain(4))
        result = bounded(entries, keep="cma:4", max_entries=2)
        assert ids(result) == ["cma:1", "cma:4"]

    def test_the_byte_bound_is_exact(self) -> None:
        entries = tuple(uploaded(n, days=n) for n in range(10, 20))
        document = ledger_document(entries)
        size = len(json.dumps(document, separators=(",", ":")))
        per_entry = (size - len(json.dumps(ledger_document(()), separators=(",", ":")))) // 10
        result = bounded(entries, keep="cma:19", max_bytes=size - 2 * per_entry)
        assert ids(result) == [f"cma:{n}" for n in range(12, 20)]
        encoded = json.dumps(ledger_document(result), separators=(",", ":"))
        assert len(encoded) <= size - 2 * per_entry

    def test_a_ledger_of_exactly_the_byte_bound_is_kept(self) -> None:
        entries = tuple(uploaded(n, days=n) for n in range(10, 20))
        size = len(json.dumps(ledger_document(entries), separators=(",", ":")))
        assert bounded(entries, keep="cma:19", max_bytes=size) == entries
        assert len(bounded(entries, keep="cma:19", max_bytes=size - 1)) == 9
