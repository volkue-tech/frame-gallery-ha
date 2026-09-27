# Project status

Last updated: 2026-09-27

## Current phase

**Phase 3 (provider adapters): in progress.**

- The user approved Phase 3 on 2026-09-27. D-141 to D-145 and the Phase 3 decisions D-108, D-112, D-115, D-124, D-127, D-131, D-134, D-132, and D-136 (adapter details) are accepted; D-119 is accepted with an amendment; Q-14 and Q-22 are resolved; `urllib3` 2.8.0 and `certifi` 2026.7.22 are approved.
- Phase 2 was independently re-run by Codex on 2026-09-27: Ruff and strict mypy passed, all 2,755 tests passed, and total line and branch coverage was 100%.
- Every commit uses the personal identity `Alexander Wilke <volkue@gmail.com>`, which the repository-local Git configuration also enforces.
- Nothing contacted Home Assistant, the television, a provider API, or GitHub. Nothing was published or pushed.

### Phase 3 progress

| Step | Commit |
| --- | --- |
| 1. Documentation re-check and the approved decisions (D-146; `ARCHITECTURE.md` §8.3, §9.2, §9.5, §9.6, §10, §15.2, §23) | `09d7c46` |
| 2. Guarded network gateway and the `urllib3` and `certifi` dependencies (D-147) | `51d9cf3` |
| 3. Home Assistant helper reader (D-148) | `f614256` |
| 4. Local media provider (D-149) | `8761cca` |
| 4a. Fixes from the internal review of the gateway (D-147 amendment) | `9b736f3` |
| 5. Art Institute of Chicago adapter (D-150) | this commit |
| 6. Cleveland Museum of Art adapter | pending |
| 7. Vocabularies, shared contract tests, and closing documentation | pending |

**Documentation re-check (D-146).** On 2026-09-27 the two official documentation pages were re-read in the in-app browser. No endpoint was called and nothing was recorded from a live response.

- *Cleveland:* the parameters, the response fields, the print JPEG, the CDN host, and the 21 departments are confirmed verbatim. The adapter sets `limit` on every request (the default is 1000), leaves out the one department whose name contains commas, and enforces period bounds on `creation_date_earliest`, because the inclusivity of `created_after` and `created_before` is undocumented.
- *Art Institute:* the search, count, pagination, courtesy, IIIF, and Images resource facts are confirmed. The documentation does **not** name the department or style values, the members of the colour object, or the members of the artwork `thumbnail`. Under the user's Q-14 instruction, the Art Institute therefore supports only the period filter in the beta, and it reads image sizes from the documented Images resource instead of the thumbnail. **Q-25** asks whether to keep this for the beta or to approve a one-time observation that would allow curated department and style lists.

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

| Item | Where |
| --- | --- |
| The Art Institute supports only the period filter in the beta: its department and style values and its colour members are undocumented. No source supports a colour filter in the beta, which narrows acceptance items B2 and C1 to the filters a source supports. | D-146, Q-25 |

## Next action

Continue Phase 3 with step 6 (Cleveland Museum of Art adapter), then stop at the Phase 3 gate for the Codex review.

**Decisions needed, by phase:**

| Before | Decisions |
| --- | --- |
| Phase 3 gate | D-146 and Q-25 (Art Institute filters in the beta). The Phase 3 implementation decisions proposed at the end of the phase. |
| Phase 4 | None (Q-23 and D-113 accepted). |
| Phase 5 | The `samsungtvws` row and its LGPL-3.0 obligations (D-135). |
| Phase 6 | The base-image pull (D-130); Q-06, Q-10; the Buildx, QEMU, and SBOM-tool rows. The authoritative Pillow runtime-wheel inspection, including the remaining `pillow.libs` entries (mandatory before packaging or publication). |
| Phase 8 | Explicit approval for the live run; Q-21 (install route). |
| Phase 9 | D-101 (final name), Q-13 (repository URL, which also replaces the contact in the User-Agent, D-119); the builder-action and Cosign rows; the qualified licence review (D-135, release gate); approval to publish. |

## External state

- No Home Assistant changes; no `configuration.yaml` touched.
- No television connection attempted.
- No GitHub repository accessed, created, or modified; no GitHub-hosted page fetched.
- No container image pulled, built, or published.
- Dependencies were installed only into the git-ignored project environment (`frame_gallery/.venv`) and the git-ignored `.tools/` directory, from PyPI (`pypi.org`, `files.pythonhosted.org`) only. Nothing else was installed or modified on the machine.
- No provider API or image endpoint called. The Phase 3 re-check read only the two official documentation pages (D-146). Research read public documentation pages, policy pages, and `robots.txt` files, plus one Microsoft Q&A answer (cited as a non-documentation source) and search-result snippets where a page blocked automated readers. Reading used web-fetch tools, `curl` (including PyPI's JSON metadata API), and the in-app browser.
- Apache-2.0 is approved. The `LICENSE` file will be added when publication is prepared (Phase 9).

## Known open decisions

See `DECISIONS.md` for the full list. The most material:

- **Preview freshness mechanism** (D-140). This is release-blocking and is selected in Phase 8.
- **Copyleft components in the runtime image** (R-25, D-135). The Pillow wheels bundle GPL-3.0-or-later `libimagequant` and LGPL-2.1-or-later FriBiDi. The qualified licence review is a release gate.
- **Final name** (D-101). The trademark wording is tracked as R-14.
- **Copyleft source-availability mechanism** (D-135).
- **Art Institute filters in the beta** (D-146, Q-25), listed above.
- **Local tests versus the runtime build** (R-26): the full suite runs inside the container in Phase 6.
- **No pre-emption before Phase 5** (R-27): the process executor with its kill timer arrives in Phase 5.
