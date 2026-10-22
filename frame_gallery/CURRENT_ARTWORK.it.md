# Opera attuale e modalità in background facoltativa

Locale, non pubblicato: [anteprima facoltativa dell’opera attuale](CURRENT_PREVIEW.it.md). Le schede esistenti restano invariate.

[English](CURRENT_ARTWORK.md) | [Deutsch](CURRENT_ARTWORK.de.md) | [Français](CURRENT_ARTWORK.fr.md) | [Español](CURRENT_ARTWORK.es.md) | Italiano

**Corretto in b16:** l'aggiornamento facoltativo accetta le risposte reali
`artmode_status` / `current_artwork`, verificando rigorosamente l'ID della richiesta.
Nessuna nuova opzione, connessione, formato di associazione o modifica delle schede.

**Beta pubblica b16: sperimentale e disattivato per impostazione predefinita.** Le schede b7/b8/b9/b10/b11/b12/b13 restano utilizzabili. Nessun nuovo aiutante, chiave API, HACS, privilegio speciale o altra app su Home Assistant Green/OS.

[Rapporto b16](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA16_VALIDATION.md) · [Sorgenti corrispondenti](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b16).

Anche una connessione in lettura può risvegliare il TV. I test controllati coprono cambi automatici e un episodio di sonno naturale su un Frame, non tutti i modelli o firmware. Lasciare disattivato se questo rischio è inaccettabile.

## Memoria automatica delle opere

### Sincronizzazione all'avvio e dopo standby — b12, facoltativo

Dopo un invio Frame Gallery precedente riuscito, attivare **Modalità in background**
e inserire in **Sincronizza all'avvio / dopo standby** (`resume_state_entity`) l'entità Samsung
HA esistente di questo TV (`media_player` o `remote`). L'ID si trova in Impostazioni
→ Dispositivi e servizi → Entità. Riavviare l'app. Nessun nuovo helper, invio di
immagini o modifica delle schede.

Il primo stato HA in cache a ogni avvio così configurato consente **una sola
lettura iniziale se indica `on`**, anche se invariato da ore. Identità, modalità
Arte, ID e immagine vengono verificati prima di artista/titolo; nessuna immagine
inviata. Un primo risultato mancante, non valido, futuro, `off`, sconosciuto o
fallito consuma l'opportunità; i successivi `on` non la ripetono.

**Finestra iniziale — b13:** una finestra fissa di dieci secondi dà
priorità a una richiesta accettata di nuova opera rispetto alla lettura iniziale
automatica. L'accettazione annulla l'opportunità iniziale residua prima
dell'invio, anche se poi fallisce o non trova alcuna opera (`no_match`). Solo un
invio valido e riuscito può quindi aprire la propria sessione di lettura. Senza
una richiesta accettata, la sincronizzazione iniziale autonoma resta possibile
dopo la finestra se lo stato HA in cache rimane valido e `on`. Le regole
successive di ripresa dopo vere transizioni `off`/`on` rimangono invariate.

Questa finestra limitata non può anticipare script con ritardi arbitrari. Se un
ricevitore autonomo è già partito, un invio successivo deve prima arrestarlo e
attenderne la fine. I test offline di questa correzione non forniscono nuove
prove hardware contro risvegli del TV o cambi di modalità.

Il monitor di ripresa legge quello stato HA in cache ogni cinque secondi;
è distinto dalle verifiche facoltative del socket Art descritte sotto.
Un `off` osservato e un
`on` più recente di al massimo 30 secondi permettono una nuova lettura. Entrambi
i percorsi condividono sei tentativi per ora mobile **in questo processo**.
Duplicati, transizioni vecchie e interruzioni non consentono nuovi tentativi.
Un rifiuto di autenticazione blocca letture automatiche nel processo. Un riavvio
è una nuova opportunità, non un limite persistente fra riavvii; evitare cicli
di riavvio.

HA `on` non dimostra modalità Arte. La connessione può risvegliare il TV o cambiarne
la modalità; il nuovo percorso è simulato offline, non verificato sull'hardware.
Vuoto: disattivato. Un'app arrestata non osserva risvegli. Restano i limiti di
visualizzazione di 90 secondi e 15 minuti.

Ogni invio selezionato con successo salva automaticamente ID TV, titolo, artista e fonte, anche con la modalità in background **disattivata**. Nessun ID da inserire. L'associazione appartiene alla vera identità del TV, non solo al suo IP. Lo stesso ID su un altro TV non indica la stessa opera. Un nuovo invio riuscito sostituisce l'associazione precedente per quel TV/ID.

I dati privati sopravvivono agli aggiornamenti normali. Azzerare la cronologia di selezione non elimina le associazioni; disinstallare cancellando i dati sì. Conservare un backup prima della reinstallazione. Limite: le ultime 2.048 associazioni e 32 MiB, più un backup. Il riferimento è un piccolo campione RGB di 64×36 pixel, non un archivio ad alta risoluzione. Le vecchie associazioni verificate tramite immagine restano compatibili.

Vecchie immagini, invii di altre app e invii senza identità stabile rimangono sconosciuti. Nessun artista indovinato o riconoscimento cloud.

### Aggiornamento facoltativo dello stato attuale — b16

`current_state_refresh` è un'opzione aggiuntiva, **disattivata per impostazione
predefinita**, che richiede `background_mode`. Consente al massimo una verifica
in lettura della coerenza della modalità Arte attuale e dell'ID immagine ogni
60 secondi, sul **socket Art già collegato**. Serve a ripristinare artista/titolo
noti dopo il menu del TV o la ripresa della presentazione, anche con la stessa
immagine. Nessuna nuova connessione né comando di immagine, alimentazione o
modalità.
Un'immagine sconosciuta resta non identificata; nessun titolo viene inventato
o ripreso dall'immagine precedente.

Una prova nuova e valida `current_state_read` vale 90 secondi.
ID duplicati, pong o notifiche di modalità attiva da soli non la rinnovano.

Con questa opzione, `off` o `nav` del canale Art mantiene **lo stesso socket**;
questi stati non sono standby fisico. Fuori dalla modalità Arte, titolo e artista
vengono nascosti. Le verifiche proseguono anche senza notifica di ritorno: entro
lo stesso limite di una volta al minuto si legge solo la modalità finché non è
attiva. Gli ID immagine vengono richiesti soltanto dopo un nuovo risultato `on`;
un ciclo di menu non conferma un'opera. Se la sessione vede inizialmente `off` o
`nav`, l'unica prova iniziale tramite miniatura attende la modalità Arte `on` su
quel socket; non viene ripetuta. Standby, stato HA «off» osservato o connessione
chiusa continuano a terminare la sessione, senza nuovo socket o riconnessione cieca.

Le richieste, anche sullo stesso socket, possono influire sul sonno automatico.
Lasciare disattivato se il rischio è inaccettabile. I test offline non certificano
la compatibilità dei firmware né l'assenza di risvegli del TV.
Le schede e gli script esistenti non richiedono modifiche.

## Attivare la scheda facoltativa

1. Conservare fotocamera, timer, schede e ID `script.frame_gallery_new_artwork`.
2. Attivare **Modalità in background** e riavviare l'app. Avvia/Arresta controlla il servizio, non l'immagine. Senza l'entità facoltativa sopra nessun contatto all'avvio; con essa il primo HA `on` può consentire la lettura dopo la finestra di dieci secondi, salvo che una richiesta di invio accettata la sostituisca.
3. Sostituire solo il contenuto dello script con lo [script di invio completo](examples/background-send-script.yaml). Adattare slug e timer se diversi. Le schede continuano a funzionare; sostituire le chiamate dirette a `hassio.app_start` con lo script.
4. Dopo un invio precedente riuscito, configurare l'entità sopra per leggere l'opera già visibile senza un nuovo invio. Su un'installazione senza associazione TV salvata, richiedere la prima opera in modalità Arte visibile; l'invio riuscito consente una sessione sperimentale. Aggiornare da solo non apre connessioni.
5. Aggiungere una scheda manuale con il YAML **completo** seguente.

La scheda immagine/colore/artista mostra l'**ultima anteprima inviata**, non una schermata dal vivo. Questa scheda nativa aggiuntiva presenta separatamente le informazioni attuali.

```yaml
type: markdown
title: Frame Gallery — Opera attuale
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% if item is not defined or item is none %}
  Nessuna informazione attuale disponibile.
  {% elif item.state == 'artwork' and
      as_timestamp(now()) - as_timestamp(item.last_reported, 0) <
      (900 if item.attributes.get('confirmation_method') == 'slideshow_events' else 90) %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Ultima conferma: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'validation_required' %}
  In attesa di una verifica autorizzata. Controllare impostazioni background/entità e registro; la lettura iniziale configurata non richiede una nuova immagine.
  {% elif item.state == 'checking' %}
  Immagine attuale non confermata. In attesa di una prova valida di immagine o presentazione.
  {% elif item.state == 'unidentified' %}
  Nessuna associazione salvata per l'opera visualizzata.
  {% else %}
  Opera attuale non confermata. TV non disponibile o sessione sospesa.
  {% endif %}
```

## Conferma e limiti

**Recupero storico b10 — soli eventi (`current_state_refresh` disattivato):** una sequenza incompleta di
notifiche riconosciute della presentazione nasconde i dati attuali e attende una
nuova sequenza completa sulla stessa connessione. Non conferma alcuna opera e
non invia altre richieste. Messaggi sconosciuti o non validi, standby, modalità
TV e perdita della connessione continuano a terminare la sessione. Codici fissi
nel registro distinguono errori di avvio, ricezione, decodifica e processo
isolato, senza messaggi grezzi o credenziali. L'avvio b12 e la finestra b13 non hanno una nuova
validazione fisica TV o sonno.

Con `current_state_refresh` attivo, le notifiche strutturalmente valide ma non
riconosciute e `off`/`nav` del canale Art nascondono i dati e mantengono lo stesso
socket secondo le regole limitate sopra. Non confermano opere né autorizzano
nuove connessioni. Standby fisico, rifiuto di autenticazione, dati di protocollo
malformati e trasporto chiuso continuano a terminare la sessione.

Nel registro, `event sequence incomplete` indica che i dati sono stati nascosti
e la stessa connessione attende, senza confermare alcuna opera.
`event session stopped: reason=...; no reconnect` indica che la sessione è
terminata, senza ripetizione immediata. Per segnalare un problema, includi quel
codice fisso, la versione e il modello del TV, mai token o dati TV grezzi.

Ogni sessione dura al massimo otto ore. Nel modo a soli eventi
(`current_state_refresh` disattivato), sonno, modalità TV o errori possono terminarla
prima. Restano applicabili le eccezioni facoltative e gli arresti definitivi sopra. Un nuovo processo configurato o una transizione HA recente sopra può consentire una lettura; anche un invio esplicito riuscito può aprire una sessione.

Dopo una lettura iniziale e confronto locale, una connessione ascolta la sequenza osservata: `image_selected`, `auto_rotation_image_changed` con lo stesso ID e modalità Arte `on`, entro cinque secondi. Con `current_state_refresh` disattivato, nella stessa sessione nessuna richiesta ripetuta, miniatura successiva o riconnessione. Attivarlo consente solo le verifiche limitate sopra, non nuove miniature o connessioni. Un evento cerca l'associazione di invio o immagine verificata di quel TV; un ID sconosciuto cancella il testo.

La prova iniziale dura 90 secondi. Una sequenza completa dura al massimo **15 minuti**, per il ciclo testato di dieci minuti. Duplicati, pong e modalità attiva non rinnovano nulla. Cicli più lunghi possono creare intervalli vuoti; i cambi manuali non sempre producono questa sequenza. Il modello può aggiungere circa un minuto di ritardo.

Con l'aggiornamento disattivato o senza una nuova verifica riuscita, un'immagine
fissa invariata può tornare non confermata dopo 90 secondi.
La sola correzione dell'avvio non estende la prova né interroga ripetutamente il TV per
mantenere una didascalia artificialmente aggiornata.

**Soli eventi (`current_state_refresh` disattivato):** Sonno, modalità TV, disconnessione, eventi non validi o errore di pubblicazione sospendono/arrestano senza riconnettere subito. Con l'opzione attiva, si applicano le regole limitate dello stesso socket e gli arresti definitivi sopra. Dopo l'effettiva fine della sessione, senza l'opzione di ripresa sopra serve ancora un nuovo invio esplicito in modalità Arte visibile. L'azione manuale Aggiornare elabora solo eventi già ricevuti. Nessun comando di alimentazione, Wake-on-LAN, selezione immagine o cambio modalità; la connessione stessa può comunque causare effetti indesiderati.

Gli ID salvati sono corrispondenze storiche, non verifica continua dei pixel. Un riutilizzo esterno non osservato non è escludibile. Un confronto iniziale contraddittorio blocca la didascalia salvata. Nessuna garanzia generale di firmware o mancato risveglio (D-235).

Il sensore è uno stato pubblicato dall'app, non un'integrazione registrata. Può mancare dopo un riavvio di Core. Dati scaduti/sospesi nascondono il titolo. Per tornare al funzionamento singolo, disattivare, riavviare e ripristinare lo script originale. Non cancellare cronologia o identità per forzare una connessione.
