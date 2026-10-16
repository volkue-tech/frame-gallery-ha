# Obra actual y modo opcional en segundo plano

[English](CURRENT_ARTWORK.md) | [Deutsch](CURRENT_ARTWORK.de.md) | [Français](CURRENT_ARTWORK.fr.md) | Español | [Italiano](CURRENT_ARTWORK.it.md)

**Candidato local b8; la versión pública b7 no cambia. Experimental y desactivado
por defecto.** Una conexión de lectura podría despertar un TV en espera. La
espera automática sin movimiento aún no está validada. Deje este modo desactivado
si despertar el TV resulta inaceptable. No necesita otro ayudante, clave API, HACS ni otra app.

Sin el modo en segundo plano, las tarjetas y el funcionamiento de una sola
ejecución no cambian. Para probarlo, active el modo y reinicie la
app. Iniciar/Detener controlan entonces el servicio, no el cambio de imagen.
El inicio automático es opcional y no envía una obra. Reinicie la app después
de modificar sus opciones.

Sustituya solo el contenido de `script.frame_gallery_new_artwork` por el
[script completo de envío](examples/background-send-script.yaml), manteniendo
su ID, la cámara y el temporizador. Las tarjetas que lo llaman siguen funcionando.
Sustituya las llamadas directas a `hassio.app_start` por este script. Adapte el
slug de la app y el ID del temporizador si difieren. Los valores técnicos siguen
en inglés. No sustituya la hora ni el ID de solicitud generados por constantes.

## Tarjeta opcional de información

Añada una tarjeta manual con este bloque completo. La tarjeta existente de
imagen/color/artista queda separada: su vista previa es la última imagen enviada,
no una captura en directo del televisor.

```yaml
type: markdown
title: Frame Gallery — Obra actual
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% if item is not defined or item is none %}
  No hay información actual disponible.
  {% elif item.state == 'artwork' and
      as_timestamp(now()) - as_timestamp(item.last_reported, 0) < 90 %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Última comprobación: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'validation_required' %}
  Consultas bloqueadas. Revise el registro y solicite explícitamente una obra.
  {% elif item.state == 'checking' %}
  Operación en curso. La imagen actual aún no está confirmada.
  {% elif item.state == 'unidentified' %}
  No se ha identificado la obra mostrada.
  {% else %}
  Obra actual no confirmada. El TV puede estar desconectado o las consultas pausadas.
  {% endif %}
```

Este estado de HA no es una integración de dispositivo registrada. Puede faltar
tras reiniciar HA o quedar obsoleto si la app falla. La tarjeta oculta los títulos
no confirmados y puede añadir aproximadamente un minuto de retraso. Las imágenes
antiguas sin una correspondencia verificada siguen desconocidas. No borre el
historial para identificarlas. No se utiliza reconocimiento de imágenes en la nube.

Tras cambiar el script, solicite **una obra nueva con el TV en modo Arte**. Solo
un envío correcto activa las consultas, aproximadamente cada 30 segundos.
Iniciar/reiniciar por sí solo no contacta al TV. La primera consulta fija su
identidad; otro dispositivo en la misma dirección se rechaza. Un error o el
modo Arte inactivo pausa las consultas sin reconectar. Para reanudar, ponga el
TV en modo Arte y solicite otra obra; actualizar no reactiva las consultas.
Para volver al modo de una ejecución, desactive el modo, reinicie y restaure el
script de envío original. No borre el historial ni las identidades para forzar la conexión.

Se verificó una lectura real con comparación de imagen y título/artista, no la
espera automática, todas las transiciones ni el crecimiento sostenido de
Recorder. El observador no envía órdenes de encendido, Wake-on-LAN ni cambios de
modo Arte; aun así, la propia conexión podría despertar el TV.
