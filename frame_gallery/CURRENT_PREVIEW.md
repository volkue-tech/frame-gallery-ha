# Current artwork preview

> **0.1.0b19 — optional unchanged-artwork confirmation (D-247/D-250/D-252).** NEW `confirm_current_artwork` is experimental and OFF by default; it requires background mode and the existing Samsung `resume_state_entity`. Only an independently granted, verified Art session may confirm Art-on/current-ID on its SAME socket, at most four GETs per minute. No new connection, startup/recovery permission, image/power/mode command or blind retry. Quiet valid reads keep still-fresh artist/title/preview visible. Off/menu/standby, stale HA/proof/clock state or connection/query failure end the session. The eight-hour limit remains; a lost session needs a later independent grant. Old `current_state_refresh` and initial-on reads remain suspended. Optional b18 `standby_resume` is separate/default OFF: the running app must observe 30 s off then fresh stable 10 s on, with at most six attempts/hour and60s spacing. Reads can still affect firmware or sleep; this is NOT a no-wake guarantee. Existing cards/scripts/data/permissions remain compatible. [b19 evidence and limits](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA19_VALIDATION.md).

**English** | [Deutsch](CURRENT_PREVIEW.de.md) | [Français](CURRENT_PREVIEW.fr.md) | [Español](CURRENT_PREVIEW.es.md) | [Italiano](CURRENT_PREVIEW.it.md)

**0.1.0b17 public beta — separate optional current-image preview.**

**Observer safety hold (D-247):** background mode remains experimental and off by
default. Automatic startup/wake connections and minute reads are suspended,
including saved opt-ins. Only a fresh explicitly requested successful send can
start passive slideshow observation. Unchanged pictures expire; menu/TV mode,
sleep or connection loss does not recover automatically. A connection can still
affect the TV: this is not a no-wake guarantee. Read the
[current-artwork setup and limits](CURRENT_ARTWORK.md) first.

The existing image card remains the last artwork sent. This separate optional card shows a cached preview only when the current artist/title state is freshly confirmed. It is not a live screenshot.

1. Keep the existing current-artwork setup, cards and scripts. This feature adds no app option, privilege, HACS extension or configuration.yaml edit.
2. After a successful delivery with this version, a small JPEG is cached automatically, including in one-shot mode. Current display requires the existing optional background observer. Older TV images are not automatically backfilled, and no additional TV request is made.
3. Once the background service has initialized, add the Local File integration in Settings → Devices & services. Name it `Frame Gallery Current Preview`; file path: `/media/frame_gallery/preview/current.jpg`. This does not replace the previous Local File camera.
4. Check the new camera's actual entity ID. The example uses `camera.frame_gallery_current_preview`; change only `camera_entity` below if HA chose another ID. Add the complete optional manual card below.

```yaml
type: markdown
title: Frame Gallery — Current artwork
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% set camera_entity = 'camera.frame_gallery_current_preview' %}
  {% if item is defined and item is not none %}
    {% set age = as_timestamp(now()) - as_timestamp(item.last_reported, 0) %}
  {% else %}
    {% set age = -1 %}
  {% endif %}
  {% if item is defined and item is not none and item.state == 'artwork'
      and age >= 0 and age <
      (900 if item.attributes.get('confirmation_method') == 'slideshow_events' else 90) %}
    {% set picture = state_attr(camera_entity, 'entity_picture') %}
    {% if item.attributes.get('preview_available', false)
        and picture is string and picture
        and state_attr(camera_entity, 'file_path') == '/media/frame_gallery/preview/current.jpg'
        and states(camera_entity) not in ['unknown', 'unavailable'] %}
      {% set separator = '&' if '?' in picture else '?' %}
  <img src="{{ (picture ~ separator ~ 'fg=' ~ item.attributes.get('preview_sha256', '')) | e }}" alt="Current artwork">

    {% else %}
  No cached preview for this artwork; artist information remains available.

    {% endif %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Last confirmed: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% else %}
  No freshly confirmed artwork is available.
  {% endif %}
```

Previews are at most 640×360 pixels and 32 KiB of JPEG data. The private cache is limited to 128 MiB including storage overhead and 4,096 entries; eviction never deletes associations or history. Unknown, old, rejected or evicted images have no invented preview. Low disk space or cache failure must not block artist metadata.

Use the complete guarded card, not an unguarded standalone current-file camera: after a crash the file can retain its last contents, while the card hides stale evidence. Availability is cleared in HA before the file changes and advertised only after a verified atomic write. The checksum busts browser image caches; it is not a new TV observation. The old latest.jpg and existing cards are untouched. No TV thumbnail download, cloud recognition or new connection is added.

[Current-artwork guide](CURRENT_ARTWORK.md)

**0.1.0b18 — optional bounded standby recovery (D-247/D-250).** Old saved switches still do not authorize automatic reads: `current_state_refresh` and initial-on reads remain suspended. NEW `standby_resume` is OFF by default and requires background mode plus an existing Samsung `resume_state_entity`. The running app must observe off continuously for 30 seconds, then a genuinely fresh on stable for 10 seconds, before one exact-device/image revalidation; at most six attempts/hour, at least 60 seconds apart across ordinary restarts. No image, power or mode commands, enrollment or blind retries are added by recovery. Lost sessions while HA stays on need a new complete cycle. Physical connection side effects remain unresolved; this is NOT a no-wake guarantee. Existing cards/scripts remain unchanged. See the [complete optional status card](CURRENT_STATUS.md), [current preview](CURRENT_PREVIEW.md) and [b18 evidence/limits](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA18_VALIDATION.md).
