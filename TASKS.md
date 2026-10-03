# Implementation plan and approval gates

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

- [ ] Switch the AppArmor profile to enforce mode and verify the whole isolation design, with an approved supervised live re-check; add the per-worker child profiles (R-31), and revisit an unprivileged parent with them (Q-10, D-172). The enforcement is a release prerequisite (Phase 6 gate).
  *D-178/D-180/D-182 implemented; actual enforced child plus seccomp negative/positive probes and parent-output read passed on Green with records preserved and scratch empty. Parent remains root with its trusted state/worker-management role; no new container privilege. The regular app is restored; two card-started deliveries passed with preview/loading/cleanup. D-183 corrects the backup-link omission found in the first run; the second after the official dev7 update had no backup warnings. Own development-install checks pass; the separate clean public-install gate remains open. See `PHASE9_REPORT.md`.*
- [ ] Measure the worst-case preparation natively on `amd64` under the real `RLIMIT_AS` (`scripts/measure_prepare.py`, as root). Mandatory before an `amd64` version is published (Phase 6 gate, D-170).
- [x] Create the user-approved public repository under `volkue-tech`.
  *https://github.com/volkue-tech/frame-gallery-ha created and verified public/empty in the personal Firefox session. No source push or binary release; personal Git authorization remains pending.*
- [ ] Complete the qualified licence review (D-135) as a release gate: `samsungtvws` (LGPL-3.0), Pillow's fribidi-shim (LGPL-2.1-or-later; the runtime wheels contain neither `libimagequant` nor FriBiDi, D-171), the Alpine base packages, the tools outside apk (s6-overlay, tempio, bashio; R-33), and the exact form of libmd's "Public Domain" part.
- [ ] Add the Apache-2.0 licence for project-owned code, and third-party notices with the GPL and LGPL texts and copyleft source availability.
- [ ] Configure GitHub Actions for tests and multi-architecture GHCR publication.
  *Native read-only validation workflow prepared (D-181); actual ARM/Intel runs and a separate gated publication workflow still pending.*
- [ ] Publish immutable versioned images for `aarch64` and `amd64`.
- [ ] Add the one-click Home Assistant repository link.
- [ ] Finalize the dashboard card with the slug observed after installing from the public repository.
- [ ] Verify clean installation on Home Assistant Green from the public repository.
- [ ] Publish release notes and known limitations.
