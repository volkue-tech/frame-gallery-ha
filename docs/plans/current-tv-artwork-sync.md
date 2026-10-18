# Automatic current artwork synchronization proposal

## D-235 coherent b9 feature / authorized release round, 2026-10-18

Every selected one-shot/background delivery now retains per-device/ID metadata
and a compact exact-JPEG reference in bounded atomic private state. Identity is
captured from the already performed support read, not another TV request. Old
image-verified mappings remain compatible. Event ID lookup may reuse confirmed
uploads with explicit provenance, not a fabricated fresh thumbnail proof.

The user authorizes beta build/publication after green checks. An opted-in
service consumes one fresh exact persisted-delivery grant for the observed
strict slideshow contract, without requiring personal hashes/profiles. Reviewed
no-wake registry stays empty. Default OFF/no boot/refresh grant/no polling or
reconnect and all isolation/freshness guards remain. Old hardware snapshots and
open known-automatic caption gate are not relabelled; no new TV test in this
round. Host gates pass 5751/16 skips/100%; native checks follow before release.

## D-234 regular service, 2026-10-18 — local integration checks complete

The actual regular-entry path now has offline multiple-cycle known/unknown
caption coverage with injected I/O, a same-byte hashed-target receipt check and
publication-failure stop/latch. Exact observed go_to_standby closes and pauses
normally, with no extra getter or reconnect. Default one-shot and existing cards
remain unchanged. The source is not installed or published by these checks.
The production hardware-policy table remains empty; no personal TV ID is shipped.
Prior private hardware evidence is preserved, not a claim about exact new code.
Native ARM/Intel validation is deferred by the user to the later release round,
before publication. A controlled genuine known-work automatic transition/profile
acceptance remains separate from the passing synthetic/replayed integration.

## D-233 slideshow events — local/offline implementation

The captured automatic sequence supplies its own new ID. The local candidate
therefore uses ordered image_selected/is_shown Yes, same-ID
auto_rotation_image_changed/type shuffleslideshow, then mode-on within five
seconds, without the D-232 extra getter. A host-only lookup reuses existing
image-verified per-TV associations; unknown IDs remain unidentified. Explicit
slideshow evidence is not a new byte proof or protection against undetected ID
reuse. Navigation clears metadata rather than being interpreted as mode-on.

An established receive-only session survives baseline age-out. Baseline is 90s;
a complete changed-ID triple gets 900s from receipt for the observed ten-minute
cycle. Duplicate ID/on/pong cannot renew; expiry clears display, not the listener.
Mode-off/errors still disarm with no reconnect. Full timing/schema/unknown-ID
and pinned-library request-count tests are offline; live profiles stay empty.
Actual cards are untouched; optional five-language examples support the new
lease and old fallback. No further live test/build/release is authorized.

## D-232 one-shot same-socket ID probe — local/offline only

The user now authorizes implementing and offline-testing one get_current_artwork
request following an exact mode-on event on the existing session, not another
device test/app update or publication. Public b8 and Event Lab remain stopped,
the latter disarmed; existing cards retained. D-231's deployed private discovery
snapshot is not changed by this local source amendment.

An optional exact internal policy selects value/status and permits one probe
per entire session; the live policy registry remains empty. Emit invalidation,
clear metadata as the parent processes it, then bounded checking. Send directly
on the same bounded socket with one random correlation nonce, no library getter
or auto-open; require an exact correlated current-ID reply within five seconds.
Unknown/mutating/off events, errors, loss and cancellation end without retry.
Duplicate on cannot resend or extend the deadline; expired initial proof cannot
trigger a request. A successful ID is diagnostic
only and ends/pauses the session, even when it is a previously known/same ID.
No new thumbnail, caption/binding lookup or proof-age renewal is authorized.

The two prior private captures demonstrated an event/status field shape and a
working notification channel, not actual status-value semantics/content-ID
reply compatibility, event completeness or sleep safety. Both on/off values and
the strict reply schema remain offline fixtures until separately tested. The
worker does not stay connected through mode-off merely to await a future on.
This is a narrow exception to the older receive-only text below, not polling.

Local implementation and manual review are complete. The unchanged full offline
gates pass with 5562 tests, 16 platform skips, host/Linux typing over 283 files
and 100% line/branch coverage. The frozen private Event Lab remains unchanged;
no live query, app update, image build or publication was performed for D-232.
Separate device validation is still required before any production profile.

## Safer-session redesign, 2026-10-17 — local implementation (D-231)

The user initially requested planning, then explicitly authorized local
implementation and offline tests of the safer design. The background option
remains saved off and the installed app stopped. No device access, reactivation,
builds or publication are included. Public b8 is already released. Earlier release/activation
statements below are historical; current authority is in STATUS.md/TASKS.md.

### Evidence and limits

The successful delivery was followed by a confirmed Art-Mode observation.
At 00:23:42 Europe/Berlin the owned HA state changed to `tv_in_use`; the user
independently reported unexpected television playback. No intervening full
standby is established. Attribute this as a suspected side effect, not a proven
firmware defect or a proven wake from sleep.

Code and a network-blocked trace of the real pinned samsungtvws 3.0.6 show
that the present observer creates a fresh client per cycle: device-info GET,
Art websocket open, mode/ID/thumbnail/ID/mode reads, then immediate socket
shutdown. The next cycle starts 30 seconds after the previous read completes.
No power, input, channel, application-launch or Art-Mode setter was found in
that call chain. `tv_in_use` returns at the first mode getter, before that
cycle's ID/thumbnail reads; any value other than exactly `on` currently produces
that coarse status. Request-level incident traces and raw mode replies were
not recorded, so the triggering step and external-control alternatives remain
unresolved. Local diagnostic evidence stays under ignored build/, not in a
public user-specific mapping or packet dump.

### Recommended scope

Keep the optional mode, existing sensor ID, cards and explicit send command.
Replace repeated short-lived read jobs with **one read-only Art session for
one explicitly authorized awake period**. Prefer unsolicited notifications on
that connection; do not assume the firmware actually supplies a complete feed.
Do not add another app, integration, helper, API key, port/polling settings or
configuration.yaml requirement.

1. **No automatic connection on boot, restart, HA `on`, reachability or a
   timer.** Initially allow at most one observer connection after a successful,
   explicitly requested artwork delivery. Use that fresh delivery's identity
   and image-proof context, enforcing the existing device pin and credential
   rules. Reusing the uploader's socket would require a larger lifecycle
   redesign; it is not promised in this first revision.
2. **Listen rather than reconnect.** Keep that observer websocket open and
   dispatch only recognized, validated Art-Mode/content notifications. No
   periodic HTTP device GET, new websocket, thumbnail/D2D connection or own
   keepalive ping. A server ping/automatic pong is still network traffic and
   must be included in later sleep testing, not described as zero traffic.
3. **No silent polling fallback.** The library handles Art-channel frames but
   does not establish that this TV emits every unsolicited image/mode change.
   Event names, fields, ordering and coverage remain an explicit validation
   gate. If events are insufficient, show unconfirmed/stale information; do
   not quietly restore 30-second polling. Sparse mode/ID queries on the same
   socket are a separate possible fallback requiring a reviewed safety test,
   not part of the initial event-only candidate.
4. **Loss or uncertainty ends the session.** Non-Art Mode, unavailable/malformed
   mode, authorization failure, socket loss, protocol limits or session expiry
   clear current attribution and disarm observation. Do not reconnect, pair,
   wake, select Art Mode or resume merely because HA later says `on`.
   Until a separately validated safe-resume signal exists, another successful
   explicit send is required. This intentionally trades automatic recovery
   after sleep for safety; it is not a seamless 24-hour tracking promise.
5. **An explicit new artwork request remains explicit.** Mark information
   checking, stop the read-only session, run the unchanged bounded delivery,
   then establish at most one new observer session. Preserve serialization,
   replay protection, history/upload/quarantine/preview behavior and existing
   script/card IDs. No unrequested artwork is sent to re-arm observation.

### Trustworthy attribution and freshness

Preserve the distinction between latest delivery and actually current work.
Establish image association once in the explicit delivery/verification path,
not by fetching a thumbnail every background cycle. Do not weaken the current
device/content-ID/thumbnail binding into a content-ID-only lookup: `MY_F...`
reuse, deletion/replacement, another uploader, session gaps and unknown IDs
must invalidate confidence. A known ID is not by itself new image proof.
Before implementation, specify the permitted session/proof epoch and amend
D-226's per-read proof contract explicitly. If reliable continuity cannot be
established without another TV transfer, report unidentified/unconfirmed rather
than guess or introduce an automatic D2D verification path.

A publisher heartbeat or an open TCP socket must not make old metadata fresh.
Keep the actual TV confirmation time separate from the HA publication time.
Only a proven complete event stream can maintain a current snapshot between
changes; without that evidence, retain the conservative 90-second freshness
limit and clear the current title after it expires. Artist information may
therefore disappear on the first conservative candidate even while the same
artwork remains visible. Do not stretch the timeout merely to hide that gap.
Any maintained-event-stream freshness policy needs explicit acceptance before
it replaces b8's observation-based meaning of `artwork`.

The existing current card derives freshness from `last_reported`. Either keep
that card safe by ceasing `artwork` heartbeats/clearing state before expiry, or
provide a compatible complete native card using the actual confirmation time.
Do not change entity IDs or silently make an old card show cached data as
current. Standard preview, last-delivery caption, selectors and timer are
untouched. Five-language wording must distinguish current, last confirmed,
unidentified, stale and paused without requiring another dashboard extension.

### Worker and protocol design

The current ProcessExecutor kills a one-shot read after five seconds. A
long-lived connection cannot simply be hidden inside that call or placed in
the credential-bearing parent. Propose a dedicated unprivileged read-session
worker with the same TV-only address guard, memory/descriptor/seccomp/AppArmor
and no-child-process protections. No Supervisor token in that worker.

Use a single receive/dispatch loop: the library's threaded `start_listening`
and synchronous getters must not compete to consume the same socket. Preserve
request-ID correlation, frame ordering and bounded handling of unsolicited
messages. Do not call the package's broad remote-control interface.

Provisional internal bounds, to test before accepting the implementation:
one worker/socket, one pending request, at most 64 queued events, 64 KiB text
frames rejected before unbounded allocation, no unsolicited artwork binaries,
five-second startup/request deadlines, existing 512 MiB worker-memory and
cumulative CPU limit, and an eight-hour maximum session. Expiry/limit failure
pauses without opening a replacement session. Stop must be cancellable within
two seconds, otherwise terminate the worker. Keep the one-shot delivery's
existing watchdog and budgets unchanged. No unbounded daemon exception.

Prefer a bounded graceful websocket close over immediate shutdown; on deadline
use the hard-close fallback. Neither close style is already proven harmless.
Repeated open/close, persistent connection, server ping/pong and teardown must
all be included in later device validation. A maintained connection could
prevent automatic no-motion sleep even without application requests.

### Three bounded work packages and gates

1. **Offline implementation, only after separate approval.** Define the
   session/freshness/proof contracts and corresponding specification amendments;
   implement the isolated session worker and dispatcher. Use authored fixtures
   and the exact installed library with real-network attempts blocked. Cover
   mode/ID changes, missing/out-of-order/duplicate events, ID reuse, stale data,
   partial frames, limits, stop, server ping, socket loss and boot/refresh
   zero-connect behavior. Preserve the full existing regression/security gates.
   Synthetic fixtures do not prove real TV event support.
2. **Controlled device validation, only after separate approval.** Establish
   actual unsolicited-event coverage and narrow suspected GET/open/getter/
   thumbnail/close side effects one at a time; do not combine steps and call
   that isolation. For the selected candidate observe repeated natural
   no-motion sleep/wake cycles, not just manual power-off. It must neither wake
   the screen, switch Art/TV/input nor delay sleep versus background-off
   controls. Include remote artwork changes/slideshows, normal TV playback,
   network loss, HA/app restart, idle transport traffic and session expiry.
   Failure keeps the feature off; a single quiet manual-off GET is not a pass.
3. **Beta handoff, only after validated safety and publication approval.**
   Native ARM/Intel isolation/resource tests, compatible five-language guides
   and complete native cards, matching source/image/signature gates and a
   reversible opt-in migration. The background default remains off. If events
   or sleep safety fail, do not release a supposedly safe automatic mode;
   retain one-shot delivery and honest unconfirmed/last-delivery information.

### Local implementation contract

Implementation/offline testing was subsequently authorized. EventController,
EventBackend and the dedicated isolated SessionProcess replace the periodic
controller in real service wiring. The reviewed-policy table is empty: no
actual device is enabled, and schemas in fixtures are expressly synthetic.
One initial identity/mode/ID/thumbnail proof may be obtained on that session;
afterward it only listens. This candidate supports only that freshly verified
baseline's attribution. A changed or invalidated ID ends its proof epoch, and
same-ID/mode-on events cannot freshen it. The conservative 90-second age limit
clears/pauses rather than pretending continuous firmware-event completeness.

No installed configuration/card or public version is changed. Device event
discovery, natural-sleep/mode validation, any continuous-freshness policy,
native image builds and publication remain separate gates. The exact local
implementation is not evidence that this television sends the synthetic events.

## Original b8 architecture below — historical baseline

**D-230 supersedes the absolute activation gate in this original proposal:**
the user accepted experimental default-off use with a wake warning and deferred
the natural-sleep test. Local b8 building is approved, publication is not.
Start/boot/restart stays passive; only a successful explicit delivery plus a
changed valid current record arms reads and first-device enrollment. Persistent
pins do not persist permission to resume. Failed/non-Art reads disarm without
retry, and read-only refresh cannot re-arm. Tokenless authorization is granted
only for the fresh successful-delivery session. Keep all original read bounds,
isolation, image proof and no-power/setter constraints. No-wake remains unverified.

Planning assessment, 2026-10-16; local implementation subsequently approved.
Use an **optional background mode in the
existing Frame Gallery app**, with separate commands for sending artwork and
refreshing current information. Publish current metadata through the documented
Home Assistant Core state API, without requiring another integration, broker,
automation or Text helper. D-225 is accepted for local code; D-226 blocks every
production automatic TV read pending separately authorized no-wake validation.
The [product scope](current-tv-artwork-update.md) remains the parent plan.

## Why a separate command is necessary

The current app executes one bounded delivery and exits. Its dashboard script
calls `hassio.app_start`. Supervisor's start operation does not execute an app's
entry point again when its container is already running. Merely leaving a
polling loop alive would therefore stop later card taps from requesting images.
This is confirmed by the official [Supervisor start implementation](https://raw.githubusercontent.com/home-assistant/supervisor/main/supervisor/apps/app.py).

Home Assistant provides a separate [app stdin action](https://www.home-assistant.io/actions/hassio.app_stdin/)
for commands to a running app. This is available on HA OS, admin-only, and
requires app support. It is an appropriate transport for a small fixed command
set, not a shell or an arbitrary-code interface.

## Alternatives

| Approach | User setup and compatibility | Assessment |
| --- | --- | --- |
| Optional background mode in the existing app | One opt-in, boot setting and one script update for existing users; existing cards can keep their script reference | Recommended for this beta |
| HA automation starting periodic read-only jobs | Extra automation and command/configuration wiring; starting the current app would upload instead | More setup and lifecycle races |
| Separate observer app in the same repository | Another installation and configuration; private uploader state cannot simply be shared | Preserves one-shot lifecycle but adds user and credential work |
| Companion HA integration | Real registered entities and native actions, but a separate installation/distribution and maintenance path | Strong long-term option, not minimal setup now |
| MQTT discovery | Registered entities through standard discovery, but MQTT must exist and be configured | Optional future transport, not a universal prerequisite |

The official [MQTT guide](https://www.home-assistant.io/integrations/mqtt/)
requires a broker and an integration setup. Supervisor service discovery can
supply a configured broker's details; it does not mean every Green already has
MQTT. Do not install a broker or integration silently.

The existing Samsung integration may provide optional availability hints. Its
[documented functions](https://www.home-assistant.io/integrations/samsungtv/)
do not establish a supported current-artwork/title feed for this feature.
Neither that integration nor access to its private configuration is required.

## Proposed app lifecycle

Keep legacy one-shot operation as the backward-compatible default. Missing
mode options must not silently enable background execution on an upgrade.
Offer one clearly explained optional background setting, not separate user
controls for polling intervals, transport, ports and heartbeat internals.

In background mode, starting, restarting or booting the app starts observation
only. It never sends a new picture as a side effect. The normal Start/Stop
controls now govern the background service; **New artwork** is a separate
explicit command. An approved metadata amendment must unlock the ordinary HA
**Start on boot** switch, which is currently prohibited by `boot: manual_only`.
Do not turn that switch on automatically or change unrelated Supervisor options.

The service supervises short-lived jobs rather than turning the entire image
runner into a perpetual process:

- A read job uses the app's own authorized TV credentials, checks Art Mode and
  current content ID, resolves a verified mapping, and closes its connections.
- An explicit send command launches one delivery with the existing deadlines,
  isolation, history, upload ledger and cleanup guarantees. Its watchdog must
  end that job, not accidentally terminate or abandon the supervising service.
- A distinct refresh command requests a read job only. It cannot reach the
  upload, selection, power, deletion or pairing commands.

Serialize TV access; pause reads during delivery and read again afterward.
Accept no overlapping deliveries or unbounded queues. Use bounded command
validation, a start/readiness handshake and request deduplication; stdin
delivery alone is not proof that a command was accepted or an image displayed.
Stopping the app must stop all jobs and release all locks/sockets.

Keep the existing loading timer as the delivery indicator. App Running now
means the service is alive, not that a picture is being sent or the TV is on.

## Minimal user setup

For existing users who want current information:

1. Enable the optional background mode and, for operation after HA reboots,
   enable the standard HA Start on boot switch.
2. Replace the body of the existing new-artwork script once with a documented
   service-aware variant. Keep its entity ID, existing camera, timer and
   selectors; cards calling that script need no image-action changes.
3. Add the optional current-information card. No new metadata helper or
   periodic automation is needed.

The revised script must ensure the service is ready and send an explicit
new-artwork command, rather than rely on app start as the request. Supply a
complete script and card in all five languages at implementation time. Preserve
the existing one-shot instructions for users leaving background mode off.

Thus zero additional installations are achievable, but a transparent,
zero-change upgrade of a start-triggered script to a resident service is not.
The earlier blanket no-migration promise applies to background-disabled users;
opting in requires the one-time script change. Automations directly calling
app_start also need to use the revised script. Never edit them automatically.

## Metadata in Home Assistant without new helpers

Apps can use the [Supervisor Core proxy](https://raw.githubusercontent.com/home-assistant/developers.home-assistant/master/docs/apps/communication.md)
with their supplied token, so users need not create or paste an HA API token.
The [Core REST API](https://developers.home-assistant.io/docs/api/rest/#post-apistatesentity_id)
can publish a state and attributes even without an entity platform behind it.

Propose one fixed, app-owned sensor-style state, with a short status plus
bounded attributes for TV ID, verified source work, title, creator and source.
Keep this separate from the last-delivery caption and preview. Do not expose a
secret or a user-supplied arbitrary state destination. Check ownership and
collisions before writing; never overwrite an existing unrelated entity.

This is **not** a registered sensor platform or device integration. The
[Core implementation](https://raw.githubusercontent.com/home-assistant/core/2026.10.1/homeassistant/components/api/__init__.py)
sets the state machine; it does not create an entity-registry entry, native
service or unique-ID-managed settings. The optional native card must handle a
missing state after Core restart and a stale state after app failure. Republish
only newly observed TV information as current, not cached captions made fresh.
Normal entity-registry rename/device-management features are not promised.

Avoid a changing timestamp attribute on every poll and never set force_update
merely to prove life. Evaluate unchanged-state reports and HA's
[last_reported timestamp](https://www.home-assistant.io/docs/configuration/state_object/)
for freshness with a time-aware native card. HA distinguishes unchanged reports
from changes to state/attributes, as explained in the official
[state reporting note](https://developers.home-assistant.io/blog/2024/03/20/state_reported_timestamp/).
Verify frontend freshness and actual Recorder growth before accepting this
path; do not claim it produces no history merely from the documentation.

## Reading cadence and TV safety

Use periodic bounded queries as the baseline. A provisional engineering target
is one read every 30 seconds while responsive and a freshness window of about
90 seconds. The local candidate gives its isolated TV request five seconds,
plus up to five seconds of isolated thumbnail comparison only for a missing
association (D-226); this supersedes the original provisional whole-read
five-second target for that initial case. These values require
hardware validation, and time-aware native cards can add display delay.
Do not promise instantaneous slideshow tracking. Event notifications can be
evaluated later but are not required from undocumented firmware behaviour.

On ordinary TV operation or repeated network failures, reduce work with a
capped backoff rather than aggressive reconnects. Never send wake-on-LAN, power
or Art Mode changes. An availability hint is not proof that Art Mode is visible.
If connections themselves wake a model or cause authorization prompts, stop
automatic attempts in that condition; safe resumption needs a validated positive
availability signal or explicit user action. No-wake behaviour is a release
gate, not something proved by the word "read-only".

No stored app token means observation is not yet authorized; do not pair from
the observer or import a different integration's token. First pairing remains
an explicit normal send/setup action. Rejecting a token disables blind retries.
Use the existing secret-isolation principles for workers and keep HA API
credentials exclusively in trusted processes.

## Required exceptions and remaining gates

The user approved local amendments to the one-shot/background restriction and
token-purpose restriction in ARCHITECTURE_CONSTRAINTS.md, lifecycle/packaging
in PRODUCT_SPEC.md and ARCHITECTURE.md, and corresponding acceptance criteria.
The new permission is narrow publishing of app-owned HA metadata; it is not
permission for arbitrary state writes, helper creation, private config access,
Supervisor management, host networking or dashboard edits.

The local implementation records concrete command/storage/timeout bounds in
D-226 and the [five-language candidate guide](../../frame_gallery/CURRENT_ARTWORK.md).
These native/device validation items remain open:

- Stable per-TV identity, verified upload correlation (including R-30), ID reuse,
  mapping schema, recovery, limits and backup behaviour.
- Exact background/legacy detection, boot semantics, stdin readiness and
  deduplication, command failure reporting and process-group cancellation.
- State ownership, restart recovery, freshness rendering without misleading
  titles, and measured memory, CPU, request and Recorder impact.
- Model-specific Art Mode/availability checks and a confirmed no-wake path.

No live HA/TV request or credential access was needed for this assessment.
The implementation is local only. Hardware tests, production no-wake policy
activation, new beta builds and publication still need their separate gates.
