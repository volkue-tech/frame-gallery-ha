# Current TV artwork beta plan

## Current amendment D-230 — experimental b8 locally authorized

The user explicitly accepted default-off experimental observation and its
wake-risk warning, deferring natural no-motion sleep validation. Local b8
building is authorized; publication/live installation is not authorized by this
amendment. Earlier absolute no-wake activation gates below are historical.

The real service may arm only after an explicit successful delivery, proven by
a newly changed valid current record with a TV ID, not exit code 0 alone.
Permit initial device enrollment in that session, then enforce bounded atomic
per-address device pins. Persist neither the observation grant nor an automatic
resume permission. Boot/restart stays passive; any failed/non-Art read disarms
until another successful explicit send. Refresh cannot re-arm. Update all five
guides/configuration warnings. Actual no-wake behaviour, transitions and Recorder
impact are open checks, not passed tests or universal compatibility claims.

Requested 2026-10-16: plan the next beta around persistent TV artwork
associations and optional dashboard information about the artwork actually
observed on the television. The user subsequently approved local implementation
of this exception to the [1.0 feature freeze](stable-1.0.md), but not publication.
The public version remains 0.1.0b7; assign the next beta number at its release gate.

The [synchronization assessment](current-tv-artwork-sync.md) proposes optional
background operation in the existing app and HA state publication without
extra helpers. D-225 is accepted for local implementation; D-226 keeps automatic
TV connections blocked until a separately authorized no-wake/device validation.
The [candidate guide](../../frame_gallery/CURRENT_ARTWORK.md) describes the local
implementation and its explicit activation limits. Enabling that mode requires a one-time
update to the existing send script; legacy users are not migrated silently.

## User experience

With background mode disabled, the existing preview, camera, timer, script and
optional last-delivery caption keep working without migration or extra setup.
Users opting in keep the script ID/cards but update the script body once.
The preview describes the last
successful Frame Gallery delivery, not every subsequent remote-control change.

Offer an optional native dashboard variant showing the current work's title,
artist and source, with the time of the last successful observation and a clear
connection status. Existing colour and artist selectors still choose the next
work; they do not describe or restrict what is currently on the TV.

The feature should follow manual artwork changes and TV slideshows through
automatic, read-only refreshes when enabled. Include a distinct read-only
refresh action; it must never call the normal image-upload start action.
Refresh intervals and stale-data limits remain to be chosen after testing.
Describe this as periodically checked, not instant or continuously guaranteed.

| Observation | Current artwork information |
| --- | --- |
| Art Mode confirmed and content ID reliably mapped | Title, artist, source and last checked time |
| Art Mode confirmed but content ID unknown | Artwork not identified; no guessed attribution |
| Ordinary TV operation confirmed | TV in use; no claim that the last artwork is currently visible |
| TV unreachable or connection refused | TV unavailable; do not infer standby from refusal alone |
| Authentication rejected or API unsupported | Specific connection limitation; no automatic pairing attempt |
| Observation expired or request failed | Current artwork unconfirmed; any retained last observation explicitly marked stale |

Do not place a known-current title below an unrelated last-delivery preview.
The first scope is current metadata and status, not a live TV screenshot.
If the existing preview is shown alongside it, label it as the last sent image.
Keep existing last-delivery information separate from current-TV information.

## What the read-only investigation established

On the tested Frame, `get_current_artwork` returned `MY_F0176`. The content-list
metadata contained dimensions and other TV fields, but no title or artist.
A target-specific TV thumbnail matched the catalogue work **Houses by the
Shore** by **Frank Knox Morton Rehn**, `commons:25027786`.

The comparison used 1,115 local cached images, with a clear best match and visual
confirmation. The prior stored caption suggested a different work and was
rejected by that comparison. Last-delivery or restored helper text therefore
cannot establish a TV content ID's attribution.

Local diagnostic evidence is retained in
`build/readonly-MY_F0176-verified-attribution.json` and
`build/readonly-MY_F0176-image-matches.json`. These ignored files are local
evidence, not release dependencies. Do not ship this user's TV ID as a global
catalogue association. The finding demonstrates feasibility on one tested TV,
not a guarantee for every Samsung model or firmware.

The current upload path receives a TV content ID in memory, but the persisted
current record and history do not retain the TV-ID-to-work association. The app
is also one-shot (`startup: once`, `boot: manual_only`), so it cannot observe
later TV changes after it exits.

## Proposed product requirements

- Persist trustworthy associations between a television, its content ID and the
  source-qualified work ID. Retain title, artist, source, attribution links,
  relevant rights information, image identity evidence and association provenance.
  Work metadata may be unavailable; never invent an artist for a local file.
- Scope associations to a stable, verified television identity, not only its IP
  address. Handle IP changes, replacement televisions, deleted content and
  conflicting or reused IDs without attributing an old work to a new image.
- Capture associations for future confirmed uploads without assuming upload
  confirmation means current selection. A successful upload followed by failed
  selection can leave a known work on the TV without making it current.
- Preserve existing sent history, upload ledger and uncertainty quarantine.
  Unconfirmed uploads and missing IDs must not create speculative associations.
  A mapping-write failure must not erase upload evidence or trigger a duplicate
  upload merely to repair the mapping.
- Address the existing concurrent-client upload ambiguity before treating an
  upload event's ID as proof of image identity (R-30). Where identity cannot be
  established, keep the association unverified and show no current attribution.
- Resolve the observed TV ID locally where a verified association exists, for
  Commons, museum sources and known local-media metadata. Normal refreshes must
  not require provider searches or catalogue-wide image comparisons.
- Survive app updates, HA restarts and interruptions with bounded persistent
  storage, recoverable migration and documented backup behaviour. Define how
  limits and deletion affect older associations; no silent incorrect fallback.
- Keep setup compatible with Home Assistant Green. Prefer native cards and
  UI setup, with no required HACS extension, SSH or `configuration.yaml` edits.
- Provide complete optional card examples, setup and troubleshooting in
  English, German, French, Spanish and Italian. Keep technical IDs and values
  stable and English as the default documentation language.

## Read-only synchronization requirements

Synchronization must never upload, select, delete, change Art Mode, send a power
command or initiate pairing. Do not wake a standby TV to obtain its content ID.
If even a connection attempt wakes the tested TV, disable automatic attempts in
that condition and resolve the limitation before enabling background refresh.

Use bounded requests, timeouts, connection cleanup and backoff. Stop blind
authentication retries and avoid overlapping pollers. Coordinate reads with
uploads, and account for an artwork changing while its ID or mode is being
queried. An inconsistent observation must not become a confident current title.
No indefinite socket, worker, image cache or temporary-file accumulation.

Reuse only explicitly authorized pairing credentials. The investigation's
temporary access to an existing integration credential does not authorize a
shipped feature to read Home Assistant's private storage. Keep credentials out
of artwork records, helper values and logs; any new permissions need review.

## Design questions recorded before implementation

Historical planning gate: choose and record the architecture only after the required repository reading
and a focused review of current official interfaces. The product requirements
above do not select an implementation. Resolve these together:

1. How optional background observation and an explicit read-only refresh work
   alongside the bounded one-shot uploader, without changing normal Start into
   a permanent service. Compare supported app/integration mechanisms against
   setup effort, permissions and lifecycle constraints; do not introduce a
   mandatory companion integration or custom dashboard extension by assumption.
2. How HA exposes current status, timestamps and metadata, separately from the
   existing last-delivery helper. Account for helper length limits and stale
   restored values; do not promise a sensor or service that does not yet exist.
3. How the TV is identified, uploads are correlated, mappings are validated and
   persisted, and deleted/reused IDs are detected. Specify storage limits,
   recovery, schema migration, locking and backup treatment.
4. Which mode/availability evidence can safely gate connections without waking
   the TV; choose refresh/backoff/freshness bounds and test them on the Green.

The local implementation approval supersedes the planning-only restriction;
D-225/D-226 and the specification amendments record the selected design.
The list above remains the design/validation trace, not a second approval request.
During initial planning, record decisions and specification/test amendments before
requesting implementation approval. If automatic observation requires a larger
architecture change, present that tradeoff rather than silently reducing the
feature to last-sent captions or manual refresh only.

## Existing TV pictures and excluded work

The first release need not identify every picture already stored on a TV.
Unknown legacy or Samsung-store artwork stays unknown. Plan a separately
approved migration or local thumbnail-assisted matching path if broad legacy
coverage is wanted; no automatic bulk scan or external recognition service.
The verified local example can inform a test or explicit migration, not a
hard-coded public association.

History reset, replaying existing TV content, deleting TV images, new providers,
new artwork curation and additional filter features remain outside this scope.
This update must not turn the read-only refresh control into a selection action.

## Acceptance and release gates

- [x] Approve the technical design, explicit current-versus-last-sent semantics,
  legacy coverage and specification/acceptance-test amendments.
- [x] Approve local implementation separately; preserve all existing quality gates.
- [ ] Test per-TV isolation, ID conflict/reuse, upload correlation, failed
  selection, missing metadata, atomic recovery and unchanged duplicate protection.
- [ ] Test manual changes and slideshows, unknown IDs, ordinary TV use, failed
  authentication, unsupported API, standby, network loss, stale restoration and
  overlapping reads/uploads. No stale title or unrelated preview claimed current.
- [ ] Verify bounded reads, backoff, shutdown, storage and credential redaction;
  specifically test that read-only synchronization does not wake the TV.
- [ ] Review complete five-language setup/card examples and unchanged standard
  cards. Run the full unchanged suite and native ARM/Intel release checks.
- [x] Obtain separate private native/Green/Frame test authorization, without
  publication and with existing cards preserved (2026-10-16).
- [ ] Complete Green/Frame verification, including physically observed no-wake,
  user-observed display checks and existing-card compatibility. The first private
  Green start exposed D-227's stdin-EOF defect; its corrected ARM container
  transport/stop test and sustained Green stdin operation passed. Full current
  observation, natural sleep and transition validation remain open.
- [ ] Obtain publication approval, freeze the next beta version, publish matching
  sources/images and verify the Store handoff. Remain beta pending feedback.

Local implementation and subsequent private native/Green/Frame tests are now
authorized. Activation of production automatic TV reads, version bump, public
builds and publication remain separate, unapproved gates. Public b7 is unchanged.

## Private validation observations, 2026-10-16

- The first Green service exited on stdin EOF. D-227's checksum-guarded BusyBox
  descriptor correction passed native ARM stdin/SIGTERM/cleanup checks, the
  unchanged 5311-test gate, and sustained startup on the Green.
- One device-info GET after user-confirmed manual power-off returned at
  15:04:04 UTC without waking the display, per the user's observation. This is
  not validation of the complete Art getter, natural sleep or every firmware.
- The user clarified automatic no-motion sleep is the real everyday case.
  Samsung documents [Sleep After separately from Night Mode](https://www.samsung.com/uk/support/tv-audio-video/how-to-use-art-mode-on-the-frame-tv/).
  Test manual off, automatic no-motion sleep and any used darkness/automation
  cases separately; do not infer equal network behaviour from a blank display.
- After the user restored Art Mode and authorized one test delivery, the actual
  background command sent commons:65256137 in 14.2 seconds. They confirmed the
  new water image. Existing card/configuration hashes remain unchanged; the
  normal last-delivery preview/caption values updated together.
- The one-read diagnostic then returned not_authorized before any TV getter:
  no own token had been stored after successful delivery. The REST device flag
  TokenAuthSupport="true" does not resolve that Art-channel capture/grant gap.
  Investigate it without inventing a token or importing integration-private
  credentials; no automatic policy is enabled and no current title is claimed.
- A subsequent isolated connection-only probe on the Green completed in
  1.294 seconds with connect/ready events and no token field. D-228 replaces
  the overly strict token-only assumption with an explicit default-off internal
  tokenless-channel grant, not an automatic fallback or UI option. No production
  grant was enabled. This probe did not read a current ID/thumbnail or prove
  full observation/no-wake behaviour. Its temporary app/Store entry were removed;
  own source/evidence remain local and the previous QA app/state are preserved.
  The unchanged full local gate after D-228 passed: 5314 tests, 15 existing
  platform skips, strict host/Linux typing and 100% whole/mandatory line/branch
  coverage. The current installed QA build remains live4; no new beta was shipped.
- Separate private QA packaging/hardware hooks remain git-ignored and are not
  public feature controls. The public b7 app and options are unchanged. All
  private source-transfer sessions are closed. Backups: public pre-test
  add0e7a9; private QA state 98515fd8 (TV-secret exclusions unchanged).
- Backend template freshness was observed across a minute: last_reported
  advanced while last_updated stayed unchanged. The temporary template was
  undone and the extra tab closed. REST JSON kept its cached timestamp, so the
  unchanged REST value is not a valid failed-heartbeat assertion. See the
  pinned [Core reporting/serialization code](https://raw.githubusercontent.com/home-assistant/core/2026.10.1/homeassistant/core.py).
  This does not by itself complete real-card or Recorder-volume acceptance.

Physical no-motion-sleep and full authenticated observation remain open.
Do not mark current attribution, slideshow following, recovery or no-wake
acceptance complete from the successful uploader or the manual-off REST probe.

The user subsequently deferred natural sleep because the living room is
occupied. Continue other work under their no-wake working hypothesis, without
changing the disabled production policy or representing that physical test as
passed. They separately confirmed Art Mode for connection-only diagnosis;
no second upload, selection or power command is included in that confirmation.

## Complete read-only Art-Mode validation, subsequently authorized

The user then explicitly authorized the complete read without a picture change.
At 18:06:48 Europe/Berlin the isolated TV path confirmed the exact device,
Art Mode, MY_F0182 and its targeted thumbnail, then rechecked ID and Art Mode.
The read took 3.643 seconds; a separate isolated comparison with the unchanged
exact processed preview passed in 1.675 seconds. The persisted association is
commons:65256137, Surface of Brofjorden, W.carter; its own test backup is da2c2962.
Normal HA API readback independently returned artwork and matching metadata.
Both existing dashboard hashes and the preview hash were unchanged.

D-229 corrects the observed one-second handshake timeout and disables the pinned
library's artificial remote-key delay for getters. The five-second read budget,
separate five-second image-proof budget, guards, isolation and no-retry rule stay
unchanged. The final unchanged local gate passed: 5314 tests/15 unchanged skips,
strict host/Linux typing and 100% whole/mandatory line/branch coverage.

The test used a disposable app with a copy of two own non-secret QA records and
read-only media; it did not migrate or overwrite the original QA/public app data.
The real template displayed fresh title/artist/source, then the stale fallback
without another TV connection. Undo restored the original developer template;
no card was saved. This establishes the single-known-image read/mapping/metadata
path, not slideshow transitions, live migration, sustained Recorder behaviour,
natural-sleep/no-wake or automatic resume. No automatic policy or publication
was enabled, and no upload, selection, power or Art-Mode write was sent.
