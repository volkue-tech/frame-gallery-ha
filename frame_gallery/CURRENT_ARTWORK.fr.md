# Œuvre actuelle et mode arrière-plan facultatif

[English](CURRENT_ARTWORK.md) | [Deutsch](CURRENT_ARTWORK.de.md) | Français | [Español](CURRENT_ARTWORK.es.md) | [Italiano](CURRENT_ARTWORK.it.md)

**Bêta b11 : expérimental et désactivé par défaut.** Les cartes b7/b8/b9/b10 restent utilisables. Aucun nouvel assistant, clé API, extension HACS, privilège spécial ou autre app n'est nécessaire sur Home Assistant Green/OS.

Même une connexion en lecture peut réveiller un TV. Les tests contrôlés couvrent des changements automatiques et un épisode de veille naturelle sur un Frame, pas tous les modèles ou firmwares. Laissez le mode désactivé si ce risque est inacceptable.

## Mémoire automatique des œuvres

### Reprendre après la veille — nouveau en b11, facultatif

Après un ancien envoi Frame Gallery réussi, activez le **mode arrière-plan** et
indiquez dans **Reprendre après la veille** (`resume_state_entity`) l'entité
Samsung HA existante de ce TV (`media_player` ou `remote`). Son ID est dans
Paramètres → Appareils et services → Entités. Redémarrez ensuite l'app. Aucun
nouvel assistant, envoi d'image ou changement de carte n'est nécessaire.

Seul cet état HA en cache est lu toutes les cinq secondes. Un `off` observé puis
un `on` plus récent, datant de 30 secondes au maximum, autorisent un seul essai
en lecture, six par heure au maximum. L'identité du TV, le mode Art et l'image
actuelle sont revérifiés. Démarrage avec TV déjà allumé, redémarrage, doublons,
états anciens/inconnus et interruption du suivi n'autorisent pas de lecture.
Un échec n'est pas répété : il faut un nouveau cycle arrêt-marche. Un refus
d'authentification bloque les essais automatiques dans ce processus.

HA `on` ne prouve pas le mode Art. La connexion peut réveiller le TV ou changer
son mode ; ce nouveau chemin est simulé hors ligne, sans nouvelle validation
matérielle. Laissez vide pour désactiver. Une app arrêtée ne suit aucun réveil.
Les limites d'affichage de 90 secondes et 15 minutes restent inchangées.

Chaque envoi sélectionné avec succès enregistre automatiquement l'ID TV, le titre, l'artiste et la source, même avec le mode arrière-plan **désactivé**. Aucun ID à saisir. L'association dépend de l'identité réelle du TV, pas seulement de son adresse IP. Le même ID sur un autre TV ne désigne pas la même œuvre. Un nouvel envoi réussi remplace l'ancienne association pour ce TV/ID.

Les données privées de l'app survivent aux mises à jour normales. Réinitialiser l'historique de sélection ne supprime pas les associations ; désinstaller avec suppression des données les efface. Gardez une sauvegarde avant réinstallation. Limite : les 2 048 dernières associations et 32 MiB, plus une sauvegarde. La référence est un petit échantillon RGB de 64×36 pixels, pas une archive haute résolution. Les anciennes associations vérifiées par image restent compatibles.

Les anciennes images, les envois d'autres apps et les envois sans identité TV stable restent inconnus. Aucun artiste deviné ni reconnaissance cloud.

## Activer la carte facultative

1. Conservez caméra, minuteur, cartes et ID `script.frame_gallery_new_artwork`.
2. Activez le **mode arrière-plan**, puis redémarrez l'app. Démarrer/Arrêter contrôle le service, pas un changement d'image. Le démarrage automatique ne contacte pas le TV.
3. Remplacez uniquement le contenu du script par le [script d'envoi complet](examples/background-send-script.yaml). Adaptez le slug et le minuteur si nécessaire. Les cartes existantes fonctionnent ; remplacez les appels directs à `hassio.app_start` par le script.
4. Avec une œuvre visible en mode Art, demandez explicitement une nouvelle œuvre. Un envoi récent réussi avec association enregistrée autorise une seule session expérimentale. Démarrer/redémarrer/actualiser seul ne l'active pas.
5. Ajoutez une carte manuelle avec le YAML **complet** ci-dessous.

La carte image/couleur/artiste existante montre le **dernier aperçu envoyé**, pas une capture en direct. Cette carte native supplémentaire sépare les informations actuelles.

```yaml
type: markdown
title: Frame Gallery — Œuvre actuelle
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% if item is not defined or item is none %}
  Aucune information actuelle disponible.
  {% elif item.state == 'artwork' and
      as_timestamp(now()) - as_timestamp(item.last_reported, 0) <
      (900 if item.attributes.get('confirmation_method') == 'slideshow_events' else 90) %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Dernière confirmation: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'validation_required' %}
  Vérifications bloquées. Consultez le journal et demandez explicitement une œuvre.
  {% elif item.state == 'checking' %}
  Opération en cours. L'image actuelle n'est pas encore confirmée.
  {% elif item.state == 'unidentified' %}
  Aucune association enregistrée pour cette œuvre.
  {% else %}
  Œuvre actuelle non confirmée. TV indisponible ou session suspendue.
  {% endif %}
```

## Confirmation et limites

**Correctif de reprise bêta b10 :** une séquence incomplète de
notifications reconnues du diaporama masque les informations actuelles et
attend une nouvelle séquence complète sur la même connexion. Elle ne confirme
aucune œuvre et ne déclenche aucune requête supplémentaire. Les messages
inconnus ou incorrects, la veille, le mode TV et la perte de connexion terminent
toujours la session. Des codes fixes dans le journal distinguent les erreurs de
démarrage, réception, décodage et processus isolé, sans messages bruts ni
identifiants secrets. La nouvelle reprise b11 n'est ni installée ni testée sur le téléviseur.

Dans le journal, `event sequence incomplete` signifie que les données sont
masquées et que la même connexion attend, sans confirmer d'œuvre.
`event session stopped: reason=...; no reconnect` signifie que la session est
terminée, sans répétition immédiate. Pour signaler un problème, indiquez ce
code fixe, la version de l'app et le modèle du TV, jamais de jetons ni de données TV brutes.

Chaque session dure au maximum huit heures et se termine plus tôt en veille,
mode TV ou erreur. Seule la transition HA fraîche explicitement configurée ci-dessus peut ouvrir une nouvelle session.

Après une lecture initiale et une comparaison locale d'image, une seule connexion écoute la séquence observée : `image_selected`, `auto_rotation_image_changed` du même ID, puis mode Art `on`, en cinq secondes. Dans cette session, pas de requêtes répétées, de nouvelles miniatures ni de reconnexion. Un événement utilise l'association d'envoi ou d'image vérifiée de ce TV ; un ID inconnu efface le texte.

La preuve initiale dure 90 secondes. La séquence complète dure au maximum **15 minutes**, adaptée au diaporama testé de dix minutes. Doublons, pongs et mode actif ne la renouvellent pas. Des cycles plus longs peuvent laisser des interruptions ; les changements manuels ne produisent pas forcément cette séquence. Le modèle peut ajouter environ une minute de retard.

Veille, mode TV, déconnexion, événement invalide ou échec de publication suspend/arrête sans reconnexion immédiate. Sans l'option de reprise ci-dessus, un nouvel envoi explicite en mode Art visible reste nécessaire. Actualiser traite seulement les événements déjà reçus. Aucune commande d'alimentation, Wake-on-LAN, sélection d'image ou changement de mode n'est envoyée ; la connexion elle-même peut toutefois avoir des effets indésirables.

Les ID enregistrés sont des correspondances historiques, pas une vérification continue des pixels. Une réutilisation externe d'ID non observée ne peut pas être exclue. Une comparaison initiale contradictoire bloque la légende enregistrée. Aucune garantie générale de non-réveil ou de firmware (D-235).

Le capteur est un état publié par l'app, pas une intégration d'appareil enregistrée. Il peut manquer après un redémarrage de Core. Les données périmées/suspendues masquent le titre. Pour revenir au mode ponctuel : désactivez le mode, redémarrez et restaurez le script initial. N'effacez pas l'historique ou les identités pour forcer la connexion.
