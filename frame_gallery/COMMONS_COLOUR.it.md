# Scegliere un colore — dalla beta 0.1.0b6

[English](COMMONS_COLOUR.md) | [Deutsch](COMMONS_COLOUR.de.md) | [Français](COMMONS_COLOUR.fr.md) | [Español](COMMONS_COLOUR.es.md) | **Italiano**

La lingua di questa guida si sceglie con i link: Home Assistant non cambia automaticamente la documentazione. Il filtro esiste dalla **0.1.0b6**. La versione pubblica b6 ha il modulo dell'app in inglese/tedesco; il prossimo aggiornamento candidato aggiunge anche francese, spagnolo e italiano. I nomi dei campi qui sotto sono quelli italiani del candidato; su b6 usa la chiave tecnica indicata. I valori di selezione restano in inglese.

Segui prima la [configurazione standard](SETUP.it.md). Il selettore nella dashboard è facoltativo: non servono un nuovo script, HACS o modifiche a configuration.yaml. Nessuna chiave API è richiesta.

## Scegliere nella configurazione dell'app

Apri Impostazioni → App → Frame Gallery → Configurazione. In **Fonte delle opere** (`source`) seleziona `wikimedia_commons`. In **Colore desiderato (Commons)** (`color`) scegli per esempio `Blue`; `any` significa tutti i colori. Salva: la scelta vale dal prossimo avvio. La scheda esistente e le informazioni facoltative sull'opera continuano a funzionare.

Un blu deve occupare una parte visibile dell'opera, circa il 5 %, non necessariamente la zona più grande. Un quadro blu e giallo può quindi rientrare in entrambi i gruppi. Sono famiglie ampie, non valori HEX o colori esatti della parete. I margini neri aggiunti per il televisore non contano. L'analisi è preparata con il catalogo: il Green non scarica tante immagini per provarne i colori.

Le opzioni sono `any`, `Red`, `Orange`, `Yellow`, `Green`, `Blue`, `Purple`, `Pink`, `Brown`, `Beige`, `Gray`, `Black`, `White`. Significano tutti, rosso, arancione, giallo, verde, blu, viola, rosa, marrone, beige, grigio, nero, bianco. I dati conservano anche le quote e fino a tre famiglie importanti per future combinazioni. La selezione simultanea di più colori non è disponibile.

## Senza nuove corrispondenze

L'esecuzione termina correttamente. L'immagine sul TV, l'anteprima e le informazioni precedenti restano invariati: non viene scelto un colore diverso. Le opere già inviate o caricate restano escluse e una selezione piccola può esaurirsi. Scegli un altro colore o `any`. Con limiti di tempo e richieste, un'esecuzione senza risultati non dimostra che tutte le opere di quel colore siano esaurite.

**Preferisci 16:9** può passare a un'immagine orizzontale intera con margini, mai a un altro colore. `contain` resta la scelta consigliata per evitare ritagli. Un aggiornamento del catalogo non azzera la cronologia.

## Altre fonti

Il colore funziona solo con Commons. Chicago, Cleveland e i file locali restano disponibili ma non supportano il filtro: il registro segnala che non è applicato. La scheda sotto non cambia la fonte. Se la cambi nella configurazione dell'app, il selettore di colore non si applica alle altre fonti. L'ultima opera visualizzata non identifica necessariamente la fonte del prossimo avvio.

## Aggiungere il selettore nella dashboard

1. Apri Impostazioni → Dispositivi e servizi → Helper → Crea helper → Menu a discesa (i nomi possono variare). Nome: `Frame Gallery Colour`.
2. Aggiungi separatamente le 13 opzioni inglesi elencate sopra, esattamente come scritte. Non tradurre questi valori.
3. Salva, apri l'helper → ⋮ → Dettagli e verifica l'ID reale, normalmente `input_select.frame_gallery_colour`. Un nome già usato può creare un suffisso.
4. In Frame Gallery → Configurazione, inserisci l'ID in **Colore dalla dashboard (facoltativo, Commons)** (`color_helper`). Mostra le opzioni facoltative non utilizzate, se necessario. Mantieni Commons e salva.
5. Inizia con `any`. Incolla tutto il blocco sotto nella scheda; sostituisci tutti gli ID diversi.

Cambiare il menu non avvia automaticamente l'app: prima scegli, poi tocca l'immagine. Il suo valore ha priorità sul colore salvato; durante un'esecuzione le modifiche valgono per il prossimo avvio. Se non è leggibile, viene usato il colore salvato con un avviso. Non usare lo stesso helper delle informazioni sull'opera.

## Scheda completa con anteprima e colore

Riutilizza fotocamera, timer e script della guida standard. YAML non crea gli helper. Tutti i componenti sono nativi di Home Assistant.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
      - entity: input_select.frame_gallery_colour
        name: Colore desiderato (solo Commons)
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

La scheda facoltativa di titolo/artista può restare separata sotto lo stack. Non si tratta di una singola scheda personalizzata con un bordo comune; non servono estensioni aggiuntive.

Per provare: seleziona `Blue`, tocca l'immagine e attendi la fine, poi ripeti con `any`. Se non ci sono opere nuove idonee, l'immagine rimane invariata e l'esecuzione termina comunque. Per il prossimo candidato, [artista e colore insieme](COMMONS_ARTIST.it.md) sono un'opzione separata, non ancora disponibile su b6.
