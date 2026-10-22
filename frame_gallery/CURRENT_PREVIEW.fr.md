# Aperçu de l’œuvre actuelle

[English](CURRENT_PREVIEW.md) | [Deutsch](CURRENT_PREVIEW.de.md) | **Français** | [Español](CURRENT_PREVIEW.es.md) | [Italiano](CURRENT_PREVIEW.it.md)

**Bêta publique 0.1.0b17 — aperçu actuel séparé et facultatif.**

**Restriction de sécurité (D-247) :** le mode arrière-plan reste expérimental et
désactivé par défaut. Connexions automatiques au démarrage/réveil et lectures par
minute suspendues, même avec les options enregistrées. Seul un nouvel envoi
explicite réussi peut démarrer l'observation passive du diaporama. Une image
inchangée expire ; aucune reprise automatique après menu/mode TV, veille ou perte
de connexion. La connexion peut encore affecter le TV : aucune garantie de
non-réveil. Lire d'abord la [configuration et les limites](CURRENT_ARTWORK.fr.md).

La carte d’image existante reste celle de la dernière œuvre envoyée. Cette carte facultative affiche un aperçu enregistré uniquement lorsque le titre et l’artiste actuels sont confirmés récemment. Ce n’est pas une capture en direct.

1. Conserver la configuration actuelle, les cartes et les scripts. Aucune nouvelle option d’app, permission spéciale, extension HACS ou modification de configuration.yaml.
2. Après un envoi réussi avec cette version, un petit JPEG est enregistré automatiquement, même en mode ponctuel. L’affichage actuel nécessite l’observateur facultatif existant. Les anciennes images du TV ne sont pas récupérées automatiquement ; aucune requête TV supplémentaire.
3. Après l’initialisation du service en arrière-plan, ajouter l’intégration Local File dans Paramètres → Appareils et services. Nom : `Frame Gallery Current Preview` ; chemin : `/media/frame_gallery/preview/current.jpg`. Ne pas remplacer l’ancienne caméra Local File.
4. Vérifier l’ID réel de la nouvelle caméra. L’exemple utilise `camera.frame_gallery_current_preview` ; adapter uniquement `camera_entity` si nécessaire. Ajouter la carte manuelle complète ci-dessous.

```yaml
type: markdown
title: Frame Gallery — Œuvre actuelle
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
  <img src="{{ (picture ~ separator ~ 'fg=' ~ item.attributes.get('preview_sha256', '')) | e }}" alt="Œuvre actuelle">

    {% else %}
  Aucun aperçu enregistré pour cette œuvre ; les données de l’artiste restent disponibles.

    {% endif %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Dernière confirmation: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% else %}
  Aucune œuvre confirmée récemment.
  {% endif %}
```

Les aperçus sont limités à 640×360 pixels et 32 KiB de JPEG. Le cache privé est limité à 128 MiB, surcharge comprise, et 4 096 entrées ; l’éviction ne supprime ni associations ni historique. Pas d’aperçu inventé pour une image inconnue, ancienne, rejetée ou évincée. Le manque d’espace ou une erreur du cache ne doit pas bloquer les métadonnées.

Utiliser la carte complète avec contrôle de fraîcheur, pas une caméra seule : après un arrêt brutal, le fichier peut conserver sa dernière image, mais la carte masque les preuves périmées. La disponibilité est désactivée dans HA avant le changement de fichier et réactivée après une écriture atomique vérifiée. L’empreinte évite le cache du navigateur ; ce n’est pas une nouvelle observation TV. latest.jpg et les cartes existantes restent inchangés. Aucun téléchargement d’aperçu TV, reconnaissance cloud ou nouvelle connexion.

[Guide de l’œuvre actuelle](CURRENT_ARTWORK.fr.md)
