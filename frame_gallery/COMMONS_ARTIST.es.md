# Selección de artista — desde la beta 0.1.0b7

[English](COMMONS_ARTIST.md) | [Deutsch](COMMONS_ARTIST.de.md) | [Français](COMMONS_ARTIST.fr.md) | **Español** | [Italiano](COMMONS_ARTIST.it.md)

Requiere 0.1.0b7 o posterior; no configures estas opciones en 0.1.0b6. Elige un artista opcional para Commons. Ningún ayudante obligatorio nuevo ni sustitución de la tarjeta: la tarjeta estándar sigue funcionando. Las otras fuentes indican que no admiten este filtro.

Sin selector en el panel: muestra las opciones opcionales sin usar en Frame Gallery → Configuración. En **Artista deseado (Commons, opcional)** (`artist`), copia un nombre completo de la [lista](ARTIST_CHOICES.md), por ejemplo `Wassily Kandinsky`. Vacío o `All artists` significa sin restricción. Guarda e inicia la app como siempre.

## Configuración

Para un desplegable: Ajustes → Dispositivos y servicios → Ayudantes → Crear ayudante → Desplegable (los nombres pueden variar). Nombre: `Frame Gallery Artist`. Añade `All artists` y tus nombres favoritos como opciones separadas. Debajo tienes un ejemplo. No traduzcas los nombres ni los valores técnicos.

```text
All artists
Wassily Kandinsky
Claude Monet
Vincent van Gogh
Pierre-Auguste Renoir
Winslow Homer
W.carter
```

Abre el ayudante → ⋮ → Detalles y comprueba su ID real, normalmente `input_select.frame_gallery_artist`. Un nombre existente puede generar un sufijo. Introduce ese ID en **Artista desde el panel (opcional, Commons)** (`artist_helper`), conserva Commons y guarda. Elige primero `All artists`. No reutilices el ayudante Texto de información de la obra.

El desplegable tiene prioridad sobre el artista guardado. Un valor ilegible, no disponible o inválido usa el ajuste guardado con un aviso. Cambiar el desplegable no inicia automáticamente la app: primero elige, después toca la imagen. Los cambios durante una ejecución se aplican al siguiente inicio.

Deben coincidir tanto el artista como el color. La alternativa de formato puede relajar 16:9, nunca el artista o el color. Las obras ya enviadas siguen excluidas. La lista muestra totales, no obras sin usar: Kandinsky y Monet tienen una obra cada uno actualmente. La selección puede agotarse después de usarla. Sin coincidencias, televisor, vista previa y texto permanecen intactos y la ejecución termina correctamente. Amplía con `All artists` o `any`. No se reinicia el historial automáticamente.

## Solo artista

Tarjeta solo con artista: reutiliza cámara, temporizador y script de la [instalación](SETUP.es.md). Solo se añade el desplegable de artistas. Sustituye todos los ID diferentes. YAML no crea ayudantes. No hace falta HACS, SSH ni cambiar configuration.yaml.

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
    name: Mostrar una nueva obra
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
      content: Cargando la obra…
```

## Artista y color

Tarjeta con artista y color: configura también el [ayudante de color](COMMONS_COLOUR.es.md), con `input_select.frame_gallery_colour` y `color_helper`. Reutiliza cámara, temporizador y script. Es una pila nativa, sin extensión del panel.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
      - entity: input_select.frame_gallery_artist
        name: Artista (solo Commons)
      - entity: input_select.frame_gallery_colour
        name: Color deseado (solo Commons)
  - type: picture-entity
    entity: camera.frame_gallery_preview
    name: Mostrar una nueva obra
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
      content: Cargando la obra…
```

La [tarjeta opcional de información](ARTWORK_INFO.md) sigue separada y sin cambios. El artista de la vista previa no indica necesariamente tu próxima selección. La app no instala tarjetas ni crea o rellena ayudantes automáticamente.
