# Product specification

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
