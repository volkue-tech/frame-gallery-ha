# Changelog

## Unreleased

- Optional native dashboard artwork-information card (title, artist, museum),
  using one dedicated UI-created Text helper. Standard image card unchanged.
- Preview-coupled metadata updates, bounded output, omitted missing fields and
  clean failure handling. No extra museum requests or dashboard extension.
- Not included in 0.1.0b1; new images and an approved Green upgrade are required.

## 0.1.0b1 (release candidate; public installation not yet verified)

- Independently implemented one-shot app for Home Assistant OS, including Green
  (`aarch64`) and native `amd64`; no SSH or configuration-file edits for users.
- Local images and the documented Art Institute of Chicago / Cleveland Museum
  of Art open-access sources; museum period filters and Cleveland departments.
  Colour and art-style filtering are not offered.
- Landscape selection, bounded 16:9 preference with fallback, whole-artwork
  fitting with margins by default, persistent duplicate history and uncertainty
  quarantine; bounded cancellation and temporary-image cleanup.
- UI-created preview camera and loading timer; enforced worker profiles and
  additional worker network restrictions, memory/CPU limits and token isolation.
- Original dependency notices, exact corresponding-source packaging and
  replacement/rebuild instructions; Apache-2.0 covers project-owned code only.
- Native ARM/Intel quality gates and gated, signed version-image publication.
  Publication and clean public installation remain separately verified gates.
- Development-app delivery and enforced isolation passed on one Home Assistant
  Green / Samsung Frame combination. Fresh TV pairing was not reset; Chicago
  access has varied between tests. Compatibility with every TV/network is not
  promised. See the repository's phase reports and engineering licence review.

## 0.1.0.dev0 (development build, not released)

- First packaging of the app for Home Assistant OS (`aarch64` and `amd64`).
- Sources: the Art Institute of Chicago (period filter), the Cleveland Museum of Art (department and period filters), and your own images.
- One bounded run per start: at most two minutes, and at most 70 seconds when nothing matches.
- No work is sent twice while unsent works remain; an upload whose outcome is unknown is held back for 30 days.
- Workers that decode images or talk to the TV run as an unprivileged user with memory, CPU, and file limits.
- Not yet tested against a real TV or on a Home Assistant Green.
