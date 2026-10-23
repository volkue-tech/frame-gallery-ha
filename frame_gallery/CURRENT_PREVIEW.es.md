# Vista previa de la obra actual

[English](CURRENT_PREVIEW.md) | [Deutsch](CURRENT_PREVIEW.de.md) | [Français](CURRENT_PREVIEW.fr.md) | **Español** | [Italiano](CURRENT_PREVIEW.it.md)

**Beta pública 0.1.0b17 — vista previa actual separada y opcional.**

**Restricción de seguridad (D-247):** el modo en segundo plano sigue siendo
experimental y desactivado por defecto. Se suspenden las conexiones automáticas
al iniciar/despertar y las consultas por minuto, incluso con opciones guardadas.
Solo un nuevo envío explícito correcto puede iniciar la observación pasiva del
pase. Una imagen sin cambios caduca; no hay recuperación automática tras menú/
modo TV, reposo o pérdida de conexión. La conexión aún puede afectar al TV: no es
garantía de que no despierte. Lea primero la [configuración y límites](CURRENT_ARTWORK.es.md).

La tarjeta de imagen existente sigue mostrando la última obra enviada. Esta tarjeta opcional muestra una vista previa guardada solo cuando el título y artista actuales están confirmados recientemente. No es una captura en directo.

1. Conservar la configuración actual, las tarjetas y los scripts. Sin nuevas opciones de la app, permisos especiales, HACS ni cambios en configuration.yaml.
2. Tras un envío correcto con esta versión se guarda automáticamente un JPEG pequeño, también en modo de una sola ejecución. La visualización actual requiere el observador opcional existente. Las imágenes antiguas del TV no se recuperan automáticamente; no se añaden consultas al TV.
3. Después de inicializar el servicio en segundo plano, añadir Local File en Ajustes → Dispositivos y servicios. Nombre: `Frame Gallery Current Preview`; ruta: `/media/frame_gallery/preview/current.jpg`. No sustituir la cámara Local File anterior.
4. Comprobar el ID real de la nueva cámara. El ejemplo usa `camera.frame_gallery_current_preview`; cambiar solo `camera_entity` si HA eligió otro ID. Añadir la tarjeta manual completa de abajo.

```yaml
type: markdown
title: Frame Gallery — Obra actual
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% set camera_entity = 'camera.frame_gallery_current_preview' %}
  {% if item is defined and item is not none %}
    {% set age = as_timestamp(now()) - as_timestamp(item.last_reported, 0) %}
  {% else %}
    {% set age = -1 %}
  {% endif %}
  {% if item is defined and item is not none and item.state == 'artwork'
      and age >= 0 and age <
      (900 if item.attributes.get('confirmation_method') == 'slideshow_events' else 90) %}
    {% set picture = state_attr(camera_entity, 'entity_picture') %}
    {% if item.attributes.get('preview_available', false)
        and picture is string and picture
        and state_attr(camera_entity, 'file_path') == '/media/frame_gallery/preview/current.jpg'
        and states(camera_entity) not in ['unknown', 'unavailable'] %}
      {% set separator = '&' if '?' in picture else '?' %}
  <img src="{{ (picture ~ separator ~ 'fg=' ~ item.attributes.get('preview_sha256', '')) | e }}" alt="Obra actual">

    {% else %}
  No hay vista previa guardada de esta obra; los datos del artista siguen disponibles.

    {% endif %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Última confirmación: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% else %}
  No hay una obra confirmada recientemente.
  {% endif %}
```

Vistas previas de hasta 640×360 píxeles y 32 KiB de JPEG. Caché privada limitada a 128 MiB, incluida la sobrecarga, y 4.096 entradas; la expulsión no borra asociaciones ni historial. No se inventan vistas previas para imágenes desconocidas, antiguas, rechazadas o expulsadas. La falta de espacio o fallos de caché no deben bloquear los metadatos.

Usar la tarjeta completa con control de antigüedad, no una cámara sin protección: tras un cierre inesperado el archivo puede conservar su contenido, pero la tarjeta oculta las pruebas caducadas. La disponibilidad se desactiva en HA antes de cambiar el archivo y solo se activa después de una escritura atómica verificada. La huella evita la caché del navegador; no es una nueva observación del TV. latest.jpg y las tarjetas existentes no cambian. Sin descarga adicional de miniaturas del TV, reconocimiento en la nube ni nuevas conexiones.

[Guía de la obra actual](CURRENT_ARTWORK.es.md)

Candidato local sin publicar: [recuperación limitada tras espera y tarjeta de estado completa](CURRENT_STATUS.es.md). YAML existente conservado; sin cambios instalados ni publicación.
