# Frame Gallery

> **0.1.0b6 public beta:** [1000 near-widescreen Wikimedia Commons works](COMMONS.md), one optional Commons colour wish and a [native dashboard colour picker](COMMONS_COLOUR.md).
> No API key is needed. Update without uninstalling; your saved sources and
> existing camera, timer, script and optional artwork-information helper still work.

**Colour-picker guide:** [English](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_COLOUR.md) | [Deutsch](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_COLOUR.de.md).
These are separate guides; their language is not selected automatically by Home Assistant.

One start, one fresh artwork on your Samsung Frame. Choose museum artwork or your own images, preserve the whole work without cropping by default, and optionally see the latest successful preview on your Home Assistant dashboard.

![Product illustration: a framed TV and its optional dashboard preview. Not a screenshot.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/frame-gallery-overview.png)

*Illustration, not a screenshot. The dashboard is optional and is configured separately; installation does not add a card automatically.*

> Native ARM/Intel validators and actual publisher images, public sources, anonymous pulls and independent signatures passed for b6. [Release checks](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA6_VALIDATION.md). No new Green/TV live test is claimed. The preceding b3 passed two Commons deliveries and preview/text/loading/cleanup on Green, with physical TV confirmation of the second work. [Historical b3 evidence](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA3_VALIDATION.md). Compatibility with every TV model is not guaranteed.

**Start here:** [Install](#installation) → [Show your first artwork](#first-start-and-pairing) → [Add the dashboard card](#dashboard).

**More:** [Options](#options) · [Your own images](#your-own-images) · [Common questions](#common-questions) · [Log messages](#reading-the-log) · [Limitations](#good-to-know).

Frame Gallery is an independent project. It is not made, endorsed, or supported by Samsung, by the museums, or by Home Assistant.

## Before you start

- **Home Assistant OS** with Supervisor/apps (formerly add-ons), for example a Home Assistant Green, with Home Assistant 2026.2 or newer. Home Assistant Container and Core-only installations cannot run apps.
- **A Samsung Frame TV** on the same home network (the same subnet) as Home Assistant.
- **A fixed address for the TV.** Reserve the TV's IPv4 address in your router (a DHCP reservation). The app needs the address itself, such as `192.168.1.20`; a name like `tv.local` is not accepted.
- **On the TV:** under the connection settings for external devices, set the access notification to *First Time Only*, so that the TV asks for permission only once.

No SSH, no command line, and no change to `configuration.yaml` is needed at any step.

## Installation

[Add the repository to Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fvolkue-tech%2Fframe-gallery-ha), or use `https://github.com/volkue-tech/frame-gallery-ha` in the repository dialog. Installation downloads the already built image; your Green does not compile the app or need SSH. This path passed a separate public Green installation.

1. Use [Add to Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fvolkue-tech%2Fframe-gallery-ha), or paste `https://github.com/volkue-tech/frame-gallery-ha` in **Settings → Apps → App store → ⋮ → Repositories**. This is an app repository, not a HACS integration.
2. Open **Frame Gallery – Samsung Frame TV** in the app store and select **Install**. You can search for **Samsung** or **Frame Gallery**. Home Assistant downloads the image for your device (`aarch64` for the Green, `amd64` for a PC).
3. Open the **Configuration** tab, enter the TV's address under **TV address**, and select **Save**. For the first test, keep the remaining defaults; there is no API key to obtain and no need to configure advanced options.
4. Leave **Watchdog** off: the app runs once per start and then stops by design, which the watchdog would take for a crash.

You can use Frame Gallery immediately from its app page. No dashboard setup is needed for the first test.

### Simple configuration (0.1.0b6)

The normal form has six fields: **TV address**, **Artwork source**, **Colour wish (Commons)**, **Landscape
only**, **Prefer 16:9**, and **Image fit**. The German UI uses **TV-IP-Adresse**,
**Bildquelle**, **Farbwunsch (Commons)**, **Nur Querformat**, **16:9 bevorzugen**, and **Bildanpassung**.
Configuration keys stay unchanged, so updates retain existing settings.

For the curated wide artworks choose `wikimedia_commons`, keep Landscape only on
and choose `contain` (the complete artwork, no crop). Sources are within 2.5% of
16:9; Prefer 16:9 still uses the stricter approximately 1% threshold. Leave it
on for the closest matches, or turn it off for the whole selection. Small
margins can remain. No API key, registration or additional dashboard setup is needed.

Museum period/department filters, margin colour and dashboard helpers are
optional. Enable **Show unused optional configuration options** only when you
need one. Period applies to Chicago/Cleveland; department only to Cleveland.
Commons supports the single colour wish, not period/department/style filters.
Choose `any` or one of Red, Orange, Yellow, Green, Blue, Purple, Pink, Brown,
Beige, Gray, Black and White. A noticeable area (about 5%) qualifies; it need
not dominate the image. A blue-yellow work can match either group. Other
sources report colour as ignored. No new matching work means a clean stop,
keeping the previous artwork, never a silent different-colour fallback.
See [colour selection and the optional dashboard picker](COMMONS_COLOUR.md).

On an upgrade previously saved optional values can remain visible. This is
normal; saved filters and helper IDs are not silently deleted or reset. An
unset optional field uses the same defaults as before: no museum filter and
black margins. Do not enable automatic startup or the watchdog for this one-shot app.

## First start and pairing

1. Make sure the TV is on.
2. Start the app on its **Info** tab and watch the **Log** tab.
3. When the app reaches the TV for the first time, the TV shows a prompt asking whether to allow the connection. **Accept it within 20 seconds.**
4. If the log ends with `outcome=tv_not_authorized`, the prompt was not accepted in time: start the app again and accept it. Once the log shows `outcome=delivered`, the TV is paired, and later starts need no prompt.

The pairing key the TV issues is stored in the app's private data and is excluded from Home Assistant backups; the app-only development backup check confirmed the configured exclusions. Fresh TV authorization was not reset during the development tests, so first-time pairing on every TV model is not claimed as verified.

## Dashboard

**Optional — your TV already works without this.** Continue here only when you
want a preview and a convenient button in your dashboard. The one-time setup
creates three named things: a preview camera, a loading timer and a script.
They have different jobs; none is a physical camera or a second installation.

![Actual working Frame Gallery card with Theo van Doesburg's colourful Counter-composition XVI and optional artwork information. Tap the preview to start another run.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/dashboard-commons.png)

*Actual historical b3 Green screenshot; optional artwork information is shown too. This installation uses a German label; you can choose your own card name. Artwork: Theo van Doesburg, [Counter-composition XVI](https://commons.wikimedia.org/w/index.php?curid=3817033), Wikimedia Commons reproduction with public-domain metadata checked on 2026-10-05. The complete examples below use generic entity IDs for a new setup; the text card remains optional.*

**Tap the preview to request new artwork.** The example labels the image **Load new artwork** so first-time users can see that it is a button, not just a picture. During a run, the card adds an "Updating artwork…" note; afterward it shows the latest successful preview. Holding the image opens the camera's more-info view. A failed run keeps the previous preview.

The card uses only built-in Home Assistant components: no HACS, Mushroom or custom button card. It is not added automatically. Set it up once with a preview camera, a timer, a script and the complete card below. All of these are created through the user interface, not `configuration.yaml`.

Use an administrator account for setup and for starting the app. The entity IDs below are the expected ones; check them in **Settings → Devices & services → Entities** and adjust the YAML if yours differ. The observed public app ID is `a94fc569_frame_gallery`. Check the app-page URL if yours differs; do not use a local development slug.

**Copying the examples:** copy each entire YAML block, preserving its indentation. On GitHub, move the pointer over the block and use its top-right copy button. If your Home Assistant Documentation tab offers no copy button, [open this guide on GitHub](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/DOCS.md#dashboard). Do not copy the surrounding instructions or the Markdown backtick fences.

### 1. Create and name the preview camera

Start the app once successfully so the preview file exists. Then open **Settings → Devices & services → Add integration → Local File**.

![Actual Home Assistant Local File setup dialog in German, with the Name and File path fields. Replace the default Local File name with Frame Gallery Preview and enter the preview path below.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/local-file-setup.png)

*Actual setup dialog, before filling it in. **Name** is the name of the new entity; **Dateipfad** means File path. Replace the displayed default `Local File` — do not leave it unchanged. The screenshot uses German; the values below are the same in every UI language.*

In the setup dialog, fill in **both** fields before selecting **OK**:

| Field | Enter |
| --- | --- |
| Name | `Frame Gallery Preview` — replace the default `Local File` |
| File path | `/media/frame_gallery/preview/latest.jpg` |

**This creates the preview camera automatically.** It is not a physical camera: Home Assistant uses a camera entity to display the image file. The integration page may still be headed **Local File**. Its **1 entity** link means setup succeeded, not that another setup step is required.

The name makes the preview recognizable in entity lists and dashboard pickers. The expected technical ID is `camera.frame_gallery_preview`, but naming conventions or an existing entity can produce a different ID. Check it once:

1. On the **Local File** integration page, select **1 entity** (**1 Entität** in German).
2. This opens a filtered entity list. Select the row **Frame Gallery Preview** — or **Local File** if you kept the default name.
3. The image opens. Select the top-right **⋮ → Details**.
4. Copy the **ID** from the Entity section. Also check that **File path** is `/media/frame_gallery/preview/latest.jpg`.

**Already created it as Local File?** Reuse it; do not delete and recreate it. From the image window, select the **cog icon** to open the entity settings. Set the display name to `Frame Gallery Preview`. If you also want the example's ID, separately set **Entity ID** to `camera.frame_gallery_preview`, provided it is unused, and select **Update**. Changing the display name alone does not rename an existing ID. If you change the ID, update any existing cards, scripts or automations that reference it. See [Home Assistant's entity naming guide](https://www.home-assistant.io/docs/configuration/customizing-devices/).

Alternatively, keep an ID such as `camera.local_file` and use that exact ID instead of `camera.frame_gallery_preview` in the complete card below. In the visual card editor, the **Entity** picker shows the display name and thumbnail, not necessarily the technical ID: choose **Frame Gallery Preview**, or **Local File** if you left its name unchanged.

If this file path is already configured, reuse its existing camera entity; Home Assistant refuses a duplicate Local File integration for the same path. Multiple app installations share this latest-preview path but retain separate private histories.

**Screenshot privacy:** the Details view also contains camera access tokens and a token-bearing image URL. Do not share the entire attributes section. For support, copy only the entity ID and file path, or share a screenshot showing only those safe fields.

### 2. Create the loading timer

Open **Settings → Devices & services → Helpers → Create helper → Timer**. Name: `Frame Gallery run`. Duration: `0:02:30`. Expected entity: `timer.frame_gallery_run`.

In the app's Configuration tab, set **Dashboard loading timer** (`loading_timer`) to this exact entity ID. Enable **Show unused optional configuration options** if the field is hidden. Creating the timer or script alone does not connect completion feedback. Use a separate timer for each app. The app cancels it after cleanup; expiry remains the fail-safe if completion cannot be reported.

### 3. Create the script

Open **Settings → Automations & scenes → Scripts → Create script → ⋮ → Edit in YAML**, paste the following, and save. Expected entity: `script.frame_gallery_new_artwork`.

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

### 4. Add the dashboard card

Once the camera, timer and script are ready, edit a dashboard, add a card, choose **Manual**, and paste the whole block. If any of your entity IDs differ, replace the corresponding IDs throughout the examples before saving:

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
```

**Try it:** save the card and tap its image once. The TV should receive a new work and the card should update to the latest successful preview. The loading note is only shown while the timer is active; it is normal for the card to show just the image and its label when idle. Hold the image to open a larger preview. Margins in the preview preserve the complete artwork rather than cropping it.

The visible label is not an entity ID: you can translate `Load new artwork` to `Neues Kunstwerk laden`, and `Updating artwork…` to `Kunstwerk wird geladen …`, without renaming the camera, timer or script.

**Card editor check:** if the image is missing or Home Assistant reports "Entity not found", check the camera ID using the steps above. Do not create another Local File integration for the same path. The editor's preview of the loading note is not proof that an artwork run is active; check the timer and app log outside the editor.

**Loading behavior:** the app ends the explicitly configured timer after cleanup on delivery, no-match or graceful cancellation. Idle means finished, not necessarily successful; check the app log for its outcome. Failed start, hard kill or a failed notification leaves loading bounded by the timer's 150-second expiry. Preview refresh is independent. No running-state sensor is required.

**Optional artwork information (0.1.0b2 and newer):** the unchanged standard card above
needs no extra helper. A separately prepared native card adds title, artist and
museum below it: [complete artwork-information setup](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/ARTWORK_INFO.md).
This feature is not in **0.1.0b1**. Update the existing app without uninstalling it,
then connect one dedicated Text helper through **Dashboard artwork information**.
The guide includes the complete native card and the saved helper length settings.
No HACS extension is needed.

**Optional colour picker (0.1.0b6 and newer, Commons only):** keep the standard
card if you prefer a minimal setup. To choose a colour directly on the dashboard,
follow the [complete native colour-card guide](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_COLOUR.md).
It is available in [English](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_COLOUR.md) and [Deutsch](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_COLOUR.de.md), with complete copy-and-paste cards in both languages.
It adds one Dropdown helper through the UI, connected by `color_helper`, and
reuses the same camera, timer and script. Select a colour, then tap the preview;
changing the dropdown alone does not start a run. Other sources do not apply it.

**A new artwork every morning (optional).** **Settings → Automations & scenes → Create automation → ⋮ → Edit in YAML**:

```yaml
alias: Frame Gallery every morning
description: Shows a new artwork at 07:30.
triggers:
  - trigger: time
    at: "07:30:00"
actions:
  - action: script.turn_on
    target:
      entity_id: script.frame_gallery_new_artwork
mode: single
```

## Options

| Option | What it does | Default |
| --- | --- | --- |
| TV address | The TV's IPv4 address. Only private home-network addresses are accepted. | none: required |
| Artwork source | `wikimedia_commons` (1000 near-widescreen works; no key), `art_institute_chicago`, `cleveland_museum_of_art`, or `local_media` (your own images). | `wikimedia_commons` |
| Department (Cleveland only) | A department of the Cleveland Museum of Art, or `any`. | `any` |
| Period (both museums) | `period_before_1400`, `period_1400_1599`, `period_1600_1799`, `period_1800_1899`, `period_1900_and_later`, or `any`. | `any` |
| Colour wish (Commons only) | `any` or Red, Orange, Yellow, Green, Blue, Purple, Pink, Brown, Beige, Gray, Black, White. A noticeable colour area qualifies. | `any` |
| Landscape only | Only choose works that are wider than they are tall. | on |
| Prefer the TV's shape | Prefer works within about 1 % of the TV's 16:9 shape. | on |
| Fit | `contain` shows the whole work with margins; `cover` fills the screen and may crop. | `contain` |
| Margin colour | The margin colour in `contain` mode, as `#RRGGBB`. | `#000000` |
| Source, department, period, and colour helpers | Optional helpers whose state replaces the matching option at every start (see below). | empty |
| Log detail | `info`, or `debug` for every candidate the app considered. | `info` |

Version 0.1.0b5 and newer put **Wikimedia Commons first** and select it for new
installations. Updates retain your saved source: choosing Chicago, Cleveland
or your own images will not be undone. To switch an existing installation,
select `wikimedia_commons` and save.

The full list of department and period values, with their labels and the other spellings the app accepts, is in [the vocabulary guide](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/VOCABULARY.md).

**Recommended starting point:** keep the default landscape selection, screen-shape preference and `contain` fitting. If the bounded search finds no new work near 16:9, it can fall back to a landscape work with margins. `contain` still preserves the whole work; `cover` is the option that can crop. Google Arts & Culture is not a source in this app.

### Which filter works with which source

| Filter | Your own images | Art Institute of Chicago | Cleveland Museum of Art | Wikimedia Commons |
| --- | --- | --- | --- | --- |
| Department | not supported | not supported | supported | not supported |
| Style | not supported | not supported | not supported | not supported |
| Period | not supported | supported | supported | not supported |
| Colour | not supported | not supported | not supported | one colour family |
| Landscape only, the TV's shape, fit | supported | supported | supported | supported |

A filter that the chosen source does not support is not applied. The app says so in its log, in its last line (`ignored_filters=…`), and in its run record; it never pretends to apply it. A value that is not on the lists above is refused: the run ends at once with `outcome=config_invalid`, and the log names the option.

### Changing filters from the dashboard (optional)

Each filter option has a matching helper option. Create a dropdown helper (**Settings → Devices & services → Helpers → Create helper → Dropdown**) whose options are values from the lists above, and enter its entity ID, for example `input_select.frame_gallery_source`, in the helper option. At every start, the app reads the helper's state and uses it instead of the option. If the helper is missing, unavailable, or holds an unknown value, the app uses the option instead and writes a warning to its log.

## Your own images

Put JPEG and PNG files into the folder `frame_gallery/library` of Home Assistant's media, for example with **Media → My media → frame_gallery → library → Upload** (to be confirmed in the supervised test). The app creates the folder the first time it runs with your own images as the source. It looks at most four folder levels deep and at most 20 000 entries, skips hidden files, links, and files over 40 MiB, and lists the files it skipped in one warning. The preview folder is never used as a source.

## Common questions

**Why does the app say "Stopped" after showing a picture?** That is normal. Each start sends one work, updates the preview and exits. Start it again for another work; leave Watchdog off.

**Will the TV image be cropped?** Not with the default `contain` setting. When proportions differ, margins appear. The app prefers works near 16:9 and can fall back to other landscape works. Choose `cover` only if cropping is acceptable.

**Why is the previous picture still on the card?** The preview changes only after a successful upload and preview publication. Check the app's final log line first. If delivery succeeded but the preview failed, follow the warning in the log. Also verify the camera's file path and the card's entity ID. The native camera refresh can take a short while; loading completion and preview refresh are separate.

**Why is "Updating artwork…" still visible?** Check that the app's **Dashboard loading timer** option matches the timer in your script and card. The note expires after 150 seconds even if the app cannot report completion. A disappearing note is not proof of delivery: check the log.

**No artwork was found. What now?** For Commons, try a different colour or `any`; a small colour pool can be exhausted by already-sent works. For museums, try a broader period or Cleveland's `any` department. A bounded search may not find a match on every run. The app keeps the previous image and stops cleanly; it does not search forever or silently choose another colour. See `no_match` below.

**Can I filter by colour or style, or use Google Arts & Culture?** From b6, Commons supports one colour wish and an optional native dashboard dropdown. Chicago supports period; Cleveland supports department and period. Those sources and local images do not apply the Commons colour wish. Art-style filtering is unavailable, and Google is not one of the sources.

**Do old pictures accumulate on Home Assistant?** Downloaded and prepared images are temporary and are cleaned up. The app retains the latest preview, bounded history and metadata, not an ever-growing archive of artwork downloads. Your own media library is left untouched. Pictures uploaded to the TV do stay on the TV; this app does not delete them.

**Still stuck?** [Open an issue](https://github.com/volkue-tech/frame-gallery-ha/issues) with your app version, TV model and final log outcome. Remove private details, pairing tokens, passwords and access tokens before sharing logs.

## Reading the log

Every run ends with one line such as `outcome=delivered exit=0 elapsed=23.4`. What the outcomes mean:

| Outcome | Meaning | What to do |
| --- | --- | --- |
| `delivered` | The TV shows the new artwork. | Nothing. |
| `delivered_with_warnings` | The TV shows it, but the preview or a record could not be written. | Check that Home Assistant's media storage is available. |
| `delivered_unrecorded` | The TV shows it, but the history could not be saved. | Check the free space of the Home Assistant system. The work is still not sent again. |
| `no_match` | Nothing new matched. The last line has a hint: "filters too restrictive", "nothing new left for these filters", "search limits reached", or, for your own images, "no usable JPEG or PNG images in /media/frame_gallery/library". | Loosen the filters, or add images (for your own images: JPEG or PNG files in that folder). "Search limits reached" can work on the next start. |
| `config_invalid` | An option is invalid; the log names it. | Correct the option and save. |
| `tv_unreachable` | The TV did not answer, or the connection broke. | Check that the TV is on and on the same subnet, and that its address is right. |
| `tv_not_authorized` | The pairing prompt was not accepted in time, or the TV refused the stored key. | Start again and accept the prompt within 20 seconds. |
| `tv_rejected` | The TV does not support art mode for this app, or refused the artwork. | Check that it is a Frame TV in art mode. |
| `deadline_exceeded` | Too little time was left to finish safely. With the hint "paired; start the app again", pairing worked. | Start the app again. |
| `source_failed` | The museum could not be reached or answered unexpectedly. | Try again later. |
| `image_failed` | No candidate could be prepared. | Try again; for your own images, check the files. |
| `already_running` | Another run was still active. | Wait, then start again. |
| `state_error` | The app's saved state could not be read or written, for example a full disk. | Check the free space. |
| `cancelled` | The app was stopped during the run. | Nothing; start it again when you like. |
| `internal_error` (exit 70) | A program error. | Please report it with the log. |
| `watchdog_termination` (exit 71) | The run took longer than its hard limit of 130 seconds and was ended. | Please report it with the log. |

## Good to know

- **A run is short and bounded.** A run takes at most two minutes; one that finds nothing to show ends within 70 seconds.
- **Very old works can come back.** The app remembers the latest 20 000 artworks it showed. Older ones are forgotten, so a very old artwork could in theory be shown again. At one artwork a day, that takes about 55 years.
- **An uncertain upload waits 30 days.** If the connection breaks during an upload, the app cannot know whether the TV received the work. It then leaves that work out for 30 days rather than risk sending it twice.
- **Art Institute images can look soft.** The museum offers images 1686 pixels wide, so they are enlarged up to about 2.3 times for a 4K screen. Cleveland's images are 3400 pixels wide and look sharper.
- **Filters depend on the source.** Commons offers one colour wish; the Art Institute offers period, and Cleveland department and period. Museums and local images do not apply the Commons colour wish. No art-style filter is offered. Unsupported filters are reported as ignored.
- **Some TVs are not supported yet.** TVs whose art interface reports version 0.97 are refused (`tv_rejected`) in this version, because the library the app uses could send an image twice to them.
- **The connection to the TV is not certificate-checked.** The TV's local interface uses a certificate that cannot be verified; whether to pin it is decided after the supervised test. Keep the TV's address reserved in your router.
- **Another app uploading at the same moment** could, in rare cases, make the TV show that app's image instead; your artwork is still stored on the TV and is not sent again.
- **Old artworks stay on the TV.** The app does not delete earlier uploads from the TV's memory.
- **Isolation is enforced by design.** The parent and workers use enforced AppArmor profiles. Image workers additionally cannot create network sockets; the TV worker can use IPv4 TCP, not UDP. These restrictions were tested in the separate development app on the Green. The public installation's protection/profile settings and stored profile bytes were checked, and normal runs succeeded; its kernel negative probes were not repeated.

## Starting over

There is no button to make the app forget what it has shown, and you need none to pair the TV again: when the TV refuses the stored pairing key, the app deletes it, and the next start asks the TV again.

To start over completely, uninstall the app and install it again. Uninstalling removes the app's private data: the list of works already sent, the record of uploads, the cache, and the pairing key (to be confirmed in the supervised test). The artworks already on your TV and the last preview in your media folder stay where they are.

## Privacy

- The app sends nothing about you, your images, your configuration, or your TV to any third party, and it has no analytics.
- It contacts only the source you selected (a museum or Wikimedia Commons and its image host), your TV on your home network, and, if you use helpers or the loading timer, Home Assistant itself. The selected source sees normal request metadata, including your public IP address.
- Source requests carry the app's name, version, and a project contact address. Commons uses its dedicated project contact; users need no account or API key.

## Licences

The project's own code is licensed under the Apache License 2.0. The app image also contains third-party software under its own licences, among them the LGPL-3.0 library `samsungtvws`, LGPL-2.1-or-later code inside the Pillow image library, and parts of the Alpine Linux system the image is built on that are under the GPL, such as BusyBox (GPL-2.0-only) and bash (GPL-3.0-or-later); the image is therefore not free of GPL components. The third-party notices list every component and its licence, and each release carries the corresponding source code of the copyleft components.

This software is based in part on the work of the Independent JPEG Group. Portions of this software are copyright © The FreeType Project (www.freetype.org). All rights reserved.

## Validation notes for contributors

The public beta has signed pre-built ARM/Intel images, matching component
sources, and native architecture validation. Scope and limitations are recorded
in the [Green/TV development report](https://github.com/volkue-tech/frame-gallery-ha/blob/main/PHASE8_REPORT.md)
and [public-beta report](https://github.com/volkue-tech/frame-gallery-ha/blob/main/PHASE9_REPORT.md).
This is engineering evidence, not independent legal advice or a compatibility
claim for every television.

The public app ID `a94fc569_frame_gallery` was observed on a separate Green
installation. Its two normal card-started deliveries refreshed the preview
without reload and ended loading. The complete configurations used there are
the [public beta card](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/examples/public-beta-test-card.yaml)
and [public beta script](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/examples/public-beta-test-script.yaml).
Those examples use installation-specific test entity names; for a new setup,
use the complete generic examples above and check the resulting entity IDs.

Development tests also exercised no-match, cancellation, notification failure
and the timer's expiry. One recovery run refreshed within 14 seconds of preview
publication; that observation is not a universal refresh-time guarantee.
