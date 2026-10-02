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
- [ ] Measure the worst-case preparation natively on `amd64` under the real `RLIMIT_AS`. *Open: no native `amd64` host was available; the measurement under Rosetta is informative only (D-170). The gate decides whether and where it runs.*
- [x] Record the Buildx and QEMU rows (bundled with Docker Desktop, whose start the user approved on 2026-10-02 so that they can be used) and the SBOM approach (no SBOM tool is downloaded or installed without a separate approval), and propose answers to Q-06 and Q-10 (D-171, D-172).
- [x] Run an independent review of the Phase 6 commits; fix or record every confirmed finding (8 agents; 19 of 20 findings confirmed, all fixed or recorded; *Review records* in `DECISIONS.md`).
- [x] Update status and commit.

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
- [ ] Complete the qualified licence review (D-135) as a release gate: `samsungtvws` (LGPL-3.0), Pillow's fribidi-shim (LGPL-2.1-or-later; the runtime wheels contain neither `libimagequant` nor FriBiDi, D-171), the Alpine base packages, the tools outside apk (s6-overlay, tempio, bashio; R-33), and the exact form of libmd's "Public Domain" part.
- [ ] Add the Apache-2.0 licence for project-owned code, and third-party notices with the GPL and LGPL texts and copyleft source availability.
- [ ] Configure GitHub Actions for tests and multi-architecture GHCR publication.
- [ ] Publish immutable versioned images for `aarch64` and `amd64`.
- [ ] Add the one-click Home Assistant repository link.
- [ ] Finalize the dashboard card with the slug observed after installing from the public repository.
- [ ] Verify clean installation on Home Assistant Green from the public repository.
- [ ] Publish release notes and known limitations.
