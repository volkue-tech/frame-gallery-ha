# Frame Gallery — Opera attuale

Candidato locale non pubblicato. Carte e script esistenti conservati. Carta nativa completa con stati distinti. standby_resume è un NUOVO consenso disattivato per impostazione predefinita: richiede background ed entità Samsung esistente,30s di spento osservato e accensione recente stabile10s. Un tentativo per transizione,max6/ora,min60s anche dopo riavvii. Nessuna lettura iniziale/periodica, comando immagine/power/modalità o ripetizione cieca. La connessione può influire sul TV; i test offline non garantiscono il non risveglio. L'app deve restare attiva per tutta la transizione; da arrestata non può riprendere. Dopo disconnessione senza nuovo standby attendere un nuovo ciclo completo. Le guide b17 restano il comportamento pubblicato fino a pubblicazione autorizzata separatamente.

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
