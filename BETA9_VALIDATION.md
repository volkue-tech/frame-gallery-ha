# Beta 0.1.0b9 — native validation and publication

2026-10-18. Both native validators, actual publisher images, matching public
sources and independent anonymous image/signature checks passed. The
[app prerelease](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b9)
is public (release 416479944). This documentation-only handoff accompanies the
Store update; runtime/source stays frozen at 234eac5.
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
  was preserved, not waived; corrected native gates were repeated in full.
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

## Hosted native validators

[Publisher run 39130904153](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/39130904153)
passed its exact-commit/source approval gate and both reusable native validators
at frozen runtime/source 234eac513427e7ef75e5cd97ce238542c33b96d7.
Both downloaded ZIPs match the API byte count and SHA256. Strict completed-run
provenance, bounded safe extraction and content checks confirm full host gates,
5759 container tests/eight root-only skips, all eight separate root checks,
26 preparations under real 1 GiB RLIMIT_AS and 150 inspections without failures.

| Native validator | Peak virtual memory | Slowest preparation | Evidence ZIP SHA256 |
| --- | --- | --- | --- |
| ARM/aarch64 | 771.6 MiB | 2.25 s | d780167862154b591ab12a6d8f2f416152a4d65ab665f01e5e5941029653e043 |
| Intel/amd64 | 768.0 MiB | 2.06 s | c46adf63a6b692c82e6b19142efb26bd61d09238ed9a89c55071279042aab94b |

## Actual publisher images and independent verification

All five jobs in run 39130904153 completed successfully. Each actual publisher
repeated the container/root/measurement checks before pushing the validated
layers and signing the immutable digest. Both downloaded publisher archives
passed exact completed-run/commit/actor provenance, byte count/SHA256, bounded
safe extraction and content checks. Each contains 5759/eight skips + eight root
checks, 26 successful preparations under real 1 GiB RLIMIT_AS, 150 inspections
without failures and the 202-file original licence evidence check.

| Actual publisher | Artifact | Peak virtual memory | Slowest preparation | ZIP SHA256 |
| --- | --- | --- | --- | --- |
| ARM/aarch64 | 12138581993 | 771.6 MiB | 2.24 s | 2da88097388939f9205e61e23517338b482507423dfed19532527ec95bab2aa9 |
| Intel/amd64 | 12139235951 | 768.0 MiB | 2.78 s | 631124da7f81c7a26c795cd1affb3bceaacf1861d6ac03ef741766117b1c59e0 |

Independently anonymous tag/digest readback, exact-digest pulls and isolated
no-network/unprivileged imports passed for both images. Each exact 116-file
runtime source fingerprint matches
034b9db98153955628f9e3a633a2ff90f7d7fee2edd741af51083f7e0f5b097f,
with b9 version, unchanged 1000-work catalogue/557 artist choices, default-off
background mode and empty production reviewed-profile registry. Intel imports
on this ARM Mac are emulated inspections, not the separate native CI proof.

Cosign independently verified each digest against the publish.yml certificate
identity on refs/heads/codex/commons-default, issuer
https://token.actions.githubusercontent.com and frozen source commit
234eac513427e7ef75e5cd97ce238542c33b96d7. Embedded publisher digests match exactly:

- ARM: sha256:e3cdc11c015289c4060aa2dc4c41958f9e3518882da17a9e3fbaaad3dab1aa26
- Intel: sha256:ba02dc1aff25e6617adf32d9fc2e43984773c9498179d2ebc4d406939c15b46e

The personal Firefox session saved and independently read back both temporary
release approvals as DISABLED_AFTER_0.1.0b9. Token permissions were not expanded.
No token was written to a file/log; the finite personal broker is ended after
the final push. Final public Store readback, extra main-triggered validation
and credential-closure receipts are recorded after handoff under the git-ignored
build/current-artwork-b9-release directory, separate from the frozen runtime.

## Local handoff rerun

The unchanged suite was also repeated during publishing. The first Codex-sandbox
run failed two macOS group/setgid workspace checks (5749 passed/16 skips), with
the original failure log retained, SHA256
6469c3b3775f35db605bb831bd737b93bd13e47e3c96a853cb0421634c14d414.
Both exact checks passed outside that sandbox (two passed), then the entire
unmodified gate passed outside it: 5751 passed/16 Linux-only skips, strict mypy
on host/Linux over 295 files, Ruff/format/licence/configuration checks and 100%
whole/mandatory line+branch coverage (11252 statements/2670 whole branches).
No test, skip or protection was changed to obtain this result. Successful rerun:
build/current-artwork-b9-release/handoff-gates-unsandboxed.log, SHA256
ad4c247f2d22e4ab04c15992edc9ded3191e7c16c21e20aee2cc214de02adb0f.

## Release gates

- [x] Full offline suite: 5751 passed/16 Linux-only skips, strict host/Linux
  typing over 295 files, Ruff/format, 100% whole/mandatory line+branch coverage,
  complete committed licence/configuration checks. Source-package gate separate.
  Final post-Expat gate log SHA256:
  ddeb606ff43c15b312df831775aeeecbdd542a567c7452ee36920a165999145f.
- [x] Native aarch64 and amd64 validation, real confinement/root checks and
  RLIMIT_AS image measurements; no emulation claim for native Intel.
  Local native ARM corrected inventory/container checks pass 5759/8 skips +
  8 root checks. The earlier inventory-failed image's separate measurement used
  the same b9 runtime/actual Expat 2.9.0: 26/26 cases under real 1 GiB RLIMIT_AS,
  maximum 1.63s/771.6 MiB VM, 150 inspections/no failures. No failed overall run
  is relabelled green. Both native CI validators have now repeated all checks;
  actual publisher images also repeated them before registry publication.
  A separate unprivileged/network-none/256-MiB store stress passed at 2048
  records: 25.1-MB primary + backup, replacement 1.5468s, peak RSS 138900 KiB.
  Neither local ARM result is a new HA Green/TV live test.
- [x] Exact clean personal commit 234eac513427e7ef75e5cd97ce238542c33b96d7,
  pushed to codex/commons-default. Matching public
  [source package](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b9):
  release 416381333, asset 653191970, 581365760 bytes, SHA256
  596574599fd80406355025147604687977645462e314faa1b415ee84eca35fb6.
  Anonymous full download and every-member/exact-clean-commit preflight passed;
  174 retained upstream source archives, no credentials/user state/artwork files.
  Later documentation-only closure does not change this frozen runtime/source.
- [x] Both actual publisher images pass checks, immutable tags and OIDC signatures.
- [x] Anonymous image pulls/imports and independent signature verification.
- [x] App prerelease v0.1.0b9 published after green checks, not just a source tag.
- [x] Both temporary publisher approvals visibly disabled/read back.

Store/main handoff uses this documentation-only commit after the green checks;
anonymous byte readback and the final automatic main CI run are separate closure
receipts. No installed HA app or dashboard is changed by publishing this beta.
