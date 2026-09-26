# Frame Gallery for Home Assistant

Frame Gallery is a planned, independently implemented Home Assistant app for displaying curated artwork on compatible Samsung Frame televisions.

This repository currently contains the product specification and agent handoff package only. It intentionally contains no application implementation copied or adapted from predecessor projects.

## Intended user experience

1. Add the repository to the Home Assistant app store with one click.
2. Install the pre-built app on Home Assistant OS, including Home Assistant Green.
3. Enter the television IP address and choose artwork filters.
4. Start the app manually, from an automation, or from a documented dashboard card.
5. The app selects one eligible, previously unsent artwork, prepares it without unwanted cropping, uploads it to the television, updates the dashboard preview, and exits cleanly.

No SSH access or `configuration.yaml` changes should be required for end users.

## Project status

Phase 2 (core, deterministic selection, and rendering) is implemented and tested against fakes, awaiting the Phase 3 gate. The app is not usable yet: provider adapters, persistent state, the television adapter, and packaging follow in Phases 3–6. Developer setup and quality gates: `frame_gallery/DEVELOPMENT.md`.

Planned first-beta sources:

- local media;
- the Art Institute of Chicago;
- the Cleveland Museum of Art.

The two museum sources use only their documented open-access APIs and CC0 images; local media uses your own images. See:

- `ARCHITECTURE.md` (the approved architecture, with Phase 2 refinements marked)
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

