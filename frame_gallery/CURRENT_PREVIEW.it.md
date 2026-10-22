# Anteprima dell’opera attuale

[English](CURRENT_PREVIEW.md) | [Deutsch](CURRENT_PREVIEW.de.md) | [Français](CURRENT_PREVIEW.fr.md) | [Español](CURRENT_PREVIEW.es.md) | **Italiano**

**Beta pubblica 0.1.0b17 — anteprima attuale separata e facoltativa.**

**Limitazione di sicurezza (D-247):** la modalità in background resta sperimentale
e disattivata per impostazione predefinita. Connessioni automatiche all'avvio/
risveglio e letture al minuto sono sospese, anche con opzioni salvate. Solo un
nuovo invio esplicito riuscito può avviare l'osservazione passiva della
presentazione. Le immagini immutate scadono; nessuna ripresa automatica dopo
menu/modalità TV, standby o perdita della connessione. La connessione può ancora
influire sul TV: nessuna garanzia di mancato risveglio. Leggere prima
[configurazione e limiti](CURRENT_ARTWORK.it.md).

La scheda immagine esistente continua a mostrare l’ultima opera inviata. Questa scheda facoltativa mostra un’anteprima salvata solo con titolo e artista attuali confermati di recente. Non è una schermata in diretta.

1. Conservare configurazione attuale, schede e script. Nessuna nuova opzione dell’app, permesso speciale, estensione HACS o modifica di configuration.yaml.
2. Dopo un invio riuscito con questa versione viene salvato automaticamente un piccolo JPEG, anche in modalità singola. La visualizzazione attuale richiede l’osservatore facoltativo esistente. Le vecchie immagini del TV non vengono recuperate automaticamente; nessuna richiesta TV aggiuntiva.
3. Dopo l’inizializzazione del servizio in background, aggiungere Local File in Impostazioni → Dispositivi e servizi. Nome: `Frame Gallery Current Preview`; percorso: `/media/frame_gallery/preview/current.jpg`. Non sostituire la precedente camera Local File.
4. Verificare l’ID effettivo della nuova camera. L’esempio usa `camera.frame_gallery_current_preview`; modificare solo `camera_entity` se necessario. Aggiungere la scheda manuale completa qui sotto.

```yaml
type: markdown
title: Frame Gallery — Opera attuale
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
  <img src="{{ (picture ~ separator ~ 'fg=' ~ item.attributes.get('preview_sha256', '')) | e }}" alt="Opera attuale">

    {% else %}
  Nessuna anteprima salvata per quest’opera; i dati dell’artista restano disponibili.

    {% endif %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Ultima conferma: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% else %}
  Nessuna opera confermata di recente.
  {% endif %}
```

Anteprime fino a 640×360 pixel e 32 KiB di JPEG. Cache privata limitata a 128 MiB, overhead incluso, e 4.096 voci; l’espulsione non cancella associazioni o cronologia. Nessuna anteprima inventata per immagini sconosciute, vecchie, rifiutate o espulse. Spazio insufficiente o errori della cache non devono bloccare i metadati.

Usare la scheda completa con controllo di freschezza, non una camera senza protezione: dopo un arresto anomalo il file può conservare l’immagine, ma la scheda nasconde le prove scadute. La disponibilità viene disattivata in HA prima di cambiare il file e riattivata solo dopo una scrittura atomica verificata. L’impronta evita la cache del browser; non è una nuova osservazione TV. latest.jpg e le schede esistenti restano invariati. Nessun download aggiuntivo di miniature TV, riconoscimento cloud o nuova connessione.

[Guida dell’opera attuale](CURRENT_ARTWORK.it.md)
