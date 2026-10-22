# Current artwork and optional background mode

> **b17 safety candidate (D-247) — not published:** automatic startup/wake
> connections and `current_state_refresh` minute reads are suspended, including
> saved opt-ins. `resume_state_entity` is now a stop signal only, never a start
> grant. After a fresh explicit successful send, the existing passive receiver
> can follow complete slideshow events. Unchanged images expire; sleep or a
> lost session does not recover automatically. These restrictions override the
> older b11–b16 recovery instructions below. Cards, script IDs and saved artwork
> associations are unchanged. Connection side effects are not certified absent.

Local, unreleased: [optional current-image preview](CURRENT_PREVIEW.md). Existing cards stay unchanged.

English | [Deutsch](CURRENT_ARTWORK.de.md) | [Français](CURRENT_ARTWORK.fr.md) | [Español](CURRENT_ARTWORK.es.md) | [Italiano](CURRENT_ARTWORK.it.md)

**Historical b16 parser correction — refresh is suspended in b17:** the optional current-state refresh accepts the Frame's real
`artmode_status` / `current_artwork` replies with strict fresh request-ID checks.
No new option, connection, stored-ID format or card change is needed.

**b17 candidate: experimental and off by default; publication gates pending.** Existing b7/b8/b9/b10/b11/b12/b13/b16 cards remain usable. No API key, new helper, HACS extension, special permissions or second app is needed on Home Assistant Green/OS.

[Historical b16 validation](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA16_VALIDATION.md) · [Historical matching sources](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b16).

A read-only connection can still wake a television. Controlled tests covered automatic slideshow changes and one natural-sleep episode on one Frame, not every model or firmware. Leave background mode off if any wake-up risk is unacceptable.

## Automatic artwork memory

### Optional initial synchronization and resume — b12

<details>
<summary>Historical b12–b16 behaviour — suspended in b17; not current setup instructions</summary>

After a previous successful Frame Gallery send, enable **Background mode** and
enter this TV's existing Samsung HA `media_player` or `remote` entity ID in
**Initial sync / resume after sleep** (`resume_state_entity`). Find it under Settings → Devices
& services → Entities. No new helper or image send is needed for a wake. Keep
your existing cards and script. Restart the app after changing its options.

The first cached HA sample at each configured app start permits **one initial
read if it says `on`**, even if unchanged for hours. The TV's identity, Art Mode,
current ID and image are verified before any artist/title is restored. There is
no image send. A missing, invalid, future, `off`, unknown or failed first sample
consumes the startup opportunity; later `on` samples cannot retry it.

**Startup handoff — b13:** a fixed ten-second window gives an accepted
new-artwork command priority over the automatic initial read. Acceptance cancels
the leftover startup opportunity before sending, even if the send later fails or
finds no match (`no_match`); only a valid successful delivery may then start its
own read session. Without an accepted send, standalone initial synchronization
remains available after the window if the cached HA state stays valid and `on`.
The later genuine `off`/`on` recovery rules below remain unchanged.

This bounded window cannot anticipate arbitrarily delayed scripts. Once a
standalone receiver has started, a later send must first stop it and wait for its
exit. Offline tests of this fix provide no new hardware proof against waking the
TV or changing its mode.

The resume monitor reads this cached HA state every five seconds; this is
separate from the optional Art-socket checks below. A later observed
`off` followed by a newer `on` within 30 seconds permits one further read. Both
paths share at most six attempts per rolling hour **in that service process**.
Duplicates, stale wake edges or monitoring gaps do not retry. Authentication
refusal blocks automatic reads for that process. Restarting is a new initial
opportunity, not a persistent cross-restart rate limit; do not use restart loops.

HA `on` is not Art Mode proof. A connection may still wake the TV or affect its
mode; this new path has offline simulations, not new hardware safety evidence.
Leave the field empty to disable it. A stopped app cannot observe a wake. The
90-second initial and 15-minute slideshow display limits below are unchanged.

</details>

Every successfully selected upload now saves its TV image ID, title, artist and source automatically, even with background mode **off**. Nothing needs to be entered manually. The association belongs to the actual TV identity, not just its IP address: the same image ID on another TV is not the same artwork. A successful new upload replaces an older association for that TV/ID.

The private app data survives normal updates. Clearing the selection history does not erase associations; uninstalling with app-data deletion does. Keep an app backup before reinstalling. Storage is bounded to the latest 2,048 upload associations and 32 MiB, plus one backup. Each reference is a tiny 64×36 RGB sample, not a full-resolution artwork archive. Older image-verified associations remain compatible.

Old TV pictures, uploads from other apps and deliveries without a stable TV identity remain unidentified. Frame Gallery does not guess artists or use cloud image recognition.

### Optional current-state refresh — b16

<details>
<summary>Historical minute-read behaviour — suspended in b17, even when saved as enabled</summary>

`current_state_refresh` is a separate optional switch, **OFF by default**, and
requires `background_mode`. It allows at most one read-only coherence check of
the current Art Mode and image ID per 60 seconds, over the **already established
Art socket**. It is intended to restore known artist/title information after
using the TV menu or resuming a slideshow, including when the image stays the
same. It opens no new connection and sends no image, power or mode command.
An unknown image remains unidentified; the app never invents a title or borrows
the previous one.

A fresh successful `current_state_read` proof is valid for 90 seconds.
Duplicate IDs, pongs or mode-on notifications alone do not renew it.

With this option enabled, Art-channel `off` or `nav` retains the **same socket**;
these states are not physical standby. Captions are cleared while Art Mode is
not on. Scheduled checks continue even if the return-to-Art notification is
missed: within the same once-per-minute limit, only the mode is read while not
on. Image IDs are read only after a fresh `on` result, so menu-only cycles cannot
publish artwork. If the session initially sees `off` or `nav`, the original
one-time thumbnail proof waits for Art Mode `on` on that socket; it is not
repeated. Standby, an observed HA-off state or a closed connection still stops
the session, without opening a new socket or blindly reconnecting.

Read requests may affect automatic sleep even on the same socket. Leave this
option off if that risk is unacceptable. Offline tests do not certify firmware
compatibility or no-wake behaviour. Existing cards and scripts need no changes.

</details>

## Enable the optional current-artwork card

1. Keep your camera, timer, existing cards and `script.frame_gallery_new_artwork` entity ID.
2. Enable **Background mode**, then restart the app. Start/Stop controls the service, not an image change. Startup and HA `on` do not contact the TV in b17, even with saved resume/refresh options. The optional Samsung entity can only stop observation.
3. Replace only the script body with the [complete background send script](examples/background-send-script.yaml). Adjust the app slug and existing timer ID if needed. Cards calling this script keep working; direct `hassio.app_start` automations must call the script instead.
4. With Art Mode visibly on, explicitly request one new artwork through the script. Only a fresh successful send grants one experimental passive event session. Starting the service or selecting Refresh does not read an already displayed picture. After menu/TV mode, sleep or connection loss, there is no automatic recovery; another explicit successful send is required.
5. Add a Manual dashboard card using the **complete** YAML below.

The existing picture/colour/artist card shows the **last sent preview**, not a live TV screenshot. This additional native card shows current information separately.

The unchanged card below retains an older `validation_required` help message about initial reads. In b17 that path is suspended: the message means a fresh explicit successful send is required, not that configuring an entity will start a read.

```yaml
type: markdown
title: Frame Gallery — Current artwork
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% if item is not defined or item is none %}
  No current information is available.
  {% elif item.state == 'artwork' and
      as_timestamp(now()) - as_timestamp(item.last_reported, 0) <
      (900 if item.attributes.get('confirmation_method') == 'slideshow_events' else 90) %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Last confirmed: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'validation_required' %}
  Waiting for an authorised check. Check background/entity settings and the app log; a configured initial read does not need a new image.
  {% elif item.state == 'checking' %}
  Current display is not confirmed yet. Waiting for a valid image or slideshow proof.
  {% elif item.state == 'unidentified' %}
  The displayed artwork has no saved association.
  {% else %}
  Current artwork is not confirmed. The TV may be unavailable or the session paused.
  {% endif %}
```

## How confirmation works — and its limits

In b17, a fresh explicit successful send can start one passive Art session. Its
initial thumbnail comparison confirms a known work for 90 seconds; a new complete
slideshow sequence (`image_selected`, matching `auto_rotation_image_changed`,
then Art Mode `on` within five seconds) confirms it for at most 15 minutes.
Duplicate IDs, pongs and mode-on alone do not renew evidence. A fixed picture
therefore becomes unconfirmed; unknown IDs never borrow another work's caption.

There are no minute GETs or automatic initial/wake connections, even if their
saved options are enabled. Menu/TV mode, standby, connection loss and errors can
end the session; no reconnect follows. The cached Samsung entity is stop-only.
Manual Refresh drains existing events, not a new TV query. Sessions last at most
eight hours. A connection itself can still affect the TV; this is not a no-wake
guarantee. Existing cards, scripts and stored associations remain compatible.

<details>
<summary>Historical b10–b16 confirmation/recovery details — suspended paths are not b17 instructions</summary>

**Historical b10 recovery — event-only mode (`current_state_refresh` off):** incomplete sequences of recognized
slideshow notifications clear the current caption and wait on the same
connection for a new complete sequence. They never confirm an artwork or
trigger another query. Unknown or malformed messages, standby, TV mode and
connection loss still end the session. Fixed failure codes in the app log
distinguish startup, receive, decoding and worker errors without raw messages
or credentials. The b12 startup path and b13 handoff have no new live-TV or sleep validation.

With `current_state_refresh` on, structurally valid but unrecognized
notifications and Art-channel `off`/`nav` clear the caption while retaining the
same socket under the bounded rules above. They do not confirm artwork or grant
a new connection. Physical standby, authentication refusal, malformed protocol
data and a closed transport still stop the session.

In the log, `event sequence incomplete` means the caption was cleared and the
same connection is waiting, not that an artwork was confirmed.
`event session stopped: reason=...; no reconnect` means the session ended;
include that fixed reason code, app version and TV model in a bug report, not
access tokens or raw TV data. That failed session is not automatically retried.

Each session lasts at most eight hours. In event-only mode
(`current_state_refresh` off), sleep, TV mode or failure can end it earlier.
The opt-in exceptions and terminal stops above still apply. A configured new process start or later fresh HA wake edge above can permit a new read; an explicit successful send can also start a session.

After one initial read and local image comparison, one connection listens for the observed slideshow sequence: `image_selected`, matching `auto_rotation_image_changed`, then Art Mode `on`, within five seconds. With `current_state_refresh` off, there are no repeated TV queries, subsequent thumbnails or reconnects within that session. Enabling it permits only the bounded checks above, not new thumbnails or connections. A later event resolves metadata from that TV's saved upload or image-verified association; an unknown ID clears the caption.

Initial image proof lasts 90 seconds. A complete slideshow sequence lasts at most **15 minutes**, intended for the tested ten-minute slideshow. Duplicate IDs, pongs and mode-on events do not renew it. Slower slideshows can therefore show gaps; manual selections need not provide this sequence. The template can add about one minute of display delay.

With current-state refresh off, or without a successful fresh check, a fixed,
unchanged picture can become unconfirmed after 90 seconds.
The initial-start fix alone does not extend proof age or repeatedly query the TV to
keep a static caption alive.

**Event-only (`current_state_refresh` off):** Sleep, TV mode, disconnection, malformed events or publication failure stop/pause the session without an immediate reconnect. When opted in, the bounded same-socket rules and terminal stops above apply instead. After a session has actually ended, without the optional wake-edge setting a new explicit send in visible Art Mode is still required. Manual Refresh only reads already received events. The observer sends no power, Wake-on-LAN, image-selection or mode-change commands. A connection itself can nevertheless cause side effects.

Saved IDs are historical correspondence, not continuous pixel verification. An external, unobserved replacement/reuse of a TV ID cannot be ruled out during event-only listening. A mismatching initial image comparison suppresses the saved caption. No general firmware/no-wake guarantee is claimed (D-235).

The sensor is an app-published HA state, not a registered device integration; it may temporarily disappear after a Core restart. Stale or paused data hides the title. To return to one-shot operation, disable background mode, restart and restore the one-shot send script. Do not delete history or device pins to force a connection.

</details>
