# Automatic current artwork synchronization proposal

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
