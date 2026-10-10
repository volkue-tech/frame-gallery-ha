# Frame Gallery — next update Info text

**Unpublished local candidate, not the currently available 0.1.0b5.** Use this
prepared Info text only when the new version has passed its separately approved
native/release checks. It is not evidence of a new Green or television test.

Fresh artwork on your Samsung Frame — from Home Assistant, with one tap.

![Actual historical Frame Gallery dashboard with Theo van Doesburg's colourful geometric artwork.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/dashboard-commons.png)

*Actual historical b3 Green screenshot, not a mockup or proof of the new colour
dropdown. Theo van Doesburg, [Counter-composition XVI](https://commons.wikimedia.org/w/index.php?curid=3817033).
The dashboard is optional and configured separately.*

- Choose **1000 curated near-widescreen works from Wikimedia Commons**, museum
  artwork from the Art Institute of Chicago or Cleveland Museum of Art, or your
  own JPEG/PNG files. No API key. Commons is first/default for new installations;
  saved source choices on updates stay unchanged.
- For Commons, optionally choose **one colour**. A matching work must contain a
  meaningful area of that colour; it need not be the dominant area. **any** keeps
  the whole selection. The colour filter does not apply to the other sources.
- Keep the whole artwork without cropping by default. Previously uploaded/sent
  works remain excluded; this update does not reset history.
- Reuse your existing dashboard. Optionally add a native colour dropdown with
  one UI-created helper; no new script, custom card or dashboard extension.
- Optional title/artist/source information remains separate. Install on Home
  Assistant OS, including Green, without SSH, Docker setup or configuration.yaml.

**First start:** enter the TV's fixed private IPv4 address, save, leave Watchdog
and automatic startup off, and start with the TV on. Accept the pairing prompt
within 20 seconds. One start performs one bounded run and then stops.

**For Commons:** keep Landscape only on and Image fit `contain`. Sources are
within 2.5% of 16:9; Prefer 16:9 uses the unchanged approximately 1% rule and may
fall back within the selected colour. Small margins remain possible. A run with
no new matching work stops cleanly, keeping the previous image and caption.

**Next:** the Documentation tab explains the preview camera, timer, script and
complete native cards. They are not created automatically. Colour on the
dashboard is optional and explicitly Commons-only. Existing sources remain
available; unsupported filters are reported rather than claimed to apply.

Frame Gallery is independent, not affiliated with or endorsed by Samsung,
Wikimedia, the museums or Home Assistant. Compatibility with every TV model is
not guaranteed. Release notes must state the checks actually performed.
