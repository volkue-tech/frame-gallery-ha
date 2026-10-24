# Frame Gallery — Opera attuale

**0.1.0b19 — conferma facoltativa delle opere invariate (D-247/D-250/D-252).** NUOVO: `confirm_current_artwork`, sperimentale e disattivato per impostazione predefinita; richiede background e l'entità Samsung esistente `resume_state_entity`. Solo una sessione Art verificata e autorizzata separatamente può confermare modalità/ID sulla STESSA connessione, al massimo quattro GET al minuto. Nessuna nuova connessione, autorizzazione iniziale/ripresa, comando immagine/power/modalità o tentativo cieco. Le letture valide mantengono visibili artista/titolo/anteprima ancora recenti. Spento/menu/standby, dati HA/prove/orologio scaduti o errori chiudono la sessione. Resta il limite di otto ore; dopo disconnessione serve un'altra autorizzazione indipendente. Vecchio `current_state_refresh` e letture iniziali restano sospesi. `standby_resume` b18 resta separato/disattivato: osservare 30 s spento e 10 s acceso recente stabile, massimo sei tentativi/ora distanziati 60 s. Anche le letture possono influire su firmware o sonno; nessuna garanzia di non risveglio. Carte/script/dati/permessi compatibili. [Prove e limiti b19](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA19_VALIDATION.md).

[English](CURRENT_STATUS.md) | [Deutsch](CURRENT_STATUS.de.md) | [Français](CURRENT_STATUS.fr.md) | [Español](CURRENT_STATUS.es.md) | Italiano

```yaml
type: markdown
title: Frame Gallery — Opera attuale
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% set camera_entity = 'camera.frame_gallery_current' %}
  {% set messages = {
      'safety_hold': "Ripresa automatica non autorizzata. Le vecchie opzioni non la attivano.",
      'configuration_required': "Entità Samsung mancante; ripresa automatica disattivata.",
      'waiting_for_standby': "In attesa di un intero ciclo standby/risveglio osservato; nessuna lettura all'avvio.",
      'standby': "HA indica TV spento. Lettura in pausa; nessun comando di accensione inviato.",
      'wake_settling': "Risveglio rilevato; attesa di stato HA stabile prima della lettura.",
      'wake_revalidation': "Verifica unica autorizzata dopo il risveglio in corso.",
      'ha_state_unavailable': "Stato HA assente, non valido o interrotto. Serve un nuovo ciclo completo.",
      'rate_limited': "Limite tentativi raggiunto. Nessuna ripetizione differita; serve un nuovo ciclo.",
      'budget_unavailable': "Ripresa bloccata: budget salvato non leggibile/scrivibile in sicurezza.",
      'tv_authorization': "Autorizzazione TV rifiutata. Nessuna ripetizione automatica; verificare accesso TV.",
      'association_required': "Validazione locale TV/associazione fallita. Nessuna connessione di ripresa avviata.",
      'connection_failed': "Sessione di lettura fallita o disconnessa. Nessuna ripetizione cieca.",
      'session_failed': "Sessione rifiutata o errata. Metadati attuali nascosti.",
      'service_stopped': "Frame Gallery è stata arrestata; nessuna conferma TV attuale.",
      'proof_expired': "Prova immagine scaduta. In attesa di una nuova prova valida.",
      'waiting_for_event': "Immagine attuale non confermata. Attesa di eventi passivi completi della presentazione; nessuna richiesta TV in corso."
  } %}
  {% if item is not defined or item is none %}
  Nessuna informazione attuale disponibile.
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

  Ultima conferma: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'artwork' %}
  L'ultima conferma è scaduta. Nessun artista attuale visualizzato.
  {% elif reason in messages %}
  {{ messages[reason] }}
  {% elif item.state == 'checking' %}
  Verifica di modalità Arte e immagine; non ancora confermata.
  {% elif item.state == 'unidentified' %}
  Nessuna associazione salvata per l'opera osservata.
  {% elif item.state == 'tv_in_use' %}
  Modalità Arte non confermata: programma TV o menu delle opere.
  {% elif item.state == 'not_authorized' %}
  {{ messages['tv_authorization'] }}
  {% elif item.state == 'unavailable' %}
  Sessione di lettura non disponibile o terminata; causa non confermata.
  {% elif item.state == 'validation_required' %}
  Nessuna prova TV attuale. Le associazioni salvate non confermano l'immagine in diretta.
  {% else %}
  Sincronizzazione in pausa; questa versione non indica la causa esatta. Non dimostra un guasto di rete del TV.
  {% endif %}
  {% endif %}
```
