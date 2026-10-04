# Optional artwork information

**Available in 0.1.0b2 and newer; not available in 0.1.0b1.** Update the existing
app from its Info tab — do not uninstall it or reset its history. Its configuration
must include **Dashboard artwork information** (`artwork_info_helper`).

The [standard dashboard card](DOCS.md#dashboard) remains the
recommended starting point. It needs no artwork-information helper. This
optional addition shows the title, artist and museum in a separate native
information card beneath the image. No HACS, custom dashboard extension, SSH or
`configuration.yaml` change is needed.

![Actual native Frame Gallery preview with artwork title, artist and museum](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/dashboard-artwork-info.png)

*Actual b2 dashboard screenshot after a Core restart, not a mockup. The German
button label is editable. Artwork: Martin Johnson Heade,
[Magnolias on Light Blue Velvet Cloth](https://www.artic.edu/artworks/100829),
Art Institute of Chicago. Its official API record marks the work public domain.
This screenshot verifies the dashboard, not the physical TV display.*

## 1. Create one Text helper

In Home Assistant, open **Settings → Devices & services → Helpers → Create
helper → Text**. Enter the name, then expand **More options** (**Weitere
Optionen** in German) to see the length and display-mode settings. The default
maximum is **100**, which must be changed to **255** before saving. Enter:

| Setting | Value |
| --- | --- |
| Name | `Frame Gallery Artwork` |
| Minimum length | `0` (the app must be able to clear the caption) |
| Maximum length | `255` |
| Initial value | Leave unset; do not set a fixed initial value |
| Display mode | Text, not Password |

Home Assistant creates an entity for this helper. The expected ID is
`input_text.frame_gallery_artwork`, but an existing name can cause a suffix.
Open the helper's entity, then **⋮ → Details**, to check and copy its actual
entity ID. Its display name and its technical ID are different things.

Leaving **Initial value** unset allows Home Assistant to restore the helper's
previous value after a restart. Do not type artwork details into this helper:
the app owns its small JSON value. Use a dedicated helper, not one used for
filtering, automations or another app.

Some Home Assistant versions do not offer an Initial value field in this
dialog; in that case there is nothing to enter. After creating the helper,
open its settings and **More options** once to confirm that the saved maximum
really is **255**.

## 2. Connect the helper to Frame Gallery

Open **Settings → Apps → Frame Gallery → Configuration**. Enable **Show unused
optional configuration options** (**Nicht verwendete optionale
Konfigurationsoptionen einblenden** in German) if the field is hidden. If you
just upgraded and it is still missing, reload this browser page once.
Enter the copied ID in **Dashboard artwork information** and save. Also confirm
that **Dashboard loading timer** contains your existing timer's ID; creating
the timer or script alone does not connect app-completion feedback.
The underlying artwork-information option is
`artwork_info_helper`. The app does not create or rename the helper for you.

The next successful artwork delivery fills the helper automatically, using
metadata that the museum already supplied. There are no extra museum requests.
It does not immediately backfill a picture from an earlier app run.

For museum artworks, available title/artist fields and the museum are shown.
Missing fields are omitted, not guessed. Local images use the filename stem as
their title and have no inferred artist. Long text may be shortened with an
ellipsis to fit the helper's 255-character state limit.

## 3. Add the optional card

Reuse the preview camera, timer and script from the standard setup. Do not
create duplicate versions of them. In your dashboard, choose **Edit dashboard
→ Add card → Manual** and paste the **whole** block below.

Check these four IDs before saving:

- Camera: `camera.frame_gallery_preview` — select your actual preview camera.
  If you originally accepted the default Local File name, it may instead be
  `camera.local_file`. Changing a display name does not necessarily change its ID.
- Script: `script.frame_gallery_new_artwork`.
- Timer: `timer.frame_gallery_run`.
- Text helper: `input_text.frame_gallery_artwork` — replace **all occurrences**
  if yours differs, including the one inside the template.

This is a complete stack containing the original picture card, the existing
loading message and the optional information card. It uses only built-in Home
Assistant cards. On GitHub, use the code block's copy button; alternatively,
open [the complete YAML file](examples/artwork-info-card.yaml).

```yaml
type: vertical-stack
cards:
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
  - type: conditional
    conditions:
      - condition: state
        entity: timer.frame_gallery_run
        state_not: active
      - condition: state
        entity: input_text.frame_gallery_artwork
        state_not: ""
      - condition: state
        entity: input_text.frame_gallery_artwork
        state_not: unknown
      - condition: state
        entity: input_text.frame_gallery_artwork
        state_not: unavailable
    card:
      type: markdown
      content: >-
        {% set info = states('input_text.frame_gallery_artwork') | from_json(default={}) %}
        {% if info is mapping %}
        <div>{% if info.title is string and info.title %}<b>{{ info.title | e }}</b><br>{% endif %}{% if info.artist is string and info.artist %}{{ info.artist | e }}<br>{% endif %}{% if info.museum is string and info.museum %}<small>{{ info.museum | e }}</small>{% endif %}</div>
        {% endif %}
```

For German labels, change `Load new artwork` to `Neues Kunstwerk laden` and
`Updating artwork…` to `Kunstwerk wird geladen …`. Do not translate entity IDs.
The artist, title and museum are displayed as escaped text, never as executable
markup or links supplied by a provider.

## What to expect

- Tap the image to request the next artwork, exactly as before. The caption is
  hidden while the loading timer is active.
- When there is no matching artwork or the TV delivery fails, the previous
  preview and information remain unchanged.
- Before replacing the preview, the app clears the old caption. If that fails,
  it retains the previous preview rather than knowingly publishing an image
  with the wrong caption. The new artwork may already be on the TV; the log
  reports a preview warning.
- If the preview updates but writing its new caption fails, the caption normally
  stays empty. A lost response can also mean Home Assistant has already applied
  the correct new caption; the app does not know this and reports a warning.
  It never deliberately restores the previous caption. The app does not retry
  authentication after an HTTP 401/403 or extend its existing run budget.
- Home Assistant updates its camera and helper asynchronously. Brief browser
  refresh differences are possible; this is not an atomic image/text UI update.
- Without this option, image-only operation is unchanged. To disable it, remove
  the option value and remove the optional information card; the helper need
  not be deleted. Removing only the card does not disable helper writes.

If nothing appears, first confirm that your installed version has the new
option, then check the helper ID, minimum `0`, maximum `255`, and the app log.
Do not share a camera Details screenshot without removing its access token.
Live rendering, two successive deliveries, browser reload, no-match retention,
safe configuration-error retention and helper/preview restoration after one
Core restart passed on the approved Green update. Physical TV display confirmation
is deferred by the user. See [the exact validation scope](../BETA2_VALIDATION.md).
