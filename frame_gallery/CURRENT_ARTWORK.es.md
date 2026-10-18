# Obra actual y modo opcional en segundo plano

[English](CURRENT_ARTWORK.md) | [Deutsch](CURRENT_ARTWORK.de.md) | [Français](CURRENT_ARTWORK.fr.md) | Español | [Italiano](CURRENT_ARTWORK.it.md)

**Beta b9: experimental y desactivado por defecto.** Las tarjetas b7/b8 siguen funcionando. No necesita ayudantes, claves API, HACS, permisos especiales ni otra app en Home Assistant Green/OS.

Incluso una conexión de lectura puede despertar el TV. Las pruebas controladas cubren cambios automáticos y un episodio de reposo natural en un Frame, no todos los modelos o firmware. Mantenga el modo desactivado si ese riesgo es inaceptable.

## Memoria automática de obras

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

Cada sesión dura como máximo ocho horas y termina antes con reposo, modo TV o
errores. No se reanuda automáticamente cuando el televisor vuelve a despertar.

Tras una lectura inicial y comparación local, una conexión escucha la secuencia observada: `image_selected`, `auto_rotation_image_changed` con el mismo ID y modo Arte `on`, en cinco segundos. No hay consultas repetidas cada 30 segundos, miniaturas posteriores ni reconexión automática. Un evento busca la asociación de envío o imagen verificada de ese TV; un ID desconocido borra el texto.

La prueba inicial dura 90 segundos. Una secuencia completa dura como máximo **15 minutos**, para el ciclo probado de diez minutos. Duplicados, pongs y modo activo no renuevan nada. Ciclos más largos pueden dejar huecos; los cambios manuales no siempre generan esta secuencia. La plantilla puede añadir aproximadamente un minuto de retraso.

Reposo, modo TV, desconexión, eventos inválidos o fallo de publicación pausan/detienen sin reconectar. Para reanudar, ponga el TV en modo Arte y envíe explícitamente otra obra. Actualizar solo procesa eventos ya recibidos. El observador no envía órdenes de encendido, Wake-on-LAN, selección de imagen ni cambios de modo; la propia conexión aún puede tener efectos secundarios.

Los ID guardados son correspondencias históricas, no comprobación continua de píxeles. No se puede descartar una reutilización externa no observada de un ID. Una comparación inicial contradictoria bloquea la leyenda guardada. Sin garantía general de firmware ni de no despertar el TV (D-235).

El sensor es un estado publicado por la app, no una integración registrada. Puede faltar tras reiniciar Core. Los datos caducados/pausados ocultan el título. Para volver al modo de una ejecución, desactive el modo, reinicie y restaure el script original. No borre historial ni identidades para forzar una conexión.
