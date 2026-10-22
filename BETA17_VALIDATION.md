# Beta 0.1.0b17 validation

**Observed exact-source release checks passed.** Host, matching public
source, native ARM/Intel, all four independent evidence archives, both public
image probes and signatures below are verified results, not copied expectations.
No HA/TV connection or physical firmware/no-wake test was performed.

## Scope and exact source

This beta combines the D-247 automatic-observer-I/O safety hold, D-246 bounded
optional current-image preview and D-249 initial-thumbnail preview correction.
It does not establish the physical cause of the reported wake/TV-mode incident
or a general firmware/no-wake guarantee.

- Frozen source: `edae2271dbd103edd80db629d097f91e895d97a2`.
- Version: `0.1.0b17`.
- Runtime: 121 files, aggregate SHA256
  `f7ef6bf86dd28d69f86ed22b8d7dd912dce8f29390afa5158b15531b4033679b`.
- Matching public asset: [frame-gallery-sources-0.1.0b17.tar](https://github.com/volkue-tech/frame-gallery-ha/releases/download/sources-v0.1.0b17/frame-gallery-sources-0.1.0b17.tar),
  581,888,000 bytes, SHA256
  `2f31e831713e3702f1fbd12d38fb273e7a2a677d3a07a412f594e7b428a61e46`.
  Source-only release ID 420919092; asset ID 666336778.
- Matching sources must be anonymously verified before any image distribution.
- No HA/TV connection, app install/start/update or existing card/script mutation
  is part of these build/publication checks. The installed app remains stopped.

## Observed host and offline checks

The frozen source passed 6,228 tests with 16 unchanged platform skips, Ruff and
format checks, strict host/Linux typing over 318 files, 100% whole line/branch
coverage (11,984 statements / 2,918 branches) and 100% mandatory-package coverage
(9,132 / 2,148). No gate threshold, test expectation or platform skip was waived.

The real image prepare/send/store/reopen/publisher pipeline covers one-shot and
background receipts and initial verified-thumbnail publication. A session-local
proof selects the exact cached delivered bytes without changing caption
provenance. Old same-ID/same-work/different-crop bindings, receipt replacement,
wrong device, rejected image, missing cache, optional verification/read failure
and session invalidation are covered. A failed optional preview preserves an
already valid caption, never inventing new proof.

The existing incident replay, production-composition safety tests, eight virtual
hours and guard-removal negative controls are offline evidence only. Production
wiring cannot automatically open startup/wake Art sessions or issue minute
current-state GETs, including saved opt-ins. A configured Samsung entity is a
stop signal only. A fresh explicitly requested successful send can arm one
passive slideshow receiver. Static pictures expire; menu/TV mode, sleep and
connection loss do not automatically recover. Connection side effects remain
unproven; no new physical hardware result is inferred.

See the unchanged historical engineering reports
[current preview](CURRENT_PREVIEW_VALIDATION.md) and
[observer safety hold](OBSERVER_SAFETY_HOLD_VALIDATION.md).

## Observed native validation

Observed in each native validator and actual publisher image: 6,236 production
tests with eight platform/root skips, followed by eight separately executed root
checks. Every archive additionally records 13 worst-case preparations twice under
the real 1 GiB address-space limit and 150 inspections without failure.

- Exact workflow/run and five-job conclusion: [run 39825989063](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/39825989063), all five jobs successful at frozen source `edae2271dbd103edd80db629d097f91e895d97a2`.
- ARM validator: artifact 12447292418, 23,837 bytes, SHA256 `6271b7aaf920e184fcc483c525c47a97dd43be45569f0da9146676addb29a342`; 6,236 production tests / 8 root skips + 8 separate root checks; 13 cases × 2 under the real 1 GiB limit, peak 771.6 MiB, slowest 2.31 s; 150 inspections / zero failures.
- Intel/AMD validator: artifact 12446494897, 23,793 bytes, SHA256 `2fccbceea3d080df45eafae00963bc965834e57986221f36bc006c61e0cf2ea1`; 6,236 production tests / 8 root skips + 8 separate root checks; 13 cases × 2 under the real 1 GiB limit, peak 768.0 MiB, slowest 2.76 s; 150 inspections / zero failures.
- Actual ARM publisher image/root/memory/source checks: artifact 12449160610, 21,046 bytes, SHA256 `98b4e3e1a7c34a854530f01e02c1cf0d04357200054f315312adf1ebce8e72d7`; 6,236 production tests / 8 root skips + 8 separate root checks; 13 cases × 2 under the real 1 GiB limit, peak 771.6 MiB, slowest 2.32 s; 150 inspections / zero failures.
- Actual Intel/AMD publisher image/root/memory/source checks: artifact 12448427491, 21,087 bytes, SHA256 `8ea30ada8eba99ccb7455470e02467c68e9330ef48a5603395a7f36fb51c8b4d`; 6,236 production tests / 8 root skips + 8 separate root checks; 13 cases × 2 under the real 1 GiB limit, peak 768.0 MiB, slowest 2.46 s; 150 inspections / zero failures.
- Four independent archive provenance/content/hash checks: passed for exactly the four run/source-bound artifacts above; unique safe members, downloaded ZIP length/SHA256, native architecture, full suite/root/memory/licence evidence and publisher digests were checked.

## Observed anonymous images, signatures and app publication

- Anonymous source download and exact snapshot/every-member verification passed
  before native CI dispatch. The downloaded version, frozen commit, byte length
  and SHA256 match the independently recorded source receipt. All-member
  snapshot verification includes 174 retained dependency-source archives, not
  a claim that the whole source package has 174 members. This does not establish
  any native/image result.
- ARM immutable image digest and independent runtime/safety/preview probe:
  `ghcr.io/volkue-tech/frame-gallery-ha-aarch64@sha256:f425e4fd83577a56fef47ac0404b77acef0266cb469243802792ce50cbb9564c`; exact 121-file runtime hash plus parser, stop-only/default-deny, per-device cache and real initial-thumbnail-to-preview publication probes passed in a read-only, non-root, networkless inspection container.
- Intel/AMD immutable image digest and independent runtime/safety/preview probe:
  `ghcr.io/volkue-tech/frame-gallery-ha-amd64@sha256:fd9e8dab84979d0a36232813865a6d77367ce3d2634e5951e82d675ac0e299dc`; the same exact-runtime/safety/preview probes passed. This Mac image inspection is not the native Intel validation; the separate exact CI jobs above supply that evidence.
- Independent keyless signature/source/workflow verification:
  both immutable digests verified anonymously with the pinned Cosign tool, expected GitHub workflow identity, `https://token.actions.githubusercontent.com` issuer and exact workflow source `edae2271dbd103edd80db629d097f91e895d97a2`.
- App prerelease and exact frozen target: [prerelease 421060980](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b17) targets `edae2271dbd103edd80db629d097f91e895d97a2`; successful HTTP 201 response, actual ID, tag, body and prerelease/non-draft status match the planned payload.
- Both exact build approvals disabled and read back: both `FRAME_GALLERY_RELEASE_APPROVED_SHA` and `FRAME_GALLERY_RELEASE_SOURCE_SHA256` were read back as `DISABLED_AFTER_0.1.0b17` in the authenticated GitHub UI; no permissions expanded.

The final handoff must change exactly the 22 approved documentation files,
preserve all 21 complete code fences and retain the exact 121-file runtime,
config/defaults/schema, workflow, dependency, privilege and script bytes.
Final anonymous main/Store/docs/source readback and memory-only broker shutdown
are operational closure checks; they must not be claimed before they occur.

## User-visible limits

Background observation remains experimental and OFF by default. Existing
saved options, IDs, associations, cards and scripts remain compatible. In b17,
initial/wake reconnections and minute reads are suspended even when previously
enabled. Unknown artwork never borrows another title or preview. Proof expires
after 90 seconds initially or at most 15 minutes for a complete slideshow event.

The optional preview is a cached derivative, not a live TV screenshot. It has
at most 640×360 pixels and 32 KiB JPEG bytes per entry; private storage is
bounded to 128 MiB including JSON/base64 overhead and 4,096 entries. Eviction
never clears associations/history. Availability is invalidated in HA before
the atomic current-file change and advertised only after verification. Existing
latest.jpg and cards remain unchanged. Old/uncached works have no preview.
No new TV request, connection, dependency, app option, permission, HACS extension
or configuration.yaml edit is required. Green/HAOS users need no special rights.

The app image includes components under their own licences, including copyleft
components; corresponding sources/notices remain required. This is engineering
evidence, not independent legal advice or universal device compatibility.
