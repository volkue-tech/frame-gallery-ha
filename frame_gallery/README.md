# Frame Gallery

Fresh artwork on your Samsung Frame — from Home Assistant, with one tap.

![Actual Frame Gallery dashboard: colourful geometric artwork by Theo van Doesburg, a tap-to-load preview and optional artwork information.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/dashboard-commons.png)

*Actual Green screenshot; the dashboard is optional and set up separately. Theo van Doesburg, [Counter-composition XVI](https://commons.wikimedia.org/w/index.php?curid=3817033), Wikimedia Commons reproduction with public-domain metadata checked on 2026-10-05. The user confirmed this work on the TV. The screenshot is historical b3 evidence, not a new-release live test.*

- Choose 1000 curated near-widescreen works from Wikimedia Commons, museum artwork from the Art Institute of Chicago or Cleveland Museum of Art, or your own JPEG/PNG images. No API key is needed. Commons is first/default on new installations; updates retain your saved source.
- For Commons, optionally choose one colour. It must occupy a noticeable part of the work, not necessarily the largest area. `any` keeps all colours. The other sources remain available but do not apply this colour wish.
- From b7, optionally choose a Commons artist, alone or combined with colour. Use an offered catalogue label/key; other sources report this filter as ignored.
- Show the whole work without cropping by default. Previously sent works are skipped while new eligible works remain.
- Start from the app page, an automation, or an optional dashboard card with a preview of the latest successful upload.
- Optionally add title, artist and museum below the preview with built-in cards and one Text helper; the standard card stays minimal.
- Install on Home Assistant OS, including Green. No SSH, Docker setup, HACS, or edits to `configuration.yaml`.

**First start:** enter your TV's fixed private IPv4 address in **Configuration**, save, keep **Watchdog off**, and start the app with the TV on. Accept the TV's connection prompt within 20 seconds. With **Background mode off** (the default), the app stops after each run by design.

**Next:** open the **Documentation** tab for the setup guide and complete dashboard examples. The dashboard is not installed automatically. Setup is available in [English](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/DOCS.md#installation), [Deutsch](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/SETUP.de.md) | [Français](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/SETUP.fr.md) and [Español](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/SETUP.es.md) | [Italiano](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/SETUP.it.md).

**Optional colour dropdown:** [English](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_COLOUR.md) | [Deutsch](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_COLOUR.de.md) | [Français](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_COLOUR.fr.md) | [Español](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_COLOUR.es.md) | [Italiano](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_COLOUR.it.md). Add one helper and reuse your camera, timer and script; no extra dashboard extension is needed. Guides are selected manually; from b7 the app form follows the HA interface language with English/German/French/Spanish/Italian names and help. Technical values remain English. Art-style filtering is not available.

**For Commons:** select `wikimedia_commons`, keep Landscape only on and Image fit `contain`. Sources are within 2.5% of 16:9; leave Prefer 16:9 on for the closest matches or turn it off for the whole curated selection. Small margins can remain, without cropping. Your existing dashboard still works. See the [collection and rights notes](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS.md).

**Public beta 0.1.0b8.** Matching public sources, native ARM/Intel validators and actual publisher images, anonymous pulls/imports and independent signatures passed. [Validation scope](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA8_VALIDATION.md). No b8 Green/TV migration, sustained polling or new frontend-language test is claimed. Artist and colour must both match; no match keeps the previous image/information and ends cleanly, without widening the selection or resetting history. Historical hardware checks remain separate. Compatibility with every Frame model is not guaranteed. Update without uninstalling.

**Optional current-TV artwork (b8):** [show verified current title and artist](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/CURRENT_ARTWORK.md), with five-language guides and no extra dashboard extension/helper. Experimental background mode is off by default; read-only connections may wake a sleeping TV, and natural no-motion sleep remains untested. Existing cards work with the mode off; their preview/caption still means last delivered, not a live TV image.

Frame Gallery is an independent project, not affiliated with or endorsed by Samsung, the museums, or Home Assistant.

**Optional artist picker (b7 and newer):** complete native cards in [English](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_ARTIST.md) | [Deutsch](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_ARTIST.de.md) | [Français](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_ARTIST.fr.md) | [Español](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_ARTIST.es.md) | [Italiano](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_ARTIST.it.md). Existing cards and history remain unchanged; update before configuring artist options on b6.
