# Implementation plan and approval gates

## 1000 Commons works and single-colour selection (user request, 2026-10-09)

Product scope and acceptance checklist:
[weekend update plan](docs/plans/commons-1000-colour-update.md).
User authorized planning, research and autonomous local work, then clarified
that up to three meaningful colour groups and their shares should be collected
for future combinations. This update exposes only one colour selection.

The 2026-10-10 clarification opens research to illustration, graphic art,
artistic photography and digital works, with artistic merit and recognizable
works/makers prioritized. Contemporary-art prospects need rights to the actual
artwork, not merely the photo. Existing runtime PD/CC0 and format gates remain unchanged.

- [x] Obtain explicit approval to research CC BY/CC BY-SA original works with
  correct attribution and separately checked artwork rights (2026-10-10).
- [ ] Review CC leads separately, retaining exact source/licence/version,
  creator/title, supplied notices and modification/ShareAlike obligations.
  No preview or own-source statement constitutes artwork clearance. Design
  mandatory accessible attribution before admitting these to runtime/release.
  *90 CC previews actually viewed; 21 promising reserves remain separate from
  the accepted count. Full raw notices and source/upload/thumbnail hashes retained;
  the local reserve page is not a runtime attribution implementation.*

- [x] Verify the 400-work baseline and document product scope and acceptance.
  *400 distinct IDs, 299 artist labels, zero colour profiles in the selection
  manifest; no runtime, release or HA/TV change.*
- [x] Complete the repository required reading before technical design/code.
  *All eight required documents read; local pilot boundary recorded in D-212.*
- [x] Pilot colour profiles on 40–60 visually checked baseline works; retain
  full group distributions and source/version evidence, not invented colours.
  *48 visually inspected; provisional v2 calibrated. All 400 baseline profiles
  and a colour-filtered private preview exist; thirteen research tests pass.
  Broader visual calibration remains part of the final catalogue check.*
- [x] Research and visually verify at least 600 additional distinct eligible works,
  keeping the existing width, ratio, rights and reproduction requirements.
  *663 additions retained after stricter source/licence checks and actual
  second-view review. All 5432 checkpoint previews screened,
  all 400 baseline upload pins checked and 307 scoped artwork QIDs retained. Candidate
  counts and temporary network deferrals are not accepted-work counts.*
- [x] Complete source-bound colour profiles and a reviewable preview for all
  1000 accepted works; preserve baseline IDs/pins and deferred research.
  *D-215: exactly 1000 active entries (344 baseline + 656 additions), all with
  source-bound full palettes/distributions/top groups and compact runtime labels.
  Preview defaults to these 1000; held 56 and reserve 7 are separately filterable.
  All 1063 research profiles and the historical 400 manifest are retained.*
- [x] Resolve the selection treatment of the 56 remaining baseline physical-measurement scope prompts before claiming
  1000 genuinely usable complete works. Do not silently repin/remove a baseline
  work or treat an automatic prompt as an established crop.
  *All 400 source revisions/upload pins checked offline; 239 have parsed
  measurements. Four of 60 prompts were individually resolved: three explicitly
  separate frame dimensions and one exact 2.5% boundary artefact, after actual source/preview review; no baseline
  pin or file was changed. Exact source-bound decisions are retained in research.*
  *User reviewed ten examples and explicitly approved temporary local selection
  holds and replacement on 2026-10-10. The exact approval, proposal hash and 56
  identity/pin pairs are retained. No prompt is relabelled a proven crop; no
  baseline source, pin or history entry is removed. Seven accepted additions
  stay reserve; the frozen active runtime data contain exactly 1000.*
- [x] Implement the single Commons colour option, default any, with bounded
  selection, history compatibility and no silent colour fallback.
  *Local 1000-work candidate: readable names, one basic field, source-pinned offline
  prefilter and vocabulary v2. Static/helper production wiring and shape-only
  fallback/no-match preservation tested. Not released or installed.*
- [x] Add the requested complete native dashboard card with an optional colour
  dropdown helper, source-specific instructions and existing script/timer reuse.
  *D-216: guide/example identity tests; no new extension or mandatory helper.
  Card explicitly labels colour as Commons-only. Existing sources stay available;
  unsupported colour is reported rather than silently claimed to apply.*
- [x] Assess further selectors against actual available metadata, without
  implementing unapproved filters or removing existing providers.
  *560 artist labels across 1000 works; only 299 records have a retained work
  Q-ID. Artist search and future colour combinations are the strongest next
  candidates; period/motif/museum need normalized metadata first. See draft guide.*
- [x] Test and document the local draft's upgrade/no-match/unsupported-source behaviour and run
  the unchanged quality gates; record observed results in STATUS.
  *Final 1000-work gates: 5,027 passed, eleven platform skips, strict mypy for
  Mac/Linux (252 files), 100% line/branch coverage; 106 offline research tests.
  Full-palette recomputation passes for all 1063 research profiles; actual frozen
  runtime matches its 1000-work source/profile manifests. Browser observed
  1000/56/7 separate sets and 385 active blue matches. Draft guide and next Info
  text are local; published b5 unchanged. Native/release/live checks remain gated.*
- [ ] Obtain separate approval for native release builds/publication and
  separately for a Green update/TV test; do not infer either from local work.

No IP discovery, multi-colour UI, new provider or configuration.yaml change.
Credentials are not needed for initial research; security-sensitive GitHub
access changes remain subject to the deferred access task's confirmation.

## Deferred personal release-access improvement (user request, 2026-10-06)

- [ ] After b5, arrange browserless personal GitHub release access, limited to
  `volkue-tech/frame-gallery-ha`: fine-grained Variables read/write for exact
  approval values and Actions read/write for manual dispatch, alongside the
  existing push/release access. Prefer safe macOS Keychain retrieval without
  printing/persisting secrets in repository files or logs. User asked to keep
  this for later, not to alter token rights or store credentials during b5.
  Confirm the security-sensitive access change at implementation time; no
  corporate account, organization or credential is permitted.

## 400 usable Commons works and first-user UX (2026-10-06, D-211)

- [x] Retain original proposals/caches; research additions in a separate folder.
- [x] Visually inspect complete works; reject frames, details, duplicate scans,
  poor reproductions and incompatible rights, without weakening the 2.5% limit.
- [x] Freeze 400 distinct usable JPEG entries and their auditable provenance;
  recheck all additions through the unchanged production metadata adapter.
  *166 unchanged + 234 new; 299 artist labels; 400/400 metadata acceptance over
  eight bounded audit passes in 74.45 s. No image/TV validation implied.*
- [x] Promote the authentic colourful Commons dashboard screenshot to Info/guide.
- [x] Explain the first TV run separately from optional camera/timer/script setup.
- [x] Add expanded-catalogue tests, full quality gates and a scrolling preview.
  *5,006 tests, eleven platform skips, 100% line/branch coverage, Ruff and strict
  mypy. Preview: 400 usable works + 34 separately retained older review cases;
  search/filter/bookmark tests passed. 26 vetted reserves remain local.*
- [x] Obtain explicit new publication approval before numbered release, personal
  credential session, native builds, signed images or Store changes.
  *User explicitly approved 0.1.0b5 and the bounded personal session, 2026-10-06.*
- [x] Freeze numbered b5 sources; publish and anonymously verify their archive.
  *Runtime/source 44b7278; public sources-v0.1.0b5, 523,089,920 bytes,
  SHA256 d810c71ed634f3936e5761032c694e7fd9413374349acd5a1b41dd50e04f8637;
  anonymous download and every-member/version/commit preflight passed.*
- [x] Validate both native architectures and actual publisher runtime images;
  verify independent signatures, anonymous pulls and exact catalogue/default.
  *Run 37536546471: all five jobs passed; all four evidence ZIP hashes matched.
  Each native/actual image passed 5,012 non-root tests plus five root checks,
  all memory/inspection cases; anonymous 400-work/default imports and exact
  candidate-identity signatures passed. Public prerelease 405188764 exists;
  Store main handoff completed at 6a79f8c with exact authenticated ref readback.*
- [x] Only after successful checks, publish b5 Store main and release and disable
  both one-time approvals. *Main readback HTTP 200 at 2026-10-06 22:30:23 UTC;
  both variables read back as DISABLED_AFTER_0.1.0b5. The bounded personal
  credential process closes immediately after this final receipt push.*

Samsung IP reuse/discovery remains an optional feasibility question. No HA/TV
changes or network scans are authorized by this task. Published b4 is immutable.

## Commons default and source-order UX (2026-10-06, D-210)

- [x] Use Commons first and as the shared default for new/missing-source options.
- [x] Preserve all four saved source selections, shape/fit, helpers and history.
- [x] Add parser/metadata/production-wiring regressions and update documentation.
- [x] Run full local quality gates and record observed results.
- [x] Research Detect-button feasibility only from official docs; no live scan.

The scope-planning pause is superseded by D-211's local implementation approval.
Initial 770 focused tests and final 5,006 full-suite tests passed; see STATUS.

Gate: separate user approval before new runtime release/images/publication or
live installation. Published b4 remains unchanged. No discovery implementation
or extra network permissions are approved.

## Near-widescreen Commons update (2026-10-06, D-209)

User authorized preserving research and publishing the update autonomously.
No new HA/TV mutation is included in this approval.

- [x] Retain all 200 research proposals, preview, reviewed IDs and source metadata
  locally; create a checksummed snapshot and a metadata-only release inventory.
- [x] Curate 166 near-widescreen JPEG sources; defer 34 rights/proportion/format
  cases without losing them from research. Preserve Commons history IDs.
- [x] Explicitly cap normal metadata batches at ten and exclude already-sent
  entries from mixed batches. Add larger-catalogue/exhaustion regressions.
- [x] Update numbered b4 metadata and English/German hints without new fields,
  dependencies, broad permissions or a changed strict 16:9 tolerance.
- [x] Finish final production-adapter metadata check and full local quality gates.
  *166/166 metadata entries accepted in 35.61 s over four bounded audit passes;
  4,995 tests, eleven platform skips, 100% line/branch coverage.*
- [x] Publish/download/hash-check exact corresponding sources from the clean candidate.
  *Runtime/source 5011966; public sources-v0.1.0b4, 522,618,880 bytes,
  SHA256 6a3ece93091f52f8d89ee37cb59b63625ccd7ebde6d12b025ac7969ee5c60e16;
  anonymous download and every-member preflight passed.*
- [x] Validate both native architectures and actual publisher images/signatures.
  *Run 37428676044: all five jobs succeeded. Both native suites and actual
  publisher containers passed; no new Green/TV test.*
- [x] Independently verify anonymous sources/registry and exact Cosign evidence.
  *Both anonymous pulls/manifest comparisons, actual version/catalogue checks
  and independent exact-SHA/identity signatures passed; BETA4_VALIDATION.md.*
- [x] Retain/hash-check both actual publisher evidence ZIPs.
  *Both downloaded ZIPs matched their public hashes and published digests;
  native actual-container checks and limits passed. Receipts: BETA4_VALIDATION.md.*
- [x] Only then update Store main, announce b4 and disable/read back both approvals.
  *Public release 404519064 / v0.1.0b4, 2026-10-06 09:12:20 UTC, exact runtime
  5011966; anonymous Store metadata and tag readback passed. Both approvals
  read back as DISABLED_AFTER_0.1.0b4; previous betas retained.*
- [x] Record the actual receipt using the bounded memory-only credential process.
  *BETA4_VALIDATION.md and STATUS.md. Publication close stops the broker and
  caffeinate; the local checkpoint records their observed shutdown. No token
  is persisted and no new HA/TV mutation is included.*

## Post-beta Commons (2026-10-05, D-206)

User authorized local implementation of the 50-work source without a request
feature. Previous live/publication approvals do not authorize this update.

- [x] Recheck API docs, curate 50 metadata-only works, replace two unresolved
  US-basis entries, pin upload hashes.
- [x] Add guarded finite source, rights/rendition checks, schema/helper selection
  and optional captions using existing no-repeat/runtime ports.
- [x] Add synthetic safety/contract and production-wiring regression tests.
- [x] Finish full local quality gates and record actual evidence in STATUS.md.
- [x] After dedicated contact-header permission: repeat metadata-only adapter
  check after the CC0 correction; actual result 50/50 in 10.35 s, ten requests.
- [x] Explicit b3 publication approval received: new numbered beta,
  exact-source/source-package and native
  ARM/Intel image/signature validation. Never overwrite b2.
- [x] Publish/download/hash-check exact matching sources; validate on both
  native architectures and hash-check their evidence ZIPs.
- [x] Complete actual publisher jobs, anonymous pulls and independent signatures.
- [x] Green update/test authorized: update preserving history; verify Commons preview/
  caption/loading/cleanup and actual TV display, then publish as authorized.
- [x] Disable and read back both one-time publisher variables after success.
- [x] Publish the b3 announcement and final user-facing documentation/validation receipt.
  *Public prerelease v0.1.0b3, ID 404028775, published 2026-10-05 18:57:36 UTC;
  draft=false / prerelease=true verified. Runtime/source remains 15644bf;
  public main contains the final guides, screenshot and Green validation report.
  Both one-time publisher approvals are disabled; previous betas remain.*

Follow-up (not part of the frozen b3 runtime): propose a broader minimum
landscape ratio after the user's feedback about Macke's large side margins.
No wider-ratio policy or new configuration field has been approved/implemented.

The initial local-only stop gate was superseded by the user's explicit b3
publication and Green-test approval. Do not update public Store main until
both actual publisher jobs and independent image verification succeed.

## Phase 0 — Specification package

Owner: Codex

- [x] Create the isolated repository.
- [x] Record product requirements.
- [x] Record independent-development boundaries.
- [x] Define product acceptance criteria.
- [x] Create Claude and Codex project instructions.
- [x] Commit the specification baseline.

Gate: user authorizes Claude to begin Phase 1.

## Phase 1 — Independent architecture proposal

Owner: Claude

- [x] Read all repository specifications.
- [x] Research only permitted official documentation and approved dependency documentation.
- [x] Write `ARCHITECTURE.md` describing original component boundaries, data flow, failure handling, storage, package layout, and test strategy.
- [x] Compare dashboard filter approaches: helpers, Ingress, and future companion integration.
- [x] Propose the first-release scope and defer nonessential features explicitly.
- [x] Record proposed dependencies and licenses in `DECISIONS.md`.
- [x] Identify unresolved decisions and risks.
- [x] Update `STATUS.md`.
- [x] Commit documentation only.

- [x] Codex review of commit `d42adf5`: conditionally accepted; Phase 2 not yet approved.
- [x] Apply the user decisions and review corrections (revision 2): beta providers (local media, Art Institute of Chicago, Cleveland Museum of Art); distinct filters and capability matrix; 120 s deadline; TV-upload exclusion ledger; release-blocking preview freshness; approved decisions; vertical-slice sequencing.
- [x] Amend `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` accordingly, with amendment logs.
- [x] Commit documentation only.

- [x] Codex final gate review of commit `9352e77`: architecture changes accepted; one dependency correction required.
- [x] Correct the Pillow 12.3.0 wheel inventory: the wheels bundle GPL-3.0-or-later `libimagequant` and LGPL-2.1-or-later FriBiDi. Scope Apache-2.0 to project-owned code, and add both libraries to D-135.
- [x] Record the `mypy-extensions` (MIT) and `pathspec` (MPL-2.0) development-only rows.
- [x] Record the accepted decisions Q-03, Q-04, Q-08, Q-09, Q-11, Q-12, Q-18 item 4 (D-113), and Q-23, and amend `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` where they are normative.
- [x] Commit documentation only.

- [x] Codex final approval of Phase 1 at commit `dda877c`; Phase 2 authorized.
- [x] Gate adjustment approved by Codex: verification of the remaining `pillow.libs` entries moved from the Phase 2 gate to the Phase 6 runtime-wheel inspection.

Gate: user and Codex approve the architecture before application code is written. **Passed** (`dda877c`).

## Phase 2 — Core skeleton, deterministic selection and rendering

Owner: Claude

- [x] Create the original package structure from the approved architecture.
- [x] Define the contracts for provider, television, storage, clock/deadline, allowance, downloader, executor, and renderer.
- [x] Add configuration validation (including the IPv4 television address), filter vocabularies with the capability matrix, and structured outcome types.
- [x] Implement the 120 s phase-budget calculator and the watchdog.
- [x] Implement the run-orchestrator skeleton (`app`: lifecycle stages, outcome classification, SIGTERM handling) against fakes.
- [x] Implement deterministic selection: exclusion interface, shape classification, upscale rule, strict 16:9, fallback, and shortlist.
- [x] Implement the image preparation pipeline (`contain` and `cover`) behind the executor seam, starting with the in-process executor.
- [x] Establish linting, formatting, type checking, and unit-test commands with `uv`.
- [x] Start a provisional `THIRD_PARTY_NOTICES.md` with Pillow and its known bundled libraries (including `libimagequant` and FriBiDi), the nine `pillow.libs` entries marked as pending Phase 6 verification, and the development dependencies.
- [x] Add unit tests, including the phase sums and the 70 s no-match bound.
- [x] Run an independent multi-lens review of the Phase 2 code (architecture, scope and acceptance, correctness, imaging and security, test quality), verify each finding, fix the confirmed ones with regression tests, and record the rest.
- [x] Update status and commit.

Gate: Codex reviews architecture conformance and independence. **Passed**: Codex reran the Phase 2 gates on 2026-09-27, and the user approved Phase 3 the same day, accepting D-141 to D-145.

## Phase 3 — Provider adapters

Owner: Claude

- [x] Re-verify the live Art Institute of Chicago and Cleveland Museum of Art documentation (documentation pages only). Done on 2026-09-27 (D-146).
- [x] Implement the guarded network gateway, and add `urllib3` and `certifi` to the third-party notices (D-147).
- [x] Implement the `ha` helper-override client (at most 4 reads, static fallback; B3–B5) (D-148).
- [x] Implement the local media provider (D-149).
- [x] Implement the Art Institute of Chicago provider: documented API, CC0 public-domain works only (D-146, D-150).
- [x] Implement the Cleveland Museum of Art provider: documented API, CC0 records only, documented print JPEG only (D-146, D-151).
- [x] Implement combined filters per the capability matrix, visible reporting of unsupported filters, orientation checks, the strict-format budget (30 remote dimension requests), and pacing. The Art Institute supports only the period in the beta (D-146); Cleveland combines department and period (D-151, D-152).
- [x] Add independently authored or synthesized fixtures and the shared contract tests. Any recorded observation requires user approval. (Synthesized only; nothing recorded; D-152.)
- [x] In the contract suite, assert that each adapter agrees with `CAPABILITY_MATRIX` and `ALLOWED_RIGHTS`, that discovery-endpoint 404/410 responses map to `HTTP_ERROR`, and that local inspections return `None` for unreadable files (D-141).
- [x] Fix the vocabularies (Q-14) with labels that stay distinct across both museums (D-143). Version 1, documented in `frame_gallery/VOCABULARY.md` (D-152).
- [x] Run independent reviews of the gateway, the helper reader, and local media; fix every confirmed finding with regression tests (`9b736f3`, `37e85d0`).
- [x] Update status and commit.
- [x] Phase 3 gate decision (user, 2026-09-27): Q-25 resolved with option (a), so the first beta ships without a colour filter; D-146 to D-152 accepted; no live Art Institute observation approved.
- [x] Amend `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` so that B2 and C1 apply only to the filters the selected source supports, with amendment logs.

Gate: Codex reviews provider access patterns, bounding, fixtures, and legal boundaries. **Passed** (user decision, 2026-09-27).

## Phase 4 — Bounded state and duplicate prevention

Owner: Claude

- [x] Implement the atomic, recoverable, bounded write primitive and history (D-153).
- [x] Implement the TV-upload exclusion ledger with the write-ahead uncertainty quarantine (D-154).
- [x] Implement the temporary-workspace lifecycle, the startup sweep, and the bounded metadata cache (D-155, D-156), with the exhausted-page hints deferred from Phase 3 (D-157).
- [x] Implement atomic preview publication and the run records (D-158).
- [x] Complete PRE-STAGE, RECORD, and PUBLISH in the runner. Test E7–E10 against a fake television port that emits progress markers, in process and with a real SIGKILL of a child process (D-159).
- [x] Add unit and integration tests for cleanup, corruption, limits, version handling, and the ledger scenarios E7–E10.
- [x] Run independent reviews of the store and of the later Phase 4 commits; fix every confirmed finding with regression tests.
- [x] Update status and commit.

Gate: Codex reviews crash safety, the bounds, duplicate prevention (E7–E10), and the proposed decisions D-153 to D-159. **Passed** (user decision, 2026-09-27): D-153 to D-159 accepted; Codex re-ran the quality gates; the 20 000-entry bound is accepted for the first beta (R-29).

## Phase 5 — Samsung adapter contract

Owner: Claude

Authorized by the user on 2026-09-27, after the Phase 4 gate.

- [x] First check and document the version and the LGPL-3.0 obligations of `samsungtvws` 3.0.6 (D-135). The pinned version may be installed from PyPI into the git-ignored project environment only (D-160).
- [x] Establish the adapter surface only by inspecting the installed `samsungtvws` 3.0.6 distribution (D-161).
- [x] Implement the isolated process executor with the complete bootstrap: privilege drop to an unprivileged user, the parent-death signal, umask, resource limits, the bytes-only channel, progress markers, and the bootstrap test (D-163, D-164). The root-only and Linux-only assertions of the bootstrap test are written and first run in the Linux container (D-165).
- [x] Re-run E7–E10 with the process-based television worker, including a real SIGKILL of the runner while its worker runs.
- [x] Measure worst-case prepare memory and time under the real limit. *Measured on the development host without `RLIMIT_AS`, which macOS cannot set, for the §11.1 worst cases with sources filling the 40 MiB cap (R-09, `scripts/measure_prepare.py`); under the real limit in the Linux container, as root (D-165).* **Moved to Phase 6** as the condition of D-165 (Phase 5 gate). *Done in Phase 6, in the `aarch64` container under the real 1 GiB limit: every case passes (D-170).*
- [x] Implement connection, pairing-token persistence, upload, and select in the television worker. The adapter owns the token store and the `auth` result, polls `DeliveryRequest.stop_requested` while it waits (killing the worker and relaying the markers already sent), and `deliver` returns only after its worker is dead (D-141, D-162, D-163).
- [x] Map library failures and markers to clear outcomes and ledger transitions (D-162).
- [x] Add mocked adapter tests; do not contact the live television. They include runs of the unchanged library over a socket pair against a scripted television.
- [x] Update third-party notices, status, and decisions.
- [x] Run independent reviews of the design and of the Phase 5 commits; fix or record every confirmed finding.
- [x] Commit.

Gate: Codex reviews the isolation design and its tests, the Samsung adapter against the installed library, and the `samsungtvws` row with its LGPL-3.0 obligations. Phase 6 does not start before it is explicitly authorized. **Passed** (user decision, 2026-10-02, after the Codex gate review): D-160 to D-164 accepted; D-165 accepted on the condition that the Linux and root checks and the measurement under the real `RLIMIT_AS` pass in Phase 6 (mandatory before any live test on the Green); Art API 0.97 stays unsupported in the beta; TLS pinning is decided after the Phase 8 observation; `inspect` gets parent-opened read-only descriptors, where possible, and batching in Phase 6; the 1 GiB limit stays until the Linux measurement; AppArmor child profiles stay in Phase 9 (`DECISIONS.md`, *Phase 5 gate decisions*).

## Phase 6 — Home Assistant app packaging

Owner: Claude

Authorized by the user on 2026-10-02, after the Phase 5 gate. Network access for the build is limited to what the user approved separately the same day: starting Docker Desktop; reading the tags of `ghcr.io/home-assistant/base` and pulling it for `aarch64` and `amd64`, pinned by tag and digest; the Alpine package source for `python3`; and PyPI for the hash-checked `musllinux` wheels of the runtime and the test tools. No access to the Green, the television, a provider API, or GitHub; nothing installed, pushed, or published.

- [x] Create current-format Home Assistant app metadata and option translations that state source applicability (D-168).
- [x] Package the one-shot runtime and the persistent and media mappings, starting without `host_network` (D-167, D-168).
- [x] Wire the entry point (`__main__`, D-166), with the one process executor that the runner, the Samsung adapter, and the watchdog share, a start shield that defers stop requests, and the refusal to run unless `Launch.enforced` in the container (D-163): logging with the redactor, a `CancellationController(start_deferred=True)` created before the SIGTERM handler is installed, the environment allowlist, the watchdog (fire time and start from `RunBudget`; if `RunResult.summary_emitted` is false, wait for the watchdog's exit instead of exiting), container-network discovery, and the options file.
- [x] Create a modern multi-platform Dockerfile and a draft AppArmor profile in complain mode (D-167, D-168). *Codex's follow-up check, reported on 2026-10-03: `apparmor_parser -Q -T` accepts the profile's syntax (exit code 0, in a temporary aarch64 container). That is a syntax check only; the enforcement on the Green is untested (Phase 8 complain mode, Phase 9 enforced).*
- [x] Add local container build tests for supported architectures where available, including the D-130 checks (`scripts/container_check.sh`; D-167, D-170).
- [x] Once the Python version is fixed, repeat the Pillow wheel SBOM inspection against the exact two runtime wheels (`aarch64`, `amd64`). Record the result in `DECISIONS.md` and the third-party notices; it is authoritative for the bundled-library inventory (D-171: neither `libimagequant` nor FriBiDi is in the wheels).
- [x] In the same inspection, verify the versions and SPDX identifiers of the remaining `pillow.libs` entries (libXau, libXdmcp, Brotli, libbsd, liblzma, libmd, libpng, libsharpyuv, libzstd). This is mandatory before packaging or publication (gate adjustment approved by Codex at `dda877c`). *Done: every version and licence is verified (D-171). libbsd's and libmd's licences, which the wheel does not carry, come from the official Alpine package directory (Codex's follow-up check, reported on 2026-10-03). libmd's field includes "Public Domain", which is not an SPDX identifier; the licence review settles its exact form. Nothing was published.*
- [x] Write complete installation, configuration, capability-matrix, troubleshooting, and draft dashboard documentation, with the known limitations in plain language (among them R-29: very old works can come back once they leave the 20 000-entry history) (`DOCS.md`, D-168).
- [x] Implement `inspect` batching (§8.3, D-149), with read-only descriptors that the parent opened, where possible (Phase 5 gate decision; D-169).
- [x] Run the Linux and root isolation tests in the container (the two passes of D-165) and the worst-case preparation measurement under the real `RLIMIT_AS`, as root. Both must pass (the condition of D-165); they are mandatory before any live test on the Green. The 1 GiB limit changes only if the measurement calls for it. *The D-130 checks, the smoke run, and both D-165 passes passed on `aarch64` and `amd64`. The measurement passed natively on `aarch64`, where the heaviest case peaks at 766 MiB of address space, so the limit stays. On `amd64` it runs here only under Rosetta, where every process carries about 278 MiB more address space and the heaviest case fails; that result is informative only (D-170).*
- [ ] Measure the worst-case preparation natively on `amd64` under the real `RLIMIT_AS`. *No native `amd64` host was available; the measurement under Rosetta is informative only (D-170).* **Moved to Phase 9** (Phase 6 gate): mandatory before an `amd64` version is published.
- [x] Record the Buildx and QEMU rows (bundled with Docker Desktop, whose start the user approved on 2026-10-02 so that they can be used) and the SBOM approach (no SBOM tool is downloaded or installed without a separate approval), and propose answers to Q-06 and Q-10 (D-171, D-172).
- [x] Run an independent review of the Phase 6 commits; fix or record every confirmed finding (8 agents; 19 of 20 findings confirmed, all fixed or recorded; *Review records* in `DECISIONS.md`).
- [x] Update status and commit.

Gate: Codex reviews Home Assistant OS/Green compatibility and security. **Passed** (user decision, 2026-10-03, after the Codex review and its follow-up checks): D-166 to D-172 accepted, the 1 GiB limit unchanged; the native `amd64` measurement is mandatory before an `amd64` version is published, at the latest in Phase 9; the qualified licence review and the enforcement of the AppArmor profile stay release prerequisites (`DECISIONS.md`, *Phase 6 gate decision*).

## Phase 7 — Offline release validation

Owner: Codex and Claude

Authorized by the user on 2026-10-03, after the Phase 6 gate: offline validation with the existing local environments and container images, failure-path tests, and a release-candidate report. No new features, and no additional review loops without a concrete finding. No access to the Green, the television, or a provider API; nothing created, pushed, or published on GitHub.

- [x] Run full unit, integration, lint, type, timing, and container tests. *At the release candidate `f42f72a`: `check.sh` (4 600 passed, 8 skipped, 100 % line and branch coverage); the timing tests; the container checks of the existing images on both architectures, without a build or network (`container_check.sh --no-build`, D-173): the images hold the release candidate's sources, D-130 a-d, the inventory, both D-165 passes, and the measurement under the real `RLIMIT_AS` on `aarch64` (`RELEASE_CANDIDATE.md`).*
- [x] Verify no excluded predecessor material is present. *The names of the excluded projects appear only in the three files that state the boundary, in each of the 72 commits; no third-party code, header, or asset; the icon and logo are drawn by a script; the fixtures are synthesized; the images derive from the pinned base alone (`RELEASE_CANDIDATE.md` 3.6).*
- [x] Verify dependency notices and the approved project license. *The notices list everything the image ships, on both architectures (`image_inventory.py --notices`, now part of `container_check.sh`; D-173); Apache-2.0 is approved for the project's own code (D-102), and its `LICENSE` file follows in Phase 9. The licence texts, the corresponding sources, and the open licence questions stay with the qualified licence review (Phase 9).*
- [x] Exercise the no-result, timeout, corrupt-history, failed-download, failed-decode, failed-upload, and upload-ledger paths. *Through the real image on both architectures, 10 scenarios, each as specified (`scripts/failure_paths.py`, D-173); a failed upload after `upload_started`, which needs a television that takes the upload, through the suite (E7-E10, the unchanged library against a scripted television).*
- [x] Produce a release-candidate report. *`RELEASE_CANDIDATE.md`.*

Gate: user approves live Home Assistant Green installation and television test. **Live installation/test approved** (2026-10-03): after Codex inspected the report, the user explicitly approved a separate test app and Chicago/Cleveland image delivery. D-173 remains a proposed documentation clarification; publication remains unapproved.

## Phase 8 — Supervised Home Assistant Green validation

Owner: Codex with user supervision

- [x] Install under a unique development slug without replacing another app (install route per Q-21). *`local_frame_gallery_dev`, Frame Gallery (Test), 0.1.0.dev0; built by Supervisor on Green via `/local_apps` in the existing Terminal & SSH app. Protection enabled, own AppArmor profile loaded, watchdog disabled. See `PHASE8_REPORT.md`.*
- [x] Preserve all existing Home Assistant configuration. *Changes were limited to explicitly approved separate test elements and temporary test-app diagnostics. Normal source/options restored; no existing app/dashboard/script/integration or `configuration.yaml` changed.*
- [x] Run a local-media test. *TV confirmed selection in 7.2 s; a second run excluded the same file and stopped as `no_match`, preserving the preview. A separately approved labelled 3:2 fixture delivered in 9.9 s; its Green preview exactly matches local contain preparation with black side margins and refreshed without reload. The user confirmed all four coloured edges/corner labels and black side margins on the physical TV: edge/no-crop check passed (`PHASE8_REPORT.md`).*
- [x] Run Art Institute of Chicago and Cleveland Museum of Art tests, including a restrictive-filter fallback test, against `192.168.178.30`, entered in the options and never hard-coded. *Chicago `aic:88793` delivered in 15.5 s after D-174; Cleveland strict and restrictive fallback deliveries previously passed. TV API confirmed selection; physical-TV visual confirmation is recorded separately in `PHASE8_REPORT.md`.*
- [x] Verify Home Assistant Green-to-television connectivity without `host_network` before considering any change. *Local, Cleveland and corrected Chicago deliveries confirmed by the TV API, without a networking/protection change.*
- [x] Select and document one proven preview refresh mechanism. Verify, in repeated live tests covering card-started, automation-started, app-page-started, and no-match runs, that each newly delivered image is shown without a stale browser cache (release-blocking).
  *Native Local File refresh of atomically replaced `latest.jpg`, D-140. Earlier repeated card/app-page/no-match tests are now joined by an actual self-disabling event automation (19.7 s delivery) and a post-cancellation card delivery (17.0 s). Both refreshed without reload or a camera-update action. The recovery screenshot bounds refresh to at most 14 s after publication on this setup, not a universal timing guarantee. Loading is a separate open finding.*
- [x] Verify history, the upload ledger, cleanup, finite stop within 120 s (no-match within 70 s), the loading indicator, and no stale temporary files.
  *D-174/D-175 installed only in the separate test app, without uninstall/reset; protection stays enabled. Live post-cleanup report: state 7 files / 3 105 bytes; cache 2 / 513; preview 1 / 1 465 960; scratch 0 files/bytes/run directories/temporary files. Quarantine and TV buckets unavailable, not proven empty. Shared media contains only the retained fixture and one preview; about 15.7 GB free. Detailed history/ledger and crash/forced-stop checks remain open.*
  *Continuation: 44 offline Linux signal/crash/sweep checks passed. Three Green graceful stops ended as cancelled; the last removed scratch files after a 5,156,644-byte download and preserved the previous preview SHA256. Recovery delivery and scratch cleanup succeeded. Detailed private-state integrity and a hard-kill on Green remain open. Running-based loading demonstrably ended early in one run and persisted after delivery in another; correct it only with user approval. Investigate `sh: invalid number '--'` during Supervisor stops. The own event automation is saved, successfully traced and disabled, with no schedule (`PHASE8_REPORT.md`).*
  *Approved correction completed: D-176/D-177 runtime `d1bb654` installed only in the retained test app. Delivery, no-match and a graceful stop after a 647755-byte download acknowledged loading completion after scratch cleanup. The real Green stop no longer emitted `invalid number '--'`; preview stayed unchanged on no-match/stop. Missing-notification injection proved the 150 s expiry without manual cancel. Original filters/explicit timer restored. This does not complete the combined integrity/forced-stop requirement.*
  *Private-state snapshot inspection completed through an explicitly approved official local app-only backup, without weakening protection: six JSON files passed the observed format/identifier/timestamp/bounds and consistency checks; history 12 unique entries, backup 11; ledger two uploaded entries and its backup retains the latest write-ahead intent. Both synthetic fixtures and known museum deliveries remain remembered; current/last-run/preview agree. Audit copies removed, backup retained; no restoration or TV action. This validates the current snapshot, not Green crash recovery; the combined requirement remains open (`PHASE8_REPORT.md`).*
  *Latest completion supersedes the earlier pending integrity/forced-stop/loading findings above: approved Green SIGKILL before TV contact, with a live isolated worker and fsynced pre-staged history; next start removed the durable temporary file and a separate synthetic leftover run. Options, history/ledger primary and backup copies, current and preview hashes stayed unchanged. Both sent fixtures were excluded, clean `no_match` exit 0, scratch empty. All 13 native Green memory cases passed under unchanged 1 GiB/15 s worker limits (765.5 MiB peak address space, 11.1 s slowest); 150 inspections passed. Own AppArmor attachment confirmed in complain mode, not enforcement. Normal app rebuilt from exact saved source; about 1 GB diagnostic inputs/archives removed, 15.5 GB free. Live after-upload hard-kill/power-loss claims are explicitly excluded; those ledger failure paths remain offline-tested (`PHASE8_REPORT.md`).*
- [x] Record the entity IDs and the proven refresh mechanism. Complete the dashboard card, script, and timer, except for the public slug.
  *Test IDs and full YAML examples are recorded in `PHASE8_REPORT.md` and `frame_gallery/examples/`; native preview refresh and corrected app-owned loading completion/expiry are verified on Green. Public-slug/clean-install confirmation remains Phase 9.*
- [x] Remove or retain the development installation only as directed by the user. If it is removed, confirm that its `/data` folder goes with it, the reset path of D-172 (Q-06). *Retained and restored to the ordinary `0.1.0.dev1` test app as explicitly requested; stopped/protected, no uninstall or data reset. Uninstall removal semantics were not tested on the user's retained data.*

Remaining live limitation: fresh pairing/token rejection is not proven on this already-authorized TV; no authorization was reset. AppArmor enforcement/child profiles and a clean public install are Phase 9 gates. This checklist completion does not authorize Phase 9 or publication.

Gate: user approves release hardening, public publication, and final name.

## Phase 9 — AppArmor, release hardening, and public beta

Owner: Codex and Claude

Authorized by the user on 2026-10-03: complete the next phase; name Frame Gallery
and personal public repository volkue-tech/frame-gallery-ha explicitly confirmed.
Codex performs the engineering licence audit, without claiming legal counsel's
approval. Existing release prerequisites remain mandatory.

- [x] Switch the AppArmor profile to enforce mode and verify the whole isolation design, with an approved supervised live re-check; add the per-worker child profiles (R-31), and revisit an unprivileged parent with them (Q-10, D-172). The enforcement is a release prerequisite (Phase 6 gate).
  *D-178/D-180/D-182 implemented; actual enforced child plus seccomp negative/positive probes and parent-output read passed on Green with records preserved and scratch empty. Parent remains root with its trusted state/worker-management role; no new container privilege. The regular app is restored; two card-started deliveries passed with preview/loading/cleanup. D-183 corrects the backup-link omission found in the first run; the second after the official dev7 update had no backup warnings. Own development-install checks pass; the separate clean public-install gate remains open. See `PHASE9_REPORT.md`.*
- [x] Measure the worst-case preparation natively on `amd64` under the real `RLIMIT_AS` (`scripts/measure_prepare.py`, as root). Mandatory before an `amd64` version is published (Phase 6 gate, D-170).
  *Native GitHub Intel job `111256837847` succeeded on `39d25da` at 18:02:25 UTC, run `37141542920`; ARM job succeeded as well. No emulation. Both container/root suites and the scripted 13-case, twice-repeated memory gate passed. This does not complete licence/image/public-install gates.*
- [x] Create the user-approved public repository under `volkue-tech`.
  *https://github.com/volkue-tech/frame-gallery-ha created in the personal Firefox session. The audited `main` at `39d25da` is pushed and its remote SHA verified; only the personal identity and main history were transferred. Native hosted run `37141542920` started; no binary release.*
- [x] Complete the user-requested engineering licence audit (D-179) and the distribution controls of D-135: `samsungtvws` (LGPL-3.0), Pillow's fribidi-shim (LGPL-2.1-or-later; the runtime wheels contain neither `libimagequant` nor FriBiDi, D-171), the Alpine base packages, the tools outside apk (s6-overlay, tempio, bashio; R-33), and the exact form of libmd's "Public Domain" part. This records an engineering assessment, not a qualified lawyer's approval.
  *Latest evidence supersedes the historical preparation notes below:
  ENGINEERING_LICENSE_REVIEW records applicability, retained original notices,
  source/replaceability controls and remaining provenance/patent/ownership risks.
  Exact runtime sources are public and anonymously hash-verified; actual image
  notices and signatures passed. No independent legal opinion is claimed or
  concrete unresolved source/notice obligation waived.*
  *D-186 to D-191 retain the exact source evidence and original texts. A local
  172-archive corresponding-source candidate plus the own clean source snapshot
  is assembled/read-back hash-verified (512 MB), not publicly released. Remaining
  applicability, replacement/rebuild and final source/publication gates stay open.*
  *D-192 supplies SOURCE_AND_REBUILD and a tracked, tested offline source-package
  assembler, plus 111 original Alpine subsidiary/primary/recipe documents.
  Full host gates passed (4,749 tests, 100% line/branch). Final release applicability,
  exact-commit assembly/validation and public availability remain separate checks.*
- [x] Add the Apache-2.0 licence for project-owned code, and third-party notices with the GPL and LGPL texts and copyleft source availability.
  *Latest: all 201 original evidence documents verified in the published images;
  matching 172-archive corresponding sources remain publicly downloadable.
  Original third-party licences remain intact; the image is not GPL-free.*
  *Project LICENSE/NOTICE and the current original third-party/GPL/LGPL texts are
  committed and shipped in the Supervisor-compatible image context (D-190).
  All 89 evidence files are byte-checked and readable as uid 65534 in the native
  ARM image; notice/source-data tests now run there without evidence skips.
  Complete source distribution and engineering applicability remain open.*
- [x] Configure GitHub Actions for tests and multi-architecture GHCR publication.
  *Native read-only validation workflow succeeded on ARM and Intel (D-181, run `37141542920`, source `39d25da`). A separate gated publication workflow and validation of later changes remain pending.*
  *D-193 prepares the manual-only, exact-commit/source-hash-gated native publisher
  with fresh actual-image checks, non-overwrite and signature verification.
  It remains disabled for dev0/unset approval variables; no registry run is
  claimed. Latest local host/ARM-container suites pass; matching source assets,
  hosted validation, anonymous image availability and public install remain open.*
  *D-194 prepares numbered candidate `0.1.0b1`, with full host/native ARM suites
  passed and an unchanged-dependency offline lock check. Stage remains
  experimental; matching source publication and signed public image validation
  are not skipped by giving the candidate a version number.*
  *Latest D-195 progress (2026-10-04): both native jobs passed for exact runtime
  commit `d736c7a`. Its 172-archive source-only prerelease `sources-v0.1.0b1`
  is public; the anonymous download matches 518,133,760 bytes and SHA256
  `8034a982322532b34b0c9893cda5135cb16448dc694e2c59f68ae42fedeb64b5`.
  The exact-commit/source approval variables were saved and read back, and
  publisher run `37159551965` started. Its approval and both native validations
  passed; the two publishers passed the public-source preflight and started
  checking their actual upload images. Actual image
  publication/signatures, anonymous pulls and clean public installation are
  still unproved. Earlier draft-package/workflow statements above describe
  historical milestones, not the latest publication state.*
- [x] Publish immutable versioned images for `aarch64` and `amd64`.
  *D-196: publisher `37159551965` passed both actual-image validations,
  non-overwrite/signing and source preflight. Both exact digests were independently
  anonymously pulled and Cosign-verified against the own workflow/issuer/commit.
  Registry version tags are not administrator-immutable; the recorded signed
  digests are. No `latest` app tag was published. Evidence ZIP hashes match.*
- [x] Add the one-click Home Assistant repository link.
  *Latest D-198: actual official redirect/repository recognition and separate
  pre-built installation passed on Green; no end-user SSH/config edit required.*
  *Prepared in README/app guide using the official repository redirect and exact
  personal URL; still marked installation candidate. Live redirect/install
  verification and public metadata push remain pending.*
- [x] Finalize the dashboard card with the slug observed after installing from the public repository.
  *D-198: `a94fc569_frame_gallery`; full script/card in DOCS and exact installed
  beta examples. Native preview refreshed and timer loading ended on both runs.*
- [x] Verify clean installation on Home Assistant Green from the public repository.
  *D-198: separate store install after `60f22c4`, two delivered runs (21.2/17.3 s),
  physical first-image confirmation, safe invalid-option refusal/restoration,
  zero temporary counts, protection/profile settings and app-only backup checked.
  Public kernel negative probes/fresh pairing were not repeated. Corrected root
  repository test still needs fresh hosted CI before final announcement.*
- [x] Publish release notes and known limitations.
  *D-199: public prerelease `v0.1.0b1`, tag `8a3e7ee`, with install/setup links,
  exact signed-image/source identities and explicit compatibility/filter/licence
  limits. Both final native jobs passed in run `37193338410`.*
- [x] Deactivate the one-time image-publication approval values after release.
  *After the user's personal GitHub confirmation, both values are saved/read back
  as `DISABLED_AFTER_0.1.0b1`. This is reversible and fails the publisher's exact
  commit/hash checks; no variables/data were deleted or privileges expanded.*

Phase 9 public-beta work is complete within the documented engineering/test
scope. Fresh authorization across all TV models, public-install kernel negative
probes and independent legal counsel are not claimed. No next feature phase is
authorized by this completion record.

## Post-beta — optional artwork information (D-202)

User explicitly authorized local implementation on 2026-10-04. Keep the standard
card minimal and the title/artist/museum card separate/optional; no additional
dashboard extension. The earlier Phase 9 completion is not broader authorization.

- [x] Implement explicit Text-helper option, parent-only scoped output, bounded
  plain-text JSON and preview-coupled failure ordering, with synthetic tests.
- [x] Write complete optional native-card/helper instructions; retain the basic
  card and initially mark the new feature unreleased; graduate after validation.
- [x] Run full local quality gates and record the actual results.
  *Ruff, strict host/Linux mypy (244 files), 4,904 passed, eleven unchanged
  Linux/root-only skips; 100% line/branch coverage (9,272 / 2,002). No native
  runtime or live HA validation is inferred from this macOS run.*
- [x] After explicit publication approval: select a new version (never overwrite
  0.1.0b1), build/validate native ARM/Intel, refresh source evidence and sign/publish.
  *D-204: 0.1.0b2 images and corresponding sources published and independently
  verified for exact runtime commit f3d916c; all five publisher jobs passed.
  Both approval variables are disabled again. Subsequent store push and app
  announcement completed separately, recorded below and in D-205.*
- [x] Create the approved dedicated Text helper with saved minimum 0, maximum
  255 and Text mode; confirm its actual ID without changing existing helpers.
  *D-204: input_text.frame_gallery_artwork, settings reopened and verified.*
- [x] Complete the personal store-main push and app-release announcement after
  successful authorized live validation; do not infer either from public images.
  *Store main push completed at e908602, independently confirmed anonymously.
  The user briefly postponed the test, then reauthorized all software testing
  with physical display confirmation deferred. D-205 records completed software
  validation. Public prerelease v0.1.0b2 targets 4c93d86; anonymous release/main
  verification and byte-identical guide/report/screenshot downloads passed.
  Physical TV confirmation remains explicitly deferred by the user.*
- [x] After explicit live-change approval: update Green without data reset,
  create/configure dedicated helper, verify repeated refresh/no-match/failure,
  helper restoration after HA restart, and optional-card rendering.
  *D-205: in-place b2 update, two successful native image/text updates, browser
  reload, no-match and safe config-invalid retention, zero temporary counts,
  restored original options, and one separately approved Core restart passed.
  Live TV-transport/metadata faults were not injected; synthetic tests cover
  them. Physical display confirmation is explicitly deferred, not claimed.*

Publication approved on 2026-10-04 (D-203). The subsequent explicit live approval
covers the existing-app update, dedicated helper, separate test card and TV run.
The user subsequently reauthorized software live testing and explicitly approved
one HA Core restart. Physical confirmation of the displayed TV image will be
supplied later; do not claim that observation from protocol success alone.
