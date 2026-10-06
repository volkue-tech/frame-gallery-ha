# Changelog

## 0.1.0b4 (release candidate)

- Replace the broad-ratio Commons selection with 166 curated near-widescreen
  works from 112 artist labels. Sources are at least 3000 pixels wide and
  within 2.5% of 16:9. No artwork files are bundled.
- Preserve all existing Commons history IDs, settings and dashboard helpers.
  No new configuration field; English/German hints explain the unchanged
  stricter 1% preference and safe no-crop fallback.
- Cap discovery at ten normal metadata batches per run, retain all existing
  request/deadline limits, and omit permanently sent works from mixed batches.
- Retain all 200 research proposals; defer 34 rights/proportion/source-format cases
  rather than treating a research preview as release clearance.
- The candidate still requires exact-source publication, native ARM/Intel
  validation and signed-image checks. No new Green/TV live test is claimed.

## 0.1.0b3 (public beta)

- Wikimedia Commons: 50 curated landscape works of classical modernism, no
  registration or API key. Current rights, pinned file identity and bounded
  image sizes checked on every run; existing no-repeat and cleanup retained.
- Existing standard card and optional artist/title card work without new helpers.
- Shorter basic configuration, optional museum filters/margin colour and hidden
  unused colour compatibility option. Existing saved options remain accepted.
- German configuration labels and concise source/no-crop/16:9 explanations.
- Commons project contact is volkue+commonsapi@gmail.com; no user email required.
- Local tests and all 50 live metadata records passed. Native ARM/Intel actual
  images and independent signatures passed. The existing public Green app was
  upgraded without reinstall/reset; two distinct Commons deliveries refreshed
  preview/caption and finished loading/cleanup. The user confirmed the second
  work on the TV. Landscape means wider than tall, not a guarantee of small margins.

## 0.1.0b2 (public beta)

- Optional native dashboard artwork-information card (title, artist, museum),
  using one dedicated UI-created Text helper. Standard image card unchanged.
- Preview-coupled metadata updates, bounded output, omitted missing fields and
  clean failure handling. No extra museum requests or dashboard extension.
- Native ARM/Intel images validated and signed; existing public Green app upgraded
  without resetting history. Repeated image/text refresh and negative outcomes
  tested; physical b2 TV display confirmation is deferred.
- Not included in 0.1.0b1; update the existing app to enable the optional feature.

## 0.1.0b1 (first public beta)

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
  Publication and a separate clean public Green installation passed; evidence
  and limitations are recorded in the Phase 9 report.
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
