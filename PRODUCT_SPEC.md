# Product specification

## Explicit initial already-on synchronization, 2026-10-19 (D-239)

With background mode and an existing resume_state_entity configured, the first
cached HA on sample may authorize ONE experimental initial read, even when
last_changed is old. The user explicitly accepts the connection-side-effect
risk; HA on is not Art Mode proof. The first sample consumes the opportunity,
including errors/off/unknown, so there is no delayed startup retry. Retain the
original later fresh-edge recovery and shared per-process attempt bounds.
No image/power/mode command, enrollment, personal ID or installed-card change.
Require intact exact-target/device history, fresh real Art/ID/image proof and
same finite receiver. Defaults remain passive. Preserve 90/900 proof ages and
document static-picture age-out honestly. Offline/native gates before the
authorized bugfix publication; no live HA/TV test in this implementation round.

## Experimental post-sleep resume, 2026-10-18 (D-238)

An optional existing Samsung HA resume_state_entity, with background enabled,
may trigger one read-only revalidation after a fresh observed off-to-on edge.
User explicitly accepts unverified connection side effects for this experimental
path. No new image/power/mode command, timer retry, enrollment, card edit or live
test. Require archived target/device identity and a new real Art/image proof;
boot-on/unknown/stale/error cannot restore a caption or authorize blind reads.
Installed b10 stays stopped; beta publication follows green offline/native gates.

## Local b9 recovery/diagnostic fix, 2026-10-18 (D-237, unreleased)

User authorizes local diagnosis and offline fix preparation only; b9 stays
stopped, installed cards stay unchanged, with no HA/TV call or publication.
Do not present the missing raw cause of the 19:54:55 b9 failure as identified.
For strictly decoded, timely slideshow notifications only, incomplete order or
five-second pending expiry clears caption and discards pending state while
retaining the SAME finite receiver. A later complete fresh triple is required;
never accept late halves, the discarded event as a new selection, bare IDs or
same-ID proof renewal. No attribution is preferable to a guessed caption.
This narrowly replaces D-233's whole-session termination for those valid but
non-confirming sequences, not malformed/unknown/replayed/stale/future input,
off/standby/disconnect, identity, resource or publication failures. No new
request, connection, automatic resume, permission, helper or card ID.
Bound parent diagnostics to fixed allowlisted codes and one recovery warning
per explicit session; never log raw payloads, exception bodies or credentials.

## Complete delivery associations, 2026-10-18 (D-235)

Every TV-confirmed successful selection must retain a bounded, atomic local
association, including ordinary one-shot sends with background mode disabled.
Use the actual TV identity learned from the delivery's existing capability
response and its acknowledged upload ID; neither IP address nor content ID
alone is a globally unique artwork key. Keep provider ID/title/artist/source,
exact uploaded-image digest and provenance. Never guess an identity, bundle a
user's associations, or require manual ID entry, new HA rights or another TV
connection. Failed/uncertain uploads do not create successful associations.

Separate historical confirmed-upload associations from current-display proof.
The current artist card may resolve exact device+ID associations only inside
the validated observation/event path, clears stale/unknown/non-Art data, and
never wakes/reconnects merely to obtain metadata. Existing verified bindings,
history, cards and source configuration remain compatible. Preserve metadata
across updates/restarts and history reset; document bounds and uninstall loss.
Unsupported/missing device identity or persistence failure must be explicit,
not silently attributed to another TV. Keep background mode optional/default
off with firmware/sleep limitations, and no hardcoded personal TV identity.

User subsequently requests the complete coherent feature, Green/ordinary
HAOS compatibility without special permissions, and authorizes building and
publishing the next beta after successful testing. No additional live TV
connections are authorized by the implementation request; b8 stays off.
Native release checks and exact new-candidate evidence remain required.

## Regular event-service integration, 2026-10-18 (D-234, local only)

Keep the production profile table empty, background off by default and old
cards/one-shot behaviour unchanged. A new background delivery receipt includes
the SHA256 of its actual target address (no plaintext address in current.json).
Only fresh changed receipt bytes with a valid TV ID and matching target digest
may arm observation. Old/missing/different target evidence cannot authorize a
connection; existing histories and verified associations are not rewritten.
Bind receipt parsing to those same bytes, not a second racing file read.

Any failed owned current-state publication stops and latches the service without
another write attempt. Only the observed exact unsolicited go_to_standby object
under the slideshow policy clears metadata and ends as a normal pause. Never
turn it into a command or reconnect. Regular-entry integration is offline-tested
with injected I/O; prior private hardware runs are not exact new-runtime proof.
Native ARM/Intel checks are explicitly deferred to the later release round,
before publication. No GitHub, live activation or publication is authorized here.

## Local event-confirmed slideshow attribution, 2026-10-17 (D-233)

The user authorizes implementation and offline tests only, based on the lab4
slideshow notifications and physical confirmation. No further HA/TV connection,
installed-app change, container build, version bump or publication. Keep b8 off,
existing cards/IDs/state/history intact and the live device-policy registry empty.

An explicitly injected slideshow contract requires this ordered triple within
five seconds: image_selected with is_shown Yes and valid content_id/matte fields;
auto_rotation_image_changed with the identical current_content_id and exact
observed type shuffleslideshow; then art_mode_changed/status on. Reject extra,
correlated, malformed, stale/future, reordered, overlapping or conflicting data.
Navigation nav clears attribution/pending selection but is not on or a reason
to reconnect. Mode-off, errors and disconnects disarm the existing session.

Clear old metadata on selection/navigation. Only a completed triple may consult
existing image-verified device+ID associations; unknown IDs remain unidentified.
Do not create or rewrite a binding, infer from last-delivery metadata or invent
a new thumbnail hash. Mark this as slideshow evidence, distinct from a fresh
thumbnail: any carried digest references the stored association, not new bytes.
Undetected server-side ID replacement/reuse is not ruled out by events alone;
do not claim otherwise. The D-232 bare-ID request still cannot restore metadata.

The byte-proof baseline expires after 90 seconds; a completed changed-ID triple
expires at most 15 minutes after its actual receipt, supporting the observed
ten-minute slideshow. Duplicate same-ID triples/on/pongs/publications never
renew confirmation. Expiry clears metadata but keeps the bounded receiver alive
for later transitions, not a retry or new request. Incomplete triples time out
after five seconds. Keep the one initial device/mode/ID/thumbnail proof and zero
post-baseline application requests, polling, thumbnail transfers or reconnects.

Existing four-field observation JSON remains unchanged by default; only new
slideshow observations add an evidence tag. The optional five-language complete
card template understands the 15-minute event limit with a 90-second fallback.
Existing installed cards are never edited; their old shorter limit remains.
Multiple simulated cycles are offline evidence only; natural sleep/no-wake and
multi-cycle hardware validation remain separately authorized follow-ups.

## Local one-shot same-session ID probe, 2026-10-17 (D-232)

The user authorizes local implementation/offline tests only: no HA/TV access,
installed-test-app update, image build or publication. Public b8 stays off and
existing cards unchanged. This narrowly amends D-231's receive-only phase.

An exact injected/reviewed software policy may permit one get_current_artwork
request on the already established, initially verified Art websocket, triggered
only by a strictly validated Art-Mode-on notification. No approved production
policy exists. The observed event/status key shape does not establish its value
semantics; on/off examples remain offline fixtures pending separate validation.
Mode-off still terminates: never hold/reconnect through off to await on.
An expired initial image proof cannot trigger a follow-up request.

At most one follow-up ID request per entire session, not one per duplicate or
timer tick. Send directly on the existing bounded transport, never through a
getter that can reopen a socket or silently discard intervening events. Bound
the reply wait to five seconds, retain cancellation/frame/queue/rate bounds,
match the exact request correlation and reject unknown/mutating/error replies.
Duplicate on messages while waiting cannot cause another request or extend the
deadline. Stop the session after success or failure, with no retry or thumbnail.

Emit invalidation before probing; the parent clears attribution when consuming
that event (there is no synchronous HA publication acknowledgement). A new or
repeated ID alone cannot create/restore a binding, refresh the 90-second image proof or
show an artist/title as current. Publish checking while pending, then paused;
the validated bare ID is diagnostic evidence only. Existing one-shot/card IDs,
last-delivery information and history remain unchanged.

## Local event-session candidate, 2026-10-17 (D-231)

The user authorizes local implementation and offline tests only. No device
access, live configuration, build or publication is included. The installed
background mode remains off and existing cards unchanged. This candidate
replaces production wiring to repeated short-lived observer jobs, not the
legacy one-shot delivery behavior or public b8 image.

Use at most one bounded read-only Art websocket after a fresh explicit
successful delivery and an exact reviewed device-event policy. No policies
are approved yet: absent policy reports validation_required without a TV
worker, including after an explicit send. No boot, idle, refresh, HA on-state,
timer or retry can create a session. No observer pairing/tokenless fallback.

Within an approved session, obtain one initial bounded identity/mode/ID/targeted
thumbnail proof, then only receive validated notifications on the same socket.
No periodic GET, thumbnail, application keepalive ping or reconnection. Protocol
responses such as pong/close are not zero traffic and need later sleep tests.
Mode-off, malformed/unknown events, loss, limits and identity/image uncertainty
clear current attribution and end the session. Art Mode must be confirmed, not
inferred from reachability or generic HA on. Keep all send/history protections.

The initial conservative candidate trusts only the byte-verified baseline in
this session. Changed/invalidated IDs pause, including a later return to a known
old ID; never resolve an event by content ID alone. Duplicate/same-ID/mode-on
events and HA publications do not refresh image proof. Clear current information
after 90 seconds from actual baseline receipt, even if the socket is still open.
Continuous event-stream attribution beyond this conservative limit requires a
separate reviewed event-coverage/freshness amendment and hardware evidence.
No existing card is allowed to make an old title current through a heartbeat.

## D-230 experimental background exception, 2026-10-16

The user accepted experimental default-off observation with a wake-risk warning
and deferred the natural-sleep test. This supersedes the absolute activation
gate below, not the requirement to avoid power/WOL/setter commands. No-wake is
unverified. Start/boot/restart stays passive. A successful explicit send arms
bounded reads and permits initial device enrollment; subsequent reads enforce
a persistent identity pin. Inactive Art Mode or any read failure stops polling
until another successful explicit send. Tokenless authorization is session-only
and comes only from that successful send, never a failed/missing-token retry.
Publication remains separately gated. Existing one-shot defaults/cards remain.

## Optional current TV background mode amendment 2026-10-16

Local implementation is user-authorized (D-225/D-226); private hardware testing
was subsequently approved, but publication was not. `background_mode` is optional and false when absent or
null. Preserve old configurations, script references, preview and last-delivery
caption. Enabling background mode needs a one-time replacement of the send
script body, keeping its entity ID. Never edit user scripts/cards automatically.

In that mode, app start/boot/restart only starts the service. Fixed validated
stdin commands separately request one bounded delivery or a read-only refresh.
Consume fresh request IDs durably before delivery, reject replays and expired
requests, and bound the request journal. Keep the existing loading timer and
all upload/history/quarantine/cleanup protections. Serialize all TV work.

Keep current TV information separate from last sent. Publish only a fixed,
owned Core state without requiring a new helper or integration. It is not an
entity-registry integration. Unknown/stale/offline observations cannot retain a
current title. A known association must match device, content ID and thumbnail
identity. Establish new associations only after isolated comparison with the
exact processed preview and a matching confirmed-upload ID; never infer from
last-caption text or bundle user-specific mappings.

Automatic TV connections are blocked until a validated no-wake policy is bound
to an exact device. The local candidate ships no approved policy. In validated
operation, failure/non-Art-Mode disarms reads without reconnecting; restart
does not resume TV reads on its own. Retain this conservative limit until a
separately approved safe-resume design is validated. No power, WOL, pairing,
upload or selection operation may be reached from the observation path.
An explicitly reviewed identity/channel policy may distinguish a token-bearing
Art channel from a validated tokenless one (D-228). Missing/rejected credentials
must never cause an automatic tokenless fallback. The local candidate enables
neither a production no-wake policy nor a tokenless grant.

New configuration texts and optional setup/script/card guides cover EN/DE/FR/ES/IT.
No version bump, image build, installed-app update or release is authorized here.

## Next-update artist and language amendment (2026-10-10, D-221/D-222)

Local implementation authorized: Commons-only optional `artist` and dedicated
`artist_helper`, default unrestricted, combined with existing colour/shape.
Validate offered complete attribution labels/keys only. Preserve originals,
source pins, history/upload/quarantine and all budgets. Shape fallback never
relaxes artist or colour; no match retains TV/preview/caption and ends cleanly.
Other sources visibly report an artist wish as unsupported. Standard cards and
old options remain valid; native favourite-artist Dropdown is optional alongside
colour, without HACS, SSH or configuration.yaml. No automatic helper creation.

Configuration names/help: English, German, French, Spanish and Italian.
Technical values/IDs stay compatible. Italian is additionally an official
documentation language; finish IT setup/colour and five-language artist guides
and language links before release. English remains default and technical
background remains English. Native image/publication/live gates stay separate.
History reset is only a discussed proposal (D-223), not implementation scope.

## Draft Commons colour update (2026-10-09, D-212/D-213)

Local next-update scope: 1000 usable Commons works in total, preserving the
baseline 400 and requiring 600 additional distinct eligible full artworks.
Discovery records are not accepted works. Width >=3000, JPEG, <=2.5% relative
16:9 deviation, conservative rights, visual and artwork-duplicate checks remain.

Commons alone supports one colour wish. Default `any` means all colours. Twelve
project-defined colour families are measured offline from the unpadded preview,
currently with a provisional meaningful-area threshold of 5%. A matching colour
need not dominate the artwork. Collect up to three distinct meaningful families
with shares and representatives, plus the complete distribution and palette,
bound to exact source/thumbnail hashes and method version for later combinations.
The first UI has no multiple-colour choice or extra mandatory dashboard helper.

Prefilter the pinned catalogue before network requests, without more Green
downloads or decoding. Missing/stale colour evidence is not a match. History,
upload ledger, quarantine and all request/time/cleanup bounds stay in force.
16:9 fallback may relax shape, never the colour wish. An empty/uncertain result
ends cleanly without replacing the TV image, preview or caption. Unsupported
museum/local colour wishes remain visibly reported. Published b5 is unchanged;
new native images, publication and live testing require separate approvals.

## Commons catalogue expansion (2026-10-06, D-211; next release)

Prepare 400 distinct near-widescreen works in total: all 166 released b4 pins
unchanged, plus 234 visually reviewed additions. This supersedes only the older
50/166 catalogue sizes, not rights guards, source identities, the ten-request
discovery cap, strict 1% preference, no-crop fallback, history or cleanup.
Every selected source is JPEG, at least 3000 pixels wide and within 2.5% relative
16:9 deviation. Retain previous research and deferrals separately; no artwork
bytes are bundled. Metadata acceptance is not decoding, worldwide legal
clearance or TV evidence. Publication still needs explicit approval and exact
new native images. Samsung discovery remains outside implementation scope.

## Source-default UX amendment (2026-10-06, D-210; next release)

Wikimedia Commons is the default for new installations and absent/null source
options, and is first in the configuration's source choices. Explicit saved
sources remain unchanged on updates. No additional option, discovery feature,
network permission or change to fitting/shape/history is authorized by this
amendment. The published b4 default remains Chicago until a new release.

## Post-beta Commons extension (2026-10-05, D-206)

Locally authorized fourth source: `wikimedia_commons`, with 50 individually
curated landscape reproductions, predominantly classical modernism. No API key,
registration or artwork-request feature. Bundle metadata only; recheck curated
identity/upload hash, current rights and bounded renditions via the documented
MediaWiki API. No worldwide copyright-clearance claim.

Commons supports source and existing shape/fit options, not department, style,
period or colour. Unsupported filters are reported. Existing history/upload
ledger, deadlines, no-crop default, preview/caption and cleanup remain in force.
A fully sent catalogue ends as no-match rather than recycling works. Landscape
does not guarantee 16:9 or native 4K detail. This is unreleased local work; new
native images, Green/TV changes and publication need separate approval.

## Product vision

Frame Gallery should let a non-technical Home Assistant OS user install an app, choose artwork preferences, and send a fresh artwork to a compatible Samsung Frame television without SSH, shell access, Docker knowledge, or changes to Home Assistant's `configuration.yaml`.

The initial product is a one-shot app: each start selects and uploads at most one artwork, records its history, publishes a dashboard preview, cleans temporary data, and exits.

## Target environment

- Home Assistant OS with Supervisor/apps.
- Home Assistant Green (`aarch64`) is the primary hardware target.
- `amd64` is the secondary target.
- Compatible Samsung Frame television reachable on the same local network.
- Initial live validation television: `192.168.178.30`, but this value must never be shipped as a default or hard-coded into application logic.
- The television is configured by its IPv4 address literal on the local network. Only RFC 1918 private addresses are accepted (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`). The app rejects:
  - link-local (`169.254.0.0/16`), loopback, unspecified, multicast, and broadcast addresses;
  - the container's own networks, including the Supervisor's internal network.

## Installation experience

- The public release must be installable from a custom Home Assistant app repository.
- Documentation must include a one-click `my.home-assistant.io` repository link.
- The released app must use pre-built multi-architecture container images.
- Installation and use must require no SSH session and no `configuration.yaml` edit.
- The configuration screen must explain all options in plain language.

## Run lifecycle

1. Read and validate app options.
2. Resolve any optional filter values supplied by Home Assistant helper entities.
3. Select exactly one enabled artwork source.
4. Find one eligible artwork within strict request, attempt, and total-time limits.
5. Reject artworks already present in the persistent sent history, the TV-upload exclusion ledger, or an unexpired quarantine entry.
6. Download only the selected artwork at the resolution needed for processing.
7. Prepare a television-ready image according to the configured fit policy.
8. Upload and select the image on the television. As soon as the television confirms the upload, record the artwork in the TV-upload exclusion ledger, even if selection is then refused, times out, or becomes uncertain.
9. Persist sent history only after the television confirms selection.
10. Atomically publish the processed image as the dashboard preview.
11. Remove temporary files in both success and failure paths.
12. Exit successfully after one upload, or exit cleanly without changing the television when no eligible image can be found.

The app must never remain indefinitely in a loading or searching state.

## Artwork sources

The architecture must support independent provider adapters. Initial providers for the first public beta:

### Art Institute of Chicago

- Uses only the museum's documented public API.
- Selects only public-domain (CC0) works that have an image.
- Random artwork discovery.
- Optional period filtering, using the documented creation-year metadata.
- Department (collection), style, and colour filtering are **not supported in the first beta**. The documentation names these fields but not their values or members, and undocumented values are not used (D-146; Q-25, resolved with option (a)). No Art Institute department, style, or colour values are offered. A Cleveland department configured while this source is selected is not applied and is reported as unsupported.
- Uses the documented image service at the largest size the provider documents for public-domain works.
- Respects the provider's published request limits and courtesy-header guidance.
- Provider failures, format changes, empty result sets, and rate limits must have bounded handling and useful logs.

### Cleveland Museum of Art

- Uses only the museum's documented Open Access API.
- Selects only records and images explicitly marked CC0 / open access.
- Uses the documented print JPEG rendition, with its published dimensions, never the very large original TIFF.
- Random artwork discovery.
- Optional department (collection) and period filtering, using documented metadata.
- Style filtering is not supported (the documentation has no style field). Colour filtering is not part of the first beta. It may be added only if it can be done locally within the same strict download and time budgets (Q-24).
- Provider failures, format changes, empty result sets, and rate limits must have bounded handling and useful logs.

### Home Assistant media

- Select supported image files from an app-documented media directory.
- Support JPEG and PNG at minimum.
- Ignore unsupported and corrupt files with a useful warning.
- Persistent duplicate prevention.
- Never treat the generated dashboard preview as a new source image.

The provider interface must allow future museum or open-collection APIs without changing the selection and rendering core.

### Researched and excluded sources

The original specification named these sources. The Phase 1 research (see `ARCHITECTURE.md` §9.4) found that none of them offers a documented API compatible with its access terms. They are therefore **not** part of the first beta, and undocumented or `robots.txt`-incompatible access must not be implemented.

- **Google Arts & Culture.** There is no documented public API. `robots.txt` disallows `/api/*`. Google's Terms prohibit automated access that violates `robots.txt`, and partner institutions hold the image rights. The source may be reconsidered only if a stable, documented API becomes available.
- **Bing daily imagery.** There is no documented API. The image path is disallowed in `robots.txt` for general crawlers, and the Microsoft Services Agreement restricts use of the photos. Not planned.
- **Museum of Modern Art and Musée d'Orsay.** No open-access API or open image licence was found. They are not offered as filter values.

## Filter inputs

Static app options must always work without Home Assistant helpers.

Supported filters, kept clearly distinct:

- **source / museum**, which selects the provider: local media, Art Institute of Chicago, or Cleveland Museum of Art;
- **department / collection** within the selected museum;
- **style or period**;
- **colour**;
- landscape-only, **enabled by default**;
- strict near-16:9 TV-format preference, **enabled by default**;
- fit policy, `contain` (no crop) by default.

Not every source supports every filter. The documentation must publish a filter capability matrix. A filter that the selected source does not support must be visibly identified as unsupported, in the option descriptions, the log, and the run record. It must never silently claim to work.

The department, style/period, and colour filter requirements apply **only to the filters the selected source supports**. For the first beta, the capability matrix is (D-146, D-152):

| Filter | Home Assistant media | Art Institute of Chicago | Cleveland Museum of Art |
| --- | --- | --- | --- |
| Department / collection | unsupported | unsupported | supported |
| Style | unsupported | unsupported | unsupported |
| Period | unsupported | supported | supported |
| Colour | unsupported | unsupported | unsupported |

A valid filter value that the selected source does not support is not applied, and is reported as unsupported (acceptance item B8). The first beta ships without a colour filter (Q-25, resolved with option (a)):

- The colour option offers no value besides "any" (and its no-filter synonyms), so any other colour value is rejected as invalid (B5).
- Its option description must say that no source supports colour yet.
- The style/period option offers periods only; a style value is likewise invalid.
- A helper that sends an invalid value falls back to the static value with a warning.

Optional Home Assistant helper entity IDs may override the static source, department, style/period, or colour values at runtime. Missing, unavailable, or invalid helper entities must fall back to the static option and must not fail the run.

## Selection limits and fallback

- Every remote request must have a finite timeout.
- Strict TV-format inspection must have a finite probe budget.
- A complete selection run must have a finite total deadline.
- Default hard total runtime deadline: **120 seconds**, divided as follows:
  - configuration plus helper resolution: at most 10 seconds;
  - discovery, download, verification, and image preparation together: at most 60 seconds;
  - television connection, pairing, upload, and selection: at most 40 seconds;
  - history, preview publication, run record, and cleanup: a reserved 10 seconds.
- Every individual timeout is clamped to the remaining total deadline.
- A run that finds no matching candidate must finish cleanly within 70 seconds by default.
- An artwork is a strict near-16:9 match when its aspect ratio `r` (width ÷ height, after EXIF orientation) satisfies `abs(ln(r / (16/9))) <= ln(1.01)`, that is, within ±1 % of 16:9 (about 1.760–1.796). This threshold may be revisited after the supervised Home Assistant Green visual tests.
- The strict-format probe budget is **30 remote dimension requests**. Local header inspection has its own separate, bounded allowance.
- An advanced total-deadline option may be offered later, validated within a safe range. The standard dashboard instructions use the 120-second default.
- When no strict near-16:9 match exists and landscape-only plus no-crop preservation are enabled, the app may fall back to an eligible landscape artwork.
- The fallback artwork must be fitted completely onto the 16:9 target canvas without cropping, normally using black side or top/bottom margins.
- If no eligible strict or fallback artwork exists, the television must remain unchanged and the app must stop cleanly.

## Image preparation

- Default target canvas: 3840 × 2160 pixels.
- Default behavior: preserve the complete artwork and never crop it.
- `contain`: scale proportionally and place on a configurable solid-color canvas; black is the default.
- `cover`: optional explicit user choice that may crop edges.
- Stretching that distorts aspect ratio is not allowed.
- Correct EXIF orientation before fitting.
- Convert unsupported color modes safely for television-compatible JPEG output.
- The exact processed file sent to the television must also become the dashboard preview.

## Duplicate prevention and storage

- Store sent-art identifiers persistently in the app data directory so history survives restarts and upgrades.
- Use provider-qualified identifiers to avoid collisions across sources.
- Do not record a work as sent until upload and selection succeed.
- Keep a separate, bounded **TV-upload exclusion ledger**:
  - Once the television confirms an upload, the provider-qualified identifier enters the ledger, even if selection is then refused, times out, or becomes uncertain.
  - If an upload was started but not confirmed, the identifier is held in a bounded, temporary uncertainty quarantine for **30 days**.
  - Candidates in the confirmed sent history, the upload ledger, or an unexpired quarantine entry are never selected again.
  - The confirmed sent history, the current artwork, and the dashboard preview change only after the television confirms selection.
  - Both records use the same atomic, bounded state design.
- The history format must be bounded or compactable and recover gracefully from a partially written or corrupt file.
- Temporary high-resolution downloads must not accumulate.
- The app must not build an unbounded local copy of the provider's entire artwork catalog.
- Cached metadata must have explicit size and age limits.

## Dashboard experience

**Optional post-beta feature authorized 2026-10-04 (D-202):** preserve the
standard preview card and provide a separate optional information card showing
the published artwork's title, artist and museum. Use existing provider metadata
only; omit missing artist/title rather than invent them. The UI-created Text
helper and native card need no HACS, SSH or configuration.yaml change. Metadata
changes only after TV-confirmed selection and successful preview publication;
clear old labels before preview replacement, with bounded failure handling.
No-match/TV failure preserve the previous information; a failed final write
shows no caption instead of mismatched old labels. The TV JPEG stays unchanged.

Documentation must provide complete copy-and-paste-ready Home Assistant dashboard YAML that:

- displays the latest preview image;
- starts the app when tapped;
- shows a temporary loading state that always returns to idle;
- avoids stale browser caching after a successful run;
- works without editing `configuration.yaml`, without mapping the configuration folder, without SSH, and without manually modifying files.

The primary preview design is a Local File camera reading `/media/frame_gallery/preview`. Home Assistant OS creates `/media` without user configuration, and the default media directories are part of Home Assistant's default external-directory allowlist. A normal Home Assistant Green installation therefore needs no `configuration.yaml` edit.

**Preview freshness is release-blocking.** Validation on the live Home Assistant Green must select and document one proven refresh mechanism, and must show each newly delivered image without a stale browser cache across repeated tests before the dashboard is declared complete. The refresh mechanism must be fully UI- or API-based. Candidates:

- Local File's file-change detection;
- `homeassistant.update_entity`;
- alternating two preview file names with `local_file.update_file_path`;
- another fully UI- or API-based method proven in validation.

The chosen mechanism must keep the preview correct on every documented start path.

Home Assistant's Collection Image integration may be documented as an optional alternative for Home Assistant 2026.9 or later. It must not raise the app's general minimum Home Assistant version.

Filter selection from a dashboard is desirable. The architecture proposal should compare these approaches without implementing them in Phase 1:

- documented Home Assistant helpers;
- an app Ingress interface;
- a future companion integration that exposes native entities.

## Logging and errors

- Log the selected source and effective filters without leaking tokens or private data.
- Distinguish no-results, provider/network failure, image-processing failure, television connection failure, and television rejection.
- Use concise user-actionable messages.
- Normal no-match completion must not produce a misleading crash trace.
- No log should contain Home Assistant credentials, Supervisor tokens, pairing secrets, or complete sensitive API payloads.

## Privacy and network behavior

- All television communication stays on the local network.
- Remote artwork requests go only to the selected provider and required image host.
- Do not add analytics or telemetry.
- Do not upload the user's images, configuration, history, or television information to a third-party service.

## Non-goals for the first release

- Deleting or managing old images already stored on the television.
- Managing a Samsung account or paid Samsung Art Store subscription.
- Maintaining a full local mirror of an artwork provider.
- Editing Home Assistant dashboards automatically.
- Editing Home Assistant `configuration.yaml`.
- Supporting Home Assistant Container installations without Supervisor/apps.
- Google Arts & Culture and Bing sources (see *Researched and excluded sources*).
- Claiming affiliation with Samsung, Google, Microsoft, any museum, or Home Assistant.

## Amendment log

- **2026-10-04: user-approved optional artwork-information feature (D-202).**
  Adds title/artist/museum below the unchanged standard card. Local implementation
  only; no live HA edit or publication approval inferred. Fields are bounded,
  escaped when displayed, and may be abbreviated to fit a 255-character helper.

- **2026-09-26: Phase 1 Codex review of commit `d42adf5`, with user decisions.**
  - Beta providers are now local media, Art Institute of Chicago, and Cleveland Museum of Art. Google Arts & Culture and Bing moved to *Researched and excluded sources*, and the Museum of Modern Art and Musée d'Orsay filter values were removed.
  - The filters were separated into source/museum, department/collection, style/period, and colour, with a published capability matrix. The landscape-only and strict-format defaults moved to *Filter inputs*.
  - The runtime limits were replaced with the 120-second total deadline and its phase split, the 70-second no-match bound, and the 30 remote dimension requests.
  - The TV-upload exclusion ledger and the uncertainty quarantine were added.
  - Dashboard preview freshness was made release-blocking, and the preview platform basis was recorded.
  - Lifecycle step 5 now also excludes the upload ledger and quarantine. Step 10 now ties history to confirmed *selection*, not upload.
  - The order of lifecycle steps 9 and 10 is unchanged and remains subject to decision D-113.
- **2026-09-26: Codex final gate review of commit `9352e77`, with user decisions.**
  - *Target environment:* the TV address must be an RFC 1918 private IPv4 literal. Link-local (`169.254.0.0/16`), loopback, unspecified, multicast, and broadcast addresses and the container and Supervisor networks are rejected (Q-12, D-125).
  - *Run lifecycle:* steps 9 and 10 were swapped, so sent history is persisted before the preview is published (D-113, Q-18 item 4). The product vision sentence was reordered to match.
  - *Selection limits:* the strict near-16:9 match is defined as `abs(ln(r / (16/9))) <= ln(1.01)` (±1 %, about 1.760–1.796). It may be revisited after Phase 8 (Q-03, D-116).
  - *Duplicate prevention:* the uncertainty quarantine period is 30 days (Q-23, D-137).
- **2026-09-27: Phase 3 gate, with user decisions.**
  - Q-25 is resolved with option (a): the first beta ships without a colour filter, and without Art Institute department and style filters. No live Art Institute observation is approved.
  - D-146 to D-152 are accepted.
  - *Artwork sources:* the Art Institute offers only the period filter. Cleveland offers department and period; it has no style filter, and colour stays outside the first beta.
  - *Filter inputs:* the department, style/period, and colour requirements apply only to the filters the selected source supports, and the first-beta capability matrix is stated. A valid filter value that the source does not support stays visibly reported (acceptance item B8). A colour or style value, which the first beta does not offer, is rejected as invalid (B5). Acceptance items B2 and C1 are reworded to match.
