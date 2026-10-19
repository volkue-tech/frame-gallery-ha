# Beta 0.1.0b11 — optional experimental wake recovery

2026-10-19. The [app prerelease](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b11)
is public (release 417073722), after both native validators, actual publisher
images and independent public-image/signature checks passed. Frozen runtime/source:
ee91eef7267f3a8e3d833553030f0e1a3a2db97c.
This documentation-only handoff does not change that runtime. No installed HA
update, TV connection, image send or dashboard change is part of this round.
The installed b10 was left stopped; no new live or universal no-wake pass.

## Scope and explicit limits

D-238 adds optional `resume_state_entity`, unset by default. With experimental
background mode enabled, the app reads only the configured existing Samsung HA
media-player/remote cache every five seconds. After an observed off state and
a newer on transition at most 30 seconds old, it consumes one attempt before
preparing a read-only session. Startup-on, duplicate, stale, future, conflicting,
reordered and unknown states, cache gaps and clock reversal do not authorize
recovery. At most six attempts are permitted in a rolling hour. Failure never
retries that edge; authentication refusal latches automatic attempts off.

HA on is a connection trigger, not Art Mode evidence. The local preparation
requires the intact saved TV pin and a prior confirmed-upload association for
the same device and target fingerprint. It does not enroll, repin, send or
select a picture. A new isolated session must prove actual TV identity, Art
Mode, current image ID and matching image reference before confirming a caption.
Corrupt/unreadable credentials cannot become a tokenless fallback. A legitimately
absent token is distinct and still requires the explicit limited grant and
existing device/upload evidence. Unknown old images remain unidentified.

Natural-sleep evidence shows that the server closes the old connection; the
existing cached Samsung entity has no Art Mode attribute. The user therefore
explicitly accepted a limited experimental reconnect after a fresh HA edge.
Offline simulations cannot establish that making that connection is physically
side-effect-free. It may wake the TV or affect its mode. No all-model/firmware
support or no-wake guarantee is claimed. The 90-second initial proof and
900-second slideshow proof limits are unchanged; display gaps remain possible.

Existing camera/timer/script/card IDs, last-sent preview, artwork associations,
history, 1000-work catalogue, filters and dependencies remain compatible. No
helper, dashboard extension, configuration.yaml change, host network or extra
Green privileges. The exact parent-only AppArmor backup-link pair now includes
the existing artwork-deliveries.json archive; no broad worker/container rule.

## Offline evidence

Full unchanged host gates pass 5865 tests/16 genuine Linux-only skips, strict
host/Linux typing over 301 files and 100% whole/mandatory line/branch coverage.
The final implementation run took 51.18 seconds. A full repeat after the
five-language entry-guide edits took 51.67 seconds, also 5865/16 skips and 100%.
No test or protection was excluded. Repeat evidence:
`build/current-artwork-b11-release/handoff-gates.log`, SHA256
7e38e723ea2ef062f715edc963994bd0824840660c18d284c7d6fbc92abdbf1d.

The final complete pre-push rerun also passed: 5865 tests/16 skips in 50.00s,
301-file strict host/Linux typing and 100% line/branch coverage. Retained log
`build/current-artwork-b11-release/handoff-final-gates.log`, SHA256
e10c3fb4e3ad428761e280afa7e193314adc4a4f12d431cf980f86b930307887.

Actual service-entry tests use fake Core/TV transport with real option parsing,
stores, publication and controller wiring. They cover two no-send sleep/wake
cycles, known/unknown/mismatched images, another TV, TV-program mode, observation
and HA authentication refusal, publication failure and shutdown during a read.
Pure gate tests cover freshness, restart, replay, gaps and rate limits. Local
binding tests preserve target/archive/preview bytes and reject corrupt pins,
archives or tokens without any network call. An inventory regression enumerates
every backup-enabled store and checks its exact parent AppArmor link pair.

These are authored simulations, not new hardware observations. Older controlled
slideshow/sleep tests remain historical evidence for their own stated scope.

## Native and public-image evidence

[Exact publisher run 39219940581](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/39219940581)
completed all five jobs successfully at the frozen candidate. Four archives
passed exact completed-run/repository/actor/branch/commit provenance, API byte
count/SHA256 and bounded safe extraction/content checks. Each records 5873
production tests/eight root-only skips, eight separate root tests, 26 successful
preparations under real 1 GiB RLIMIT_AS and 150 inspections without failure.
Native validators also include full host quality gates; each image contains
the 202-file original public licence evidence bundle.

| Evidence | Artifact | Peak VM | Slowest preparation | ZIP SHA256 |
| --- | --- | --- | --- | --- |
| Native ARM | 12171603952 | 771.6 MiB | 2.30 s | 186a1d4a3e17b34aca4ffde527b8148ea1d4a96fbdae98a9f700120f4f4e4c01 |
| Native Intel | 12171494343 | 768.0 MiB | 2.38 s | c775f2c2f303b0d473ac48f702c9cf3d6e8c40a506a381757bcfd4220fde901e |
| Actual ARM publisher | 12173086363 | 771.6 MiB | 2.25 s | 0da3a7a572461f08f5702a6a2e6d5c74cc9c11f10229d3e6edb8b24b46deeb99 |
| Actual Intel publisher | 12173410439 | 768.0 MiB | 2.75 s | 22ccebfa58ad83fce854ad87156aad411544696696b3ff6269ff10b516e01834 |

Anonymous tag/digest readback, exact-digest pulls and isolated unprivileged,
read-only/no-network imports passed for both images. Each has version b11,
1000 works/557 artist choices, background default OFF and resume_state_entity
default None. The pure boot-on/off/on/duplicate gate assertions and the exact
117-file runtime fingerprint passed:
42860592a050a7e35bf4c2b282966b8b49002ed37ecd34d8c6d4908edc1422dd.
Intel imports on this ARM Mac are emulated inspections, not native Intel proof;
the separate hosted Intel jobs provide that proof. Immutable digests match the
actual publisher evidence:

- ARM: sha256:6e608c3fe7c9452db026afcda92fbb19568c57cab786c813b9bdbe19d3c4ae2e
- Intel: sha256:e791669e1bd3084011818b0b40ac30f906620779523ec2a79b901869cbafad2a

Independent Cosign checks bind both digests to the exact frozen source commit,
publish.yml on refs/heads/codex/commons-default and issuer
https://token.actions.githubusercontent.com. No personal registry credentials
were used for these public pulls/signature checks. The app itself was not run
against HA or the TV.

## Matching sources and release handoff

The [source-only release](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b11)
was public and independently downloaded anonymously before image publication.
Source release 416739575, asset 654593876, 581488640 bytes, SHA256
28510bf857a03ff1a04ab871261d0f83e69a8654798e4290e61a26cc5a76c01c.
Every member and the exact clean project snapshot passed preflight; 174 retained
upstream source archives. Unrelated untracked docs/community was not touched.

Both one-time approval variables were saved and independently visually read
back as DISABLED_AFTER_0.1.0b11 after the successful release. Neither token rights
nor Green privileges were expanded. The documentation-only Store/main handoff
retains all complete YAML/code blocks and the frozen runtime/config/workflows.
The memory-only broker is ended after the final push. Public byte-exact Store
readback (including the changed AppArmor profile), any additional automatic
main CI and exact process closure are post-push receipts, not results
pre-claimed by this pre-push documentation snapshot.

All private receipts live under `build/current-artwork-b11-release`; no
credentials belong in this report. Native Terminal/window control is unavailable;
only completed task-owned sessions may be closed, never unrelated user work.
