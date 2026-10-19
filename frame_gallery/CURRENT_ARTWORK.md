# Current artwork and optional background mode

English | [Deutsch](CURRENT_ARTWORK.de.md) | [Français](CURRENT_ARTWORK.fr.md) | [Español](CURRENT_ARTWORK.es.md) | [Italiano](CURRENT_ARTWORK.it.md)

**Beta b12: experimental and off by default.** Existing b7/b8/b9/b10/b11 cards remain usable. No API key, new helper, HACS extension, special permissions or second app is needed on Home Assistant Green/OS.

A read-only connection can still wake a television. Controlled tests covered automatic slideshow changes and one natural-sleep episode on one Frame, not every model or firmware. Leave background mode off if any wake-up risk is unacceptable.

## Automatic artwork memory

### Optional initial synchronization and resume — b12

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

The app then reads only that cached HA state every five seconds. A later observed
`off` followed by a newer `on` within 30 seconds permits one further read. Both
paths share at most six attempts per rolling hour **in that service process**.
Duplicates, stale wake edges or monitoring gaps do not retry. Authentication
refusal blocks automatic reads for that process. Restarting is a new initial
opportunity, not a persistent cross-restart rate limit; do not use restart loops.

HA `on` is not Art Mode proof. A connection may still wake the TV or affect its
mode; this new path has offline simulations, not new hardware safety evidence.
Leave the field empty to disable it. A stopped app cannot observe a wake. The
90-second initial and 15-minute slideshow display limits below are unchanged.

Every successfully selected upload now saves its TV image ID, title, artist and source automatically, even with background mode **off**. Nothing needs to be entered manually. The association belongs to the actual TV identity, not just its IP address: the same image ID on another TV is not the same artwork. A successful new upload replaces an older association for that TV/ID.

The private app data survives normal updates. Clearing the selection history does not erase associations; uninstalling with app-data deletion does. Keep an app backup before reinstalling. Storage is bounded to the latest 2,048 upload associations and 32 MiB, plus one backup. Each reference is a tiny 64×36 RGB sample, not a full-resolution artwork archive. Older image-verified associations remain compatible.

Old TV pictures, uploads from other apps and deliveries without a stable TV identity remain unidentified. Frame Gallery does not guess artists or use cloud image recognition.

## Enable the optional current-artwork card

1. Keep your camera, timer, existing cards and `script.frame_gallery_new_artwork` entity ID.
2. Enable **Background mode**, then restart the app. Start/Stop controls the service, not an image change. Without the optional entity above, startup does not contact the TV; with it, first HA `on` may trigger the initial read.
3. Replace only the script body with the [complete background send script](examples/background-send-script.yaml). Adjust the app slug and existing timer ID if needed. Cards calling this script keep working; direct `hassio.app_start` automations must call the script instead.
4. If Frame Gallery has sent successfully before, configure the optional entity above to read the already displayed artwork without a new send. On a new installation without a saved TV association, request your first new artwork in visible Art Mode; the successful send grants one experimental event session. Refresh alone cannot open a connection.
5. Add a Manual dashboard card using the **complete** YAML below.

The existing picture/colour/artist card shows the **last sent preview**, not a live TV screenshot. This additional native card shows current information separately.

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

**Beta b10 recovery fix:** incomplete sequences of recognized
slideshow notifications clear the current caption and wait on the same
connection for a new complete sequence. They never confirm an artwork or
trigger another query. Unknown or malformed messages, standby, TV mode and
connection loss still end the session. Fixed failure codes in the app log
distinguish startup, receive, decoding and worker errors without raw messages
or credentials. The changed b12 startup path has no new live-TV or sleep validation.

In the log, `event sequence incomplete` means the caption was cleared and the
same connection is waiting, not that an artwork was confirmed.
`event session stopped: reason=...; no reconnect` means the session ended;
include that fixed reason code, app version and TV model in a bug report, not
access tokens or raw TV data. That failed session is not automatically retried.

Each session lasts at most eight hours and ends earlier on sleep, TV mode or
failure. A configured new process start or later fresh HA wake edge above can permit a new read; an explicit successful send can also start a session.

After one initial read and local image comparison, one connection listens for the observed slideshow sequence: `image_selected`, matching `auto_rotation_image_changed`, then Art Mode `on`, within five seconds. Within that session there are no repeated TV queries, subsequent thumbnails or reconnects. A later event resolves metadata from that TV's saved upload or image-verified association; an unknown ID clears the caption.

Initial image proof lasts 90 seconds. A complete slideshow sequence lasts at most **15 minutes**, intended for the tested ten-minute slideshow. Duplicate IDs, pongs and mode-on events do not renew it. Slower slideshows can therefore show gaps; manual selections need not provide this sequence. The template can add about one minute of display delay.

A fixed, unchanged picture can therefore become unconfirmed after 90 seconds.
The initial-start fix does not extend proof age or repeatedly query the TV to
keep a static caption alive.

Sleep, TV mode, disconnection, malformed events or publication failure stop/pause the session without an immediate reconnect. Without the optional wake-edge setting, resuming still requires an explicit new send in visible Art Mode. Refresh only reads already received events. The observer sends no power, Wake-on-LAN, image-selection or mode-change commands. A connection itself can nevertheless cause side effects.

Saved IDs are historical correspondence, not continuous pixel verification. An external, unobserved replacement/reuse of a TV ID cannot be ruled out during event-only listening. A mismatching initial image comparison suppresses the saved caption. No general firmware/no-wake guarantee is claimed (D-235).

The sensor is an app-published HA state, not a registered device integration; it may temporarily disappear after a Core restart. Stale or paused data hides the title. To return to one-shot operation, disable background mode, restart and restore the one-shot send script. Do not delete history or device pins to force a connection.
