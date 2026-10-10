# Frame Gallery — instalación y primera tarjeta

[English](DOCS.md#installation) | [Français](SETUP.fr.md) | **Español**

Guía inicial para la **beta 0.1.0b6**. El idioma de esta página se elige con
los enlaces de arriba, no automáticamente desde Home Assistant.
Los documentos técnicos siguen [en inglés](DOCS.md#options).
Esta actualización traduce las guías, no el formulario de configuración
de la app. Las rutas de menú y los campos se indican en inglés para que
coincidan con la interfaz inglesa; si Home Assistant está traducido, busca
las secciones equivalentes.

**Pasos:** instalar → mostrar una obra en el TV → añadir la tarjeta opcional →
[añadir el selector de color](COMMONS_COLOUR.es.md).

## Antes de empezar

- **Home Assistant OS con Supervisor/Apps**, por ejemplo Home Assistant Green,
  con Home Assistant 2026.2 o posterior. Las instalaciones Container y
  Core sin Supervisor no pueden instalar esta app.
- Un **Samsung Frame TV** en la misma red local y subred.
- La dirección IPv4 privada del TV, por ejemplo `192.168.1.20`. Resérvala
  en el router para que sea fija. No se aceptan nombres como `tv.local`.
- En los ajustes de conexión del TV para dispositivos externos, selecciona
  la notificación de acceso *First Time Only* si tu modelo ofrece ese ajuste.

No necesitas SSH, terminal, clave API ni cambiar `configuration.yaml`.
Tampoco necesitas una cuenta de Wikimedia.

## 1. Instalar desde Home Assistant

1. [Añade el repositorio a Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fvolkue-tech%2Fframe-gallery-ha).
   También puedes abrir **Settings → Apps → App store → ⋮ → Repositories**
   y añadir `https://github.com/volkue-tech/frame-gallery-ha`.
   Es un repositorio de apps, no una integración HACS.
2. Busca **Samsung** o **Frame Gallery**, abre **Frame Gallery – Samsung
   Frame TV** y pulsa **Install**. Se descarga la imagen ya construida
   para tu dispositivo; el Green no tiene que compilarla.
3. En **Configuration**, introduce **TV address** y pulsa **Save**.
   Para la primera prueba, conserva los demás valores predeterminados.
4. Deja **Watchdog** y **Start on boot** desactivados. Cada inicio carga
   una obra y después la app se detiene normalmente; no debe reiniciarse
   en bucle ni cambiar la imagen cada vez que HA se reinicia.

Para actualizar, actualiza la app existente: **no la desinstales**.
Se conservan la configuración y el historial de envíos.

## 2. Mostrar la primera obra

1. Enciende el TV. En la pestaña **Info** de la app, pulsa **Start**.
2. Mira la pestaña **Log**. En la primera conexión, acepta la petición
   de autorización en el TV **en un plazo de 20 segundos**.
3. Si aparece `outcome=tv_not_authorized`, inicia la app otra vez y acepta
   la petición. `outcome=delivered` indica que el protocolo ha confirmado
   el envío y la selección; comprueba también la imagen en el TV.
4. Ver **Stopped** al terminar es normal. Vuelve a iniciar la app cuando
   quieras otra obra.

No necesitas la tarjeta para esta primera prueba. La instalación no crea
automáticamente ninguna tarjeta del panel.

### Ajustes recomendados

| Campo en inglés de la app | Recomendación |
| --- | --- |
| TV address | La dirección IPv4 privada fija del TV. |
| Artwork source | `wikimedia_commons`, predeterminado en una instalación nueva. |
| Colour wish (Commons) | `any` para todos los colores; elegir un color es opcional. |
| Landscape only | Activado para imágenes horizontales. |
| Prefer 16:9 (may take longer) | Activado para priorizar el formato más cercano; desactivado para toda la selección Commons. |
| Image fit (contain = no crop) | `contain` conserva la obra completa. `cover` puede recortar los bordes. |

Las 1000 fuentes Commons se alejan como máximo un 2,5 % de la proporción 16:9.
La preferencia 16:9 utiliza un umbral más estricto de aproximadamente un 1 %;
pueden quedar pequeños márgenes. Las opciones avanzadas son opcionales.
Activa **Show unused optional configuration options** solo cuando necesites
uno de esos campos. El filtro de color funciona únicamente con Commons.

## 3. Añadir la tarjeta estándar al panel

**Opcional.** Crearás una cámara de vista previa, un temporizador y un script.
La «cámara» muestra el archivo de imagen; no es una cámara física.
Utiliza una cuenta administradora. No necesitas HACS ni una extensión de tarjetas.

![Tarjeta real de Frame Gallery con Counter-composition XVI e información opcional de la obra.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/dashboard-commons.png)

*Captura histórica de la beta b3 en Green, con texto en alemán e información
opcional. No muestra el nuevo selector de color ni es una nueva prueba.
Obra: Theo van Doesburg,
[Counter-composition XVI](https://commons.wikimedia.org/w/index.php?curid=3817033),
reproducción de Wikimedia Commons cuyos metadatos de dominio público se
comprobaron el 5 de octubre de 2026.*

### A. Crear y nombrar la cámara de vista previa

Después de una ejecución correcta de la app, abre **Settings → Devices &
services → Add integration → Local File**. El archivo de vista previa debe
existir antes.

![Diálogo real de Local File en alemán con los campos Name y Dateipfad.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/local-file-setup.png)

*Captura antes de rellenar los campos. «Dateipfad» significa ruta del archivo.
Los dos valores siguientes son iguales en todos los idiomas.*

| Campo | Valor que debes introducir |
| --- | --- |
| Name | `Frame Gallery Preview` — sustituye el nombre predeterminado `Local File`. |
| File path | `/media/frame_gallery/preview/latest.jpg` |

Pulsa **OK**. **La cámara se crea automáticamente.** La página de la
integración puede seguir llamándose **Local File**; el enlace **1 entity**
significa que ya existe la entidad, no que falte otra instalación.

1. Pulsa **1 entity** y después la fila **Frame Gallery Preview**
   (o **Local File** si conservaste el nombre predeterminado).
2. En la ventana de la imagen, abre **⋮ → Details** y copia **ID**.
3. El ID esperado es `camera.frame_gallery_preview`. Comprueba también
   la ruta del archivo. Si tu ID es diferente, utiliza el ID real en el YAML.

Si ya creaste esta cámara, reutilízala: no crees otra integración Local File
con la misma ruta. El selector de entidades de la tarjeta muestra el
**nombre visible** Frame Gallery Preview o Local File, no necesariamente
el ID técnico. Cambiar el nombre visible de una entidad existente no cambia
automáticamente su ID. Mantén los nombres propuestos para facilitar la instalación.

**Privacidad:** Details también contiene tokens de acceso y una URL con token.
Comparte solo el ID y la ruta, no todos los atributos.

### B. Crear el temporizador de carga

Abre **Settings → Devices & services → Helpers → Create helper → Timer**.
Nombre: `Frame Gallery run`. Duración: `0:02:30`.
ID esperado: `timer.frame_gallery_run`.

En la configuración de Frame Gallery, introduce ese ID en **Dashboard loading
timer** (`loading_timer`). Muestra las opciones opcionales si está oculto.
Crear el temporizador no basta: ese campo conecta la finalización de la app
con tu temporizador. Utiliza uno dedicado a esta app.

### C. Crear el script

Abre **Settings → Automations & scenes → Scripts → Create script → ⋮ →
Edit in YAML**. Copia el bloque **completo**, guarda y comprueba el ID
`script.frame_gallery_new_artwork`. El alias se mantiene en inglés para
conservar el nombre técnico esperado. Si tus IDs o el ID de la app son
distintos, cámbialos en todas sus apariciones. El ID público observado de
la app es `a94fc569_frame_gallery`; comprueba la URL de su página.
No uses el ID de una antigua app local de pruebas.

```yaml
alias: Frame Gallery new artwork
description: Starts the Frame Gallery app and shows a note on the dashboard while it runs.
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

### D. Añadir la tarjeta

Edita el panel, elige **Add card → Manual** y pega el bloque completo.
Sustituye todos los IDs diferentes antes de guardar.

```yaml
type: vertical-stack
cards:
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

Toca la imagen para cargar una obra nueva; mantén pulsado para abrir la vista
previa. El texto de carga solo se muestra mientras el temporizador está activo.
Es normal que desaparezca cuando está inactivo. El temporizador vuelve al estado
inactivo después de la limpieza, incluso sin coincidencia o tras una cancelación
correcta. Su duración de 150 segundos limita la espera si falla la notificación.
Que desaparezca el texto no demuestra un envío correcto: consulta el registro.
La actualización de la imagen es independiente de ese temporizador.

Si aparece «Entity not found», comprueba los IDs en lugar de crear otra cámara.
En el editor, la vista previa del texto de carga no demuestra que haya una
ejecución activa.

**Copiar el YAML:** en GitHub, sitúa el puntero sobre el bloque y utiliza el botón
de copia. Si la pestaña Documentation no lo ofrece, abre esta página en GitHub.
No copies los delimitadores Markdown y conserva la sangría.

## 4. Añadir un color o los datos de la obra

- [Selector de color: guía completa en español](COMMONS_COLOUR.es.md).
  Añade una lista opcional, no un script nuevo. Cambiar el color no inicia
  automáticamente una ejecución.
- [Título y artista: guía en inglés](ARTWORK_INFO.md).
  Opcional: necesita un ayudante Text separado. La tarjeta estándar
  funciona sin él.

Si no hay una obra nueva que coincida, se conservan la imagen y los datos
anteriores. Las obras ya enviadas siguen excluidas. Las imágenes descargadas
temporalmente se limpian; la app no elimina las obras guardadas en el TV.

## Ayuda y límites

No se garantiza la compatibilidad con todos los modelos de TV.
Si falla, mira el resultado final del registro y consulta
[las explicaciones técnicas en inglés](DOCS.md#reading-the-log).
[Informa de un problema](https://github.com/volkue-tech/frame-gallery-ha/issues)
con la versión, el modelo y el resultado, sin contraseñas ni tokens.

Proyecto independiente, sin afiliación con Samsung, Wikimedia, los museos
ni Home Assistant. Las [licencias y notas técnicas](DOCS.md#licences)
siguen en inglés.
