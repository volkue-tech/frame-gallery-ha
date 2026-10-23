# Frame Gallery — Opera attuale

**0.1.0b18 — ripresa facoltativa e limitata dopo standby (D-247/D-250).** Le vecchie opzioni non autorizzano letture automatiche: `current_state_refresh` e la lettura iniziale con TV già acceso restano sospese. Il NUOVO `standby_resume` è disattivato per impostazione predefinita; richiede background ed entità Samsung esistente `resume_state_entity`. L'app attiva deve osservare 30 secondi di spento continuo, poi un'accensione realmente recente e stabile per 10 secondi, prima di una sola verifica del TV e dell'immagine. Massimo sei tentativi all'ora, distanziati di almeno 60 secondi anche dopo normali riavvii. La ripresa non aggiunge comandi immagine, power o modalità, nuovi abbinamenti o ripetizioni cieche. Dopo disconnessione senza nuovo standby occorre un altro ciclo completo. Gli effetti fisici della connessione restano irrisolti: nessuna garanzia di non risveglio. Carte/script conservati. [Carta di stato completa facoltativa](CURRENT_STATUS.it.md) · [anteprima attuale](CURRENT_PREVIEW.it.md) · [prove e limiti b18](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA18_VALIDATION.md).

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
