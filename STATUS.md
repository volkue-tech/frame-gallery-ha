# Project status

Last updated: 2026-09-27

## Current phase

**Phase 2 (core skeleton, deterministic selection and rendering): complete, awaiting the Phase 3 gate.**

- Codex gave final approval of Phase 1 at commit `dda877c` and authorized Phase 2 only. The gate adjustment for the remaining `pillow.libs` entries is recorded in commit `63ebbc8`.
- Phase 2 is implemented, tested, independently reviewed, and fixed. The decisions it proposes are D-141 to D-145.
- Codex independently reran the complete Phase 2 quality gate on 2026-09-27: Ruff and strict mypy passed, all 2,755 tests passed, and total line and branch coverage was 100%.
- The local history was rewritten before publication so every commit uses the personal identity `Alexander Wilke <volkue@gmail.com>`. The repository-local Git configuration enforces the same identity for future commits.
- Nothing contacted Home Assistant, the television, a provider API, or GitHub. Nothing was published or pushed. Phase 3 has not started.

## Completed

### Phase 0: specification package (Codex)

- Created the isolated repository.
- Recorded the product requirements.
- Defined the independent-development boundaries.
- Wrote the acceptance tests.
- Wrote the agent instructions.
- Defined the phases and approval gates.

### Phase 1, revision 1: architecture proposal (Claude, commit `d42adf5`)

- Researched permitted sources only, with independent re-checks.
- Ran an internal multi-agent review; 58 confirmed findings were incorporated.
- Wrote `ARCHITECTURE.md` and the first `DECISIONS.md` (decisions, inventory, risks, questions).

### Phase 1, revision 2: Codex review applied (Claude, commit `9352e77`)

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
- An IPv4 literal for the TV address (D-125). The test value `192.168.178.30` is never hard-coded.
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

### Phase 1, final gate corrections: Codex final gate review of `9352e77` applied (Claude, commit `dda877c`)

**Pillow licensing correction**

- The earlier claim that the Pillow PyPI wheels omit `libimagequant` was false and has been withdrawn.
- The Pillow 12.3.0 wheels bundle GPL-3.0-or-later `libimagequant` 4.4.1 and LGPL-2.1-or-later FriBiDi 1.0.16 (with its shim). The full bundled-library inventory from the Codex inspection is recorded in `DECISIONS.md`. The remaining `pillow.libs` entries are marked for verification.
- Apache-2.0 covers project-owned code only (D-102). The runtime image is **not** GPL-free.
- `libimagequant` and FriBiDi are added to the copyleft review (D-135). The qualified licence review stays a release gate, and R-25 records the risk.
- Pillow 12.3.0 stays proposed. The inspection will be repeated against the exact runtime wheels once the Python version is fixed; that result is authoritative (D-130, `TASKS.md` Phase 6).

**Development-only rows**

- `mypy-extensions` 1.1.0 (MIT) and `pathspec` 1.1.1 (MPL-2.0) were recorded; neither is shipped.

**Decisions accepted**

- Q-03 (D-116): square band 0.95–1/0.95; strict near-16:9 is ±1 %, `abs(ln(r / (16/9))) <= ln(1.01)` (about 1.760–1.796); maximum upscale 2.5×. The strict threshold may be revisited after Phase 8.
- Q-11 (D-117): fallback only with landscape-only and `contain`; no fallback in `cover`.
- Q-12 (D-125): RFC 1918 IPv4 literals only; link-local, loopback, unspecified, multicast, broadcast, and the container and Supervisor networks are rejected. `192.168.178.30` is used only as the Phase 8 test value.
- Q-23 (D-137): a 30-day uncertainty quarantine.
- Q-18 item 4 (D-113): history is recorded before the preview is published.
- Q-09 (§16.3, D-114, D-140): the UI card, script, 150 s timer helper, enabled Running sensor, and optional post-run automation.
- Q-08 (D-120, D-123): the Art Institute of Chicago is the default remote source.
- Q-04 (D-118): the candidate fingerprint.

**Specification amendments**

- `PRODUCT_SPEC.md`: the RFC 1918 address rule, lifecycle steps 9 and 10 swapped, the strict ±1 % definition, and the 30-day quarantine. Each change is recorded in its amendment log.
- `ACCEPTANCE_TESTS.md`: B7 reworded in place for RFC 1918. No IDs changed.

### Phase 2: core skeleton, deterministic selection and rendering (Claude, commit `36cda3d`)

**Project and tooling** (D-142)

- The Python project lives in `frame_gallery/`: `src/frame_gallery/`, `tests/`, `pyproject.toml`, `uv.lock`, `requirements/runtime.txt` (hash-pinned, exported from the lock), `scripts/check.sh`, and `DEVELOPMENT.md`.
- `uv` 0.12.19 was installed from PyPI into the git-ignored `.tools/`, with its wheel hash checked against PyPI. The locked development environment is `frame_gallery/.venv`, also git-ignored, as are the caches and coverage data.
- The locked versions match the inventory: Pillow 12.3.0; pytest 9.1.1, pytest-cov 7.1.0, coverage 7.16.1, Ruff 0.16.9, mypy 2.3.1, and their recorded dependencies.
- Local interpreter: CPython 3.12.14, the only Python 3.12+ on this machine (bundled with the local Codex desktop runtime). No interpreter was downloaded.
- `THIRD_PARTY_NOTICES.md` is started as a provisional notice. It lists Pillow and its known bundled libraries, including GPL-3.0-or-later `libimagequant` and LGPL-2.1-or-later FriBiDi, marks the nine `pillow.libs` entries as pending Phase 6 verification, and lists the development tools. It states that the runtime is not GPL-free.

**Implemented**

- *Core types and ports:* value types, errors, the injected clock and random source, the provider, exclusion-store, image-executor, and television ports, and the runner's other ports.
- *Budget:* the 120 s phase calculator (10 / 60 / 40 / 10 s), the content window (discovery at most 30 s, 2 s PRE-STAGE reserve), allowances, clamped deadlines, and the watchdog (130 s).
- *Configuration:* option parsing with the accepted defaults; RFC 1918-only television addresses with injected container networks; the vocabulary mechanism (the built-in lists are provisional and empty until Phase 3, D-143); the capability matrix; helper merging; and visible reporting of unsupported filters.
- *Selection:* exclusions, exact-arithmetic shape and 16:9 rules, the 2.5× upscale limit, the shortlist of two, fallback only with landscape-only and `contain`, seeded tie-breaks, separate remote-probe and local-inspection allowances, and explicit end reasons.
- *Image preparation* behind the in-process executor: a bounded header pre-scan, JPEG (including MPO) and PNG only, dimension and pixel limits, EXIF orientation, mode and colour-key handling, ICC-to-sRGB conversion, `contain` and `cover`, an exact 3840 × 2160 baseline JPEG with no metadata, and the q85 fallback. The parent validates the result and computes its SHA-256.
- *Orchestrator skeleton* against fakes: every stage, outcome classification (§4.2, §12.4), deadline propagation, stop-request handling (§7.6), and settling and FINISH on every path.
- *Logging:* redaction (known secrets and credential patterns), UTC formatting, and the summary line.
- *Isolation seam:* the bytes-only JSON channel and the in-process executor. The process executor comes in Phase 5.

**Quality gates** (`scripts/check.sh`, run for this commit):

- Ruff check and format: clean.
- `mypy --strict` over `src` and `tests`: clean.
- pytest: **2 755 passed**, with **100 % line and branch coverage overall** (3 741 statements, 742 branches). The architecture's 100 % gate for `budget`, `selection`, `isolation`, `providers`, the outcome classification, the runner, and the imaging worker, pre-scan, and JPEG header parser also passes (2 400 statements, 476 branches).
- The architecture boundary test (D-107, D-145) and the whole-session network guard (H2) are active.

**Independent review.** Five lenses, each with a skeptical verifier: 75 findings, 61 confirmed (about 30 distinct issues), 12 refuted, and 2 uncertain. All confirmed findings are fixed with regression tests, or recorded as decisions (see *Review records* in `DECISIONS.md`).

**Re-verification.**

- The original reproductions were re-run against the fixes, and adversarial sweeps looked for regressions.
- The sweeps found two remaining stop-request windows, TIFF-directory bombs in image metadata, and redaction bypasses. All are fixed (D-141, D-144, D-145).
- The final design passes exhaustive stop-request sweeps with no violations: a stop request, direct or as a real SIGTERM, at every Python function entry (11 641 points) and every traced line (5 429 points).

## Specification deviations still awaiting decision

Proposed in Phase 2, for approval at the Phase 3 gate:

| Item | Where |
| --- | --- |
| Port shapes that differ from §9.1 and §12.1 (central capability matrix and rights allowlist; `DimensionProbe` instead of `probe_ref`; token handling inside the Phase 5 adapter) | D-141 |
| `deadline_exceeded` also covers a CONFIGURE overrun; an adapter failure after `selected` gives `delivered_with_warnings` | D-141 |
| The summary-line key is `ignored_filters=` (§19 amended to match §9.2 and D-124) | D-141 |
| Lock and export workflow: `uv.lock` plus `uv export`, instead of `uv pip compile` | D-142, amends D-128 |
| The built-in vocabulary is empty until Phase 3, so any filter other than `any` is `config_invalid` | D-143 |

## Next action

The user and Codex review Phase 2 (architecture conformance and independence), then either approve Phase 3 or request changes.

**Decisions needed, by phase:**

| Before | Decisions |
| --- | --- |
| Phase 3 | The Phase 2 decisions D-141 to D-145. Q-14, Q-22. The `urllib3` and `certifi` rows. Any observation requests. |
| Phase 4 | None (Q-23 and D-113 accepted). |
| Phase 5 | The `samsungtvws` row and its LGPL-3.0 obligations (D-135). |
| Phase 6 | The base-image pull (D-130); Q-06, Q-10; the Buildx, QEMU, and SBOM-tool rows. The authoritative Pillow runtime-wheel inspection, including the remaining `pillow.libs` entries (mandatory before packaging or publication). |
| Phase 8 | Explicit approval for the live run; Q-21 (install route). |
| Phase 9 | D-101 (final name), Q-13 (repository URL); the builder-action and Cosign rows; the qualified licence review (D-135, release gate); approval to publish. |

## External state

- No Home Assistant changes; no `configuration.yaml` touched.
- No television connection attempted.
- No GitHub repository accessed, created, or modified; no GitHub-hosted page fetched.
- No container image pulled, built, or published.
- Dependencies were installed only into the git-ignored project environment (`frame_gallery/.venv`) and the git-ignored `.tools/` directory, from PyPI (`pypi.org`, `files.pythonhosted.org`) only. Nothing else was installed or modified on the machine.
- No provider API or image endpoint called. Research read public documentation pages, policy pages, and `robots.txt` files, plus one Microsoft Q&A answer (cited as a non-documentation source) and search-result snippets where a page blocked automated readers. Reading used web-fetch tools, `curl` (including PyPI's JSON metadata API), and the in-app browser.
- Apache-2.0 is approved. The `LICENSE` file will be added when publication is prepared (Phase 9).

## Known open decisions

See `DECISIONS.md` for the full list. The most material:

- **Preview freshness mechanism** (D-140). This is release-blocking and is selected in Phase 8.
- **Copyleft components in the runtime image** (R-25, D-135). The Pillow wheels bundle GPL-3.0-or-later `libimagequant` and LGPL-2.1-or-later FriBiDi. The qualified licence review is a release gate.
- **Final name** (D-101). The trademark wording is tracked as R-14.
- **Copyleft source-availability mechanism** (D-135).
- **Phase 2 proposals** (D-141 to D-145), listed above.
- **Local tests versus the runtime build** (R-26): the full suite runs inside the container in Phase 6.
- **No pre-emption before Phase 5** (R-27): the process executor with its kill timer arrives in Phase 5.
