# Frame Gallery — Obra actual

Candidato local sin publicar. Se conservan tarjetas y scripts existentes. Tarjeta nativa completa con estados diferenciados. standby_resume es un NUEVO permiso desactivado por defecto: requiere segundo plano y entidad Samsung existente,30s de apagado observado y encendido reciente estable10s. Una lectura por transición,máx6/h,mín60s incluso tras reinicios. Sin consultas iniciales/periódicas, órdenes de imagen/encendido/modo ni reintentos ciegos. La conexión puede afectar al TV; las pruebas sin conexión no garantizan que no despierte. La app debe ejecutarse durante toda la transición; detenida no puede recuperar. Tras desconexión sin nuevo apagado hay que esperar otro ciclo completo. Las guías b17 siguen describiendo la versión publicada hasta una publicación autorizada aparte.

[English](CURRENT_STATUS.md) | [Deutsch](CURRENT_STATUS.de.md) | [Français](CURRENT_STATUS.fr.md) | Español | [Italiano](CURRENT_STATUS.it.md)

```yaml
type: markdown
title: Frame Gallery — Obra actual
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% set camera_entity = 'camera.frame_gallery_current' %}
  {% set messages = {
      'safety_hold': "Recuperación automática no autorizada. Los ajustes antiguos no la activan.",
      'configuration_required': "Falta la entidad de estado Samsung; recuperación automática desactivada.",
      'waiting_for_standby': "Esperando un ciclo de espera/despertar completo; el inicio no consulta al TV.",
      'standby': "HA indica TV apagado. Lectura en pausa; no se envía orden de encendido.",
      'wake_settling': "Despertar detectado; esperando estado HA estable antes de leer.",
      'wake_revalidation': "Comprobación única autorizada tras despertar en curso.",
      'ha_state_unavailable': "Estado HA ausente, inválido o interrumpido. Hace falta un ciclo nuevo completo.",
      'rate_limited': "Límite de intentos alcanzado. Sin reintento diferido; hace falta un ciclo nuevo.",
      'budget_unavailable': "Recuperación bloqueada: presupuesto guardado no se puede leer/escribir con seguridad.",
      'tv_authorization': "Autorización TV rechazada. Sin reintentos automáticos; revise el acceso al TV.",
      'association_required': "Falló la validación local del TV o la asociación. No se inició conexión de recuperación.",
      'connection_failed': "Sesión de lectura fallida o desconectada. Sin reintentos ciegos.",
      'session_failed': "Sesión rechazada o incorrecta. Metadatos actuales ocultos.",
      'service_stopped': "Frame Gallery se detuvo; sin confirmación TV actual.",
      'proof_expired': "La prueba de imagen caducó. Esperando una prueba nueva válida.",
      'waiting_for_event': "Imagen actual sin confirmar. Esperando eventos pasivos completos de la presentación; no hay consulta al TV."
  } %}
  {% if item is not defined or item is none %}
  No hay información actual disponible.
  {% else %}
  {% set age = as_timestamp(now()) - as_timestamp(item.last_reported, 0) %}
  {% set reason = item.attributes.get('status_reason', '') %}
  {% if item.state == 'artwork' and age >= 0 and age <
      (900 if item.attributes.get('confirmation_method') == 'slideshow_events' else 90) %}
  {% set picture = state_attr(camera_entity, 'entity_picture') %}
  {% if item.attributes.get('preview_available', false) and
      states(camera_entity) not in ['unknown', 'unavailable'] and
      state_attr(camera_entity, 'file_path') == '/media/frame_gallery/preview/current.jpg' and
      picture is string and picture %}
  <img src="{{ picture | e }}{{ '&' if '?' in picture else '?' }}fg={{ item.attributes.get('preview_sha256', '') | e }}" style="max-width:100%;border-radius:12px" />

  {% endif %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Última confirmación: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'artwork' %}
  La última confirmación ha caducado. No se muestra un artista actual.
  {% elif reason in messages %}
  {{ messages[reason] }}
  {% elif item.state == 'checking' %}
  Comprobando modo Arte e imagen; aún sin confirmar.
  {% elif item.state == 'unidentified' %}
  No hay asociación guardada para la obra observada.
  {% elif item.state == 'tv_in_use' %}
  Modo Arte no confirmado: programa TV o menú de obras.
  {% elif item.state == 'not_authorized' %}
  {{ messages['tv_authorization'] }}
  {% elif item.state == 'unavailable' %}
  Sesión de lectura no disponible o finalizada; causa sin confirmar.
  {% elif item.state == 'validation_required' %}
  Sin prueba actual del TV. Las asociaciones guardadas no son confirmación en directo.
  {% else %}
  Sincronización en pausa; esta versión no indica la causa exacta. Esto no demuestra un fallo de red del TV.
  {% endif %}
  {% endif %}
```
