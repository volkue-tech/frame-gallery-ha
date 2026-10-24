# D-252 — Art-only steady confirmation, local/offline candidate

Historical local evidence retained below. Its implemented runtime is included in public beta0.1.0b19; see [observed native/public gates](BETA19_VALIDATION.md). This does not add a physical no-wake guarantee.

2026-10-24. Not installed, published or assigned a new version. Existing live
cards/scripts/app settings were not accessed or changed during this task.

## Why this change exists

The preceding read-only b18 diagnosis found a successful wake confirmation at
11:05:43 CEST followed by `checking/proof_expired` at11:07:12. The90s initial
proof expired without another accepted image observation; HA on and an open
transport are not image proof. No current raw-event capture or physical mode
test was performed. That diagnosis is not a demonstration of a connection
failure or proof of why subsequent device events were absent.

## Implemented local contract

- NEW `confirm_current_artwork`, default OFF and absent from installation
  defaults. Old saved `current_state_refresh` remains ignored. Require background
  mode and an existing Samsung `media_player`/`remote` stop entity. This new
  option grants no startup, wake or other connection permission.
- Only after an independently granted session has verified the actual TV,
  Art Mode, current ID and initial image can this path use that same Art socket.
  No initial-off/menu deferral, new client, reconnect, keepalive, enrollment,
  image transfer, power or mode setter. Existing standby consent/budgets and
  successful-send arbitration stay independent.
- At most one `on / current / current / on` cycle per60s, with agreeing IDs and
  fresh exact response correlations. Retain the existing5s shared deadline,
  64-frame response limit,480-cycle budget and eight-hour session ceiling.
  Recorded `artmode_status`/`current_artwork` responses, including their real
  matte/target fields and id-only correlation, are accepted. Unknown extra error
  fields, wrong/mixed nonces or inconsistent IDs do not establish proof.
- During a quiet bounded read, keep the prior still-valid proof visible rather
  than displaying a checking flash every minute. Publish a fresh receipt only
  after a complete coherent cycle. Existing90s current-state and900s complete
  changed-slideshow evidence contracts and all card attributes remain intact.
- Drain queued standby/navigation/off notifications before any due GET. Those
  notifications, cached HA off/unknown/unavailable/gaps, cancellation, lost
  transport, unknown frames, malformed/ambiguous replies or timeout terminate
  without retry. No mode-only polling while in TV/menu mode. Fresh clock/proof
  gaps deny I/O; even a frozen clock with receive-only timeouts is finite.
- Parent rejects missing baseline, replayed and late strict confirmations too.
  Real per-TV association/cache lookup is unchanged. Known works retain their
  artist/title/preview; unknown/rejected/uncached works cannot borrow another
  work's metadata/image. No association is created by observing an image.

## Observed offline results

Evidence directory: `build/steady-confirmation-20261024.MuSFhY/` (ignored).

- Targeted final integration run: **264 passed in8.28s**. This includes the
  installed `samsungtvws`/WebSocket parser over local socketpairs, real recorded
  reply shapes, actual background-entry wiring, schema/defaults and five-locale
  help. Socketpair tests assert one Art transport, one initial thumbnail and
  exactly four additional GETs for a successful confirmation; queued standby
  adds none. No TCP/TLS/TV/HA/provider connection is involved.
- Complete host `bash frame_gallery/scripts/check.sh`: **6427 passed,
  16 unchanged platform/root skips in61.57s**. Ruff/format and strict host/Linux
  typing passed for326 files. Whole100% line/branch coverage:12328 statements /
  3032 branches. Mandatory100%:9282 statements /2198 branches. Thresholds and
  platform skips were not weakened.
- Quiet same-image replay:420 coherent cycles over seven virtual hours,
  1680 GETs on the identical transport, unique request nonces and no periodic
  checking publication. A separate replay ends at the original eight-hour
  lifetime without attempting a replacement connection.
- Counter-cases cover negative mode before/during a cycle, partial selection,
  changed/mismatched IDs, cancellation, missing/replayed baseline, stale clocks,
  backpressure, timeout, unknown/error fields, frozen time, no fresh grants,
  static/complete passive slideshow evidence and default/old-option safety.
- Three isolated in-memory guard-removal controls produced intended assertion
  failures: falsely freshening the baseline clock, inventing a confirmation
  without GETs, and accepting unknown error fields. No runtime file was mutated
  for these controls. An initial negative-control harness import failure was
  corrected; it was not counted as a successful negative control.
- Preservation check:22 guide files / **26 complete existing code fences**
  unchanged; full background-send script, AppArmor, Dockerfiles, dependency
  manifests/lock, workflows and version bytes unchanged. Supervisor metadata
  adds only the new optional schema key; no default or permission changes.
  All five configuration languages include the separate consent and limits.

## Limits and next gates

These are local macOS/offline results, not a native Green/Intel image result or
a physical no-wake/automatic-sleep/no-mode-switch certificate. Even a GET over an
existing socket might affect firmware or prevent natural sleep. A race between
physical sleep and its notifications cannot be ruled out by simulated inputs.
The path therefore remains separately experimental/default OFF; the installed
app, current cards, scripts and existing monitoring were left untouched.

The existing eight-hour session limit remains; this is not an unlimited watcher.
After menu/TV mode, transport or proof failure, the option itself never retries
or opens a connection. A later independently authorized send or complete opted-in
standby cycle is still required. No claim of recovery after every possible
device/firmware condition is made. Native validation, publication and controlled
hardware/sleep testing require their own later authority.
