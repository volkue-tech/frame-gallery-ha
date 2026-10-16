# Current artwork and optional background mode

English | [Deutsch](CURRENT_ARTWORK.de.md) | [Français](CURRENT_ARTWORK.fr.md) | [Español](CURRENT_ARTWORK.es.md) | [Italiano](CURRENT_ARTWORK.it.md)

**Public beta b8. Existing b7 cards remain compatible with background mode off.
Experimental and off by default.**
Read-only connections may wake a sleeping TV. Automatic no-motion sleep has not
been validated: leave this mode off if waking the TV is unacceptable. No API
key, new helper, HACS extension or second app is required.

## Keep existing cards

Leave **Background mode** off to retain the existing one-shot app and cards.
To opt in, enable it and restart the app. Start/Stop then
controls the service, not a picture change. Optionally enable **Start on boot**;
boot/restart will not send an artwork. Restart after changing app options.

Replace only the body of `script.frame_gallery_new_artwork` with the complete
[background send script](examples/background-send-script.yaml). Keep its entity
ID, existing timer and camera. Cards and automations calling that script keep
working. Automations directly calling `hassio.app_start` must use the script
instead. Never use app restart as an image-change button.

Use the installed app slug and your existing timer ID if they differ from the
example. The script generates a fresh request ID and timestamp; do not hard-code
or reuse them. Sending is explicit; a read-only refresh cannot send an image.

## Optional current information card

Add a Manual card and paste this complete configuration. It adds no helper and
does not change your existing picture/colour/artist card. That image remains
the **last sent preview**, not a live screenshot of the TV.

```yaml
type: markdown
title: Frame Gallery — Current artwork
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% if item is not defined or item is none %}
  No current information is available.
  {% elif item.state == 'artwork' and
      as_timestamp(now()) - as_timestamp(item.last_reported, 0) < 90 %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Last checked: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'validation_required' %}
  TV checks are blocked. Check the app log and send an artwork explicitly.
  {% elif item.state == 'checking' %}
  Artwork operation in progress. Current display is not yet confirmed.
  {% elif item.state == 'unidentified' %}
  The displayed artwork has not been identified.
  {% else %}
  The current artwork is not confirmed. The TV may be unavailable or checks paused.
  {% endif %}
```

This is an app-published HA state, not a registered device integration. After a
Core restart it can temporarily be missing; after an app failure it becomes
stale. The card hides unconfirmed titles. The time-aware template can add up to
roughly one minute of display delay. Old TV pictures without verified mappings
remain unidentified. No cloud image-recognition service is used.

## Safety and recovery

After updating the script, explicitly request **one new artwork while the TV
is in Art Mode**. Only a successful delivery arms checks, roughly every 30
seconds. Start/boot/restart alone never contacts the TV. The first check pins
the device identity; later checks refuse another device at the same address.
An error, authorization failure or inactive Art Mode pauses checks without
reconnecting. To resume, put the TV in Art Mode yourself and explicitly send
another artwork. A read-only refresh cannot re-arm paused checks. Turning the
mode off and restarting restores the one-shot path; also restore the original
one-shot send script. Do not clear history or device pins to force a connection.

The last-delivery caption remains separate. Do not present it as current TV
information. One real Art-Mode read, image comparison and title/artist template
were verified on a Frame; this is not a no-wake guarantee for your model.
Natural sleep, transitions and sustained Recorder growth remain beta follow-ups.
No power, wake-on-LAN or Art-Mode changes are sent by the observer. These limits
do not make the underlying connection itself incapable of waking a television.
