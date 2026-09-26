# Project status

Last updated: 2026-09-26

## Current phase

**Phase 1 (independent architecture proposal), revision 2.**

The Codex review of commit `8ea5491` conditionally accepted the architecture. This revision applies the user's decisions and the review's corrections, and it changes documentation only.

**Phase 2 is not yet approved.** No application code has been written, no dependency installed, and nothing has been contacted or published.

## Completed

### Phase 0: specification package (Codex)

- Created the isolated repository.
- Recorded the product requirements.
- Defined the independent-development boundaries.
- Wrote the acceptance tests.
- Wrote the agent instructions.
- Defined the phases and approval gates.

### Phase 1, revision 1: architecture proposal (Claude, commit `8ea5491`)

- Researched permitted sources only, with independent re-checks.
- Ran an internal multi-agent review; 58 confirmed findings were incorporated.
- Wrote `ARCHITECTURE.md` and the first `DECISIONS.md` (decisions, inventory, risks, questions).

### Phase 1, revision 2: Codex review applied (Claude, this commit)

**Beta providers**

- Google Arts & Culture and Bing are removed from the beta. Their researched status is kept in `ARCHITECTURE.md` §9.4 and in the new *Researched and excluded sources* section of `PRODUCT_SPEC.md`.
- The beta sources are now **local media, the Art Institute of Chicago, and the Cleveland Museum of Art**.
- Cleveland is part of the normative design (D-136). Only CC0 records are used, and only the documented 3400 px print JPEG, never the TIFF.

**Filters**

- Four distinct filters: source/museum, department/collection, style/period, and colour.
- A capability matrix shows which source supports which filter.
- Unsupported filters are visibly reported in the log, the summary line, and the run record (D-124).

**Runtime**

- A **120 s** default hard deadline, split 10 / 60 / 40 / 10 s, with all timeouts clamped.
- `no_match` finishes within **70 s**.
- A 150 s dashboard timer indicator.
- 30 remote dimension requests, and a separate allowance for local header reads (D-114).

**Duplicate prevention**

- A **TV-upload exclusion ledger** with a write-ahead uncertainty quarantine (D-137).
- The confirmed sent history, the current artwork, and the preview still change only after the TV confirms selection.
- New acceptance items `E7`–`E10`.

**Preview**

- The Local File camera stays the primary design, and its platform basis is recorded (D-111).
- Freshness is **release-blocking**: Phase 8 must prove one refresh mechanism (D-140).
- Collection Image (2026.9+) is an optional alternative only, and does not raise the minimum Home Assistant version.

**Approved decisions recorded**

- `frame_gallery` as the provisional identifier (D-138).
- Apache-2.0 (D-102).
- `uv` (D-128).
- An IPv4 literal for the TV address (D-125); the accepted ranges are still proposed (Q-12). The test value `192.168.178.30` is never hard-coded.
- No `host_network` initially (Q-16).
- Inspect only the installed `samsungtvws` 3.0.6 (D-104).
- `contain`, landscape-only, and strict 16:9 on by default, with no crop (D-123).
- Bounded cleanup and atomic writes (D-106, D-110).
- Beta scope (D-120), including its three sources (D-132, D-136); the adapter details are still proposed.
- The top-level budget (D-114): 120 s total, split 10/60/40/10, `no_match` within 70 s, 30 remote probes. The sub-budgets are proposed.

**Implementation sequencing**

- A vertical slice (D-139). `TASKS.md` Phases 2–9 are restructured to match.

**Specification amendments**

- `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` are amended as directed, each with an amendment log.
- Unrelated text is preserved.
- New acceptance items are appended, so existing IDs stay stable.

**Research and checks**

- The Cleveland Open Access and Home Assistant preview options were researched from documentation pages only. Key facts were independently re-checked; the citation guidance and the refresh cadence were not.
- Cross-reference and consistency checks were run, followed by an independent review of this revision.

## Specification deviations still awaiting decision

| Item | Where |
| --- | --- |
| History recorded before the preview is published (lifecycle steps 9 and 10). Duplicate prevention no longer depends on this order. | D-113, Q-18 item 4 |

## Next action

The user and Codex review revision 2, then either approve Phase 2 or request changes.

**Decisions needed, by phase:**

| Before | Decisions |
| --- | --- |
| Phase 2 | This revision (the Phase 2 gate). Q-03 (thresholds), Q-11 (fallback in `cover` mode), and the remaining part of Q-12 (IPv4 ranges). Development-only dependencies, once the `mypy-extensions` and `pathspec` SPDX IDs are recorded. The Pillow row, once its bundled-library table is verified from the pinned wheels. |
| Phase 3 | Q-04, Q-14, Q-22. The `urllib3` and `certifi` rows. Any observation requests. |
| Phase 4 | Q-23 (quarantine period) and Q-18 item 4 (D-113). |
| Phase 5 | The `samsungtvws` row and its LGPL-3.0 obligations (D-135). |
| Phase 6 | The base-image pull (D-130); Q-06, Q-08, Q-09, Q-10; the Buildx, QEMU, and SBOM-tool rows. |
| Phase 8 | Explicit approval for the live run; Q-21 (install route). |
| Phase 9 | D-101 (final name), Q-13 (repository URL); the builder-action and Cosign rows; approval to publish. |

## External state

- No Home Assistant changes; no `configuration.yaml` touched.
- No television connection attempted.
- No GitHub repository accessed, created, or modified; no GitHub-hosted page fetched.
- No container image pulled, built, or published.
- No dependency installed.
- No provider API or image endpoint called. Research read public documentation pages, policy pages, and `robots.txt` files, plus one Microsoft Q&A answer (cited as a non-documentation source) and search-result snippets where a page blocked automated readers. Reading used web-fetch tools, `curl` (including PyPI's JSON metadata API), and the in-app browser.
- Apache-2.0 is approved. The `LICENSE` file will be added when publication is prepared (Phase 9).

## Known open decisions

See `DECISIONS.md` for the full list. The most material:

- **Preview freshness mechanism** (D-140). This is release-blocking and is selected in Phase 8.
- **Lifecycle order** (D-113, Q-18 item 4).
- **Uncertainty-quarantine period** (Q-23). Proposed: 30 days.
- **Loading indicator** (Q-09). The timer-driven indicator makes the `G1` deliverable card + script + timer helper, plus a post-run automation if needed. The Running sensor's latency is measured in Phase 8.
- **Final name** (D-101). The trademark wording is tracked as R-14.
- **Copyleft source-availability mechanism** (D-135).
