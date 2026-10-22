# Œuvre actuelle et mode arrière-plan facultatif

> **Candidat de sécurité local D-247 — non publié :** les connexions automatiques
> au démarrage/réveil et les lectures périodiques `current_state_refresh` sont
> suspendues, même avec les options enregistrées. `resume_state_entity` sert
> uniquement à arrêter, jamais à démarrer. Après un nouvel envoi explicite réussi,
> le récepteur passif existant peut suivre les événements complets du diaporama.
> Une image inchangée expire ; aucune reprise automatique après veille ou perte
> de session. Ceci remplace les anciennes instructions de reprise b11–b16 ci-dessous.
> Cartes, identifiants de script et associations restent inchangés. L'absence
> d'effets secondaires de connexion n'est pas garantie.

Local, non publié : [aperçu facultatif de l’œuvre actuelle](CURRENT_PREVIEW.fr.md). Les cartes existantes restent inchangées.

[English](CURRENT_ARTWORK.md) | [Deutsch](CURRENT_ARTWORK.de.md) | Français | [Español](CURRENT_ARTWORK.es.md) | [Italiano](CURRENT_ARTWORK.it.md)

**Corrigé dans b16 :** l'actualisation facultative accepte les vraies réponses
`artmode_status` / `current_artwork`, avec contrôle strict de l'ID de requête.
Aucun nouveau réglage, connexion, format d'association ou changement de carte.

**Bêta publique b16 : expérimental et désactivé par défaut.** Les cartes b7/b8/b9/b10/b11/b12/b13 restent utilisables. Aucun nouvel assistant, clé API, extension HACS, privilège spécial ou autre app n'est nécessaire sur Home Assistant Green/OS.

[Rapport b16](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA16_VALIDATION.md) · [Sources correspondantes](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b16).

Même une connexion en lecture peut réveiller un TV. Les tests contrôlés couvrent des changements automatiques et un épisode de veille naturelle sur un Frame, pas tous les modèles ou firmwares. Laissez le mode désactivé si ce risque est inacceptable.

## Mémoire automatique des œuvres

### Synchronisation au démarrage et après veille — b12, facultatif

Après un ancien envoi Frame Gallery réussi, activez le **mode arrière-plan** et
indiquez dans **Synchroniser au démarrage / après veille** (`resume_state_entity`) l'entité
Samsung HA existante de ce TV (`media_player` ou `remote`). Son ID est dans
Paramètres → Appareils et services → Entités. Redémarrez ensuite l'app. Aucun
nouvel assistant, envoi d'image ou changement de carte n'est nécessaire.

Le premier état HA en cache à chaque démarrage ainsi configuré autorise **une
seule lecture initiale s'il indique `on`**, même inchangé depuis des heures.
Identité, mode Art, ID et image sont vérifiés avant toute attribution ; aucune
image n'est envoyée. Un premier résultat absent, invalide, futur, `off`, inconnu
ou en erreur consomme cette possibilité ; les `on` suivants ne la répètent pas.

**Fenêtre de démarrage — b13 :** une fenêtre fixe de dix secondes donne
la priorité à une demande de nouvelle œuvre acceptée sur la lecture initiale
automatique. L'acceptation annule la possibilité initiale restante avant l'envoi,
même si celui-ci échoue ensuite ou ne trouve aucune œuvre (`no_match`). Seul un
envoi réussi et valide peut alors ouvrir sa propre session de lecture. Sans
demande acceptée, la synchronisation initiale autonome reste possible après la
fenêtre si l'état HA en cache reste valide et `on`. Les règles ultérieures de
reprise après une véritable transition `off`/`on` restent inchangées.

Cette fenêtre limitée ne peut pas anticiper des scripts arbitrairement retardés.
Si un récepteur autonome a déjà démarré, un envoi ultérieur doit d'abord l'arrêter
et attendre sa fin. Les tests hors ligne de ce correctif n'apportent aucune
nouvelle preuve matérielle contre un réveil du TV ou un changement de mode.

La surveillance de reprise lit cet état HA en cache toutes les cinq secondes ;
elle est distincte des vérifications facultatives du socket Art ci-dessous.
Un `off` observé puis
un `on` plus récent de 30 secondes au maximum permettent une nouvelle lecture.
Les deux chemins partagent six essais par heure glissante **dans ce processus**.
Doublons, anciennes transitions et lacunes n'autorisent pas de répétition. Un
refus d'authentification bloque les lectures automatiques du processus. Un
redémarrage est une nouvelle possibilité, pas une limite persistante entre
redémarrages ; évitez les boucles de redémarrage.

HA `on` ne prouve pas le mode Art. La connexion peut réveiller le TV ou changer
son mode ; ce nouveau chemin est simulé hors ligne, sans nouvelle validation
matérielle. Laissez vide pour désactiver. Une app arrêtée ne suit aucun réveil.
Les limites d'affichage de 90 secondes et 15 minutes restent inchangées.

Chaque envoi sélectionné avec succès enregistre automatiquement l'ID TV, le titre, l'artiste et la source, même avec le mode arrière-plan **désactivé**. Aucun ID à saisir. L'association dépend de l'identité réelle du TV, pas seulement de son adresse IP. Le même ID sur un autre TV ne désigne pas la même œuvre. Un nouvel envoi réussi remplace l'ancienne association pour ce TV/ID.

Les données privées de l'app survivent aux mises à jour normales. Réinitialiser l'historique de sélection ne supprime pas les associations ; désinstaller avec suppression des données les efface. Gardez une sauvegarde avant réinstallation. Limite : les 2 048 dernières associations et 32 MiB, plus une sauvegarde. La référence est un petit échantillon RGB de 64×36 pixels, pas une archive haute résolution. Les anciennes associations vérifiées par image restent compatibles.

Les anciennes images, les envois d'autres apps et les envois sans identité TV stable restent inconnus. Aucun artiste deviné ni reconnaissance cloud.

### Actualisation facultative de l'état actuel — b16

`current_state_refresh` est une option distincte, **désactivée par défaut**, qui
nécessite `background_mode`. Elle autorise au maximum une vérification en lecture
de la cohérence du mode Art actuel et de l'ID d'image par période de 60 secondes,
sur le **socket Art déjà connecté**. Elle vise à rétablir artiste/titre connus
après le menu du TV ou la reprise du diaporama, même si l'image reste identique.
Aucune nouvelle connexion ni commande d'image, d'alimentation ou de mode.
Une image inconnue reste non identifiée ; aucun titre n'est inventé ou repris
de l'image précédente.

Une preuve fraîche et validée `current_state_read` est valable 90 secondes.
Les ID dupliqués, pongs ou notifications de mode actif ne la renouvellent pas à eux seuls.

Avec cette option, `off` ou `nav` du canal Art conserve **le même socket** ; ces
états ne sont pas une veille physique. Hors mode Art, titre et artiste sont
masqués. Les vérifications continuent même sans notification de retour : dans
la même limite d'une fois par minute, seul le mode est lu tant qu'il n'est pas
actif. Les ID d'image ne sont demandés qu'après un nouveau résultat `on` ; un cycle
de menu seul ne confirme aucune œuvre. Si la session voit d'abord `off` ou `nav`,
la preuve initiale unique par miniature attend le mode Art `on` sur ce socket ;
elle n'est pas répétée. La veille, un état HA « off » observé ou une connexion
fermée termine toujours la session, sans nouveau socket ni reconnexion aveugle.

Même sur ce socket, les requêtes peuvent perturber la veille automatique.
Laissez l'option désactivée si ce risque est inacceptable. Les tests hors ligne
ne garantissent ni compatibilité des firmwares ni absence de réveil.
Les cartes et scripts existants n'ont pas besoin de modification.

## Activer la carte facultative

1. Conservez caméra, minuteur, cartes et ID `script.frame_gallery_new_artwork`.
2. Activez le **mode arrière-plan**, puis redémarrez l'app. Démarrer/Arrêter contrôle le service, pas l'image. Sans l'entité facultative ci-dessus, aucun contact au démarrage ; avec elle, le premier HA `on` peut autoriser la lecture après la fenêtre de dix secondes, sauf si une demande d'envoi acceptée la remplace.
3. Remplacez uniquement le contenu du script par le [script d'envoi complet](examples/background-send-script.yaml). Adaptez le slug et le minuteur si nécessaire. Les cartes existantes fonctionnent ; remplacez les appels directs à `hassio.app_start` par le script.
4. Après un ancien envoi réussi, configurez l'entité ci-dessus pour lire l'œuvre déjà affichée sans nouvel envoi. Sur une installation sans association TV enregistrée, demandez la première œuvre en mode Art visible ; l'envoi réussi autorise une session expérimentale. Actualiser seul n'ouvre aucune connexion.
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
  En attente d'une vérification autorisée. Vérifiez les réglages arrière-plan/entité et le journal ; la lecture initiale configurée ne nécessite aucune nouvelle image.
  {% elif item.state == 'checking' %}
  Image actuelle non confirmée. En attente d'une preuve d'image ou de diaporama valide.
  {% elif item.state == 'unidentified' %}
  Aucune association enregistrée pour cette œuvre.
  {% else %}
  Œuvre actuelle non confirmée. TV indisponible ou session suspendue.
  {% endif %}
```

## Confirmation et limites

**Reprise historique b10 — événements seuls (`current_state_refresh` désactivé) :** une séquence incomplète de
notifications reconnues du diaporama masque les informations actuelles et
attend une nouvelle séquence complète sur la même connexion. Elle ne confirme
aucune œuvre et ne déclenche aucune requête supplémentaire. Les messages
inconnus ou incorrects, la veille, le mode TV et la perte de connexion terminent
toujours la session. Des codes fixes dans le journal distinguent les erreurs de
démarrage, réception, décodage et processus isolé, sans messages bruts ni
identifiants secrets. Le démarrage b12 et la fenêtre b13 n'ont pas de nouvelle validation TV ou veille.

Avec `current_state_refresh` activé, les notifications structurellement valides
mais non reconnues et `off`/`nav` du canal Art masquent les informations tout en
conservant le même socket selon les règles limitées ci-dessus. Elles ne
confirment aucune œuvre et n'autorisent aucune nouvelle connexion. La veille
physique, le refus d'authentification, des données de protocole mal formées et
un transport fermé terminent toujours la session.

Dans le journal, `event sequence incomplete` signifie que les données sont
masquées et que la même connexion attend, sans confirmer d'œuvre.
`event session stopped: reason=...; no reconnect` signifie que la session est
terminée, sans répétition immédiate. Pour signaler un problème, indiquez ce
code fixe, la version de l'app et le modèle du TV, jamais de jetons ni de données TV brutes.

Chaque session dure au maximum huit heures. En mode événements seuls
(`current_state_refresh` désactivé), veille, mode TV ou erreur peuvent l'arrêter
plus tôt. Les exceptions facultatives et arrêts définitifs ci-dessus restent applicables. Un nouveau processus configuré ou une transition HA fraîche ci-dessus peut autoriser une nouvelle lecture ; un envoi explicite réussi peut également ouvrir une session.

Après une lecture initiale et une comparaison locale d'image, une seule connexion écoute la séquence observée : `image_selected`, `auto_rotation_image_changed` du même ID, puis mode Art `on`, en cinq secondes. Avec `current_state_refresh` désactivé, aucune requête répétée, nouvelle miniature ou reconnexion dans cette session. Son activation permet seulement les vérifications limitées ci-dessus, pas de nouvelles miniatures ou connexions. Un événement utilise l'association d'envoi ou d'image vérifiée de ce TV ; un ID inconnu efface le texte.

La preuve initiale dure 90 secondes. La séquence complète dure au maximum **15 minutes**, adaptée au diaporama testé de dix minutes. Doublons, pongs et mode actif ne la renouvellent pas. Des cycles plus longs peuvent laisser des interruptions ; les changements manuels ne produisent pas forcément cette séquence. Le modèle peut ajouter environ une minute de retard.

Si l'actualisation est désactivée ou sans nouvelle vérification réussie, une
image fixe inchangée peut redevenir non confirmée après 90 secondes.
Le correctif de démarrage seul ne prolonge pas la preuve et n'interroge pas le TV en boucle pour
maintenir artificiellement une légende actuelle.

**Événements seuls (`current_state_refresh` désactivé) :** Veille, mode TV, déconnexion, événement invalide ou échec de publication suspend/arrête sans reconnexion immédiate. Avec l'option activée, les règles limitées du même socket et les arrêts définitifs ci-dessus s'appliquent. Après la fin effective d'une session, sans l'option de reprise ci-dessus, un nouvel envoi explicite en mode Art visible reste nécessaire. L'action manuelle Actualiser traite seulement les événements déjà reçus. Aucune commande d'alimentation, Wake-on-LAN, sélection d'image ou changement de mode n'est envoyée ; la connexion elle-même peut toutefois avoir des effets indésirables.

Les ID enregistrés sont des correspondances historiques, pas une vérification continue des pixels. Une réutilisation externe d'ID non observée ne peut pas être exclue. Une comparaison initiale contradictoire bloque la légende enregistrée. Aucune garantie générale de non-réveil ou de firmware (D-235).

Le capteur est un état publié par l'app, pas une intégration d'appareil enregistrée. Il peut manquer après un redémarrage de Core. Les données périmées/suspendues masquent le titre. Pour revenir au mode ponctuel : désactivez le mode, redémarrez et restaurez le script initial. N'effacez pas l'historique ou les identités pour forcer la connexion.
