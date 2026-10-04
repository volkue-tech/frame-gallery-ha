# Frame Gallery 0.1.0b1

First public beta of an independently implemented Home Assistant app for Samsung
Frame artwork. Install through Home Assistant OS/Supervisor, including Green;
no SSH, Docker installation or `configuration.yaml` edits required.

[Add the repository to Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fvolkue-tech%2Fframe-gallery-ha)

Open **Settings → Apps → App store → Frame Gallery → Install**, set the TV's fixed
private IPv4 address, and leave Watchdog off. Follow the
[complete app and dashboard guide](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/DOCS.md).

## Included

- Local images, Art Institute of Chicago and Cleveland Museum of Art sources.
- Period filters, Cleveland department filter, landscape-only selection and a
  bounded 16:9 preference with fallback. Whole-artwork fitting is the default.
- Persistent sent/upload history, bounded execution and temporary-file cleanup.
- Native preview card with a loading timer and fail-safe expiry, without a custom card.
- Pre-built ARM/Intel images and keyless signatures; no runtime build on Green.

Separate public Green installation passed two deliveries (21.2 s and 17.3 s),
preview/loading updates, safe invalid-option refusal and cleanup. The user
confirmed the first artwork on the physical TV. These times are observations,
not guarantees. Native ARM/Intel runtime validation and image checks passed.
Exact evidence and scope: [Phase 9 report](https://github.com/volkue-tech/frame-gallery-ha/blob/main/PHASE9_REPORT.md).

## Known limitations

- No Google Arts & Culture/Bing providers, colour filter or style filter.
- First-time pairing was not reset/tested on every TV model. Art API version
  0.97 is refused; Samsung's Art Mode interface is undocumented.
- The latest preview path is shared by multiple installations; private histories
  are separate. Existing TV uploads are not automatically imported or deleted.
- History retains 20,000 artworks; uncertain uploads are excluded for 30 days.
- Museum availability and image resolution vary. Strict shape matching can
  fall back to another landscape work; contain mode may add margins.
- The local TV connection does not validate the TV's self-signed certificate.

## Images and corresponding sources

Runtime/source commit: `d736c7a9cd45f709de17572e68a5ebf8c5344933`.
Later repository metadata, tests and documentation do not rebuild these images.

- ARM: `ghcr.io/volkue-tech/frame-gallery-ha-aarch64@sha256:f170fb081171da23e25c8a46ad836625b4c174c5fd7d1a3b07d305344dc6e313`
- Intel: `ghcr.io/volkue-tech/frame-gallery-ha-amd64@sha256:89cf1ac74d80c5ad696aa1c7ffb67e8c5f62518f323e8b51a42716fc8eb9ff70`

[Matching corresponding-source package](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b1):
518,133,760 bytes; SHA256
`8034a982322532b34b0c9893cda5135cb16448dc694e2c59f68ae42fedeb64b5`.
Both images and this source download were independently verified anonymously.

Own code is Apache-2.0; third-party components retain their licences. The image
contains GPL/LGPL components and is not wholly Apache-2.0 or GPL-free. Original
notices and matching sources are supplied. The recorded engineering assessment
is not independent legal counsel, patent clearance or an ownership warranty.
No Samsung, museum or Home Assistant endorsement is implied.
