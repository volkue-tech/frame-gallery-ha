# Changelog

## 0.1.0b19 (public beta)

Exact [native run 40100876404](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/40100876404) passed all five jobs. Both native validators and both actual publisher images each passed 6,435 production tests with eight root skips plus eight separate root checks. All four exact archives passed independent provenance/byte-hash/content checks; matching public sources, both immutable public-image steady-confirmation/recovery/preview probes and independent source/workflow-bound signatures passed. No physical no-wake guarantee. See [b19 validation](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA19_VALIDATION.md).

- Add separate experimental/default-OFF confirm_current_artwork consent for
  coherent mode/ID confirmation of an unchanged artwork on its already verified
  Art socket. Requires background mode and a configured existing Samsung entity.
  No new connection/startup/recovery permission or image/power/mode command.
- At most four correlated GETs per minute, with the existing5s/64-frame query
  bound and eight-hour session lifetime. Only complete agreeing Art-on/current
  replies renew proof; quiet reads retain still-fresh captions without flicker.
- Queued off/menu/standby, stale HA/clock/proof, ambiguous replies, transport
  failure or cancellation end the session without retry. Old refresh opt-ins
  remain held; standby recovery has independent consent and durable budgets.
- Preserve existing cards/scripts, per-TV attribution, current/last-sent preview
  semantics, data, dependencies and privileges. Simulations do not establish
  physical no-wake/sleep safety; the new option remains off after installation.

## 0.1.0b18 (public beta)

Exact [native run 39931258791](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/39931258791) passed all five jobs. Both native validators and both actual publisher images each passed 6,362 production tests with eight root skips plus eight separate root checks. All four exact archives passed independent provenance/byte-hash/content checks; matching public sources, both immutable public-image recovery/status/preview probes and independent source/workflow-bound signatures passed. No physical no-wake claim. App [prerelease](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b18). See [b18 validation](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA18_VALIDATION.md).

- Add a NEW default-off experimental standby_resume consent, independent of
  saved old switches. Observe cached HA off continuously for 30 seconds and a
  fresh on stable for 10 seconds before one exact-device/image revalidation.
- Consume each edge once; persist at most six reservations per rolling hour,
  at least 60 seconds apart across restarts. Invalid storage or HA/clock gaps
  deny recovery; TV authorization refusal latches. No boot-on/minute TV reads,
  send, power, mode, enrollment or blind retry is added by recovery.
- Add explicit status reasons and complete optional native status cards in
  English, German, French, Spanish and Italian. Existing cards, scripts and
  associations remain compatible and unchanged; unknown works stay unknown.
- The app must stay running to observe a full standby/wake cycle. Lost sessions
  while HA remains on need a new cycle; static image proofs still expire.
  Connection side effects on physical firmware remain unproven, not eliminated.

## 0.1.0b17 (public beta)

Exact [run 39825989063](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/39825989063) completed all five jobs successfully. Both native validators and both actual publisher images each passed 6,236 production tests with eight root skips and eight separate root checks; all four archives passed independent provenance/hash/content checks. Matching public sources, both anonymous immutable-image safety/preview probes and independent source/workflow-bound signatures passed. App [prerelease 421060980](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b17) targets the verified source.
See the [b17 validation report](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA17_VALIDATION.md).
No physical firmware/no-wake guarantee is inferred from these checks.

### Automatic observer I/O safety hold

- Suspend automatic initial/wake Art connections and scheduled current-state
  reads, including saved experimental opt-ins, after an unresolved wake/mode
  report. This is a conservative mitigation, not a proven firmware-cause fix.
- Retain the optional Samsung entity as a stop signal only. Off, unknown,
  unavailable, failed reads or observation gaps close the passive receiver;
  HA on cannot restart it. Saved values and all artwork associations remain.
- Keep explicit successful sends and passive known/unknown slideshow captions.
  Unchanged images can expire; automatic recovery after sleep/connection loss
  is intentionally suspended. No card/script or permission change is required.
- Explain the temporary restriction consistently in all five configuration
  locales and current-artwork guides. No new hardware no-wake guarantee is claimed.

### Optional current-artwork preview

- Cache a small worker-derived JPEG after each successfully associated upload,
  including one-shot runs. No additional TV connection, thumbnail or download.
- Key previews by actual TV identity, content/work IDs and delivered bytes.
  Bound the private cache to 128 MiB including JSON/base64 and 4,096 entries;
  eviction never clears associations or selection history.
- Publish a separate current.jpg only behind acknowledged preview-availability
  invalidation. Unknown/uncached/stale works never borrow the last-sent image;
  optional-cache failures preserve artist metadata. latest.jpg is unchanged.
- Add a complete optional native current-picture/artist card and Local File
  setup in English, German, French, Spanish and Italian. No new app option,
  special permission, dependency, HACS requirement or existing-card migration.
- Optional native card setup is separate; no automatic change to installed
  cards. Old/uncached works have no preview, without suppressing known metadata.
- Preserve the initial thumbnail caption's provenance while allowing only its
  exact session-verified upload preview. A same-ID same-work replacement cannot
  borrow cached bytes solely because its title/artist match.

## 0.1.0b16 (public beta)

- Fix fresh current-artwork confirmation: distinguish request names from the
  Frame's actual reply events (`artmode_status` and `current_artwork`). The
  previous parser rejected these correctly correlated responses, so optional
  minute synchronization could remain unconfirmed even with a known artwork.
- Replay the already recorded real replies and complete four-getter cycle,
  including the installed library over offline socketpairs. Correct synthetic
  responders so they no longer hide the request/reply-name mismatch.
- Preserve strict fresh request-ID correlation, same-connection mode/ID proof,
  all rate/deadline/standby guards, default-off options, stored per-TV mappings,
  permissions and existing cards/scripts. No new connection or TV command.
- This is an offline-verified protocol fix, not a new physical no-wake or
  automatic-sleep guarantee. Publication does not start or update an installed
  Home Assistant app or modify its dashboard.
- Exact native ARM/Intel validators and actual publisher images each passed
  6,103 production tests plus eight separate root checks. Four independently
  hash/provenance/content-checked archives, the public matching sources, both
  anonymous exact-image imports/parser checks and independent signatures passed.
  See the [b16 validation report](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA16_VALIDATION.md).

## 0.1.0b15 (public beta)

- Finalize same-connection synchronization with recovery even when the mode-on
  notification after leaving the artwork menu is lost. Each minute first reads
  mode; image-ID getters run only after a fresh on reply. Navigation cannot
  leave the observer waiting indefinitely. Existing stop/standby/HA-off gates
  and all no-new-connection/no-setter bounds remain.
- Positive notifications containing unexpected correlation/fields never
  substitute for a fresh coherent mode/ID response.
- Art-mode off/menu clears captions but retains mode-only checks on the same
  opted-in socket. Initial off/nav defers the original single thumbnail proof
  until Art Mode is on; physical standby remains terminal. Parent processing
  delays cannot shorten the minimum 60-second attempt interval.

### Retained source-only b14 intermediate (no app/Store release)

- Optional `current_state_refresh` switch, OFF by default: keep the current
  artist/title synchronized with coherent mode/current/current/mode reads on
  the already established Art socket, at most one cycle per minute.
- Recover after menu/slideshow changes and unchanged images without sending
  another artwork. Unknown valid notifications clear attribution instead of
  automatically killing the opted-in receiver; unknown images have no invented
  artist/title. Default event-only behaviour remains available.
- Fresh correlated replies, exact per-TV associations, shared five-second/
  64-frame cycles and finite budgets. Drain queued off/standby/navigation before
  sending a read. No new connection, thumbnail, power/mode command or keepalive.
- Existing cards, scripts, helper IDs, sources, history and privileges unchanged;
  English/German/French/Spanish/Italian option help and setup notes included.
- Experimental: read requests may affect automatic sleep. Offline and native
  builds are not physical firmware/no-wake validation. Connection loss/auth
  refusal still waits for a separately valid start/wake grant, not blind retry.

## 0.1.0b13 (public beta)

- Avoid duplicate initialization around a dashboard-started image request.
  Reserve a fixed ten-second initial handoff and process input before ticking.
  An accepted new-artwork request consumes the unused initial/old-edge evidence
  before cleanup, publication or delivery; failure and no_match cannot leave a
  hidden initial read behind. A fresh successful delivery may start its receiver.
- Preserve one standalone initial read after the handoff and continued valid
  cached HA on, plus later genuine off/on recovery and existing attempt/auth
  limits. Invalid/off/unknown/error/gap clears pending startup evidence. Refresh
  and rejected/replayed input cannot postpone the deadline or reopen a failure.
- Keep existing cards, scripts, per-TV memory, history, catalogue, dependencies,
  permissions and default-off mode. No new image/power/mode command or TV polling.
  Five-language guides explain the handoff; existing complete YAML is unchanged.
- The grace is bounded, not prediction of arbitrarily delayed user actions.
  A later send still reaps an already running independent receiver. The reported
  physical Art-to-TV transition's cause remains unproved; no new hardware or
  universal no-wake/no-mode-change guarantee is claimed.
- Numbered host gates passed 5,943 tests/16 platform skips, strict typing and
  100% line/branch coverage. Both native validators and actual publisher images
  passed 5,951 production tests/eight root skips plus eight separate root tests
  each. Matching public sources, four hash/provenance/content-checked archives,
  both anonymous exact-image imports and independent signatures passed. See the
  [b13 validation report](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA13_VALIDATION.md).
  Publishing does not update or start an installed HA app or change dashboard
  configuration. These gates do not prove a physical TV-mode safety fix.

## 0.1.0b12 (public beta)

- Fix initial synchronization when the Frame already shows an artwork: with
  background mode and the existing resume_state_entity configured, the first
  cached HA on sample permits one read-only initial check, even if on has not
  changed for hours. No new image send or off/on cycle is required. Missing,
  invalid, off, unknown or failed first samples consume this startup opportunity.
- Keep later fresh off-to-on recovery and the shared six-attempt per-process
  hourly ceiling. Repeated on states, refresh and a failed initial attempt do
  not retry. A new configured process start permits one new initial attempt.
- Reuse exact saved TV/target/token validation and fresh isolated Art/ID/image
  proof. No enrollment, sender, image/power/mode command, TV polling, extra
  helper, permission or dependency. Existing cards/scripts/data stay compatible.
- Update all five languages and new complete card examples with neutral waiting
  text. Installed cards are never edited. Initial/slideshow proof ages remain
  90/900 seconds; static art may become unconfirmed without a later valid event.
- Experimental and default off/unset. HA on is not Art Mode proof and may be
  old: a getter-only connection may still wake or affect some TVs. Offline
  simulation is not a new hardware or standby/no-wake guarantee.
- Full host gates pass 5,904 tests with 16 Linux-only skips, strict host/Linux
  typing for 302 files and 100% line/branch coverage. An in-memory old-policy
  negative control fails eight initial-read regressions without changing source.
  Native ARM/Intel validators and actual publisher images pass 5,912 production
  tests plus eight separate root tests per architecture. Matching public sources,
  four hash/provenance-checked evidence archives, real 1-GiB checks, anonymous
  pulls/imports and independent signatures passed. Publishing does not install
  the update, start an HA app or modify existing cards.

## 0.1.0b11 (public beta)

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
  Full offline gates, both native validators and actual publisher images,
  matching public sources, four provenance/hash-verified evidence archives,
  anonymous pulls/imports and independent signatures passed. No new live test,
  installed-app change or universal no-wake guarantee is claimed.

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
