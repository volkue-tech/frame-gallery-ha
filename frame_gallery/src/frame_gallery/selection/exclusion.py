"""The exclusion interface (§8.2, §13.6, D-137).

Selection skips every work in the confirmed sent history, every ``uploaded``
ledger entry, and every unexpired ``uncertain`` ledger entry. The persistent
store that provides these sets arrives in Phase 4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ExclusionSet:
    """Qualified identifiers that must never be selected in this run."""

    history: frozenset[str] = field(default_factory=frozenset)
    uploaded: frozenset[str] = field(default_factory=frozenset)
    uncertain: frozenset[str] = field(default_factory=frozenset)
    """Only the ``uncertain`` entries whose quarantine has not expired."""

    def __contains__(self, qualified_id: object) -> bool:
        return (
            qualified_id in self.history
            or qualified_id in self.uploaded
            or qualified_id in self.uncertain
        )

    def __len__(self) -> int:
        return len(self.history | self.uploaded | self.uncertain)

    def excludes_for_good(self, qualified_id: str) -> bool:
        """Excluded for good: in history, or known to be stored on the
        television. An ``uncertain`` work is not, because its quarantine ends."""
        return qualified_id in self.history or qualified_id in self.uploaded


class ExclusionStore(Protocol):
    """Provides the exclusion set for a run."""

    def load_exclusions(self, now: datetime) -> ExclusionSet:
        """The current exclusions. ``now`` decides quarantine expiry.

        Raises ``StateError`` when a state file was written by a newer version.
        """
        ...
