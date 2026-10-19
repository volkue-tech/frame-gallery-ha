# Beta 0.1.0b12 validation

## Candidate scope

D-239 adds one explicitly opted-in initial read from the first cached HA `on`
sample when background mode and `resume_state_entity` are configured. The
sample may have been unchanged for hours; it is a trigger, not Art Mode proof.
Consume the initial opportunity even on off/unknown/invalid/error and do not
retry. Retain the later fresh-edge gate and shared per-process six/hour bound.
The service consumes the initial gate before processing any queued command.

Reuse intact same-target/device upload memory and token checks, with no
enrollment, repinning, sender, image/power/mode command, new dependency or Green
privilege. Actual Art/ID/thumbnail verification must precede any artist/title.
Keep the same finite event receiver and 90/900-second proof ages. A static
picture can age out; no duplicate/pong/heartbeat fabricates fresh image proof.
Installed cards, script IDs, history, associations and configuration stay intact.

## Offline result

Full host gates pass **5,904 tests / 16 Linux-only skips** in 49.63 seconds,
strict host/Linux typing for 302 files and **100% whole-suite and mandatory
line/branch coverage**. The first sandboxed baseline stripped Setgid bits in
two unchanged filesystem tests; all four handover tests pass outside that
sandbox, and the complete candidate gate above ran there without weakening tests.

Cases cover old unchanged initial on, off/unknown/missing/future/malformed data,
one consumed opportunity, duplicate states/refresh, later wake cycles and cap,
new process start, pinned/wrong/unknown/changed artworks, missing archive/pin,
corrupt or absent tokens, auth/publication/cancel failures, static expiry and
queued-command ordering. Five-language help/guides retain complete native YAML.
No HA/TV connection or installed-card/app edit was made for this implementation.
An in-memory negative control restores the old no-initial-read policy: eight
new assertions fail and twelve safety cases still pass. The normal source then
passes all twenty new initial-gate cases. No production file is mutated by it.

## Native and public release gates — passed

Frozen runtime/source commit: `63ae34ca764919950746740c9e7bcad6e2d88f20`.
The matching [public source package](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b12)
is 581,539,840 bytes, SHA256
`9e9482938b1586a1828514e54c1b4c89ec6f8f0ad4a93b231353a0f980773227`.
Its anonymous download and complete commit/member preflight passed before
granting any image-publication approval. Runtime package fingerprint: 117 files,
`d04e74feaeef73e77dee0717aa6770a47f5c28e9c7d1d1af36a887dcc02f11f6`.

Exact [native run 39330930659](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/39330930659)
completed all five jobs successfully on that frozen commit. Native ARM and Intel
validators and actual publisher images each pass **5,912 production tests / eight
root skips**, plus **eight separate root tests**. All four GitHub artifact byte
hashes, provenance and bounded contents were independently verified. Each includes
26 real 1-GiB preparations (13 cases twice), ten isolated workers and 150
inspections with zero failures. ARM peak virtual memory was 771.6 MiB; Intel
768.0 MiB. The slowest measured cases were 2.30 and 2.78 seconds respectively.

Both public version tags anonymously resolve to the verified immutable digests:

- ARM: `sha256:f728c6015c0020bdb7b233c9dccf50418be871dc80f9ea29a79b9063047ffb12`
- Intel: `sha256:e4efa8001caf76fd2cb536e294cb4845a0e5fcad4b870d4ce8b998f77098c1ab`

Anonymous pulls, isolated imports, all 117 runtime-file bytes/fingerprint, version,
1,000-work/colour/artist data and initial/resume/default guards passed. Independent
Cosign checks pin each immutable digest, the candidate workflow branch, GitHub
OIDC issuer and exact frozen commit. Intel import on this ARM Mac is emulated
inspection; its native evidence is the actual GitHub Intel jobs, not that import.

Public app prerelease [v0.1.0b12](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b12)
(417819499) targets the frozen runtime/source commit. The final Store handoff is
documentation-only: runtime/config/workflows and eleven complete code/YAML blocks
remain byte-unchanged. Public readback and operational closure receipts are
retained locally under `build/current-artwork-b12-release`; no prior beta result
is substituted for a new gate.

## Hardware limits

The earlier private Lab6 already-awake trial read MY_F0185 on the user's Frame
with no physical picture/mode change reported. It is not this changed runtime's
live validation or a standby/non-wake test. HA `on` can be stale and does not
prove visible Art Mode. The read connection itself may wake/change some models.
Background and resume options remain off/unset by default. Publication does
not install the update on HA, start an app, send an image or modify a dashboard.
