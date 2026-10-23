# Frame Gallery — Current artwork

**0.1.0b18 — optional bounded standby recovery (D-247/D-250).** Old saved switches still do not authorize automatic reads: `current_state_refresh` and initial-on reads remain suspended. NEW `standby_resume` is OFF by default and requires background mode plus an existing Samsung `resume_state_entity`. The running app must observe off continuously for 30 seconds, then a genuinely fresh on stable for 10 seconds, before one exact-device/image revalidation; at most six attempts/hour, at least 60 seconds apart across ordinary restarts. No image, power or mode commands, enrollment or blind retries are added by recovery. Lost sessions while HA stays on need a new complete cycle. Physical connection side effects remain unresolved; this is NOT a no-wake guarantee. Existing cards/scripts remain unchanged. See the [complete optional status card](CURRENT_STATUS.md), [current preview](CURRENT_PREVIEW.md) and [b18 evidence/limits](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA18_VALIDATION.md).

English | [Deutsch](CURRENT_STATUS.de.md) | [Français](CURRENT_STATUS.fr.md) | [Español](CURRENT_STATUS.es.md) | [Italiano](CURRENT_STATUS.it.md)

```yaml
type: markdown
title: Frame Gallery — Current artwork
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% set camera_entity = 'camera.frame_gallery_current' %}
  {% set messages = {
      'safety_hold': "Automatic recovery is not authorized. Existing saved switches do not enable it.",
      'configuration_required': "Samsung status entity is missing; automatic recovery is disabled.",
      'waiting_for_standby': "Waiting for a fully observed standby/wake cycle; app startup alone makes no TV request.",
      'standby': "HA reports the TV off. Reading is paused; no power command is sent.",
      'wake_settling': "Wake detected; waiting for a stable HA state before any TV read.",
      'wake_revalidation': "Performing the single authorized wake revalidation.",
      'ha_state_unavailable': "HA state missing, invalid or interrupted. Recovery is blocked until a new clean cycle.",
      'rate_limited': "Recovery attempt limit reached. No delayed retry; a new clean cycle is required.",
      'budget_unavailable': "Recovery blocked: the saved attempt budget cannot be safely read or written.",
      'tv_authorization': "TV authorization refused. No automatic retries; review TV access authorization.",
      'association_required': "Local device/association validation failed. No recovery connection was started.",
      'connection_failed': "Reading session failed or disconnected. No blind retry; wait for a new clean cycle.",
      'session_failed': "Reading session rejected or failed. Current metadata is hidden.",
      'service_stopped': "Frame Gallery was stopped; no current TV confirmation.",
      'proof_expired': "The image proof expired. Waiting for a new valid proof.",
      'waiting_for_event': "Current image not confirmed. Waiting for complete passive slideshow events; no TV request is running."
  } %}
  {% if item is not defined or item is none %}
  No current information available.
  {% else %}
  {% set age = as_timestamp(now()) - as_timestamp(item.last_reported, 0) %}
  {% set reason = item.attributes.get('status_reason', '') %}
  {% if item.state == 'artwork' and age >= 0 and age <
      (900 if item.attributes.get('confirmation_method') == 'slideshow_events' else 90) %}
  {% set picture = state_attr(camera_entity, 'entity_picture') %}
  {% if item.attributes.get('preview_available', false) and
      states(camera_entity) not in ['unknown', 'unavailable'] and
      state_attr(camera_entity, 'file_path') == '/media/frame_gallery/preview/current.jpg' and
      picture is string and picture %}
  <img src="{{ picture | e }}{{ '&' if '?' in picture else '?' }}fg={{ item.attributes.get('preview_sha256', '') | e }}" style="max-width:100%;border-radius:12px" />

  {% endif %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Last confirmed: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'artwork' %}
  The last image confirmation expired. No current artist information is shown.
  {% elif reason in messages %}
  {{ messages[reason] }}
  {% elif item.state == 'checking' %}
  Checking Art Mode and the current image; not confirmed yet.
  {% elif item.state == 'unidentified' %}
  No saved association for the currently observed artwork.
  {% elif item.state == 'tv_in_use' %}
  Art Mode is not confirmed (TV programme or artwork menu).
  {% elif item.state == 'not_authorized' %}
  {{ messages['tv_authorization'] }}
  {% elif item.state == 'unavailable' %}
  Reading session unavailable or ended; the exact cause is unconfirmed.
  {% elif item.state == 'validation_required' %}
  No current TV proof. Saved associations alone are not a live confirmation.
  {% else %}
  Synchronization paused; this app version did not supply the exact reason. This does not prove a TV network failure.
  {% endif %}
  {% endif %}
```
