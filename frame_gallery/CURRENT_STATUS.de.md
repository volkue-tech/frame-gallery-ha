# Frame Gallery — Aktuelles Kunstwerk

Lokaler, unveröffentlichter Kandidat. Bestehende Karten und Scripte bleiben erhalten. Diese vollständige optionale native Karte unterscheidet gestoppt, pausiert und fehlgeschlagene Lesesitzungen. standby_resume ist eine NEUE, standardmäßig ausgeschaltete Freigabe mit Hintergrundmodus und vorhandener Samsung-Entität:30s durchgehend Aus beobachten, danach frisches An10s stabil. Ein Versuch pro Wechsel, max6/Stunde/min60s Abstand über Neustarts. Keine Start-/Minutenabfragen, Bild-/Power-/Modusbefehle oder blinden Wiederholungen. Schon Lesen kann Firmware-Nebenwirkungen haben; Offline-Tests garantieren kein Nichtaufwecken. Die App muss während des ganzen Wechsels laufen; eine gestoppte App kann nicht fortsetzen. Bei Verbindungsverlust und weiter bestehendem HA-An ist ein neuer echter Standby-/Aufwachwechsel nötig. Die b17-Anleitungen bleiben bis zu einer separat freigegebenen Veröffentlichung das veröffentlichte Verhalten.

[English](CURRENT_STATUS.md) | Deutsch | [Français](CURRENT_STATUS.fr.md) | [Español](CURRENT_STATUS.es.md) | [Italiano](CURRENT_STATUS.it.md)

```yaml
type: markdown
title: Frame Gallery — Aktuelles Kunstwerk
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% set camera_entity = 'camera.frame_gallery_current' %}
  {% set messages = {
      'safety_hold': "Automatischer Wiederanlauf nicht freigegeben. Alte gespeicherte Schalter aktivieren ihn nicht.",
      'configuration_required': "Samsung-Zustandsentität fehlt. Automatischer Wiederanlauf ist gesperrt.",
      'waiting_for_standby': "Warte auf vollständig beobachteten Standby-/Aufwachwechsel. App-Start allein fragt den TV nicht ab.",
      'standby': "HA meldet den TV als aus. Abgleich pausiert; es wird kein Einschaltbefehl gesendet.",
      'wake_settling': "Aufwachen erkannt. Warte auf stabilen HA-Zustand; noch keine TV-Abfrage.",
      'wake_revalidation': "Der einmal freigegebene Wiederanlauf prüft jetzt Kunstmodus und Bild.",
      'ha_state_unavailable': "HA-Zustand fehlt, ist ungültig oder die Beobachtung war unterbrochen. Neuer sauberer Wechsel nötig.",
      'rate_limited': "Versuchsbegrenzung erreicht. Kein verzögerter Retry; neuer sauberer Wechsel nötig.",
      'budget_unavailable': "Wiederanlauf gesperrt: gespeicherte Versuchsbegrenzung nicht sicher lesbar/schreibbar.",
      'tv_authorization': "TV-Zugriff nicht autorisiert. Keine automatischen Wiederholungen; TV-Freigabe prüfen.",
      'association_required': "Lokale TV-/Bildzuordnung nicht validierbar. Keine Wiederanlauf-Verbindung gestartet.",
      'connection_failed': "Lesesitzung fehlgeschlagen oder getrennt. Keine blinde Wiederholung; neuer sauberer Wechsel nötig.",
      'session_failed': "Lesesitzung abgewiesen oder fehlerhaft. Aktuelle Künstlerdaten ausgeblendet.",
      'service_stopped': "Frame Gallery wurde gestoppt. Keine aktuelle TV-Bestätigung.",
      'proof_expired': "Bildbestätigung abgelaufen. Warte auf einen neuen gültigen Nachweis.",
      'waiting_for_event': "Aktuelles Bild nicht bestätigt. Warte auf vollständige passive Diashow-Ereignisse; es läuft keine TV-Abfrage."
  } %}
  {% if item is not defined or item is none %}
  Noch keine aktuellen Informationen verfügbar.
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

  Zuletzt bestätigt: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'artwork' %}
  Die letzte Bildbestätigung ist abgelaufen. Keine aktuellen Künstlerdaten anzeigen.
  {% elif reason in messages %}
  {{ messages[reason] }}
  {% elif item.state == 'checking' %}
  Prüfe Kunstmodus und aktuelle Bild-ID; noch nicht bestätigt.
  {% elif item.state == 'unidentified' %}
  Für das aktuell beobachtete Kunstwerk ist keine Zuordnung gespeichert.
  {% elif item.state == 'tv_in_use' %}
  Kunstmodus nicht bestätigt: TV-Programm oder Bildmenü aktiv.
  {% elif item.state == 'not_authorized' %}
  {{ messages['tv_authorization'] }}
  {% elif item.state == 'unavailable' %}
  Lesesitzung nicht erreichbar oder beendet; genaue Ursache nicht bestätigt.
  {% elif item.state == 'validation_required' %}
  Kein aktueller TV-Nachweis. Gespeicherte Zuordnungen allein sind keine Live-Bestätigung.
  {% else %}
  Abgleich pausiert; diese App-Version meldet keine genaue Ursache. Das beweist keinen TV-Netzwerkfehler.
  {% endif %}
  {% endif %}
```
