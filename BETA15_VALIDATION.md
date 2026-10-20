# Beta 0.1.0b15 — same-connection synchronization candidate

No Home Assistant/TV connection is part of this task. Installed b13 remains
stopped. Existing native cards, scripts, data and privileges stay unchanged.
b14 is retained only as its immutable corresponding-source intermediate;
it was never promoted as an app/image/Store release.

## Behaviour and explicit risk choice

The separate experimental `current_state_refresh` switch defaults OFF and
requires a granted background Art session. At most once per minute it reads
mode/current/current/mode on that SAME socket, requires fresh correlated replies,
matching IDs and mode-on at both ends, and resolves only the pinned TV archive.
Unknown works borrow no title. Static/same/changed art and missed mode-on events
can recover without upload or a replacement Art connection.

Menu/Art-off clears captions but keeps bounded mode-only reads until fresh on.
Art-off is not physical standby. If startup sees off/nav, the original single
initial thumbnail proof is deferred until fresh on, under the shared five-second
deadline; no ID-only first caption or recurring thumbnail download. Standby,
HA-off, cancellation, refusal and closed transport stop without blind reconnect.
After an actual disconnect, only the existing explicitly permitted startup/
fresh HA off-on/delivery grants can open a new session. This is not an unlimited
reconnect mechanism or a literal guarantee after every possible fault.

Attempts share five seconds/64 frames, minimum60s actual attempt spacing even
with parent backpressure, at most480 in the existing eight-hour session.
No power/mode/image setter, keepalive, dependency or special Green privilege.
Fresh current-state proof ages after90s, compatible with unchanged native YAML.
Read connections/requests can affect automatic sleep: offline tests cannot
certify physical no-wake or sleep behaviour across firmware/configurations.

## Observed offline evidence

- Full unchanged check.sh:6044 passed/16 platform skips in50.87s.
- Ruff/306 formatted files and strict host/Linux typing passed.
- Whole line/branch100%:11700 statements/2826 branches.
- Mandatory100%:8932 statements/2088 branches.
- Actual pinned library over socketpair checks same Art URL, fixed getters,
  one original thumbnail, deferred off/nav startup, exact device and shutdown.
- Parent/controller covers caption clearing, single retained opted-in session,
  deferred baseline, known/unknown metadata and terminal standby.
- Earlier development typing failure retained, not skipped or weakened.
- Five in-memory guard-removal controls produce expected failures: coherent
  equal IDs, correlation, explicit policy, Art-off recovery and actual attempt
  spacing. They do not modify production or test source files.
- Eight virtual hours through the actual worker loop:479 coherent reads,
  1916 read requests, minimum60s spacing and finite shutdown without another
  send at the deadline. No real device or sleep-safety claim.

The b13 rejected frame was not retained; these synthetic cases do not claim
to reconstruct it or prove its physical cause. Native ARM/Intel actual-image,
source, artifact, anonymous-image/import and independent-signature gates remain
required before app/Store promotion. Final hashes/IDs are added only once observed.
