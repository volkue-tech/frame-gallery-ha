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

## Release gates — pending

Exact frozen commit, matching public source package, native ARM/Intel validators
and publisher images, four provenance/hash-checked evidence archives, anonymous
image pull/import and independent signatures must all pass before publication.
They are not inferred from the host result or previous beta evidence.

## Hardware limits

The earlier private Lab6 already-awake trial read MY_F0185 on the user's Frame
with no physical picture/mode change reported. It is not this changed runtime's
live validation or a standby/non-wake test. HA `on` can be stale and does not
prove visible Art Mode. The read connection itself may wake/change some models.
Background and resume options remain off/unset by default. Publication does
not install the update on HA, start an app, send an image or modify a dashboard.
