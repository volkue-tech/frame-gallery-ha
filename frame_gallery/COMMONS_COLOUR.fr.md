# Choisir une couleur — à partir de la bêta 0.1.0b6

[English](COMMONS_COLOUR.md) | [Deutsch](COMMONS_COLOUR.de.md) | **Français** | [Español](COMMONS_COLOUR.es.md)

Cette page est en français. Home Assistant ne choisit pas automatiquement la
langue de la documentation : utilisez les liens ci-dessus.
Cette mise à jour traduit les guides, pas les champs de configuration de l’app.
Les libellés de ces champs sont indiqués en anglais ci-dessous.

Ce guide s’applique à **0.1.0b6 et aux versions suivantes**, avec 1000 œuvres
Commons sélectionnées. Le filtre de couleur n’est pas disponible dans
0.1.0b5 ni dans les versions antérieures. Pour commencer, suivez d’abord le
[guide d’installation et de carte standard](SETUP.fr.md).
Le sélecteur de couleur sur le tableau de bord est facultatif.

## Choisir une couleur dans l’app

1. Ouvrez **Settings → Apps → Frame Gallery → Configuration**
   (Paramètres → Apps → Frame Gallery → Configuration).
2. Choisissez `wikimedia_commons` dans **Artwork source**.
3. Juste en dessous, dans **Colour wish (Commons)**, choisissez une couleur,
   par exemple **Blue** pour le bleu. **any** signifie toutes les couleurs
   et reste la valeur par défaut.
4. Enregistrez. La prochaine exécution, lancée depuis l’app ou votre carte
   actuelle, cherchera une œuvre dans cette sélection.

Aucune clé API, nouvelle entrée auxiliaire, nouveau script ou nouvelle carte
n’est nécessaire pour ce réglage. L’aperçu et l’affichage facultatif du titre
et de l’artiste restent utilisables. Un nouveau catalogue ne réinitialise pas
l’historique des œuvres envoyées.

## Que signifie « bleu » ?

Le bleu doit occuper une surface visible de l’œuvre, sans nécessairement être
sa couleur dominante. Le seuil est d’environ cinq pour cent de l’image.
Une œuvre bleue et jaune peut donc correspondre à Blue comme à Yellow.
Les tons ocre et dorés peuvent être classés dans Yellow. Il s’agit de familles
de couleurs, pas d’une correspondance exacte à une peinture murale ou à un code HEX.

Les choix sont Red, Orange, Yellow, Green, Blue, Purple, Pink, Brown, Beige,
Gray, Black et White. Les données d’analyse conservent aussi les proportions
et jusqu’à trois familles importantes distinctes. Cette version propose
volontairement **une seule** couleur, pas de combinaisons de couleurs.

L’analyse est réalisée sur le Mac pendant la préparation du catalogue.
L’app n’a pas besoin de télécharger de nombreuses images sur le Green pour
tester leurs couleurs. Les marges noires ajoutées pour adapter l’image au
téléviseur ne sont pas comptées comme des couleurs de l’œuvre.

## Aucune nouvelle œuvre ne correspond ?

L’exécution se termine proprement. L’image actuelle du téléviseur, l’aperçu
et les informations de l’œuvre sont conservés. L’app ne choisit pas une autre
couleur sans vous le dire. Les œuvres déjà envoyées ou téléversées restent
exclues ; une petite sélection peut finir par être épuisée.

Choisissez une autre couleur ou **any**. Le journal distingue l’absence de
résultat d’une erreur de source. Comme la durée et le nombre de requêtes sont
limités, une exécution sans résultat ne signifie pas forcément que toutes les
œuvres de cette couleur sont définitivement exclues.

**Prefer 16:9** peut utiliser une autre image horizontale avec des marges si
aucune œuvre ne correspond au format préféré, mais jamais une autre couleur.
Nous recommandons **contain** pour conserver l’œuvre entière sans la recadrer.

## Autres sources et entrée auxiliaire facultative

La sélection de couleur fonctionne uniquement avec Commons. Chicago, Cleveland
et vos propres images ne disposent pas de ce filtre ; le journal indique qu’un
choix de couleur pour ces sources n’a pas été appliqué.

Ces autres sources restent disponibles. La carte ci-dessous est prévue pour
Commons et ne propose pas de changement de source. Si vous changez la source
dans la configuration de l’app, la couleur de la carte ne s’y applique **pas**.
Le sélecteur porte donc le libellé **Couleur souhaitée (Commons uniquement)**.
L’œuvre actuellement affichée ne permet pas de déduire la source du prochain
chargement.

Une entrée auxiliaire de couleur peut piloter ce choix depuis le tableau de bord.
Elle n’est pas nécessaire pour l’installation standard. L’app accepte, par
exemple, **Blau**, **Blue** et **color_blue** comme une même valeur.
Ne traduisez pas les valeurs de la liste en français : utilisez celles indiquées
ci-dessous. Plusieurs couleurs dans une seule valeur ne forment pas une combinaison.

## Ajouter le sélecteur à la carte

**Facultatif ; disponible à partir de 0.1.0b6.** La carte standard fonctionne
toujours sans cette étape. Aucun HACS ni nouveau script n’est nécessaire.
Une nouvelle entrée auxiliaire Dropdown est nécessaire uniquement pour
choisir la couleur sur le tableau de bord.

Les chemins de menu suivants utilisent les libellés anglais. Si votre Home
Assistant est en français, cherchez les rubriques équivalentes ; leur traduction
peut varier selon la version.

1. Ouvrez **Settings → Devices & services → Helpers → Create helper → Dropdown**.
   Nommez la liste `Frame Gallery Colour`.
2. Ajoutez ces options séparément, exactement comme indiqué, une par option :
   `any`, `Red`, `Orange`, `Yellow`, `Green`, `Blue`, `Purple`, `Pink`, `Brown`,
   `Beige`, `Gray`, `Black`, `White`. `any` signifie toutes les couleurs.
   Les valeurs anglaises sont identiques dans toutes les versions de ce guide.
3. Enregistrez et vérifiez l’identifiant réel de l’entité : ouvrez l’entrée
   auxiliaire → **⋮ → Details**. Identifiant attendu :
   `input_select.frame_gallery_colour`. Une entité existante de même nom peut
   entraîner un identifiant différent.
4. Dans **Frame Gallery → Configuration**, saisissez cet identifiant dans
   **Colour helper** (`color_helper`). Si le champ est masqué, activez
   **Show unused optional configuration options**. Gardez Commons comme source
   et enregistrez.
5. Choisissez `any`. Utilisez le bloc complet ci-dessous dans votre carte.
   Remplacez partout les identifiants de caméra, de minuterie, de script ou de
   liste si les vôtres sont différents.

Le sélecteur est prioritaire sur la couleur enregistrée dans l’app.
Changer la couleur **ne lance pas automatiquement** une exécution : choisissez
d’abord la couleur, puis touchez l’image. Un changement pendant un chargement
s’applique à l’exécution suivante. Si l’entrée auxiliaire est illisible, l’app
utilise son réglage enregistré et l’indique dans le journal.
La sélection simultanée de plusieurs couleurs n’est pas proposée.

### Carte complète avec aperçu et sélecteur de couleur

Réutilisez la caméra, la minuterie et le script du guide d’installation.
Le YAML **ne crée pas** l’entrée auxiliaire : terminez d’abord les cinq étapes.
Tous les composants de la carte sont intégrés à Home Assistant.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
      - entity: input_select.frame_gallery_colour
        name: Couleur souhaitée (Commons uniquement)
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

La carte facultative avec le titre et l’artiste peut rester séparément en dessous.
Sans extension supplémentaire, cet ensemble reste un groupe de cartes natives,
pas une carte personnalisée unique.

**Vérification rapide après la mise à jour :** choisissez `Blue`, touchez
l’image et attendez la fin. Choisissez ensuite `any` et recommencez.
Si aucune œuvre non encore envoyée ne correspond, l’image et les informations
restent inchangées et l’exécution se termine tout de même. Le sélecteur peut
rester visible pendant le chargement.
