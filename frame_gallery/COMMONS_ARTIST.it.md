# Selezione dell'artista — aggiornamento candidato non pubblicato

[English](COMMONS_ARTIST.md) | [Deutsch](COMMONS_ARTIST.de.md) | [Français](COMMONS_ARTIST.fr.md) | [Español](COMMONS_ARTIST.es.md) | **Italiano**

Non ancora disponibile nella versione pubblica 0.1.0b6. Non configurare queste opzioni su b6. Il candidato aggiunge un artista facoltativo per Commons. Nessun nuovo helper obbligatorio o sostituzione della scheda: quella standard continua a funzionare. Le altre fonti segnalano che il filtro non è supportato.

Senza selettore nella dashboard: mostra le opzioni facoltative non utilizzate in Frame Gallery → Configurazione. In **Artista desiderato (Commons, facoltativo)** (`artist`), copia un nome completo dalla [lista](ARTIST_CHOICES.md), ad esempio `Wassily Kandinsky`. Vuoto o `All artists` significa nessuna restrizione. Salva e avvia l'app normalmente.

## Configurazione

Per un menu a discesa: Impostazioni → Dispositivi e servizi → Helper → Crea helper → Menu a discesa (i nomi possono variare). Nome: `Frame Gallery Artist`. Aggiungi `All artists` e i tuoi nomi preferiti come opzioni separate. Sotto trovi un esempio. Non tradurre i nomi o i valori tecnici.

```text
All artists
Wassily Kandinsky
Claude Monet
Vincent van Gogh
Pierre-Auguste Renoir
Winslow Homer
W.carter
```

Apri l'helper → ⋮ → Dettagli e verifica il suo ID effettivo, normalmente `input_select.frame_gallery_artist`. Un nome già esistente può generare un suffisso. Inserisci questo ID in **Artista dalla dashboard (facoltativo, Commons)** (`artist_helper`), mantieni Commons e salva. Inizia con `All artists`. Non riutilizzare l'helper Testo delle informazioni sull'opera.

Il menu ha priorità sull'artista salvato. Un valore illeggibile, non disponibile o non valido usa l'impostazione salvata con un avviso. Cambiare il menu non avvia automaticamente l'app: prima scegli, poi tocca l'immagine. Le modifiche durante un'esecuzione valgono dall'avvio successivo.

Devono corrispondere sia l'artista sia il colore. L'alternativa di formato può allentare il 16:9, mai artista o colore. Le opere già inviate restano escluse. La lista mostra totali, non opere inutilizzate: Kandinsky e Monet hanno attualmente un'opera ciascuno. La selezione può esaurirsi dopo l'uso. Senza risultati, TV, anteprima e didascalia restano invariati e l'esecuzione termina correttamente. Amplia con `All artists` o `any`. Nessun ripristino automatico della cronologia.

## Solo artista

Scheda con solo artista: riutilizza fotocamera, timer e script della [configurazione](SETUP.it.md). Si aggiunge soltanto il menu degli artisti. Sostituisci tutti gli ID diversi. YAML non crea helper. Non servono HACS, SSH o modifiche a configuration.yaml.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
      - entity: input_select.frame_gallery_artist
        name: Artista (solo Commons)
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

## Artista e colore

Scheda con artista e colore: configura anche [l'helper del colore](COMMONS_COLOUR.it.md), con `input_select.frame_gallery_colour` e `color_helper`. Riutilizza fotocamera, timer e script. È uno stack nativo, senza estensioni della dashboard.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
      - entity: input_select.frame_gallery_artist
        name: Artista (solo Commons)
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

La [scheda facoltativa delle informazioni](ARTWORK_INFO.md) resta separata e invariata. L'artista dell'anteprima non indica necessariamente la prossima selezione. L'app non installa schede e non crea né popola automaticamente helper.
