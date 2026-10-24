# Frame Gallery — Œuvre actuelle

**0.1.0b19 — confirmation facultative des œuvres inchangées (D-247/D-250/D-252).** NOUVEAU : `confirm_current_artwork`, expérimental et désactivé par défaut ; exige le mode arrière-plan et l'entité Samsung existante `resume_state_entity`. Seule une session Art vérifiée et autorisée séparément peut confirmer mode/ID sur la MÊME connexion, au maximum quatre GET par minute. Aucune nouvelle connexion, autorisation de démarrage/reprise, commande image/alimentation/mode ni répétition aveugle. Les lectures valides conservent les données artiste/titre/aperçu encore fraîches. Arrêt/menu/veille, données HA/preuves/horloge périmées ou échec ferment la session. Limite de huit heures maintenue ; après déconnexion, une nouvelle autorisation indépendante est nécessaire. Ancien `current_state_refresh` et lecture initiale restent suspendus. `standby_resume` b18 reste séparé/désactivé : observer 30 s d'arrêt puis 10 s d'allumage récent stable, six tentatives/heure maximum espacées de 60 s. Même les lectures peuvent affecter le micrologiciel ou la veille ; aucune garantie de non-réveil. Cartes/scripts/données/droits compatibles. [Preuves et limites b19](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA19_VALIDATION.md).

[English](CURRENT_STATUS.md) | [Deutsch](CURRENT_STATUS.de.md) | Français | [Español](CURRENT_STATUS.es.md) | [Italiano](CURRENT_STATUS.it.md)

```yaml
type: markdown
title: Frame Gallery — Œuvre actuelle
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% set camera_entity = 'camera.frame_gallery_current' %}
  {% set messages = {
      'safety_hold': "Reprise automatique non autorisée. Les anciens réglages ne l'activent pas.",
      'configuration_required': "Entité d'état Samsung absente; reprise automatique désactivée.",
      'waiting_for_standby': "En attente d'un cycle veille/réveil entièrement observé; aucune lecture au démarrage.",
      'standby': "HA indique TV arrêtée. Lecture en pause; aucune commande d'alimentation envoyée.",
      'wake_settling': "Réveil détecté; attente d'un état HA stable avant toute lecture.",
      'wake_revalidation': "Vérification unique autorisée après réveil en cours.",
      'ha_state_unavailable': "État HA absent, invalide ou interrompu. Nouveau cycle complet nécessaire.",
      'rate_limited': "Limite de tentatives atteinte. Pas de répétition différée; nouveau cycle nécessaire.",
      'budget_unavailable': "Reprise bloquée: budget enregistré illisible ou non inscriptible en sécurité.",
      'tv_authorization': "Autorisation TV refusée. Aucune répétition automatique; vérifier l'accès TV.",
      'association_required': "Validation locale du TV ou de l'association impossible. Aucune connexion de reprise démarrée.",
      'connection_failed': "Session de lecture échouée ou déconnectée. Pas de répétition aveugle.",
      'session_failed': "Session de lecture rejetée ou incorrecte. Métadonnées actuelles masquées.",
      'service_stopped': "Frame Gallery a été arrêtée; aucune confirmation TV actuelle.",
      'proof_expired': "Preuve d'image expirée. En attente d'une nouvelle preuve valide.",
      'waiting_for_event': "Image actuelle non confirmée. Attente d'événements passifs complets du diaporama ; aucune requête TV en cours."
  } %}
  {% if item is not defined or item is none %}
  Aucune information actuelle disponible.
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

  Dernière confirmation: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'artwork' %}
  La dernière confirmation a expiré. Aucun artiste actuel affiché.
  {% elif reason in messages %}
  {{ messages[reason] }}
  {% elif item.state == 'checking' %}
  Vérification du mode Art et de l'image; pas encore confirmée.
  {% elif item.state == 'unidentified' %}
  Aucune association enregistrée pour l'œuvre observée.
  {% elif item.state == 'tv_in_use' %}
  Mode Art non confirmé: programme TV ou menu des œuvres.
  {% elif item.state == 'not_authorized' %}
  {{ messages['tv_authorization'] }}
  {% elif item.state == 'unavailable' %}
  Session de lecture indisponible ou terminée; cause non confirmée.
  {% elif item.state == 'validation_required' %}
  Aucune preuve TV actuelle. Les associations enregistrées ne sont pas une confirmation en direct.
  {% else %}
  Synchronisation en pause; cette version n'indique pas la cause précise. Cela ne prouve pas une panne réseau TV.
  {% endif %}
  {% endif %}
```
