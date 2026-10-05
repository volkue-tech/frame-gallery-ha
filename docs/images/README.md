# Documentation visuals

`frame-gallery-overview.svg` is an original, editable product illustration made
for this project. Its geometric artwork is original too: no museum artwork,
Samsung imagery, third-party UI screenshot or predecessor asset is included.
The PNG is a rendered copy for Markdown and Home Assistant compatibility.
The original SVG and its PNG render have the same Apache-2.0 licence as the
project's own code. This does not relicense artwork or UI in the screenshot below.

This is explicitly an illustration, not evidence of a live dashboard, automatic
dashboard installation, or a photograph of a particular TV. Keep its visible
disclaimer and the surrounding Markdown caption when reusing it.

`dashboard-preview.png` is an actual screenshot captured on 2026-10-04 through
Firefox's native region-screenshot tool from the running public-beta installation.
It contains only the card; no address bar, account, sidebar, notifications, or
configuration. The region was selected before capture, not retouched afterward.
No upload was triggered and no HA/TV settings were changed for the capture.
It depicts a German card label; the user guide explains that labels are editable
and uses generic entity IDs rather than this installation's test identifiers.

Displayed artwork: [“Elephant Bridge” souvenir](https://www.clevelandart.org/art/1929.342),
1900s, unknown maker, Cleveland Museum of Art, accession 1929.342,
Gift of the Gilpin Players of Karamu House. The official object page explicitly
permits copying, modifying and distributing the work; the museum's
[Open Access policy](https://www.clevelandart.org/open-access) designates eligible
images CC0. Both pages were checked on 2026-10-04. The public-beta test report
records this previously delivered work as `cma:110817`.

This documentation screenshot is not a bundled provider image or default artwork
for the app. It lives outside the runtime build context. No raw museum image was
downloaded for this documentation work, and the screenshot is not evidence of
fresh physical-TV confirmation. Credits do not imply museum or HA endorsement.
Do not use screenshots or assets of excluded predecessor apps.

## First-time setup screenshot

`local-file-setup.png` is the user's original Home Assistant Local File setup
dialog screenshot, supplied on 2026-10-04 during fresh-install testing and
included following the user's request for first-user documentation screenshots.
It is copied without retouching from the supplied image. It contains no artwork,
address bar, sidebar, account details, entity attributes or access tokens.
It shows the unfilled German dialog, not a completed configuration. The guide's
caption explicitly instructs readers to replace the default `Local File` name
with `Frame Gallery Preview` and fill in the file path. Home Assistant's UI is
third-party material; the project's Apache-2.0 licence does not relicense it.
The asset lives outside the app runtime build context.

For a future screenshot of the dashboard Entity picker, use a clean view with
the named preview only, without development/test entries or personal entities.
Do not reuse the supplied full Details screenshot: it exposes camera tokens.
The existing verified-CC0 dashboard screenshot already illustrates the result.

## Optional artwork-information screenshot

`dashboard-artwork-info.png` was captured on 2026-10-04 after the approved b2
Green update and one Core restart. Firefox's native region-screenshot tool
selected only the image and information cards before capture. The original
captured PNG is copied byte-for-byte without retouching. No account, sidebar,
calendar, address bar or camera access token is included. The German button
label is explained in the guide. This is software-rendering evidence, not
physical TV confirmation, which the user deferred.

Artwork: Martin Johnson Heade, **Magnolias on Light Blue Velvet Cloth**, 1885–95,
Art Institute of Chicago, artwork 100829. The official metadata endpoint
`https://api.artic.edu/api/v1/artworks/100829?fields=id,title,artist_display,is_public_domain,credit_line,image_id`
was read once on 2026-10-04 and returned `is_public_domain: true`, matching
title/artist and image ID `0729fbba-51e3-a2d7-6d4d-61c2be62af3f`.
Credit: Purchased with funds provided by Gloria and Richard Manney;
Harold L. Stuart Endowment Fund. See the [official object page](https://www.artic.edu/artworks/100829),
[API copyright guidance](https://api.artic.edu/docs/#copyright) and
[image-licensing policy](https://www.artic.edu/image-licensing).
The website object/licensing pages returned 403 to the web-reading tool;
the factual per-work verification is the successful official API response,
not an assertion that those pages were newly readable. No raw museum image
was downloaded for documentation. The screenshot is outside the runtime build
context; the project's Apache-2.0 licence does not relicense third-party UI
or museum material.

## Commons beta screenshot

`dashboard-commons.png` was captured on 2026-10-05 after the approved b3
in-place Green update. Firefox's native region-screenshot tool selected only
the Frame Gallery heading and its existing preview/information cards. The
captured PNG is copied byte-for-byte, with no retouching; no account, address
bar, sidebar, calendar, configuration or camera token is included. Its SHA256
is `acaae007c0b92dd5c9135441bb17be0108937882321dc4a84f75d0b101061cf0`.

Artwork: Theo van Doesburg, **Counter-composition XVI**, Commons page
[`3817033`](https://commons.wikimedia.org/w/index.php?curid=3817033).
The approved metadata-only 50-work check and the actual b3 production run
both accepted this pinned file's public-domain metadata and current identity.
The selected prepared payload SHA256 was
`bc5d34a0195692176e6541bdad745561020b5d43389cfe74935572fae7ece6de`;
this is the prepared image hash, not a hash of the original Commons upload.
The native stack rendered matching title/artist/source, and the user physically
confirmed the work on the TV. See [b3 validation](../../BETA3_VALIDATION.md).

This is not a bundled provider artwork, default image or claim of worldwide
copyright clearance. Current rights statements remain the source's statements;
the project's Apache-2.0 licence does not relicense artwork or Home Assistant
UI. The screenshot lives outside the runtime build context. No predecessor
project asset was used.

## Presentation references (earlier pass)

Reviewed on 2026-10-04 for documentation structure only:

- [Mushroom](https://github.com/piitaya/lovelace-mushroom): a short benefits list,
  installation before developer material, and separate usage/help sections.
- [Alexbelgium's community apps](https://github.com/alexbelgium/hassio-addons):
  a prominent Home Assistant repository installation link.
- [Official Matter Server guide](https://github.com/home-assistant/addons/blob/master/matter_server/DOCS.md):
  first-use instructions before advanced configuration.
- [Home Assistant presentation requirements](https://developers.home-assistant.io/docs/apps/presentation/):
  app-store introduction in the app's README, user guide in DOCS.

No text, artwork, screenshots, icons or code from these projects was copied.
Their installation mechanisms are not requirements of Frame Gallery; this app
does not require HACS or Mushroom.
