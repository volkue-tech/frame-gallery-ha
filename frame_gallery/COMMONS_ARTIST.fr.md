# Sélection d'artiste — mise à jour candidate non publiée

[English](COMMONS_ARTIST.md) | [Deutsch](COMMONS_ARTIST.de.md) | **Français** | [Español](COMMONS_ARTIST.es.md) | [Italiano](COMMONS_ARTIST.it.md)

Pas encore disponible dans la version publique 0.1.0b6. Ne configurez pas ces options sur b6. Le candidat ajoute un souhait d'artiste facultatif pour Commons. Aucun nouvel assistant obligatoire ni remplacement de la carte : la carte standard reste utilisable. Les autres sources signalent ce filtre comme non pris en charge.

Sans sélecteur sur le tableau de bord : affichez les options facultatives inutilisées dans Frame Gallery → Configuration. Dans **Artiste souhaité (Commons, facultatif)** (`artist`), copiez un nom complet proposé dans la [liste](ARTIST_CHOICES.md), par exemple `Wassily Kandinsky`. Vide ou `All artists` signifie sans restriction. Enregistrez puis démarrez l'app normalement.

## Configuration

Pour un menu déroulant : Paramètres → Appareils et services → Entrées → Créer une entrée → Liste déroulante (les intitulés peuvent varier). Nom : `Frame Gallery Artist`. Ajoutez `All artists` et vos noms préférés comme options distinctes. Un exemple figure ci-dessous. Ne traduisez pas les noms ni les valeurs techniques.

```text
All artists
Wassily Kandinsky
Claude Monet
Vincent van Gogh
Pierre-Auguste Renoir
Winslow Homer
W.carter
```

Ouvrez l'assistant → ⋮ → Détails et vérifiez son ID réel, normalement `input_select.frame_gallery_artist`. Un nom existant peut entraîner un suffixe. Saisissez cet ID dans **Artiste depuis le tableau de bord (facultatif, Commons)** (`artist_helper`), gardez Commons et enregistrez. Choisissez d'abord `All artists`. Ne réutilisez pas l'entrée Texte des informations sur l'œuvre.

Le menu remplace l'artiste enregistré. Une valeur illisible, indisponible ou invalide utilise le souhait enregistré avec un avertissement. Modifier le menu ne lance pas automatiquement l'app : choisissez, puis touchez l'image. Un changement en cours s'applique au prochain lancement.

L'artiste et la couleur doivent tous deux correspondre. Le repli de format peut assouplir le 16:9, jamais l'artiste ni la couleur. Les œuvres déjà envoyées restent exclues. La liste donne des totaux, pas les œuvres inutilisées : Kandinsky et Monet ont chacun une œuvre actuellement. La sélection peut être épuisée après son utilisation. Sans résultat, téléviseur, aperçu et légende restent inchangés et le lancement se termine proprement. Élargissez avec `All artists` ou `any`. Aucun historique n'est réinitialisé automatiquement.

## Artiste seul

Carte avec artiste seul : réutilisez caméra, minuteur et script de [l'installation](SETUP.fr.md). Seul le menu d'artistes est ajouté. Remplacez tous les ID différents. YAML ne crée pas les assistants. Aucun HACS, SSH ni changement de configuration.yaml.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
      - entity: input_select.frame_gallery_artist
        name: Artiste (Commons uniquement)
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

## Artiste et couleur

Carte avec artiste et couleur : configurez aussi [l'assistant de couleur](COMMONS_COLOUR.fr.md), avec `input_select.frame_gallery_colour` et `color_helper`. Réutilisez caméra, minuteur et script. Une pile native, sans extension du tableau de bord.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
      - entity: input_select.frame_gallery_artist
        name: Artiste (Commons uniquement)
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

La [carte facultative des informations](ARTWORK_INFO.md) reste séparée et inchangée. L'artiste affiché pour l'aperçu ne décrit pas forcément votre prochaine sélection. L'app n'installe pas de cartes et ne crée ni ne remplit automatiquement les assistants.
