# Colour selection from Beta 0.1.0b6

**English** | [Deutsch](COMMONS_COLOUR.de.md) | [Français](COMMONS_COLOUR.fr.md) | [Español](COMMONS_COLOUR.es.md)

This is the English guide. Home Assistant does not automatically switch this
page's language; use the language links above for another language.

This guide applies to **0.1.0b6 and newer**, with 1000 curated Commons works.
The colour filter is not available in Beta 0.1.0b5 or earlier versions.
For your first setup, follow the [standard guide](DOCS.md#dashboard) first.
Choosing a colour on the dashboard is optional.

## Choose a colour in the app

1. Open **Settings → Apps → Frame Gallery → Configuration**.
2. Select **Wikimedia Commons** as the artwork source.
3. Under **Colour wish (Commons)**, choose a colour, for example **Blue**.
   **any** means all colours and remains the default.
4. Save. The next artwork run, started from the app or your existing dashboard
   card, will search within this selection.

No API key, new helper, new script or replacement card is needed.
Your existing preview and optional artist/title display remain usable.
A new catalogue does not reset your sent-artwork history.

## What does “blue” mean?

Blue must cover a noticeable area of the artwork, but need not be its largest
colour. Selection uses approximately five percent of the image area as its
threshold. A blue-and-yellow work can therefore appear under either Blue or
Yellow. Ochre and gold tones may fall under Yellow. Each colour is a broad
family, not an exact match to a wall paint or HEX value.

The choices are Red, Orange, Yellow, Green, Blue, Purple, Pink, Brown, Beige,
Gray, Black and White. The analysis data also retain area shares and up to
three important distinct colour families. This update deliberately offers
only **one** colour in the UI. It does not add colour-combination selection.

Analysis takes place during catalogue preparation on the Mac. The app does
not need to download many images to the Green to try out their colours.
Black TV margins added by image fitting are not counted as artwork colours.

## No matching new artwork?

The run stops cleanly. The previous TV image, preview and artwork information
remain unchanged. The app does not silently choose a different colour.
Previously sent or uploaded works remain excluded; a small colour selection
can eventually be exhausted.

Choose another colour or **any**. The log distinguishes a run without a match
from a source failure. Because search time and request counts are bounded,
one run without a match does not necessarily mean that every work of that
colour is permanently excluded.

The existing **Prefer 16:9** option may fall back to a landscape image with
margins, but never to a different colour. **contain** remains the recommendation
to preserve the complete artwork without cropping.

## Other sources and optional helpers

The new colour selection applies only to Commons. Chicago, Cleveland and your
own images do not gain a colour filter; a colour wish set for those sources
is reported in the log as not applied.

The other sources remain available. The card below is deliberately configured
for Commons and does not offer a source switch. If you change the source in
the app's configuration, the colour selected on the card does **not** apply
there. That is why the dropdown is labelled **Colour wish (Commons only)**.
A future dashboard source selector would need to hide irrelevant filters
according to the selected source; the last displayed artwork does not reliably
identify the next source.

An optional colour helper can control the same selection from the dashboard.
It is not needed for the normal setup. The app understands **Blau**, **Blue**
and **color_blue** as the same value. Multiple colours in one value are not
interpreted as a combination. Without a helper, the app's single colour field
is enough.

## Colour picker directly on the dashboard

**Optional; available from 0.1.0b6.** Your existing standard card works without
this step. No HACS or new script is needed; the new Dropdown helper is only
required for dashboard colour selection.

1. Open **Settings → Devices & services → Helpers → Create helper → Dropdown**.
   Set its name to `Frame Gallery Colour`.
2. Add these options individually, exactly as shown, one per option:
   `any`, `Red`, `Orange`, `Yellow`, `Green`, `Blue`, `Purple`, `Pink`, `Brown`,
   `Beige`, `Gray`, `Black`, `White`. `any` means all colours. German colour
   names are also understood; all guides consistently use these English values
   so translating the guide does not change the setup.
3. Save and check the actual entity ID: open the helper → **⋮ → Details**.
   Expected: `input_select.frame_gallery_colour`. An existing entity with the
   same name may cause a different ID.
4. In **Frame Gallery → Configuration**, enter this ID under **Colour helper**
   (`color_helper`). If hidden, enable **Show unused optional configuration
   options**. Keep Commons as the source and save.
5. Set the helper to `any`. Use the entire block below in your card; replace
   any different camera, timer, script and helper IDs everywhere they occur.

The colour picker takes precedence over the app's saved colour wish.
Changing it does **not** automatically start a run: first choose a colour,
then tap the image. A change during a running request applies to the next
start. If the helper cannot be read, the app falls back to its saved selection
and reports this in the log. Selecting multiple colours at once is not offered.

### Complete card with preview and colour picker

Reuse the camera, timer and script from the standard guide.
YAML does **not** create the helper; complete the five steps above first.
All cards use built-in Home Assistant components.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
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

The optional artist/title card can remain separately below it. Without an
additional dashboard extension, this is visually a group of native cards,
not a specially programmed single card.

**Quick check after updating:** select `Blue`, tap the image and wait for the
run to finish. Then select `any` and tap again. If no unsent work matches,
the image and artist information remain unchanged and the run still ends.
The dropdown may remain visible while the run is active.
