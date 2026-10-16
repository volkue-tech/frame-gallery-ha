# Opera attuale e modalità in background facoltativa

[English](CURRENT_ARTWORK.md) | [Deutsch](CURRENT_ARTWORK.de.md) | [Français](CURRENT_ARTWORK.fr.md) | [Español](CURRENT_ARTWORK.es.md) | Italiano

**Candidato locale b8; la versione pubblica b7 non cambia. Sperimentale e
disattivato per impostazione predefinita.** Una connessione in lettura potrebbe
risvegliare un TV in standby. Lo standby automatico senza movimento non è ancora
verificato. Lasciare il modo disattivato se il risveglio è inaccettabile.
Non servono altri aiutanti, chiavi API, HACS o un'altra app.

Senza la modalità in background, le schede e il funzionamento a esecuzione
singola restano invariati. Per provarla, attivarla e riavviare l'app.
Avvia/Arresta controllano quindi il servizio, non il cambio dell'immagine.
L'avvio automatico è facoltativo e non invia un'opera. Riavviare l'app dopo
averne modificato le opzioni.

Sostituire solo il contenuto di `script.frame_gallery_new_artwork` con lo
[script di invio completo](examples/background-send-script.yaml), mantenendo
ID, fotocamera e timer. Le schede che chiamano lo script continuano a funzionare.
Sostituire le chiamate dirette a `hassio.app_start` con lo script. Adattare lo
slug dell'app e l'ID del timer se diversi. I valori tecnici restano in inglese.
Non sostituire l'ID della richiesta e l'ora generati con valori fissi.

## Scheda informativa facoltativa

Aggiungere una scheda manuale con questo blocco completo. La scheda esistente
con immagine/colore/artista resta separata: la sua anteprima è l'ultima immagine
inviata, non una schermata dal vivo del televisore.

```yaml
type: markdown
title: Frame Gallery — Opera attuale
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% if item is not defined or item is none %}
  Nessuna informazione attuale disponibile.
  {% elif item.state == 'artwork' and
      as_timestamp(now()) - as_timestamp(item.last_reported, 0) < 90 %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Ultima verifica: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'validation_required' %}
  Verifiche bloccate. Controllare il registro e richiedere esplicitamente un'opera.
  {% elif item.state == 'checking' %}
  Operazione in corso. L'immagine attuale non è ancora confermata.
  {% elif item.state == 'unidentified' %}
  L'opera visualizzata non è stata identificata.
  {% else %}
  Opera attuale non confermata. TV non disponibile oppure verifiche in pausa.
  {% endif %}
```

Questo stato di HA non è un'integrazione dispositivo registrata. Può mancare
dopo un riavvio di HA o diventare obsoleto se l'app si arresta. La scheda nasconde
i titoli non confermati e può aggiungere circa un minuto di ritardo. Le vecchie
immagini senza associazione verificata restano sconosciute. Non cancellare la
cronologia per identificarle. Non viene usato il riconoscimento immagini cloud.

Dopo la modifica dello script, richiedere **una nuova opera con il TV in modalità
Arte**. Solo un invio riuscito attiva le letture, circa ogni 30 secondi.
Avvia/riavvia da solo non contatta il TV. La prima lettura memorizza l'identità;
un altro dispositivo allo stesso indirizzo viene rifiutato. Errori o modalità
Arte inattiva sospendono le letture senza riconnessione. Per riprendere, portare
il TV in modalità Arte e richiedere un'altra opera; aggiornare non riattiva le
letture. Per tornare al modo singolo, disattivare il modo, riavviare e ripristinare
lo script di invio originale. Non cancellare cronologia o identità per forzare la connessione.

È stata verificata una lettura reale con confronto immagine e titolo/artista,
non lo standby automatico, tutte le transizioni o la crescita del Recorder.
L'osservatore non invia comandi di alimentazione, Wake-on-LAN o modifiche alla
modalità Arte; tuttavia la connessione stessa potrebbe risvegliare il TV.
