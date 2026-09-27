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

Gate: Codex reviews architecture conformance and independence.

## Phase 3 — Provider adapters

Owner: Claude

- [x] Re-verify the live Art Institute of Chicago and Cleveland Museum of Art documentation (documentation pages only). Done on 2026-09-27 (D-146).
- [x] Implement the guarded network gateway, and add `urllib3` and `certifi` to the third-party notices (D-147).
- [x] Implement the `ha` helper-override client (at most 4 reads, static fallback; B3–B5) (D-148).
- [x] Implement the local media provider (D-149).
- [x] Implement the Art Institute of Chicago provider: documented API, CC0 public-domain works only (D-146, D-150).
- [ ] Implement the Cleveland Museum of Art provider: documented API, CC0 records only, documented print JPEG only.
- [ ] Implement combined filters per the capability matrix, visible reporting of unsupported filters, orientation checks, the strict-format budget (30 remote dimension requests), and pacing.
- [ ] Add independently authored or synthesized fixtures and the shared contract tests. Any recorded observation requires user approval.
- [ ] In the contract suite, assert that each adapter agrees with `CAPABILITY_MATRIX` and `ALLOWED_RIGHTS`, that discovery-endpoint 404/410 responses map to `HTTP_ERROR`, and that local inspections return `None` for unreadable files (D-141).
- [ ] Fix the vocabularies (Q-14) with labels that stay distinct across both museums (D-143).
- [ ] Update status and commit.

Gate: Codex reviews provider access patterns, bounding, fixtures, and legal boundaries.

## Phase 4 — Bounded state and duplicate prevention

Owner: Claude

- [ ] Implement the atomic, recoverable, bounded write primitive and history.
- [ ] Implement the TV-upload exclusion ledger with the write-ahead uncertainty quarantine.
- [ ] Implement the temporary-workspace lifecycle, the startup sweep, and the bounded metadata cache.
- [ ] Implement atomic preview publication and the run records.
- [ ] Complete PRE-STAGE, RECORD, and PUBLISH in the runner. Test E7–E10 against a fake television port that emits progress markers.
- [ ] Add unit and integration tests for cleanup, corruption, limits, version handling, and the ledger scenarios E7–E10.
- [ ] Update status and commit.

## Phase 5 — Samsung adapter contract

Owner: Claude

- [ ] Establish the adapter surface only by inspecting the installed `samsungtvws` 3.0.6 distribution.
- [ ] Implement the isolated process executor with the complete bootstrap: privilege drop to an unprivileged user, the parent-death signal, umask, resource limits, the bytes-only channel, progress markers, and the bootstrap test.
- [ ] Re-run E7–E10 with the process-based television worker. Measure worst-case prepare memory and time under the real limit.
- [ ] Implement connection, pairing-token persistence, upload, and select in the television worker. The adapter owns the token store and the `auth` result, polls `DeliveryRequest.stop_requested` while it waits (killing the worker and relaying the markers already sent), and `deliver` returns only after its worker is dead (D-141).
- [ ] Map library failures and markers to clear outcomes and ledger transitions.
- [ ] Add mocked adapter tests; do not contact the live television.
- [ ] Update third-party notices, status, and decisions.
- [ ] Commit.

## Phase 6 — Home Assistant app packaging

Owner: Claude

- [ ] Create current-format Home Assistant app metadata and option translations that state source applicability.
- [ ] Package the one-shot runtime and the persistent and media mappings, starting without `host_network`.
- [ ] Wire the entry point (`__main__`): logging with the redactor, a `CancellationController(start_deferred=True)` created before the SIGTERM handler is installed, the environment allowlist, the watchdog (fire time and start from `RunBudget`; if `RunResult.summary_emitted` is false, wait for the watchdog's exit instead of exiting), container-network discovery, and the options file.
- [ ] Create a modern multi-platform Dockerfile and a draft AppArmor profile in complain mode.
- [ ] Add local container build tests for supported architectures where available, including the D-130 checks.
- [ ] Once the Python version is fixed, repeat the Pillow wheel SBOM inspection against the exact two runtime wheels (`aarch64`, `amd64`). Record the result in `DECISIONS.md` and the third-party notices; it is authoritative for the bundled-library inventory.
- [ ] In the same inspection, verify the versions and SPDX identifiers of the remaining `pillow.libs` entries (libXau, libXdmcp, Brotli, libbsd, liblzma, libmd, libpng, libsharpyuv, libzstd). This is mandatory before packaging or publication (gate adjustment approved by Codex at `dda877c`).
- [ ] Write complete installation, configuration, capability-matrix, troubleshooting, and draft dashboard documentation.
- [ ] Update status and commit.

Gate: Codex reviews Home Assistant OS/Green compatibility and security.

## Phase 7 — Offline release validation

Owner: Codex and Claude

- [ ] Run full unit, integration, lint, type, timing, and container tests.
- [ ] Verify no excluded predecessor material is present.
- [ ] Verify dependency notices and the approved project license.
- [ ] Exercise the no-result, timeout, corrupt-history, failed-download, failed-decode, failed-upload, and upload-ledger paths.
- [ ] Produce a release-candidate report.

Gate: user approves live Home Assistant Green installation and television test.

## Phase 8 — Supervised Home Assistant Green validation

Owner: Codex with user supervision

- [ ] Install under a unique development slug without replacing another app (install route per Q-21).
- [ ] Preserve all existing Home Assistant configuration.
- [ ] Run a local-media test.
- [ ] Run Art Institute of Chicago and Cleveland Museum of Art tests, including a restrictive-filter fallback test, against `192.168.178.30`, entered in the options and never hard-coded.
- [ ] Verify Home Assistant Green-to-television connectivity without `host_network` before considering any change.
- [ ] Select and document one proven preview refresh mechanism. Verify, in repeated live tests covering card-started, automation-started, app-page-started, and no-match runs, that each newly delivered image is shown without a stale browser cache (release-blocking).
- [ ] Verify history, the upload ledger, cleanup, finite stop within 120 s (no-match within 70 s), the loading indicator, and no stale temporary files.
- [ ] Record the entity IDs and the proven refresh mechanism. Complete the dashboard card, script, and timer, except for the public slug.
- [ ] Remove or retain the development installation only as directed by the user.

Gate: user approves release hardening, public publication, and final name.

## Phase 9 — AppArmor, release hardening, and public beta

Owner: Codex and Claude

- [ ] Switch the AppArmor profile to enforce mode and verify the whole isolation design, with an approved supervised live re-check.
- [ ] Create the user-approved public repository under `volkue-tech`.
- [ ] Complete the qualified licence review (D-135) as a release gate: `samsungtvws` (LGPL-3.0), the Pillow-bundled `libimagequant` (GPL-3.0-or-later) and FriBiDi (LGPL-2.1-or-later), and the Alpine base packages.
- [ ] Add the Apache-2.0 licence for project-owned code, and third-party notices with the GPL and LGPL texts and copyleft source availability.
- [ ] Configure GitHub Actions for tests and multi-architecture GHCR publication.
- [ ] Publish immutable versioned images for `aarch64` and `amd64`.
- [ ] Add the one-click Home Assistant repository link.
- [ ] Finalize the dashboard card with the slug observed after installing from the public repository.
- [ ] Verify clean installation on Home Assistant Green from the public repository.
- [ ] Publish release notes and known limitations.
