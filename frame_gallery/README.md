# Frame Gallery

Fresh artwork on your Samsung Frame — from Home Assistant, with one tap.

![Actual Frame Gallery dashboard: colourful geometric artwork by Theo van Doesburg, a tap-to-load preview and optional artwork information.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/dashboard-commons.png)

*Actual Green screenshot; the dashboard is optional and set up separately. Theo van Doesburg, [Counter-composition XVI](https://commons.wikimedia.org/w/index.php?curid=3817033), Wikimedia Commons reproduction with public-domain metadata checked on 2026-10-05. The user confirmed this work on the TV. The screenshot is historical b3 evidence, not a new-release live test.*

- Choose 400 near-widescreen works from Wikimedia Commons, museum artwork from the Art Institute of Chicago or Cleveland Museum of Art, or your own JPEG/PNG images. No API key is needed. Commons is first/default on new installations; updates retain your saved source.
- Show the whole work without cropping by default. Previously sent works are skipped while new eligible works remain.
- Start from the app page, an automation, or an optional dashboard card with a preview of the latest successful upload.
- Optionally add title, artist and museum below the preview with built-in cards and one Text helper; the standard card stays minimal.
- Install on Home Assistant OS, including Green. No SSH, Docker setup, HACS, or edits to `configuration.yaml`.

**First start:** enter your TV's fixed private IPv4 address in **Configuration**, save, keep **Watchdog off**, and start the app with the TV on. Accept the TV's connection prompt within 20 seconds. The app stops after each run by design.

**Next:** open the **Documentation** tab for the setup guide, complete dashboard examples, supported filters, and troubleshooting. The dashboard is not installed automatically. Colour and style filters are not available in this beta.

**For Commons:** select `wikimedia_commons`, keep Landscape only on and Image fit `contain`. Sources are within 2.5% of 16:9; leave Prefer 16:9 on for the closest matches or turn it off for the whole curated selection. Small margins can remain, without cropping. Your existing dashboard still works. See the [collection and rights notes](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS.md).

**Public beta: 0.1.0b5.** Matching public sources, native ARM/Intel validators and actual runtime images, anonymous pulls and independent signatures passed. See the [b5 validation scope](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA5_VALIDATION.md). No new Green/TV live test is claimed. The preceding public b3 passed two deliveries and preview/text/loading/cleanup on Green; see the [historical validation scope](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA3_VALIDATION.md). Compatibility with every Frame model is not guaranteed.

Frame Gallery is an independent project, not affiliated with or endorsed by Samsung, the museums, or Home Assistant.
