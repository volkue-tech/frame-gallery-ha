"""Run-record builders (§13.1)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from frame_gallery.app.outcomes import Outcome
from frame_gallery.app.records import (
    CURRENT_FORMAT,
    LAST_RUN_FORMAT,
    MAX_TEXT_LENGTH,
    AttemptNote,
    RunStats,
    build_current_record,
    build_last_run_record,
)
from frame_gallery.config.filters import (
    EffectiveFilters,
    FilterChoice,
    FilterDimension,
    FilterField,
    FilterSet,
    IgnoredFilter,
    IgnoreReason,
    Provenance,
)
from frame_gallery.domain import SourceKey
from frame_gallery.providers.contract import Attribution
from frame_gallery.selection.shortlist import DiscoveryEnd, SelectionResult, SelectionStats

START = datetime(2026, 3, 1, 8, 0, 0, tzinfo=UTC)
END = datetime(2026, 3, 1, 8, 0, 42, tzinfo=UTC)


def _filters() -> EffectiveFilters:
    requested = FilterSet(
        source=SourceKey.CLEVELAND_MUSEUM_OF_ART,
        department=FilterChoice("cma_test_prints", Provenance.HELPER),
        style=FilterChoice("style_test_one"),
        source_provenance=Provenance.HELPER,
    )
    return EffectiveFilters(
        source=SourceKey.CLEVELAND_MUSEUM_OF_ART,
        department="cma_test_prints",
        style=None,
        period=None,
        color=None,
        ignored=(
            IgnoredFilter(
                field=FilterField.STYLE,
                dimension=FilterDimension.STYLE,
                key="style_test_one",
                reason=IgnoreReason.UNSUPPORTED_BY_SOURCE,
                provenance=Provenance.STATIC,
            ),
        ),
        requested=requested,
    )


def test_last_run_record_for_a_no_match_run_is_json_and_complete() -> None:
    stats = RunStats(
        selection=SelectionResult(
            entries=(),
            end=DiscoveryEnd.EXHAUSTED,
            stats=SelectionStats(candidates_seen=4, excluded=1, rejected={"too_small": 3}),
        ),
        attempts=[AttemptNote("cma:1", "strict", "not_found")],
    )
    record = build_last_run_record(
        outcome=Outcome.NO_MATCH,
        hint="filters too restrictive",
        started_at=START,
        finished_at=END,
        elapsed_s=42.04,
        filters=_filters(),
        stats=stats,
        artwork_id=None,
    )
    json.dumps(record)  # serializable
    assert record["format"] == LAST_RUN_FORMAT
    assert record["version"] == 1
    assert record["outcome"] == "no_match"
    assert record["exit_code"] == 0
    assert record["started_at"] == "2026-03-01T08:00:00+00:00"
    assert record["elapsed_s"] == 42.0
    assert record["filters"] == {
        "source": "cleveland_museum_of_art",
        "source_provenance": "helper",
        "applied": {"department": "cma_test_prints"},
        "provenance": {"department": "helper", "style": "static", "color": "static"},
    }
    assert record["ignored_filters"] == [
        {
            "filter": "style",
            "value": "style_test_one",
            "reason": "unsupported_by_source",
            "provenance": "static",
        }
    ]
    stats_record = record["stats"]
    assert isinstance(stats_record, dict)
    assert stats_record["attempts"] == [{"id": "cma:1", "basis": "strict", "result": "not_found"}]
    assert stats_record["selection"]["candidates_seen"] == 4
    assert stats_record["selection"]["rejected"] == {"too_small": 3}


def test_last_run_record_before_filters_are_known() -> None:
    record = build_last_run_record(
        outcome=Outcome.CONFIG_INVALID,
        hint=None,
        started_at=START,
        finished_at=END,
        elapsed_s=0.01,
        filters=None,
        stats=RunStats(),
        artwork_id=None,
    )
    assert record["filters"] is None
    assert record["ignored_filters"] == []
    assert record["stats"] == {"attempts": []}


def test_current_record_bounds_untrusted_text() -> None:
    long_title = "T" * 1000
    record = build_current_record(
        qualified_id="aic:42",
        attribution=Attribution(title=long_title, creator="A", date_text=None),
        sha256="ab" * 32,
        delivered_at=END,
        preview_fingerprint="cd" * 32,
    )
    json.dumps(record)
    assert record["format"] == CURRENT_FORMAT
    attribution = record["attribution"]
    assert isinstance(attribution, dict)
    assert len(attribution["title"]) == MAX_TEXT_LENGTH
    assert attribution["date"] is None
    assert record["delivered_at"] == "2026-03-01T08:00:42+00:00"
    assert record["preview_fingerprints"] == ["cd" * 32]
