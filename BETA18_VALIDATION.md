# 0.1.0b18 — observed release validation

Exact [native run 39931258791](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/39931258791) passed all five jobs. Both native validators and both actual publisher images each passed 6,362 production tests with eight root skips plus eight separate root checks. All four exact archives passed independent provenance/byte-hash/content checks; matching public sources, both immutable public-image recovery/status/preview probes and independent source/workflow-bound signatures passed. No physical no-wake claim.

## Exact source and public matching archive

Frozen application/image source: `b37b4f4932997050db028c35423573d6cced1574`.
Runtime: 123 files, SHA256 `5ba2b96d4c12c5f0b86f361ed9a4f2aa61ed016818671485433b6a7fd2cf9f16`.
[Complete matching sources](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b18): 582,010,880 bytes, SHA256 `3ed99901d4bafbfd5bced457f9cbb864c0dc8140a44f8f450aaaec56d0d6a2f0`; source release 421648046, asset 668596086. Anonymous full download and every-member clean-snapshot preflight passed BEFORE native CI dispatch or image distribution. The archive includes 174 retained corresponding dependency-source archives/build materials/notices; previous assets/releases remain intact. This is engineering evidence, not an independent legal opinion.

## Observed host and native gates

Versioned host: 6,354 tests /16 unchanged Linux/root skips in 56.30s; 323-file Ruff/format and strict host/Linux typing. Whole 100% line/branch coverage: 12,228 statements /2,992 branches; mandatory 100%: 9,206 /2,170. No weakened threshold, dependency, skip or privilege.

- native-aarch64-validation: artifact 12492526809, 23,849 bytes, SHA256 `35f63f8a62a057a9b5511121cc4b467555e0d3d0eae0c6871dfb4fb6fad0d1d5`; 6,362 production /8 root skips +8 root checks; 13 cases ×2 under the real 1 GiB address-space limit; peak 771.6 MiB, slowest 2.31s; 150 inspections, zero failures.
- beta-aarch64-evidence: artifact 12493278227, 21,070 bytes, SHA256 `09145be115c87272c679ac9e2e796ca97fd27244d35727b5741e2d77630cc17c`; 6,362 production /8 root skips +8 root checks; 13 cases ×2 under the real 1 GiB address-space limit; peak 771.6 MiB, slowest 2.30s; 150 inspections, zero failures.
- native-amd64-validation: artifact 12493340156, 23,806 bytes, SHA256 `c1f7b7040be363d92bb1d7591f238d19f31842296fdf1affa80b820c1e44a174`; 6,362 production /8 root skips +8 root checks; 13 cases ×2 under the real 1 GiB address-space limit; peak 768.1 MiB, slowest 2.82s; 150 inspections, zero failures.
- beta-amd64-evidence: artifact 12494245831, 21,068 bytes, SHA256 `cc995be2b5d890577d380d027ef4c75598cdda9d15700d90601a99ceb82e6686`; 6,362 production /8 root skips +8 root checks; 13 cases ×2 under the real 1 GiB address-space limit; peak 768.0 MiB, slowest 2.85s; 150 inspections, zero failures.

All four ZIPs were matched to the exact run/source, artifact ID, GitHub length/SHA256, unique safe members, native architecture and full suite/root/memory/licence evidence. Native CI, not the Mac's isolated import check, supplies native Intel evidence.

GitHub also annotated the existing pinned checkout/setup/upload actions as using deprecated Node.js 20 metadata while being forced to run on Node.js 24. The unchanged workflow completed successfully; reviewing those action runtime pins is a follow-up, not a change made by this beta. This annotation concerns CI tooling, not an added app dependency.

## Public images, signatures and app publication

- aarch64: `ghcr.io/volkue-tech/frame-gallery-ha-aarch64@sha256:eba356686afaf437be9522aad21bfdde8b0418f3fcdcd6444e29ece1e95fd17a`; anonymous tag/digest match, exact 123-file runtime hash, read-only/non-root/networkless recovery/status/default-deny/preview probes and independent pinned Cosign signature passed.
- amd64: `ghcr.io/volkue-tech/frame-gallery-ha-amd64@sha256:36743b6697cb460bc4a604e50c8df595bf73534ae9ad0bffd489fe22d39bf2c5`; anonymous tag/digest match, exact 123-file runtime hash, read-only/non-root/networkless recovery/status/default-deny/preview probes and independent pinned Cosign signature passed.

Signatures require the pinned verifier, the exact immutable digest, GitHub workflow identity `https://github.com/volkue-tech/frame-gallery-ha/.github/workflows/publish.yml@refs/heads/codex/commons-default`, issuer `https://token.actions.githubusercontent.com`, and frozen workflow SHA above.

App [prerelease 421778494](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b18) targets the exact frozen source. Its successful HTTP 201 response, ID, tag, body and prerelease/non-draft flags were retained. Both exact build approvals were disabled and read back as `DISABLED_AFTER_0.1.0b18`. Store/docs promotion, final anonymous readback and credential-process exit are later operational closure checks, not pre-claimed by this commit.

## Scope, compatibility and important limits

NEW `standby_resume` is OFF by default, independent of old switches, and requires background mode plus the existing Samsung entity. The app must remain running and observe off for 30 seconds, then a genuinely fresh on stable for 10 seconds, before one exact-device/image revalidation. One-use grants and a durable private budget enforce six reservations/hour and at least 60 seconds apart across ordinary restarts. Corrupt/newer/unwritable state, HA/clock gaps and authorization refusal fail closed. Deleting/restoring private data can reset historical budget data; no rollback protection is claimed.

No boot-on or minute TV reads, image/power/mode commands, enrollment or blind retries are added by recovery. A lost session while HA stays on requires a new clean cycle. Static proof still expires after 90 seconds; complete changing-ID slideshow evidence after 900 seconds. Known captions/previews require fresh exact-device/image proof; unknown works remain unidentified. Finite status reasons distinguish stopped, standby, settling, passive waiting, expired proof and failure.

All 21 original complete examples and five NEW optional complete native status-card blocks remain byte-identical through the documentation handoff. Existing full script, helper IDs, associations, history, dependencies, AppArmor and privileges are preserved. The new cards are documented, not installed automatically; five-language template checks are structural/offline, not a new HA rendering claim.

No HA/TV connection or installed app/card/script mutation occurred during release. The unresolved physical wake/mode incident is NOT certified fixed. Read connections can have firmware side effects; offline/native tests cannot certify physical standby, automatic sleep or no-wake/no-mode-switch behavior. Keep the opt-in OFF if that risk is unacceptable. See [local case/replay evidence](STANDBY_RESUME_VALIDATION.md).
