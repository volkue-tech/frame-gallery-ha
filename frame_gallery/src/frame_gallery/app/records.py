"""The run records: ``last_run.json`` and ``current.json`` content (§13.1).

The builders return plain JSON-compatible dictionaries; the store (Phase 4)
writes them atomically and enforces the 16 KiB bound. Records never contain
secrets, the television address, or raw helper values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Final

from frame_gallery.app.outcomes import Outcome
from frame_gallery.config.filters import EffectiveFilters, FilterField
from frame_gallery.providers.contract import Attribution
from frame_gallery.selection.shortlist import SelectionResult

LAST_RUN_FORMAT: Final = "frame-gallery-last-run"
CURRENT_FORMAT: Final = "frame-gallery-current"
RECORD_VERSION: Final = 1
MAX_TEXT_LENGTH: Final = 200


def _text(value: str | None) -> str | None:
    """Bound untrusted text; control characters are stripped by the store's JSON."""
    if value is None:
        return None
    return value[:MAX_TEXT_LENGTH]


def _timestamp(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


@dataclass(slots=True)
class AttemptNote:
    """One ATTEMPT, for diagnostics."""

    qualified_id: str
    basis: str
    result: str
    """``prepared``, ``not_found``, ``transport``, ``deadline``,
    ``rejected:<rule>``, or ``failed:<reason>``."""


@dataclass(slots=True)
class RunStats:
    selection: SelectionResult | None = None
    attempts: list[AttemptNote] = field(default_factory=list)


def _filters_record(filters: EffectiveFilters) -> dict[str, object]:
    requested = filters.requested
    return {
        "source": filters.source.value,
        "source_provenance": requested.source_provenance.value,
        "applied": {dimension.value: key for dimension, key in filters.active().items()},
        "provenance": {
            field.value: requested.choice(field).provenance.value
            for field in (FilterField.DEPARTMENT, FilterField.STYLE, FilterField.COLOR)
        },
    }


def _ignored_record(filters: EffectiveFilters | None) -> list[dict[str, str]]:
    if filters is None:
        return []
    return [
        {
            "filter": ignored.field.value,
            "value": ignored.key,
            "reason": ignored.reason.value,
            "provenance": ignored.provenance.value,
        }
        for ignored in filters.ignored
    ]


def _stats_record(stats: RunStats) -> dict[str, object]:
    record: dict[str, object] = {
        "attempts": [
            {"id": note.qualified_id, "basis": note.basis, "result": note.result}
            for note in stats.attempts
        ]
    }
    selection = stats.selection
    if selection is not None:
        s = selection.stats
        record["selection"] = {
            "end": selection.end.value,
            "shortlisted": len(selection.entries),
            "candidates_seen": s.candidates_seen,
            "excluded": s.excluded,
            "evaluated": s.evaluated,
            "rights_rejected": s.rights_rejected,
            "dims_unavailable": s.dims_unavailable,
            "rejected": dict(sorted(s.rejected.items())),
            "fallback_offered": s.fallback_offered,
            "probes_used": s.probes_used,
            "inspections_used": s.inspections_used,
        }
    return record


def build_last_run_record(
    *,
    outcome: Outcome,
    hint: str | None,
    started_at: datetime,
    finished_at: datetime,
    elapsed_s: float,
    filters: EffectiveFilters | None,
    stats: RunStats,
    artwork_id: str | None,
) -> dict[str, object]:
    """``last_run.json``: written for every outcome except watchdog termination."""
    return {
        "format": LAST_RUN_FORMAT,
        "version": RECORD_VERSION,
        "outcome": outcome.value,
        "exit_code": outcome.exit_code,
        "hint": hint,
        "started_at": _timestamp(started_at),
        "finished_at": _timestamp(finished_at),
        "elapsed_s": round(elapsed_s, 1),
        "filters": None if filters is None else _filters_record(filters),
        "ignored_filters": _ignored_record(filters),
        "stats": _stats_record(stats),
        "artwork": artwork_id,
    }


def build_current_record(
    *, qualified_id: str, attribution: Attribution, sha256: str, delivered_at: datetime
) -> dict[str, object]:
    """``current.json``: the artwork on the television; written only after ``selected``.

    The store (Phase 4) appends ``sha256`` to the list of the last 10 preview
    fingerprints kept in the same file.
    """
    return {
        "format": CURRENT_FORMAT,
        "version": RECORD_VERSION,
        "id": qualified_id,
        "sha256": sha256,
        "delivered_at": _timestamp(delivered_at),
        "attribution": {
            "title": _text(attribution.title),
            "creator": _text(attribution.creator),
            "date": _text(attribution.date_text),
            "credit_line": _text(attribution.credit_line),
            "detail_url": _text(attribution.detail_url),
        },
    }
