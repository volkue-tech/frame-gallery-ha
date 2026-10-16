# Œuvre actuelle et mode arrière-plan facultatif

[English](CURRENT_ARTWORK.md) | [Deutsch](CURRENT_ARTWORK.de.md) | Français | [Español](CURRENT_ARTWORK.es.md) | [Italiano](CURRENT_ARTWORK.it.md)

**Bêta publique b8. Les cartes b7 existantes restent compatibles lorsque ce
mode est désactivé. Expérimental et désactivé par défaut.**
Une connexion en lecture peut réveiller un TV en veille.
La veille automatique sans mouvement n'est pas encore validée. Laissez ce mode
désactivé si un réveil est inacceptable. Aucun assistant supplémentaire, clé API, HACS ou autre app.

Sans le mode arrière-plan, les cartes et le fonctionnement ponctuel restent
inchangés. Pour essayer ce mode, activez-le et redémarrez l'app. Démarrer
et Arrêter contrôlent alors le service, pas un changement d'image. Le démarrage
automatique est facultatif ; il n'envoie aucune œuvre. Après une modification
des options de l'app, redémarrez-la.

Remplacez seulement le contenu de `script.frame_gallery_new_artwork` par le
[script d'envoi complet](examples/background-send-script.yaml), en conservant
son ID, la caméra et le minuteur. Les cartes qui l'appellent restent utilisables.
Remplacez les appels directs à `hassio.app_start` par ce script. Adaptez le slug
de l'app et l'ID du minuteur si nécessaire. Les valeurs techniques restent en
anglais. Ne remplacez pas l'ID de requête et l'heure générés par des constantes.

## Carte d'information facultative

Ajoutez une carte manuelle avec ce bloc complet. La carte image/couleur/artiste
existante reste indépendante ; son aperçu est la dernière image envoyée, pas
une capture en direct du téléviseur.

```yaml
type: markdown
title: Frame Gallery — Œuvre actuelle
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% if item is not defined or item is none %}
  Aucune information actuelle disponible.
  {% elif item.state == 'artwork' and
      as_timestamp(now()) - as_timestamp(item.last_reported, 0) < 90 %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Dernière vérification : {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'validation_required' %}
  Vérifications bloquées. Consultez le journal et demandez explicitement une œuvre.
  {% elif item.state == 'checking' %}
  Opération en cours. L'image actuelle n'est pas encore confirmée.
  {% elif item.state == 'unidentified' %}
  L'œuvre affichée n'a pas été identifiée.
  {% else %}
  Œuvre actuelle non confirmée. Téléviseur indisponible ou vérifications en pause.
  {% endif %}
```

Cet état HA n'est pas une intégration d'appareil enregistrée. Il peut manquer
après un redémarrage de HA ou devenir périmé après un arrêt de l'app. La carte
masque les titres non confirmés ; son affichage peut ajouter environ une minute
de retard. Les anciennes images sans correspondance restent inconnues. Ne
supprimez pas l'historique pour les identifier. Aucun service cloud de
reconnaissance d'images n'est utilisé.

Après la modification du script, demandez **une nouvelle œuvre lorsque le TV
est en mode Art**. Un envoi réussi active les lectures, environ toutes les 30
secondes. Démarrer/redémarrer seul ne contacte jamais le TV. La première lecture
mémorise son identité ; un autre appareil à la même adresse est refusé. Une
erreur ou un mode Art inactif suspend les lectures sans reconnexion. Pour
reprendre, remettez vous-même le TV en mode Art puis demandez une autre œuvre.
Une simple actualisation ne réactive rien. Pour revenir au fonctionnement
ponctuel, désactivez le mode, redémarrez et restaurez le script d'envoi initial.
N'effacez ni l'historique ni les identités mémorisées pour forcer la connexion.

Une lecture réelle avec comparaison d'image et affichage titre/artiste a été
vérifiée, pas la veille automatique, toutes les transitions ou la croissance du
Recorder. Aucune commande d'alimentation, Wake-on-LAN ou modification du mode Art
n'est envoyée par l'observateur ; la connexion elle-même pourrait toutefois réveiller le TV.
