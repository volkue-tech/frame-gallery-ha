# Frame Gallery — installazione e prima scheda

> Novità beta b11: ripresa facoltativa dopo una transizione spento-acceso Samsung
> HA appena osservata, con un solo tentativo in lettura senza inviare un'altra
> immagine. Configura una volta l'entità esistente; l'avvio con il TV già acceso
> non apre una connessione. L'[opera attuale](CURRENT_ARTWORK.it.md) resta
> sperimentale e disattivata per impostazione predefinita: la connessione può
> risvegliare il TV o cambiarne la modalità. Ogni invio riuscito memorizza
> titolo/artista per quel TV, anche senza background. Il modo singolo seguente non cambia.

[English](DOCS.md#installation) | [Deutsch](SETUP.de.md) | [Français](SETUP.fr.md) | [Español](SETUP.es.md) | **Italiano**

Scegli la lingua con i link: Home Assistant non traduce automaticamente questa guida. Dalla **0.1.0b7**, il modulo dell'app offre inglese, tedesco, francese, spagnolo e italiano secondo la lingua dell'interfaccia HA. La [selezione facoltativa dell'artista](COMMONS_ARTIST.it.md) richiede b7. Su b6 i campi sono in inglese/tedesco: usa le chiavi tecniche indicate. I valori, gli ID e i percorsi restano uguali. I documenti tecnici rimangono [in inglese](DOCS.md#options).

## 1. Installare

Servono Home Assistant OS con Supervisor/App, per esempio HA Green, e HA 2026.2 o successivo. Le installazioni Container e solo Core non possono installare l'app. Il Samsung Frame deve essere nella stessa rete locale e sottorete. Non servono SSH, HACS, chiavi API o modifiche a configuration.yaml.

1. [Aggiungi il repository a Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fvolkue-tech%2Fframe-gallery-ha). In alternativa: Impostazioni → App → Store delle app → ⋮ → Repository e aggiungi `https://github.com/volkue-tech/frame-gallery-ha`.
2. Cerca **Samsung** o **Frame Gallery**, apri **Frame Gallery – Samsung Frame TV** e seleziona **Installa**. Il Green scarica un'immagine già costruita, non compila niente.
3. In Configurazione, inserisci l'IPv4 privato fisso del TV in **Indirizzo del televisore** (`tv_host`), per esempio `192.168.1.20`, e salva. Riserva l'indirizzo nel router. Nomi come `tv.local` non sono accettati.
4. Lascia Watchdog e **Avvia all'avvio del sistema** disattivati: ogni avvio carica un'opera e termina. Non deve riavviarsi in ciclo o cambiare immagine a ogni riavvio di HA.

Per gli aggiornamenti, aggiorna l'app esistente: **non disinstallarla**. Le impostazioni e la cronologia rimangono.

## 2. Prima opera sul televisore

Accendi il TV e premi **Avvia** nella scheda Informazioni dell'app. Segui il **Registro**. Alla prima connessione accetta la richiesta sul TV entro **20 secondi**. Se il modello offre la notifica per dispositivi esterni, scegli l'opzione per la sola prima connessione.

Con `outcome=tv_not_authorized`, riprova e accetta. `outcome=delivered` conferma caricamento e selezione nel protocollo: controlla anche l'immagine reale. **Arrestata** dopo l'esecuzione è normale. Avvia di nuovo per un'altra opera.

| Campo | Consiglio |
| --- | --- |
| Fonte delle opere (`source`) | `wikimedia_commons`, predefinita per le nuove installazioni. |
| Colore desiderato (Commons) (`color`) | `any` per tutti i colori. |
| Solo formato orizzontale (`landscape_only`) | Attivo. |
| Preferisci 16:9 (può richiedere più tempo) (`strict_tv_format`) | Attivo per i rapporti più vicini; disattivo per tutta la selezione. |
| Adattamento dell'immagine (contain = senza ritaglio) (`fit_mode`) | `contain` mostra l'opera intera; `cover` può tagliare i bordi. |

Le 1000 opere Commons sono entro il 2,5 % del 16:9; la preferenza usa circa l'1 %. Piccoli margini possono rimanere. Mostra le opzioni facoltative non utilizzate solo quando servono. La scheda della dashboard non viene creata automaticamente.

## 3. Creare la fotocamera dell'anteprima

Dopo un'esecuzione riuscita: Impostazioni → Dispositivi e servizi → Aggiungi integrazione → **Local File**. Il file di anteprima deve già esistere.

![Finestra Local File reale in tedesco, prima di inserire nome e percorso.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/local-file-setup.png)

La schermata storica è in tedesco: Dateipfad significa percorso del file.

| Campo | Valore |
| --- | --- |
| Nome | `Frame Gallery Preview`, al posto del nome predefinito Local File. |
| Percorso del file | `/media/frame_gallery/preview/latest.jpg` |

OK crea automaticamente una **entità fotocamera** che mostra il file, non una fotocamera fisica. La pagina dell'integrazione si chiama ancora Local File. **1 entità** significa che è già stata creata, non che occorre un'altra installazione.

Apri **1 entità → riga Frame Gallery Preview → ⋮ → Dettagli → ID**. L'ID previsto è `camera.frame_gallery_preview`. Se diverso, usalo ovunque nello YAML. Un nome esistente può creare un suffisso; rinominare dopo non modifica automaticamente l'ID. Riutilizza la fotocamera esistente, non crearne un'altra con lo stesso percorso. Nel selettore della scheda cerca il nome visibile, non soltanto l'ID.

**Privacy:** nei Dettagli compaiono anche token di accesso. Condividi solo l'ID e il percorso, mai tutti gli attributi.

## 4. Creare il timer

Impostazioni → Dispositivi e servizi → Helper → Crea helper → Timer. Nome: `Frame Gallery run`, durata `0:02:30`. Verifica l'ID `timer.frame_gallery_run`.

In Configurazione dell'app inseriscilo in **Timer di caricamento della dashboard** (`loading_timer`) e salva. Crearlo non basta: questo campo collega la fine dell'esecuzione al timer. Usa un timer dedicato a questa app.

## 5. Creare lo script

Impostazioni → Automazioni e scene → Script → Crea script → ⋮ → Modifica in YAML. Incolla tutto il blocco, salva e verifica `script.frame_gallery_new_artwork`. L'alias inglese mantiene il nome tecnico suggerito. Controlla nella URL dell'app l'ID pubblico di esempio `a94fc569_frame_gallery`, non quello di una vecchia app di test. Sostituisci ovunque gli ID diversi.

```yaml
alias: Frame Gallery new artwork
description: Avvia Frame Gallery e mostra un messaggio di caricamento nella dashboard.
mode: single
sequence:
  - condition: state
    entity_id: timer.frame_gallery_run
    state: idle
  - action: timer.start
    target:
      entity_id: timer.frame_gallery_run
    data:
      duration: "00:02:30"
  - action: hassio.app_start
    data:
      app: a94fc569_frame_gallery
    continue_on_error: true
  - wait_template: "{{ not is_state('timer.frame_gallery_run', 'active') }}"
    timeout: "00:02:30"
    continue_on_timeout: true
  - delay: "00:00:04"
```

## 6. Aggiungere la scheda

Modifica la dashboard → Aggiungi scheda → Manuale. Incolla tutto il blocco, sostituisci gli ID diversi e salva. Usa un account amministratore.

```yaml
type: vertical-stack
cards:
  - type: picture-entity
    entity: camera.frame_gallery_preview
    name: Mostra una nuova opera
    show_state: false
    show_name: true
    camera_view: auto
    aspect_ratio: "16:9"
    tap_action:
      action: perform-action
      perform_action: script.turn_on
      target:
        entity_id: script.frame_gallery_new_artwork
    hold_action:
      action: more-info
  - type: conditional
    conditions:
      - condition: state
        entity: timer.frame_gallery_run
        state: active
    card:
      type: markdown
      content: Caricamento dell'opera…
```

Tocca l'immagine per una nuova opera; tieni premuto per l'anteprima. Il testo compare solo con timer attivo. Il timer viene annullato dopo la pulizia, anche senza risultati o dopo un annullamento corretto. La durata di 150 secondi limita l'attesa se la notifica fallisce. Il testo che scompare non prova il successo del caricamento: controlla il registro. L'aggiornamento dell'immagine è indipendente dal timer.

Se un'entità non esiste, verifica gli ID: non creare una seconda fotocamera. L'anteprima del testo nell'editor non dimostra un'esecuzione attiva.

## Opzioni e aiuto

- [Selettore di colore](COMMONS_COLOUR.it.md): un helper Menu a discesa, nessun nuovo script.
- [Selettore dell'artista](COMMONS_ARTIST.it.md): disponibile da b7; aggiorna prima se usi b6.
- [Titolo e artista](ARTWORK_INFO.md): guida inglese, helper Testo separato; la scheda standard funziona senza.

Su GitHub i blocchi hanno un pulsante di copia. Se manca nella scheda Documentazione di HA, apri la guida su GitHub. Copia solo YAML, non i delimitatori Markdown.

Senza nuove opere idonee, TV, anteprima e informazioni restano invariati. Le opere già inviate rimangono escluse. I download temporanei vengono puliti; l'app non cancella le immagini già nel TV. Non è garantita la compatibilità con tutti i modelli. [Segnala un problema](https://github.com/volkue-tech/frame-gallery-ha/issues) con versione, modello e risultato finale, senza segreti.

Progetto indipendente, non affiliato a Samsung, Wikimedia, musei o Home Assistant. [Aiuto tecnico e licenze](DOCS.md#reading-the-log) restano in inglese.
