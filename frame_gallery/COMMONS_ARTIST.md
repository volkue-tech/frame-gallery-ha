# Artist selection — unreleased update candidate

**English** | [Deutsch](COMMONS_ARTIST.de.md) | [Français](COMMONS_ARTIST.fr.md) | [Español](COMMONS_ARTIST.es.md) | [Italiano](COMMONS_ARTIST.it.md)

Not available in public 0.1.0b6 yet. Do not configure these artist options on b6. This candidate adds one optional artist wish for Commons. No new mandatory helper or dashboard replacement: the standard card keeps working. Other providers report this wish as unsupported.

Without a dashboard selector: show unused optional options in Frame Gallery → Configuration and fill **Artist wish (Commons, optional)** (`artist`) with an exact name from the [choice list](ARTIST_CHOICES.md), for example `Wassily Kandinsky`. Empty or `All artists` means unrestricted. Save, then start the app as usual.

## Setup

For a dashboard Dropdown, create a helper through Settings → Devices & services → Helpers → Create helper → Dropdown. Name it `Frame Gallery Artist`. Add `All artists` plus only your preferred names from the list; each is a separate option. A starter list is below. Do not translate artist names or technical values.

```text
All artists
Wassily Kandinsky
Claude Monet
Vincent van Gogh
Pierre-Auguste Renoir
Winslow Homer
W.carter
```

Open the helper → ⋮ → Details and verify its actual ID, normally `input_select.frame_gallery_artist`. An existing name can produce a suffix. Enter the actual ID in **Artist helper (Commons, optional)** (`artist_helper`), keep Commons selected and save. Select `All artists` initially. Do not reuse the artwork-information Text helper.

The helper overrides the saved artist. An unreadable/unavailable/invalid helper warns and falls back to the static value. Changing the Dropdown does not start a run; select your preferences, then tap the artwork. Changes during a run apply at the next start.

Artist and colour are an intersection, not alternatives. Shape fallback may relax 16:9, never artist or colour. Already sent/uploaded works stay excluded. The list shows catalogue totals, not unused counts: Kandinsky and Monet currently each have one work. After using it, that choice can be exhausted. No match leaves TV, preview and caption unchanged and finishes cleanly. Choose `All artists` or `any` for a broader selection; there is no implicit history reset.

## Artist only

Artist-only card: reuse the camera, timer and script from [setup](DOCS.md#dashboard). Only the artist Dropdown is added. Replace every ID if yours differs. YAML does not create helpers. No HACS, SSH or configuration.yaml change.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
      - entity: input_select.frame_gallery_artist
        name: Artist (Commons only)
  - type: picture-entity
    entity: camera.frame_gallery_preview
    name: Load new artwork
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
      content: Updating artwork…
```

## Artist and colour

Artist and colour card: additionally complete the [colour helper setup](COMMONS_COLOUR.md), retaining `input_select.frame_gallery_colour` and `color_helper`. Reuse the same script/camera/timer. This is a native vertical stack, not a custom dashboard extension.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
      - entity: input_select.frame_gallery_artist
        name: Artist (Commons only)
      - entity: input_select.frame_gallery_colour
        name: Colour wish (Commons only)
  - type: picture-entity
    entity: camera.frame_gallery_preview
    name: Load new artwork
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
      content: Updating artwork…
```

The [optional artwork-information card](ARTWORK_INFO.md) remains separate and unchanged. The current artwork caption is not the next requested artist. The app does not install cards, create helpers or populate the full list automatically.
