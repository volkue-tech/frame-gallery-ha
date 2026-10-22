# Obra actual y modo opcional en segundo plano

Local, sin publicar: [vista previa opcional de la obra actual](CURRENT_PREVIEW.es.md). Las tarjetas existentes no cambian.

[English](CURRENT_ARTWORK.md) | [Deutsch](CURRENT_ARTWORK.de.md) | [Français](CURRENT_ARTWORK.fr.md) | Español | [Italiano](CURRENT_ARTWORK.it.md)

**Corregido en b16:** la actualización opcional acepta las respuestas reales
`artmode_status` / `current_artwork`, comprobando estrictamente el ID de solicitud.
Sin nuevas opciones, conexiones, formatos de asociación ni cambios de tarjeta.

**Beta pública b16: experimental y desactivado por defecto.** Las tarjetas b7/b8/b9/b10/b11/b12/b13 siguen funcionando. No necesita nuevos ayudantes, claves API, HACS, permisos especiales ni otra app en Home Assistant Green/OS.

[Informe b16](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA16_VALIDATION.md) · [Fuentes correspondientes](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b16).

Incluso una conexión de lectura puede despertar el TV. Las pruebas controladas cubren cambios automáticos y un episodio de reposo natural en un Frame, no todos los modelos o firmware. Mantenga el modo desactivado si ese riesgo es inaceptable.

## Memoria automática de obras

### Sincronización al iniciar y tras reposo — b12, opcional

Tras un envío Frame Gallery anterior correcto, active el **modo en segundo plano**
y escriba en **Sincronizar al iniciar / tras reposo** (`resume_state_entity`) la entidad Samsung
HA existente de este TV (`media_player` o `remote`). Busque su ID en Ajustes →
Dispositivos y servicios → Entidades. Reinicie la app. No necesita otro ayudante,
envío de imagen ni cambiar tarjetas.

El primer estado HA en caché de cada inicio configurado permite **una lectura
inicial si indica `on`**, aunque lleve horas sin cambiar. Se verifican identidad,
modo Arte, ID e imagen antes de mostrar artista/título; no se envía una imagen.
El primer resultado ausente, inválido, futuro, `off`, desconocido o fallido
consume la oportunidad inicial; los `on` posteriores no la repiten.

**Ventana de inicio — b13:** una ventana fija de diez segundos da
prioridad a una solicitud aceptada de nueva obra frente a la lectura inicial
automática. La aceptación cancela la oportunidad inicial pendiente antes del
envío, aunque este falle después o no encuentre ninguna obra (`no_match`). Solo
un envío válido y correcto puede entonces abrir su propia sesión de lectura.
Sin una solicitud aceptada, la sincronización inicial independiente sigue
disponible tras la ventana si el estado HA en caché sigue válido y `on`. Las
reglas posteriores de recuperación tras cambios reales `off`/`on` no cambian.

Esta ventana limitada no puede anticipar scripts con retrasos arbitrarios. Si
ya se ha iniciado un receptor independiente, un envío posterior debe detenerlo
primero y esperar a que termine. Las pruebas sin conexión de este arreglo no
aportan nuevas pruebas físicas contra despertares del TV o cambios de modo.

El monitor de reanudación lee ese estado HA en caché cada cinco segundos;
es independiente de las comprobaciones opcionales del socket Art descritas abajo.
Un `off` observado y un
`on` más reciente de como máximo 30 segundos permiten otra lectura. Ambas rutas
comparten seis intentos por hora móvil **en ese proceso**. Duplicados, cambios
antiguos y lagunas no autorizan reintentos. El rechazo de autenticación bloquea
lecturas automáticas del proceso. Reiniciar crea una oportunidad nueva, no un
límite persistente entre reinicios; no utilice bucles de reinicio.

HA `on` no demuestra modo Arte. La conexión podría despertar el TV o cambiar su
modo; esta ruta nueva solo tiene simulaciones, no validación física nueva.
Vacío: desactivado. Una app detenida no observa despertares. Los límites de
visualización de 90 segundos y 15 minutos no cambian.

Cada envío seleccionado correctamente guarda automáticamente el ID del TV, título, artista y fuente, incluso con el modo en segundo plano **desactivado**. No hay que introducir ID. La asociación pertenece a la identidad real del TV, no solo a su IP. El mismo ID en otro TV no es la misma obra. Un nuevo envío correcto sustituye la asociación anterior de ese TV/ID.

Los datos privados sobreviven a las actualizaciones normales. Reiniciar el historial de selección no borra asociaciones; desinstalar eliminando los datos sí. Conserve una copia antes de reinstalar. Límite: las últimas 2.048 asociaciones y 32 MiB, más una copia. La referencia es una muestra RGB de 64×36 píxeles, no un archivo de alta resolución. Las asociaciones antiguas verificadas por imagen siguen siendo compatibles.

Imágenes antiguas, envíos de otras apps y envíos sin identidad estable quedan sin identificar. No se adivinan artistas ni se usa reconocimiento en la nube.

### Actualización opcional del estado actual — b16

`current_state_refresh` es un interruptor adicional, **desactivado por defecto**,
que requiere `background_mode`. Permite como máximo una comprobación de lectura
de la coherencia del modo Arte actual y del ID de imagen cada 60 segundos, por
el **socket Art ya conectado**. Su objetivo es recuperar artista/título conocidos
tras usar el menú del TV o reanudar el pase, incluso si la imagen sigue siendo
la misma. No abre otra conexión ni envía órdenes de imagen, encendido o modo.
Una imagen desconocida queda sin identificar; no se inventa un título ni se toma
el de la imagen anterior.

Una prueba nueva y correcta `current_state_read` es válida durante 90 segundos.
Los ID duplicados, pongs o avisos de modo activo por sí solos no la renuevan.

Con esta opción, `off` o `nav` del canal Art conserva **el mismo socket**; estos
estados no son reposo físico. Fuera del modo Arte se ocultan título y artista.
Las comprobaciones continúan aunque falte la notificación de regreso: dentro
del mismo límite de una vez por minuto, solo se lee el modo mientras no esté
activo. Los ID de imagen se solicitan únicamente tras una respuesta `on` recién
leída; un ciclo de menú no confirma ninguna obra. Si la sesión recibe primero
`off` o `nav`, la prueba inicial única con miniatura espera al modo Arte `on` en
ese socket; no se repite. El reposo, un estado HA «off» observado o una conexión
cerrada sigue terminando la sesión, sin otro socket ni reconexión a ciegas.

Incluso por el mismo socket, las consultas pueden afectar al reposo automático.
Deje la opción desactivada si ese riesgo es inaceptable. Las pruebas sin conexión
no garantizan compatibilidad con el firmware ni que el TV no se despierte.
No hay que cambiar las tarjetas ni los scripts existentes.

## Activar la tarjeta opcional

1. Conserve cámara, temporizador, tarjetas y el ID `script.frame_gallery_new_artwork`.
2. Active **Modo en segundo plano** y reinicie la app. Iniciar/Detener controla el servicio, no la imagen. Sin la entidad opcional anterior no se contacta al TV al iniciar; con ella el primer HA `on` puede permitir la lectura tras la ventana de diez segundos, salvo que una solicitud de envío aceptada la sustituya.
3. Sustituya solo el contenido del script por el [script de envío completo](examples/background-send-script.yaml). Ajuste el slug y temporizador si difieren. Las tarjetas siguen funcionando; sustituya llamadas directas a `hassio.app_start` por el script.
4. Tras un envío anterior correcto, configure la entidad anterior para leer la obra ya visible sin otro envío. En una instalación sin asociación TV guardada, solicite la primera obra con modo Arte visible; un envío correcto permite una sesión experimental. Actualizar por sí solo no abre una conexión.
5. Añada una tarjeta manual con el YAML **completo** siguiente.

La tarjeta de imagen/color/artista muestra la **última vista previa enviada**, no una captura en directo. Esta tarjeta nativa adicional muestra la información actual por separado.

```yaml
type: markdown
title: Frame Gallery — Obra actual
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% if item is not defined or item is none %}
  No hay información actual disponible.
  {% elif item.state == 'artwork' and
      as_timestamp(now()) - as_timestamp(item.last_reported, 0) <
      (900 if item.attributes.get('confirmation_method') == 'slideshow_events' else 90) %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Última confirmación: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'validation_required' %}
  Esperando una comprobación autorizada. Revise ajustes de segundo plano/entidad y registro; la lectura inicial configurada no necesita otra imagen.
  {% elif item.state == 'checking' %}
  Imagen actual no confirmada. Esperando una prueba válida de imagen o pase.
  {% elif item.state == 'unidentified' %}
  La obra mostrada no tiene una asociación guardada.
  {% else %}
  Obra actual no confirmada. TV no disponible o sesión pausada.
  {% endif %}
```

## Confirmación y límites

**Recuperación histórica b10 — solo eventos (`current_state_refresh` desactivado):** una secuencia incompleta
de notificaciones reconocidas del pase oculta los datos actuales y espera una
nueva secuencia completa en la misma conexión. No confirma ninguna obra ni
envía otra consulta. Los mensajes desconocidos o incorrectos, el reposo, el modo
TV y la pérdida de conexión siguen terminando la sesión. Los códigos fijos del
registro distinguen errores de inicio, recepción, decodificación y proceso
aislado, sin mensajes sin procesar ni credenciales. El inicio b12 y la ventana b13 no tienen nueva
validación física de TV o reposo.

Con `current_state_refresh` activado, las notificaciones estructuralmente válidas
pero no reconocidas y `off`/`nav` del canal Art ocultan los datos y conservan el
mismo socket según las reglas limitadas anteriores. No confirman ninguna obra
ni permiten otra conexión. El reposo físico, el rechazo de autenticación, los
datos de protocolo mal formados y un transporte cerrado siguen terminando la sesión.

En el registro, `event sequence incomplete` significa que los datos se han
ocultado y la misma conexión espera, sin confirmar ninguna obra.
`event session stopped: reason=...; no reconnect` indica que la sesión terminó,
sin repetición inmediata. Al informar de un problema, incluya ese código fijo,
la versión y el modelo del TV, nunca tokens ni datos sin procesar del televisor.

Cada sesión dura como máximo ocho horas. En el modo de solo eventos
(`current_state_refresh` desactivado), el reposo, el modo TV o los errores pueden
terminarla antes. Siguen aplicándose las excepciones opcionales y paradas definitivas anteriores. Un nuevo proceso configurado o un cambio HA reciente anterior permite otra lectura; un envío explícito correcto también puede abrir una sesión.

Tras una lectura inicial y comparación local, una conexión escucha la secuencia observada: `image_selected`, `auto_rotation_image_changed` con el mismo ID y modo Arte `on`, en cinco segundos. Con `current_state_refresh` desactivado, no hay consultas repetidas, miniaturas posteriores ni reconexión dentro de esa sesión. Activarlo solo permite las comprobaciones limitadas anteriores, no nuevas miniaturas ni conexiones. Un evento busca la asociación de envío o imagen verificada de ese TV; un ID desconocido borra el texto.

La prueba inicial dura 90 segundos. Una secuencia completa dura como máximo **15 minutos**, para el ciclo probado de diez minutos. Duplicados, pongs y modo activo no renuevan nada. Ciclos más largos pueden dejar huecos; los cambios manuales no siempre generan esta secuencia. La plantilla puede añadir aproximadamente un minuto de retraso.

Con la actualización desactivada o sin una nueva comprobación correcta, una
imagen fija sin cambios puede quedar sin confirmar tras 90 segundos. El arreglo
de inicio por sí solo no prolonga la prueba ni consulta repetidamente el TV para mantener una
leyenda artificialmente actualizada.

**Solo eventos (`current_state_refresh` desactivado):** Reposo, modo TV, desconexión, eventos inválidos o fallo de publicación pausan/detienen sin reconectar de inmediato. Si se activa la opción, se aplican las reglas limitadas del mismo socket y las paradas definitivas anteriores. Una vez terminada realmente la sesión, sin la opción anterior de reanudación sigue siendo necesario otro envío explícito en modo Arte visible. La acción manual Actualizar solo procesa eventos ya recibidos. El observador no envía órdenes de encendido, Wake-on-LAN, selección de imagen ni cambios de modo; la propia conexión aún puede tener efectos secundarios.

Los ID guardados son correspondencias históricas, no comprobación continua de píxeles. No se puede descartar una reutilización externa no observada de un ID. Una comparación inicial contradictoria bloquea la leyenda guardada. Sin garantía general de firmware ni de no despertar el TV (D-235).

El sensor es un estado publicado por la app, no una integración registrada. Puede faltar tras reiniciar Core. Los datos caducados/pausados ocultan el título. Para volver al modo de una ejecución, desactive el modo, reinicie y restaure el script original. No borre historial ni identidades para forzar una conexión.
