# Beta 0.1.0b9 validation scope

Candidate preparation, 2026-10-18. Publication is authorized after green gates;
native results, public sources and published image checks are still pending.
This document does not turn a local check into a live hardware result.

## Changed feature

Every selected send persists metadata for the actual television and content ID,
even with background mode off. Existing capability-response identity is reused:
no extra delivery HTTP request. Compact exact-JPEG references are generated in
the existing image worker; the parent verifies the reference's output digest.
Bounded private atomic storage survives normal updates independently of preview
and selection history. Failed/uncertain sends cannot create confirmed receipts.

The opt-in service consumes a fresh persisted-delivery grant for one isolated,
finite event session. Five initial Art getters and one initial thumbnail, then
strict automatic slideshow events only: no polling, post-baseline thumbnails,
automatic reconnect or power/mode/image setters. Boot/restart/refresh cannot arm
a session. Unknown IDs have no artist; upload correspondence is tagged separately
from initial image proof. State-publication failures stop the observer.

## Packaging and compatibility

- Home Assistant OS/Green normal protected app; existing homeassistant_api and
  media mapping only. No privileged/full-access/host-network/security changes.
- Existing camera, timer, send-script entity ID, preview and caption helpers
  remain. Optional current-card guide includes complete native YAML in five
  languages. No configuration.yaml edits or custom dashboard extension.
- Existing catalogue, source pins, 1,000 works, filters and Python dependency
  versions stay unchanged. Background mode remains OFF. Alpine's new transitive
  libexpat=2.9.0-r0 is now explicitly pinned; exact source/recipe hashes and MIT
  COPYING retained alongside older evidence (D-236). First inventory failure
  was preserved, not waived; candidate gates must be repeated.
- In this development/release round no HA/TV connection is opened, no installed
  app is started/updated, and no user dashboard is edited. The user's b8 remains
  stopped/background OFF; private lab evidence is historical.

## Evidence limits

Controlled private predecessor candidates observed automatic slideshow changes
and one natural-sleep episode on one Frame. The known automatic artist-caption
hardware gate did not hit the one mapped work during random follow-ups; it is
still open. Offline known/unknown sequences prove software logic, not that
missing hardware transition. The changed b9 candidate has no new live-TV test.
No universal no-wake, firmware compatibility, manual-selection or sustained
eight-hour/Recorder-growth guarantee is made. Connections may still wake a TV.
External unobserved content-ID replacement/reuse cannot be excluded during
event-only listening. Initial contradictory pixel evidence rejects attribution.

## Release gates

- [x] Full offline suite: 5751 passed/16 Linux-only skips, strict host/Linux
  typing over 295 files, Ruff/format, 100% whole/mandatory line+branch coverage,
  complete committed licence/configuration checks. Source-package gate separate.
  Final post-Expat gate log SHA256:
  ddeb606ff43c15b312df831775aeeecbdd542a567c7452ee36920a165999145f.
- [ ] Native aarch64 and amd64 validation, real confinement/root checks and
  RLIMIT_AS image measurements; no emulation claim for native Intel.
- [ ] Exact clean personal commit, matching source package publicly accessible.
- [ ] Both actual publisher images pass checks, immutable tags and OIDC signatures.
- [ ] Anonymous image pulls/imports and independent signature verification.
- [ ] Store metadata/main updated only after both architectures are validated;
  temporary publisher approvals disabled and credential process ended.
