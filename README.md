# Frame Gallery for Home Assistant

Frame Gallery is a planned, independently implemented Home Assistant app for displaying curated artwork on compatible Samsung Frame televisions.

This repository contains the product specification, the architecture, and the implementation in progress (`frame_gallery/`). It intentionally contains no application code copied or adapted from predecessor projects.

## Intended user experience

1. Add the repository to the Home Assistant app store with one click.
2. Install the pre-built app on Home Assistant OS, including Home Assistant Green.
3. Enter the television IP address and choose artwork filters.
4. Start the app manually, from an automation, or from a documented dashboard card.
5. The app selects one eligible, previously unsent artwork, prepares it without unwanted cropping, uploads it to the television, updates the dashboard preview, and exits cleanly.

No SSH access or `configuration.yaml` changes should be required for end users.

## Project status

Phases 2 to 6 are implemented. Phases 2 to 5 cover the core, deterministic selection and rendering, the guarded network gateway, the Home Assistant helper reader, the three source adapters, the bounded persistent state (history, the TV-upload exclusion ledger, the metadata cache, the workspace, the preview, and the run records), the Samsung television adapter, and the isolated worker processes that run the image and television work. Everything is tested offline against fakes, synthesized fixtures, and a scripted television; no real television has been contacted yet. Phase 6 packaged the app for Home Assistant OS: the entry point, the container image for `aarch64` and `amd64` (built and checked locally, with the whole test suite inside it; nothing published), the app configuration, a draft AppArmor profile, and the user documentation (`frame_gallery/DOCS.md`). Its gate passed on 2026-10-03; Phase 7, the offline validation of a release candidate, is in progress.

The app has not run on Home Assistant yet: the first supervised run on a Home Assistant Green against a real television is Phase 8. In the first beta, the Art Institute offers the period filter, and Cleveland offers department and period; no source offers a colour filter (see `frame_gallery/VOCABULARY.md`). Developer setup and quality gates: `frame_gallery/DEVELOPMENT.md`.

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

## Attribution

The product idea is inspired by community experimentation around Home Assistant and Samsung Frame art-mode automation. The implementation in this repository must be written independently. Any future attribution must not imply that unlicensed predecessor code was copied, relicensed, or incorporated.

