"""Allowances and per-request limits (§7.2, D-114).

The count allowances and per-request timeouts below are proposed values that
Phases 2, 5, and 8 confirm by measurement (D-114). The 30 remote dimension
requests are accepted (Q-20).
"""

from __future__ import annotations

from typing import Final

SHORTLIST_SIZE: Final = 2
"""Candidates that may be fully downloaded and prepared."""

CANDIDATE_ALLOWANCE: Final = 150
"""Candidates evaluated after exclusion."""

METADATA_REQUEST_ALLOWANCE: Final = 15
"""Provider metadata requests per run."""

REMOTE_PROBE_ALLOWANCE: Final = 30
"""Remote requests made only to learn an image's dimensions (accepted, Q-20)."""

LOCAL_DIRECTORY_ENTRY_ALLOWANCE: Final = 20_000
LOCAL_DIRECTORY_DEPTH: Final = 4
LOCAL_INSPECTION_ALLOWANCE: Final = 300
"""Local header inspections: a separate allowance from the remote probes."""

LOCAL_INSPECTION_S: Final = 2.0
"""One local header inspection in the worker (§8.3), clamped to discovery."""

METADATA_REQUEST_S: Final = 10.0
PROBE_REQUEST_S: Final = 5.0
DOWNLOAD_REQUEST_S: Final = 20.0
HELPER_REQUEST_S: Final = 3.0
CONNECT_S: Final = 5.0
READ_S: Final = 10.0
DNS_S: Final = 3.0
