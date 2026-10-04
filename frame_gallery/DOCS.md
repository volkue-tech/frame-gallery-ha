# Frame Gallery

One start, one fresh artwork on your Samsung Frame. Choose museum artwork or your own images, preserve the whole work without cropping by default, and optionally see the latest successful preview on your Home Assistant dashboard.

![Product illustration: a framed TV and its optional dashboard preview. Not a screenshot.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/frame-gallery-overview.png)

*Illustration, not a screenshot. The dashboard is optional and is configured separately; installation does not add a card automatically.*

> **[0.1.0b1 public beta](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b1).** Tested through a public-repository installation on Home Assistant Green and a real Samsung Frame. Compatibility with every TV model is not guaranteed.

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
3. Open the **Configuration** tab, enter the TV's address under **TV address**, choose your filters, and select **Save**.
4. Leave **Watchdog** off: the app runs once per start and then stops by design, which the watchdog would take for a crash.

You can use Frame Gallery immediately from its app page. No dashboard setup is needed for the first test.

## First start and pairing

1. Make sure the TV is on.
2. Start the app on its **Info** tab and watch the **Log** tab.
3. When the app reaches the TV for the first time, the TV shows a prompt asking whether to allow the connection. **Accept it within 20 seconds.**
4. If the log ends with `outcome=tv_not_authorized`, the prompt was not accepted in time: start the app again and accept it. Once the log shows `outcome=delivered`, the TV is paired, and later starts need no prompt.

The pairing key the TV issues is stored in the app's private data and is excluded from Home Assistant backups; the app-only development backup check confirmed the configured exclusions. Fresh TV authorization was not reset during the development tests, so first-time pairing on every TV model is not claimed as verified.

## Dashboard

![Actual working Frame Gallery public-beta card showing the complete Elephant Bridge artwork. Tap the preview to start another run.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/dashboard-preview.png)

*Actual dashboard screenshot. This installation uses a German label; you can choose your own card name. Artwork: [“Elephant Bridge” souvenir](https://www.clevelandart.org/art/1929.342), Cleveland Museum of Art, 1929.342, [CC0 Open Access](https://www.clevelandart.org/open-access). The complete examples below use generic entity IDs for a new setup.*

**Tap the preview to request new artwork.** During a run, the card adds an "Updating artwork…" note; afterward it shows the latest successful preview. Holding the image opens the camera's more-info view. A failed run keeps the previous preview.

The card uses only built-in Home Assistant components: no HACS, Mushroom or custom button card. It is not added automatically. Set it up once with a preview camera, a timer, a script and the complete card below. All of these are created through the user interface, not `configuration.yaml`.

Use an administrator account for setup and for starting the app. The entity IDs below are the expected ones; check them in **Settings → Devices & services → Entities** and adjust the YAML if yours differ. The observed public app ID is `a94fc569_frame_gallery`. Check the app-page URL if yours differs; do not use a local development slug.

1. **Preview camera.** Start the app once successfully so the preview file exists. Then **Settings → Devices & services → Add integration → Local File**. Name: `Frame Gallery Preview`. File path: `/media/frame_gallery/preview/latest.jpg`. Expected entity: `camera.frame_gallery_preview`. If this path is already configured, reuse its existing camera entity in the complete card below; HA refuses a duplicate Local File integration for the same path. Multiple installations share this latest-preview path but retain separate private histories.
2. **Timer.** **Settings → Devices & services → Helpers → Create helper → Timer**. Name: `Frame Gallery run`. Duration: `0:02:30`. Expected entity: `timer.frame_gallery_run`.
   In the app's Configuration tab, set **Dashboard loading timer** (`loading_timer`) to this exact entity ID. Use a separate timer for each app. The app cancels it after cleanup; expiry remains the fail-safe if completion cannot be reported.
3. **Script.** **Settings → Automations & scenes → Scripts → Create script → ⋮ → Edit in YAML**, paste the following, and save. Expected entity: `script.frame_gallery_new_artwork`.

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

4. **Card.** Edit a dashboard, add a card, choose **Manual**, and paste the whole block:

```yaml
type: vertical-stack
cards:
  - type: picture-entity
    entity: camera.frame_gallery_preview
    name: Frame Gallery
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

**Loading behavior:** the app ends the explicitly configured timer after cleanup on delivery, no-match or graceful cancellation. Idle means finished, not necessarily successful; check the app log for its outcome. Failed start, hard kill or a failed notification leaves loading bounded by the timer's 150-second expiry. Preview refresh is independent. No running-state sensor is required.

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
| Artwork source | `art_institute_chicago`, `cleveland_museum_of_art`, or `local_media` (your own images). | `art_institute_chicago` |
| Department (Cleveland only) | A department of the Cleveland Museum of Art, or `any`. | `any` |
| Period (both museums) | `period_before_1400`, `period_1400_1599`, `period_1600_1799`, `period_1800_1899`, `period_1900_and_later`, or `any`. | `any` |
| Colour | Only `any`: no source supports a colour filter yet. | `any` |
| Landscape only | Only choose works that are wider than they are tall. | on |
| Prefer the TV's shape | Prefer works within about 1 % of the TV's 16:9 shape. | on |
| Fit | `contain` shows the whole work with margins; `cover` fills the screen and may crop. | `contain` |
| Margin colour | The margin colour in `contain` mode, as `#RRGGBB`. | `#000000` |
| Source, department, period, and colour helpers | Optional helpers whose state replaces the matching option at every start (see below). | empty |
| Log detail | `info`, or `debug` for every candidate the app considered. | `info` |

The full list of department and period values, with their labels and the other spellings the app accepts, is in [the vocabulary guide](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/VOCABULARY.md).

**Recommended starting point:** keep the default landscape selection, screen-shape preference and `contain` fitting. If the bounded search finds no new work near 16:9, it can fall back to a landscape work with margins. `contain` still preserves the whole work; `cover` is the option that can crop. Google Arts & Culture is not a source in this app.

### Which filter works with which source

| Filter | Your own images | Art Institute of Chicago | Cleveland Museum of Art |
| --- | --- | --- | --- |
| Department | not supported | not supported | supported |
| Style | not supported | not supported | not supported |
| Period | not supported | supported | supported |
| Colour | not supported | not supported | not supported |
| Landscape only, the TV's shape, fit | supported | supported | supported |

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

**No artwork was found. What now?** Try a broader period, Cleveland's `any` department, or a different source. A bounded search may not find a match on every run. The app stops cleanly; it does not search forever. See `no_match` below.

**Can I filter by colour or style, or use Google Arts & Culture?** Not in this beta. Chicago supports period; Cleveland supports department and period. Colour and style are unavailable, and Google is not one of the sources.

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
- **Filters are limited in this first version.** The Art Institute offers only the period filter, and Cleveland the department and period filters. There are no style or colour filters yet, because the museums' documentation does not define their values.
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
- It contacts only the museum you selected (and its image host), your TV on your home network, and, if you use helpers or the loading timer, Home Assistant itself.
- Requests to the museums carry the app's name, version, and a project contact address, as the museums' guidelines ask.

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
