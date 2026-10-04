# Frame Gallery

Fresh artwork on your Samsung Frame — from Home Assistant, with one tap.

![Actual Frame Gallery public-beta dashboard card with an artwork preview and a tap-to-load label.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/dashboard-preview.png)

*Actual dashboard screenshot. The optional card is set up separately. Artwork: [“Elephant Bridge” souvenir](https://www.clevelandart.org/art/1929.342), Cleveland Museum of Art, 1929.342, [CC0 Open Access](https://www.clevelandart.org/open-access).*

- Choose museum artwork from the Art Institute of Chicago or Cleveland Museum of Art, or use your own JPEG/PNG images.
- Show the whole work without cropping by default. Previously sent works are skipped while new eligible works remain.
- Start from the app page, an automation, or an optional dashboard card with a preview of the latest successful upload.
- Optionally add title, artist and museum below the preview with built-in cards and one Text helper; the standard card stays minimal.
- Install on Home Assistant OS, including Green. No SSH, Docker setup, HACS, or edits to `configuration.yaml`.

**First start:** enter your TV's fixed private IPv4 address in **Configuration**, save, keep **Watchdog off**, and start the app with the TV on. Accept the TV's connection prompt within 20 seconds. The app stops after each run by design.

**Next:** open the **Documentation** tab for the setup guide, complete dashboard examples, supported filters, and troubleshooting. The dashboard is not installed automatically. Colour and style filters are not available in this beta.

**Public beta: 0.1.0b2.** The existing public Green app was upgraded and its optional artwork information was software-tested, including restart restoration. Physical TV confirmation of the b2 runs is deferred; earlier b1 physical-TV evidence remains recorded. Compatibility with every Frame model is not guaranteed.

Frame Gallery is an independent project, not affiliated with or endorsed by Samsung, the museums, or Home Assistant.
