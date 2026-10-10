# Elegir un color — desde la beta 0.1.0b6

[English](COMMONS_COLOUR.md) | [Deutsch](COMMONS_COLOUR.de.md) | [Français](COMMONS_COLOUR.fr.md) | **Español**

Esta página está en español. Home Assistant no cambia automáticamente el
idioma de la documentación: utiliza los enlaces de arriba.
Esta actualización traduce las guías, no los campos de configuración de la app.
Los nombres de esos campos se indican en inglés a continuación.

Esta guía sirve para **0.1.0b6 y versiones posteriores**, con 1000 obras
seleccionadas de Commons. El filtro de color no está disponible en 0.1.0b5
ni en versiones anteriores. Para empezar, sigue primero la
[guía de instalación y tarjeta estándar](SETUP.es.md).
El selector de color del panel es opcional.

## Elegir un color en la app

1. Abre **Settings → Apps → Frame Gallery → Configuration**
   (Ajustes → Apps → Frame Gallery → Configuración).
2. Elige `wikimedia_commons` en **Artwork source**.
3. Justo debajo, en **Colour wish (Commons)**, selecciona un color,
   por ejemplo **Blue** para azul. **any** significa todos los colores
   y sigue siendo la opción predeterminada.
4. Guarda. La próxima ejecución, iniciada desde la app o tu tarjeta actual,
   buscará una obra dentro de esta selección.

No necesitas una clave API, un ayudante nuevo, otro script ni cambiar la tarjeta
para utilizar este ajuste. La vista previa y la información opcional del título
y del artista siguen funcionando. Un catálogo nuevo no reinicia el historial
de obras enviadas.

## ¿Qué significa «azul»?

El azul debe ocupar una parte visible de la obra, pero no tiene que ser su color
dominante. El umbral es aproximadamente el cinco por ciento de la imagen.
Una obra azul y amarilla puede aparecer tanto con Blue como con Yellow.
Los tonos ocres y dorados pueden clasificarse como Yellow. Son familias
generales de colores, no una coincidencia exacta con una pintura de pared o un HEX.

Las opciones son Red, Orange, Yellow, Green, Blue, Purple, Pink, Brown, Beige,
Gray, Black y White. Los datos de análisis también conservan proporciones
y hasta tres familias importantes diferentes. Esta versión permite
deliberadamente **un solo** color, no combinaciones de colores.

El análisis se realiza en el Mac durante la preparación del catálogo.
La app no tiene que descargar muchas imágenes en el Green para probar sus
colores. Los márgenes negros añadidos al adaptar la imagen al televisor
no se cuentan como colores de la obra.

## ¿No hay una obra nueva que coincida?

La ejecución termina correctamente. La imagen actual del televisor, la vista
previa y los datos de la obra se conservan. La app no elige otro color sin avisar.
Las obras ya enviadas o subidas siguen excluidas; una selección pequeña puede
agotarse con el tiempo.

Elige otro color o **any**. El registro distingue la falta de coincidencias de
un fallo de la fuente. Como el tiempo y las solicitudes están limitados, una
ejecución sin resultado no significa necesariamente que todas las obras de
ese color queden excluidas permanentemente.

**Prefer 16:9** puede recurrir a otra imagen horizontal con márgenes si no hay
una coincidencia con el formato preferido, pero nunca a otro color.
Recomendamos **contain** para conservar la obra completa sin recortarla.

## Otras fuentes y ayudante opcional

La selección de color solo funciona con Commons. Chicago, Cleveland y tus
propias imágenes no tienen este filtro; el registro indica que el color no
se ha aplicado cuando se utiliza una de esas fuentes.

Las otras fuentes siguen disponibles. La tarjeta de abajo está diseñada para
Commons y no incluye un selector de fuente. Si cambias la fuente en la
configuración de la app, el color de la tarjeta **no** se aplica a ella.
Por eso la lista se llama **Color deseado (solo Commons)**.
La última obra mostrada no permite saber qué fuente se usará en la próxima
ejecución.

Un ayudante de color puede controlar la misma selección desde el panel.
No es necesario para la instalación estándar. Por ejemplo, la app entiende
**Blau**, **Blue** y **color_blue** como el mismo valor.
No traduzcas las opciones al español: utiliza los valores indicados abajo.
Varios colores en un solo valor no se interpretan como una combinación.

## Añadir el selector a la tarjeta

**Opcional; disponible desde 0.1.0b6.** La tarjeta estándar sigue funcionando
sin este paso. No necesitas HACS ni un nuevo script. El ayudante Dropdown nuevo
solo es necesario para elegir el color desde el panel.

Las rutas de menú siguientes utilizan los nombres en inglés. Si Home Assistant
está en español, busca las secciones equivalentes; sus traducciones pueden
variar según la versión.

1. Abre **Settings → Devices & services → Helpers → Create helper → Dropdown**.
   Ponle el nombre `Frame Gallery Colour`.
2. Añade estas opciones por separado, exactamente como aparecen, una por opción:
   `any`, `Red`, `Orange`, `Yellow`, `Green`, `Blue`, `Purple`, `Pink`, `Brown`,
   `Beige`, `Gray`, `Black`, `White`. `any` significa todos los colores.
   Los valores en inglés son iguales en todas las versiones de esta guía.
3. Guarda y comprueba el ID real de la entidad: abre el ayudante →
   **⋮ → Details**. ID esperado: `input_select.frame_gallery_colour`.
   Si ya existe una entidad con ese nombre, el ID puede ser distinto.
4. En **Frame Gallery → Configuration**, introduce ese ID en **Colour helper**
   (`color_helper`). Si no aparece, activa **Show unused optional configuration
   options**. Mantén Commons como fuente y guarda.
5. Selecciona `any`. Utiliza el bloque completo de abajo en tu tarjeta.
   Sustituye en todas las apariciones los IDs de cámara, temporizador, script
   y ayudante que sean diferentes en tu instalación.

El selector tiene prioridad sobre el color guardado en la app.
Cambiar el color **no inicia automáticamente** una ejecución: primero elige
el color y después toca la imagen. Un cambio durante la carga se aplica
en la siguiente ejecución. Si el ayudante no se puede leer, la app utiliza
su ajuste guardado y lo indica en el registro.
No se ofrece la selección simultánea de varios colores.

### Tarjeta completa con vista previa y selector de color

Reutiliza la cámara, el temporizador y el script de la guía de instalación.
El YAML **no crea** el ayudante: termina antes los cinco pasos.
Todos los componentes de la tarjeta están integrados en Home Assistant.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
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

La tarjeta opcional del título y del artista puede mantenerse por separado debajo.
Sin una extensión adicional, el resultado es un grupo de tarjetas nativas,
no una única tarjeta personalizada.

**Prueba rápida después de actualizar:** elige `Blue`, toca la imagen y espera
a que termine. Después elige `any` y repite. Si no coincide ninguna obra
que todavía no se haya enviado, la imagen y los datos se conservan y la ejecución
termina igualmente. El selector puede seguir visible durante la carga.
