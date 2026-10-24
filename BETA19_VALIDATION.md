# 0.1.0b19 — observed release validation

Exact [native run 40100876404](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/40100876404) passed all five jobs. Both native validators and both actual publisher images each passed 6,435 production tests with eight root skips plus eight separate root checks. All four exact archives passed independent provenance/byte-hash/content checks; matching public sources, both immutable public-image steady-confirmation/recovery/preview probes and independent source/workflow-bound signatures passed. No physical no-wake guarantee.

## Exact source and sources-first gate

Frozen commit `0716050082ddb5eb0b08f73ce2d1eb5024987028`; runtime: 124 files, SHA256 `4b3cfe7c0df058093160f2c0c8e026738d0d8ecb80a565bb15e8961eff979414`.
[Matching sources](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b19): 582,092,800 bytes, SHA256 `50aec29806979b3046c07b8da03ad91bd570eb512f16df0c8dc3fcda686a8c36`; release 422751192, asset 672352550. Full anonymous download and every-member clean-snapshot verification passed BEFORE image distribution. Includes 174 retained corresponding dependency-source archives/build materials/notices; prior releases/sources preserved. Engineering evidence, not an independent legal opinion.

## Observed software checks

Versioned host: 6,427 passed / 16 unchanged skips in 59.14 s; 326-file Ruff/format and strict host/Linux typing. Whole line/branch coverage: 100% (12,328 statements / 3,032 branches); mandatory coverage: 100% (9,282 / 2,198). Initial sandbox run failed two unchanged setgid tests; the four group tests and full unchanged suite passed outside the macOS sandbox. No weakening/skips/dependency/privilege changes.

Exact public-image probe passed offline with all network/external commands blocked, including 420 strict same-socket cycles/seven virtual hours, unique correlated GETs, default denial and queued negative-mode suppression. Three child-memory guard-removal controls failed intended assertions. All 26 complete card/script code fences remain unchanged. Original implementation evidence: [D-252](STEADY_CONFIRMATION_VALIDATION.md).

The documentation-only handoff was rechecked with the complete unchanged host
suite: 6,427 passed / 16 unchanged skips in 60.03 s, with the same full typing
and 100% line/branch coverage gates. Its initial run caught five missing D-247
references in the new guide introductions; restoring those safety references
made all eleven focused guide tests and the full suite pass. No runtime or test
was changed to resolve the documentation regression.

## Four actual native archives

- native-aarch64-validation: artifact 12562848766, SHA256 `ca6e6a4e382e31f6dd92425282f5811eaceae34106789d0485281fb4214b58af`; 6435 tests +8 separate root checks,13 cases ×2, peak Vm 771.6 MiB,150 inspections/0 failures.
- beta-aarch64-evidence: artifact 12564075478, SHA256 `921e3aab88f2c2f54fb0e54260016a4cd1b62ad502dcf84bcc31f531a203c2af`; 6435 tests +8 separate root checks,13 cases ×2, peak Vm 771.6 MiB,150 inspections/0 failures.
- native-amd64-validation: artifact 12563381634, SHA256 `2f2aa8c8293554a7fc6fc1c1442bd0caa9c470838db5cccd4b236552d9605ea9`; 6435 tests +8 separate root checks,13 cases ×2, peak Vm 768.0 MiB,150 inspections/0 failures.
- beta-amd64-evidence: artifact 12564025906, SHA256 `2006a7c39c8799a35e1d4b652c0c6f9d714c5f51ae83e5d949db886ac30dbd03`; 6435 tests +8 separate root checks,13 cases ×2, peak Vm 768.0 MiB,150 inspections/0 failures.

The exact five-job run above used native Linux aarch64/x86_64, not Mac emulation. Each actual publisher independently verified matching public source members and validated its own runtime image, including root isolation, repeated worst-case memory below 1 GiB and 150 inspections. Four exact ZIP identities/lengths/API digests, source/run provenance and bounded extracted content were independently checked.

## Independent public images/signatures

- aarch64: `ghcr.io/volkue-tech/frame-gallery-ha-aarch64@sha256:adaa82be9e94c0edcf6a64f43d622400692194f388839d79502128fa4532bd1a`; anonymous version-tag/immutable-digest match,124-file runtime hash, non-root/read-only/networkless confirmation/recovery/preview probe and independent pinned Cosign verification.
- amd64: `ghcr.io/volkue-tech/frame-gallery-ha-amd64@sha256:2a870abea7017fded1c6d25bb038fab346141c30ed312573cafc0bb0209bba33`; anonymous version-tag/immutable-digest match,124-file runtime hash, non-root/read-only/networkless confirmation/recovery/preview probe and independent pinned Cosign verification.

Signatures bind exact digest, frozen source and `https://github.com/volkue-tech/frame-gallery-ha/.github/workflows/publish.yml@refs/heads/codex/commons-default`, issuer `https://token.actions.githubusercontent.com`.

## Scope and remaining physical limits

NEW `confirm_current_artwork` is experimental/default OFF and grants no connection. Only an independently granted/proven existing Art session may perform at most four GETs/minute, within 5 s / 64 frames and the original eight-hour ceiling. Negative mode, HA/proof/clock gaps or failures end without retry. Old switches stay held; b18 standby consent/budgets remain independent. No offline/native result certifies physical sleep/no-wake/no-mode-switch safety; prior firmware incidents remain unresolved. Existing cards/scripts/data/privileges preserved. No HA/TV connection or installed operation occurred in this release task.

App [prerelease 422786520](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b19) targets exact frozen source; successful HTTP 201 response retained. Both exact approvals disabled/read back as `DISABLED_AFTER_0.1.0b19`. Documentation-only Store promotion, final public readback and broker exit are subsequent closure checks, not pre-claimed by this commit.
