# Beta 0.1.0b13 validation

## Candidate scope — D-240

Fix reproduced duplicate initial-read dispatch around the existing dashboard
send. The service receives commands before ticking. A fixed ten-second
monotonic handoff defers the initial read while the existing script requests an
image. Claimed NEW_ARTWORK consumes initial and old off-edge evidence before
reap/publication/send; failure, no_match, unchanged receipt or failed post-send
proof cannot revive it. Only a fresh successful delivery arms its receiver.

Without a send, standalone configured initialization remains available once
after the handoff and continued valid cached on. Invalid/missing/off/unknown/
error/gap cancels pending evidence. Fresh later off/on, authentication refusal,
six/hour limits, exact per-device attribution and 90/900-second ages remain.
No field, helper, dependency, special Green permission or installed-card change.

The handoff cannot predict arbitrarily delayed actions. A later explicit send
must still reap an already established standalone receiver. The physical cause
of the reported Art-to-TV incident is not proved by the saved event_rejected
reason or these offline replays. No changed-runtime hardware/no-wake guarantee.

## Offline evidence

The unnumbered D-240 source passed all unchanged host gates: 5,943 tests passed,
16 genuine Linux/root-only skips, strict host/Linux typing over 303 files and
100% whole/mandatory line and branch coverage. Three in-memory negative controls
fail when grace, accepted-send supersession or input priority is removed.
They do not alter source files. Original sandbox group/setgid failures remain
retained; the complete normal-permissions runs pass without weakening tests.

The numbered b13 candidate also passes the unchanged complete gates: 5,943/16
platform skips in 58.48s, 303-file strict host/Linux typing, Ruff/format and
100% coverage (11,491 statements/2,744 branches; mandatory 8,769/2,028).
All five complete current-card YAML blocks are byte-identical to b12.
Preserve existing cards/scripts and
unrelated untracked docs/community. No HA/TV connection, installed-app update/
start or dashboard edit is part of this authorized publication round.

## Native and public gates — pending

Before public app/Store handoff: freeze an exact personally authored commit;
assemble and anonymously verify every member of matching public sources;
pass both native validators and actual publisher images; verify four bounded
evidence archives, exact public image imports/fingerprints and independent
signatures. Only observed results may replace this pending status. Disable both
exact approval variables and end the memory-only broker after the final push.

Earlier b12 results are historical, not changed-b13 evidence. Publishing never
starts/updates installed HA apps, sends an artwork or edits cards/scripts.
