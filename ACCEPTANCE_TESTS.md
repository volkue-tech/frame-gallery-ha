# Acceptance tests

## Local startup/send arbitration (D-240)

- Reproduce queued and delayed existing-script sends with initial on and without
  it: accepted requests within the ten-second handoff have no pre-send read;
  one successful send starts at most its one post-send receiver. Receive input
  before any service tick; no real-time sleep or outbound network in tests.
- Failed/no_match/unchanged-receipt sends and unavailable/auth-refused post-send
  proof cannot fall back to an unused initial read. Cover the actual regular
  entry, durable claim, stores, fake Core and publisher, not only a fake controller.
- Standalone opted-in startup/refresh still has one initial read after the fixed
  handoff. Invalid/missing/off/unknown/error, stale/reordered data and sample gaps
  cancel pending evidence; no delayed retry. Refresh/input flood/rejected or
  replayed commands cannot postpone the deadline or reset attempt/auth bounds.
- Supersession clears old off-edge evidence; only a later newly observed off/on
  may resume. Stop/publication/reap failures remain fail closed. A later send
  after standalone initialization must reap its old worker before delivery.
- Existing cards/scripts/options/data/worker permissions stay unchanged. Full
  offline quality gates, no HA/TV access, no version/build/publication. Hardware
  mode-side-effect cause and future native/live acceptance are not inferred.

## Initial already-on synchronization (D-239)

- Default/off/unconfigured mode still cannot connect. First valid configured
  on sample grants one attempt even if unchanged for hours; fresh Core read
  is a trigger, never a claim of fresh Art/pixel proof. Future/invalid data fail.
- Consume the initial opportunity before any preparation, including missing,
  timeout/off/unknown/auth failure. Repeated on/reports/refresh cannot retry.
  A later genuine off/new-on uses unchanged edge rules and shared six/hour cap.
- Actual entry with fake Core/store/receiver/publisher resolves known images,
  leaves unknown images unidentified, rejects other-TV/changed-image/TV-mode/
  token/archive problems, stops on publication/cancel and never invokes send.
- Static initial proof ages out after 90 seconds with no request or fabricated
  freshness. Retain same finite receiver for later complete slideshow events.
  Initial on after another process start is a new permitted opportunity, not
  certification of a persistent cross-restart throttle or physical no-wake.
- Existing cards/scripts/data/privileges remain; complete five-language help,
  offline quality gates and exact native ARM/Intel/source/image/signature checks
  before publishing. Old private probe is not this candidate's hardware pass.

## Experimental sleep/wake resume (D-238)

- Default/one-shot/unconfigured mode preserves every previous path and request.
- One configured media_player/remote Core entity only; strict entity/timestamp/
  state/body validation. No TV polling/discovery or new permission. A 401/403
  latches reader authentication off; missing/timeout/unknown clears pending edge.
- Start-on, stale/future/reordered/repeated on, HA outage/gap/restart and forged
  entity data cannot resume. Observed off/new fresh on grants one attempt,
  consumed even on failure. Six/hour bound; no retry until a different full edge.
- Resume validates exact target/device archive and token locally, never calls
  send/enroll/repin, then uses real isolated initial Art/ID/image verification.
  Unknown/reused/other-TV IDs cannot inherit an old caption. Cover multiple
  sleep/wake cycles, TV-program mode, lost socket, cancellation/publication error.
- Existing cards/scripts/history/source settings and installed b10 stay intact.
  Required five locales, complete optional guide and actual regular-entry wiring
  tests cover this option. Full host/native ARM/Intel gates precede publication;
  physical no-wake behaviour remains unverified, never inferred from replay.

## Local b9 recovery/diagnostic regression (D-237, no live/publication gate)

- Authored nav/restart cases must fail on b9 before the fix. Incomplete known
  sequences clear confirmation and pending state, keep exactly one receiver
  and accept only a later whole matching five-second triple. Expired late
  halves, duplicates and discarded events cannot supply or renew a caption.
- Cover orphan/repeated/conflicting rotation, missing rotation, overlapping
  selection and pending timeout. Recovered known/unknown per-device lookups
  retain their metadata rules and byte-identical archives/history.
- Pinned parser/socketpair replay asserts one channel, five initial getters,
  one initial thumbnail and zero post-baseline application requests; no TCP
  or real HA/TV. This is not captured proof of the failed b9 message.
- Off/standby/unknown/malformed/stale/future/identity/limit/publication failures
  still clear and disarm without reconnect. No observer settings/privileges,
  installed cards, app version, private frozen capture or release are changed.
- Parent accepts only fixed diagnostic enums on unavailable end records, logs
  no arbitrary string/frame/exception/token and warns at most once per explicit
  session about incomplete sequences. Old end/Observation shapes remain valid.
- Full lint/host+Linux strict typing/coverage/isolation/store gates must pass;
  native ARM/Intel and any changed-candidate live/sleep pass remain future gates.

## Complete upload memory/current artwork acceptance (D-235)

- Every selected one-shot/background send persists per-device/ID metadata before
  history or preview failures/cancellation. Earlier failures do not create it.
  Actual device identity comes from the existing capability read, no extra GET.
- Reopen across restart/update; keep different TVs/sources separate, replace
  same-TV reused IDs, reject missing/malformed identity rather than guess by IP.
  Damaged/future/unreadable state and stale backup fail closed. Count/byte bounds,
  deadlines and write failures preserve existing data, with no TV retry.
- Tiny reference matches exact output SHA; isolated initial thumbnail comparison
  may confirm old uploads or reject contradictory metadata. No fabricated byte
  proof, stale caption shortcut or metadata on unknown event IDs.
- Test the actual regular entry with delivery-backed one-use grant and empty
  reviewed registry, multiple known/unknown cycles, failure stop and no resume.
  Default/off/boot/refresh cannot connect; target/device mismatch cannot arm.
- Existing card/sensor/script IDs remain compatible. EN/DE/FR/ES/IT guides have
  complete native YAML, upload-memory explanation and firmware/wake limitations.
  Green protected packaging, unchanged special permissions, full offline gates,
  native aarch64/amd64 tests and real image checks precede beta publication.
- Prior known-work automatic hardware gate remains open; no replay may relabel
  it passed. Generic experimental use remains opt-in with explicit warning.

## Regular event-service integration acceptance (D-234, local)

- Actual background entry/controller/backend/store/publisher wiring is exercised
  with injected I/O and synthetic test policy only. Boot/refresh do not connect;
  a successful fresh explicit delivery is still required.
- New background current records hash the actual target, not plaintext address;
  one-shot records stay unchanged. Missing/legacy/wrong target receipts cannot
  arm the old TV, including changed address during delivery. Parse the same bytes.
- All publication failures stop/reap the listener and prevent subsequent/final
  write retries. Test non-auth failures, ownership refusal and 401/403 separately.
- Exact go_to_standby pauses/clears and closes; extra/correlated/unrecognized
  objects fail closed. Real pinned-library socketpair asserts no new connection,
  extra getter or setter on standby.
- Multiple unknown/known transitions and expiry preserve histories/bindings;
  unknown works never borrow captions. Existing cards/IDs and default one-shot
  behaviour remain compatible. No native/hardware result is inferred from replay.
- Keep old private hardware snapshots exact; record changed runtime fingerprint.
  Native candidate ARM/Intel are deferred to the later release round and must
  pass before publication; no public push/release follows from local success.

## Local slideshow event attribution acceptance (D-233)

- Exact authored lab4 shapes decode selected/shown, matching automatic rotation
  and on; no coercion of Yes/on/shuffleslideshow, extra fields or old replies.
  Nav invalidates, never aliases on. Unapproved policies open no worker.
- Enforce ordered matching IDs within five seconds; missing halves, overlap,
  conflicting IDs, repeated rotation, future/old queued records and timeout fail
  closed. Selection clears previous metadata before any new attribution.
- Existing image-verified associations for the exact TV supply title/artist;
  unknown/other-TV IDs never borrow a prior caption. Stored digest is tagged as
  historical association evidence, not newly downloaded bytes. Snapshot input
  cannot impersonate slideshow evidence. Existing binding/history/current files
  remain byte-identical; no event creates a binding or verifier job.
- Simulate multiple ten-minute cycles and returning known IDs. Listener remains
  alive after the 90-second baseline expires; each real changed-ID triple lasts
  at most 900 seconds from receipt. Same-ID replay/on/pong/publication cannot
  renew it. Expired metadata clears, then later valid events can confirm again.
- Pinned-library socketpair tests assert one REST identity read, one WebSocket,
  five initial getters, one initial thumbnail and zero post-baseline requests,
  even across nav and multiple changes. Off/unknown frames stop without retry.
- Fixed owned sensor/old card/script IDs stay unchanged; five-language complete
  native templates bound event data to 900 seconds, old snapshots to 90. Existing
  actual cards remain untouched; no live rendering is inferred from offline tests.
- Unchanged full typing/security/isolation/coverage gates; production profile
  table empty, b8 remains off, no HA/TV access/build/publication. Actual ID reuse,
  hardware multiple cycles and natural sleep/no-wake safety are not certified.

## Local same-session ID probe acceptance (D-232)

- Existing receive-only policies remain receive-only. Production registry empty;
  boot/refresh/HA availability/explicit send without policy cannot open a worker.
- One exact injected policy triggers only on mode-on in its selected value/status
  field; off ends without probing, and unknown/malformed/duplicate-key/correlated
  notifications fail closed.
  Observed field names are not proof of actual firmware status-value semantics.
- One follow-up get_current_artwork maximum on the original socket after initial
  proof. No new client/open/connection, thumbnail, ping, mutation, polling/retry.
  Real pinned-library/socket-pair tests assert exact request and socket counts.
- Emit invalidation before the request; the parent clears current artist/title
  on receipt, without a synchronous HA acknowledgement before the send. Keep
  checking without stopping the pending worker, bounded to five seconds from
  actual parent receipt. Expired initial proof cannot trigger a request. Exact
  correlation and valid ID required; off/mutation/unknown/errors/timeouts/gaps
  cancel and disarm. Repeated on cannot extend deadline or send twice.
- Success emits bare diagnostic ID then ends/pauses. Same/old/new ID never calls
  image verification/binding lookup or republishes artwork. Preserve cards,
  one-shot/history and unchanged full coverage/security/typing gates.
- Stop/cancel, partial/binary/oversized frames, ping floods, stale/future queued
  results and missing socket cannot bypass bounds or reconnect. No hardware,
  sleep safety, installed-app change or publication follows from offline tests.

## Local event-session acceptance, 2026-10-17 (D-231; existing IDs unchanged)

- Default/absent background keeps the one-shot path and existing cards. Start,
  restart, idle and refresh open no TV connection. With no reviewed profile,
  even successful explicit send cannot arm an observer. No profiles are approved.
- On the exact injected offline policy, one successful explicit delivery may
  start one bounded isolated session; subsequent events use that same socket.
  After initial byte proof there are no GET/thumbnail/application ping requests.
  Server ping/pong is tested as transport traffic, not a no-wake guarantee.
- Mode-off, unknown/malformed/correlated frames, partial-frame deadlines,
  binary/fragment/size/rate/queue bounds and disconnects clear attribution and
  disarm without reconnecting. A known ID from an older session is not proof.
- Only the freshly verified initial baseline supplies image identity. Changed
  ID/mutation invalidates the epoch; same-ID/mode-on/duplicate messages cannot
  renew its age. Queued stale/future snapshots are rejected; after 90 seconds
  current information clears without new TV traffic. No artwork heartbeat makes
  cached data look current on the existing last_reported-based card.
- Stop uses the cancellation pipe and bounded close/kill/reap. A stuck/unreaped
  worker prevents a replacement or send. Bootstrap, environment isolation,
  resource limits, TV-only TCP guard, Linux filter and AppArmor child apply to
  the new task. No Supervisor token or user-configurable event-policy bypass.
- Real installed library tests run only on socket pairs/mocked network seams;
  real worker lifecycle tests install the H2 guard. Event schemas are expressly
  synthetic. Native Linux enforcement and actual event/sleep/mode behavior need
  separate tests/approval; no hardware result is inferred from offline success.

## D-230 experimental activation acceptance, 2026-10-16

- Off/missing/null background mode preserves one-shot behaviour; all five
  languages warn that read-only connections may wake a sleeping TV.
- Opt-in alone and start/boot/restart make no TV request. Only a successful
  explicit delivery enables session authorization and the first bounded read.
- Initial enrollment is permitted only in that post-delivery session. Pin at
  most 32 exact per-address device identities in a 16 KiB atomic document; do
  not silently replace/evict a pin or recover a damaged primary into enrollment.
- A different identity is rejected before Art connection. Stored-token rejection
  cannot switch to tokenless or retry. Any failed/non-Art read disarms polling;
  refresh alone cannot re-arm. Known identity plus thumbnail digest, not last
  sent metadata or content ID alone, determines the current caption.
- Natural no-motion sleep/no-wake is explicitly deferred, not passed. Local beta
  building is approved; publication and further live mutation are separate gates.

## Optional background current artwork candidate 2026-10-16 (earlier D-226 gate)

- Missing/null/false background option preserves the complete one-shot path,
  old state records and standard card; only a real boolean true opts in.
- Background boot/start/restart/idle cannot send an image. An explicit send
  command uses the unchanged bounded runner, isolation and loading completion.
  Script ID/card references remain; opt-in migration is documented, never automatic.
- Validate fixed JSON commands, limits and fresh timestamps; atomically consume
  request IDs before sending. Duplicates, expired requests, a full journal,
  restart and an uncertain dispatch do not create a second delivery.
- No production no-wake policy is enabled before hardware validation. Missing
  policy/device identity cannot start a TV worker. Missing tokens cannot start
  one without an explicit reviewed tokenless-channel grant (D-228); malformed
  grants and token/grant combinations fail before loading the TV library.
  A rejected stored token never triggers a tokenless retry. A failed/off-mode
  observation disarms reads; idle/refresh must not reconnect or pair.
- The read worker allows only getters, uses the TV-only connect guard, targets
  a single thumbnail, bounds D2D lengths, checks identity/mode/ID consistency
  and closes connections. No selection/upload/power/WOL/write request is allowed.
- Mapping requires the exact processed preview hash and a successful isolated
  image comparison, not a restored caption. Device/ID/thumbnail mismatch yields
  unidentified. Bound/atomically recover mapping storage independently of history.
- Publish only the fixed app-owned Core state with bounded metadata; ownership
  collisions and 401/403 fail closed. Display-escaped metadata, missing/stale
  states, Core restart and app failure cannot show an old title as current.
  Unchanged heartbeat metadata uses no changing timestamp or force_update flag.
- Complete five-language option/script/card instructions preserve source/artist/
  colour options and technical IDs. Run unchanged full quality gates; native
  memory/confinement, real Recorder growth and no-wake hardware checks remain
  separate live/build gates. No publication without explicit approval.

## Next artist/language candidate (D-221/D-222; existing A–J IDs unchanged)

- Missing/null/empty/no-filter artist defaults preserve old configurations and
  standard cards. Whole known labels normalize deterministically; partial,
  unknown or multi-artist inputs fail static validation or warn/helper-fallback.
- Every retained catalogue attribution resolves to a bounded distinct key/label;
  unknown, attributed and workshop labels are transparent. Do not guess names.
- Valid static/helper artist wishes are Commons-only; all other providers report
  ignored artist state in log and run record. Provenance is recorded.
- Artist plus colour plus shape are an intersection before network requests.
  Sent/upload/quarantine exclusions remain; empty/exhausted selections never
  recycle or relax artist/colour, preserve current TV/preview/caption and clean up.
- Complete optional native favourite-artist/colour cards reuse camera/timer/script
  without HACS/SSH/configuration.yaml. Document total vs unsent counts.
- en/de/fr/es/it generated config files cover every schema field with translated
  names/help and identical technical values. English default remains available.
- IT setup/colour and five-language artist guides have reciprocal language links,
  complete verified card YAML, unchanged IDs/actions, explicit availability and
  compatibility. Translation/source tests do not claim live-language evidence.
- Full unchanged quality gates, then approved native ARM/Intel release gates;
  live installed-app/helper/card/TV validation requires separate confirmation.

## Commons catalogue expansion (D-211; existing IDs unchanged)

- Exactly 400 unique IDs, pinned hashes and title/artist pairs; retain the first
  166 entries identically to the unchanged b4 manifest and exclude its 34 deferrals.
- Add 234 actually inspected JPEG works with source-page evidence and recorded
  physical-proportion checks; all originals meet width >=3000 and the 2.5% bound.
- Keep the strict approximately 1% rule unchanged; 152 prepared source ratios
  meet it. Larger synthetic 200/400 catalogues stay within the ten normal
  metadata-request ceiling, and exhausted history makes no requests/no repeats.
- Retain research/preview and test source filters, search and reversible local
  bookmarks. Production metadata-only audit must accept all 400 current pins;
  it does not replace native-image, decoding or television validation.

## Source-default UX amendment (D-210; existing IDs unchanged)

- New-install Supervisor defaults and runtime missing/null-source defaults agree
  on `wikimedia_commons`; Commons is first, with all four source IDs retained.
- Explicit saved Chicago, Cleveland, local-media and Commons selections are
  preserved. Shape/fit settings, optional helpers and history stay compatible.
- Synthetic production runs with missing, null and explicit Commons sources
  select distinct Commons works, update the preview and leave scratch empty.
- No network discovery or live HA/TV change is part of this local amendment.

## Additional post-beta Commons criteria (D-206; existing IDs unchanged)

- Exactly 50 unique curated metadata entries, no artwork files. Exclude the two
  research entries whose US public-domain basis remained open.
- Static/helper source `wikimedia_commons` needs no key. Unsupported optional
  filters are reported. Offer only curated IDs/pinned uploads with current Public
  Domain or canonical CC0 rights, no attribution requirement/declared restriction.
- Lazy batches of five records maximum use existing HTTPS/public-IP gateway,
  pacing, allowance and deadlines. Ten normal metadata requests maximum; errors,
  missing files and exhaustion finish cleanly, never unboundedly.
- Download returned bounded JPEG renditions with their actual dimensions; never
  huge originals when thumbnail metadata is missing. Shared byte/decode/upscale/
  fit guards apply, including safe landscape contain fallback with margins.
- Repeated synthetic production runs record distinct history, match preview to TV
  payload/caption and leave scratch empty. Fully sent catalogue does not recycle;
  uncertainty is not classified as a permanent exclusion.
- Public b2 remains unchanged. New native ARM/Intel validation and approved
  Green/TV tests are release gates; local tests do not substitute for them.

These are product-level acceptance criteria. Unit and integration test details should be derived independently during implementation.

## A. Installation and packaging

- [ ] A public test repository can be added through Home Assistant's repository UI or one-click link.
- [ ] Home Assistant Green discovers the app without SSH or local file copying.
- [ ] Home Assistant Green installs the pre-built `aarch64` image.
- [ ] An `amd64` image is built from the same release source.
- [ ] Installation requires no `configuration.yaml` change.
- [ ] The app exposes understandable option names and descriptions in the Home Assistant UI.

## B. Configuration

- [ ] A missing television IP prevents start with a clear validation message.
- [ ] Static source, department, style/period, and colour filters work without helper entities, for exactly the filters that the selected source supports according to the published capability matrix. For the first beta, that is department and period for the Cleveland Museum of Art, and period for the Art Institute of Chicago; no source supports colour. A valid filter value that the selected source does not support is not applied and is reported as unsupported (B8). A value that matches none of the offered values is rejected as invalid (B5). In the first beta, that is any style value, any Art Institute department value, and any colour value other than "any" or a no-filter synonym (`all`, `random`, `none`, or an empty value).
- [ ] A valid helper value overrides its static value.
- [ ] A missing or unavailable helper falls back to the static value.
- [ ] Invalid filter values are rejected or normalized predictably.
- [ ] Landscape-only and fit-mode defaults preserve the full artwork.
- [ ] A television address that is not an RFC 1918 private IPv4 literal (including link-local `169.254.0.0/16`, loopback, unspecified, multicast, broadcast, and container or Supervisor network addresses) is rejected with a clear validation message.
- [ ] A filter the selected source does not support is visibly reported as unsupported (option description, log, and run record) and never silently claimed to work.

## C. Candidate selection

- [ ] Combined filters are applied together, but only the filters that the selected source supports according to the published capability matrix. For the first beta: department and period together for the Cleveland Museum of Art, and period for the Art Institute of Chicago. A valid filter value that the selected source does not support is not applied and is reported as unsupported (B8).
- [ ] Portrait and square candidates are rejected when landscape-only is enabled.
- [ ] Previously sent identifiers are skipped across app restarts.
- [ ] Strict near-16:9 selection never exceeds its budget of 30 remote dimension requests, and local header inspection stays within its separate allowance.
- [ ] The complete run never exceeds its 120-second default total deadline by more than a small shutdown allowance.
- [ ] A restrictive filter combination can fall back from strict near-16:9 to an eligible landscape work.
- [ ] When no candidate exists, the app exits cleanly and does not call the television upload operation.
- [ ] Provider network, parsing, and empty-result failures do not create infinite retries.
- [ ] Art Institute of Chicago candidates are public-domain (CC0) works only.
- [ ] Cleveland Museum of Art candidates are CC0 / open-access records only, and the downloaded image is the documented print JPEG, never the original TIFF.
- [ ] A run without a matching candidate finishes cleanly within 70 seconds by default.

## D. Image preparation

- [ ] A landscape image with a non-16:9 aspect ratio appears completely on a 3840 × 2160 canvas in `contain` mode.
- [ ] Default `contain` mode does not crop any artwork pixels.
- [ ] Black margins are used by default where necessary.
- [ ] `cover` mode crops only when explicitly selected.
- [ ] EXIF-rotated input is oriented correctly.
- [ ] RGB, RGBA, palette, and grayscale inputs produce a television-compatible JPEG.
- [ ] Excessive dimensions, pixel counts, or download sizes are rejected safely.
- [ ] The preview bytes correspond to the processed television image.

## E. Television behavior

- [ ] A successful run uploads one image and selects it as active art.
- [ ] Pairing or authorization requirements are reported clearly.
- [ ] Connection timeouts and television rejection terminate cleanly.
- [ ] Failed uploads do not enter the image into sent history.
- [ ] A successful run (upload and selection confirmed) enters exactly one provider-qualified identifier into history.
- [ ] Starting the app again does not resend the same work while unused eligible works remain.
- [ ] Upload succeeded but selection was refused: the work enters the TV-upload exclusion ledger, not the sent history, and it is not uploaded again on the next run.
- [ ] Upload succeeded but the connection was lost during selection: the work enters the TV-upload exclusion ledger, and it is not uploaded again on the next run.
- [ ] The process was killed after the upload: the work is excluded on the next run (upload ledger or uncertainty quarantine) and is not uploaded again on the next run.
- [ ] Confirmed sent history, current artwork, and dashboard preview change only after the television confirms selection.

## F. Cleanup and persistence

- [ ] Temporary downloads are removed after success.
- [ ] Temporary downloads are removed after provider, decode, processing, and upload failures.
- [ ] Repeated runs do not grow temporary storage.
- [ ] History survives app restarts and version upgrades.
- [ ] A corrupt history file is quarantined or recovered without crashing the app.
- [ ] Metadata caches enforce documented size and age limits.
- [ ] The generated preview cannot be selected as local source artwork.

## G. Dashboard documentation

- [ ] Documentation contains one complete copy-and-paste-ready dashboard card.
- [ ] The card displays the latest preview.
- [ ] Tapping the card starts the app.
- [ ] The loading indicator always returns to idle after success, clean no-match, or failure.
- [ ] **Release-blocking:** across repeated live tests on Home Assistant Green, each newly delivered image is displayed without a stale browser cache, using the single documented, UI/API-based refresh mechanism.
- [ ] The documented setup requires no `configuration.yaml` edit, no configuration-folder mapping, no SSH step, and no manual file modification.

## H. Quality and compliance

- [ ] Unit tests cover every bounded loop and fallback branch.
- [ ] Integration tests use mocks or independently authored fixtures and require no live provider or television.
- [ ] Logs contain no secrets or private API payloads.
- [ ] Dependency licenses and notices are complete.
- [ ] No code, tests, documentation, assets, or structure from excluded predecessor projects appear in the repository.
- [ ] The chosen project license is approved by the user before publication.
- [ ] A full live run is completed on Home Assistant Green only after explicit user approval.

## I. Optional artwork information (post-beta, D-202)

- [ ] Unset option leaves the existing preview/card and HA request set unchanged.
- [ ] An explicit dedicated Text helper displays the published title, artist and museum; missing fields are omitted, text is escaped, and long fields are abbreviated within 255 characters.
- [ ] No-match, TV failure and stop-before-publication leave old metadata untouched. Clear-before-preview and write-after-preview ordering is verified; failed clear retains preview, later failure leaves no caption.
- [ ] At most one scoped GET and two fixed input_text.set_value POSTs use one shared two-second budget, without retries/redirects/token leakage or new privileges; 401/403 stops further authentication attempts.
- [ ] Complete native card/helper instructions need no HACS/SSH/configuration.yaml; the last helper state restores after HA restart with no Initial value (live test required).
- [ ] New versioned native ARM/Intel images, source/signature gates and an approved Green upgrade/card test pass before the feature is advertised as released.

## J. Commons colour and 1000-work update (draft, D-212/D-213)

- [ ] All 400 baseline identities/pins remain; 600 new distinct artworks have
  recorded rights, full-reproduction, visual and duplicate decisions, not just
  eligible search dimensions. Source width/ratio/JPEG limits stay unchanged.
- [ ] All 1000 works have source-bound profiles with full area distributions,
  top <=3 distinct families, no invented monochrome colours and retained palette.
- [ ] Single colour defaults to any, including older missing/null options.
  Every offered English/German alias resolves correctly; unknown/multiple values
  are invalid. Other sources visibly ignore unsupported colour wishes.
- [ ] Commons filters before metadata, with exact source pins; missing/stale
  profiles cannot match. No extra image analysis/downloads occur on Green.
- [ ] Tests cover all families, stale sources, empty matches, sent/upload-ledger/
  quarantine exclusions, metadata failures and shape fallback without colour
  relaxation. No-match preserves TV/preview/caption/history and finishes bounded.
- [ ] Research preview and full unchanged quality gates pass; no private artwork
  bytes are bundled. Native/publication and live installation/testing gates stay
  separate and must pass before advertising the update as released.

## Amendment log

- **2026-10-09:** append draft section J for the approved local colour/1000-work
  update. Historical first-beta colour limitations below remain dated history;
  existing A–I position-based acceptance IDs do not change.

- **2026-10-04:** append section I for the user-approved optional attribution
  feature. Existing A–H position-based acceptance IDs stay unchanged.

- **2026-09-26: Phase 1 Codex review of commit `d42adf5`, with user decisions.**
  - New items were appended at the end of their sections, so the position-based IDs used in `ARCHITECTURE.md` Appendix A stay stable.
  - Added: B7 (local IPv4 address), B8 (unsupported filters visibly reported), C9–C10 (AIC and CMA rights and renditions), C11 (no-match within 70 s), and E7–E10 (TV-upload exclusion ledger scenarios).
  - Reworded in place:
    - B2 and C1: distinct filter dimensions.
    - C4: 30 remote dimension requests.
    - C5: 120 s deadline.
    - E5: history changes only after upload *and* selection are confirmed.
    - G5: preview freshness, now release-blocking.
    - G6: no configuration edits of any kind.
- **2026-09-26: Codex final gate review of commit `9352e77`, with user decisions.**
  - Reworded in place: B7 now requires an RFC 1918 private IPv4 literal and names the rejected ranges (Q-12, D-125). No IDs changed.
- **2026-09-27: Phase 3 gate, with user decisions.**
  - Reworded in place: B2 and C1 now apply only to the filters that the selected source supports according to the published capability matrix. For the first beta: Cleveland supports department and period, the Art Institute period, and no source supports colour (D-146, D-152).
  - Q-25 is resolved with option (a): the first beta ships without a colour filter.
  - A valid filter value that the selected source does not support stays visibly reported (B8). A value that matches none of the offered values, such as a style value or a colour other than a no-filter value, is rejected as invalid (B5). No IDs changed.
