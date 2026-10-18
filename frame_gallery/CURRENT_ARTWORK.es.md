# Obra actual y modo opcional en segundo plano

[English](CURRENT_ARTWORK.md) | [Deutsch](CURRENT_ARTWORK.de.md) | [Français](CURRENT_ARTWORK.fr.md) | Español | [Italiano](CURRENT_ARTWORK.it.md)

**Beta b11: experimental y desactivado por defecto.** Las tarjetas b7/b8/b9/b10 siguen funcionando. No necesita nuevos ayudantes, claves API, HACS, permisos especiales ni otra app en Home Assistant Green/OS.

Incluso una conexión de lectura puede despertar el TV. Las pruebas controladas cubren cambios automáticos y un episodio de reposo natural en un Frame, no todos los modelos o firmware. Mantenga el modo desactivado si ese riesgo es inaceptable.

## Memoria automática de obras

### Reanudar tras el reposo — nuevo en b11, opcional

Tras un envío Frame Gallery anterior correcto, active el **modo en segundo plano**
y escriba en **Reanudar tras el reposo** (`resume_state_entity`) la entidad Samsung
HA existente de este TV (`media_player` o `remote`). Busque su ID en Ajustes →
Dispositivos y servicios → Entidades. Reinicie la app. No necesita otro ayudante,
envío de imagen ni cambiar tarjetas.

Solo se lee ese estado HA en caché cada cinco segundos. Un `off` observado y un
`on` posterior de como máximo 30 segundos permiten un intento de lectura, como
máximo seis por hora. Se verifican identidad del TV, modo Arte e imagen actual.
Inicio con TV ya encendido, reinicio, duplicados, estados antiguos/desconocidos
o lagunas no autorizan lecturas. Los fallos no se repiten: se necesita otro ciclo
apagado-encendido. El rechazo de autenticación bloquea intentos automáticos en
ese proceso.

HA `on` no demuestra modo Arte. La conexión podría despertar el TV o cambiar su
modo; esta ruta nueva solo tiene simulaciones, no validación física nueva.
Vacío: desactivado. Una app detenida no observa despertares. Los límites de
visualización de 90 segundos y 15 minutos no cambian.

Cada envío seleccionado correctamente guarda automáticamente el ID del TV, título, artista y fuente, incluso con el modo en segundo plano **desactivado**. No hay que introducir ID. La asociación pertenece a la identidad real del TV, no solo a su IP. El mismo ID en otro TV no es la misma obra. Un nuevo envío correcto sustituye la asociación anterior de ese TV/ID.

Los datos privados sobreviven a las actualizaciones normales. Reiniciar el historial de selección no borra asociaciones; desinstalar eliminando los datos sí. Conserve una copia antes de reinstalar. Límite: las últimas 2.048 asociaciones y 32 MiB, más una copia. La referencia es una muestra RGB de 64×36 píxeles, no un archivo de alta resolución. Las asociaciones antiguas verificadas por imagen siguen siendo compatibles.

Imágenes antiguas, envíos de otras apps y envíos sin identidad estable quedan sin identificar. No se adivinan artistas ni se usa reconocimiento en la nube.

## Activar la tarjeta opcional

1. Conserve cámara, temporizador, tarjetas y el ID `script.frame_gallery_new_artwork`.
2. Active **Modo en segundo plano** y reinicie la app. Iniciar/Detener controla el servicio, no cambia la imagen. El inicio automático no contacta al TV.
3. Sustituya solo el contenido del script por el [script de envío completo](examples/background-send-script.yaml). Ajuste el slug y temporizador si difieren. Las tarjetas siguen funcionando; sustituya llamadas directas a `hassio.app_start` por el script.
4. Con una obra visible en modo Arte, solicite explícitamente una nueva obra. Un envío reciente correcto con asociación guardada autoriza una sola sesión experimental. Iniciar/reiniciar/actualizar no la activa.
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
  Consultas bloqueadas. Revise el registro y solicite explícitamente una obra.
  {% elif item.state == 'checking' %}
  Operación en curso. La imagen actual aún no está confirmada.
  {% elif item.state == 'unidentified' %}
  La obra mostrada no tiene una asociación guardada.
  {% else %}
  Obra actual no confirmada. TV no disponible o sesión pausada.
  {% endif %}
```

## Confirmación y límites

**Corrección de recuperación beta b10:** una secuencia incompleta
de notificaciones reconocidas del pase oculta los datos actuales y espera una
nueva secuencia completa en la misma conexión. No confirma ninguna obra ni
envía otra consulta. Los mensajes desconocidos o incorrectos, el reposo, el modo
TV y la pérdida de conexión siguen terminando la sesión. Los códigos fijos del
registro distinguen errores de inicio, recepción, decodificación y proceso
aislado, sin mensajes sin procesar ni credenciales. La nueva reanudación b11 no se ha
instalado ni probado en el televisor.

En el registro, `event sequence incomplete` significa que los datos se han
ocultado y la misma conexión espera, sin confirmar ninguna obra.
`event session stopped: reason=...; no reconnect` indica que la sesión terminó,
sin repetición inmediata. Al informar de un problema, incluya ese código fijo,
la versión y el modelo del TV, nunca tokens ni datos sin procesar del televisor.

Cada sesión dura como máximo ocho horas y termina antes con reposo, modo TV o
errores. Solo la transición HA reciente configurada arriba permite abrir otra sesión.

Tras una lectura inicial y comparación local, una conexión escucha la secuencia observada: `image_selected`, `auto_rotation_image_changed` con el mismo ID y modo Arte `on`, en cinco segundos. Dentro de esa sesión no hay consultas repetidas, miniaturas posteriores ni reconexión. Un evento busca la asociación de envío o imagen verificada de ese TV; un ID desconocido borra el texto.

La prueba inicial dura 90 segundos. Una secuencia completa dura como máximo **15 minutos**, para el ciclo probado de diez minutos. Duplicados, pongs y modo activo no renuevan nada. Ciclos más largos pueden dejar huecos; los cambios manuales no siempre generan esta secuencia. La plantilla puede añadir aproximadamente un minuto de retraso.

Reposo, modo TV, desconexión, eventos inválidos o fallo de publicación pausan/detienen sin reconectar de inmediato. Sin la opción anterior de reanudación, sigue siendo necesario otro envío explícito en modo Arte visible. Actualizar solo procesa eventos ya recibidos. El observador no envía órdenes de encendido, Wake-on-LAN, selección de imagen ni cambios de modo; la propia conexión aún puede tener efectos secundarios.

Los ID guardados son correspondencias históricas, no comprobación continua de píxeles. No se puede descartar una reutilización externa no observada de un ID. Una comparación inicial contradictoria bloquea la leyenda guardada. Sin garantía general de firmware ni de no despertar el TV (D-235).

El sensor es un estado publicado por la app, no una integración registrada. Puede faltar tras reiniciar Core. Los datos caducados/pausados ocultan el título. Para volver al modo de una ejecución, desactive el modo, reinicie y restaure el script original. No borre historial ni identidades para forzar una conexión.
