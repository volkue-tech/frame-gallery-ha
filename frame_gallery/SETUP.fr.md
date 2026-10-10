# Frame Gallery — installation et première carte

[English](DOCS.md#installation) | **Français** | [Español](SETUP.es.md)

Guide de démarrage pour la **bêta 0.1.0b6**. La langue de cette page est choisie
avec les liens ci-dessus, pas automatiquement par Home Assistant.
Les documents techniques restent [en anglais](DOCS.md#options).
Cette mise à jour traduit les guides, pas le formulaire de configuration de
l’app. Les chemins de menu et les noms de champs ci-dessous sont indiqués en
anglais pour correspondre à l’interface anglaise ; dans un Home Assistant
traduit, cherchez les rubriques équivalentes.

**Parcours :** installer → afficher une œuvre sur le téléviseur → ajouter la carte
facultative → [ajouter le sélecteur de couleur](COMMONS_COLOUR.fr.md).

## Avant de commencer

- **Home Assistant OS avec Supervisor/Apps**, par exemple Home Assistant Green,
  avec Home Assistant 2026.2 ou plus récent. Les installations Container et
  Core seules ne peuvent pas installer cette app.
- Un **Samsung Frame TV** sur le même réseau local et le même sous-réseau.
- L’adresse IPv4 privée du téléviseur, par exemple `192.168.1.20`. Réservez-la dans
  votre routeur afin qu’elle reste fixe. Les noms comme `tv.local` ne sont
  pas acceptés.
- Dans les paramètres de connexion du téléviseur pour les appareils externes,
  choisissez la notification d’accès *First Time Only*, si votre modèle
  propose ce réglage.

Aucun SSH, terminal, clé API ni modification de `configuration.yaml` n’est
nécessaire. Aucun compte Wikimedia n’est requis.

## 1. Installer depuis Home Assistant

1. [Ajoutez le dépôt à Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fvolkue-tech%2Fframe-gallery-ha).
   Sinon, ouvrez **Settings → Apps → App store → ⋮ → Repositories** et ajoutez
   `https://github.com/volkue-tech/frame-gallery-ha`. C’est un dépôt d’apps,
   pas une intégration HACS.
2. Recherchez **Samsung** ou **Frame Gallery**, ouvrez **Frame Gallery – Samsung
   Frame TV** et choisissez **Install**. L’image déjà construite pour votre
   appareil est téléchargée ; le Green ne compile rien.
3. Dans **Configuration**, renseignez **TV address** puis **Save**.
   Gardez les autres valeurs par défaut pour le premier essai.
4. Laissez **Watchdog** et **Start on boot** désactivés. Chaque démarrage
   charge une œuvre puis l’app s’arrête normalement ; elle ne doit pas
   redémarrer en boucle ni changer l’image à chaque redémarrage de HA.

Pour une mise à jour, mettez à jour l’app existante : **ne la désinstallez pas**.
Vos réglages et l’historique des envois sont conservés.

## 2. Afficher la première œuvre

1. Allumez le téléviseur. Dans l’onglet **Info** de l’app, choisissez **Start**.
2. Suivez l’onglet **Log**. Lors de la première connexion, acceptez la demande
   d’autorisation sur le téléviseur **dans les 20 secondes**.
3. Si le journal indique `outcome=tv_not_authorized`, relancez l’app et
   acceptez la demande. `outcome=delivered` indique que l’envoi et la sélection
   ont été confirmés par le protocole ; vérifiez aussi l’affichage sur le téléviseur.
4. L’état **Stopped** après l’exécution est normal. Démarrez à nouveau l’app
   quand vous voulez une autre œuvre.

La carte n’est pas nécessaire pour ce premier essai. Elle n’est pas créée
automatiquement lors de l’installation.

### Réglages recommandés

| Champ anglais de l’app | Conseil |
| --- | --- |
| TV address | L’adresse IPv4 privée fixe du téléviseur. |
| Artwork source | `wikimedia_commons`, valeur par défaut pour une nouvelle installation. |
| Colour wish (Commons) | `any` pour toutes les couleurs ; une seule couleur est facultative. |
| Landscape only | Activé pour les images horizontales. |
| Prefer 16:9 (may take longer) | Activé pour privilégier le format le plus proche ; désactivé pour toute la sélection Commons. |
| Image fit (contain = no crop) | `contain` pour l’œuvre entière, sans recadrage. `cover` peut couper les bords. |

Les 1000 sources Commons s’écartent d’au plus 2,5 % du rapport 16:9. La préférence
16:9 utilise un seuil plus strict d’environ 1 % ; de petites marges peuvent
rester. Les options avancées sont facultatives. Activez **Show unused optional
configuration options** uniquement pour afficher les champs dont vous avez
besoin. Le filtre de couleur concerne Commons uniquement.

## 3. Ajouter la carte standard au tableau de bord

**Facultatif.** Vous créez une caméra d’aperçu, une minuterie et un script.
La « caméra » montre le fichier d’image ; ce n’est pas une caméra physique.
Utilisez un compte administrateur. Aucun HACS ni extension de carte n’est requis.

![Carte Frame Gallery réelle avec Counter-composition XVI et des informations facultatives sur l’œuvre.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/dashboard-commons.png)

*Capture historique de la bêta b3 sur Green, avec un libellé allemand et les
informations facultatives. Ce n’est pas une capture du sélecteur de couleur
ni un nouveau test. Œuvre : Theo van Doesburg,
[Counter-composition XVI](https://commons.wikimedia.org/w/index.php?curid=3817033),
reproduction Wikimedia Commons dont les métadonnées de domaine public ont été
vérifiées le 5 octobre 2026.*

### A. Créer et nommer la caméra d’aperçu

Après une exécution réussie de l’app, ouvrez **Settings → Devices & services →
Add integration → Local File**. Le fichier d’aperçu doit déjà exister.

![Dialogue réel Local File en allemand, avec les champs Name et Dateipfad.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/local-file-setup.png)

*Capture avant saisie. « Dateipfad » signifie chemin du fichier.
Les deux valeurs ci-dessous sont identiques dans toutes les langues.*

| Champ | Valeur à saisir |
| --- | --- |
| Name | `Frame Gallery Preview` — remplacez le nom par défaut `Local File`. |
| File path | `/media/frame_gallery/preview/latest.jpg` |

Validez avec **OK**. **La caméra est créée automatiquement.** La page de
l’intégration peut toujours s’appeler **Local File** ; le lien **1 entity**
signifie que l’entité existe, pas qu’une autre installation est nécessaire.

1. Cliquez sur **1 entity**, puis sur la ligne **Frame Gallery Preview**
   (ou **Local File** si vous avez gardé le nom par défaut).
2. Dans la fenêtre de l’image, ouvrez **⋮ → Details** et copiez **ID**.
3. L’ID attendu est `camera.frame_gallery_preview`. Vérifiez aussi le chemin
   du fichier. Si votre ID diffère, utilisez votre ID réel dans le YAML.

Si vous avez déjà créé cette caméra, réutilisez-la : ne créez pas une seconde
intégration Local File avec le même chemin. Dans le sélecteur d’entité de la
carte, recherchez le **nom affiché** Frame Gallery Preview ou Local File,
pas uniquement l’ID technique. Renommer une entité existante ne change pas
automatiquement son ID. Conservez les noms proposés pour faciliter la configuration.

**Confidentialité :** la vue Details contient aussi des jetons d’accès et une
URL avec un jeton. Ne partagez que l’ID et le chemin, pas tous les attributs.

### B. Créer la minuterie de chargement

Ouvrez **Settings → Devices & services → Helpers → Create helper → Timer**.
Nom : `Frame Gallery run`. Durée : `0:02:30`.
ID attendu : `timer.frame_gallery_run`.

Dans la configuration de Frame Gallery, renseignez cet ID dans **Dashboard
loading timer** (`loading_timer`). Affichez les options facultatives si
nécessaire. Créer la minuterie ne suffit pas : ce champ relie la fin de
l’exécution à votre minuterie. Utilisez une minuterie dédiée à cette app.

### C. Créer le script

Ouvrez **Settings → Automations & scenes → Scripts → Create script → ⋮ →
Edit in YAML**. Copiez le bloc **complet**, enregistrez et vérifiez l’ID
`script.frame_gallery_new_artwork`. L’alias reste en anglais pour conserver
le nom technique attendu. Si vos IDs ou l’ID de l’app diffèrent, adaptez-les
partout. L’ID public observé de l’app est `a94fc569_frame_gallery` ; vérifiez
l’URL de sa page. N’utilisez pas l’ID d’une ancienne app locale de test.

```yaml
alias: Frame Gallery new artwork
description: Starts the Frame Gallery app and shows a note on the dashboard while it runs.
mode: single
sequence:
  - condition: state
    entity_id: timer.frame_gallery_run
    state: idle
  - action: timer.start
    target:
      entity_id: timer.frame_gallery_run
    data:
      duration: "00:02:30"
  - action: hassio.app_start
    data:
      app: a94fc569_frame_gallery
    continue_on_error: true
  - wait_template: "{{ not is_state('timer.frame_gallery_run', 'active') }}"
    timeout: "00:02:30"
    continue_on_timeout: true
  - delay: "00:00:04"
```

### D. Ajouter la carte

Modifiez votre tableau de bord, choisissez **Add card → Manual** et collez
le bloc complet. Remplacez les IDs différents avant d’enregistrer.

```yaml
type: vertical-stack
cards:
  - type: picture-entity
    entity: camera.frame_gallery_preview
    name: Afficher une nouvelle œuvre
    show_state: false
    show_name: true
    camera_view: auto
    aspect_ratio: "16:9"
    tap_action:
      action: perform-action
      perform_action: script.turn_on
      target:
        entity_id: script.frame_gallery_new_artwork
    hold_action:
      action: more-info
  - type: conditional
    conditions:
      - condition: state
        entity: timer.frame_gallery_run
        state: active
    card:
      type: markdown
      content: Chargement de l’œuvre…
```

Touchez l’image pour charger une nouvelle œuvre ; un appui long ouvre l’aperçu.
Le texte de chargement apparaît uniquement pendant l’activité de la minuterie.
Son absence au repos est normale. La minuterie revient à l’état inactif après
le nettoyage, même sans résultat ou après une annulation propre. Son expiration
après 150 secondes limite l’attente si la notification échoue. La disparition
du texte n’est pas une preuve d’envoi réussi : consultez le journal.
Le rafraîchissement de l’image est indépendant de cette minuterie.

Si la carte affiche « Entity not found », vérifiez les IDs plutôt que de créer
une deuxième caméra. Dans l’éditeur, l’aperçu du texte de chargement ne prouve
pas qu’une exécution est active.

**Copier le YAML :** sur GitHub, survolez un bloc et utilisez le bouton de copie.
Si l’onglet Documentation n’en propose pas, ouvrez cette page sur GitHub.
Ne copiez pas les délimiteurs Markdown, et gardez l’indentation.

## 4. Ajouter une couleur ou les informations de l’œuvre

- [Sélecteur de couleur : guide français complet](COMMONS_COLOUR.fr.md).
  Il ajoute une liste facultative, pas un nouveau script. La couleur ne
  déclenche pas automatiquement une exécution.
- [Titre et artiste : guide anglais](ARTWORK_INFO.md).
  Facultatif : une entrée auxiliaire Text distincte est nécessaire.
  La carte standard reste utilisable sans elle.

Une exécution sans nouvelle correspondance conserve l’image et les
informations précédentes. Les œuvres déjà envoyées restent exclues.
Les images téléchargées temporairement sont nettoyées ; les œuvres déjà
stockées sur le téléviseur ne sont pas supprimées par l’app.

## Aide et limites

La compatibilité avec tous les modèles de TV n’est pas garantie.
Pour un échec, consultez le résultat final du journal, puis
[les explications techniques en anglais](DOCS.md#reading-the-log).
[Signalez un problème](https://github.com/volkue-tech/frame-gallery-ha/issues)
avec la version, le modèle et le résultat, sans mots de passe ni jetons.

Projet indépendant, sans affiliation avec Samsung, Wikimedia, les musées
ou Home Assistant. Les [licences et notes techniques](DOCS.md#licences)
restent en anglais.
