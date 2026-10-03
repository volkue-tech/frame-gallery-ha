# Frame Gallery for Home Assistant

Frame Gallery is an independently implemented Home Assistant app for displaying curated artwork on compatible Samsung Frame televisions. **0.1.0b1 is a public install candidate; the clean public-repository Green test is still pending.** It is not yet the final beta announcement.

This repository contains the product specification, architecture and independently implemented app (`frame_gallery/`). It intentionally contains no application code copied or adapted from predecessor projects.

## Installation candidate

[Add the Frame Gallery repository to Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fvolkue-tech%2Fframe-gallery-ha)

Then open **Settings → Apps → App store → Frame Gallery → Install**. The app
downloads the pre-built image for Home Assistant Green (`aarch64`) or an Intel/AMD
installation (`amd64`); no SSH, Docker setup or `configuration.yaml` edit is needed.
Enter the TV's fixed private IPv4 address, keep Watchdog off, and read
[the app guide](frame_gallery/DOCS.md). This beta uses Supervisor's supported
`experimental` lifecycle flag, not an unsupported `beta` flag.

The one-click link uses Home Assistant's
[official repository redirect](https://raw.githubusercontent.com/home-assistant/my.home-assistant.io/main/redirect.json).

## Intended user experience

1. Add the repository to the Home Assistant app store with one click.
2. Install the pre-built app on Home Assistant OS, including Home Assistant Green.
3. Enter the television IP address and choose artwork filters.
4. Start the app manually, from an automation, or from a documented dashboard card.
5. The app selects one eligible, previously unsent artwork, prepares it without unwanted cropping, uploads it to the television, updates the dashboard preview, and exits cleanly.

No SSH access or `configuration.yaml` changes should be required for end users.

## Project status

The application, packaging and offline validation are implemented. Supervised
development-app tests on Home Assistant Green and a real Samsung Frame TV passed:
museum delivery, no-crop fitting, dashboard preview refresh, bounded loading,
duplicate history, cancellation/cleanup and the documented crash-recovery checks.
Enforced AppArmor child profiles and worker network restrictions were also tested
on the Green, followed by successful regular deliveries. See `PHASE8_REPORT.md`
and `PHASE9_REPORT.md` for the exact scope and limitations.

Phase 9 is in progress. Both numbered architecture images were published by
[run 37159551965](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/37159551965)
from runtime commit `d736c7a`. Native host/container/root/memory gates passed;
both images were independently downloaded anonymously and their keyless Cosign
signatures verified against the own workflow, issuer and exact commit.
[Matching sources](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b1)
are public and anonymously hash-verified. App-store metadata added afterward
selects those already verified images; it does not rebuild or retag them.
The separate clean public-repository Green installation, observed public app ID
and final beta announcement remain pending. Current state: `STATUS.md` and `TASKS.md`.

In the first beta, the Art Institute offers the period filter, and Cleveland
offers department and period; no source offers a colour filter (see
`frame_gallery/VOCABULARY.md`). Developer setup and quality gates:
`frame_gallery/DEVELOPMENT.md`.

One known limitation of the design: the app remembers the latest 20 000 artworks it has shown. Older ones are forgotten, so a very old artwork could in theory be shown again. At one artwork a day that takes about 55 years (R-29 in `DECISIONS.md`).

First-beta sources:

- local media;
- the Art Institute of Chicago;
- the Cleveland Museum of Art.

The two museum sources use only their documented open-access APIs and CC0 images; local media uses your own images. See:

- `ARCHITECTURE.md` (the approved architecture, with the Phase 2 to Phase 6 refinements marked)
- `PRODUCT_SPEC.md`
- `ARCHITECTURE_CONSTRAINTS.md`
- `ACCEPTANCE_TESTS.md`
- `LEGAL_BOUNDARIES.md`
- `TASKS.md`
- `STATUS.md`
- `DECISIONS.md`
- `THIRD_PARTY_NOTICES.md` (provisional)
- `RELEASE_CANDIDATE.md` (the report of the offline release validation)
- `PHASE8_REPORT.md` (supervised Green/TV development tests)
- `PHASE9_REPORT.md` (release hardening and remaining gates)
- `ENGINEERING_LICENSE_REVIEW.md` (bounded engineering assessment, not legal counsel)
- `SOURCE_AND_REBUILD.md` (sources and library replacement for developers)
- `RELEASE_PROCESS.md` (gated maintainer publication procedure)

## Attribution

The product idea is inspired by community experimentation around Home Assistant and Samsung Frame art-mode automation. The implementation in this repository must be written independently. Any future attribution must not imply that unlicensed predecessor code was copied, relicensed, or incorporated.
