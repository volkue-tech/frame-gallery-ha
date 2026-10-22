# Local observer safety hold — D-247

Prepared on 2026-10-22; local and unpublished. The installed b16 app remains
stopped. This task makes no HA/TV connection, image send, power/mode command,
installed update, card/script edit, GitHub access or release. No native Terminal
window was opened for this offline implementation.

## What the evidence establishes

The already saved normal HA Recorder shows two later off/on transitions at
16:13:29/16:20:05 and16:35:09/16:36:29 CEST. The observer's checking states follow
the HA on observations, not the reverse. Low consumption0.71/0.78W was sampled
at16:15:52/16:17:57; the second off transition has25.03W, not sampled deep-sleep
proof. Neither generic HA on nor power alone distinguishes Art Mode from TV
programme. Both existing activity-detail views record no reason. The retained
last100 app log lines show no new image send in this incident window and do not
record every successful connection or getter payload.

The user subsequently confirmed manually switching TV programme off, returning
the Frame to Art Mode; exact time is unknown. Later art-ID reports are therefore
not independent evidence contradicting the initial TV-programme observation.

These data do **not** identify a proven physical cause. The observer cannot be
exonerated either: a connection after HA on could have a firmware side effect.
Motion wake, other integrations or remote actions are not excluded by this
limited history. Do not present this software mitigation as a reproduced or
definitively repaired firmware fault.

## Confirmed software weakness and mitigation

Previously, a generic initial HA on or fresh off/on edge could authorize an Art
connection, although neither establishes physical Art Mode. Initial reads open
the device-info/Art/thumbnail paths; optional minute reads continue on the Art
socket. There is no explicit observer power/mode setter, but that does not make
the connection or getters proven side-effect-free.

The regular entry now has three barriers:

1. `CachedStateStopMonitor` never returns RESUME. Optional cached Samsung state
   can only stop on off/missing/unknown/unavailable/error, invalid clocks/samples
   or a sampling gap. No configured entity means no extra Core read.
2. The production controller has its default-deny resume hook; no
   `HostObserver.prepare_resume` or keep-TV-session exception is wired in.
3. The production observer receives `current_state_refresh=False` regardless
   of a saved true option, so a delivery grant selects passive slideshow policy.

Historical edge/query implementations remain available for isolated offline
replays, not selectable by ordinary saved options or service commands. New
settings, dependencies, permissions, disk limits or data migrations are absent.

A fresh successful explicit send retains one bounded receiver and initial
identity/mode/current-image proof. Complete passive changed-ID slideshow events
still resolve known per-TV metadata; unknown IDs remain unidentified. Off,
standby, auth/transport/publication failure closes/disarms without an automatic
restart. Navigation clears metadata and may receive a later complete sequence
on the same socket, with no follow-up application query.

This intentionally reduces functionality: no initial already-on synchronization,
no automatic post-sleep recovery, no minute refresh of an unchanged picture.
Existing freshness limits still clear expired captions rather than inventing
confirmation. A later explicit successful send is needed to arm a new session.
The remaining explicitly triggered connection is not a universal no-wake
guarantee. Five-language help and guide notices disclose these restrictions.

## Offline evidence

All evidence is under the ignored `build/b16-safety-fix-20261022-29tRyg/`.

- `regression-before.log`:21 failures/35 passes on the old real-entry wiring.
  The new assertions detected automatic sessions or a state-refresh policy
  despite the required hold; no real network access occurred.
- `regression-after.log`:56 affected entry cases passed after the mitigation.
- `targeted-all.log`:140 entry, monitor, pinned-library socketpair and packaging
  cases passed before the final auth-revocation case was added.
- `incident-replay-result.json`: the unchanged private Recorder evidence
  (SHA256 c2dec5f685211d9baa3118bcf9e1d9d7e5cc42c1f4b82ca5791e9a9ad5c349f3)
  is resampled into1698 five-second virtual samples. Historical edge policy
  grants3 resumes; the new monitor grants0, with114 stop samples. This is an
  authorization replay, not a capture of every original poll or a firmware test.
- Three independent in-memory negative controls re-enable periodic reads,
  restore the resume hook or discard stop signals. Each targeted assertion
  fails as intended; source/test files are not changed by the controls.
- A separate real-entry test injects an unexpected RESUME from the monitor;
  the default-deny controller barrier still prevents a TV session.
- Eight virtual hours of initial on and sleep/wake cycles yield only NONE/SLEEP.
  Passive-session HA failure and TV auth revocation close/latch without recovery.
- `compatibility-result.json`: exact config/schema/defaults, app profile, full
  send script and TV/binding implementation files match the previous local
  preview commit. All five complete current-artist YAML blocks are byte-identical.

The full suite uses its H2 outbound-network guard, including isolated workers.
Final frozen command: `bash frame_gallery/scripts/check.sh`, outside the local
filesystem sandbox for the existing POSIX-permission/process tests, completed
successfully. `host-gates-frozen.log` records6197 passed/16 unchanged platform
skips in54.99s; Ruff/format and strict host/Linux typing cover317 files. Whole
coverage is100% (11947 statements/2904 branches); mandatory coverage is100%
(9132/2148). No native ARM/Intel or hardware inference is made from this run.

The first full attempt stopped at a strict test-import typing error, corrected
by importing the monitor from its defining module. A subsequent full run passed
6196/16 but left one legacy auth-latch branch unexercised after entry quarantine;
the explicit-session revocation regression restores that coverage. No skips or
coverage thresholds were added or weakened. An intermediate four-case failure
also exposed a test-fixture expectation (its baseline is deliberately
UNIDENTIFIED, not ARTWORK); the test now checks that exact existing observation.

## Remaining boundaries

No new native ARM/Intel container or Green/hardware run is claimed. Published
and installed code are not changed. A future release needs separate authority
and exact-source native/source/image/signature gates. Physical no-wake and
mode safety cannot be established from offline simulation alone. The original
incident's cause remains unresolved even though these automatic I/O paths are
removed from the local production wiring.
