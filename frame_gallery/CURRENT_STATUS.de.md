# Frame Gallery — Aktuelles Kunstwerk

**0.1.0b19 — optionale Bestätigung unveränderter Kunstwerke (D-247/D-250/D-252).** NEU: `confirm_current_artwork`, experimentell und standardmäßig AUS; erforderlich sind Hintergrundmodus und die vorhandene Samsung-Entität `resume_state_entity`. Nur eine separat freigegebene, geprüfte Kunstmodus-Sitzung darf Modus/Bild-ID über DIESELBE Verbindung bestätigen, höchstens vier GETs pro Minute. Keine neue Verbindung, Start-/Wiederanlauffreigabe, Bild-/Power-/Modusbefehle oder blinden Wiederholungen. Gültige ruhige Abfragen halten noch frische Künstler-/Titel-/Vorschaudaten sichtbar. Aus/Menü/Standby, veraltete HA-/Bild-/Zeitnachweise oder Verbindungs-/Abfragefehler beenden die Sitzung. Die Achtstundengrenze bleibt; nach Abbruch ist eine spätere separate Freigabe nötig. Altes `current_state_refresh` und Startabrufe bleiben gesperrt. b18 `standby_resume` bleibt separat/standardmäßig AUS: laufend 30 s Aus, danach frisches stabiles 10 s An beobachten, höchstens sechs Versuche/Stunde mit 60 s Abstand. Auch Abfragen können Firmware/Schlaf beeinflussen; keine Nichtaufweckgarantie. Karten/Skripte/Daten/Rechte bleiben kompatibel. [b19-Nachweise und Grenzen](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA19_VALIDATION.md).

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
