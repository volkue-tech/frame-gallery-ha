# Frame Gallery for Home Assistant

Frame Gallery is an independently implemented Home Assistant app for displaying curated artwork on compatible Samsung Frame televisions. It is currently **pre-release**, not yet a one-click installable public beta.

This repository contains the product specification, the architecture, and the implementation in progress (`frame_gallery/`). It intentionally contains no application code copied or adapted from predecessor projects.

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

Phase 9 release preparation is in progress. Source is public, but no container
images or public beta release are published yet. The first native ARM/Intel CI
run passed, including the real memory limits. Validation of later changes,
complete dependency licence/corresponding-source compliance and a clean public-repository
Green installation remain release gates. Do not treat this source checkout as
the final simple-install distribution. Current state: `STATUS.md` and `TASKS.md`.

In the first beta, the Art Institute offers the period filter, and Cleveland
offers department and period; no source offers a colour filter (see
`frame_gallery/VOCABULARY.md`). Developer setup and quality gates:
`frame_gallery/DEVELOPMENT.md`.

One known limitation of the design: the app remembers the latest 20 000 artworks it has shown. Older ones are forgotten, so a very old artwork could in theory be shown again. At one artwork a day that takes about 55 years (R-29 in `DECISIONS.md`).

Planned first-beta sources:

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

## Attribution

The product idea is inspired by community experimentation around Home Assistant and Samsung Frame art-mode automation. The implementation in this repository must be written independently. Any future attribution must not imply that unlicensed predecessor code was copied, relicensed, or incorporated.
