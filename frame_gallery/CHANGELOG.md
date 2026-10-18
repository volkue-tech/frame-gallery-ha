# Changelog

## 0.1.0b11 (beta candidate)

- Optional experimental resume after sleep: configure this TV's existing Samsung
  HA media_player/remote in resume_state_entity and enable background mode.
  One freshly observed off-to-on edge allows one read-only revalidation, without
  sending an image. A prior successful pinned-target upload is required.
- Boot-on, duplicates, stale/future/reordered states, HA gaps and invalid identity
  do not grant reads. Six attempts/hour maximum, consumed before the attempt;
  failure has no automatic retry. Authentication refusal latches observation off.
- Recheck actual TV identity, Art Mode, current ID and image before displaying
  artist/title. Unknown/replaced/other-TV images never borrow the last caption.
  No power, Wake-on-LAN, mode, upload or selection command on the resume path.
- Fix the missing exact parent-only AppArmor backup-link rule for the existing
  artwork-deliveries.json file; do not broaden worker/container privileges.
  Preserve existing cards/scripts/associations and one-shot defaults.
- Wake/connection side effects are NOT hardware-validated for this candidate.
  HA on is not Art Mode proof; a read-only connection may still wake or change
  the mode of some televisions. Both options are optional/default off or unset.
  Offline/native test and publication results are recorded separately; no new
  live test, installed-app change or universal no-wake guarantee is claimed.

## 0.1.0b10 (public beta)

- Keep the same finite event receiver after incomplete sequences of recognized
  slideshow notifications. Clear the current caption and discard all pending
  parts; only a later complete matching five-second sequence can confirm a work.
  No partial-ID attribution, duplicate renewal, new query or reconnect.
- Add fixed, allowlisted failure codes to the app log for startup, receiving,
  event decoding, worker and parent-contract errors. No raw messages,
  exception bodies or credentials; recovery warning is bounded per session.
- Retain shutdown on unknown/malformed/stale messages, off/standby, identity,
  resource and publication failures. Background remains experimental/default OFF.
- Existing cards, script/helper IDs, per-TV associations, history, catalogue,
  filters, dependencies and protected Green permissions remain unchanged.
  Current-artwork guidance remains consistent across all five languages.
- Eight authored restart regressions fail on b9 and pass with the fix. Full
  offline gates pass 5773 tests/16 Linux-only skips and 100% line/branch coverage.
  The actual b9 live-abort cause remains unproven because its log lacks event
  reasons; this is not a new hardware, sleep or universal compatibility pass.
  Native ARM/Intel validators and actual publisher images, matching public
  sources, four verified evidence archives, anonymous image pulls/imports and
  independent signatures passed. Publishing does not update installed HA apps
  or edit cards. Update in place without uninstalling.

## 0.1.0b9 (public beta)

- Automatically remember title, artist, source and TV image ID after every
  selected upload, even with background mode off. Associations are per actual
  television identity, not just an IP address, and survive normal app updates.
  Bounded atomic storage and compact local image references; no user-managed IDs.
- Replace repeated background queries with one finite event session after a
  fresh explicit send. Automatic slideshow events can show the saved artist
  and title; unknown older TV images stay unidentified rather than borrow text.
  No post-baseline image requests, polling, automatic reconnect or power/mode
  setters. Boot/restart/refresh alone never starts a TV session.
- Background mode remains experimental, optional and OFF by default. Controlled
  private tests covered slideshow changes and one natural-sleep episode on one
  Frame, not all models/firmwares. A connection may still wake a television.
  Unobserved external reuse of an image ID is an event-only attribution limit.
- Keep existing camera, timer, script ID and cards. Optional current-artwork
  native card and setup/script instructions in English, German, French,
  Spanish and Italian. No new Green permissions, helpers, dependencies or
  configuration.yaml changes. Last-upload preview stays separate from current TV.
- Matching public sources, native ARM/Intel validators and actual publisher
  images, four bounded hash/provenance-checked evidence archives, anonymous
  pulls/imports and independent signatures passed. Earlier private snapshots
  are not a changed-b9 hardware pass; no new live-TV test is claimed.
- Pin Alpine's transitive libexpat 2.9.0-r0 and retain its exact MIT licence,
  source and recipe evidence; all Python dependency versions remain unchanged.

## 0.1.0b8 (public beta)

- Optional **experimental background mode**, off by default. Read-only TV
  connections may wake a sleeping Frame; automatic no-motion sleep has not
  been validated. No power, Wake-on-LAN or Art-Mode setters in the observer.
- Keep the app running, then explicitly send a new artwork through the updated
  script to arm current-artwork checks. Boot/restart never contacts the TV.
  Failed reads or inactive Art Mode pause checks without automatic reconnects.
- Verify per-TV content IDs and thumbnails before associating title/artist.
  Bounded atomic mappings and device pins persist separately from send history.
  Unknown TV pictures remain unidentified; no cloud recognition or bulk scan.
- Optional native current-information card and complete five-language guides.
  Existing one-shot operation, preview/cards, filters and history stay unchanged
  unless the user explicitly opts in and replaces the send-script body.
- Preserve stdin through the pinned s6 init path; retain bounded isolated TV,
  image and delivery workers, shutdown, replay protection and temporary cleanup.
- No new providers, dependencies, catalogue entries or history-reset action.
- Matching public sources, native ARM/Intel validators and actual publisher
  images, bounded evidence archives, anonymous pulls/imports and independent
  signatures passed. Natural no-motion sleep/no-wake, sustained polling,
  transitions and real b8 HA migration remain open beta follow-ups.

## 0.1.0b7 (public beta)

- Optional Commons artist selection, alone or combined with colour. Exact
  catalogue artist names or offered keys are accepted; other sources report
  this filter as ignored. No match preserves the previous image and caption.
- Complete optional native artist-only and artist-plus-colour dashboard cards,
  with a favourites dropdown. No custom card or new mandatory helper.
- Configuration names and help in English, German, French, Spanish and Italian,
  selected by the Home Assistant interface language. Technical values remain
  English. Setup, colour and artist guides have manual five-language links.
- Keep all 1000 catalogue entries, source pins, history IDs, defaults, limits,
  dependencies and existing cards unchanged. No history-reset control or
  new Green/TV live validation is included.
- Matching public sources, both native validators and actual publisher images,
  bounded evidence checks, anonymous imports/pulls and independent signatures
  passed before Store handoff. Existing installations update without uninstalling.

## 0.1.0b6 (public beta)

- 1000 curated near-widescreen Commons works: 344 unchanged baseline entries
  and 656 additions. Temporarily hold 56 user-reviewed baseline cases; retain
  their IDs, research and send history. Seven additional reviewed works remain
  reserves. No original artworks are bundled.
- One optional Commons colour wish, default `any`, using source-bound offline
  palettes. A noticeable colour area qualifies; it need not be dominant.
  Other sources remain available and report unsupported colour as ignored.
  No different-colour fallback; no match keeps the previous image and caption.
- Complete optional native dashboard card with a colour dropdown helper.
  Existing camera, timer, script and optional artwork information still work;
  no custom dashboard extension or configuration.yaml changes.
- Preserve no-crop defaults, strict ratio preference, bounded request/worker
  limits, temporary-file cleanup and all existing history IDs. Matching public
  sources, native ARM/Intel validators and actual publisher images, anonymous
  pulls and independent signatures passed before Store publication.
  No new Green/TV live test is included in this release phase.

## 0.1.0b5 (public beta)

- Expand the pinned near-widescreen Commons catalogue to 400 works from 299 artist labels: all 166 b4 entries unchanged, plus 234 visually reviewed JPEG works. Sources remain at least 3000 pixels wide and within 2.5% of 16:9; no crop, ratio-rule, request-budget or history reset. Metadata-only research and the 34 older deferred proposals are retained.

- Put an authentic colourful Commons dashboard screenshot first on the Info
  page and explain the optional dashboard setup separately from the first TV run.

- Put Wikimedia Commons first in the artwork-source choices and select it by
  default for new installations or missing source options. Preserve all saved
  source choices on updates; no change to shape, fit or history settings.

## 0.1.0b4 (public beta)

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
- Matching public sources, native ARM/Intel validators and actual runtime images,
  anonymous pulls and independent signatures passed. Existing versions remain
  available. No new Green/TV live test is claimed for this catalogue update.

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
