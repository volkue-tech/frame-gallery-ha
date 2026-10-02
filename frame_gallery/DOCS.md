# Frame Gallery

Frame Gallery sends one fresh artwork to a Samsung Frame TV each time you start it, then stops. It picks a public-domain work from the Art Institute of Chicago, an open-access work from the Cleveland Museum of Art, or one of your own images; prepares it for the TV's 16:9 screen without cropping (unless you ask for it); uploads it; shows it; and keeps a preview for your dashboard. It never shows the same work twice while unsent works remain.

> **Status: development build (0.1.0.dev0).** This is the first beta in preparation. It has not yet been tested against a real TV or on a Home Assistant Green; that happens in a supervised test before any release. The dashboard below is a draft until then.

Frame Gallery is an independent project. It is not made, endorsed, or supported by Samsung, by the museums, or by Home Assistant.

## Before you start

- **Home Assistant OS** with apps (formerly add-ons), for example a Home Assistant Green. Home Assistant Container and Core installations cannot run apps.
- **A Samsung Frame TV** on the same home network (the same subnet) as Home Assistant.
- **A fixed address for the TV.** Reserve the TV's IPv4 address in your router (a DHCP reservation). The app needs the address itself, such as `192.168.1.20`; a name like `tv.local` is not accepted.
- **On the TV:** under the connection settings for external devices, set the access notification to *First Time Only*, so that the TV asks for permission only once.

No SSH, no command line, and no change to `configuration.yaml` is needed at any step.

## Installation

The public repository and its one-click link are published with the first release. Until then, the app can be installed only as a local development copy, as described in the project's development notes (`DEVELOPMENT.md`, *Installing a local development copy*). Until images are published, Home Assistant builds the app on your device when you install it, which needs an internet connection and may take several minutes.

1. Add the repository in **Settings → Apps → App store → ⋮ → Repositories**, or use the one-click link from the release notes.
2. Open **Frame Gallery** in the app store and select **Install**. Home Assistant downloads the image for your device (`aarch64` for the Green, `amd64` for a PC).
3. Open the **Configuration** tab, enter the TV's address under **TV address**, choose your filters, and select **Save**.
4. Leave **Watchdog** off: the app runs once per start and then stops by design, which the watchdog would take for a crash.

## First start and pairing

1. Make sure the TV is on.
2. Start the app on its **Info** tab and watch the **Log** tab.
3. When the app reaches the TV for the first time, the TV shows a prompt asking whether to allow the connection. **Accept it within 20 seconds.**
4. If the log ends with `outcome=tv_not_authorized`, the prompt was not accepted in time: start the app again and accept it. Once the log shows `outcome=delivered`, the TV is paired, and later starts need no prompt.

The pairing key the TV issues is stored in the app's private data and is excluded from Home Assistant backups (to be confirmed in the supervised test).

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

The full list of department and period values, with their labels and the other spellings the app accepts, is in the project's vocabulary document.

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

## Dashboard (draft)

The dashboard shows the artwork on the TV and starts the app with a tap. It consists of a camera for the preview, a timer for the "Updating artwork…" note, a script, and a card, all created in the user interface. The entity IDs below are the expected ones; check them in **Settings → Devices & services → Entities** and adjust the YAML if yours differ. The app's ID is `local_frame_gallery` for a local development copy; the release notes name it for the public repository.

1. **Preview camera.** **Settings → Devices & services → Add integration → Local File**. Name: `Frame Gallery Preview`. File path: `/media/frame_gallery/preview/latest.jpg`. Expected entity: `camera.frame_gallery_preview`.
2. **Running sensor.** In **Settings → Devices & services → Home Assistant Supervisor**, open the Frame Gallery device and enable its **Running** sensor, which is disabled by default. Expected entity: `binary_sensor.frame_gallery_running`.
3. **Timer.** **Settings → Devices & services → Helpers → Create helper → Timer**. Name: `Frame Gallery run`. Duration: `0:02:30`. Expected entity: `timer.frame_gallery_run`.
4. **Script.** **Settings → Automations & scenes → Scripts → Create script → ⋮ → Edit in YAML**, paste the following, and save. Expected entity: `script.frame_gallery_new_artwork`.

```yaml
alias: Frame Gallery new artwork
description: Starts the Frame Gallery app and shows a note on the dashboard while it runs.
mode: single
sequence:
  - action: timer.start
    target:
      entity_id: timer.frame_gallery_run
    data:
      duration: "00:02:30"
  - action: hassio.app_start
    data:
      app: local_frame_gallery
    continue_on_error: true
  - repeat:
      sequence:
        - delay: "00:00:05"
        - action: homeassistant.update_entity
          target:
            entity_id: binary_sensor.frame_gallery_running
      until:
        - condition: template
          value_template: >-
            {{ is_state('binary_sensor.frame_gallery_running', 'on')
               or repeat.index >= 3
               or not is_state('timer.frame_gallery_run', 'active') }}
  - if:
      - condition: state
        entity_id: binary_sensor.frame_gallery_running
        state: "on"
    then:
      - repeat:
          sequence:
            - delay: "00:00:05"
            - action: homeassistant.update_entity
              target:
                entity_id: binary_sensor.frame_gallery_running
          until:
            - condition: template
              value_template: >-
                {{ is_state('binary_sensor.frame_gallery_running', 'off')
                   or repeat.index >= 27
                   or not is_state('timer.frame_gallery_run', 'active') }}
  - action: timer.cancel
    target:
      entity_id: timer.frame_gallery_run
```

5. **Card.** Edit a dashboard, add a card, choose **Manual**, and paste:

```yaml
type: vertical-stack
cards:
  - type: picture-entity
    entity: camera.frame_gallery_preview
    name: Frame Gallery
    show_state: false
    tap_action:
      action: perform-action
      perform_action: script.turn_on
      target:
        entity_id: script.frame_gallery_new_artwork
  - type: conditional
    conditions:
      - condition: state
        entity: timer.frame_gallery_run
        state: active
    card:
      type: markdown
      content: Updating artwork…
```

The note disappears when the app has finished, and at the latest after two and a half minutes: the timer always runs out on its own. Starting the app needs an administrator account.

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

**Known gap in the draft.** Whether the preview always refreshes in the browser after a new artwork is not yet proven. The supervised test on a Home Assistant Green chooses one refresh method and completes this section; until then, reload the page if the preview looks old.

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
- **The security profile is a draft.** The app runs with a restrictive AppArmor profile in a logging-only mode until it is verified before the release.

## Privacy

- The app sends nothing about you, your images, your configuration, or your TV to any third party, and it has no analytics.
- It contacts only the museum you selected (and its image host), your TV on your home network, and, if you use helpers, Home Assistant itself.
- Requests to the museums carry the app's name, version, and a project contact address, as the museums' guidelines ask.

## Licences

The project's own code is licensed under the Apache License 2.0. The app image also contains third-party software under its own licences, among them the LGPL-3.0 library `samsungtvws`, LGPL-2.1-or-later code inside the Pillow image library, and parts of the Alpine Linux system the image is built on that are under the GPL, such as BusyBox (GPL-2.0-only) and bash (GPL-3.0-or-later); the image is therefore not free of GPL components. The third-party notices list every component and its licence, and each release carries the corresponding source code of the copyleft components.

This software is based in part on the work of the Independent JPEG Group. Portions of this software are copyright © The FreeType Project (www.freetype.org). All rights reserved.
