# Project status

Last updated: 2026-09-27 (Phase 4 gate)

## Current phase

**Phase 4 (bounded state and duplicate prevention): complete. Stopped at the Phase 4 gate for the Codex review. Phase 5 has not started.**

- The user authorized Phase 4 on 2026-09-27. The Phase 3 gate had passed the same day.
- The proposed decisions D-153 to D-159 await the gate.
- Every commit uses the personal identity `Alexander Wilke <volkue@gmail.com>`.
- Nothing contacted Home Assistant, the Home Assistant Green, the television, a provider API, or GitHub. Nothing was published or pushed. The local backup branch was not touched. Every test uses synthesized data.

### Phase 4 progress

| Step | Commit |
| --- | --- |
| 1. Atomic write primitive, reader and quarantine, and history (D-153) | `a74ba1c` |
| 2. TV-upload ledger and the file state store (D-154) | `1677ccd` |
| 3. Workspace lifecycle, startup sweep, and store layout (D-155) | `f347ffb` |
| 4. Bounded, persistent metadata cache (D-156) | `4fcab6e` |
| 5. Exhausted-page hints and the once-per-run cache write (D-157) | `b8a6c44` |
| 6. Atomic preview publication and the run records (D-158) | `5435d06` |
| 6a. Fixes from the internal review of steps 1 to 3 (D-153 to D-155 amendments) | `bb25277` |
| 7. End-to-end state scenarios E7–E10, with a real SIGKILL (D-159; D-156 amended) | `ec9e8a4` |
| 7a. Fixes from the second internal review (D-153, D-157, D-158, and D-159 amendments) | `86cc82b` |
| 8. Status, tasks, README, and development notes for the gate | this commit |

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

### Phase 3: provider adapters (Claude, commits `09d7c46` to `979ef8a`; gate passed 2026-09-27)

**Implemented**

- *Documentation re-check* (D-146). Only the two official documentation pages were read. Consequences:
  - the Art Institute supports only the period filter in the beta, and takes image sizes from its Images resource;
  - Cleveland's 21 departments are confirmed verbatim, and it sends an explicit `limit` on every request.
- *Guarded gateway* (`net/`, D-108, D-115, D-131, D-147):
  - exact host policies, HTTPS on 443, public addresses only, a connection pinned to the validated IP with SNI and a post-handshake TLS and peer check;
  - at most 3 re-validated redirects; pacing; the 401/403/429 stop; the single metadata retry;
  - byte caps with one gzip layer, per-request totals enforced by a socket-shutdown timer, and the metadata allowance;
  - only `net/transport.py` imports `socket`, `ssl`, `http.client`, `urllib3`, and `certifi`.
- *Helper reader* (`ha/client.py`, D-112, D-148): one read per helper, the token sent only to a private Supervisor address inside the container's own networks, 3 s and 64 KiB per read, and the `state` string only, with the static fallback (B3–B5).
- *Local media* (`providers/local_media.py`, D-149):
  - a bounded scan through `O_NOFOLLOW` folder descriptors, with every folder and file pinned by device and inode;
  - the D-118 fingerprint, the three preview guards (F7), and one aggregated warning;
  - a header-only `inspect` worker task;
  - a guarded copy for delivery, and an empty-library hint.
- *Art Institute* (`providers/aic.py`, D-150) and *Cleveland* (`providers/cma.py`, D-151): the documented APIs only, CC0 works only, every record re-checked, the documented renditions only (IIIF `1686,`; the Cleveland print JPEG, never the TIFF), random pages without replacement, and the counts cached behind a cache port.
- *Vocabulary version 1* (D-152): 12 curated Cleveland departments and 5 periods, documented in `frame_gallery/VOCABULARY.md`, which a test keeps identical to the code. The capability matrix is narrowed for the Art Institute.
- *Tests:*
  - the shared contract suite for all three adapters;
  - end-to-end runs through the real adapters, gateway, and fetcher over synthesized APIs;
  - real HTTP-stack tests over a local socket pair.

**Dependencies.** `urllib3` 2.8.0 (MIT) and `certifi` 2026.7.22 (MPL-2.0) were installed from PyPI into the git-ignored environment only. Their installed metadata was checked, and they are recorded in the lock, `requirements/runtime.txt`, the inventory, and `THIRD_PARTY_NOTICES.md`.

**Quality gates** (`frame_gallery/scripts/check.sh`, run for the closing commit):

- Ruff check and format: clean.
- `mypy --strict` over `src` and `tests`: clean.
- pytest: **3 454 passed**, with **100 % line and branch coverage overall** (5 458 statements, 1 162 branches).
- The architecture's 100 % gate, now including `net` and `ha`, also passes (4 037 statements, 884 branches).

**Independent reviews.** Two reviewers checked the gateway (`51d9cf3`) and the helper reader and local media (`f614256`, `8761cca`). They found 11 defects, all verified, and all are fixed with regression tests in `9b736f3` and `37e85d0`. The most serious:

- the transport's time bounds did not hold after a `Connection: close` response;
- a symbolic-link swap during discovery could reach a file outside the library.

Writing the real-stack tests exposed one more transport defect, which is fixed too. See *Review records* in `DECISIONS.md`.

**Commits**

| Step | Commit |
| --- | --- |
| 1. Documentation re-check and the approved decisions (D-146; `ARCHITECTURE.md` §8.3, §9.2, §9.5, §9.6, §10, §15.2, §23) | `09d7c46` |
| 2. Guarded network gateway and the `urllib3` and `certifi` dependencies (D-147) | `51d9cf3` |
| 3. Home Assistant helper reader (D-148) | `f614256` |
| 4. Local media provider (D-149) | `8761cca` |
| 4a. Fixes from the internal review of the gateway (D-147 amendment) | `9b736f3` |
| 5. Art Institute of Chicago adapter (D-150) | `571a210` |
| 6. Cleveland Museum of Art adapter (D-151) | `72dba4a` |
| 6a. Fixes from the internal review of the helper reader and local media (D-147, D-148, D-149 amendments) | `37e85d0` |
| 7. Vocabularies, shared contract tests, and closing documentation (D-152) | `979ef8a` |
| Gate. Phase 3 gate decision: Q-25 resolved with option (a); D-146 to D-152 accepted; `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` (B2, C1) amended | `b6578d8` |

**Documentation re-check (D-146).** On 2026-09-27 the two official documentation pages were re-read in the in-app browser. No endpoint was called and nothing was recorded from a live response.

- *Cleveland:* the parameters, the response fields, the print JPEG, the CDN host, and the 21 departments are confirmed verbatim. The adapter sets `limit` on every request (the default is 1000), leaves out the one department whose name contains commas, and enforces period bounds on `creation_date_earliest`, because the inclusivity of `created_after` and `created_before` is undocumented.
- *Art Institute:* the search, count, pagination, courtesy, IIIF, and Images resource facts are confirmed. The documentation does **not** name the department or style values, the members of the colour object, or the members of the artwork `thumbnail`. Under the user's Q-14 instruction, the Art Institute therefore supports only the period filter in the beta, and it reads image sizes from the documented Images resource instead of the thumbnail. **Q-25** is resolved with option (a) at the Phase 3 gate: this stays so for the first beta, which ships without a colour filter, and no observation is approved.

### Phase 4: bounded state and duplicate prevention (Claude, commits `a74ba1c` to `86cc82b` and the closing documentation commit; awaiting the gate)

**Implemented** (the new `store` package, standard library only)

- *Atomic primitive and reader* (D-153):
  - every write works relative to a directory descriptor: `O_DIRECTORY | O_NOFOLLOW` directories, `O_EXCL` temporary files, `fsync`, `.bak` through a hard link, rename, and directory `fsync`;
  - a self-check reads each document back with the reader's own rules before it is written;
  - the reader tries the primary, then `.bak`, then empty, with a quarantine of at most three files;
  - a newer version, or a file that cannot be read, ends the run with `state_error` before the television is touched.
- *History* (D-153): at most 20 000 entries and 5 MiB, the oldest dropped first. It changes only after `selected` (E10).
- *Upload ledger and state store* (D-154):
  - the write-ahead `uncertain` intent is committed durably before the television is contacted;
  - it is promoted on `uploaded`, and removed only without `upload_started` or on an explicit refusal;
  - the 30-day quarantine; an entry is pruned once both copies of history hold its work;
  - at most 20 000 entries and 5 MiB; the `flock` lock (`already_running`).
- *Workspace and sweep* (D-155): `/tmp/frame-gallery/run-<random>/{in,out}` at mode 0700, removed on every path. The startup sweep runs after the lock and removes only our own temporary files and leftover run directories.
- *Metadata cache and hints* (D-156, D-157):
  - `/data/cache/<provider>.json` holds counts and exhausted-page hints: at most 1 000 entries, 2 MiB, 8 KiB per entry, and 7 days, least recently used first, written once per run in FINISH;
  - the Art Institute and Cleveland adapters skip, for 7 days, pages whose works were all sent already;
  - a run whose skipped pages leave nothing new gets the hint "nothing new left for these filters".
- *Preview and records* (D-158):
  - the preview is the television payload, read again and hashed, and written atomically at mode 0644 below `/media/frame_gallery/preview`, with every path component checked;
  - `current.json` keeps the fingerprints of the last 10 previews for the local library's guard 3 (F7); `last_run.json` records every run; both are at most 16 KiB.
- *Runner and wiring:*
  - PRE-STAGE, RECORD, and PUBLISH run against the real store;
  - the runner tells the adapters which works are excluded for good (history and uploads) for their hints, reports skipped pages, and writes the provider's cache once in FINISH;
  - `StoreLayout` builds every store port from the `/data`, `/media`, and `/tmp` anchors for the Phase 6 entry point.

**Tests** (D-159):

- unit tests with failure injection on every system-call path of the store;
- E7–E10 end to end over the real store, with a fake television that emits its progress markers;
- E9 also with a real SIGKILL of a child process at four points (after the intent, after `uploaded`, after `selected`, and inside the promotion write);
- F1–F7; a full and a read-only `/data`; newer and damaged files;
- the cache across runs, with the real Art Institute adapter over the synthesized API.

**Quality gates** (`frame_gallery/scripts/check.sh`, run for the closing commit):

- Ruff check and format: clean.
- `mypy --strict` over `src` and `tests`: clean.
- pytest: **3 850 passed**, with **100 % line and branch coverage overall** (6 834 statements, 1 416 branches).
- The architecture's 100 % gate, now including `store`, also passes (5 376 statements, 1 134 branches).

**Independent reviews.**

- The store commits (`a74ba1c`, `1677ccd`, `f347ffb`): 7 findings (2 medium, 5 low) and 3 test gaps, all fixed with regression tests in `bb25277`. The most serious: timestamps at the limits of `datetime` would have ended every run as `internal_error`, and pruning could lose the newest delivery's exclusion after the history primary was damaged.
- The later commits (`4fcab6e` to `ec9e8a4`): no high-severity finding and no path to a duplicate upload; 6 low findings, all fixed with regression tests in `86cc82b`. The most material: hints rested on quarantined works and on pages that offered nothing, so a work could stay hidden beyond its quarantine and a run could wrongly report "nothing new left".
- The end-to-end cache test found that a clock step back of a few seconds discarded every full-length hint; fixed in `ec9e8a4`.

See *Review records* in `DECISIONS.md`.

## Specification deviations

Every Phase 3 deviation was accepted at the Phase 3 gate. The Phase 4 deviations below are proposed and await the Phase 4 gate; `ARCHITECTURE.md` is not amended before they are accepted.

| Proposed item | Where |
| --- | --- |
| The ledger prunes only when an intent is committed, and only works that both copies of history hold (§13.6 step 5 says: on the next ledger write, once the work is in history). This is stricter: a damaged history primary can never lose the newest delivery's exclusion. | D-154 |
| The reader also quarantines files that are not regular or exceed the size bound (§13.2: "only parse or schema failures"). A file that exists but cannot be read, or one written by a newer version, ends the run with `state_error` instead of falling back to `.bak` or an empty state. | D-153 |
| After a failed directory `fsync` that follows a successful rename, an intent is an error (`state_error`, stricter), while recorded history, a promotion, the preview, and the records count as written, with a warning. | D-153, D-154, D-158 |
| Adapters receive a predicate for the works excluded for good (history or `uploaded`), for the exhausted-page hints only, and still yield every candidate (§9.1). A page is hinted only if it offered works and all of them were sent already. Skipped pages lead to the hint "nothing new left for these filters" (an extension of §4.2), and `last_run.json` reports them. | D-157 |
| The metadata cache is written once per run in FINISH, before the last-run record (§4.1 names only the last-run record there). An expiry more than 7 days ahead is cut to 7 days from now. | D-156, D-157 |
| Internal dependencies beyond §5: `store` uses `selection.exclusion`, `imaging.contract`, and `budget`; `providers.cache` imports `store.cache` (as §5 lists). `WorkspacePaths` moves to `domain.py`, `PublishError` to `errors.py`, the qualified-identifier rule to `domain.py`, and the D-118 fingerprint to the shared `fingerprint.py`; `DeliveryArtifact` gains `fingerprint`. | D-153, D-155, D-156, D-158 |
| Timestamps in state files must lie from 2000 to 8999, and later versions must keep writing `format` and `version` first. | D-153 |
| `in/` and `out/` have mode 0700 until Phase 5 sets the modes that the unprivileged worker needs (§11.3). The preview file is `latest.jpg` until Phase 8 chooses the refresh mechanism (D-140). | D-155, D-158 |

## Next action

The Codex review at the Phase 4 gate. Phase 5 does not start before it is explicitly authorized.

**Decisions needed, by phase:**

| Before | Decisions |
| --- | --- |
| Phase 4 gate | D-153 to D-159 and the deviations above. |
| Phase 5 | Authorization to start; the `samsungtvws` row and its LGPL-3.0 obligations (D-135). E7–E10 are run again with the process-based television worker. |
| Phase 6 | The base-image pull (D-130); Q-06, Q-10; the Buildx, QEMU, and SBOM-tool rows. The authoritative Pillow runtime-wheel inspection, including the remaining `pillow.libs` entries (mandatory before packaging or publication). The option descriptions state the capability matrix, including that no source supports colour yet (B8). The entry point wires the store from `StoreLayout`. |
| Phase 8 | Explicit approval for the live run, which is also the first live request to the museums and the first time the project contact is transmitted (Q-22); Q-21 (install route). The live check of the Art Institute `params` form (D-150). The preview refresh mechanism and file names (D-140). |
| Phase 9 | D-101 (final name), Q-13 (repository URL, which also replaces the contact in the User-Agent, D-119); the builder-action and Cosign rows; the qualified licence review (D-135, release gate); approval to publish. |

## External state

- No Home Assistant changes; no `configuration.yaml` touched.
- No television connection attempted.
- No GitHub repository accessed, created, or modified; no GitHub-hosted page fetched.
- No container image pulled, built, or published.
- Dependencies were installed only into the git-ignored project environment (`frame_gallery/.venv`) and the git-ignored `.tools/` directory, from PyPI (`pypi.org`, `files.pythonhosted.org`) only. Nothing else was installed or modified on the machine.
- No provider API or image endpoint called. The Phase 3 re-check read only the two official documentation pages (D-146). Every provider test uses synthesized documents (`tests/support/museums.py`); nothing was recorded from a live API.
- Phase 3 installed `urllib3` 2.8.0 and `certifi` 2026.7.22 from PyPI into the git-ignored project environment only.
- The two internal reviewers worked only inside the repository and without network access, using local files and a socket pair. One of them once ran `grep` on the standard library's `http/client.py`, which lives with the local interpreter outside the repository. That is language source, not predecessor material, and the disclosure is recorded in `DECISIONS.md`.
- Earlier research (Phases 1 and 2) read public documentation pages, policy pages, and `robots.txt` files, plus one Microsoft Q&A answer (cited as a non-documentation source) and search-result snippets where a page blocked automated readers. Reading used web-fetch tools, `curl` (including PyPI's JSON metadata API), and the in-app browser.
- Phase 4 worked only in the repository, in temporary directories created by the tests, and in this session's scratch directory. The SIGKILL tests start child processes of the project interpreter on this machine. No dependency was added.
- The two Phase 4 reviewers worked on `git archive` snapshots in the session's scratch directory, without network access, and changed nothing in the repository.
- Apache-2.0 is approved. The `LICENSE` file will be added when publication is prepared (Phase 9).

## Known open decisions

See `DECISIONS.md` for the full list. The most material:

- **Preview freshness mechanism** (D-140). This is release-blocking and is selected in Phase 8.
- **Copyleft components in the runtime image** (R-25, D-135). The Pillow wheels bundle GPL-3.0-or-later `libimagequant` and LGPL-2.1-or-later FriBiDi. The qualified licence review is a release gate.
- **Final name** (D-101). The trademark wording is tracked as R-14.
- **Copyleft source-availability mechanism** (D-135).
- **Local tests versus the runtime build** (R-26): the full suite runs inside the container in Phase 6.
- **No pre-emption before Phase 5** (R-27): the process executor with its kill timer arrives in Phase 5.
