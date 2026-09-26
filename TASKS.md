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

- [ ] Read all repository specifications.
- [ ] Research only permitted official documentation and approved dependency documentation.
- [ ] Write `ARCHITECTURE.md` describing original component boundaries, data flow, failure handling, storage, package layout, and test strategy.
- [ ] Compare dashboard filter approaches: helpers, Ingress, and future companion integration.
- [ ] Propose the first-release scope and defer nonessential features explicitly.
- [ ] Record proposed dependencies and licenses in `DECISIONS.md`.
- [ ] Identify unresolved decisions and risks.
- [ ] Update `STATUS.md`.
- [ ] Commit documentation only.

Gate: user and Codex approve the architecture before application code is written.

## Phase 2 — Core skeleton and contracts

Owner: Claude

- [ ] Create an original package structure from the approved architecture.
- [ ] Define provider, television, storage, clock/deadline, downloader, and renderer contracts.
- [ ] Add configuration validation and structured result types.
- [ ] Establish linting, formatting, type checking, and unit-test commands.
- [ ] Add contract-level tests.
- [ ] Update status and commit.

Gate: Codex reviews architecture conformance and independence.

## Phase 3 — Persistent history and image pipeline

Owner: Claude

- [ ] Implement atomic, recoverable, bounded history.
- [ ] Implement temporary-workspace lifecycle.
- [ ] Implement validated download and decode boundaries.
- [ ] Implement `contain` and optional `cover` rendering.
- [ ] Implement atomic preview publication.
- [ ] Add unit tests for cleanup, corruption, limits, aspect ratio, and image modes.
- [ ] Update status and commit.

## Phase 4 — Provider framework

Owner: Claude

- [ ] Implement the provider interface and bounded selection orchestration.
- [ ] Implement local media provider first.
- [ ] Implement Bing provider.
- [ ] Implement experimental Google Arts & Culture connector from permitted public behavior and documentation only.
- [ ] Implement combined filters, orientation checks, strict format budget, deadline, and landscape fallback.
- [ ] Add independently authored fixtures and tests.
- [ ] Update status and commit.

Gate: Codex reviews provider access patterns, bounding, fixtures, and legal boundaries.

## Phase 5 — Samsung television adapter

Owner: Claude

- [ ] Integrate the approved, licensed Samsung transport dependency.
- [ ] Implement connection, pairing-token persistence, upload, and select operations.
- [ ] Map library failures into clear application results.
- [ ] Add mocked adapter tests; do not contact the live television.
- [ ] Update third-party notices, status, and decisions.
- [ ] Commit.

## Phase 6 — Home Assistant app packaging

Owner: Claude

- [ ] Create current-format Home Assistant app metadata and option translations.
- [ ] Package one-shot runtime and persistent/media mappings.
- [ ] Create a modern multi-platform Dockerfile.
- [ ] Add local container build tests for supported architectures where available.
- [ ] Write complete installation, configuration, troubleshooting, and dashboard documentation.
- [ ] Update status and commit.

Gate: Codex reviews Home Assistant OS/Green compatibility and security.

## Phase 7 — Offline release validation

Owner: Codex and Claude

- [ ] Run full unit, integration, lint, type, and container tests.
- [ ] Verify no excluded predecessor material is present.
- [ ] Verify dependency notices and proposed project license.
- [ ] Exercise no-result, timeout, corrupt-history, failed-download, failed-decode, and failed-upload paths.
- [ ] Produce a release-candidate report.

Gate: user approves live Home Assistant Green installation and television test.

## Phase 8 — Supervised Home Assistant Green validation

Owner: Codex with user supervision

- [ ] Install under a unique development slug without replacing another app.
- [ ] Preserve all existing Home Assistant configuration.
- [ ] Run a local-media test.
- [ ] Run a restrictive-filter fallback test against `192.168.178.30`.
- [ ] Verify preview refresh, history, cleanup, finite stop, and no stale temporary files.
- [ ] Remove or retain the development installation only as directed by the user.

Gate: user approves public publication, final name, and license.

## Phase 9 — Public beta release

Owner: Codex and Claude

- [ ] Create the user-approved public repository under `volkue-tech`.
- [ ] Add the approved project license and third-party notices.
- [ ] Configure GitHub Actions for tests and multi-architecture GHCR publication.
- [ ] Publish immutable versioned images for `aarch64` and `amd64`.
- [ ] Add the one-click Home Assistant repository link.
- [ ] Verify clean installation on Home Assistant Green from the public repository.
- [ ] Publish release notes and known limitations.

