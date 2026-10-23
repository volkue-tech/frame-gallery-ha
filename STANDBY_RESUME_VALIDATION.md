# D-250 standby recovery — local/offline validation

Local candidate, 2026-10-23. Not installed, versioned, committed, published or
hardware-tested by this task. No Home Assistant/TV connection, credential,
power/mode/image command or installed card/script change was made.

## Behaviour and safety boundary

- NEW `standby_resume` is optional/default false. Old saved flags do not
  activate it. Background mode and one existing Samsung media_player/remote
  entity are required; no extra helper, integration or special rights.
- Observe valid off continuously for at least30s, then a genuinely newer on
  timestamp, <=30s old, stable for10s. Poll only cached HA state every5s.
  Invalid/future/reordered timestamps, >15s gaps or clock discontinuity discard
  evidence. Boot-on never grants a read; a stopped app cannot observe a cycle.
- Spend an edge before reserving its durable budget. A separate one-use <=5s
  claim is required by production preparation, not merely a monitor event.
  Strict local target/device/association/token checks precede the existing
  isolated Art Mode/ID/thumbnail proof; no sender, enrollment or repinning.
- Private atomic budget: max6 reservations/rolling hour, minimum60s apart,
  across restarts; <=2048 bytes, no backup fallback or corruption repair.
  Newer/corrupt/nonregular/unwritable state denies a reservation. An absent file
  initializes an empty budget; deleting/restoring private app data can reset its
  history, unlike an ordinary restart. No claim covers manual data rollback.
  TV auth refusal persists; only successful explicit delivery clears that latch,
  not rate history. A failed optional latch-clear blocks later automatic reads.
- No automatic initial-on or minute TV reads. A failed or lost session is not
  retried while HA remains on; another fully observed valid cycle is required.
  A fresh explicit send retains its original arbitration/receiver path.
- Only fresh actual-device image proof supplies known metadata and cached
  preview. Unknown pictures stay unidentified; static proofs still expire at
  90s, complete changed-ID slideshow evidence at900s. Passive waiting is now
  clearly distinguished from an active read. No guessed artist/current image.

These are software bounds, NOT a physical no-wake/no-mode-switch guarantee.
Cached HA on is not physical Art Mode proof. The unresolved earlier firmware/
connection-side-effect incident is not claimed fixed. A later native build,
release, opt-in live setup and controlled hardware test need separate authority.

## Observed checks

Final command: `bash frame_gallery/scripts/check.sh`.

- **6,354 passed /16 unchanged Linux/root platform skips, 56.23s.**
- Ruff/format and strict host/Linux typing: **323 files**, no issues.
- Whole line/branch coverage: **100%**,12,228 statements /2,992 branches.
- Required-package coverage: **100%**,9,206 statements /2,170 branches.
- No gate threshold, dependency, privilege, platform skip or existing default
  safety expectation was relaxed. Early failures and their corrections remain
  in the ignored local evidence, not hidden as successful runs.

Actual production entry is exercised with synthetic Core/store/isolated-session
transports:34 new-consent variants plus the28 retained old-option cases, sender
arbitration and default-deny barrier. Cover known/unknown/wrong TV/mismatched
image, TV/menu mode, missing archive/pin, token faults, HA/auth failure,
publication/cancellation, missing entity and corrupt/rate-limited budget.
Assert zero send/upload/select calls and state_refresh=false. Auth denial is
checked in the persisted budget, not just in a fake controller flag.

Pure monitor/store tests cover short off/on flaps, settling, old/future/reordered
samples, repeated on, hidden timestamp changes, cadence/gaps, wall/monotonic
faults, consumed/expired claims, explicit send supersession, restarts, byte/
entry/time bounds, primary corruption/newer version, symlink/FIFO/directory,
write/readback failure and auth-latch clearing without clearing rate limits.

## Recorded replay and independent negative controls

Replay of the already captured20-hour Samsung-state timeline:19 recorded rows,
14,401 virtual five-second polls,9 eligible one-use reservations, **zero grants
while HA off** and **zero duplicate grants after a simulated restart**. This
replay creates local fake budget state only; no TV session or authentication.
It tests eligibility, not TV behaviour or physical Art Mode.

Three source-unmodified, in-memory negative controls failed the intended tests:
remove observed-off duration, remove settling duration, or remove six/hour cap.
The failures establish that the tests detect those missing guards, not firmware
compatibility. No recorded private household data is added to tracked source.

## Card/configuration compatibility

All **21 original complete code/YAML fences** and the full background-send
script remain byte-identical to the published baseline. Ten critical files
(including AppArmor, workflows, dependency lock/requirements and version) are
unchanged. The only metadata/schema addition is optional standby_resume; no
saved defaults or existing IDs are rewritten.

Five new complete native CURRENT_STATUS guides distinguish service stopped,
standby, waiting/settling, safety hold, missing setup/association, passive
waiting/expired proof, rate/storage/auth limits and failed reading sessions.
They share one90/900s metadata/image gate and omit an unavailable optional
camera. Old sensors get honest generic fallbacks rather than an invented
network diagnosis. Unknown reason strings are never displayed as remote text.
Structural/JSON-literal and publisher tests passed; no live HA rendering is
claimed. No additional template engine was installed for offline QA.

The existing configuration locales (English/German/French/Spanish/Italian)
clearly describe separate consent and limits. Existing installed cards remain
unchanged; using the new explanatory messages later requires the optional full
card configuration, not a destructive dashboard recreation.
