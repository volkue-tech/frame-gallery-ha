# Decision log

## Commons colour research and 1000-work scope (2026-10-09)

### D-213 — draft single-colour Commons prefilter and minimal configuration

Status: **accepted local implementation scope** under the user's current
autonomous update request. The research palette/threshold remains provisional;
native/release/live gates are not granted. Implement against the unchanged
400-work baseline while additional-work curation proceeds separately.

- Offer twelve `color_` vocabulary keys with English/German aliases; keep every
  existing key, helper and explicit source setting. Version the vocabulary to 2.
  Only Commons gains COLOR capability; museum/local colour wishes remain visibly
  ignored, not secretly imposed or fetched through another provider.
- Promote the existing optional colour option into one basic field immediately
  after source, default `any` (all colours). Do not add percentage, multi-colour,
  HEX or extra helper fields. Older absent colour values remain `any`.
  Native list values display readable English names (e.g. `Blue`), not internal
  `color_blue` keys; the vocabulary normalizes labels/aliases to the same key.
- Ship only a small generated immutable ID-to-(upload-pin, search-family) map.
  Full top-three/distribution/palette/provenance evidence stays in research, not
  a thousand-JPEG runtime cache. The classifier does not run on Green.
- Before shuffle or the first metadata request, restrict candidates to the
  requested family and an exact matching upload pin. Missing profiles and stale
  pins never become colour matches. Unfiltered selection keeps previous behaviour.
- Preserve current metadata request caps, rights/hash rechecks, history/ledger/
  quarantine, deadlines, shape-only fallback and cleanup. Empty colour results
  must not send another colour or mutate TV/preview/caption/history.
- Maintain current count claims (400) until 600 additions have actual full-work,
  provenance and duplicate decisions. This draft is not advertised as released.

### D-212 — locally prepared, source-bound colour profiles before UI implementation

Status: **accepted local research/implementation scope** by the user's request;
the pilot algorithm and thresholds remain **provisional**, not release-approved.
Publication, native release builds, Green changes and TV tests require their
separate approvals. No credentials are needed for the public research.

- Preserve all 400 baseline IDs, titles, artists and upload pins. Target 600
  additional distinct eligible artworks without relaxing D-211's requirements.
- Prepare colour metadata on the Mac, not by extra downloads/decoding on Green.
  Start with 48 baseline works: initial modern works plus a deterministic spread
  of the catalogue. Research-only tooling is outside the shipped app package.
- Reuse the existing guarded Commons HTTPS path, five imageinfo records per
  request, existing pacing/TLS/host/address rules and PD/CC0 checks. This research
  pass has its own explicit finite budget; it does not increase runtime budgets.
  Request a 512px JPEG; accept only independently decoded <=1024px axes and a
  stricter 2 MiB research sink, never the original-file URL. Save private source
  evidence/thumbnails below ignored build/, not as distributed artwork assets.
- Decode in a fresh child with no inherited credentials, a 15s parent timeout,
  10s CPU limit and 512 MiB address-space limit on Linux. No Linux-style memory
  enforcement is claimed on the Mac. Refuse other formats and ambiguous colour
  spaces; honour EXIF and ICC/sRGB. Do not crop, trim composition edges or add
  TV padding. Record actual versus API-reported thumbnail dimensions separately:
  the first observed JPEG was 960x528 despite a 512px request.
- Provisional deterministic method: <=256px analysis sample, 128 median-cut
  palette entries without dithering, HSV/lightness family classification across
  twelve named groups. Store all palette counts and group distributions, up to
  three distinct dominant groups, meaningful search groups and representatives.
  The provisional meaningful-area threshold is 5%; neither it nor the names
  are final before visual calibration. Never invent three colours for a
  monochrome work or collapse future combination data to a single label.
- Bind every profile to original Commons upload SHA1, thumbnail SHA256, actual
  dimensions, rights observation, timestamp, method version and Pillow version.
  Unchanged pins remain required when this metadata is later used at runtime.
- Single-colour UI only, default any; future combination UI is not in scope.
  Any later colour-prefilter must preserve exclusions, shape-only fallback
  within the requested colour and clean no-match rather than colour relaxation.

Official Imageinfo and Pillow documentation was rechecked on 2026-10-09.
This is a research prototype, not an amendment claiming the released adapter
already supports colour. Released b5 capabilities remain unchanged; D-213 adds
colour only in the local next-update draft.

Observed local milestone: 48 pilot thumbnails visually inspected, then all 400
baseline profiles prepared using provisional `commons-colours-pilot-v2`.
Dark saturated blue is no longer treated as black; ochre is distinguished from
orange/brown. Separate dominant and chromatic top-three groups preserve neutral
areas and colourful accents. Full distributions retain minor/non-search colours.
All source pins and thumbnail hashes pass the audit; 64,316,428 thumbnail bytes,
maximum actual axis 960px. Metadata-only profiles/audit are under research/;
private JPEGs/contact sheets and preview remain under ignored build/.
Thirteen offline research tests pass; the unchanged full production gate passed
outside the Mac sandbox after its group/setgid tests failed inside the sandbox.
The private preview's 400-card count and eleven violet matches were browser-tested.
This initial profile-only milestone preceded D-213's local colour draft; no new
accepted artwork or public colour capability is claimed.

Discovery candidates remain explicitly unreviewed. A broad query generated many
irrelevant photos, so documented Artwork/insource-oil filters were added without
discarding the original evidence. Additional-source checks use five imageinfo
records plus current revision content per request, private source hashes and
direct rights-basis declarations; commented/nowiki examples do not count.
PD-Art alone is not treated as a US rights basis. Automatic evidence screening
is not curator acceptance or qualified legal clearance. Ambiguous declarations
remain deferred for manual review. The documented multi-page revisions query
omits rvlimit; the initial parameter refusal is retained, not silently ignored.

Next local milestone: single-colour draft production gates pass (5,020 tests,
eleven platform skips, 100% line/branch coverage, strict Mac/Linux mypy).
Static/default and German helper colour choices deliver distinct matching works
through the real wiring with synthetic network/TV. Shape fallback preserves the
colour; an empty match preserves previous TV/preview/caption/history and cleans
scratch. Full baseline metadata is in frame_gallery/research for host/container
test consistency; production still copies only the compact 64,385-byte index,
not full palettes or JPEGs. No native/release/live gate is represented by these tests.

Expansion research milestone: 5,000 metadata candidates, 1,280 automatically
eligible records and the first 1,268 previews actually screened; 861 first-screen
deferrals. The second review of 28 contact sheets plus stricter source/physical
proportion and artwork-identity checks has yielded **144 retained local
additions**. The earlier provisional 127 are superseded: plain dimensions in
museum/GAP receipts and descriptions expose additional possible crops; neither
image/sheet scopes nor out-of-band physical ratios are silently ignored. Separate
Art Photo attribution/share-alike declarations stay deferred. Forty-two choices
remain deferred. The 400 baseline upload pins were rechecked and 347 artwork QIDs
retained. Curator
receipts and complete provisional colour data are metadata-only under
frame_gallery/research. The private preview has 544 works; the runtime
catalogue still has exactly 400. 456 additions and the full release scope remain.

The private evidence parser now recognizes explicitly labelled Dutch `h/b`
museum measurements with repeated/mixed units. All measurement scopes remain
visible; out-of-band originals are deferred. A Rijksmuseum upload credit is
separated from the maker explicitly recorded in its source description. If
that statement is absent, the artist is unidentified, not guessed from a category.

Source-supported PD-Art-two-auto (explicit old deathyear), PD-old-100-1923 and
PD-old-70-expired aliases now count as private evidence, not automatic curator
acceptance or worldwide legal clearance. Bare PD-Art is still insufficient.
Original physical dimensions that contradict the reproduction and rotated
portrait previews remain deferred. Missing physical measures are explicitly
recorded, never invented; complete-image visual review remains required.

Individual thumbnail/network failures are separately retained and not blindly
retried or counted as permanent artwork rejection. New search/thumbnail tooling
saves a refusal receipt before ending that finite pass. Two older observed
failures were transcribed with their evidence limitations, including one missing
API error detail. Raw source revisions, thumbnail hashes, prior inspected sheets
and actual decisions remain resumable below ignored build/, not overwritten by
later preview batches. Research JPEGs are never shipped. Full local production
gates still pass; native/release/live gates are not implied.

## 400-work Commons and first-user UX scope (2026-10-06)

### D-211 — preserve research, target 400 usable works, keep setup minimal

Status: **accepted for implementation and b5 publication** by the user's explicit
request and fresh publication approval on 2026-10-06. A memory-only personal
token session of at most four hours is authorized; no HA/TV mutation is implied.

- Target 400 distinct usable works **in total**, adding 234 to released b4's 166.
  Preserve the prior 200 proposals and deferred entries in their dated research
  snapshot. Keep new searches, public metadata and review decisions separately.
- Retain JPEG, source width >=3000 and relative 16:9 deviation <=2.5%, pinned
  upload identity, conservative PD/CC0 provenance, full-artwork visual review,
  and artwork-level duplicate screening. Do not meet the count through crops,
  frames, details, alternate scans or weaker rights rules. Research selection
  alone is not runtime acceptance or qualified legal clearance.
- Use the existing credited authentic Commons screenshot as the prominent Info
  hero, not a fabricated UI or new raw-artwork asset. It is historical b3 evidence
  and is explicitly labelled as such. Clarify first TV start versus optional
  dashboard setup; preserve complete native-card YAML and existing helper IDs.
- Commons default/order follow D-210. Keep five basic fields, optional advanced
  options, current budgets, shape tolerance, no-crop fallback and history IDs.
- Samsung IP reuse from an existing HA integration is optional feasibility only.
  No discovery implementation, subnet scanning, new permissions or live changes.
- A four-hour memory-only personal-token session was rejected before starting
  due to unclear new-publication authority. Clipboard cleared; no token held or
  authentication attempted. The user subsequently explicitly approved b5
  publication and the bounded session. A new release still requires exact
  sources, native tests and signatures before updating public Store main.

Local implementation observed: 400 entries / 299 artist labels, including all
166 b4 tuples unchanged and 234 additions, plus 26 screened reserves. 152 source
ratios meet the unchanged strict preference. The original 34 deferrals remain
excluded. Production metadata audit accepted 400/400 over eight bounded passes
in 74.45 seconds; it is not a normal run, decoding or TV test. Final local gates
passed 5,006 tests, eleven platform skips, 100% line/branch coverage, Ruff and
strict mypy. AIC-only test fixtures now name their modelled source explicitly;
the actual absent/null-source composition-root test proves Commons delivery.
Publication receipt (2026-10-07 Europe/Berlin): native run 37536546471 passed
all five jobs; both actual image repeats, four artifact hashes, anonymous
sources/pulls, isolated 400-work/Commons-default imports and independent exact-
identity signatures passed. Public prerelease 405188764 / v0.1.0b5 targets
frozen runtime/source 44b7278 (2026-10-06 22:26:34 UTC). Store main handoff
completed at 6a79f8c, authenticated exact-ref readback HTTP 200 at 2026-10-06
22:30:23 UTC, after the final full documentation gate passed.
BETA5_VALIDATION.md records exact digests and limits. The
anonymous API watcher stopped on a rate-limit refusal; personal Firefox
supplied final UI evidence without extending token rights. No new HA/TV test
is authorized or claimed; previous sources, tags and versions are retained.

## Source-default UX amendment (2026-10-06)

### D-210 — Commons first and default for new installations

Status: **accepted for local implementation** by the user's explicit request.
Publication, live installation and network discovery are not authorized here.

- Supersede only the source-default part of Q-08/D-123/D-206: Commons replaces
  Chicago for new installations and absent/null source options. Generate the
  Supervisor default from the runtime constant, keeping both in agreement.
- Put Commons first, followed by Chicago, Cleveland and local media. Retain all
  four existing IDs and explicit saved choices; no automatic migration.
- Preserve source-helper overrides, no-crop/shape defaults, history, catalogue
  and all network permissions. No additional configuration fields/dependencies.
- Published b4/source/images remain immutable. This is a next-release change
  requiring separate publication approval and matching new runtime validation.
- The requested Detect button is feasibility research only. Official app
  configuration documentation lists data fields, not executable action buttons.
  Samsung's official HA integration already supports automatic discovery
  (SSDP/DHCP/Zeroconf matches in Core's manifest). A custom Ingress setup page
  or companion integration would be a separate design/scope decision, not a
  schema toggle. Discovery must not silently choose among multiple televisions
  or equate a Samsung match with verified Frame/Art Mode support.

Public documentation checked on 2026-10-06; no API/device discovery request:
[app configuration](https://developers.home-assistant.io/docs/apps/configuration/),
[Ingress](https://developers.home-assistant.io/docs/apps/presentation/#ingress),
[Samsung Smart TV](https://www.home-assistant.io/integrations/samsungtv/),
[official Core manifest](https://github.com/home-assistant/core/blob/dev/homeassistant/components/samsungtv/manifest.json).

## Near-widescreen Commons catalogue (2026-10-06)

### D-209 — retained research and bounded b4 selection

The user approved the scrolling 200-proposal preview, asked to preserve the
research locally and publish an update independently using only the personal
volkue-tech/frame-gallery-ha account. No new HA/TV mutation is authorized here.

- Preserve all 200 proposals, review/rejection IDs, source-page metadata and
  HTML locally, plus a checksummed snapshot. The release stores a small,
  metadata-only manifest with included/deferred IDs and evidence hashes.
  No full-resolution artwork downloads are bundled or archived as app assets.
- Replace b3's broad-ratio 50-work runtime catalogue with 166 distinct pinned
  JPEG sources from 112 artist labels, width >=3000 and relative 16:9 deviation
  <=2.5%. Preserve `commons:<pageid>` and existing sent/upload history. The old
  catalogue remains in Git and the retained b3 matching-source distribution.
- The app's strict preference stays `abs(ln(r/(16/9))) <= ln(1.01)`; 67 selected
  originals meet it. Contain/no-crop, landscape, safe fallback, request/byte/time
  budgets and all existing options/helpers remain unchanged. No new form field.
- Defer 34 proposals: 11 PNG/TIFF sources outside the JPEG-only adapter, five
  scan/work proportion review cases, and 18 source-rights review cases. These
  remain in private research. Beckmann's 1937 artwork conflicts with its
  PD-old-100-expired tag; a template label is not accepted as legal clearance.
  Additional attribution claims and old-only/regional tags without explicit US
  basis are deferred. This is conservative curation, not a legal opinion.
- Preserve the ten normal five-record-request discovery ceiling explicitly for
  the larger catalogue, within the existing shared allowance of 15 including
  redirects/retries. Omit permanently excluded entries from mixed requests;
  retain quarantine handling. Exhaustion ends cleanly without automatic repeats.
  Each run samples the shuffled catalogue, not an exhaustive 166-item scan.
- Source-only release, exact-commit/hash approvals, both native validators and
  actual publishers, anonymous registry/source checks and independent Cosign
  verification remain mandatory before exposing b4 in public Store main.
  Existing b1/b2/b3 sources/images remain. No new live Green/TV test is claimed.

Official template meanings checked 2026-10-06: [PD-Art-two-auto](https://commons.wikimedia.org/wiki/Template:PD-Art-two-auto),
[PD-old-100-expired](https://commons.wikimedia.org/wiki/Template:PD-old-100-expired),
[PD-old-70](https://commons.wikimedia.org/wiki/Template:PD-old-70).
The 2.5% research criterion is not a blanket copyright determination.

Personal credentials: the user named the exact Mac Passwords item
`Github Frame Gallery Token`. Its account and repository were verified as
volkue-tech / the public personal repository. The token remains process-memory
only with a four-hour maximum, and clipboard data is cleared. Actions-variable
API returned 403 once and was not retried; a narrow repository metadata probe
confirmed the correct personal account/repository. The already authenticated
personal Firefox session provides the existing release-gate UI; no token scope
or account permission is expanded, and no corporate credential is accessed.

Publication evidence: frozen runtime/source `5011966879d5993d548a54df32e0361da86135ca`;
matching public sources SHA256
`6a3ece93091f52f8d89ee37cb59b63625ccd7ebde6d12b025ac7969ee5c60e16`.
Run `37428676044` passed all five jobs, including both native validators and
actual publishers. Independently checked anonymous manifests/pulls, actual
runtime labels/catalogue and exact workflow/SHA/issuer signatures passed.
All four evidence ZIPs matched their public hashes and were retained locally.
Exact image digests and native measurements are in BETA4_VALIDATION.md.
Both one-time variables are disabled and read back as `DISABLED_AFTER_0.1.0b4`.
No new HA/TV test is implied; b3 hardware evidence remains historical.

Public release `404519064` / `v0.1.0b4` was published at 2026-10-06 09:12:20 UTC,
after public main exposed the verified version. Anonymous readback confirmed the
public prerelease and tag at exact runtime/source `5011966`; Store metadata
confirmed b4 and the pre-built image mapping. The publication receipts are
documentation-only follow-ups, not additional runtime/image changes. Prior
versions and source archives remain available; no b4 Green installation occurred.

## Commons beta and configuration UX (2026-10-05)

### D-208 — verified b3 publication and in-place Green evidence

The approved frozen runtime/source is `15644bf0f42b24e89621020fce9f511942237832`.
Both native validations and actual publisher jobs passed. Anonymous pulls,
tag/digest byte comparison, actual version/revision/platform labels and independent
Cosign verification passed. The matching source download and all four evidence
ZIPs matched their public hashes. See [b3 validation](BETA3_VALIDATION.md) for
digests, signatures, source receipt, exact test counts and measurement scope.
No older image/source tag was overwritten; no dependency pin or notice changed.

Only after those gates, public main exposed b3 and the existing Green app was
updated through its UI with previous-version backup retention enabled. No
reinstall, history reset, card/helper recreation, SSH or configuration.yaml
edit. Only source/strict-format options changed; the German UI, existing
script/card, two distinct Commons deliveries, explicit repeat exclusion,
preview/caption/loading completion and bounded cleanup were observed. The user
confirmed the second work physically. Both publisher variables were disabled
and read back. The new screenshot contains only the cards and public artwork.

The old token session expired at its fixed 45-minute boundary and was not
extended or persisted. The user supplied the same personal credential privately
for a fresh, same-scope Store/completion push. Normal API app-info returned 401
and was not retried; authenticated UI was used for the Green test.

User feedback: landscape-only (>1:1) can still leave large side margins, as
Macke's approximately 1.21:1 work demonstrated. A minimum broader ratio is
a possible future product decision; no frozen b3 code/configuration definition
was changed after its exact-source/native validation.

### D-207 — autonomous b3 preparation and preserved configuration

The user explicitly asked to carry out the next beta build/Green test
independently and to keep app configuration comprehensible. Initial automatic
review held the GitHub publication as requiring explicit approval. The user
then separately approved publishing beta 0.1.0b3 to volkue-tech/frame-gallery-ha:
candidate push, corresponding-source upload, ARM/Intel pipeline and store
metadata after successful checks. An in-place Green update plus Commons run
is also authorized, not unrelated HA/dashboard edits or credentials.
No configuration.yaml change, no app reinstall and no history reset.

- Numbered candidate 0.1.0b3; never overwrite b2. Public main stays on its working
  image version until exact-source, both native images and signatures are verified.
  The manual publisher permits only main and codex/commons-curated, replacing
  the completed b2 candidate ref. Existing exact-SHA/hash/unused-tag gates stay.
- Basic form: TV/source/landscape/strict shape/fit. Department, period, colour and
  margin colour become optional without Supervisor defaults; parser defaults
  remain exactly the same. Retain their schema keys and existing saved values.
  No unsupported schema grouping or undocumented per-source dynamic hiding.
- Unused colour is compatibility-only; not a promised filter. Native optional-
  field reveal is documented. Existing optional settings may remain visible.
- English/German texts map raw source keys to human-readable sources, explain
  contain/cover and recommend disabling strict shape for the Commons selection.
  No new options, dependencies, permissions, API key or dashboard extension.
- Generator and regressions verify all translations, schema/parser alignment,
  unchanged effective defaults and old saved-option compatibility. Live UI and
  native validation are distinct gates; do not claim them from local tests.

Basis: official [app configuration](https://developers.home-assistant.io/docs/apps/configuration/)
rechecked 2026-10-05 (optional ? schemas and translations). Repository GitHub
auth is presently unavailable; request the existing personal token privately
instead of trying another identity or saving credentials.

## Curated Commons extension (2026-10-05)

### D-206 — bounded, keyless Wikimedia Commons adapter

Status: local implementation authorized by the user's “leg los” after the
50-landscape research. No HA/TV mutation or publication approval this turn.

- Source `wikimedia_commons`, history prefix `commons`; Chicago stays default.
  No registration/key, new dependency, image bundling or artwork-request feature.
- User approved `volkue+commonsapi@gmail.com` for Commons API contact headers on
  2026-10-05. Commons' host policy overrides the User-Agent for metadata/image
  requests only, preserving the runtime version; museum contacts and Git identity
  stay unchanged. The address is a project contact, not a secret or API key.
- Fifty metadata entries across eight artists: curated page ID/file title,
  original-upload SHA-1, plain title/artist. Hash identifies the selected
  reproduction, not legal/security clearance. Changed uploads/titles are skipped.
- Delaunay files 22950618/104640628 stay in historical research only: their US
  basis was open. Replacements are Klee's Before the Town (60907526) and Deep
  Pathos (60907632), visually checked with explicit PD-old-auto-expired pages.
- Documented MediaWiki query/imageinfo, formatversion 2, pageids, five records
  per request, iilimit 1, English filtered rights fields, iiurlwidth 3840, maxlag 5.
  Finite shuffle: at most ten normal requests; allowance 15 includes gateway
  redirects/retries. Shared pacing, time and byte caps remain.
- Exact metadata host commons.wikimedia.org; image hosts upload.wikimedia.org
  and thumb.wikimedia.org under /wikipedia/commons/. Returned URLs/sizes only.
  JPEG at most 3840 per axis; never oversized-original fallback. Workers still
  verify actual bytes/dimensions. No arbitrary categories or HTML parsing.
- Current Public domain requires Copyrighted false. CC0 additionally requires
  the canonical creativecommons.org/publicdomain/zero/1.0/ dedication URL
  (http/https and deed.en metadata forms, never fetched). Commons may report
  Copyrighted True for CC0. Both require AttributionRequired false and no declared
  Restrictions. Missing/revoked/unsupported rights fail closed. This is Commons'
  statement, not legal advice or universal copyright clearance.
- No optional department/style/period/colour filter. Shared geometry/contain and
  optional artist/title helper work, source label Wikimedia Commons (not a claim
  it owns the museum collection). None is strict ±1% 16:9; contain can leave margins.
- Existing history/upload ledger decides no-repeat. Entire batches permanently
  excluded skip requests and increment discovery notes; mixed batches yield valid
  records to selection. Quarantine is never a permanent exclusion. After 50 sent
  works: no-match, no recycle. No persistent metadata cache or downloaded library.
- Synthetic fixtures/shared contract and production-wiring simulations cover
  requests, rights, failures, repeated delivery, fallback, captions and cleanup.
  Live metadata evidence is distinct from decode/container/Green/TV validation.
- Work isolated on codex/commons-curated. Config changes are local only; published
  b2 remains unchanged. New version, exact-source package, native ARM/Intel and
  approved live validation are required before publication; never retag b2.

Official references rechecked on 2026-10-05:
[Imageinfo](https://www.mediawiki.org/wiki/API:Imageinfo),
[API usage](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_API_Usage_Guidelines),
[Commons reuse](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia),
[CC0](https://creativecommons.org/publicdomain/zero/1.0/),
[Before the Town](https://commons.wikimedia.org/w/index.php?curid=60907526),
[Deep Pathos](https://commons.wikimedia.org/w/index.php?curid=60907632).

## Optional dashboard attribution (2026-10-04)

### D-205 — observed b2 Green rendering, negative outcomes and Core restoration

**Status:** completed within the user's approved software-test scope (2026-10-04);
physical TV confirmation deferred by the user. Personal public prerelease
`v0.1.0b2` subsequently published at 19:17:19 UTC targeting `4c93d86`;
anonymous API/main/file comparisons independently verified it.

The same public-store installation was updated in place to 0.1.0b2. The UI's
keep-previous-version backup option was enabled; no backup restore is inferred.
Saved explicit timer and artwork-information targets, and one separate native
test stack, leave the original camera/timer/script/card and private history intact.
All temporary source/filter/address changes were restored to the user's original
settings. No configuration.yaml, account privilege, SSH or extra extension change.

Two new deliveries completed in 19.4 and 16.6 s with `selected` markers. Both
native preview and escaped title/artist/museum changed correctly. A browser
reload retained the first caption. A restrictive museum/period combination
ended `no_match` in 1.2 s; safe unspecified-address refusal ended `config_invalid`
before any TV communication. Both retained the second preview/caption and
acknowledged loading completion. Observed storage summaries had zero temporary
files/run directories and one latest preview. TV transport faults and metadata
service faults were not induced live; synthetic coverage is the evidence there.

The user explicitly approved one Core restart. The UI reported no running
automations/scripts in its confirmation dialog. After restart, disconnect and
a fresh browser reload, the previous Text-helper caption and preview reappeared
without another artwork run; HA subsequently reported fully started. This
verifies restoration for this setup, not every installation or integration.

A card-only native Firefox capture after restoration is included in the optional
guide, with no personal dashboard context or tokens. One official AIC record
lookup confirmed the depicted artwork 100829's `is_public_domain: true` and
matching metadata; documentation references the official policy/guidance rather
than relicensing museum/UI material. Website 403s were not misreported as reads.
`BETA2_VALIDATION.md` contains exact runs, image/source identities and limits.
The user can later supply physical confirmation of the magnolia artwork; do
not silently promote protocol selection to a physical-TV observation.

### D-204 — independently verified b2 images and bounded live-test authorization

**Status:** completed image/source checks (2026-10-04); D-205 records later software validation. Physical confirmation remains deferred.

Runtime/source commit: `f3d916c1519f86482a740c7dda54767d8ad99092`.
Personal publisher run `37223299682` completed all five jobs successfully.
Both native validations and actual upload-image suites passed; each actual-image
suite reports 4,914 passed, five root-only skips, then five root checks passed.
Both architectures passed all 26 worst-case image measurements under the real
1 GiB RLIMIT_AS; no emulated measurement replaces the native Intel result.

Independently anonymously downloaded image identities:

- ARM: `ghcr.io/volkue-tech/frame-gallery-ha-aarch64@sha256:9e58bd22eaa4171025ff6b650b1de4a568ecb20a9254766786fade2597650e42`.
- Intel: `ghcr.io/volkue-tech/frame-gallery-ha-amd64@sha256:765a87631cc044a1fc6e16c91a3bbc67cb92643409fccb6c8640365aaf57441a`.

Each tag/digest manifest matches byte-for-byte; pulled image architecture,
version and revision labels match. Independent Cosign 3.1.3 checks passed using
the exact candidate-branch certificate identity from D-203, GitHub issuer and
the full runtime SHA. No main-branch certificate identity is falsely claimed.
Downloaded publisher ZIP SHA256s match GitHub: ARM
`9daed3b85dddb99d04179ba8a4311dc130a776acbd307cf7401b4da03ef268e9`, Intel
`c7227304bea5d716a37be6a61221ea7ba95f6845afa8facc8cb86f6f984b73c0`.
Native validation ZIP SHA256s: ARM
`909fd5d38db7167318a69077fdebba6e50270cdff8fac6a98684f10aead050af`, Intel
`9be892ffbad920e5d0a99c24c1bc48ee9c56034434982f14ffe83b9e00b69592`.

The public source-only prerelease `sources-v0.1.0b2` contains 172 upstream
archives and the exact own snapshot, 521,646,080 bytes, SHA256
`b5ac1de25f01dac9def0e855d35bb9e88f3ba24ddb0410ef9173cbd79b2846a5`.
Its anonymous download passed hashing and exact-commit/member release preflight.
Both one-time GitHub approval values are saved/read back as
`DISABLED_AFTER_0.1.0b2`; no credential or permission was expanded.

The user subsequently explicitly approved updating the same installed public
app, one dedicated Text helper, a separate test card and a TV delivery, while
preserving the original card/history and leaving configuration.yaml untouched.
Created helper: `input_text.frame_gallery_artwork`; min 0/max 255/Text mode
persisted and independently confirmed by reopening settings. Native AX setValue
changed the visible maximum without persisting it on first creation; real
keyboard input, saving and reopening confirmed the corrected 255 value.
The guide now explains More options and the default 100 maximum.

Read-only diagnostics confirmed the original camera/timer/script IDs. The
stored normal HA API account is non-admin; an admin-only template request
returned 401 and was not retried. One scoped current-user metadata probe
confirmed the role. Its privileges were not expanded. The existing authorized
admin Firefox session is the separate UI route for these approved live changes.
No app update/options edit/card save/TV send/restart is claimed at this checkpoint.
HA restart restoration still needs separate user approval. Store-main push and
the app-release announcement are pending the personal credential handoff and
actual live validation. Historical b1 receipts remain valid for b1 only.

Subsequent checkpoint: the personal main push completed at `e908602`, verified
by anonymous ls-remote. The user then said the TV is being used and postponed
the live test. No Green app update/start, options/card modification or TV send
was performed during that pause. The user then explicitly reauthorized software
live testing, with physical TV display confirmation deferred, and separately
approved one HA Core restart. The public app release and guide graduation remain
pending actual results; protocol success is not physical display confirmation.

### D-203 — approved b2 publication without exposing a missing store image

**Status:** the user explicitly authorized publication on 2026-10-04. No live
Home Assistant update or helper/card edit is authorized by this request.

Prepare numbered beta `0.1.0b2` with unchanged dependencies, base, isolation and
notices. Publish matching corresponding sources before any binary. The manual
publisher additionally permits only the personal repository's exact
`refs/heads/codex/artwork-info` candidate branch, still requiring the approved
commit/source SHA, both native checks, non-overwrite and keyless signatures.
Its signature certificate names the actual workflow ref, not a false main ref.
Only after both versioned images pass may this candidate fast-forward `main`,
so the app store never deliberately advertises a nonexistent new image. The
old version/source remain retained. Disable the one-time approval values afterward.
New optional-helper rendering/restoration remains explicitly unverified until
the user authorizes a supervised Green update. No general arbitrary-branch or
automatic publisher is introduced. Native/public evidence is recorded as it occurs.

### D-202 — native, optional artwork-information card without changing TV pixels

**Status:** user authorized local implementation after approving the visual.
The subsequent UX decision keeps the standard image card unchanged and the
information card separate/optional. No community dashboard extension is used.
Publication, new signed images and live HA configuration require separate approval.

- `artwork_info_helper` is optional/unset by default and accepts only one explicit
  `input_text.<lowercase identifier>` with at most 64 object-ID characters. It
  must not also be a configured filter helper. Users create a dedicated Text
  helper through the UI: minimum 0, maximum 255, no Initial value, Text mode.
- The parent retains its existing Supervisor token only if needed, exactly as
  for filter helpers/timer completion. The guarded Core client can GET this
  existing helper and POST only `input_text.set_value` for that explicit ID.
  This narrowly amends the HA-port write prohibition; no entity creation,
  configuration write, new role, port, mapping, dependency or daemon is added.
- After TV-confirmed selection/history recording, PUBLISH checks/clears this
  helper before replacing the preview. If the clear fails, it retains the old
  preview and reports a preview warning; confirmed TV delivery/history remain
  recorded. If preview publication fails after the clear, information stays
  empty. Only successful preview publication permits the final metadata write.
  A failed final write normally leaves the new preview with no caption, not old
  labels. A lost acknowledgement can mean Core already applied the correct new
  caption; there is no retry or attempted restoration of the previous caption.
  `no_match`, TV failure and a stop before PUBLISH leave old information untouched.
- One shared two-second child deadline bounds the GET and at most two POSTs;
  preview processing consumes time from it too. Existing PUBLISH/FINISH/total
  limits are unchanged. No retry/redirect; responses close; a 401/403 prevents
  later metadata or timer authentication attempts. No metadata/token bodies
  enter logs. The target is inside the container's own Supervisor networks.
- The helper holds a single compact JSON object (`title`, `artist`, `museum`),
  maximum 255 characters including JSON escaping. Title/artist are normalized
  plain text, each at most 100 characters, shortened further with an ellipsis
  when needed. Missing fields stay empty; museum labels come only from known
  provider keys. Local images use the filename stem, no invented artist.
  No additional provider request, public sidecar or temporary file is created.
- The native Markdown information card HTML-escapes each string and omits absent
  fields. It is hidden during loading and when the helper is empty/unavailable.
  The complete optional card leaves the native preview/refresh/action unchanged.
  Core/helper and camera refresh are asynchronous: this pairs metadata with
  the published file, not a claim of simultaneous browser-frame updates.
- Persistence uses HA's restored Text-helper state, not a transient REST-created
  sensor. The Initial-value setting must stay unset. Removing/editing this
  dedicated helper affects the optional caption; reset/reinstall/history and
  standard-card behavior are unchanged when the option is unset.
- The released `0.1.0b1` image does not contain this feature. Local source changes
  must not be published under that existing image tag. Release preparation must
  choose a new version, build/validate both architectures, update corresponding
  source evidence, sign/publish images and verify a Green upgrade before claiming
  availability. Native helper/card/restoration behavior still needs that live test.

## Store brand refresh (2026-10-04)

### D-201 — approved independent mark as repository presentation assets

**Status:** user explicitly approved adopting and publishing the selected logo.

The Living Gallery Window mark was designed independently with built-in Imagegen
and approved after previewing at 32, 48 and 64 CSS pixels on light/dark surfaces.
No predecessor or competitor image was used as a generation input. The transparent
refinement removes only the exterior white corners. Commit the approved RGBA
master and both prompts under `frame_gallery/assets/brand/`; export it unchanged
to both Supervisor presentation PNGs through `scripts/app_images.py`.

The master is 1254 × 1254 (1,044,252 bytes). Keep its exact approved pixels and
alpha: Home Assistant requires a square PNG icon; 128 × 128 is a recommendation,
not a required size, and the logo may have another size/aspect ratio
([official presentation guidance](https://developers.home-assistant.io/docs/apps/presentation/)).
Both exported PNGs are byte-identical; Git deduplicates their identical blob.
The test-context allowlist includes the master so host/container presentation
tests see the same source. No art-generation dependency or brand asset is copied
into the runtime Docker stage, and the released container is not rebuilt.

The registered personal GitHub repository is the authoritative store source.
The official Supervisor code inspected at `bdcba61` updates its local Git copy
and serves the icon/logo from local app paths
([repository](https://github.com/home-assistant/supervisor/blob/bdcba61fc7c1500e96d2e319d07546f7b896e067/supervisor/store/repository.py),
[store API](https://github.com/home-assistant/supervisor/blob/bdcba61fc7c1500e96d2e319d07546f7b896e067/supervisor/api/store.py)).
No separate image hosting, brands-repository submission, registry publication,
new release tag, app reinstall, dashboard edit or live HA mutation is authorized
or needed for this publication. Store refresh and browser reload can be necessary;
no particular live cache interval or refreshed Green display is claimed.

## App-store discoverability (2026-10-04)

### D-200 — searchable display metadata without a runtime release

**Status:** accepted by the user for implementation and publication.

Keep the project/repository brand Frame Gallery. Set only the app display name
to `Frame Gallery – Samsung Frame TV` and its description to
`Samsung Frame TV artwork from museums or your own images.` The store's
location-sensitive fuzzy search includes descriptions, but a keyword late in a
description can still be excluded. The official frontend inspected at
[`6775b1e`](https://github.com/home-assistant/frontend/blob/6775b1e2bb78b3263312a0b6e8ad7c8dd25006d3/src/panels/config/apps/components/supervisor-apps-filter.ts)
searches name, description and slug with threshold `0.2`; Samsung now starts at
offset 16 in the display name and at offset 0 in the description. This is not a
claim that the exact installed frontend version or refreshed live results were
tested. A regression keeps both metadata fields' keyword offsets at most 20.

The generator remains authoritative. Slug, repository identity, version,
architecture image mappings, release tags, runtime and dashboard entities remain
unchanged. No rebuild, reinstall, TV run or live HA mutation is part of this
metadata publication. Installation instructions name the updated store entry.

## Public beta release (2026-10-04)

### D-199 — final native gates and public beta announcement

Status: authorized public-beta work completed in the documented scope.

Native run `37193338410` completed successfully for exact commit `8a3e7ee`:
ARM job `111409999318`, Intel job `111409999440`, including host quality gates,
actual test-context suites/root checks and real-limit memory measurements.
Both suites recorded 4,836 passes / five root-only skips and all five separate
root checks. A GitHub Node 20-to-24 action-runtime warning is recorded, not an
app-test failure or a reason to change pinned actions during release.

The saved prerelease was published only after both jobs succeeded. Public
`v0.1.0b1` tag was independently resolved without saved Git credentials and
matches `8a3e7ee0b5e07fb734768e18b9d9ac58e64e084e`. The release page confirms
the prerelease label and correct own account. Runtime/source commit stays
`d736c7a`; no public image/source archive was rebuilt, retagged or replaced.
Public release: https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b1 .

Technical source/notices, signatures, install, live preview/loading/fallback and
cleanup controls are recorded within their observed scope. The engineering
assessment requested in D-179 is not a qualified lawyer's opinion, historical
ownership/patent clearance, universal TV compatibility or a repeated fresh-pairing
test. Earlier records and private data remain preserved.

After the user's GitHub sudo confirmation, both publication variables were
saved/read back as `DISABLED_AFTER_0.1.0b1`. They deliberately fail exact
commit/hash checks, rather than deleting recoverable metadata. No permission was
expanded. The bounded token process had already ended at its 45-minute deadline
while waiting for that confirmation; no token was persisted. The final record
is a personal documentation-only commit, not a new runtime/image release.

## Public installation checkpoint (2026-10-04)

### D-198 — public Green verification and portable repository regression

Status: within the authorized Phase 9 publication/live-test scope; final
corrected hosted checks and beta announcement remain required.

The corrected repository at `60f22c4` was recognized and its separate pre-built
`0.1.0b1` app installed through the official UI. Public slug is
`a94fc569_frame_gallery`. Two normal card-started deliveries, immediate invalid
configuration refusal, preview/loading completion, cleanup and a local app-only
backup passed in the exact scope recorded in PHASE9_REPORT. Preserve the older
app/history; the new app starts its own history. The existing Local File camera
was reused unchanged because HA refuses a duplicate integration for the same
preview path; separate beta timer/script/dashboard were created with approval.

Hosted run `37185516101` failed the new root-descriptor pytest check: the app-only
container build context correctly contains no outer `repository.yaml`. Native
ARM reproduced the failure. Actual root/app-descriptor checks now run as a
mandatory fail-closed host gate in `check.sh`, while synthetic fixtures run on
both platforms. Missing/linked/invalid descriptors still fail; no skip, fallback,
coverage exemption, runtime/dependency/image change or rebuild is introduced.
Full Mac gates passed (4,830 / eleven existing skips, strict mypy 240 files,
100% line/branch); native ARM passed (4,836 / five root-only skips plus five
separate root checks). Final hosted native verification remains mandatory.
The final documentation check also caught the presentation regression's old
development slug. It now requires the observed public slug and cross-checks
the complete installed beta examples; all other assertions remain intact.
Follow-up build-context inspection found those examples absent from the test
context allowlist. Add `!examples/` and require it in the presentation regression.
This copies examples only to the unpublished test stage, not the runtime stage.
The previously passing bind-mounted ARM suite is not proof of actual context
inclusion. Actual-context checks and fresh hosted validation remain required.

The installed AppArmor backup equals the reviewed file after only Supervisor's
root-profile name substitution. Supervisor reports protection/custom profile,
no host network/full access/privileged capabilities. These observations are not
a new public-install kernel label/socket-negative probe; the earlier enforced
development-app probe evidence and fresh-pairing limitation remain explicit.

## Public repository recognition (2026-10-04)

### D-197 — required root repository descriptor

Status: correction within the authorized Phase 9 publication scope; public
retest pending, with no runtime or image change.

The real official one-click installation link reached the Green's repository
dialog with the correct own URL. Supervisor then returned "is not a valid app
repository". The required `repository.yaml` was absent both locally and on
public main `0b850e7`. Add the root descriptor with the own repository name,
URL and maintainer only. The packaging regression demonstrably fails before
the file exists and checks its exact metadata/root location afterwards.
No new dependency, privilege, personal contact address, image version, source
release or runtime change is introduced. The existing app remains untouched;
this failed attempt installed/started no app. Recognition must be retested
after publishing the correction, then separately confirm the new app install.

Primary requirement: https://developers.home-assistant.io/docs/apps/repository/
(root descriptor mandatory; read 2026-10-04).

## Public-image verification (2026-10-04)

### D-196 — verified pre-built images and separate install metadata

Status: within the user-authorized Phase 9 publication scope; clean public Green
installation and final dashboard/announcement remain pending.

Publisher `37159551965` completed successfully: both native validations and
both actual-image publishers, with source preflight, non-overwrite check,
unchanged RootFS layers and keyless signing. Runtime/source commit remains
`d736c7a9cd45f709de17572e68a5ebf8c5344933`. The exact images are:

- `ghcr.io/volkue-tech/frame-gallery-ha-aarch64@sha256:f170fb081171da23e25c8a46ad836625b4c174c5fd7d1a3b07d305344dc6e313`
- `ghcr.io/volkue-tech/frame-gallery-ha-amd64@sha256:89cf1ac74d80c5ad696aa1c7ffb67e8c5f62518f323e8b51a42716fc8eb9ff70`

Own publisher evidence archives were saved and SHA256-compared with GitHub's
artifact digests; both `published-digest.txt` entries match the above. All 13
preparation cases, twice each under 1 GiB, and 150 inspections passed per arch.
Maximum measured VM/time: ARM 766.5 MiB / 2.15 s; Intel 762.8 MiB / 1.92 s.
These are hosted Linux measurements, not promises of TV delivery or Green timing.

Both tag and digest manifest bytes/headers were independently checked without
saved credentials; complete anonymous Docker pulls succeeded and expose the
expected architecture and revision label. Hash-pinned official Cosign 3.1.3
independently verified both certificates/claims/transparency evidence against
`publish.yml@refs/heads/main`, issuer `https://token.actions.githubusercontent.com`
and the exact approved commit. No ignored-TLS/ignored-log verification option,
registry login, business account or secret mount was used.

Repository-linked packages were already public; no visibility mutation was
needed. Their UI's Latest badge is not a Docker `latest` tag: Cosign also creates
its digest-derived signature artifact tag. The numbered app tag is `0.1.0b1`.

Only after this evidence, generated Supervisor metadata gains the fixed own
`image: ghcr.io/volkue-tech/frame-gallery-ha-{arch}` and repository URL. Version
stays `0.1.0b1`, runtime bytes/digests/source package stay unchanged. Supervisor
supports the placeholder as a per-architecture compatibility path and uses
`version` as the image tag. Keep its supported `experimental` lifecycle flag:
the official schema has no `beta` stage. Sources:
https://developers.home-assistant.io/docs/apps/configuration/ and
https://raw.githubusercontent.com/home-assistant/my.home-assistant.io/main/redirect.json .
Later app-store/documentation metadata is not a new runtime-image build and
must not be substituted for the source package's recorded runtime commit.

## Phase 9 hosted correction (2026-10-04)

### D-195 — explicit JSON depth bound independent of the interpreter

Status: correction within the already authorized release scope; full local and
fresh native hosted validation remain required before publication.

The personal main push to `3550186` is verified. Intel job `111301941395` in
run `37156871737` failed three JSON-depth tests: its Python 3.14.7 build accepted
100,000 nested containers instead of raising a parser recursion error. The IPC
path still refused the resulting tree, but its test expected the parser's error;
network JSON and stored JSON relied on that parser limit and did not refuse it.
This is an input-bound defect, not a reason to waive the tests or coverage gate.

All three decoding paths now scan already byte-capped input before parsing and
refuse more than 32 nested containers, matching the existing IPC limit. The
scanner uses constant auxiliary space, ignores quoted content and escaped
quotes/backslashes, and leaves syntax validation to the JSON parser. The IPC
tree check remains as a second defense. Network refusal retains
`UNEXPECTED_FORMAT`; stored JSON raises `ValueError`, without altering existing
recovery behavior. No dependency, live configuration or persistent state changes.

Tests cover the exact 32/33 boundary in the scanner and both other decoding paths,
large quoted bracket strings, escapes, UTF-8, malformed input left to the parser,
extreme IPC input rejected before the parser is called, defensive tree refusal,
and deterministic mapping of a parser recursion failure. Existing deep-input
tests remain. Final full gates and matching exact-commit sources are mandatory;
earlier source candidates must not be published.

Final commands exited 0: full native Mac gates (4,816 passes / eleven existing
platform skips, strict host/Linux mypy 238 files, 100% full line/branch coverage
at 9,201 statements / 1,972 branches; mandated subset 7,543 / 1,640 at 100%).
Native ARM container validation: 4,822 passes / five root-only skips, all five
separate root checks and all 201 shipped notice documents verified. Logs:
`build/phase9/check-json-nesting-complete-20261004.log` and
`build/phase9/container-json-nesting-complete-aarch64-20261004.log`.
Subsequent exact-commit hosted run `37157727919` completed with success for
`d736c7a9cd45f709de17572e68a5ebf8c5344933`: native ARM `111304589397` and native
Intel `111304589480`, both including container/root/real-limit memory checks.
The matching clean-commit source package passed assembly and independent
preflight: 172 source archives, 518,133,760 bytes, SHA256
`8034a982322532b34b0c9893cda5135cb16448dc694e2c59f68ae42fedeb64b5`.
After exclusive Firefox access was confirmed, the source-only prerelease was
published at `sources-v0.1.0b1` (release ID `402713178`). Public metadata and tag
resolve to the exact approved commit; an actual unauthenticated download has the
same 518,133,760 bytes and SHA256. Both own repository approval variables were
saved and read back. Manual publisher run `37159551965` started on the exact
commit, with its approval and both native validations passed. Both publisher
jobs passed the public-source preflight and started actual-image validation.
No image/signature/clean-public-install success is claimed. These uncommitted
progress-document edits do not change the approved runtime commit/package.

## Phase 9 implementation decisions (2026-10-03)

### D-194 — numbered candidate before activation and exact source publication

Status: candidate preparation within the already authorized Phase 9 scope.

Use `0.1.0b1` for the first reviewed runtime/project/Supervisor version, keeping
the app's experimental stage and no pre-built image mapping until both signed
architecture images are anonymously available. This is not a final beta
announcement or a claim of completed clean public installation. Dependencies,
runtime behavior, existing Green configuration and user state are unchanged.
Refresh the lock offline and require the unchanged complete quality gates.

The real D-193 source package for clean `a7a99f8` passed assembly and independent
release-preflight verification: 172 source archives, 518,092,800 bytes, SHA256
`75502e27d7a216e8b8f73f301f713d242f8813e5c105f06dc9fe6058659609e6`.
Its 1,079-entry own snapshot contains no Git history or ignored build state.
The local LABEL-only publication build has exactly the tested runtime's RootFS
layers. That package is evidence for `a7a99f8`, not a matching `0.1.0b1` release
asset: assemble a fresh candidate from the final clean numbered-version commit.
Only that matching package may be published in the source-only release.

The personal main push to `a7a99f8` is verified. Native hosted validation run
`37155043758` was observed in progress, not reported passed in this entry.
Credentials remain transient/private; no business identity or backup branch
is transferred. Source/public-image/signature/install gates remain mandatory.

Before publication, a further workflow check found that GitHub's unspecified
Linux shell is `bash -e {0}`, without pipefail. The validation log's `check.sh |
tee` could therefore hide a failed quality gate. Both own workflows now explicitly
declare `defaults.run.shell: bash`, whose documented invocation includes
`-eo pipefail`. Nine offline regressions cover the host-only check of the actual
workflow declarations, synthetic declaration failures, actual passing
and failing pipelines, and the old shell as a negative control. No tests, warning
or coverage requirements are weakened. Previous hosted step status alone is not
proof that the piped host gate passed; require a new fail-closed native run.
Official reference: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#defaultsrunshell
The superseded `5161dff` source upload remains a private, untagged draft only;
no source release, registry tag or binary was distributed for that candidate.

The ARM job in run `37155043758` actually failed the notice shipping check and
two notice tests: `.gitignore`'s unanchored `build/` rule excluded the exact empty
Zstd upstream `build/LICENSE` and its image payload copy. Local tests saw these
files, but a fresh Git checkout did not. Narrow exceptions now retain only those
two original files; no generated build directory is broadly admitted. Source
assembly now checks all notice originals and copies in the actual Git archive,
including byte counts and hashes. Six regressions cover empty originals, missing
copies/originals, altered bytes, symlinks and same-size hash mismatches. The old
source packages are superseded and must not be published. No notice requirement,
test or safety limit was relaxed.

Final correction gates actually exited 0: native Mac (outside the sandbox's
group/setgid restriction) 4,794 passes / eleven platform skips, strict mypy 236
files, 100% full/mandated line and branch coverage; native ARM container 4,800
passes / five root-only skips and all five separate root checks. All 201 shipped
notice documents are byte/readability verified. Both actual workflow YAML/run
scripts pass syntax checks. The prior hosted ARM and Intel jobs both ended in
failure; neither is presented as a release success. Fresh hosted checks must pass.

The corrected `7f20c14` main push is verified, but hosted run `37156461763`
failed two old local-media test fixtures. They assumed unlink/recreate always
allocates a new inode; native Ubuntu can reuse it immediately. Both now allocate
the byte-identical replacement while the old file still exists, assert distinct
inodes and atomically rename it into place. The original refusal/no-worker
assertions remain. Runtime code is unchanged. That host run also exposed an
uncovered OS signal-refusal path previously covered only incidentally by timing;
two deterministic tests now verify both group/process kill attempts under
ProcessLookupError and PermissionError. No existing tests or coverage gate are
removed. The matching `7f20c14` source upload stays a superseded private draft,
not a public source release. Require full gates and fresh native hosted checks
of the final fixture correction.

Final fixture-correction gates exited 0: Mac 4,796 passed / eleven platform skips,
strict mypy 236 files, 100% full and mandated line/branch coverage; native ARM
container 4,802 passed / five root-only skips and all five separate root checks.
The 73 local-media tests and both direct signal-refusal tests also passed in
targeted runs. All 201 original shipped documents remain byte-verified.

### D-193 — gated native image publication and separately published sources

Status: prepared within the authorized Phase 9 scope, **not dispatched or proved
on a registry**. This does not activate publication or complete release gates.

Publication is manual-only on the own main repository. Two deliberately unset
repository approval variables bind the reviewed Git commit and the complete
source-package SHA256. Preflight also requires an explicit numbered beta whose
Supervisor metadata and runtime version agree; the current dev0 fails this gate.
Sources must already be anonymously available in the own source-only
`sources-v<VERSION>` release. Every archive member and the clean project snapshot
are compared against the actual publishing checkout before registry work.

Read-only native ARM/Intel validation is reusable from the same commit. Each
publishing job then validates its **actual** local image again, including all
container/root/notices/native memory checks. A LABEL-only developer Dockerfile
adds own provenance without a package rebuild; RootFS layers must still match.
No test image is published. Existing version tags are refused by authenticated
HEAD: only 404 permits creation; 200, redirects, 401/403 and other failures stop,
without blind retries. Workflow-wide serialization covers its own tag writers.
Digests are immutable; repository administrators could still move registry tags,
so retain the signed digest, not an absolute server-enforced tag-immutability claim.

Only publishing jobs get packages:write/id-token:write. Registry login uses the
ephemeral own-repository GITHUB_TOKEN, not the user's personal token, a classic
token, a business login or a secret committed to this repository. No credential
is attached to artifacts. Keyless signing publishes the workflow certificate,
identity/digest to Sigstore's public transparency service; it sends no HA/TV data.
The workflow verifies the signature against its exact own main workflow identity.
Package visibility/anonymous pull and clean public Green installation remain
subsequent observed gates. Do not silently delete/reuse a partly published version
after failure; preserve it and use an explicitly reviewed corrective procedure.

Signing tool recorded before execution: Cosign **3.1.3**, Apache-2.0, release-only,
not shipped in the app. Official GitHub release metadata reports amd64 SHA256
`4629c757b7618056f8ddd7e2625ae9fdd94c0372a65049520bc7d9df9efc7f71`
and arm64 `c5d324e091826b0d7a78eb16fef316450b4eb9aaec045611c08ba06f5e73220a`.
The workflow checks those exact bytes before running the tool. The versioned
official LICENSE is Apache-2.0. No binary is downloaded/run on this Mac as part
of this preparation. Home Assistant composite builder actions are not needed:
the existing approved native Docker workflow publishes its actually checked
local runtime rather than delegating a new rebuild to an additional action.

Primary references read:
- https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
- https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
- https://api.github.com/repos/sigstore/cosign/releases/latest (returned v3.1.3)
- https://raw.githubusercontent.com/sigstore/cosign/v3.1.3/LICENSE
- https://developers.home-assistant.io/docs/apps/configuration/

The D-192 assembler's first real attempt rejected Go's legitimate escaped
`!masterminds` basename **before creating a package**. Only that literal basename
character is now supported; traversal/symlink/hash bounds remain unchanged.
A dedicated regression covers the official naming convention. Twenty source-
assembler and 27 release-preflight/registry regressions pass locally. The first
Linux run exposed HTTPError response-body ResourceWarnings; errors are now
explicitly closed on both authorization and HEAD failure paths, without changing
the warnings-as-errors gate. The new closure/no-retry regression and full native
Mac/ARM-container suites pass; see the exact results in PHASE9_REPORT.

### D-192 — original Alpine subsidiary texts and repeatable source assembly

Status: implementation within the authorized Phase 9 engineering audit;
verification results recorded in PHASE9_REPORT. No new runtime dependency,
privilege, licence relabeling or live Green mutation.

The exact already retained Alpine source/recipe archives supply 111 additional
original documents, 2,672,323 bytes. All are read as inert regular members, never
extracted as a tree or executed; source hashes match D-186's fixed manifest.
`alpine-original-notices-manifest.json` records original member names, hashes and
lengths. This retains primary/subsidiary licences and notices, not a blanket claim
that build/test/manual licences all govern the installed binary. The original
empty Zstd build/LICENSE is retained faithfully, not used as a licence grant.
SQLite and tzdata dedications retain their original scope/exception wording;
recipe-only packages retain the exact recipe without fabricated MIT copyrights.
Auxiliary posixtz source says LGPL, despite tzdata's apk Public-Domain shorthand.
An offline existing native ARM image check found neither possible installed
posixtz executable path; its broader build source is retained regardless.

`source_bundle.py` replaces the ignored one-off D-191 assembler with a tested
development tool. Only nine fixed manifest sections and a clean Git HEAD are
accepted. It bounds 200 archives / 1 GiB total input, rejects symlinks, traversal,
tampered/missing sources and dirty/changing Git state; output is an exclusively
created own-build tar with deterministic metadata and read-back member hashes.
It never downloads, extracts or executes upstream sources. An existing output
is preserved; failed partial output remains unpublished for inspection.

SOURCE_AND_REBUILD documents corresponding source layout, separate-library
replacement, upstream build inputs and local developer installation. Ordinary
users still require no SSH/Docker/configuration edits. No byte-reproducible
Pillow/OS rebuild or independent legal opinion is claimed. Original code, locks
and decoder behavior are unchanged; full engineering applicability, final source
publication and public-install gates are not waived by this implementation.

### D-178 — enforced, one-way image and television child profiles

Status: accepted within the user-approved Phase 9 hardening scope (R-31).

The shipped entry point refuses to run without its own enforced Supervisor
AppArmor profile. Each fresh worker switches to the built-in image_worker or
tv_worker child before dropping credentials, setting no-new-privileges, loading
third-party code or accepting a request. The kernel label is checked before and
after the switch; the parent checks the bootstrap report before sending data.
Missing profiles, wrong labels, complain mode and failed transitions fail closed.
There is no user option to disable this requirement. The internal test wiring is
not the shipped entry point and can still be exercised on Docker Desktop, whose
kernel cannot enforce this policy.

Image workers have no network permission; they read only code/libraries, the
owned library and input scratch, and write delivery JPEGs only in output scratch.
TV workers may use IPv4 TCP and read the prepared delivery JPEG, but may not
read/write /data, previews, arbitrary scratch or shared-memory files. Neither
child may execute a program or switch back. Both permit setuid/setgid solely for
the trusted bootstrap; after the drop all capability sets are empty and NNP=1.
Existing memory, CPU, file, process, wall-time and parent-death limits remain.

Q-10/D-172 revisited: the parent remains root for this beta. It must create and
verify root-owned state and per-run group access, spawn/downgrade multiple fresh
workers, read their outputs and reap them. No additional capability or mount is
introduced. Moving orchestration to an unprivileged parent would require a new
privileged broker and a separately reviewed architecture, not a flag change.

Supervisor renames only the top-level profile header. Children are nested and
their actual parent name is obtained from the kernel, not guessed from a public
repository hash. Parent transition rules allow the two child suffixes; worker
bootstrap accepts only the validated own parent and a fixed task mapping.
Syntax acceptance is not claimed as live enforcement: Green tests must prove
allowed operation and denied access before release.

Primary references checked during implementation:
- https://raw.githubusercontent.com/home-assistant/supervisor/main/supervisor/utils/apparmor.py
- https://manpages.ubuntu.com/manpages/resolute/man2/aa_change_profile.2.html
- https://gitlab.com/apparmor/apparmor/-/raw/master/libraries/libapparmor/src/kernel.c

The AppArmor 4.1.7-r1 parser and its official 4.1.7 profile includes were used only
in a temporary development container. They are not new runtime dependencies.

### D-179 — final name and repository

Status: accepted, explicit user reply on 2026-10-03. Final name: Frame Gallery.
Personal repository: https://github.com/volkue-tech/frame-gallery-ha . This resolves
D-101/Q-13 for the chosen identifiers, not the publication/installation evidence.
Apache-2.0 remains the accepted licence of project-owned code only (D-102).
The empty public repository was created through the verified personal Firefox
session on 2026-10-03. The first audited `main` push at `39d25da` is now verified
against the remote SHA; native validation run `37141542920` started. Only the
personal main history was transferred, not the retained old-identity backup
branch. No container or release yet; the description says the beta is unreleased.
The user asked Codex to conduct the engineering licence audit; do not represent
this as an independent legal opinion or waive unresolved compliance obligations.

### D-180 — worker-only network syscall enforcement

Status: accepted implementation within the authorized Phase 9 hardening scope;
combined-profile no-TV probes and two normal card-started deliveries passed on
Green. Clean public-install validation remains a separate release gate.

The enforced Green image-worker label denied options, unrelated scratch,
shared-memory writes, execution and return transitions, but its `deny network`
rule did not reject either socket creation or real TCP/UDP attempts to the
container's loopback port 9. This is an observed enforcement gap, not a claim
about its kernel's cause. Do not claim that AppArmor alone proves no network.

A small, independently implemented seccomp BPF filter now complements AppArmor.
After the verified privilege drop/NNP and before starting the lifeline thread or
reading task input, image tasks deny socket creation; the TV task permits only
IPv4 stream sockets with default/explicit TCP. Both reject socketpair, ptrace,
pidfd_getfd and io_uring_setup, as well as foreign ABIs and high-bit/x32 syscall
aliases. Workers inherit only the validated pipe/file descriptors, not network
descriptors. The parent verifies the task-specific guard in the ready report.
Installation/architecture failures refuse the request; there is no public switch
to disable it. AppArmor continues to enforce file and executable restrictions.

This uses the existing standard-library ctypes/libc kernel interface, with no
new runtime package or container privileges. The parent does not install the
filter. Native aarch64 Docker kernel probes confirmed image sockets refused and
TV IPv4 TCP allowed with UDP/IPv6/UNIX refused. Subsequently the Green's actual
enforced children plus seccomp passed the image TCP/UDP denials and TV TCP
allowance/UDP denial, file/exec/return denials, identity, NNP, token and address-
space checks. Confirmed records/options/preview hashes were unchanged and scratch
empty. This was a synthetic no-TV probe, not a successful artwork delivery.
Architecture-wide generated-filter tests cover both aarch64/x86_64. Native
amd64 kernel tests subsequently passed in the hosted run recorded in D-185.

Primary ABI references checked: [kernel seccomp documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html),
[seccomp UAPI](https://github.com/torvalds/linux/blob/v6.12/include/uapi/linux/seccomp.h),
[x86_64 syscalls](https://github.com/torvalds/linux/blob/v6.12/arch/x86/entry/syscalls/syscall_64.tbl),
[generic/aarch64 syscalls](https://github.com/torvalds/linux/blob/v6.12/include/uapi/asm-generic/unistd.h),
and [audit architecture constants](https://github.com/torvalds/linux/blob/v6.12/include/uapi/linux/audit.h).
No kernel implementation or example filter was copied.

### D-181 — native validation CI, no publication rights

Status: first native hosted run `37141542920` started at `39d25da` on 2026-10-03.
Both jobs passed native host/Docker architecture checks and dependency setup;
quality gates and container/memory outcomes remain pending.

Validation uses the official GitHub standard `ubuntu-24.04-arm` and
`ubuntu-24.04` runners, asserts native host/Docker architecture and does not
install QEMU. Each runs the host gates, native disposable-child seccomp tests,
container/root checks and `--measure` under real RLIMIT_AS. The workflow has only
`contents: read`, does not persist checkout credentials, never accesses HA/TV,
and cannot publish registry images or change the repository. Results are retained
for 14 days. Publishing remains a separate, gated workflow to add later.

Development-only official GitHub Actions, not shipped in the app image; exact
commit LICENSE files read on 2026-10-03, all MIT (GitHub, Inc. and contributors):

| Action | Pinned commit | Licence source |
| --- | --- | --- |
| actions/checkout v4 | `11d5960a326750d5838078e36cf38b85af677262` | https://github.com/actions/checkout/blob/11d5960a326750d5838078e36cf38b85af677262/LICENSE |
| actions/setup-python v5 | `a26af69be951a213d495a4c3e4e4022e16d87065` | https://github.com/actions/setup-python/blob/a26af69be951a213d495a4c3e4e4022e16d87065/LICENSE |
| actions/upload-artifact v4 | `ea165f8d65b6e75b540449e92b4886f43607fa02` | https://github.com/actions/upload-artifact/blob/ea165f8d65b6e75b540449e92b4886f43607fa02/LICENSE |

CI uses the already-approved uv 0.12.19, installed from PyPI wheels with explicit
hashes (aarch64 manylinux 2.17/2.28 and x86_64 manylinux 2.17, rechecked against
https://pypi.org/pypi/uv/0.12.19/json). Project dependencies use `uv sync --locked`.
No new runtime package or paid runner is introduced. Official runner reference:
https://docs.github.com/en/actions/reference/runners/github-hosted-runners .

### D-182 — parent reads worker outputs using the existing Docker capability

Status: implemented and positively checked within authorized Phase 9. The
extended enforced Green probe passed parent-output read in `0.1.0.dev6`, with
both worker checks, all eight confirmed hashes unchanged and scratch empty.
After restoring the normal entry point, a card-started Cleveland delivery was
selected by the TV in 19.4 s; preview refreshed and loading ended. That run also
exposed a separate backup-link permission omission, addressed by D-183.

The extended enforced Green probe confirmed worker permissions, but the root
parent failed to read the synthetic worker-owned 0660 output with EACCES.
The draft's `dac_read_search` does not match Docker's default capability set:
Docker supplies `DAC_OVERRIDE`, not `DAC_READ_SEARCH`. Replace that one parent
AppArmor capability with `dac_override`; do not add a container capability,
grant FOWNER, make outputs world-readable or weaken either child. Six parent
capabilities remain. DAC override also covers write/execute mode checks, so its
AppArmor permission is not described as read-only; the unchanged mandatory path
rules still restrict writes and execution independently. The root parent already
has the trusted state/workspace-management role and CHOWN, not untrusted decoding.
The worker capability drop, child paths, seccomp, NNP and budgets remain intact.

This supersedes the specific `dac_read_search` requirement in D-168/D-172 and
§17.6, not their other responsibilities. Reference checked on 2026-10-03:
https://docs.docker.com/engine/containers/run/#runtime-privilege-and-linux-capabilities .

### D-183 — pair-specific parent links for atomic state backups

Status: implemented and live re-checked within authorized Phase 9. After the
official Supervisor update to `0.1.0.dev7`, a card-started Cleveland delivery
finished with selected/uploaded markers, exit 0 in 16.9 s. Both backup warnings
were absent; state had seven files / 4,323 bytes with no temporary files, scratch
was empty, preview refreshed without reload and loading ended. Original options
and protected/non-host-networking state were unchanged. The subsequent app-only
checkpoint verified 14 unique history IDs / 13 prior-generation IDs (subset,
latest-delivery difference only), three uploaded ledger IDs in history and the
latest uncertainty in the ledger backup. This is actual snapshot evidence;
absence of a warning alone was not treated as its substitute.

The first ordinary enforced run delivered successfully but reported EACCES
refreshing both history and upload-ledger backup generations. `Directory` uses
`os.link(primary, backup_temporary)` before an atomic rename; the existing `rwk`
parent state permission does not grant hard-link creation. Add two `link subset`
rules, each restricted to its own `/data/state/{history,upload_ledger}.json`
primary and corresponding `.bak.tmp-*` link name. No general `l` permission,
cross-document link, worker rule, Docker capability, mount or protection change
is added. The existing validated-primary, descriptor-relative, no-symlink and
fsync/rename logic remains unchanged. Packaging tests require exactly these two
parent-only link pairs. Syntax and link/target direction checked against the
official packaged AppArmor manual on 2026-10-03:
https://manpages.debian.org/bookworm/apparmor/apparmor.d.5.en.html#Link_rules .

### D-184 — inventory every installed slashpackage category

Status: implemented in the authorized Phase 9 engineering audit; no runtime,
privilege, dependency or live-system change. The real existing aarch64 image
contains s6-dns 2.4.1.2 under `/package/web`, s6-networking 2.8.0.0 under
`/package/net` and skalibs 2.15.0.0 under `/package/prog`. The earlier
`/package/admin`-only inventory omitted all three. Inventory now scans the four
fixed categories, sorts results and skips symlink categories/version aliases;
a regression test fails with the old implementation. Corrected in-container
inventory observes eleven versioned S6 packages; all 22 inventory unit tests
pass. Notices now identify the three omitted components and the verified helper.

Their exact official versioned sources/COPYING files are retained: all ISC.
The exact s6-overlay source `conf/versions` and `mk/skaware.mk` also disclose
BearSSL revision `7bea48e5e850ab4cafbe68d3765cdaba13a86d6f` and a static-libc
toolchain build. Those transitive sources, texts and binary/build provenance
remain explicitly open; do not infer them from Alpine's dynamic musl package.
Nine additional base archives, including the exact tempio binary VCS revision
and official base recipe commit, have URL/calculated-hash records in
`LICENSES/base-source-manifest.json`. This is partial D-135 evidence, not release
clearance. Source files were read or retained only, never executed.

### D-185 — native hosted ARM and Intel validation evidence

Status: passed in the authorized personal public repository, source `39d25da`.
Run `37141542920` verifies native host and Docker architecture before any test;
no QEMU/Rosetta is used. ARM job `111256837980` completed successfully at
17:58:51 UTC and Intel job `111256837847` at 18:02:25 UTC on 2026-10-03.
Both host quality/kernel gates, container builds, inventory/init/stop checks,
4,718 non-root container tests (six expected skips), five root checks and the
13-case twice-repeated real 1 GiB memory gate succeeded. The Intel native memory
condition of D-170 is now fulfilled. Hosted Docker has no own AppArmor profile;
its smoke check correctly fails closed before artwork, rather than claiming
enforced operation. Enforced Green evidence remains distinct.

The ARM log was read through the personal GitHub Firefox session: all 26 prepare
results succeeded, peak address space 765.5 MiB, slowest 2.16 s, and 150
inspections had zero failures. Intel suite/root results and successful final job
were observed; exact Intel peak/time values are not transcribed here. Evidence:
https://github.com/volkue-tech/frame-gallery-ha/actions/runs/37141542920 .
The Node.js 20 action-runtime warning was read: GitHub forces the three pinned
actions onto Node.js 24; it is not a test failure or lost-artifact warning.
Validation has no package/repository write permission. The later D-184 inventory
fix changes only development tooling/notices and still needs its own hosted
validation; no source compliance, image publication or public-install gate is
waived by this successful run.

### D-186 — exact Alpine sources and static build-input evidence

Status: partial D-135 engineering evidence, not a completed release licence gate.
The existing own ARM image's apk database supplies build commit `c` for all 61
packages. Forty-five exact official aports recipe directories were retained from
GitLab, with all included patches/build files, without evaluating shell code or
following symlinks. The quoted SHA512 lists were parsed in both one-line and
multiline form: 197 local files and all 58 external source files verify against
their exact recipe checksums. The source files total 282,359,632 bytes; recipes
243,307 bytes. Public URL/hash/package records are in
`LICENSES/alpine-source-manifest.json`; retained archives are under ignored
`build/phase9/alpine-{recipes,sources}/`. Hash checks were repeated offline.
Source archives and manifest generation are not a reproducible-binary proof or
a finding that every subsidiary licence has been reviewed.

The exact S6 recipe refers to BearSSL commit
`7bea48e5e850ab4cafbe68d3765cdaba13a86d6f`; its official Git source and original
MIT LICENSE.txt are retained. Both documented skarnet GCC 15.2.0 toolchain
archives were passively read, never executed: their libc.so strings report
`1.2.6-git-11-g5122f9f3`, resolved in official musl Git to
`5122f9f3c99fee366167c5de98b31546312921ab`. Exact musl source/COPYRIGHT are
retained, including the MIT text and subsidiary attribution/exception discussion.
These observations identify documented build inputs, not cryptographic proof of
which static objects are inside the installed S6 binaries. Go 1.26.5's exact
official source archive is SHA256-verified against go.dev release metadata;
original LICENSE/PATENTS are retained. See `LICENSES/static-source-manifest.json`.

The exact GCC 15.2.0 source shows GPL-3.0-or-later plus GCC-exception-3.1 in
`libgcc/libgcc2.c` and `libstdc++-v3/include/bits/c++config`; its full original
COPYING.RUNTIME is preserved under `LICENSES/gcc-15.2.0/`. Alpine's broad apk
licence field remains quoted verbatim, not treated as a complete file-level
licence expression. Exception eligibility and all other source/binary notices
remain part of the release engineering audit.

### D-187 — preserve full libbsd/libmd attributions and public-domain statements

Status: exact upstream COPYING texts read and preserved; no blanket legal
clearance or completed native-Pillow source bundle. Official versioned sources
libbsd 0.12.2 and libmd 1.1.0 were retained with calculated archive hashes (not
publisher signatures). `LICENSES/pillow-libbsd-libmd-source-manifest.json` records
their URLs and texts. Both original COPYING files are retained unabridged.

libmd's file-level public-domain statements cover MD4, MD5 and SHA1; the text
identifies Colin Plumb, Todd C. Miller and Steve Reid. Use the descriptive local
identifier `LicenseRef-libmd-Public-Domain` for those exact statements, with the
complete original COPYING as its definition, not the non-existent SPDX term
"Public Domain" or a newly invented licence. Its aggregate source description
also retains BSD-3-Clause, BSD-2-Clause, ISC and Beerware notices.
libbsd's complete file-level notice includes ISC/MIT/BSD-2-clause variants,
public-domain statements, Beerware and a five-clause notice for a manual page;
the prior package-directory shorthand BSD-3-Clause is not an exhaustive list.
Preserve the full source notice; do not claim all source/manual terms describe
every linked binary. Applicability and complete distributed notices remain in
the engineering release review.

### D-188 — repair a documentation-only tempio inventory regression

Status: corrected locally and verified by both native hosted jobs on `aaf7016`.
Run `37143460336` on `9cd37f8` failed on ARM and Intel solely with
`not in the notices: tempio 2026.07.0 (Go 1.26.5, 11 Go modules)`. Reading both
authenticated GitHub job logs confirmed 4,719 non-root passes / six expected
skips, all five root checks, all 26 prepare cases and 150 inspections without
failure on each architecture. ARM peak VM was 766.5 MiB / slowest 2.15 s;
Intel 762.8 MiB / slowest 2.33 s, under the unchanged 1 GiB limit. These are
successful substeps, not a successful workflow or release clearance.

The expanded notice retained the toolchain version and separate module table
but lost the exact `Go 1.26.5 and 11 Go modules` phrase the existing checker
requires. Restore that observed metadata without weakening the checker. A new
repository-document regression fails before the correction and passes after;
wrong Go version and module count must still be rejected. All 25 inventory tests
and both retained-image notices checks pass. Full unsandboxed macOS gates pass:
4,717 tests / 11 expected skips, strict mypy and 100% line/branch coverage.
An initial sandboxed run failed two unchanged setgid handover tests; the same
complete suite outside that restriction passes, without changing or skipping
those tests. Original Go LICENSE/PATENTS and GCC COPYING.RUNTIME were compared
byte-for-byte to the retained archives. No runtime or live-system change.
The exact corrected main push `aaf7016c1afd2a6ca23bdd37354c8713bc6ff192` is
remotely verified. Native run `37145245403` succeeded on both architectures:
ARM job `111267719103` completed at 18:58:37 UTC and Intel job `111267718919`
at 19:01:57 UTC (2026-10-03). Host gates, container/root checks, notices and the
real-limit memory step all succeeded. No exact new hosted peak/time or suite
counts are transcribed without reading those logs. This validates `aaf7016`,
not the subsequent source-evidence/notice-packaging changes or release gates.

### D-189 — native-Pillow sources, patent notices and the TIFF security patch

Status: partial D-135 engineering evidence; no runtime change or release clearance.
The official Pillow 12.3.0 release's wheel workflow, dependency versions and
exact multibuild submodule `4546f4d4820ffd0104b872c3b6187260b3e64edc` were read
as inert source. The release build inputs identify libavif 1.4.2's AOM 3.14.1,
dav1d 1.5.3, libyuv commit `644251f252a84bf8ce91ff0aca86a9b16b069ab8` (version
1924) and sharpyuv from libwebp 1.6.0. These agree with the observed wheel
inventory; they are build-input provenance, not cryptographic static-object
equivalence or a claim that these sources reproduce the wheel byte-for-byte.

Twelve additional exact native source archives (64,401,436 bytes) are retained
from official versioned endpoints, with no source execution or installation.
The public `LICENSES/pillow-native-source-manifest.json` records those twelve,
five release/build-input archives and four existing Alpine source archives
shared by the native inventory. All archive SHA256s were rechecked offline;
dav1d also matches its official published SHA256, the four Alpine sources match
their exact recipe SHA512s. Other SHA256s are calculated retention checks,
not publisher signatures. Initial redirects were rejected: FreeType was fetched
from the GNU-selected HTTPS mirror and X.org from its HTTPS archive endpoint;
there was no HTTP downgrade or automatic unbounded redirect following.

Twenty-seven unabridged licence/patent/patch documents are read and retained,
with byte-for-byte archive-member checks and recorded hashes. These include
AOM's BSD-2-Clause LICENSE and AOM Patent License 1.0 PATENTS, libyuv and libwebp
patent grants, complete libjpeg-turbo LICENSE.md/README.ijg, FreeType FTL and
its licence map, and native primary texts. Conditional patent grants are
retained without asserting universal patent clearance. The original libyuv
PATENTS has no final newline and remains byte-identical. Complete sources
retain subsidiary notices; file-level applicability is not declared finished.

Pillow's installed ARM SBOM embeds libtiff's upstream cherry-pick
`782a11d6b5b61c6dc21e714950a4af5bf89f023c`, the fix for CVE-2026-4775. Its decoded
patch is byte-identical to the official Pillow release patch now retained under
`LICENSES/libtiff-4.7.1/`; upstream TIFF source alone would omit this input.
The complete TIFF licence also includes the Berkeley LZW acknowledgement;
THIRD_PARTY_NOTICES now preserves that acknowledgement. No patch was newly
applied to the runtime by this project.

Three offline repository regressions verify all 27 retained text hashes/lengths,
the versioned source records and critical patent texts, and the patch/required
acknowledgements. With the existing inventory tests, 28 targeted tests pass.
Root repository evidence is currently outside the image test context, so these
three data checks are explicitly skipped there, not represented as shipped
distribution checks. Full unsandboxed local gates passed: 4,720 tests / eleven
expected skips, Ruff and strict mypy over 228 files on host/Linux, unchanged
100% package line/branch coverage (9,168 statements / 1,954 branches).
The stale provisional Pillow comment in pyproject.toml is corrected to D-171;
no requirement or lock changes. Packaging the actual notice texts, complete source bundle,
replacement/rebuild instructions and subsequent validation remain release gates.

### D-190 — original notice texts in the Supervisor-compatible build context

Status: implemented within the authorized Phase 9 distribution work; not release
clearance. The app's build context is `frame_gallery/`, so the root licence
evidence was not previously copied into the image. `scripts/license_bundle.py`
mechanically stages only the public LICENSE, NOTICE, THIRD_PARTY_NOTICES and
LICENSES files into committed `license_bundle/`, without source archives,
credentials or live data. Supervisor therefore needs no SSH or pre-build script.
The fixed allowlisted input has file-count/byte bounds; symlinks and non-regular
files are rejected; unexpected output files are preserved and stop regeneration.
Generated bytes are exact, including source files without a final newline.

The Dockerfile copies this payload to `/usr/share/frame-gallery/licenses/`;
the current collection is 89 evidence files plus its generated manifest.
The host quality gate fails if originals and generated copies differ. Container
validation reads every distributed file as UID/GID 65534 against the checkout's
manifest, rejects unexpected files and retains a count-only result.
`--no-build` treats changed licence payloads as changed build inputs.
Eight new tests cover determinism, manifest hashes, stale/missing/extra/symlink
data, preserved unexpected files and CLI/build shipping. Native-source and
repository-notice tests now use the shipped payload inside the image, so absent
evidence is a failure rather than a skipped check. The old broad Dockerfile
`licenses` assertion is narrowed to the actual OCI label it meant to prohibit;
no misleading blanket image-licence label is introduced.

Current ARM rebuild confirms the original texts are shipped, readable and
byte-verified without root. Latest complete container checks passed with 4,734
non-root tests / five root-only skips and all five separate root checks. All seven
previously unavailable repository-notice/source-data cases now pass in the image.
Full host gates passed: 4,728 tests / eleven expected skips, strict mypy over 230
files, unchanged 100% package/mandated line and branch coverage. The longer ARM
measurement also passed on the initial notice-layer rebuild: all 26 prepare
cases, 765.5 MiB peak VM, slowest 1.59 s under the real unchanged 1 GiB limit;
150 inspections, no failures (0.62 s total). Decoder/runtime code and dependencies
are unchanged across the later documentation/test refresh. App options,
Green installation and TV state are unchanged. Complete source/rebuild
distribution and engineering applicability findings remain release gates.

### D-191 — offline corresponding-source candidate assembly

Status: candidate assembled and hash-verified locally; no publication or D-135
legal/compliance clearance. The assembly reads only the exact public-source
manifests already retained under LICENSES and the clean own project commit
`40f3e65aad47464ea64590955446446d84a611a7`. Every input archive must have a
matching retained SHA256 and byte length; no missing input is silently skipped.
It packages 172 original archives (507,415,363 bytes), including all 45 exact
Alpine recipes with their patches, upstream distfiles, Python/S6/Go/native-Pillow
sources and identified static-library sources. The own source is `git archive`
of that commit (4,608,000 bytes), not Git history or the old backup branch.
Binary toolchain archives are deliberately not redistributed by this candidate.

The candidate tar contains only regular inert archive/index members; no source
was extracted or executed. Every packed archive and the project snapshot were
read back and SHA256-verified against its index. Result:
`build/phase9/source-candidate-40f3e65.tar`, 512,204,800 bytes,
SHA256 `bbe95367e669da9cbd4bb647d0bd28459d93b49fcf166bd1a6aaa52aef061992`.
It is retained on the Mac only, with about 20 GiB free; no HA backup, token,
TV pairing data or user artwork is included. This removes the mechanical
first-candidate assembly gap, not subsidiary-applicability, replacement/rebuild,
final release-source synchronization or public availability/retention gates.

### Phase 9 licence inventory corrections (engineering audit in progress)

The exact official base recipe at `6a3ff4c10f6ed8564a092c33051024a1b1042ee2`
(`2026.08.0`) specifies bashio 0.17.5 and jemalloc 5.3.1. The aarch64 image
contains jemalloc's library and helper scripts, which the earlier inventory
missed. Its version helper reports a missing-git-tags placeholder, not 5.3.1;
source-to-binary provenance and amd64 verification remain open. Exact upstream
licences verified: bashio 0.17.5 MIT, s6-overlay 3.2.3.0 ISC, jemalloc 5.3.1
BSD-2-Clause, tempio 2026.07.0 Apache-2.0. Texts for the first three are added
under `LICENSES/`. Subsidiary s6/Go components, bundled-library texts and full
corresponding sources remain open; no release-compliance completion is claimed.

Further audit progress: all eleven exact Python sdists are retained and checked
against PyPI SHA256 values; their primary licences and applicable Apache NOTICE
files are preserved. Six exact skarnet sources and ISC COPYING files are also
retained (execline, s6, linux-init, linux-utils, portable-utils, rc). Public source
manifests under `LICENSES/` record URLs/hashes. The latter hashes are calculated,
not publisher attestations. s6-overlay/helpers build sources, linked dependencies,
Go/native-wheel components and all Alpine source/patch/rebuild materials remain
open. These records do not complete D-135 or assert binary-source equivalence.

Additional progress on tempio: twenty-one exact Go source ZIPs were retained from
the official module proxy and checked against upstream tempio `go.sum` using the
documented directory-content hash algorithm (https://go.dev/ref/mod#authenticating).
The eleven modules named in the observed binary are distinguished from ten
extra test/build-source modules. Their original primary licence files are
byte-identical under `LICENSES/go/`; versions/URLs/SHA256/`h1` and primary licence
identifiers are recorded in `LICENSES/go-source-manifest.json` and notices.
Go 1.26.5 toolchain source, subsidiary notices and reproducible binary/build
equivalence are still open. No new runtime package or source execution occurred.

Status values:

- `accepted`: binding.
- `proposed`: awaiting approval by the user, and by Codex where `TASKS.md` requires it.
- `superseded`: replaced by a later decision.
- `split`: accepted in part and proposed in part; the decision text says which part is which.

Phase 1 added:

- decisions D-106 onward;
- the proposed dependency inventory;
- the risk register;
- the open questions.

Each architecture decision gives its rationale at the `ARCHITECTURE.md` section named in brackets.

This version (revision 2) records the user decisions and corrections from the **Codex review of commit `d42adf5`** (see *Review records*).

The **user's approval of Phase 3 on 2026-09-27** accepted D-108, D-112, D-115, D-124, D-127, D-131, D-134, the Phase 3 adapter details of D-132 and D-136, and D-141 to D-145. It amended D-119 and resolved Q-14 and Q-22. The documentation re-check at the start of Phase 3 is recorded in D-146.

The **Phase 3 gate on 2026-09-27** accepted D-146 to D-152 and resolved Q-25 with option (a).

The **Phase 4 gate on 2026-09-27** accepted D-153 to D-159, after Codex re-ran the quality gates (3 850 tests, 100 % line and branch coverage). The 20 000-entry bound of history and the ledger is accepted for the first beta; R-29 explains its consequence. The user authorized Phase 5 the same day.

The **Phase 5 gate on 2026-10-02**, after the Codex gate review, accepted D-160 to D-164, and D-165 on the condition that the Linux and root isolation tests and the worst-case preparation measurement under the real `RLIMIT_AS` pass in Phase 6; they are mandatory before any live test on the Home Assistant Green. It also decided the open Phase 5 questions (see *Phase 5 gate decisions*). The user authorized Phase 6 the same day.

**Phase 6** proposes D-166 to D-172 for its gate (see *Phase 6 decisions*), among them the authoritative inventory of the exact Pillow runtime wheels and of the image (D-171).

## Accepted constraints

### D-001 — Independent repository

Status: accepted

The new project is not a fork and shares no Git history or source files with predecessor projects.

### D-002 — Specification-only initial handoff

Status: accepted

Claude receives functional requirements, constraints, and acceptance criteria. Phase 1 contains no application implementation.

### D-003 — Primary platform

Status: accepted

Home Assistant OS on Home Assistant Green (`aarch64`) is the primary target. `amd64` is secondary.

### D-004 — User installation boundary

Status: accepted

End users must not need SSH, shell commands, local Docker installation, or changes to `configuration.yaml`.

### D-005 — Default artwork treatment

Status: accepted

The complete artwork is preserved by default. Cropping occurs only through an explicit option. Non-matching aspect ratios are fitted onto a 16:9 canvas, black by default.

### D-006 — One-shot lifecycle

Status: accepted

Each start performs at most one upload attempt outcome and then exits. Selection and network activity are bounded, and a no-match run leaves the television unchanged.

## Proposed decisions requiring approval

### D-101 — Project name

Status: proposed. Needed before Phase 9.

Working name: **Frame Gallery for Home Assistant**.

Rationale: distinct, descriptive, and not tied to a predecessor repository name. Branding and trademark wording need review before release (R-14).

The provisional internal identifier `frame_gallery` is **accepted** (D-138), and a later rename would be mechanical.

### D-102 — Project license

Status: **accepted** (Codex review of `d42adf5`, user decision).

The Apache License 2.0 applies to independently authored project code.

**Scope.** Apache-2.0 covers the **project-owned source code only**. It does not cover the complete distributed container image, which also contains third-party components under their own licences. These include:

- GPL-3.0-or-later `libimagequant`, bundled in the Pillow wheels;
- LGPL-2.1-or-later FriBiDi;
- LGPL-3.0 `samsungtvws`;
- GPL-2.0 OS packages such as BusyBox.

The inventory below lists them all. *Phase 6 finding (D-171, accepted at the Phase 6 gate):* the exact runtime wheels contain neither `libimagequant` nor FriBiDi, only Pillow's LGPL-2.1-or-later fribidi-shim; the image's GPL components are Alpine packages (BusyBox, bash, readline, gdbm, and others). The scope of Apache-2.0 is unchanged.

Rationale: permissive reuse with an explicit patent grant. Third-party dependencies keep their own licenses. The `LICENSE` file is added when publication is prepared (Phase 9).

### D-103 — Implementation language

Status: proposed (refined in Phase 1).

**Decision:**

- Python, with code compatible with **CPython 3.12–3.14**. CI runs all three versions.
- The container runs the Alpine `python3` of the chosen base image, pinned to an exact version.

**Rationale:**

- 3.12 is security-only.
- All runtime dependencies publish `musllinux_1_2` wheels for 3.12–3.14.
- `samsungtvws` 3.0.6 and Pillow 12 need Python ≥ 3.10.

### D-104 — Samsung transport

Status: **accepted for design.** The inspection method was approved in the Codex review. The dependency row was to be approved before Phase 5. *Amended at the Phase 4 gate (user decision, 2026-09-27):* the user authorized Phase 5 with the check of the version and the LGPL-3.0 obligations as its first step, and allowed the pinned version to be installed from PyPI into the git-ignored environment. The row is recorded in Phase 5 and confirmed at the Phase 5 gate. *Phase 5 gate (user decision, 2026-10-02):* the row and its LGPL-3.0 obligations are confirmed with D-160.

**Decision:**

- Use `samsungtvws` **3.0.6** (LGPL-3.0, Python ≥ 3.10), core install only.
- Import it only in the isolated TV worker task (D-109).
- Establish the adapter surface **only by inspecting the installed 3.0.6 distribution**: its public signatures and docstrings in a local virtual environment, without GitHub access (Q-15, resolved).

**Phase 1 findings from PyPI.** The release, license, and requirement facts were independently verified. The maintainer, pairing, and subnet notes were not re-verified.

- Since 3.0.0, the README documents no Python art API. The 2.7.2 README named `art().supported()`, `upload(data, file_type='JPEG')`, `select_image(content_id, show=…)`, and `get_artmode()`. No README documents a "no matte" value or a client-name parameter. The constructor form with `port=8002` and `token_file` appears only in READMEs up to 2.7.2.
- No exceptions or timeouts are documented.
- Newer TVs prompt on every connection unless *First Time Only* is set.
- TVs refuse connections from other subnets. The app starts without `host_network`, and Phase 8 verifies connectivity (Q-16).
- The package has a single maintainer, and its releases come in bursts.

**Why a library rather than an own implementation.** Samsung does not document Art Mode or the local protocol, and SmartThings has no art capability. A maintained library under a known license is safer than a new protocol implementation, which would also be the most sensitive area under `LEGAL_BOUNDARIES`.

### D-105 — Release architectures

Status: proposed

Publish `aarch64` and `amd64` first. Add other architectures only after successful builds and explicit support decisions.

Phase 1 note: Home Assistant currently supports only these two app architectures (32-bit support ended with release 2025.12).

## Architecture decisions (Phase 1)

### D-106 — Synchronous core, phase budgets, watchdog [§4.3, §7]

Status: **accepted** (bounded execution and cleanup; Codex review).

**Decision:**

- A single run thread, with no `asyncio`.
- Phase deadlines come from the normative 120 s budget table (D-114), and every blocking call is clamped.
- `Allowance` counters bound the loops.
- A watchdog kills the worker process group and exits at `T + 10 s`.
- DNS resolution runs in a fresh daemon thread per lookup, joined with a clamped timeout. The number of abandoned lookup threads is bounded by the request allowances.

### D-107 — Ports and adapters with an enforced import boundary [§5, §20.2]

Status: proposed

**Decision:** Third-party imports are confined to three places:

- the `imaging` worker tasks (Pillow);
- the `tv` worker task (`samsungtvws`);
- `net.transport` (`urllib3`, `certifi`).

The parent never imports Pillow or `samsungtvws`. An import-boundary check enforces this.

### D-108 — Guarded gateway for all provider traffic [§10, §7.5]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Decision:** The gateway enforces:

- exact or label-boundary host rules;
- HTTPS on port 443 only;
- one resolution, with every address checked as global;
- connection to the validated IP, with SNI and a peer check;
- `CERT_REQUIRED` with TLS ≥ 1.2 and `certifi`;
- at most 3 re-validated redirects;
- identifier `fullmatch` and percent-encoding;
- caps on decoded bytes;
- per-request totals (metadata 10 s, probe 5 s, download 20 s);
- per-address connect timeouts and re-clamped reads;
- pacing;
- no cookies, proxies, or credential files.

### D-109 — Isolated, unprivileged workers [§11.3, §12]

Status: proposed. The target design is unchanged; its delivery is sequenced by D-139.

**Decision.** All image inspection, decoding, rendering, and encoding runs in a spawned worker, and so does the whole TV interaction. Each worker:

- drops to user 65534 with no supplementary groups;
- then sets `PR_SET_PDEATHSIG`;
- sets its umask and `RLIMIT_AS`: 1 GiB for the image worker, 512 MiB for the TV worker, with CPU limits;
- installs logging and Pillow limits before any third-party import;
- sees only the allowlisted environment;
- runs in its own process group;
- returns markers and results as bytes-only JSON.

The parent chooses every path, validates `delivery.jpg`, and computes the SHA-256. The TV worker emits progress markers.

**Delivery.** The complete bootstrap, including the privilege drop, is delivered with the process executor in Phase 5. Enforce-mode AppArmor and final verification come in Phase 9 (D-139).

### D-110 — Atomic state, pre-staging, bounded records [§13]

Status: **accepted** (atomic writes and bounded state; Codex review).

**Decision:**

- **State files.** Plain JSON under `/data`:
  - `history.json`: confirmed sent and displayed works;
  - `upload_ledger.json` (D-137);
  - `current.json` and `last_run.json`;
  - a per-provider cache.
- **Write primitive.** One primitive for every write:
  - directory-descriptor operations with `O_NOFOLLOW`;
  - `O_EXCL` random temporary names;
  - `fsync`, then rename, then directory `fsync`.
- **Pre-staging.** The next history generation is written before DELIVER, and the ledger intent is committed there too. After `selected`, recording history is a single rename.
- **Backups.** History and the ledger keep a best-effort `.bak`, which covers unparseable or schema-invalid primaries.
- **Reader.** Primary, then `.bak`, then empty with a warning. Only parse or schema failures are quarantined (at most 3 files). A newer file version gives `state_error` before the TV is touched.
- **Locking.** A non-blocking lock; contention gives `already_running`.

### D-111 — Preview in `/media` through a Local File camera [§13.5, §16.3]

Status: **accepted** as the primary beta design (Codex review).

**Decision:**

- The exact delivered JPEG is published atomically under `/media/frame_gallery/preview/`. Publication is refused if any path component is a symbolic link.
- A UI-created Local File camera and a `picture-entity` card display it.
- **Platform basis.** Home Assistant OS creates `/media` without user configuration, and configured or default media directories are in the default external-directory allowlist. A normal installation therefore needs no `configuration.yaml` edit, no configuration-folder mapping, no SSH, and no manual file changes.
- Freshness is governed by D-140.

### D-112 — Static options with optional helper overrides [§15.3]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Decision:**

- Static options always work.
- The optional `source_helper`, `department_helper`, `style_helper`, and `color_helper` are each read with at most one request:
  - ≤ 4 reads in total, each ≤ 3 s, within the 10 s configuration window;
  - `fullmatch` validation, no redirects or retries;
  - `Authorization` sent only to `http://supervisor`;
  - a 64 KiB cap, and only the `state` field is used.
- Any failure falls back to the static value, with one warning.
- Originally the app wrote nothing to Home Assistant; D-176 adds only an optional, fixed timer.cancel after cleanup.

### D-113 — Record history before publishing the preview [§4.1]

Status: **accepted** (Codex final gate review of `9352e77`; Q-18 item 4 is resolved and `PRODUCT_SPEC.md` is amended).

**Decision:** Record the confirmed sent history immediately after `selected`, then publish the preview.

**Rationale:** Duplicate prevention no longer depends on this order, because the upload ledger (D-137) excludes the work once it is uploaded. The order only makes history slightly more robust.

### D-114 — Budget decomposition [§7.2]

Status: **split.**

- **Accepted** in the Codex review, replacing the earlier 265 s proposal: the 120 s total, the 10/60/40/10 split, clamping of all timeouts, the 70 s no-match bound, and 30 remote dimension requests with a separate local allowance.
- **Proposed**, to be confirmed by Phase 2, 5, and 8 measurements: the sub-budgets, the allowances, the `RLIMIT_AS` values, and the upload allowance. The 150 s timer helper was accepted in the final gate review (Q-09).
- **Phase 2 result.** The phase arithmetic is confirmed with a fake clock: the phases sum to 120 s, every child deadline stays within its phase and the total, and `no_match`, `source_failed`, and `image_failed` end by 70 s even when every step uses its whole budget. Phase 2 has no real providers, workers, or television, so the real-time measurements move to Phase 5 (preparation under `RLIMIT_AS`) and Phase 8 (the Green and the TV).
- **Phase 5 gate (2026-10-02).** The preparation measurement under the real `RLIMIT_AS` runs in the Phase 6 container (D-165) and on the Green in Phase 8 (R-09). The image worker's 1 GiB stays for now; any change is decided only from the Linux measurement.

The tables in `ARCHITECTURE.md` §7.2 are normative once approved.

**Decision.** The default hard total deadline is **`T` = 120 s**:

| Phase | Budget | Notes |
| --- | --- | --- |
| CONFIGURE + RESOLVE_FILTERS | **10 s** | IPv4 validation needs no DNS; up to 4 helper reads of ≤ 3 s each |
| Content window: SELECT + ATTEMPT + PRE-STAGE | **60 s** | Discovery ≤ 30 s; per attempt, download ≤ 20 s and prepare ≤ 15 s; the last 2 s are reserved for PRE-STAGE or a no-delivery FINISH, so `no_match`, `source_failed`, and `image_failed` all exit **by 70 s** |
| DELIVER | **40 s** | Connect ≤ 5 s; pairing wait ≤ 20 s |
| FINISH | **10 s** reserved | |
| Shutdown allowance | 10 s | Watchdog at 130 s |

**Allowances:**

- a shortlist of 2;
- 150 candidates after exclusion;
- 15 metadata requests;
- **30 remote dimension requests** (Q-20);
- 20 000 directory entries at depth ≤ 4;
- 300 local header inspections.

**Per-request limits:**

- metadata 10 s, probe 5 s, download 20 s, helper 3 s;
- connect ≤ 5 s and read ≤ 10 s, both re-clamped;
- DNS ≤ 3 s.

Every timeout is clamped to the remaining total. The worker `RLIMIT_AS` is 1 GiB for the image worker and 512 MiB for the TV worker. The dashboard timer indicator is **150 s** (`T` + 30 s).

The beta has no user-facing time option. An advanced total-deadline option may come later, validated within a safe range, and the standard instructions use 120 s.

### D-115 — Retry and pacing policy [§7.4]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Decision:**

- **Metadata GETs.** At most 1 retry, and only for a connect error, 502/503/504, or a 429 with `Retry-After` ≤ 5 s (seconds or HTTP-date). The wait is `max(Retry-After, 1 s)` plus jitter, and the retry is skipped if it would exceed the deadline.
- **403/429 stop.** Any 403, or a 429 that is not retried, from any host of a provider stops all requests to that provider for the run. Remote shortlisted candidates are then not attempted.
- **No retries** for probes, downloads, helper reads, uploads, or selects.
- **TV reconnect.** At most 1, only before `upload_started`, and never after a pairing timeout.
- **Pacing.** A `min_interval` of 1 s for both the Art Institute and Cleveland.

### D-116 — Shape and quality thresholds [§8.1]

Status: **accepted** (Codex final gate review; Q-03).

**Decision:**

- **Square band:** 0.95 ≤ w/h ≤ 1/0.95.
- **Strict near-16:9:** ±1 % in log ratio, `abs(ln(r / (16/9))) ≤ ln(1.01)`, about 1.760–1.796. This threshold may be revisited after Phase 8 visual testing.
- **Quality:** reject any work whose upscale factor exceeds 2.5×.

All values are measured after EXIF orientation, on the rendition that will be delivered.

### D-117 — Fallback permission [§8.2]

Status: **accepted** (Codex final gate review; Q-11).

**Decision:** Fallback is permitted only when `landscape_only` is on and `fit_mode` is `contain`. There is **no fallback in `cover` mode**, and a fallback image is never cropped.

### D-118 — Local media identifier [§9.3]

Status: **accepted** (Codex final gate review; Q-04)

**Decision:** `local:fp:<sha256(size ‖ first 64 KiB ‖ last 64 KiB)>`, plus the fingerprints of the last 10 previews.

### D-119 — Honest User-Agent [§10]

Status: **accepted** with the amendment below (user approval of Phase 3, 2026-09-27).

**Decision:**

- ~~The User-Agent is `FrameGallery/<version> (+<project URL>)`.~~ Superseded by the amendment below.
- Provider courtesy headers, such as the Art Institute's `AIC-User-Agent`, carry the project name and a project-owned contact email (Q-22), never user data.
- There is no browser impersonation.

**Amendment (user decision, 2026-09-27).**

- No invented or not-yet-existing project URL is used. Until a public project URL is decided (Q-13), the User-Agent is `FrameGallery/<version> (contact: volkue@gmail.com)`.
- The Art Institute's `AIC-User-Agent` uses the project contact: `FrameGallery/<version> (volkue@gmail.com)`.
- Tests keep using a clearly recognizable placeholder contact, never the real address.
- Before publication (Phase 9), both headers switch to the real public repository URL.
- The real address is transmitted only in a later, explicitly approved live request (Q-22). Phase 3 makes no live request.

### D-120 — First public beta scope [§22]

Status: **accepted** as amended in the Codex review. `PRODUCT_SPEC.md` is amended accordingly.

**Included:**

- **Sources:**
  - local media;
  - the **Art Institute of Chicago** (D-132), the default remote source (Q-08, accepted);
  - the **Cleveland Museum of Art** (D-136).
- **Filters:** source, department, style/period, and colour, with the capability matrix and visible reporting of unsupported filters (D-124); optional helpers. *Amended at the Phase 3 gate (D-146, D-152; Q-25, option (a)):* the first beta offers Cleveland departments and periods for both museums. It offers no style and no colour filter: the style option offers periods only, and the colour option accepts only "any" or a no-filter synonym (`all`, `random`, `none`, or an empty value).
- **Selection:** landscape-only, strict with fallback, the upscale rule, and `contain` (default) or `cover`.
- **State:** atomic, pre-staged history; the TV-upload exclusion ledger and quarantine (D-137); an atomic preview; a small cache; self-healing pairing.
- **Deliverables:** documentation and dashboard YAML; images for `aarch64` and `amd64`.

**Deferred:**

- a companion integration;
- multi-source rotation;
- Europeana, Rijksmuseum, and The Met;
- Cleveland colour filtering by local analysis (Q-24);
- an advanced total-deadline option;
- hostname or IPv6 TV addresses;
- Collection Image support;
- remote-probe machinery;
- matte selection;
- helper auto-provisioning;
- an unprivileged parent process (Q-10);
- a configurable library folder;
- local colour and style filters;
- a history reset (Q-06);
- more architectures.

**Excluded or not planned:**

- Google Arts & Culture (Q-01, resolved) and Bing (Q-17, resolved). Their researched status is kept in `ARCHITECTURE.md` §9.4 and `PRODUCT_SPEC.md`. Undocumented or `robots.txt`-incompatible access is never implemented.
- Ingress.
- Managing the TV's image storage.

### D-121 — Image safety limits [§11]

Status: proposed

**Decision:**

- Width and height ≤ 20 000 px each.
- Pixel limits: ≤ 64 MP for JPEG and ≤ 40 MP for PNG, both checked from the header before decoding. Pillow's global limit is set to 64 MP, and the PNG cap is an explicit check.
- Decompression-bomb warnings are raised as errors; only JPEG and PNG are opened.
- Downloads are capped at 40 MiB.
- The image worker runs under a 1 GiB `RLIMIT_AS` ceiling (virtual memory). The estimated worst-case resident peak is ≈ 450–550 MiB.

### D-122 — Colour management [§11.1]

Status: proposed

**Decision:**

- Convert embedded ICC profiles to sRGB; assume sRGB otherwise.
- Output an 8-bit RGB baseline JPEG without EXIF.
- Normalize palette and bit depth before resizing. Colour-space conversion and alpha compositing happen after resizing.

### D-123 — App options [§15.1]

Status: proposed. The defaults are **accepted** (Codex review): `contain`, with no crop; landscape-only on; strict near-16:9 on. The original default `source` was `art_institute_chicago`, accepted in the final gate review (Q-08). D-210 supersedes only that source default for the next release; explicit saved sources are retained.

**Decision.** The options are those in `ARCHITECTURE.md` §15.1:

- `tv_host`: an IPv4 literal, required;
- `source`: `art_institute_chicago`, `cleveland_museum_of_art`, or `local_media`;
- `department`: namespaced `aic_…` or `cma_…`;
- `style`: `style_…` or `period_…`;
- `color`;

  *Amended at the Phase 3 gate (D-146, D-152; Q-25, option (a)):* vocabulary version 1 ships only `cma_…` departments and `period_…` keys, and no `aic_…`, `style_…`, or `color_…` key. `color` therefore accepts only "any" or a no-filter synonym (`all`, `random`, `none`, or an empty value) in the first beta. See `ARCHITECTURE.md` §15.1.
- `landscape_only`, `strict_tv_format`, `fit_mode`, `background_color`;
- four optional `*_helper` options;
- `log_level`.

There is no time-limit option and no library-path option.

### D-124 — Filter model, vocabularies, and capability matrix [§9.2, §15.2]

Status: **accepted** (user approval of Phase 3, 2026-09-27). The documentation re-check amends the Art Institute's column of the matrix (D-146); vocabulary version 1 and the narrowed matrix are implemented (D-152).

**Decision:**

- **Four distinct dimensions:**
  1. source/museum, which selects the provider (a department is never called a museum);
  2. department/collection, namespaced by source;
  3. style/period;
  4. colour.
- **Capability matrix**, published in `DOCS.md` and in the option descriptions:
  - Art Institute: department, style, period, and colour. *Amended by D-146: period only in the beta, because the documentation does not name the department and style values or the colour object's members.*
  - Cleveland: department and period. Style and colour are unsupported in the beta.
  - Local media: none of the four.
- **Visible reporting.** A filter that does not apply to the selected source is ignored for the run and reported in three places:
  - a WARNING;
  - `ignored_filters` in the summary line;
  - `last_run.json`.
- **Helper values.** A helper value that normalizes to no vocabulary key falls back to the static value, with one warning. A known key that does not apply to the selected source overrides the static value, and is then ignored and reported like a static value.
- **Vocabularies.** Versioned, with deterministic normalization. The final lists are fixed in Phase 3 (Q-14, resolved: small, curated lists from documented values only; D-146).

### D-125 — Television address rules [§15.4]

Status: **accepted**. The IPv4 literal was accepted in the Codex review, and the ranges in the final gate review (Q-12).

**Decision:**

- `tv_host` must be an **IPv4 literal in an RFC 1918 private range**: `10/8`, `172.16/12`, or `192.168/16`.
- **Rejected:** `169.254/16` link-local addresses; loopback, unspecified, multicast, and broadcast addresses; the container's own interface networks and the Supervisor's internal network.
- No DNS is involved, and the validated literal goes to the TV worker.
- Hostnames and IPv6 are deferred.
- The user's Phase 8 test value is `192.168.178.30`. It is entered in the options only, never shipped as a default, and never hard-coded.

### D-126 — Dashboard filter approach [§16]

Status: proposed

**Decision:**

- **Beta:** static options plus documented helpers.
- **Ingress:** not planned.
- **Companion integration:** deferred.

### D-127 — Standard-library parsing only [§18.2]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Decision:** Parse `json`, and `html.parser` only if a provider is ever approved that needs it. No lxml or BeautifulSoup.

### D-128 — Reproducible builds and update policy [§17]

Status: **accepted**, including `uv` as the development lock tool (Codex review).

**Decision:**

- **Lock file** generated with `uv pip compile --generate-hashes` (`uv` 0.12.19, `MIT OR Apache-2.0`, development only). *Phase 2 proposes an amendment (D-142): a project `uv.lock` with hashes, and `requirements/runtime.txt` exported from it with `uv export`. The install rules below are unchanged.*
- **Installs** use `--require-hashes --no-deps --only-binary=:all:`.
- **Pinning:** the base image by tag and digest, and `python3` by exact apk version.
- **Reviews:** monthly, and immediately on advisories.
- **Upgrades** need the full test suite and an updated inventory. Pillow and `samsungtvws` are upgraded only in dedicated commits.

### D-129 — App configuration and AppArmor profile [§17.1, §17.6]

Status: proposed

**Decision:**

- **`config.yaml`:**
  - `startup: once`, `boot: manual_only`, `init: false`;
  - `arch: [aarch64, amd64]`;
  - `stage: experimental` until Phase 8;
  - `homeassistant: "2026.2.0"`, which is **not** raised for Collection Image;
  - `homeassistant_api: true`. This grants Core REST and WebSocket access; the app limits its own use to ≤ 4 state GETs;
  - `tmpfs: true`, `timeout: 20`;
  - `map: [{type: media, read_only: false}]`, narrowed by AppArmor;
  - `backup_exclude: cache/**, state/quarantine/**, tv/**`;
  - no `host_network` (Q-16).
- **Custom `apparmor.txt`:**
  - `/media` read-only, except read-write on `/media/frame_gallery/preview/**`;
  - creation allowed only for `/media/frame_gallery/`, `preview/`, and `library/`;
  - read-write on `/data/**` and `/tmp/**`;
  - only the paths spawn needs;
  - `inet` and `inet6` stream and dgram sockets only;
  - minimal capabilities.

  It runs in **complain mode in Phases 6–8** and is **enforced and verified in Phase 9** (D-139).
- **Security rating:** 6.

### D-130 — Container base image and build [§17.2]

Status: proposed

**Decision:**

- **Base image:** `ghcr.io/home-assistant/base`, pinned by tag and digest.
- **Build:**
  - multi-stage;
  - `python3` pinned to an exact apk version;
  - a venv created `--without-pip`, from hash-pinned, binary-only wheels;
  - Pillow from PyPI wheels only.
- **Labels:**
  - `io.hass.arch` from `BUILD_ARCH`, falling back to `TARGETARCH`;
  - `io.hass.version` from a required `ARG`;
  - the OCI `licenses` label omitted.
- **Tooling:** Buildx for builds; the Home Assistant builder actions and Cosign for releases.
- **Selection criteria:** the official guidance, reproducibility, and copyleft surface.

**Open verification (Phase 6).** The image pull needs approval. *Approved by the user on 2026-10-02:* reading the tags of `ghcr.io/home-assistant/base` and pulling it for `aarch64` and `amd64`, pinned by tag and digest, as the base of the app image, for these checks, and for the tests and the measurement in the container (*Review records*, *Phase 5 gate decision*). Then:

- (a) the Alpine and Python versions. Once the Python version is fixed, repeat the Pillow wheel SBOM inspection against the exact two runtime wheels; that result is authoritative for the inventory;
- (b) the container stops when `CMD` exits;
- (c) a stop request delivers SIGTERM with enough grace;
- (d) `SUPERVISOR_TOKEN` is visible without `with-contenv`.

**Fallback:** a plain Alpine base with `init: true`. Its inventory row must be completed first.

### D-131 — HTTP transport: `urllib3` directly [§10]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Decision:**

- The gateway uses `urllib3` 2.x with retries and redirects disabled, streaming, and explicit timeouts. It enters as a direct dependency in Phase 3.
- `requests` is not used by application code.
- `httpx` is not adopted.

### D-132 — Art Institute of Chicago adapter [§9.5]

Status: **accepted** as a beta source (Codex review). The adapter details are **accepted** (user approval of Phase 3, 2026-09-27), as amended by the documentation re-check (D-146): period filter only in the beta, dimensions from the documented Images resource, and renditions only for images at least 1686 px wide.

**Decision.** Use the documented API:

- public-domain works only. `is_public_domain` is requested in `fields`, and every record must have `is_public_domain == true` and an image id;
- department, style, period, and colour from documented metadata. Colour is filtered server-side if range queries work, and client-side otherwise. *Amended by D-146 and the Phase 3 gate (Q-25, option (a)):* the first beta supports only the period, because the department and style values and the colour members are undocumented;
- the documented 1686 px IIIF rendition, with the 4K canvas as the stated need;
- pages sampled without replacement;
- requests paced at 1 s, with the courtesy header;
- at most 15 metadata requests per run;
- a cache of counts and page hints only.

Upscaling is up to ≈ 2.28× in `contain` mode (R-19).

### D-133 — Exit-code policy [§4.2]

Status: proposed (Phase 8 check under Q-07).

**Decision:** Every classified outcome exits 0. Only `internal_error` (70) and watchdog termination (71) exit non-zero. The documentation says to keep the app's Watchdog off.

### D-134 — Rights-basis allowlist [§9.1]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Decision:**

- Every candidate carries a structured `rights_basis`.
- Each provider has an allowlist:
  - local media: `USER_SUPPLIED`;
  - Art Institute: `CC0` (`is_public_domain`);
  - Cleveland: `CC0` (`share_license_status == "CC0"`).
- Selection rejects anything else, and the contract suite checks every adapter.

### D-135 — Copyleft source availability [inventory]

Status: proposed. **The qualified licence review is a release gate (Phase 9).**

**Decision:**

- Each release attaches the corresponding source for every copyleft component in the image:
  - the `samsungtvws` sdist;
  - the exact source releases of **`libimagequant` 4.4.1 (GPL-3.0-or-later)** and **FriBiDi 1.0.16 and fribidi-shim (LGPL-2.1-or-later)**, as bundled in the Pillow wheels. Versions follow the authoritative runtime-wheel inspection;
  - the Alpine aports and distfiles for the GPL and LGPL packages in the image SBOM.
- The qualified licence review specifically covers:
  - the GPL-3.0-or-later `libimagequant` linked into Pillow, and what it means for distributing the image and for the project's Apache-2.0 code;
  - LGPL replaceability for FriBiDi and `samsungtvws`.

  Options the review may weigh:
  - comply as distributed;
  - build Pillow from source without `libimagequant`. This would change D-130's binary-only rule and needs its own decision.

  No option is chosen here.

  *Phase 6 (D-171, accepted at the Phase 6 gate on 2026-10-03):* the authoritative inspection finds neither `libimagequant` nor FriBiDi in the runtime wheels. The attached sources therefore become the `samsungtvws` sdist, the Pillow 12.3.0 sdist (for the fribidi-shim), and the Alpine aports and distfiles of the image's GPL and LGPL packages, and the review's `libimagequant` points fall away.
- The source stays available while the image is distributed, and for at least 3 years. A written offer is the fallback.
- The GPLv3 installation-information duty is assessed as not applicable, pending qualified review.

### D-136 — Cleveland Museum of Art adapter [§9.6]

Status: **accepted** as a beta source (Codex review). The adapter details are **accepted** (user approval of Phase 3, 2026-09-27). They were re-verified against the live documentation on 2026-09-27; D-146 adds an explicit `limit` on every request, leaves out the one department value that contains commas, and enforces period bounds on `creation_date_earliest`.

**Decision.** Use only the documented Open Access API:

- **Every request** carries the `cc0` flag and `has_image=1`.
- **Every record** must have `share_license_status == "CC0"` and an `images.print` entry.
- **Rendition:** only the documented print JPEG (3400 px long side, JPEG). Its string-typed `width` and `height` are parsed defensively. The `full` TIFF is never requested.
- **Filters:**
  - `department`, using the 21 documented values. *Amended by D-146 and D-151:* a curated subset of 12 is offered, and "Performing Arts, Music, & Film" is left out;
  - period, through `created_after` and `created_before` (integer years);
  - style and colour are unsupported in the beta.
- **Random selection:** a random `skip` based on the documented `info.total`. The undocumented `randomize` parameter is not used.
- **Hosts:** exactly `openaccess-api.clevelandart.org` and `openaccess-cdn.clevelandart.org`.
- **Identity and caching:** identifier `cma:<Athena id>`; requests paced at 1 s; ≤ 15 metadata requests per run; a cache of the total per filter (1 day) and skip hints (7 days).
- **Attribution:** a shortened form of the museum's suggested citation, as a courtesy.
- **Terms:** CMA's terms reserve future keys and transaction limits. The adapter allows an optional key later, and treats 401/403 as a stop.

### D-137 — TV-upload exclusion ledger and uncertainty quarantine [§12.4, §13.6]

Status: **accepted** (Codex review; replaces the earlier statement that an uploaded work might be resent).

**Decision:**

- **History unchanged.** The confirmed sent history keeps its meaning and changes only after `selected`. So do the current artwork and the preview.
- **Separate ledger.** A bounded TV-upload exclusion ledger (`upload_ledger.json`) holds two kinds of entry.
  - **`uncertain`**: a write-ahead intent. It is committed at PRE-STAGE, *after* the TV budget re-check and before the TV is contacted.
    - **Removed** whenever no `upload_started` marker was seen: the TV was unreachable, pairing was not accepted, art mode is unsupported, SIGTERM or the kill timer came before `upload_started`, or the upload allowance was insufficient. Also removed on an explicit upload refusal.
    - **Kept** as an uncertainty quarantine only after `upload_started` without `uploaded`, or when the process dies without classifying the run. The period is **30 days** (Q-23, accepted in the final gate review).
    - `upload_started` is sent before the library's upload call, so a missing marker proves nothing was uploaded.
  - **`uploaded`**: promoted immediately when the `uploaded(content_id)` marker arrives, even if selection is then refused, times out, or becomes uncertain.
    - If the promotion write fails, or the process dies before its `fsync`, the entry stays `uncertain`. The run logs an ERROR, and the outcome is unchanged.
    - Confirmed uploads that were durably recorded are never uploaded again. An upload that could not be recorded is excluded for the quarantine period.
- **Exclusion.** Selection skips anything in history, `uploaded`, or an unexpired `uncertain` entry. After a process kill following an upload, the committed intent still excludes the work.
- **Bounds.** At most 20 000 entries and 5 MiB. The ledger uses the same atomic write, `.bak`, reader, and version handling as history. Entries for works that reach history are pruned lazily.
- **Tests.** Acceptance items `E7`–`E10`.

### D-138 — Provisional app identifier `frame_gallery` [§5, §17.1]

Status: **accepted** (Codex review).

**Decision:** `frame_gallery` is the provisional internal identifier. It is used for:

- the Python package name;
- the app slug;
- `/media/frame_gallery`;
- the User-Agent;
- the TV client name, if the installed 3.0.6 API accepts one.

The final public name remains D-101.

### D-139 — Implementation sequencing (vertical slice) [§23]

Status: **accepted** (Codex review).

**Decision.** Implement in this order:

1. Deterministic selection and rendering (Phase 2).
2. The AIC, CMA, and local adapters, with fake or synthesized fixtures (Phase 3).
3. Bounded state and duplicate prevention (Phase 4).
4. The Samsung adapter contract, from the installed package (Phase 5).
5. Home Assistant app packaging (Phase 6), then offline validation (Phase 7).
6. Live Home Assistant Green and TV validation (Phase 8).
7. AppArmor enforcement and final release hardening (Phase 9).

The security and hardening design is unchanged, and no final acceptance criterion is weakened. `TASKS.md` reflects this order.

### D-140 — Preview freshness is release-blocking; refresh mechanism [§16.3]

Status: **accepted** as a requirement (Codex review). Native Local File refresh selected in Phase 8; observed evidence and limitations below.

**Decision:**

- The dashboard is not declared complete until repeated live tests on the Home Assistant Green show every newly delivered image without a stale browser cache (acceptance item `G5`).
- The mechanism must keep the preview correct on every documented start path: card tap, scheduled automation, and a start from the app page.
  - Any post-run step lives in one UI automation triggered by the Running sensor turning off, which covers every start path, including starts from the app page.
  - Alternating file names are eligible only if the app writes each delivered preview to both names, so an older artwork can never appear, for example after a `no_match` run.
- Phase 8 tests card-started, automation-started, app-page-started, and `no_match` runs.
- Phase 8 selects and documents one proven, fully UI- or API-based mechanism. The candidates are:
  1. Local File's file-change behaviour;
  2. `homeassistant.update_entity`;
  3. two alternating file names with `local_file.update_file_path`;
  4. another UI- or API-only method.
- The evidence and the chosen mechanism are recorded here and in R-07.
- The Collection Image integration (2026.9+) may be documented as an optional alternative. It must not raise the app's minimum Home Assistant version.

**Phase 8 selection (2026-10-03, within approved supervised validation):**
candidate 1, native Local File refresh of atomically replaced
`/media/frame_gallery/preview/latest.jpg`. Repeated card deliveries, an actual
event-triggered automation delivery, direct app-page delivery and unchanged
preview after no-match/cancellation are recorded in `PHASE8_REPORT.md` on
HA 2026.9.4 Green. No post-run camera action, alternating names or browser reload
was needed. One recovery run bounds visible refresh to at most 14 seconds after
publication; it is not a universal latency guarantee. No Running-triggered
refresh automation is required for this candidate. This closes the preview
freshness selection, not the separate loading or whole release gate: Running
feedback lagged about 15 minutes and produced early or prolonged indicators.

## Phase 2 implementation decisions (accepted)

These record how Phase 2 realized the architecture, and every place where it deviates from the text of `ARCHITECTURE.md`. The user accepted them with the Phase 3 approval on 2026-09-27.

### D-141 — Phase 2 layout, seams, and classification details [§4, §5, §9.1, §12, §21]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Layout.** Beyond §21, Phase 2 adds:

- top-level `domain.py` (shared value types), `errors.py` (cross-component errors), and `randomness.py` (the injected random source);
- `app/ports.py`, `app/records.py`, `app/environment.py`, `app/signals.py` (§21's `app/context` is not needed);
- `config/filters.py` (filter value types) and `config/overrides.py`. Helper merging lives in `config`; the Phase 3 `ha` package only reads helper states;
- `budget/limits.py`, `selection/exclusion.py`, `imaging/contract.py`, `imaging/sniff.py`, `imaging/delivery.py`, `isolation/channel.py`, `isolation/in_process.py`, `logs/summary.py`;
- `tests/support/` (fake clock and port fakes), `scripts/check.sh`, and `DEVELOPMENT.md`.

**Internal dependencies beyond the §5 "Depends on" column.** The top-level `domain`, `errors`, and `randomness` modules may be used by every component. Beyond those: `budget.watchdog` uses `logs.summary`; `logs.setup` uses `config.options` (the log level); `isolation.in_process` uses `budget.clock` and `logs.summary`; `imaging.contract` and `imaging.worker_tasks` use `selection.geometry` and `isolation.executor`; `providers.contract` uses `config.filters` and `budget.deadline`; `tv.port` uses `budget.deadline`. There are no cycles. §5's "stdlib" entries are read as "no third-party packages"; the enforced boundary (D-107) is unchanged: Pillow only in `imaging/worker_*`, and no networking or process modules in Phase 2.

**Port shapes.**

- *Provider (§9.1).* `Capabilities` carries the source, the key, and `dims_in_metadata`. The filter capability matrix stays central in `config.capabilities` (it drives the published matrix, B8), and the rights allowlist central in `providers.rights` (D-134). The Phase 3 contract suite asserts that each adapter agrees with both. `probe_ref` is replaced by a `DimensionProbe` bound next to the provider (`ProviderBinding`).
- *Television (§12.1).* `DeliveryRequest` carries no token seed path, and the runner does not act on `DeliveryResult.auth`: the Phase 5 adapter owns the token store (§12.2). The request carries a `stop_requested` signal instead (see *Stop requests*). The port returns or raises only once its worker is dead; the runner also kills every worker before classifying an interrupted delivery.

**Classification details.**

1. The parent validates `delivery.jpg` in ATTEMPT, not in PRE-STAGE, so an invalid output falls through to the next candidate. The parent also re-checks the reported real size against the chosen reason (defence in depth).
2. A request cut off by its *own* time limit (a probe, a download, or the 15 s preparation) is a transport or processing failure. Only a request cut off by the *content window* counts as "search limits reached" (§4.2). The decision uses deadlines, never float comparisons of timeouts.
3. `NOT_FOUND` is for single resources (a rendition or a probe target). An adapter reports a 404 or 410 from a discovery endpoint as `HTTP_ERROR`, so a broken search endpoint is `source_failed`.
4. A `DeadlineExceeded` that no stage handles is classified by the no-delivery rules inside the content window (limits reached). Before the content window it ends the run as `deadline_exceeded` (a CONFIGURE overrun). *This extends the §4.2 meaning of `deadline_exceeded`.*
5. After `selected`, RECORD always runs (§12.3): an adapter failure after `selected` gives `delivered_with_warnings`; any other internal error after `selected` still runs RECORD and reports `internal_error` with history +1.
6. `not_authorized`, `unsupported`, or `insufficient_time` reported *after* `upload_started` keep the quarantine (the upload may have happened), and the status names the outcome. §12.1 says the worker reports them only before `upload_started`.
7. Local header-inspection failures are not transport failures; they only feed the aggregated warning (§9.3). A provider that repeats a work in one pass is not charged twice, and the work never takes two slots.
8. The summary line reports ignored filters as `ignored_filters=…` (D-124 and §9.2; §19 is amended to match).

**Stop requests (§7.6).**

- `Cancelled` derives from `BaseException`, so no `except Exception` (in logging handlers or adapters) can swallow it.
- Before DELIVER, a stop request raises `Cancelled` wherever the run is. Every stage boundary, every attempt, and the points just before the preparation, the upload-intent commit, and the television call also re-check a pending request, so a request that a port swallowed is honoured before new work starts.
- **DELIVER defers stop requests for the whole television call** and for the rest of the run. The request carries a `stop_requested` signal: the adapter polls it while it waits for its worker, kills the worker, relays every marker the worker had sent, and returns. The runner classifies such a run as `cancelled` from the markers. So no SIGTERM can drop a marker, split a marker from its ledger write, or lose the adapter's reply; an adapter that ignores the signal only delays the stop until its own kill timer. (§7.6 "the worker group is killed and the markers are read" now happens inside the adapter.)
- An explicit upload refusal removes the intent even when a stop request is pending: nothing was stored.
- The entry point creates the controller with its stop requests deferred, before it installs the SIGTERM handler. The runner ends that initial deferral inside its classified region, so a stop request that arrives before the run is ready is classified as `cancelled` with a last-run record.
- One runner and one `CancellationController` serve exactly one run.

**FINISH.**

- PUBLISH (preview and current record) may not use FINISH's last 2 s; they are kept for the last-run record.
- A run decided in SELECT or ATTEMPT finishes within its content window (the 70 s bound) as long as the window leaves the 2 s reserve; after an overrun, FINISH gets its own reserve instead of a sliver.
- The summary line is logged last, after CLEANUP and after the watchdog is stopped. If the watchdog had already claimed the run, it emits the only summary line and exits 71 (§4.3, §19).

**Per-candidate decisions.** Selection stays free of I/O and reports one decision per candidate to an optional sink; the runner logs them at DEBUG (§19).

### D-142 — Development environment and lock workflow (amends D-128) [§17, §20.4]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

- **`uv`.** Version 0.12.19, installed from PyPI into the git-ignored `.tools/` directory with its wheel hash checked against PyPI. `pyproject.toml` pins `required-version`, sets `python-downloads = "never"` (interpreters would come from outside the package index), and limits the lock to macOS and Linux.
- **Lock.** A project `uv.lock` with hashes for the whole development environment. `requirements/runtime.txt` is exported from it with `uv export --locked --no-dev --no-emit-project`, hash-pinned. This replaces the separate `uv pip compile --generate-hashes` step of D-128, so the development and runtime pins cannot drift apart. Installs keep `--require-hashes --no-deps --only-binary=:all:`. The Phase 6 container build narrows the runtime file to the chosen Python version and platform.
- **No build backend.** The project is not built as a distribution (`package = false`), so no build backend enters the inventory.
- **Local interpreter.** No Python 3.12+ interpreter was installed on the development machine apart from the CPython 3.12.14 bundled with the local Codex desktop runtime. Phase 2 uses it as the base interpreter of the project environment; nothing was downloaded and nothing outside the repository was modified. Python 3.13 and 3.14 are verified in CI (Phase 9), or earlier if a local interpreter is provided.
- **Gates.** `scripts/check.sh`: Ruff check and format; `mypy --strict` over `src` and `tests`; pytest with branch coverage of at least 90 % overall and 100 % for `budget`, `selection`, `isolation`, `providers`, the outcome classification, the runner, and the imaging worker tasks (§20.4).

### D-143 — Provisional built-in vocabulary [§15.2, D-124]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

- Phase 2 ships the vocabulary *mechanism*: normalization, keys, labels, aliases, and the per-field lookup. The built-in vocabulary is empty (version `0-provisional`). Tests use synthetic vocabularies.
- Until Phase 3 fixes the real lists (Q-14), any static filter value other than `any` is therefore `config_invalid`.
- Within one option field every normalized key, label, and alias must map to exactly one key. A label shared by both museums (for example a "Photography" department at each) must therefore be made distinct in Phase 3, or the lookup made source-aware.

### D-144 — Image pipeline details [§11.1, D-121, D-122]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

- **Header pre-scan** (§11.1 step 2, §18.1 "header limits"). Before Pillow opens a source, the worker walks its header with a bounded standard-library scanner (`imaging/source_scan.py`), because Pillow loops over every marker segment or chunk without a limit, and the D-121 checks look only at the declared dimensions.
  - JPEG, from SOI to the first SOS: at most 1 024 markers, 16 MiB of header bytes, and 4 096 fill bytes. The markers 0xC8 and 0xF0–0xFD are refused, because Pillow reads them without a length and would lose sync with the scan.
  - PNG, from the signature to IEND (Pillow also parses the chunks after the image data): at most 1 024 non-image chunks totalling 16 MiB, and at most 65 536 image-data chunks (`IDAT`, `fdAT`, `fcTL`). Chunk types must be four ASCII letters, and unknown critical chunks are refused.
  - **Metadata TIFF structures.** Pillow also parses TIFF directories inside metadata, and copies every declared value. The scan therefore reads each block exactly as Pillow builds it, before Pillow opens the file:
    - the joined JPEG APP1 EXIF payloads and each APP2 MPF payload;
    - PNG `eXIf` chunks, `tEXt` chunks named `exif`, and "Raw profile type exif" text. That text is decoded within 1 MiB and never inflated without a bound.
  - It walks IFD0, the next-IFD chain, and the Exif, GPS, and Interop IFDs, with a visited set. Caps:
    - 512 entries per IFD, 16 IFDs per structure, and 4 structures per source;
    - 1 MiB of declared value bytes per structure. Pillow turns values into Python objects about 30 times their size; real EXIF fits one 64 KiB segment;
    - 64 images in an MPF index;
    - 1 MiB for one EXIF block, and 8 leading `Exif` headers. These two close two quadratic paths inside Pillow.
  - BigTIFF headers in metadata are refused as `decode`. Blocks whose header Pillow itself ignores are ignored.
  - *Trade-off:* counting *declared* sizes means that a damaged but decodable file with an absurd count in one entry, or a zero sub-IFD pointer, is refused as `limits`, where Pillow would skip the tag. MakerNote internals and SubIFDs are not walked, because the worker never asks Pillow to parse them; a future use of them must extend the walk first.
  - A cap violation gives `limits`; a malformed or truncated header gives `decode`. The parent's validator of `delivery.jpg` keeps its own, stricter rules.
- **MPO.** A JPEG with a multi-image MPF index opens in Pillow as format "MPO". It is accepted when JPEG is declared, and only frame 0 is used (§11.1 step 3).
- **EXIF.** Orientation comes from the metadata already parsed when the file is opened, so a PNG `eXIf` chunk placed after the image data is ignored. Malformed EXIF means orientation 1, never a failure.
- **Colour keys (`tRNS`).** Keys on 1-, 2-, and 4-bit images are applied on the decoded scale; 16-bit grey keys are matched on the 16-bit samples before scaling to 8 bits; 16-bit RGB keys, and keys out of range, are ignored, so the artwork stays opaque. Transparent areas composite over `background_color` after colour conversion (D-122).
- **Classification.** A truncated JPEG header is `decode`, not `format_mismatch`.
- **Strictness.** The pre-scan refuses anything the two parsers could frame differently, so Pillow can never parse past what the scan checked. For example, a JPEG with stray non-marker bytes between header segments is refused as `decode`, although Pillow alone would decode it. Encoders do not write such files.
- **Residual cost.** After the first SOS, libjpeg decodes a progressive JPEG's scans in C, and a file with a huge number of tiny scans costs CPU that the header scan does not bound. The 15 s preparation limit contains it from Phase 5 (R-27). Phase 5 measured the D-121 worst cases without `RLIMIT_AS`, but generated no JPEG with very many scans (R-09); the measurement under the real limit runs in Phase 6 (D-165).

### D-145 — Redaction scope and test guards [§18, §19, §20.1, H2, H3]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

- **Known secrets.** The Supervisor and TV tokens are registered with one process-wide redactor (installed by `configure_logging`). It also covers their percent-encoded and JSON-escaped forms. `sanitize_for_log` redacts with it *before* truncating, so a cut line can never show a fragment of a registered secret.
- **Credential patterns** (a backstop for secrets that were never registered):
  - after an authorization-type key (`Authorization`, `Proxy-Authorization`, `Cookie`, `Set-Cookie`), the whole rest of the value is redacted, and a standard scheme word (Bearer, Basic, Digest, Negotiate, Token) stays visible;
  - values of credential-named keys: `token`, `password`, `secret`, `auth`, `credentials`, `pwd`, `passphrase`, `session`, any `*_key` or `*-key`, and prefixed forms such as `access_token` or `client_secret`. Quoted values, including spaces, and `b`/`u` prefixes are covered;
  - JWT-shaped strings;
  - the same keys in header tuples (`('Authorization', '…')`), in JSON that is itself JSON-encoded, in camelCase (`accessToken`, `clientSecret`, `privateKey`), and behind percent-encoded separators (`token%3D…`).
  - SHA-256 digests and qualified identifiers stay visible, and a test checks that more than 1 000 lines in the runner's real formats pass unchanged. Consequently, `auth=…`, `session=…`, and `…_key=…` are always redacted in log text; no runner log line uses them for other values.
  - The runner logs fixed fields before untrusted text (for example the digest before the attribution in the `chosen:` line).
  - *Known limits of this heuristic layer* (R-28):
    - unregistered secrets in unusual forms can still pass: unquoted values with commas or spaces, URL user-info, and unusual encodings of a registered secret;
    - some ordinary phrases are over-redacted, for example "Bearer of Bad News".
    - The real secrets (the Supervisor and TV tokens) are registered values and are always redacted.
- **Network guard (H2).** Installed for the whole test session, collection included. It blocks `connect`, `connect_ex`, `sendto`, and `sendmsg` on `socket.socket`, `socket.create_connection`, and the five resolver functions on `socket` and `_socket`.
- **Boundary checks (D-107).** They also ban `_socket`, `_ssl`, `socketserver`, `select`, `selectors`, `ctypes`, `concurrent`, and `pty`, and process creation through `os`. They flag computed dynamic imports outside `isolation`, and allow constant dynamic imports of worker modules only in `isolation`. Self-tests prove that every detector fires. Phase 3 (`net.transport`) and Phase 5 (process isolation) must extend these rules deliberately.

## Phase 3 decisions

### D-146 — Documentation re-check at the start of Phase 3, and its consequences [§9.2, §9.5, §9.6, §15.2]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27). It was applied in Phase 3 under the user's Q-14 instruction: use no undocumented values, and leave out, with a documented limitation, any category that the official documentation does not map reliably. Q-25 is resolved with option (a): the capability changes stand for the first beta, and no live Art Institute observation is approved.

**Method.** On 2026-09-27 the two official documentation pages, `https://api.artic.edu/docs/` and `https://openaccess-api.clevelandart.org/`, were re-read in the in-app browser, and the text was extracted from the rendered pages. No API endpoint, image, or metadata URL was requested, and nothing was recorded from a live response.

**Art Institute of Chicago: documented.**

- *Search.* `GET /api/v1/artworks/search`, with Elasticsearch Query DSL in `query`. "For production use", the whole query travels as minified, URL-encoded JSON in `params`. The `is_public_domain` term query is the documented example.
- *Counting.* A documented example requests `…/artworks/search?query[term][is_public_domain]=true&limit=0`. Every paginated response carries `pagination.total`.
- *Pagination.* `page` (1-based) and `limit`. `limit` cannot exceed 100, and a single search query cannot return more than 10 000 records through any combination of `limit` and `page`.
- *Access.* Anonymous users are throttled to 60 requests per minute per IP. Scraping should stay at no more than one request per second. The `AIC-User-Agent` courtesy header carries "the name of your project and a contact email".
- *Artwork fields.* `id`, `title`, `artist_display`, `date_display`, `date_start` and `date_end` (numbers), `credit_line`, `is_public_domain`, and `image_id`. The fields `department_title`, `style_title`, `style_titles`, and `color` ("Dominant color of this artwork in HSL") exist. Every title-based field has a `.keyword` subfield for filters.
- *Images resource.* `GET /api/v1/images` accepts `ids` (comma-separated) and `fields`. Its `width` and `height` are the "Native width/height of the image".
- *IIIF.* `https://www.artic.edu/iiif/2/{identifier}/full/843,/0/default.jpg` is recommended. For public-domain images, `…/full/1686,/0/default.jpg` may be used, although 843 is still recommended "unless there's a clear need for 1686". The 4K canvas is that need (R-19).
- *Category terms.* Their `subtype` "takes one of the following values: classification, material, technique, style, subject, department, theme". The terms themselves are data behind the `category-terms` endpoints.

**Art Institute of Chicago: not documented.**

- The set of department values and the set of style values. They are API data (category terms), not documentation, and Phase 3 may not call the API.
- The names, ranges, and meaning of the members of the `color` object.
- Any member of the artwork's `thumbnail` object; its description refers only to IIIF conventions. The Phase 1 assumption (§9.5) that the thumbnail carries a documented width and height does not hold.
- Whether the IIIF server upscales a `1686,` request for an image narrower than 1686 px.

**Consequences for the Art Institute adapter** (amends D-132 and §9.5):

1. **Departments, styles, and colours are unsupported in the beta.** No `aic_…`, `style_…`, or `color_…` key is shipped, and the capability matrix lists only the period filter for the Art Institute. Because no such key exists, a configured Art Institute department, style, or colour value is rejected as invalid (B5), and a helper value falls back to the static value. A valid key that the Art Institute does not support, such as a Cleveland department, is ignored and reported (B8). Q-25 is resolved with option (a): the first beta keeps these filters unsupported, and no live observation is approved. Adding them later needs a new decision and explicit approval.
2. **Dimensions come from the documented Images resource.** After each search page, one batched request, `GET /api/v1/images?ids=<the page's image ids>&fields=id,width,height`, reads the native sizes. It counts as a metadata request.
   - The artwork's `image_id` is taken as the image record's `id`, because the documentation uses that identifier for the image in both places. The worker's check of the real dimensions (§8.2) remains the safety net.
   - A record without a matching image record is offered without dimensions and skipped as `dims_unavailable`, since the adapter has no probe.
3. **Rendition.** `full/1686,/0/default.jpg`, only for images at least 1686 px wide; narrower images are skipped. The rendition measures `1686 × round(1686 · h / w)`.
4. **Search shape.** One count request (`limit=0`), then pages of 50 records sampled without replacement from the first `min(total, 10 000)` results. Each page costs two metadata requests (search and images). A typical run therefore needs 3 requests; the allowance of 15 is never exceeded.
5. **Period filter.** An Elasticsearch `range` on the documented numeric `date_start`, which is also checked on every record.

**Cleveland Museum of Art: documented (checked verbatim).**

- *Parameters of `GET /api/artworks/`.*
  - `cc0` takes no value: "Filters by works that have share license cc0".
  - `has_image` is 0 or 1 and returns only works with a web image asset.
  - `department`: the valid values are in Appendix B.
  - `skip`, `limit`, and `fields`. Without a `limit`, the API returns its maximum of 1000 records.
  - The advanced filters `created_after` and `created_before` take integer years; negative years are BCE.
- *Response.* `info.total`, and per record:
  - `id` ("ID in AthenaCCMS");
  - `share_license_status` ("CC0", "Copyrighted", or "Other");
  - `creation_date` (a string), `creation_date_earliest`, and `creation_date_latest`;
  - `creators` (with `description`), `department`, `url`, and `images`.
- *Images.* `images.print` is "3400px at longest side, 300 dpi, jpeg format". The documentation's example gives its `url`, `filename`, `filesize`, `width`, and `height`, all as strings, on `openaccess-cdn.clevelandart.org`. The original TIFF is `images.full`.
- *Rights.* Only works with the CC0 status "additionally provide access to CC0 images".
- *Departments.* Appendix B lists 21, verbatim: African Art; American Painting and Sculpture; Art of the Americas; Chinese Art; Contemporary Art; Decorative Art and Design; Drawings; Egyptian and Ancient Near Eastern Art; European Painting and Sculpture; Greek and Roman Art; Indian and South East Asian Art; Islamic Art; Japanese Art; Korean Art; Medieval Art; Modern European Painting and Sculpture; Oceania; Performing Arts, Music, & Film; Photography; Prints; Textiles.
- *Release history.* The newest entry is version 4.0.3 (2026-07-09).
- *Rate limits.* None is documented.

**Cleveland: not documented.**

- Whether `created_after` and `created_before` are inclusive, and which date field they compare.
- How a `department` value that contains commas is parsed.

**Consequences for the Cleveland adapter** (amends D-136 and §9.6):

1. Every request sets `limit` explicitly: 1 for the count, at most 25 for a page.
2. "Performing Arts, Music, & Film" is not offered.
3. Each period bound is widened by one year on the server side, so either reading of inclusivity is covered. The exact range is then enforced on the documented `creation_date_earliest`.

**Periods, for both museums.** Five project-defined ranges of the earliest creation year: before 1400; 1400–1599; 1600–1799; 1800–1899; and 1900 and later. They are ranges, labelled with years, not styles.

### D-147 — Gateway implementation details [§7.4, §10, D-108, D-115, D-131]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27).

**Module layout.**

- `net/wire.py`: the seam (`WireRequest`, `WireResponse`, `Transport`, `Resolver`, `TransportFailure`).
- `net/policy.py`: host policies, URL and address validation, and header parsing; pure.
- `net/identity.py`: the User-Agent and courtesy header (D-119 as amended).
- `net/gateway.py`: the gateway and one `ProviderChannel` per provider and run.
- `net/transport.py`: the only module that imports `socket`, `ssl`, `http.client`, `urllib3`, and `certifi`. Only the entry point (Phase 6) may import it. `net` modules may import `urllib.parse`; every other `urllib` module stays banned. The boundary test enforces all of this, and a fresh interpreter checks that importing the rest of the package loads no network library.

**Refinements of D-108 and D-115.**

1. **Hosts.** Exact host names only; no suffix rules are needed for the beta. IP-literal hosts, user information, any port but 443, fragments, non-ASCII, and backslashes are refused.
2. **Addresses.** Every resolved address must be public. IPv4-mapped IPv6 addresses are judged by their IPv4 address. 6to4, Teredo, and NAT64 forms are refused, because Python classifies them as not globally reachable. Scoped addresses are refused. Up to 4 addresses are tried in resolver order.
3. **Pacing** is measured from the start of one request to the start of the next. Redirect hops and retries are paced like new requests.
4. **Metadata allowance.** Every wire request (a redirect hop or a retry too) takes one of the 15 metadata requests. When the allowance is spent, the channel raises `AllowanceExhausted`. Selection ends the pass with the new end `metadata_allowance`, which counts as "search limits reached" (`no_match` hint), not as a failure.
5. **Stops.** 401 and 403 stop the provider for the run, for every provider. D-115 names 403 and D-136 adds 401 for Cleveland; applying 401 everywhere is stricter. A 429 without a permitted retry stops too, including a second 429 and a retry that does not fit the deadline or the allowance.
6. **Retry.** At most one, for metadata only: after a failed connect or name resolution, a 502/503/504, or a 429 whose `Retry-After` is at most 5 s. The wait is `max(Retry-After, 1 s)` plus up to 0.25 s of jitter from the injected random source. The retry is skipped unless the caller's deadline still has room for the wait plus one connect timeout. A refused non-public address is never retried.
7. **`Retry-After`** accepts delta-seconds and the IMF-fixdate form of HTTP-date. The obsolete date forms are treated as invalid, which means a stop. `email.utils` is not used, because importing it loads `socket` into the parent.
8. **Time.** Each attempt has its own total (metadata 10 s, image 20 s), clamped to the caller's deadline. If the caller's deadline ran out, the result is `DeadlineExceeded`; if only the request's own limit did, it is `SourceError(TIMEOUT)` (D-141 item 2). The transport enforces the exchange total with a timer that shuts the socket down, so a peer that sends headers or body one byte at a time is bounded too. Body reads use `read1`, at most one socket read per call, with the socket timeout re-clamped before each read.
9. **Bodies.** A declared `Content-Length` over the cap, a body over the cap, or a gzip body that decodes past the cap is `OVER_CAP`. A body shorter than declared is `TRANSPORT`. A truncated, invalid, multi-member, or trailing-data gzip body is `UNEXPECTED_FORMAT`. Only metadata may be gzip. JSON is parsed with the standard library; NaN and Infinity are refused, as is nesting deeper than the interpreter's recursion limit.
10. **404 and 410** from a metadata request are `HTTP_ERROR` (D-141 item 3); from an image download they are `NOT_FOUND`.
11. **Downloads** go to a new file (`O_EXCL`, `O_NOFOLLOW`, mode 0600). A partial file is removed on any failure.
12. **TLS.** A fresh context per connection, trusting only the pinned `certifi` bundle (never the system or environment stores), with `CERT_REQUIRED`, host-name checking, and TLS 1.2 or newer. The connection goes to the validated IP, with SNI and the certificate check on the host name. After the handshake, the negotiated socket's version, verification mode, host-name check, and server name are checked again, and `getpeername()` must equal the validated address before anything is sent. urllib3's own host-name matching (`assert_hostname`) is not used, so Python's check stays on.
13. **Requests** send `Host`, `User-Agent`, `Accept`, `Accept-Encoding`, `Connection: close`, and any courtesy headers. There are no cookies, proxies, pools, retries, or redirects inside urllib3.
14. **Name resolution** runs in a daemon thread that the caller stops waiting for after 3 s (clamped). A lookup that hangs leaves one idle thread behind until the process exits.
15. **No probe path.** No beta source needs a remote dimension probe (§8.3). The 256 KiB probe cap is therefore not implemented yet; the probe allowance stays enforced in selection.
16. **Logs.** Each request is logged at DEBUG with the kind, the host, the path without its query, the status, the byte count, and the duration. A stop is logged at WARNING. Header values, queries, and bodies are never logged.

**Amendment after the internal review of `51d9cf3`** (see *Review records*):

- Item 2: IPv6 site-local addresses (`fec0::/10`) are refused too.
- Item 8, the time bounds. The transport captures the socket right after the connect and uses it for the exchange timer and the per-read timeouts. A response with `Connection: close` makes http.client drop the connection's own reference while the body is still read from it; before this fix, the timer and the re-clamped reads then did nothing. After the connect, the connection's timeout becomes the exchange time, because urllib3 resets the socket timeout to the connection's timeout before sending and before reading the headers. Before this fix, headers and body gaps were bounded by the connect timeout. Once a body is complete, http.client closes the socket, so re-clamping its timeout is skipped. Tests over a local socket pair with the real http.client and urllib3 stack cover a dripping peer, slow headers, slow and stalled bodies, and four body framings.
- Item 16: the `urllib3` logger is silenced completely (`logs/setup.py`). Its warnings quote the full request URL, query included, and unparsed response header data.
- The boundary test lists imports with their members, so `from http import server` in `net/transport.py` is caught like `import http.server`.

**Amendment after the internal review of `f614256` and `8761cca`:** item 4's end is renamed `provider_allowance`. It now covers any allowance of the provider's own: the gateway's metadata requests, and the local library's directory entries (D-149).

### D-148 — Helper reader details [§15.3, D-112; B3–B5]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27).

- **Module.** `ha/client.py`, `SupervisorHelperReader`, implements the `HelperReader` port. It shares the `net.wire` seam, so the real transport serves both the gateway and the reader. It does not go through the gateway, whose rules (HTTPS, public addresses, pacing) do not fit the Supervisor.
- **Request.** `GET http://supervisor/core/api/states/<entity_id>` with `Authorization: Bearer <token>`, `Accept: application/json`, `Accept-Encoding: identity`, `Connection: close`, and `User-Agent: FrameGallery/<version>`. The Supervisor is local, so the User-Agent carries no contact. The entity ID is re-validated with the options pattern (now the public `config.options.HELPER_ENTITY_ID`) and percent-encoded.
- **Where the token may go.** The name `supervisor` is resolved once per run, and every address must be private: not public, loopback, link-local, multicast, reserved, or unspecified. Otherwise nothing is sent. This keeps the token inside the Supervisor's internal network even if name resolution is wrong. Only the first address is used.
- **Bounds.** One request per configured helper (at most four), no redirect (any 3xx fails), and no retry. Each read takes at most 3 s, clamped to the configuration deadline; a read that no longer fits is skipped. The body is at most 64 KiB, `identity` encoding, and JSON. Only `state` is used: a string of at most 255 characters.
- **Failures.** Any failure gives `None` for that helper. The merge then falls back to the static value with exactly one WARNING (B4, B5). The reader logs its own reasons at INFO (no usable token; the Supervisor cannot be reached) and DEBUG (per helper), and never logs the token or a helper's value. Its `repr` hides the token. `unavailable` and `unknown` are returned as they are (B4). Only `Cancelled` propagates.
- **Token.** The entry point (Phase 6) passes the token from the reduced environment and registers it with the redactor (D-145). An empty or non-printable token means no read at all.

**Amendment after the internal review of `f614256`.** A private address alone was not enough: any RFC 1918 LAN address, or a 6to4 or Teredo address embedding a public IPv4 address, would have received the token. Now:

- the reader takes the container's own networks (`NetworkInfo.container_networks()`, which include the Supervisor's internal network);
- every resolved address must be private **and** inside one of those networks, with IPv4 and IPv6 never mixed;
- without known networks, nothing is sent;
- `is_private_address` refuses 6to4, Teredo, and NAT64 forms.

### D-149 — Local media provider details [§8.3, §9.3, D-118; F7]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27).

- **Modules.** `providers/local_media.py` holds `LocalMediaProvider` and `LocalInspectionProbe`. `app/fetching.py` holds `SourceFetcher`, the production image fetcher. Beyond D-141's dependency list, `providers.local_media` uses `imaging.contract`, `isolation.executor`, and `logs.summary`, and `app.fetching` uses `net` and `providers`.
- **Library.** The library is created at the start of discovery (mode 0755, parents included). A library that is a symbolic link, is not a folder, or cannot be created gives one WARNING and no candidate.
- **Scan bounds.**
  - The library itself is level 0, and folders up to 4 levels below it are listed. A deeper folder is skipped as `too_deep`.
  - The 20 000-entry limit counts every listed entry, hidden and skipped ones included, and ends the scan (`entry_limit`).
  - Hidden entries are skipped silently.
  - Symbolic links, special files, unsupported extensions, empty files, files over 40 MiB, unreadable entries, and recent previews are counted by reason.
- **The aggregated WARNING** is emitted once, when discovery ends: when the pass is exhausted, or when selection stops pulling and the generator is closed. It also counts the files that failed inspection. At most 5 example paths are shown, relative to the library, sanitized, and cut to 80 characters.
- **Fingerprint (D-118).** The size is encoded as 8 bytes, big-endian. For a file under 64 KiB, "first" and "last" 64 KiB are both the whole file. `fingerprint_bytes` computes the same value from bytes, so Phase 4 can store the D-118 fingerprints of published previews in `current.json` for guard 3. Identical files share one identifier, and selection counts the repeat as a duplicate (D-141 item 7).
- **Preview guards (F7).**
  - Guard 2 is a construction check: the library may not be or contain the preview folder, otherwise `ValueError`. The production folders are siblings.
  - Guard 1 skips a folder whose real path is the preview folder's.
  - Guard 3 skips the fingerprints that the wiring passes in.
- **Attribution.** Only the title: the file name without its extension, at most 100 characters.
- **Dimensions.** A new `inspect` worker task reads one file's header. It opens, pre-scans, identifies, and limit-checks the file exactly like `prepare` does before decoding, then reads the EXIF orientation; no pixels are decoded.
  - Each inspection may take at most 2 s (`LOCAL_INSPECTION_S`), clamped to the discovery deadline.
  - An unreadable image gives `None`, counted as `unreadable` (the D-141 contract).
  - A worker failure raises `SourceError(UNEXPECTED_FORMAT)`, which selection counts as an inspection failure, never a transport failure.
  - *Deviation from §8.3:* one file per task instead of batches of up to 50. Batching only pays off with the process executor, so it is deferred to Phase 5. *Phase 5 note:* the process executor keeps one worker per inspection (45 ms each on the development host); batching is not implemented. *Phase 5 gate (user decision, 2026-10-02):* batching is implemented in Phase 6, with read-only descriptors that the parent opened, where possible (see *Phase 5 gate decisions*).
- **Delivery.** The fetcher copies only a file that this scan offered. The file must still be a regular file with the scanned size and fingerprint, and it is copied in 1 MiB steps, with deadline checks, into a new 0600 file. Any change since the scan is `NOT_FOUND`: the next candidate is tried, and it is not a transport failure. Remote references go to the channel whose host policy owns the URL, so downloads share that provider's pacing and 403/429 stop.
- **Empty library.** When the local scan finishes without offering a candidate, the `no_match` hint is "no usable JPEG or PNG images in /media/frame_gallery/library" (new `Hint.LIBRARY_EMPTY`), as §9.3 requires.

**Amendment after the internal review of `8761cca`:**

- **Pinned identities (a symlink race).** A path-based open protects only the last component, so a subfolder swapped for a symbolic link during the run could have led outside the library. Now:
  - each folder is opened with `O_DIRECTORY | O_NOFOLLOW` and listed through its own descriptor;
  - every folder and file is recorded by device and inode as the listing saw it;
  - a folder, when listed, and a file, when offered, copied, or inspected, must still have that identity. The worker's `inspect` task checks the device and inode it is given.
  - A mismatch, or a folder that is now a link or a file, is skipped as the new reason `changed`, or refused as `NOT_FOUND` when copying.
  - Guard 1 now compares identities instead of real paths.
- **Read errors while copying** (`fstat` or `pread` on the library file) are `NOT_FOUND`, so the next candidate is tried. Before, they ended the run as `internal_error`.
- **An inspection cut off by the discovery deadline** raises `DeadlineExceeded` and is not counted as a failed inspection of a healthy file (D-141 item 2).
- **Entry limit.** A scan cut short by the 20 000-entry limit ends by raising `AllowanceExhausted` once its files are offered. The hint is then "search limits reached", not "no usable images". A library larger than the limit is only partly scanned, and it is the same part each run.

### D-150 — Art Institute adapter details [§9.5, D-132, D-146]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27).

- **Modules.** `providers/aic.py`, plus helpers shared with Cleveland:
  - `providers/jsonread.py`: defensive readers for untrusted JSON;
  - `providers/periods.py`: the five period ranges;
  - `providers/cache.py`: the metadata cache port and an in-memory implementation.
- **Query form.** The whole search request travels as minified JSON in `params` (the documented "entire query" form for production use): the Elasticsearch `query`, `fields` as an array, `limit`, and `page`.
  - The query is a `bool` filter: the term `is_public_domain: true`, `exists: image_id`, and, for a period, a `range` on `date_start`.
  - Whether the server honours `fields`, `limit`, and `page` inside `params` exactly as it does as separate parameters is checked in the first approved live observation (Phase 8). Every record is validated either way.
- **Count and pages.**
  - The count request uses `limit` 0 and reads `pagination.total`.
  - Pages hold 50 records. The page numbers `1..ceil(min(total, 10 000) / 50)` are shuffled with the injected random source, so no page is fetched twice in a run.
  - Per run: 1 count, then 2 requests per page (search and sizes). At most 7 pages fit the 15-request allowance, and when it is spent the pass ends as a search limit (D-147 item 4).
- **Sizes.** The Images resource is read with `ids`, `fields=id,width,height`, and an explicit `limit` equal to the number of IDs, because the documented default page size is 12. Repeated image IDs are looked up once. A width and height must be positive and at most 100 000; digit strings are accepted.
  - An image narrower than 1686 px is not offered.
  - A work whose image record is missing is offered without dimensions, and selection counts it as `dims_unavailable`.
- **Record checks.**
  - `id` must be a positive integer of at most 10^10; booleans and strings are refused.
  - `is_public_domain` must be exactly `true`.
  - `image_id` must be a lowercase UUID (the form of the documentation's examples).
  - With a period filter, `date_start` must be an integer year within the range.
  - A record that fails any check is skipped silently; a page summary is logged at DEBUG.
- **Attribution.** Title, artist, date text, and credit line, each cleaned: control and format characters become spaces, whitespace collapses, and the text is cut to 300 characters. No detail URL is stored, because the documentation defines none for artworks.
- **Rendition.** `https://www.artic.edu/iiif/2/<image_id>/full/1686,/0/default.jpg`, built only for works this run offered; the image ID is re-validated and percent-encoded. The size is `1686 × round(1686 · h / w)`, at least 1 px high.
- **Cache.** The count per filter signature (`aic:count:<period key or "any">`) is kept for 1 day through the `MetadataCache` port. Phase 3 uses the in-memory implementation; the bounded, persistent cache is Phase 4 (§13.4). *Deferred to Phase 4:* the exhausted-page hints (§9.5), because they need the exclusion set, which the adapter does not see.
- **Errors.** A structurally malformed response (not an object, a missing list, a total that is not a count) is `UNEXPECTED_FORMAT`. HTTP errors, stops, and time limits come from the gateway (D-147).

### D-151 — Cleveland adapter details [§9.6, D-136, D-146]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27).

- **Module.** `providers/cma.py`. It uses the shared helpers of D-150. `net.policy.https_url` now accepts valueless flags, so `cc0` is sent bare, as the documentation writes it.
- **Every request** starts `?cc0&has_image=1` and sets `limit` explicitly: 1 for the count, 25 for a page.
  - The count request asks only for `fields=id` and reads `info.total`.
  - A page request sends `skip`, `limit=25`, and the D-136 field list, with `creation_date_earliest` added.
- **Random pages.** Page offsets are multiples of 25. Up to 4 096 pages, the page order is a shuffled list. Beyond that, pages are drawn lazily without repeats; 64 repeated draws in a row end the pass. Per run: 1 count and at most 14 pages (the 15-request allowance).
- **Departments.** The vocabulary key maps to the exact documented value, which is sent URL-encoded. Every record's `department` must equal it. The curated list:
  - American Painting and Sculpture;
  - European Painting and Sculpture;
  - Modern European Painting and Sculpture;
  - Drawings; Prints; Photography;
  - Chinese Art; Japanese Art; Korean Art;
  - Indian and South East Asian Art; Islamic Art;
  - Textiles.

  These are the documented departments that hold two-dimensional works suited to a wall display. The other documented departments are mostly objects: African Art, Art of the Americas, Contemporary Art, Decorative Art and Design, Egyptian and Ancient Near Eastern Art, Greek and Roman Art, Medieval Art, and Oceania. "Performing Arts, Music, & Film" is left out as undocumented to parse (D-146). All 21 documented values are kept verbatim in the module, and a test checks that the curated values are a subset.
- **Period.** `created_after = first − 1` and `created_before = last + 1`, sent only for the bounds a period has. The exact range is enforced on `creation_date_earliest`, an integer year.
- **Record checks.**
  - `id` must be a positive integer.
  - `share_license_status` must be exactly `"CC0"`.
  - `images.print` must be an object whose `url` is an `https` URL on `openaccess-cdn.clevelandart.org` (port 443). The path must end in `.jpg` (any case) and contain only letters, digits, `.`, `_`, `-`, and `/`, with no empty, `.`, or `..` segments, and there may be no query.
  - A print that fails the URL check is counted, and the pass ends with one WARNING giving the count. Other failures are skipped silently.
  - `images.full` (the TIFF) is never read.
- **Dimensions** are the print's `width` and `height`: integers or digit strings, positive, at most 100 000. If either is missing or invalid, the work is offered without dimensions.
- **Attribution.**
  - Title and creation date, cleaned (D-150).
  - The first creator's documented `description`.
  - The documented `url` as the detail link, but only in the form `https://(www.)clevelandart.org/art/<accession>`.
  - No CMA trademarks are used.
- **Cache.** The count per filter signature (`cma:count:<department>:<period>`) is kept for 1 day (D-150).
- **Stops.** 401 and 403 stop the provider for the run (D-136, D-147 item 5).

### D-152 — Vocabulary version 1, the narrowed capability matrix, and the contract suite [§9.1, §9.2, §15.2, §20.1, Q-14]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27).

- **Vocabulary version 1** (Q-14, resolved) is built only from documented values (D-146):
  - *Departments:* the 12 curated Cleveland departments (D-151). Each label is `"<documented value> (Cleveland)"` and names the museum, so labels stay distinct between museums (D-143). The documented value itself is an alias.
  - *Periods:* five periods labelled with years, each with plain aliases such as `1800-1899` and `19th century`. They share their keys with `providers.periods.PERIOD_RANGES`.
  - *Excluded:* no Art Institute department, no style, and no colour (Q-25, resolved with option (a)).
  - Tests check normalization, aliases, uniqueness within each field, that no term is reserved, that no label repeats, and that the entries match the adapters' mappings.
  - `frame_gallery/VOCABULARY.md` documents the whole mapping and the capability matrix. A test parses it and requires it to match the code.
- **Capability matrix.** The Art Institute now supports only the period (D-146, amending D-124). The Phase 2 tests that used Art Institute departments as examples now use Cleveland departments. B2 and C1 therefore hold for the filters a source supports: Cleveland combines department and period; the Art Institute applies the period.
  - A valid key that the selected source does not support, such as a Cleveland department with the Art Institute or a period with local media, is ignored and reported (B8).
  - A value that matches no key, label, or alias of version 1, and is not a no-filter term (any style, any colour other than a no-filter value such as "any", an Art Institute department), is rejected as invalid (B5). As a helper value, it falls back to the static value with a warning.
  - In the first beta, no source offers a colour filter (Q-25, option (a)).
- **`dims_in_metadata`** now means "the documented metadata gives the rendition's size, so no probe is bound". A candidate whose metadata lacks the size carries `None`, and selection counts it as `dims_unavailable`.
- **Contract suite** (`tests/unit/providers/test_contract_suite.py`). Every adapter, over its own synthesized fixture, is checked for:
  - consistent source and key;
  - agreement with `CAPABILITY_MATRIX`: a supported filter changes the requests and narrows the result, and an unsupported one changes nothing;
  - rights bases within `ALLOWED_RIGHTS`;
  - laziness;
  - policy hosts only, for requests and renditions;
  - discovery 404 and 410 → `HTTP_ERROR`, including the Art Institute's size lookup; rendition 404 and 410 → `NOT_FOUND`;
  - (local media) `None` from inspecting an unreadable file (D-141).
- **End-to-end tests** (`tests/integration/test_museum_pipeline.py`) run the runner with the real adapters, gateway, and fetcher over the synthesized APIs:
  - a Cleveland run with department and period combined delivers a CC0 print JPEG, and never requests the TIFF (C1, C10);
  - an Art Institute run with a period delivers the 1686 px IIIF rendition, sends the courtesy header, and reports the unsupported department in the summary line (B8).
- **Fixtures.** The API documents are synthesized in `tests/support/museums.py`: independently authored, with invented values and envelopes that follow the re-read documentation. Nothing was recorded from a live API (§20.3).
- **Layout additions** (beyond §21 and D-141): `net/` (`wire`, `policy`, `identity`, `gateway`, `transport`), `ha/client.py`, `app/fetching.py`, and `providers/` (`aic`, `cma`, `local_media`, `jsonread`, `periods`, `cache`).

## Phase 4 decisions (accepted)

These record how Phase 4 realizes §13 and §14, and every place where it deviates from the text of `ARCHITECTURE.md`. The user accepted them at the Phase 4 gate on 2026-09-27, and `ARCHITECTURE.md` is amended to match.

### D-153 — The atomic primitive, the reader, and history [§13.2, §13.3, D-110]

Status: **accepted** (Phase 4 gate, user decision, 2026-09-27).

- **Modules.** `store/atomic.py` (the primitive, the reader, and the quarantine), `store/fields.py` (timestamps and identifiers), and `store/history.py`. The rule for qualified identifiers moves from `providers.contract` to `domain.py`, which `providers.contract` now imports, so that the store never imports a provider module (§5).
- **Directories.** The anchor's last component and every part below it are opened with `O_DIRECTORY | O_NOFOLLOW`; a symbolic link or a file in their place is refused. Missing parts are created with exactly the requested mode, whatever the umask (0700 below `/data`). Every file operation is relative to the directory descriptor.
- **Writes.**
  - JSON is compact and ASCII-only, so lone surrogates in untrusted text are escaped rather than failing. NaN and Infinity are refused.
  - The self-check (step 2) requires the bytes to parse back to an equal value **and** to pass the reader's own envelope and schema checks. A document that this code could not read back is never written.
  - The temporary file is `<name>.tmp-<16 hex digits>`. Its mode is set exactly with `fchmod`, so the umask cannot change it: 0600 for state, 0644 for the preview.
  - `.bak` is refreshed only from a primary that was valid when it was read, or that this process wrote. A damaged primary therefore never replaces a good backup.
  - A failed directory `fsync` after a successful rename is reported with `replaced = true`: the new content is in place, but its durability is uncertain. The callers decide what that means (D-154).
- **Reader.**
  - A file is *damaged* when it is not JSON; not an object of the expected `format`; has no integer `version`, or an older or unknown one; fails the schema; is not a regular file (a symbolic link is moved aside without being followed); or exceeds its size bound. Damaged files are quarantined.
  - A *newer* version, or a file that exists but cannot be read (`EACCES`, `EIO`), is reported and not quarantined. History and the ledger then end the run with `state_error` before the television is touched (D-154). Falling back to `.bak` or to an empty state in that case could lose exclusions and resend a work.
  - Both copies missing is a first run: an empty result without a warning.
- **Quarantine.** `state/quarantine/<UTC time>-<random>-<name>`. After each move, the oldest entries beyond three are removed; a damaged entry that is a directory is removed as a tree.
- **Schema strictness.** One invalid entry makes the whole document damaged, so the reader falls back to `.bak`. Unknown fields are ignored and are not written back. A repeated identifier keeps its last position.
- **History bounds.** 20 000 entries and 5 MiB; the oldest entries go first, and the new entry is always kept. Identifiers are at most 200 ASCII characters and timestamps have a fixed length, so 20 000 entries take at most about 4.64 MiB: the entry bound is the one that binds (a test checks this).
- **Known limitation: very old works can come back** (accepted for the first beta at the Phase 4 gate; R-29). History keeps the latest 20 000 delivered works. When a new delivery would exceed that, the oldest entry is dropped. The ledger has already let go of that work, so it is no longer excluded, and it could in theory be chosen and shown again. At one artwork a day, the first entry is dropped after about 55 years; at one an hour, after about 2.3 years; at one every 15 minutes, after about 7 months. Nothing else is affected: every more recent work stays excluded.

**Amendment after the internal review of `a74ba1c`, `1677ccd`, and `f347ffb`** (see *Review records*):

- **Timestamps** must lie from 2000 to 8999 (UTC). Dates at the limits of `datetime` raised `OverflowError` when a quarantine period or a time to live was added, and ended every run as `internal_error`. They are now damage, and the reader also treats an arithmetic error in a schema check as damage.
- **Numbers** too large for a finite float (for example `1e400`) are refused like NaN and Infinity.
- **A newer version over the size bound** is recognised by its first 256 bytes, which every version writes as `{"format": …, "version": …`, and is reported as newer instead of being quarantined. Later versions must keep writing these two fields first.
- **The sweep pattern** now matches the `.bak` temporary files of names up to the 100 characters that `check_name` allows.

### D-154 — The upload ledger and the file state store [§13.3, §13.6, D-137]

Status: **accepted** (Phase 4 gate, user decision, 2026-09-27).

- **Modules.** `store/upload_ledger.py` (the document and its pure transitions) and `store/state.py` (`FileStateStore`, the `StateStore` port). `store.state` uses `selection.exclusion` for the `ExclusionSet` value type. This is an internal dependency beyond §5's "stdlib" column, recorded as D-141 does. There is no cycle: `selection` does not import `store`.
- **Lock.** `/data/state/.lock`, opened with `O_NOFOLLOW` and mode 0600, then `flock(LOCK_EX | LOCK_NB)`. `EWOULDBLOCK` gives `already_running`; any other failure gives `state_error`. The startup sweep runs only once the lock is held; a failing sweep only logs a warning.
- **Loading.** History and the ledger are read once per run, in SELECT (`load_exclusions`). A newer version or an unreadable file ends the run with `state_error` before the television is contacted (D-153).
- **Intent durability.** `commit_upload_intent` raises `StateError` on any failure, **including a failed directory `fsync` after the rename**. The run then ends with `state_error`, and the runner removes the intent, which the file may already hold. The television is therefore never contacted without a durable intent.
- **Promotion.** A failed promotion raises `StateError`. The runner logs an ERROR and keeps the outcome (§13.6 step 4). If only the `fsync` failed, the file already says `uploaded`: stricter than required, never weaker.
- **Recording history.** A failed rename raises `StateError`, which gives `delivered_unrecorded`. A failed directory `fsync` after the rename only logs a WARNING: the history is in place, and the ledger's `uploaded` entry excludes the work anyway.
- **Memory mirrors the files.** After a failure before the rename, the previous entries stay. After a failure only in the `fsync`, the new entries are kept, because the file holds them.
- **Pruning.** Only the intent write prunes. It drops intents whose quarantine has ended, and works that **both** copies of history hold, the primary and its `.bak`. `.bak` is one generation old, so a delivered work keeps its `uploaded` entry until a damaged primary can no longer lose its exclusion (amended after the internal review, see below).
- **Transitions.**
  - An intent never turns an `uploaded` entry back into `uncertain`.
  - A removal only ever removes an `uncertain` entry.
  - A promotion replaces the intent, or adds an `uploaded` entry if the intent is missing.
  - A repeated identifier in a file keeps its strongest entry: `uploaded` over `uncertain`, then the later time.
- **Bounds.** 20 000 entries and 5 MiB. The oldest `uploaded` entries are dropped first, then the oldest `uncertain` ones. The entry being written is never dropped. Entries normally leave the ledger long before, once history holds their work; only 20 000 uploads that never reached history (for example, repeated refusals of selection) could reach the bound. A dropped `uploaded` entry would no longer exclude its work (R-29).
- **Quarantine period.** An `uncertain` entry excludes its work until exactly 30 days after `at`. An `at` in the future (a clock that went back) keeps the quarantine until then, so it is never shortened.
- **Leftovers.** `close` discards a pre-staged history file that was never recorded. The startup sweep removes any that a killed run left behind (D-155).

### D-155 — Workspace, startup sweep, and store layout [§13.1, §14]

Status: **accepted** (Phase 4 gate, user decision, 2026-09-27).

- **Modules.** `store/workspace.py` (`RunWorkspace`, the `Workspace` port), `store/sweep.py` (`StartupSweep`), and `store/layout.py` (`StoreLayout`: the anchors `/data`, `/media`, and `/tmp`, and the store ports built from them for the Phase 6 entry point).
- **Moved types.** `WorkspacePaths` moves from `app.ports` to `domain.py`, and `PublishError` from `app.ports` to `errors.py`. The store can then implement the runner's ports without importing `app` (§5).
- **Workspace.**
  - `/tmp/frame-gallery` must belong to the process's user and is narrowed to mode 0700. `run-<16 hex digits>` and its `in/` and `out/` are created with mode 0700, once per run, in ATTEMPT.
  - Removal is a descriptor-relative `rmtree` that never follows a symbolic link. A failure only logs a warning.
  - Phase 5 sets the modes that the unprivileged worker needs (§11.3).
- **Sweep.**
  - It runs in CONFIGURE, after the lock is taken, so a run that loses the lock sweeps nothing.
  - It removes regular files named `<name>.tmp-<16 hex digits>` or `<name>.bak.tmp-<16 hex digits>` in `/data/state`, `/data/cache`, `/data/tv`, and `/media/frame_gallery/preview`, and directories named `run-<16 hex digits>` in `/tmp/frame-gallery`.
  - Only exact names of the right kind are touched; symbolic links and other kinds are left alone.
  - At most 1 000 entries are scanned per directory. A missing directory is skipped, errors only log a warning, and the number removed is logged at INFO.
  - The quarantine directory is not swept; it has its own bound (D-153).
- **Amendment after the internal review:** a run directory whose `in/` or `out/` could not be created is removed at once, so `create` never leaves a half-made directory for the next sweep.

### D-156 — The bounded metadata cache [§13.4, D-150, D-151; F6]

Status: **accepted** (Phase 4 gate, user decision, 2026-09-27).

- **Modules.** `store/cache.py` holds `FileMetadataCache`, the value type `ExhaustedPages`, and its merge rule. The port in `providers/cache.py` gains exhausted-page hints (`get_exhausted`, `add_exhausted`, and `HINT_TTL` of 7 days) and imports the value type from `store.cache`, as §5 lists (`providers` depends on `store.cache`). The in-memory cache implements the same port for tests.
- **File.** `/data/cache/<provider>.json` (mode 0600; directory 0700) with `format`, `version`, `provider`, and a list of entries. Each entry has `key`, `expires`, `used`, and either `count` or `total` and `pages`. Keys must start with the provider's own key.
- **Bounds.**
  - 1 000 entries and 2 MiB per file; 8 KiB per entry (an entry that would exceed it is not kept); at most 800 page numbers per hint, the lowest kept.
  - A time to live is clamped to 7 days. On reading, an entry that would expire more than 7 days ahead (a clock that went back) is cut to 7 days from now. Dropping it instead would have discarded every full-length hint after a clock step back of a few seconds; the end-to-end test in D-159 found this.
  - Expired entries go first, then the least recently used (by last use, then key).
- **Recency.** Every hit updates `used`, so a run with a cache hit writes the file. That is still at most one write per run.
- **Hints.** A hint belongs to the result count it was computed for; hints for another count replace it, because the pages may have shifted. An entry keeps its first expiry when pages are added, so no hint is older than 7 days.
- **Damage.** Any structural problem (not JSON, another format or provider, an invalid entry, too many entries, oversize) discards the whole file with a WARNING, and the next write replaces it. There is no quarantine and no `.bak`: the cache is excluded from backups and can always be rebuilt. A file of a newer version is discarded and later overwritten too.
- **Writes.** Once per run, through `flush(deadline)`. With no time left, the write is skipped (INFO); a failure only logs a warning. A cache directory that is a symbolic link is never read or written.

### D-157 — Exhausted-page hints and the cache write [§9.5, §9.6, §13.4, R-13; amends D-150]

Status: **accepted** (Phase 4 gate, user decision, 2026-09-27). It closes the item that D-150 deferred to Phase 4.

- **How an adapter learns about exclusions.** `DiscoveryContext` gains `is_excluded_for_good`, which is true for works in history or `uploaded` in the ledger (`ExclusionSet.excludes_for_good`), and `notes`, a small record the adapter fills. A quarantined (`uncertain`) work is not excluded for good, because its quarantine ends. Adapters still yield every candidate, and selection still decides (§9.1); they use the predicate only to recognise pages that offer nothing new.
- **When a page is exhausted.** A page is exhausted when it offered at least one candidate and every candidate it offered is excluded for good. Records that the adapter refuses for good (rights, identifiers, the period, the rendition host, the Art Institute's minimum width) do not count either way. A page that offered nothing (an empty page, or one whose records the adapter could not use) is never exhausted, because the reason may be passing, and neither is a page with a work not yet sent, even one without dimensions.
- **Keys.** `aic:exhausted:<period or any>` and `cma:exhausted:<department or any>:<period or any>`, next to the counts. A hint is valid only for the result count it was computed with (D-156). The Art Institute pages are numbered from 1; Cleveland's pages are indices from 0 (the offset is 25 times the index), as each adapter already counts them.
- **Use.** Hinted pages are left out before the page order is shuffled, or treated as already drawn in Cleveland's lazy draw beyond 4 096 pages. The number skipped is added to `notes.pages_skipped`. Without hints, the page order and the requests are unchanged.
- **Hint when nothing is seen.** `NoDeliveryEvidence` gains `pages_skipped`. A run in which every candidate seen was excluded (`candidates_seen` may be 0) and at least one page was skipped as exhausted gets the hint "nothing new left for these filters" instead of "filters too restrictive". `last_run.json` reports `pages_skipped` with the selection statistics.
- **Writing the cache.** `ProviderBinding` gains an optional `cache` (a `CacheWriter` with `flush(deadline)`). The runner calls it once in FINISH, before the last-run record, with FINISH's deadline minus the last-run reserve; a failure only logs a warning and never changes the outcome. A run that stopped before SELECT (for example `already_running`) has no binding and never writes the cache. `StoreLayout.metadata_cache` builds the file cache for the Phase 6 wiring, which passes the same object to the adapter and to its binding.
- **Limitation.** The documentation does not promise a stable order of search results. A hinted page that shifts within the 7 days hides its works until the hint expires, and the result count changes the hint's validity only when the total changes. The effect is a missed work, never a duplicate (R-13).

**Amendment after the internal review of `4fcab6e` to `ec9e8a4`** (see *Review records*): hints first rested on every exclusion, `uncertain` included, and counted a page that offered nothing, or only works without dimensions, as exhausted. A quarantined work could then stay hidden up to 7 days beyond its 30-day quarantine, and one empty response hid a page for 7 days and later read as "nothing new left". Both are fixed as described above.

### D-158 — Preview publication and the run records [§13.1, §13.5, D-118, D8, F7]

Status: **accepted** (Phase 4 gate, user decision, 2026-09-27).

- **Modules.** `store/preview.py` (`PreviewStore`, the `PreviewPublisher` port) and `store/records.py` (`RunRecordStore`, the `RunRecords` port).
- **Fingerprint.** The D-118 fingerprint moves from `providers.local_media` into the shared top-level module `fingerprint.py`, next to `domain`, `errors`, and `randomness` (D-141). `imaging.delivery` and the store can then compute it without importing a provider. `DeliveryArtifact` gains `fingerprint`, which the parent computes over the same bytes as the SHA-256.
- **Preview.**
  - Every directory below `/media` is opened with `O_NOFOLLOW`, so a symbolic link at `frame_gallery` or `preview` is refused. Missing directories are created with exactly mode 0755, whatever the umask (amended after the internal review).
  - `delivery.jpg` is read again without following a link, at most 15 MiB, and its size and SHA-256 must match the values from ATTEMPT.
  - Each name is written with the §13.2 primitive at exactly mode 0644. The temporary file is read back and hashed before the rename.
  - Every name receives the same bytes. The default is `latest.jpg` until Phase 8 chooses the refresh mechanism (D-140).
  - Every name is staged and verified, and the deadline checked, before any name is renamed. With two names, only a rename that fails between the first and the second can leave them different; the run then reports `delivered_with_warnings`, and the next delivery writes both again. *Amended after the internal review:* before, each name was written and renamed in turn, so a failure on the second name left the names different in more cases.
  - A failed directory `fsync` after the rename only logs a warning. Any other failure raises `PublishError`, which gives `delivered_with_warnings`, for example when `/media` is unavailable.
- **`current.json`.**
  - It holds the runner's record plus `preview_fingerprints`: this delivery's fingerprint merged with the earlier ones, newest first, without repeats, at most 10.
  - The fingerprint is recorded even when the preview could not be published. It only ever keeps a copy of a delivered canvas out of the library.
  - `RunRecordStore.preview_fingerprints()` gives the list to the Phase 6 wiring for the local provider's guard 3. It never raises. A damaged `current.json` is quarantined, and its fingerprints are lost; guards 1 and 2 still apply.
- **Both records.** At most 16 KiB, mode 0600, no `.bak`. A record over the bound is refused with `StateError`. A test shows that the largest possible records fit, with every text field at 200 characters that each escape to 12 bytes. The runner's handling is unchanged: a failed preview or current record gives `delivered_with_warnings`, and a failed last-run record never loses the summary line (D-141).

### D-159 — Tests for state and duplicate prevention [§20.1; C3, E1-E10, F1-F7]

Status: **accepted** (Phase 4 gate, user decision, 2026-09-27).

- **Rig.** `tests/support/persistent.py` (`PersistentRig`) runs the runner over the real store ports (state, workspace, preview, records, and a provider's file cache) below temporary `data`, `media`, and `tmp` anchors. Each run builds fresh ports over the same directories, as a new process would, and may start days after the first. The provider, fetcher, executor, and television stay fakes; the fake television emits its progress markers. `Harness` gains optional overrides for the state, workspace, preview, and records ports.
- **Scenarios in process** (`tests/integration/test_state_scenarios.py`):
  - delivered runs (E1, E5, E6, E10, D8, F1), the ledger pruned once both history copies hold a work, and `no_match` with "nothing new left" once every work was sent;
  - E7 (selection refused after the upload) and E8 (connection lost during selection): `uploaded`, never resent;
  - E9 as a simulated kill (a `BaseException` that no handler catches) after the intent, after `uploaded`, and inside the promotion write; a failed promotion; `upload_started` without `uploaded`; no `upload_started`; a stop request after `upload_started` and after `selected`;
  - a full and a read-only `/data` (`state_error`, the television untouched), a newer history (kept), a corrupt history (F5), a failed history rename (`delivered_unrecorded`, never resent), and an unavailable `/media` (`delivered_with_warnings`);
  - repeated runs with no growth of temporary or state storage (F3), and a published preview copied into the library that `current.json`'s fingerprints keep out (F7).
- **A real SIGKILL** (`tests/integration/test_sigkill.py`). A child process runs the same rig and kills itself with SIGKILL after the intent, after `uploaded`, after `selected`, or inside the promotion write before its rename. Nothing in the child cleans up. The next run, in the test process, takes the lock, sweeps the pre-staged history, the temporary ledger file, and the run directory, and does not upload the work again. An `uncertain` work returns after the 30-day quarantine; a confirmed one never does.
- **The cache across runs** (`tests/integration/test_cached_discovery.py`). The real Art Institute adapter and gateway over the synthesized API, with the real file cache: the count and an exhausted page carry over between runs, and a run whose only page is known to be exhausted makes no search request and ends with "nothing new left".
- **Distinct payloads and the full §12.4 table.** Every delivery of the rig gets its own canvas bytes, so a stale preview, SHA-256, or fingerprint can never pass for a fresh one. Every row of the §12.4 table runs against the real ledger, and a test with the real Art Institute adapter and file cache shows that a hint never outlasts an upload quarantine (both added after the internal review).
- **Phase 5.** E7 to E10 are run again with the process-based television worker (`TASKS.md`).

## Phase 5 decisions (accepted)

These record how Phase 5 realizes §11.3 and §12, and every place where it deviates from the text of `ARCHITECTURE.md`. The user accepted them at the Phase 5 gate on 2026-10-02, D-165 with a condition, and `ARCHITECTURE.md` is amended to match.

### D-160 — `samsungtvws` 3.0.6: version, provenance, and LGPL-3.0 obligations [§12.2, D-104, D-135; R-04]

Status: **accepted** (Phase 5 gate, user decision, 2026-10-02). The user allowed the pinned version to be installed on 2026-09-27; it is installed only into the git-ignored `frame_gallery/.venv`, from the lock.

- **Version.** 3.0.6, published on 2026-09-11, is the newest release; no file of it is yanked. It requires Python 3.10 or newer.
- **Files, verified on 2026-09-27.** The official PyPI metadata lists the sdist `samsungtvws-3.0.6.tar.gz` (SHA-256 `166111d8370443cd2021b74cdfac9495896dfc41e3a87ea023289f24f922bb91`) and the wheel `samsungtvws-3.0.6-py3-none-any.whl` (SHA-256 `6e3a1b23f928b3035570cc976b64b8c2a218b06022a333855fd7cd02dc74891d`). Both were downloaded, and both hashes match the Phase 1 inventory and the lock. Only the wheel is installed.
- **Licence.** The metadata says `License-Expression: LGPL-3.0`, the deprecated SPDX short form. Neither the metadata nor any file header says "or later", so it is treated as `LGPL-3.0-only`. The `LICENSE` file is the same in the sdist and the wheel (SHA-256 `1a45b1d0a8603dfe2cfc644f9dab970b1762f92babe2aac6eb2f5d4572c4a680`) and holds only the LGPL-3.0 text, which incorporates GPL-3.0 by reference.
- **Provenance (the R-04 check).**
  - 21 of the 27 modules carry `SPDX-License-Identifier: LGPL-3.0`, with copyright lines of "DSR! <xchwarze@gmail.com>" (2019 and 2025) and, in `art/art.py`, also "Matthew Garrett <mjg59@srcf.ucam.org>" (2021).
  - The six modules without a header are `cli/__init__.py` and the `encrypted/` package, which the app does not use.
  - No MIT notice, no GPL-2.0 statement, and no relicensing statement appear anywhere in the sdist. The inconsistent licensing of versions before 2.7.0 therefore leaves no trace in 3.0.6. The qualified licence review (D-135) still covers the question.
- **Dependencies** (the core install; no extra): `websocket-client` 1.9.2 (`Apache-2.0`); `requests` 2.34.2 (`Apache-2.0`, with `NOTICE`), with `charset-normalizer` 3.5.1 (`MIT`), `idna` 3.20 (`BSD-3-Clause`), and the already approved `urllib3` and `certifi`; `yarl` 1.25.1 (`Apache-2.0`, with `NOTICE`), with `multidict` 6.9.1 (`Apache-2.0`) and `propcache` 0.5.4 (`Apache-2.0`, with `NOTICE`). These are exactly the versions of the Phase 1 inventory. Their licences were re-read from the installed metadata, and their licence and notice files are present.
- **`multidict` is held at 6.9.1.** `uv` first resolved `multidict` 7.0.0, a new major release published on 2026-09-26. Under D-128 (upgrades only after review), `constraint-dependencies = ["multidict<7"]` in `pyproject.toml` keeps the inventoried 6.9.1. A later, dedicated commit may lift it.
- **LGPL-3.0 obligations** (an engineering reading, not legal advice; the qualified review of D-135 is a release gate):
  1. The documentation and `THIRD_PARTY_NOTICES.md` state prominently that the image contains `samsungtvws` under LGPL-3.0, with its copyright notices.
  2. The LGPL-3.0 and GPL-3.0 texts accompany every distribution.
  3. The library stays unmodified: installed as a separate package from its PyPI wheel, never vendored or patched. The app uses only its public API and does not subclass it or change its code. At run time, inside the television worker only (D-162): the connect guard wraps functions of the standard library's `socket` module; a wrapper around `websocket-client`'s `create_connection` counts completed handshakes, keeps the connections it hands out so a failed attempt's connection is dropped, and during a connection attempt bounds each read of the new websocket to the pairing deadline; and on its own connection object the task answers the public `get_api_version()` from its earlier check. None of these touches a file of the library, and none stops a user from replacing it.
  4. Users can replace it: the documentation explains how to build the image with another version, and no technical measure prevents that.
  5. The exact sdist (SHA-256 above) is attached to every release as the corresponding source, and stays available for at least 3 years (D-135).
  6. No term restricts modification, or reverse engineering to debug such modifications.
- **Use.** Only the television worker task imports it (D-107); the boundary test enforces this.

### D-161 — The adapter surface of the installed `samsungtvws` 3.0.6 [§12.2, Q-15, D-104]

Status: **accepted** (Phase 5 gate, user decision, 2026-10-02).

The surface below was taken **only** from reading the installed wheel (`samsungtvws/connection.py`, `art/art.py`, `rest.py`, `helper.py`, `exceptions.py`) and from running it offline. Nothing was taken from any other project, and no television was contacted.

- **Constructor.** `SamsungTVArt(host, token=None, token_file=None, port=8001, timeout=None, key_press_delay=1, name="SamsungTvRemote")`. The task passes the IPv4 literal, `port=8002`, the stored token or `None`, `token_file=None`, `key_press_delay=0` (otherwise the library sleeps after every request), and `name="frame_gallery"` (D-138).
  - With `token_file=None`, a token the TV issues is kept in the object's `token` attribute. With a token file, the library reads the file with `readline()`, keeping any newline in the URL, and treats every read error as "no token".
  - `timeout` applies to **each** blocking wait, not to a whole call, and restarts on unrelated frames. `0` means no time-out at all. The REST client is created once, with the constructor's value. The websocket keeps the value it was opened with; `connection.settimeout()` changes it.
- **`supported()`.** A REST `GET https://<host>:8002/api/v2/` through `requests` with `verify=False`. It returns whether `FrameTVSupport` is `"true"`. It raises `HttpApiError` for a connection error, a TCP connect time-out included (`requests.ConnectTimeout` is a `requests.ConnectionError`); a raw `requests.ReadTimeout` for a time-out in the TLS handshake or the reply; `ResponseError` for an unparsable reply; and `AttributeError` for JSON that is not an object.
- **`open()`.** Calls `websocket.create_connection(url, timeout, sslopt={"cert_reqs": ssl.CERT_NONE})`, looked up at call time. The token is in the URL query, on port 8002 only. It then waits for `ms.channel.connect`, which may carry a new token, and then for `ms.channel.ready`.
  - Silence before or after the websocket handshake raises the same `websocket.WebSocketTimeoutException`, so only the handshake's completion tells a pairing prompt from a TV that does not answer.
  - While it waits for `ms.channel.connect`, it skips the start-up events `ed.edenTV.update` and `ms.voiceApp.hide`; each read gets the full time-out again.
  - `ms.channel.unauthorized` raises `UnauthorizedError`, a subclass of `ConnectionFailure`.
  - A time-out while waiting for `ready` raises `ConnectionFailure("Websocket Time out…")` and **leaves the connection set**: a second `open()` on the same object does not connect again. The base class hands back the stale connection, and `SamsungTVArt.open()` waits once more for `ready` on it: it raises again after another full time-out, or succeeds on the old connection if `ready` arrives late. A token the TV sent with `ms.channel.connect` is already in the object's `token`.
  - A failure inside the base class's `open()` (an unexpected first event, a malformed one, `ms.channel.unauthorized`) leaves the websocket only in a local variable: the library's own `close()` does not reach it.
  - A close frame gives `ResponseError` (the empty frame does not parse), and an empty event name an `AssertionError`.
- **`get_api_version()`.** The `api_version` request, then the legacy `get_api_version`; `ResponseError` without a version.
- **`upload(file, matte="shadowbox_polar", portrait_matte="shadowbox_polar", file_type="png", date=None)`.** It first calls `self.get_api_version()`.
  - On `"0.97"` it sends the image as a websocket binary frame. If a `ResponseError` follows (an error reply, or any frame that does not parse), it falls through to the second path and **uploads the same bytes again**.
  - Otherwise: `send_image`, then `ready_to_use` with a `conn_info` naming an address and port; a plain or TLS socket to that address; then the first `image_added` on the channel, **matched without a request id**. It returns that event's `content_id`.
  - The library itself uses `"none"` when no matte is given; the task passes `"none"` for both mattes, so the 16:9 rendition fills the screen.
- **`select_image(content_id, category=None, show=True)`.** The TV's own error reply raises ``ResponseError("`select_image` request failed with error number N")``; a frame that does not parse raises a `ResponseError` with another text.
- **`close()`** performs the websocket close handshake, which can wait up to 3 s. The task drops the connection with the websocket's `shutdown()` instead.
- **Logging.** The library logs a new token at INFO and every `ms.error` frame, in full, at WARNING.
- **Exceptions.** `UnauthorizedError` ⊂ `ConnectionFailure`; `ResponseError`, `HttpApiError`, and `MessageError` are separate; the `websocket` exceptions are not `OSError`s; `requests`' exceptions are.
- **How it is held to this surface.** `tests/unit/tv/test_samsung_real_library.py` runs the unchanged library over a socket pair against a scripted television (no network): the token in the URL, the token it relays (also after a missing ready event), the prompt and hang cases, start-up events that must not stretch the pairing wait, a malformed connect event, the retry on a new connection with the old one dropped, the 0.97 refusal, the D2D address check, and the select refusal text. The in-process stand-in (`tests/support/fake_samsungtvws.py`) must keep the installed signatures (a conformance test compares them) and raises the library's own exception classes. The second upload on 0.97 is read from the installed code and modelled by the stand-in; it is not run against the library, because the scripted television accepts no binary frame.

### D-162 — The television task and the Samsung adapter [§12.1–§12.4, §7.2, §5, §21; amends §12.1, §12.2, §12.4, D-147; D-114, D-115, D-137, D-141]

Status: **accepted** (Phase 5 gate, user decision, 2026-10-02). An independent critique (four lenses, adversarially verified) of the Phase 5 design shaped points 1–7. At the gate, Art API 0.97 stays `unsupported` in the beta (point 3), and TLS pinning is decided after the TV's certificate is observed in the supervised Phase 8 test (point 11).

1. **The token travels in the channel, not in a file** (amends §12.1 `token_seed_path` and §12.2 "seeds the token file into `out/`"). The stored token goes to the worker inside its request message; the worker builds the library object with `token_file=None`. A token the TV issues comes back as a `token` event before `connected`, at most one per connection attempt: it is sent even when the wait for `ms.channel.ready` fails after it, and the retry then uses it. The parent checks its form, registers it with the redactor, and installs it at once (mode 0600, atomically; the last one wins), so it is kept even if the worker dies later; `auth` is then `new_token`. After a rejection, a stored token is removed (`token_rejected`). The reasons:
   - the library would send a seeded file's newline as part of the token, and so reject or re-pair on every run;
   - a token file would sit in the worker-writable `out/`, readable by any process of the worker's group, and the parent would have to read back a file the worker controls;
   - the redactor learns a new token before any later worker log line reaches the parent.
   A token must be 6 to 64 ASCII letters or digits: the redactor ignores secrets shorter than 6 characters.
2. **Only validated bytes are uploaded.** `DeliveryRequest` carries the parent's SHA-256 of `delivery.jpg` (a port change). The worker reads the file once, without following a link, and uploads only a buffer with exactly that hash; it checks this before it contacts the TV.
3. **Art API 0.97 is `unsupported` in the beta.** On 0.97 the library may upload the same image twice (D-161), against D-115. The version is read after `connected` and before `upload_started`, so a refusal removes the intent. The version is then answered from that check on the connection object, so `upload()` neither asks again nor takes the 0.97 path. *Phase 5 gate (user decision, 2026-10-02):* 0.97 stays `unsupported` in the beta; the alternative, accepting the residual double upload after an error reply to the first upload, was not taken. The TV's real version is observed in Phase 8.
4. **Connecting.** Each attempt uses a new library object, because a second `open()` on the same object would wait again on the stale connection instead of connecting. Every connection handed out so far is dropped first, including one the library's failed `open()` never stored. A websocket time-out after a **completed handshake** is an unaccepted prompt: `not_authorized` (`prompt`), never retried (D-115). Any other failure before `connected` is retried once, if the connect time and the upload allowance are still left.
5. **Time.** The worker gets the delivery's end as an absolute `time.monotonic()` value, which every process on the host shares, so its own start-up counts against it, and it keeps 1 s to send its result.
   - With less than the connect time plus the upload allowance left, it returns `insufficient_time` before contacting the TV.
   - The pairing wait is `min(20 s, time left − 15 s)`, **one deadline per attempt**: the connect time-out of the websocket is clamped to it, and each read of the new connection waits at most until it, so start-up events the library ignores cannot stretch it (§12.2: "the prompt must be accepted within 20 s").
   - The upload and the selection may each use all the time left; the kill timer is the only total bound, and a kill during the selection still leaves `uploaded`.
   - The connect guard bounds every TCP connect (REST, websocket, and D2D) to 5 s. The TLS handshake and each read of the HTTP upgrade reply get the clamped connect time-out; the waits for `ms.channel.connect` and `ms.channel.ready` end at the pairing deadline. D-114's "connect ≤ 5 s" is thus the TCP connect; the kill timer remains the only total bound.
   - `insufficient_time` before `connected` (too little time to connect and upload, before the TV was contacted or after a slow capability check) gets no hint: nothing was paired. After `connected` it keeps "paired; start the app again" (amends the §12.4 table).
   - No library time-out is ever below 0.5 s: the library reads 0 as "none".
6. **The connect guard** lets the worker reach only the TV's IPv4 literal (any port), passes only that literal to `getaddrinfo`, and refuses every other name and every other address, including a D2D address the TV names. A refusal raises `GuardViolation`, which is not an `OSError`, and sets a flag; the task reports it as `protocol` ("the worker's connect guard refused…"), not as a TV that is off.
7. **The mapping is total.** Each step catches every `Exception`:
   - before `connected`: `UnauthorizedError` → `not_authorized` (`rejected`); a post-handshake time-out → `not_authorized` (`prompt`); a transport failure → `unreachable`; anything else (a close frame, a malformed or unexpected answer) → `protocol`; the last two are retried once (point 4); `supported()` false → `unsupported`;
   - after `connected`, before `upload_started`: the version check as in point 3; `insufficient_time` if less than the upload allowance is left;
   - after `upload_started`: a `ResponseError` → `protocol` (the TV's error number, if any, goes into the detail); a transport failure → `unreachable`; anything else → `protocol`. The quarantine is always kept: the library does not tell a refusal before the transfer from one after it, so §12.4 row 6 (explicit upload refusal) is not produced in the beta;
   - after `uploaded`: only the TV's own error reply to `select_image` → `refused`; another `ResponseError` or anything else → `protocol`; a transport failure → `unreachable`.
8. **`uploaded` may come without a content ID** (a port change). The TV confirmed the upload when `upload()` returns. If the returned ID does not have the strict form, `uploaded` is still sent, without an ID, so the ledger entry is promoted, and the result is `protocol`; the selection is skipped.
9. **The parent checks the worker.**
   - Each event must have the exact shape.
   - A marker that repeats is refused. A marker out of order is relayed first (the runner handles it conservatively) and then stops the worker as a protocol violation.
   - The status must fit the markers the parent itself relayed: `ok` needs `selected`; `refused` needs `uploaded` and no `selected`; `not_authorized`, `unsupported`, and `insufficient_time` need no `upload_started`; nothing follows `selected`; a pairing value comes only with `not_authorized`. Otherwise the status is `protocol`.
10. **Library loggers** (`samsungtvws`, `websocket`, `urllib3`, `requests`) are capped at WARNING in the worker, and both tokens are registered with the worker's redactor. The "unverified HTTPS request" warning is filtered, because the unverified TLS on port 8002 is the library's documented behaviour.
11. **Known limitations.**
    - The library matches `image_added` without a request id, so an upload by another client at the same moment could be taken for ours (R-30).
    - TLS to the TV is not verified (R-03). Pinning the certificate on first use is feasible without touching the library: the standard `ssl.SSLContext.sslsocket_class` hook can compare the certificate before any byte is sent. At the Phase 5 gate (user decision, 2026-10-02) the decision was deferred until the TV's certificate is observed in the supervised Phase 8 test (see *Phase 5 gate decisions*), because whether the certificate survives firmware updates and resets cannot be observed before Phase 8.
    - A kill during the wait for `ms.channel.ready` still loses a token the TV issued in that attempt; the next run pairs again.
12. **Layout, dependencies, and one import exception** (amends §5, §21, and D-147).
    - New modules beyond §21: `tv/contract.py`, `tv/samsung.py`, `tv/samsung_task.py`, `tv/token_store.py`; `isolation/framing.py`, `isolation/launch.py`, `isolation/process.py`, `isolation/bootstrap.py`, `isolation/worker_main.py`.
    - New internal dependencies beyond §5, as D-141 records them: `tv.contract`, `tv.samsung`, and `tv.samsung_task` use `isolation.executor`; `tv.samsung`, `tv.samsung_task`, and `tv.token_store` use `logs.redact`, and `tv.samsung` also `logs.summary`; `tv.token_store` uses `store.atomic` (the store imports nothing from `tv`); `tv.samsung_task` uses `imaging.contract` (`MAX_OUTPUT_BYTES`); `isolation.bootstrap` uses `logs.redact`; `isolation.process` uses `budget.clock` and `logs.summary`; `isolation.launch` names the worker task modules only as strings. There is no cycle.
    - D-147 made `net/transport.py` the only module that imports `socket`; `tv/samsung_task.py` now imports it too, only inside the connect guard, and the boundary test allows exactly that (no `ssl` or `http`).

### D-163 — The process executor and the worker bootstrap [§4.3, §11.3, §14; D-109, D-139, D-141; amends §11.3]

Status: **accepted** (Phase 5 gate, user decision, 2026-10-02). An independent critique of the design (four lenses; 34 findings confirmed by adversarial verification, 14 refuted) shaped it before it was written; an independent review of the implementation (five lenses; 45 findings confirmed, 4 refuted, none of high severity) amended it (see *Review records*).

- **Start.** Each task runs in a new worker: `python -I -S -B -c BOOT <configuration> <paths> -- <site-packages>`, in its own process group, with `/` as its working directory and exactly this environment: `PATH=/usr/local/bin:/usr/bin:/bin`, `LC_ALL=C.UTF-8` (so the interpreter never adds `LC_CTYPE`), `TZ=UTC`. `-S` keeps `site` out, so no `.pth` file or `sitecustomize` runs before the bootstrap; the parent's site-packages directories go at the end of the worker's path instead. The worker has six descriptors: stdin and stdout on `/dev/null`, stderr (a pipe whose last 4 KiB the parent keeps), and the request, result, and lifeline pipes (the parent holds the other end of the lifeline). `BOOT` decides nothing: it puts the paths on `sys.path` and calls `worker_main.main`. The configuration on the command line holds no secret; the request, which may carry the pairing token, follows over the pipe only after the bootstrap.
- **Bootstrap** (`isolation/bootstrap.py`), in the order of §11.3, with additions marked *(+)*:
  1. With an identity (the parent is root): `setgroups([])`, then the real, effective, and saved group and user IDs, all verified. Without one (a development host), the worker must not be root. A worker with an identity accepts no test path and no task module outside `frame_gallery`.
  2. On Linux, required: `PR_SET_DUMPABLE` 0 *(+)* and `PR_SET_NO_NEW_PRIVS` *(+)*, then `PR_SET_PDEATHSIG(SIGKILL)`, each read back; the capability sets must be empty; then the parent must still be the expected one. On every platform *(+)*, a lifeline thread ends the worker as soon as its read of the lifeline returns, which happens when the parent is gone (macOS has no parent-death signal).
  3. `umask 027`, read back.
  4. Resource limits, each as soft = hard, so the worker cannot raise them again, and read back: `RLIMIT_AS` 1 GiB (image) or 512 MiB (television); `RLIMIT_CPU` 30 s; `RLIMIT_FSIZE` 16 MiB (image) or 1 MiB (television); `RLIMIT_NOFILE` 32; `RLIMIT_CORE` 0; and last *(+)* `RLIMIT_NPROC` 0: after it the worker can start no process (and, on Linux, no thread), so nothing it runs can outlive it or leave its process group. This replaces a kill of every process of uid 65534 after each worker.
  5. The environment must be exactly the one above; only macOS's own `__CF_USER_TEXT_ENCODING` is ignored there.
  6. Logging goes to the parent over the channel: redacted, at most 900 characters a record, at most 99 records and one "dropped" note; third-party loggers at WARNING or above.
  The bootstrap reaches the platform only through a small seam (`OsOps`), so every step and every refusal is tested in-process; `ctypes` (for `prctl`, through `CDLL(None)`) is imported only there.
- **Handshake** *(+)*. The worker's first message is `ready`, with the IDs, groups, umask, limits, and environment names it verified. The parent compares them with what it asked for, and only then sends the request.
- **Channel** (amends §11.3 "`recv_bytes(maxlength = 64 KiB)`"). Frames are a 4-byte length and canonical JSON; a frame may be 64 KiB plus 1 KiB for its envelope, and each body (request, event, result) is held to the 64 KiB cap of the in-process executor, so both executors accept the same sizes. The parent reads with `poll`, which has no descriptor-number limit. Messages: `ready`, `refused`, `request`, `event`, `log`, `result` (with the worker's own peak memory and CPU time), `failure` (`crash`, `memory`, or `protocol`, naming only the exception type).
- **Ends.**
  - The kill timer is the task's timeout; a stop request is polled every 50 ms. Either sends `SIGKILL` to the worker's group and to the worker; the result pipe is then read to its end, bounded by 1 s and 1 MiB (not by a message count), and every complete event in it is still relayed, up to the first thing that is not such an event (a result, another message, or a malformed frame); the run fails with `timeout` or `stopped`, even if the adapter refuses one of those events. Messages decoded before a malformed frame in the same read are handled first, whatever the chunking.
  - A `failure` message decides `crash`, `memory`, or `protocol`; exit status 75 without one is `memory`; any other end without a result is `crash`.
  - A malformed frame, an unknown or misplaced message, a second `ready`, or an event the adapter refuses is `protocol`, and the worker is killed. A malformed or excess log record is only dropped; anything after the result is ignored.
  - After every worker, on every path, a stop request included, its group and the worker get `SIGKILL` and it is reaped, under a lock that `terminate_all` shares, so no ID that may have been reused is signalled. The reap waits at most 2 s: a worker that has not ended by then (for example one in uninterruptible I/O) is logged as an error and left unreaped, as the active worker. The descriptors are closed either way. `run` returns or raises only then, so nothing the worker writes can reach the caller afterwards.
  - The start is robust as well: a failure at any point closes every descriptor, a worker that was forked is killed and reaped (or, if the failure was inside `Popen` itself, ends on its own when its request and lifeline pipes close), and the worker is recorded as the active one as soon as `Popen` returns. The executor takes a `shield` around the start; *for Phase 6 (accepted with D-163 at the Phase 5 gate):* the entry point passes one that defers stop requests there.
- **`IsolationFailure`** *(+)*. A worker that cannot be started, refuses to run, ends before `ready`, or reports values that do not match is an `IsolationFailure`, not a `WorkerError`: no caller treats it as a failure of one task. The run ends as `internal_error` (§11.3), the prepare step tries no second candidate, a local inspection does not count an unreadable file, and the television keeps a committed intent in quarantine.
- **Logs.** Worker records are re-emitted under `frame_gallery.worker.<task>`, capped at WARNING, sanitized, at most 100 per worker. The last 4 KiB of stderr (at most 30 lines) go to DEBUG only.
- **Launch.** `Launch.production()`: as root, every worker drops to 65534; on Linux, the parent-death signal is required and every limit is set. On a host that is neither (development), the worker keeps the developer's identity and `RLIMIT_AS`, which macOS cannot set, is skipped; `Launch.enforced` is then false. *For Phase 6 (accepted with D-163 at the Phase 5 gate):* the entry point asserts `Launch.enforced` in the container, and builds one executor that the runner, the Samsung adapter, and the watchdog share.
- **Tests.** Every branch of the bootstrap and the worker's entry is covered in-process; real workers show the behaviour, among it the worker's own process group, the group kill reaching a process left in the group, the kill before the drain, the stop poll, the drain after a timeout, and that the request is sent only after a verified `ready`. Every task in `tests/support/worker_tasks.py` installs the H2 network guard first (`tests/support/h2.py`); the production `deliver` task, run with the real library in such a worker, meets it. The root-only checks run production tasks without the guard, and only tasks that open no socket (`tests/support/h2.py` names every unguarded process). `scripts/check.sh` also type-checks the code as on Linux (`mypy --platform linux`), and no coverage exemption is allowed in the worker's code. The boundary tests allow `subprocess` and `select` only in `isolation/process.py`, `ctypes` only in the bootstrap, the worker's modules only in the worker, and the process executor only in the entry point.

### D-164 — The workspace is handed to the worker's group [§11.3, §13.1; amends D-155]

Status: **accepted** (Phase 5 gate, user decision, 2026-10-02). At the gate, the `inspect` limitation below is decided: the parent passes read-only descriptors where possible, from Phase 6.

- With a worker group (65534 when the parent is root): `frame-gallery/` and `run-*/` become 0710, `in/` 2750, and `out/` 2770, all in that group. The worker can pass through, read what the parent put into `in/`, and create files only in `out/`. The setgid bit gives every file below the worker's group.
- Each directory is created 0700, then given the group (a chown by a non-root user clears the setgid bit), then its mode, and its owner, group, and mode are then checked, so a mistake fails at creation with a clear message and not as `EACCES` in the worker.
- Downloads and local copies are written 0640, whatever the umask, so the worker's group can read them.
- Without a worker group (development), every directory stays 0700, as in D-155.
- *Known limitation (unchanged from §11.3):* the `inspect` worker opens library files in `/media` itself, so as uid 65534 it can read only files that are readable by others; any other file is counted as unreadable. The Phase 6 documentation says so. *Phase 5 gate (user decision, 2026-10-02):* where possible, the parent opens each file and passes the read-only descriptor to the worker, from Phase 6 (see *Phase 5 gate decisions*).

### D-165 — What Phase 5 verified here, and what first runs in the Linux container [§11.3, §20.4; R-09]

Status: **accepted with a condition** (Phase 5 gate, user decision, 2026-10-02). The Linux and root isolation tests and the worst-case preparation measurement under the real `RLIMIT_AS` must run successfully in Phase 6, in the container. They are mandatory before any live test on the Home Assistant Green.

- **Verified on the development host** (macOS arm64, CPython 3.12.14, not root): the executor, the channel, the kill timer, stop requests with the drain, the end of a worker whose parent is killed (its lifeline), E7–E10 with the process-based television worker, including a real SIGKILL of the runner while its worker runs; every bootstrap step and refusal (in-process, with a fake that clears the parent-death signal on a change of credentials, as Linux does); the bootstrap test from inside the worker for this host (umask, hard limits including `RLIMIT_NPROC` 0 with `fork` refused, the exact environment, `/` as the working directory, the interpreter flags, no module outside the standard library and this package, the worker's own process group, only the six expected descriptors); the workspace modes and groups with a supplementary group; and the worst-case preparation time and peak memory without `RLIMIT_AS` (R-09).
- **Written, but first run in a Linux container**, in two passes that name their mode, so that a skip of what the mode promises fails (`tests/support/processes.py`, DEVELOPMENT.md):
  - as a non-root user, `FRAME_GALLERY_REQUIRE_ISOLATION=user`: the whole suite, including `RLIMIT_AS` 1 GiB and 512 MiB, the refusal of threads under `RLIMIT_NPROC` 0, and the parent-death signal, no-new-privileges, dumpability 0, and empty capability sets as read by a task inside the worker;
  - as root, `FRAME_GALLERY_REQUIRE_ISOLATION=root`, `tests/unit/isolation/test_root_isolation.py`: the drop to 65534 with no groups and every limit, checked through the `ready` report of a production worker; the dropped worker reading `in/`, writing `out/`, and unable to create a file in `in/`. The test tasks cannot run as root by design (a dropped worker refuses test paths), so a root pass skips them.
  On Linux the bootstrap also refuses to run without the parent-death signal, no-new-privileges, a non-dumpable worker, and empty capability sets.
- **Decided at the Phase 5 gate** (the condition above). Both passes run in the Phase 6 container, whose build Phase 6 approves; the measurement of `scripts/measure_prepare.py` under the real `RLIMIT_AS` moves to that container (as root, where its workers drop to 65534) and to the Green in Phase 8. The TASKS item "Measure worst-case prepare memory and time under the real limit" is met only in part in Phase 5 and moves to Phase 6.

### Phase 5 gate decisions (user, 2026-10-02)

The questions that Phase 5 put to its gate were decided as follows. The options as they were put are kept in the git history (`937ce13`).

- **TLS pinning (R-03).** Decided only after the TV's certificate is observed in the supervised Phase 8 test. Until then, the library's unverified TLS stays as it is (D-161).
- **Art API 0.97 (D-162 point 3).** `unsupported` in the beta, as implemented.
- **The Linux checks (D-165).** They run in the Phase 6 container, in two passes, together with the worst-case preparation measurement under the real `RLIMIT_AS`. They must pass there (the condition of D-165), and they are mandatory before any live test on the Green.
- **Library files for `inspect` (D-164).** Where possible, the parent opens each library file and passes the read-only descriptor to the worker. Implemented in Phase 6.
- **`inspect` batching (D-149).** Implemented in Phase 6.
- **The progressive-JPEG peak under `RLIMIT_AS` (R-09).** The 1 GiB limit of the image worker stays for now. Any change is decided only from the measurement under the real limit in the Linux container.
- **Worker containment after a code-execution exploit (R-31).** AppArmor child profiles per worker stay in Phase 9.

## Phase 6 decisions (accepted)

These record how Phase 6 packages the app (§17), wires the entry point (§4, §14), implements the two `inspect` decisions of the Phase 5 gate, verifies the container, and inventories what the image ships, with every place where the implementation deviates from the text of `ARCHITECTURE.md` or an earlier decision. The user accepted them at the Phase 6 gate on 2026-10-03, after the Codex review and its follow-up checks, with the 1 GiB limit of D-170 unchanged, and `ARCHITECTURE.md` is amended to match.

### D-166 — The entry point [§4, §4.3, §14, §15.1, §17.5; D-141, D-163]

Status: **accepted** (Phase 6 gate, user decision, 2026-10-03).

- `python -m frame_gallery` runs `__main__.main()`: one run per start. Importing the module has no side effects. A `Wiring` record holds every production port; tests replace only the parts that would start a process or reach a network (`tests/unit/app/test_main.py`).
- **Order** (the TASKS item): a `CancellationController(start_deferred=True)`, and only then the SIGTERM handler (D-141); the Supervisor token read into memory and the environment reduced to the allowlist before anything else runs (§17.5). The token is kept only when a helper option is set (read from the same options file), and it is registered with the redactor either way, as is the legacy `HASSIO_TOKEN`. Then logging through the redactor (§19); the process executor (D-163), whose worker starts are shielded so that a stop request waits until the start is complete (`deferring`); the store, the gateway and the three providers, the helper reader, the television, and the watchdog; then one run.
- **Refusal** (D-163, "for Phase 6"). On Linux the app refuses to run unless `Launch.enforced`: the parent runs as root, and every worker drops to 65534 with every limit and the parent-death signal. It then ends as `internal_error` with exit code 70 and one summary line, before it contacts anything.
- **One executor** is shared by the runner, the local inspection, the Samsung adapter (`HostTelevision`), and the watchdog.
- **The watchdog** (`RunWatchdog`) fires at the run's `T` + 10 s. The runner arms it with its own `RunBudget` (`WatchdogControl.arm(budget)`). When it fires, it kills the active worker group, removes the workspace, emits the only summary line, and ends the process with 71 (D-133). When the runner reports that it did not emit the summary, the entry point waits for the watchdog's exit instead of returning an exit code.
- **The options file** (`store/options_file.py`): `/data/options.json`, read once per run below the `/data` anchor, without following a link, at most 64 KiB, as strict JSON. Anything else ends the run as `config_invalid`, with a message that says what to do (for a damaged file: save the options again in the Configuration tab, which makes the Supervisor write it anew). `config.options` still validates every value.
- **The container's networks** (`app/networks.py`) come from the kernel's IPv4 route table, `/proc/net/route`: every route except the default one names a network the container reaches. The table is parsed in the host's byte order. On Linux a table that is missing, oversized, not ASCII, or not in the kernel's form fails closed as `config_invalid`, because the television-address rule (D-125) and the helper reader's token rule (D-148) depend on it. The kernel's form is its header line and, on every other non-empty line, at least eight fields with an eight-digit hexadecimal destination and a prefix mask. A table with only its header is valid: a container without a network has one. A development host has no table, and the list is empty there.
- **The preview fingerprints** (the local library's guard 3, D-118) are read while the run is built, before it holds the state lock, so that read changes nothing: a damaged `current.json` is only reported, and the next write under the lock quarantines it (§13.3).
- **Log level.** `log_level: debug` raises the app's own loggers once the options are read (`set_app_level`).
- **Boundary.** `__main__` is the only module that imports the real network transport and the process executor; the boundary test treats it as the composition root.

### D-167 — The container image, and the D-130 checks [§17.2; D-128, D-130, D-142; amends D-130]

Status: **accepted** (Phase 6 gate, user decision, 2026-10-03). The user approved the base-image pull and the build's network use on 2026-10-02 (*Review records*).

- **Base.** `ghcr.io/home-assistant/base:3.24-2026.08.0@sha256:93ef607824e3f27e868f11b10938283a98bf880ed57bcf8eaa81c6c2d521f6f5`, a multi-architecture index, with the tag taken from the registry's tag list on 2026-10-02. It holds Alpine 3.24.1, s6-overlay 3.2.3.0, bash, bashio, tempio, curl, jq, and bind-tools (D-171 lists every component).
- **Interpreter.** Alpine's `python3=3.14.8-r0`, pinned to the exact apk version (D-128). Its runtime closure adds 11 packages to the base: gdbm, libbz2, libexpat, libffi, libpanelw, mpdecimal, sqlite-libs, and the four `python3` and `pyc` packages. readline was already in the base, for bash. **gdbm and readline are `GPL-3.0-or-later`.**
- **Stages**, in this order:
  - `base`: the pinned base image, named once.
  - `python`: the base and `python3`, for the build. Python's package bundles a pip wheel for `ensurepip` (`pip-26.2.1-py3-none-any.whl`), which the build uses.
  - `builder`: an installer venv with that pip, and the app's venv `/opt/frame-gallery`, created `--without-pip`. The installer runs `PIP_CONFIG_FILE=/dev/null pip --isolated --python /opt/frame-gallery/bin/python install --index-url https://pypi.org/simple --require-hashes --no-deps --only-binary=:all: -r requirements/image-runtime.txt` (D-128). The app's sources are copied into the venv's site-packages and compiled.
  - `app`: the base, `python3` installed once more and in the same layer stripped of the bundled pip wheel, and the venv; no pip, no wheel, no compiler, no build tool. So no layer of the app holds pip or the packages pip vendors.
  - `test`: never published. It builds on `app`, adds the test tools from `requirements/image-test.txt` and a copy of the repository, for the container checks only.
  - `runtime`: `app` itself, as the **last stage**, so that a build without a target, as the Supervisor makes it, produces the app image and never the test stage. BuildKit builds only the stages a target needs; a builder without BuildKit builds the test stage too, but the image it produces is still the app. `scripts/container_check.sh` checks that a build without a target has the same layers, command, environment, and labels as `runtime`.
- **Only PyPI.** The base image sets `PIP_EXTRA_INDEX_URL` (and `UV_EXTRA_INDEX_URL`) to Home Assistant's wheel index. `--isolated` makes pip ignore every `PIP_*` variable and the user's configuration, and `PIP_CONFIG_FILE=/dev/null` every configuration file, so only PyPI is used; the hashes fix what is installed either way.
- **Requirement files** (amends D-142, whose `requirements/runtime.txt` stays the development export). `scripts/image_requirements.py` writes `requirements/image-runtime.txt` and `requirements/image-test.txt` from `uv.lock`: for each package, the one wheel that pip installs for CPython 3.14 on `musllinux_1_2` `aarch64` and `x86_64`, with its hash. A test fails when they differ from the lock.
- **Arguments and labels** (amends D-130). `BUILD_ARCH` and `BUILD_VERSION` are required, and there is no fallback to `TARGETARCH`. With BuildKit, `BUILD_ARCH` must match the platform being built, so a mislabelled image cannot be built; a builder without `TARGETARCH` accepts any supported `BUILD_ARCH`. The labels are `io.hass.type=app`, `io.hass.arch`, and `io.hass.version`, and the OCI title, description, and version of the app; the base image's OCI source and build time are cleared, and its `io.hass.base.*` labels, which describe the base, stay. There is no OCI `licenses` label (D-130). The Supervisor may add labels of its own when it builds the app; Phase 8 observes them.
- **Start.** `CMD ["with-contenv", "/opt/frame-gallery/bin/python", "-I", "-B", "-m", "frame_gallery"]`, under the base image's s6-overlay init (`init: false` in `config.yaml`), with `S6_CMD_RECEIVE_SIGNALS=1` and `S6_VERBOSITY=1`.
- **The D-130 checks**, run by `scripts/container_check.sh` on both architectures (results in D-170):
  - (a) Alpine 3.24.1 and Python 3.14.8; the script checks them against the base tag's Alpine series and the `python3` pin.
  - (b) The container stops when the command exits, with its exit status.
  - (c) **Not met without a remedy.** s6-overlay gives the command a grace of 3 s after a stop request and then kills it. With `S6_CMD_RECEIVE_SIGNALS=1`, the stop request (SIGTERM) reaches the app at once, and s6 waits for the app to exit, within the 20 s stop timeout of `config.yaml`. `S6_KILL_GRACETIME=18000` was tried and rejected: every container stop then took 18 s. s6 prints one cosmetic line, "sh: invalid number '--'", on such a stop.
  - (d) **Not met as worded.** s6 resets the command's environment, so `SUPERVISOR_TOKEN` is not visible without `with-contenv`. With `with-contenv` it is. After the app exits, the container lives about 3.3 s more, for s6's own shutdown.
  - **Proposal:** keep the Home Assistant base image with these two remedies. D-130's fallback, a plain Alpine base with `init: true`, is not needed.
- **Build context.** `.dockerignore` is an allowlist; the app image copies only `src/frame_gallery` and the requirement file. The Dockerfile has no `syntax` line, so the build uses BuildKit's own Dockerfile frontend and pulls no frontend image.
- **The exact pin and later builds.** Alpine's stable branch keeps only the newest build of each package. Once v3.24 replaces `python3` 3.14.8-r0, `apk add python3=3.14.8-r0` fails, and with it any later build, a build on the Green included (R-32). The packages that `python3` pulls in are not pinned, so a later build can also hold other versions than the inventory records. The pin follows D-128's monthly review with a new inventory; the Phase 8 install route (Q-21) settles how the Green gets a build.

### D-168 — App metadata, translations, the AppArmor draft, and the documentation [§15.1, §16, §17.1, §17.4, §17.6; D-123, D-129, D-138, D-140, D-152]

Status: **accepted** (Phase 6 gate, user decision, 2026-10-03). The enforcement of the AppArmor profile stays a release prerequisite (Phase 9).

- **`config.yaml` and `translations/en.yaml`** are written by `scripts/app_config.py` from the app's own definitions. The department and period choices come from the built-in vocabulary (D-152), and a test checks every offered value and pattern against the app's own parser, and that both files match what the script writes.
- **`config.yaml`** follows D-129 exactly: `startup: once`, `boot: manual_only`, `init: false`, `arch: [aarch64, amd64]`, `stage: experimental`, `homeassistant: 2026.2.0`, `homeassistant_api: true`, `tmpfs: true`, `timeout: 20`, the media folder read-write (narrowed by AppArmor), and the backup exclusions `cache/**`, `state/quarantine/**`, and `tv/**`. `tv_host` has no default, so the app cannot start without it. No `image`, URL, host network, privilege, device, or Supervisor API role is set, so the Supervisor builds the image locally from the Dockerfile until the release (Phase 9); such a build on the Green needs the same network sources as here, and Phase 8 settles the install route (Q-21).
- **Translations** say for each filter which sources it applies to (B8).
- **`apparmor.txt`** is the §17.6 profile as a draft in complain mode for Phases 6 to 8 (D-129, D-139): the capabilities `setuid` and `setgid` (the drop to 65534), `chown` and `fsetid` (the workspace handed to the worker's group: the parent sets the setgid folders' mode after giving them a group it is not a member of, and without `fsetid` the kernel would clear the setgid bit), `dac_read_search` (the parent reads what a worker wrote, mode 0640 and owned by 65534), and `kill`; TCP and UDP over IPv4 and IPv6; raw and packet sockets denied; the S6-Overlay lines of Home Assistant's example profile; `/media` read-only except the preview; `/data` and `/tmp`. It also allows UNIX stream sockets, which s6-overlay's own s6-rc services presumably use; the Phase 8 complain log shows whether that is needed. A test holds the profile to §17.6. **Syntax check** (Codex, an external follow-up check at the Phase 6 gate, reported on 2026-10-03): `apparmor_parser -Q -T` accepted `apparmor.txt` in a temporary aarch64 container with exit code 0; its only warning was that the container lacks the kernel's AppArmor interface. This checks the syntax only, **not the enforcement**: whether the profile, loaded by the Green's kernel and enforced, lets the app and its workers run is not tested. Phase 8 runs it in complain mode and reads what it would refuse; Phase 9 enforces and verifies it.
- **Documentation.** `DOCS.md` covers installation, the first start and pairing, the options and the capability matrix, the user's own images, a draft dashboard as copy-and-paste YAML (the Local File camera `camera.frame_gallery_preview`, the Running sensor `binary_sensor.frame_gallery_running`, the timer `timer.frame_gallery_run`, the script `script.frame_gallery_new_artwork`, the card, and an optional morning automation; the app ID `local_frame_gallery` for a local copy), the outcomes of the log line, the known limitations in plain language (R-29 among them), privacy, and the licences. Every entity ID is marked as expected until Phase 8 confirms it. `README.md` is the store text, and `CHANGELOG.md` starts at 0.1.0.dev0.
- **Initial icon and logo** were original geometric drawings, made by `scripts/app_images.py` without fonts or trademarks; a test redrew them and compared the pixels. The post-release user-approved mark/export supersedes this presentation detail (D-201); the released runtime image is unchanged.

### D-169 — `inspect` over parent-opened descriptors, in batches [§8.3, §11.3; D-149, D-163, D-164; Phase 5 gate decisions]

Status: **accepted** (Phase 6 gate, user decision, 2026-10-03). It implements two decisions of the Phase 5 gate.

- **The parent opens the files.** For each candidate, the parent opens the library file read-only, without following a link, non-blocking, and close-on-exec. It keeps the descriptor only if `fstat` shows the regular file with the identity (device and inode) that the scan saw. A file that cannot be opened is `unreadable`; one that changed since the scan is `changed`, and no worker starts for either.
- **The worker gets descriptors, never a path.** Up to 16 descriptors go to one `inspect` worker, at the same numbers (`Executor.run(..., files=...)`, which refuses more than 16, duplicates, and the standard three). The worker checks each descriptor's identity again, reads the header as before, and never closes a descriptor it was lent; the parent closes them after the run. So the worker, at 65534, can measure every file the app can open, which resolves the limitation of D-164. A root test shows it: a dropped worker measures a 0600 file in a 0700 folder.
- **Batches and the time limit.** The task reports one event per file, in order; an event too many, like any malformed event, is a `protocol` failure. A file whose event does not arrive within 2 s of the previous one (`LOCAL_INSPECTION_S`; for the first file, from the worker's start) stops the worker. A worker that stops, crashes, or times out fails the file it was on (`inspection_failed`, as before); the files after it go to a new worker. A batch's timeout is 2 s per file, clamped to the discovery deadline, and a timeout at that deadline ends discovery as before. An `IsolationFailure` still ends the run as `internal_error` (D-163).
- **The batch size, 16** (§8.3 allows up to 50). Every descriptor counts against the worker's `RLIMIT_NOFILE` of 32, next to its own six (D-163).
- **Selection** charges each candidate to the inspection allowance when it arrives, and lets it wait until 16 are waiting, a candidate with known dimensions arrives, or the pass ends for any reason (the provider ends, the candidate allowance runs out). The batch is then measured in one worker and ranked in the original order, so the shortlist is the one a file-by-file pass would build. Candidates after a full shortlist are reported as `unranked:shortlist_full`. At the discovery deadline the waiting ones are reported as `dims_unavailable:deadline`. When a provider stop in a batch ends the pass, the rest of that batch is reported as `unranked:provider_stopped`. Every charged candidate gets a decision.
- **The aggregated warning** of the library (§9.3) is logged when selection is done (`LocalMediaProvider.report_discovery`, which the runner calls through the new `ProviderBinding.after_discovery`), so that the files of the last batch, measured after the scan has ended, count too.
- **The trade-off.** With a shortlist of 2 (`SHORTLIST_SIZE`), a batch can measure up to 15 files more than a file-by-file pass would, and charge them to the allowance of 300. One worker start costs more than many header reads, and with the default strict 16:9 rule most photos do not qualify, so the selection usually needs many files. Measured in the aarch64 container: 150 inspections in 10 workers took 0.6 s (0.004 s each); one worker per file took 0.057 s each in an earlier run of the same script there, before batching (its output was not kept in the repository).
- **Not changed:** the allowance, the error classes, the 2 s per file, the result format (one `InspectResult` per file).

### D-170 — What the container checks verified [§11.3, §17.2, §20.4; D-130, D-165; R-09, R-26, R-27]

Status: **accepted** (Phase 6 gate, user decision, 2026-10-03), with the 1 GiB limit unchanged. It records the condition of D-165, which the Phase 5 gate set and which is met. The native `amd64` measurement is mandatory before an `amd64` version is published, at the latest in Phase 9.

`scripts/container_check.sh` builds the app image and the test image for one architecture, checks that a build without a target gives the app image, runs the D-130 checks, the inventory (D-171), and a smoke run of the app, and then the two test passes of D-165; with `--measure` it also runs `scripts/measure_prepare.py` as root under the real `RLIMIT_AS`. Every container runs with `--network none`, and no host directory is mounted. On this host (Docker Desktop 4.91.0, Engine 29.8.0, Buildx 0.37.0, BuildKit 0.33.0, Apple silicon), `aarch64` runs natively and `amd64` under Rosetta.

- **D-130 checks**, both architectures: (a) Alpine 3.24.1 and Python 3.14.8; (b) exit status 70 came through as 70; (c) the app received the stop request about 3 s after its start, cleaned up for 8 s, and the stop took 11 s; (d) `SUPERVISOR_TOKEN` visible (with `with-contenv`).
- **Smoke run**, both architectures: one local-media run with one library file and no network ended `tv_unreachable` with exit code 0 (TV address 10.0.0.5, unreachable without network), after selection, inspection, and preparation in real, dropped workers.
- **D-165, user pass** (`FRAME_GALLERY_REQUIRE_ISOLATION=user`, uid 1000): the whole suite, including `RLIMIT_AS` 1 GiB and 512 MiB, threads refused under `RLIMIT_NPROC` 0, the parent-death signal, no-new-privileges, dumpability 0, and empty capability sets as read inside the worker. At the closing commit `79dc8f7`: 4 562 passed and the 5 root-only checks skipped, on both architectures (`STATUS.md` has every result).
- **D-165, root pass** (`FRAME_GALLERY_REQUIRE_ISOLATION=root`): all 5 root checks passed on both architectures: a production `prepare`, `inspect`, and `deliver` worker each drop to 65534 with no groups and every limit; the dropped worker reads `in/`, writes `out/`, and cannot create a file in `in/`; and it measures a file only root can read, through the descriptor its parent passed.
- **Worst-case preparation under the real `RLIMIT_AS` 1 GiB** (R-09), as root, aarch64, 2 runs per case: all 13 cases succeeded. Peak address space (`VmPeak`) and resident memory (`VmHWM`), and time:

  | Case | Fit | Peak address space | Peak resident | Time |
  | --- | --- | --- | --- | --- |
  | 64 MP JPEG, baseline | contain | 170 MiB | 158 MiB | 0.5 s |
  | 64 MP JPEG, progressive | contain | 277 MiB | 265 MiB | 1.1 s |
  | 64 MP JPEG, progressive 4:4:4 | contain | 460 MiB | 448 MiB | 1.1 s |
  | 64 MP CMYK panorama | cover | 355 MiB | 344 MiB | 0.6 s |
  | **64 MP progressive CMYK panorama** | **cover** | **766 MiB** | **754 MiB** | **1.4 s** |
  | 64 MP progressive 4:4:4 panorama | cover | 644 MiB | 631 MiB | 1.2 s |
  | 64 MP JPEG behind a header flood | contain | 189 MiB | 176 MiB | 0.4 s |
  | 40 MP PNG, RGB | contain | 286 MiB | 274 MiB | 0.7 s |
  | 40 MP PNG, RGBA | contain | 439 MiB | 427 MiB | 0.8 s |
  | 40 MP PNG, palette with transparency | contain | 477 MiB | 465 MiB | 0.6 s |
  | 40 MP PNG, grey with a transparent key | contain | 478 MiB | 465 MiB | 0.5 s |
  | 40 MP PNG, 16-bit grey | contain | 453 MiB | 440 MiB | 0.6 s |
  | 40 MP PNG behind a chunk flood | contain | 303 MiB | 290 MiB | 0.5 s |

  The heaviest case leaves 258 MiB (25 %) of the 1 GiB. **The 1 GiB limit stays** (accepted at the Phase 6 gate; the Phase 5 gate decision allowed a change only from this measurement, and none is needed). The Green is several times slower; Phase 8 repeats the measurement there (R-09).
- **What the earlier figures got wrong.** The Phase 5 figures on macOS came from `ru_maxrss`, which on Linux also counts the parent's memory before `exec`. The worker now reports its own peaks from `/proc/self/status` (`VmHWM`, `VmPeak`).
- **amd64 under Rosetta.** The D-130 checks, the inventory, the smoke run, and both test passes passed. Rosetta keeps its own descriptors open in every process, which the descriptor check of the test tasks now leaves out (only when Rosetta is present). The measurement there is informative only: every case shows about 278 MiB more address space than on aarch64 at nearly the same resident memory (about 8 MiB more), presumably Rosetta's own reservations. With them, the heaviest case, the progressive CMYK panorama in `cover`, reaches the 1 GiB limit (peak 921 MiB, then a failed allocation) and fails; the other 12 cases succeed. A native amd64 host has no such reservations, and none was available for a measurement. Times under emulation say nothing about a native host.
- **A failed allocation inside the JPEG decoder is reported as `decode`.** In that amd64 case, Pillow reported libjpeg's failed allocation as "OSError: broken data stream when reading image file", so the worker answered `decode`, not `memory`. The run then skips the file as it would a broken one, which is safe; only the log names the wrong cause. Natively the heaviest case stays 258 MiB below the limit. Accepted at the Phase 6 gate as a known limitation (R-09).
- **The native amd64 memory measurement.** No native amd64 host was available, and the measurement under Rosetta is informative only. Whether the heaviest case fits the 1 GiB limit on a native amd64 host is therefore not measured. *Phase 6 gate (user decision, 2026-10-03):* the measurement is mandatory before an `amd64` version is published, and it runs at the latest in Phase 9.
- **R-26** (local tests versus the runtime build) is met for Phase 6: the whole suite runs in the image, on its Python and Pillow, for both architectures. **R-27** (pre-emption) is in force: the entry point builds the process executor.

### D-171 — The authoritative inventory: the Pillow wheels, the image, and the SBOM approach [inventory; D-130 check a, D-135; H4, R-17, R-25]

Status: **accepted** (Phase 6 gate, user decision, 2026-10-03). It replaces the provisional inventory of the bundled libraries (Codex, Phase 1) and fills the base-image rows. The qualified licence review stays a release prerequisite (D-135).

- **The SBOM approach.** No SBOM tool is downloaded or installed. `scripts/image_inventory.py` runs inside the app image, with its own interpreter and no network, and records: every Alpine package from apk's database, with its licence; what the base image installs outside apk (the s6-overlay packages, tempio's embedded Go build information, bashio); every Python distribution with its licence metadata; and, for Pillow, each library in `pillow.libs` with its SHA-256 held to the wheel's `RECORD`, the two CycloneDX SBOMs that the wheel embeds, the features Pillow reports, the zlib it loads, and the versions inside its libavif; and every wheel file under `/usr` and `/opt`, of which the app has none (D-167). `scripts/container_check.sh` keeps the result as JSON for each architecture and fails if a library differs from the wheel's `RECORD` or the image holds a wheel. A generated SBOM (for example Syft or `docker buildx --sbom`, which pulls a scanner image) needs its own approval, and the release can add one in Phase 9.
- **The two runtime wheels**, downloaded from `files.pythonhosted.org` (approved), with hashes matching `uv.lock`: `pillow-12.3.0-cp314-cp314-musllinux_1_2_aarch64.whl` (SHA-256 `fe3cca2e4e8a592be0f269a1ca4835c25199d9f3ce815c8491048f785b0a0198`) and `pillow-12.3.0-cp314-cp314-musllinux_1_2_x86_64.whl` (SHA-256 `23aceaa007d6172b02c277f0cd359c79492bbb14f7072b4ede9fbcaf20648130`). They hold the same 21 libraries in the same versions, the same licence file, and the same Pillow SBOM. Methods: the file list; the dynamic dependencies of every ELF file (`DT_NEEDED`); version strings in the binaries; the auditwheel SBOM (the libraries grafted from Alpine packages); Pillow's own SBOM; the licence file's sections; and, in the image, Pillow's own feature report and the libavif API (`avifVersion`, `avifCodecVersions`, `avifLibYUVVersion`).
- **Findings that change the inventory:**
  1. **`libimagequant` is not in the wheels.** Pillow's SBOM lists it (4.4.1, `GPL-3.0-or-later`) with the scope "optional", and that is where the Phase 1 entry came from. The wheels contain no such library, `_imaging` neither links it nor contains its code (only the feature flag's name), and in the image Pillow reports `libimagequant` as unavailable.
  2. **FriBiDi is not in the wheels.** Pillow's `fribidi-shim` (`LGPL-2.1-or-later` per Pillow's SBOM) is compiled into `_imagingft` and loads `libfribidi` only if the system has it; the image has none, and Pillow reports `fribidi` and `raqm` as unavailable. The shim's code is shipped; FriBiDi's is not.
  3. **zlib is not bundled.** Pillow was compiled against zlib-ng 2.3.3's compatible headers, but its libraries load `libz.so.1` from the system: in the image, Alpine's zlib 1.3.2-r0 (`Zlib`).
  4. **Statically linked, not in Pillow's SBOM:** bzip2 1.0.8 inside libfreetype (`bzip2-1.0.6`); inside libavif, dav1d 1.5.3 (`BSD-2-Clause`), aom 3.14.1 (`BSD-2-Clause`; AOMedia's patent licence is not in the wheel), libyuv (version number 1924, `BSD-3-Clause`), and libsharpyuv; code from Tcl/Tk's headers in `_imagingtk` (`TCL`, the licence file's `TCL_TK` section). raqm 0.10.5 (`MIT`) and fribidi-shim are compiled into `_imagingft`, and `pythoncapi_compat` (`0BSD`) into the extensions, as Pillow's SBOM says; pybind11 is used only to build.
  5. **The nine pending entries** are verified: libXau 1.0.12 and libXdmcp 1.1.5 (`MIT-open-group`, the Open Group notices in the licence file; Alpine packages 1.0.12-r0 and 1.1.5-r1), Brotli 1.2.0 (`MIT`), liblzma 5.8.3 (`0BSD` upstream since 5.6.0; the wheel's licence file still carries the older public-domain notice), libpng 1.6.58 (`libpng-2.0`), libsharpyuv 0.1.2 (part of libwebp 1.6.0, `BSD-3-Clause`), and libzstd 1.5.7 (`BSD-3-Clause`; upstream also offers `GPL-2.0-only`). **libbsd 0.12.2 and libmd 1.1.0** (Alpine packages 0.12.2-r0 and 1.1.0-r0, grafted by auditwheel as libXdmcp's dependencies): the wheel carries no licence text for them. Their licences come from the official Alpine package directory, read by Codex in an external follow-up check at the Phase 6 gate, reported on 2026-10-03 (not re-read by Claude): libbsd 0.12.2-r0 `BSD-3-Clause` (https://pkgs.alpinelinux.org/package/v3.20/main/x86/libbsd), and libmd 1.1.0-r0 "BSD-3-Clause AND BSD-2-Clause AND ISC AND Beerware AND Public Domain" (https://pkgs.alpinelinux.org/package/v3.20/main/x86_64/libmd). The versions are the ones the auditwheel SBOM names. **"Public Domain" is not an SPDX identifier**: it is recorded as Alpine states it, the four other terms are SPDX identifiers, and the exact form of the public-domain part (for example a `LicenseRef-`) is settled in the licence review. With this, the versions and licences of all nine entries are verified, and the condition approved at `dda877c` is met; nothing was published before.
- **Consequences** (accepted at the Phase 6 gate):
  - The image carries no GPL-3.0-or-later code from Pillow, and no FriBiDi. The copyleft obligations (D-135) apply to what the image does carry: `samsungtvws` (`LGPL-3.0`), Pillow's `fribidi-shim` (`LGPL-2.1-or-later`), and the copyleft Alpine packages, among them BusyBox, apk-tools, alpine-baselayout, and scanelf (`GPL-2.0-only`), bash, readline, and gdbm (`GPL-3.0-or-later`), and the GPL and LGPL parts of musl-utils, libgcc, libstdc++, keyutils, libcom_err, libidn2, libunistring, userspace-rcu, xz, and zstd (each with its own licence expression, as `THIRD_PARTY_NOTICES.md` lists them). **The image is still not free of GPL components.** At the user's request (2026-10-03), `ARCHITECTURE.md` §17.2, §23, and §24 and the Phase 9 TASKS item, which said the wheels bundle both, are corrected before the gate.
  - The withdrawn Phase 1 claim ("the PyPI wheels omit `libimagequant`") turns out to be right for these two wheels, but for a different reason than first given: they never contained it. The Phase 1 correction came from the SBOM, which describes Pillow's optional dependencies, not the wheels' contents.
- **The image** (both architectures, identical versions): 61 Alpine packages (50 from the base, 11 from `python3`), each with apk's licence field; outside apk, s6-overlay 3.2.3.0 with execline 2.9.9.0, s6 2.15.0.0, s6-linux-init 1.2.0.1, s6-linux-utils 2.6.4.1, s6-overlay-helpers 0.1.2.2, s6-portable-utils 2.3.1.2, and s6-rc 0.6.1.0; tempio 2026.07.0 (Go 1.26.5, with 11 Go modules); and bashio. The image carries no licence text for s6-overlay, tempio, its Go modules, or bashio; their licences are read from the upstream projects, which are hosted on GitHub, once that access is approved (open item, before any release). The 11 Python distributions match the inventory below. `THIRD_PARTY_NOTICES.md` lists every component.
- **Build tooling rows** (not shipped): Docker Desktop 4.91.0 with Engine 29.8.0, containerd 2.3.4, runc 1.4.3, Buildx 0.37.0, and BuildKit 0.33.0, all bundled with Docker Desktop, whose start the user approved. amd64 images run under Rosetta, which Docker Desktop uses on Apple silicon; Docker Desktop's QEMU emulation is not used for the two target platforms.

### D-172 — Answers to Q-06 and Q-10 [§13, §11.3, §17.6]

Status: **accepted** (Phase 6 gate, user decision, 2026-10-03). Q-06 and Q-10 are resolved as below.

- **Q-06 (a reset of history, or a new pairing).** Not in the beta. Uninstalling the app removes its `/data` folder, with the history, the upload ledger, the quarantine, the cache, and the pairing key, so reinstalling is the reset; the artworks on the TV and the preview in `/media` stay. A new pairing alone already happens on its own: when the TV rejects the stored key, the key is removed, and the next start asks the TV again (D-162). `DOCS.md` has a short "Starting over" section, and Phase 8 confirms that an uninstall removes `/data`.
- **Q-10 (an unprivileged parent).** Not in the beta. The parent needs root, or at least `CAP_SETUID` and `CAP_SETGID` to drop every worker to 65534, `CAP_CHOWN` and `CAP_FSETID` to hand the workspace to the worker's group, `CAP_DAC_READ_SEARCH` to read what a worker wrote, and `CAP_KILL` to end it (D-163, D-164, D-168). Without them, the workers would run as the parent's own user and could read the pairing key and the state in `/data`, which removes the separation that §11.3 is built on. The parent's own exposure is small: it parses no image (the workers do), reaches only the selected museum through the gateway's allowlist and, for helpers, the Supervisor, and runs under the AppArmor profile with these six capabilities. Revisit in Phase 9, together with the per-worker AppArmor child profiles (R-31): for example a parent with only those capabilities as ambient capabilities of a dedicated user, if s6-overlay and the Supervisor support it.

## Phase 7 decisions (proposed)

This records how Phase 7 validated the release candidate offline. It is proposed for the Phase 7 gate.

### D-173 — How Phase 7 validated the release candidate [§20, §23; D-130, D-162, D-165, D-170, D-171]

Status: proposed.

- **The existing images, not a rebuild.** As the user's authorization says, Phase 7 built nothing and used no network. `scripts/container_check.sh --no-build` checks the images that Phase 6 built instead: both must exist, the test image must build on the app image, and the app image must hold exactly the checkout's `src/frame_gallery`, compared file by file through SHA-256 manifests. The script lists every file in which the test image's copy differs from the checkout, and fails if one of them is a build input (`src/`, `requirements/`, the Dockerfile, `.dockerignore`, `pyproject.toml`, `uv.lock`). Whether a build without a target gives the app image is checked only when building, as Phase 6 did. The images' tests are therefore the Phase 6 suite; the tests added in Phase 7 ran on the host.
- **The notices as a check** (H4, §20.4). `scripts/image_inventory.py --notices` holds `THIRD_PARTY_NOTICES.md` to the image's own inventory: every Alpine package with its version and apk's licence field, every Python distribution with its version, every library in `pillow.libs`, and the components outside apk. `container_check.sh` runs it after the inventory, so every later container check fails when the notices miss a component. A test holds the notices to `requirements/image-runtime.txt`, without the image.
- **Failure paths through the real image.** `scripts/failure_paths.py` runs the image's own command, as the Supervisor starts it, through 10 scenarios on `/data` and `/media` prepared in new Docker volumes, with `--network none` and no host directory, and checks the outcome, the hint, the exit status, `last_run.json`, the ledger, the history and its quarantine, and what the run left behind (C5, C7, C11, E4, F2, F5). The silent television is a listener on a second loopback address that a helper container adds in its own network namespace (`NET_ADMIN`, that container only); the app's container joins that namespace, which has no other interface. A failed upload after `upload_started` needs a television that takes the upload, so it stays with the suite (E7-E10, the unchanged library against a scripted television).
- **The report.** `RELEASE_CANDIDATE.md`, at the repository root; a later release candidate replaces it.
- **Proposed: a clarification of D-162 point 4.** "Any other failure before `connected` is retried once" means a failure while opening the art channel. A failure of the REST check that comes first (`supported()`) ends the delivery as `unreachable` (or `protocol`) without a retry, which is within D-115's "at most one reconnect". The code and the task's own documentation already say so; the Phase 7 scenario `silent-tv` shows it (one connection, `tv_unreachable` after 5.3 s). Only D-162's text would change.

## Phase 8 corrections (authorized)

### D-174 — Shallow, per-run randomized Chicago discovery [§9.5; C3, C8, C9]

Status: authorized by the user on 2026-10-03, for the separate test app only.

- The original live run stopped after its search returned HTTP 403. Read-only Green probes subsequently found that page 1 succeeds, but pages 199 and 200, each with limit 50, return HTTP 403 with "Invalid number of results" / "You have requested too many results. Please refine your parameters." The failed page of the original run is unknown; no exact actual API boundary is inferred, and no DNS, Tailscale or security settings were changed.
- The official [AIC documentation](https://api.artic.edu/docs/) permits Elasticsearch Query DSL. Elastic's [function-score documentation](https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-function-score-query) describes `random_score` with an integer seed and `_seq_no`, without a script or fielddata on `_id`. One approved, read-only production-gateway request from the Mac validated a seed-41 shallow search: 50 public-domain records, total 59 063. This is black-box API observation, not API server source inspection.
- Each run draws one seed in `[0, 2**31)` through the injected random source, preserves the rights and period filter inside `function_score`, and reads sequentially at most the first seven pages of 50 records with that same seed. Count caching, gateway pacing, the 15-request allowance, candidate/time limits and all per-record checks stay unchanged. A 403 still stops immediately; there is no retry, reseed or bypass after it.
- Old AIC page-exhaustion hints are ignored and no new ones are written: page membership is no longer stable between runs. Existing files, sent history and upload ledger are not reset or deleted; the bounded cache expires old entries normally. Cleveland's hint behavior is unchanged.
- This supersedes the default-order random-page sampling and AIC hints of D-150/D-157, not the museum filters, rendition or rights model. Live Green validation of the new code remains required.

### D-175 — Count-only storage diagnostics after cleanup [§14; F1–F3, H3]

Status: authorized by the user on 2026-10-03, for the separate test app update.

- The normal parent cleanup calls a diagnostic hook before the final outcome line and before disarming the watchdog. A diagnostic exception is best-effort only and does not change a confirmed delivery or skip other cleanup.
- It performs six fixed, shallow scans: state, state/quarantine, cache, pairing-key directory, preview and scratch. At most 128 entries per directory, with one shared 0.5-second budget. It uses existing no-follow directory descriptors and `stat(..., follow_symlinks=False)` only: no file contents, no recursion, no writes, no directory creation, no keys, identifiers, filenames or full paths in its logs. No new permission, mapping or dependency is needed.
- Logs include regular-file counts and apparent byte sizes, own temporary-file and run-directory counts, other/unreadable entry counts, truncation and availability. An unavailable directory is not declared empty, and the report is a metadata snapshot rather than a file-integrity/history validation. It is not guaranteed to run after a hard kill.
- Prior read-only Green inspection found about 15.8 GB free and exactly two shared-media files: a 263 066-byte synthetic library fixture and a 584 565-byte latest preview. Private storage and container scratch were not exposed to the protected SSH app; diagnostics must be observed from within the test app instead of weakening that protection.

### D-176 — Explicit, bounded loading-timer completion [§16.3; G4, R-06]

Status: authorized by the user on 2026-10-03, only for the separate test app/script correction. Delivery, no-match, graceful-cancellation completion and missing-notification timer expiry verified live on Green. Original filters and explicit timer restored; see `PHASE8_REPORT.md`.

- Running updates lagged by about 15 minutes and caused both premature and prolonged loading feedback. The script no longer uses Running or camera refresh as a completion signal.
- A new optional `loading_timer` accepts only a single `timer.<lowercase identifier>` (64-character object ID maximum), validated independently from other options. Unset means no extra Core request. The app retains the Supervisor token in parent memory only for configured helpers or this timer; it still removes it from the environment and never gives it to a worker.
- After normal cleanup, before disarming the watchdog, the app sends at most one POST to the fixed `/core/api/services/timer/cancel` path, with only this entity ID. It reuses the helper reader's private/container-network address guard, has no redirects or retries, reads no response body, and uses at most 2 seconds clamped to FINISH and the 70-second no-delivery bound. HTTP errors are logged by status only and never retried or change a confirmed outcome. `already_running` never cancels the timer of the running instance.
- The UI-created script starts its own 150-second timer before the app, waits for timer idle, and holds single mode for four more seconds while s6 shuts down. The timer itself bounds feedback on failed start, missing credentials, HTTP failure, watchdog or hard kill. A timer configured for another app must not be shared; it means finished, not success.
- This narrowly amends D-112/D-166/§5/§15/§17.5/§18: no arbitrary service, HA configuration write, new role, mapping, helper entity, dependency, or persistent daemon. Tests must cover successful delivery, no-match, graceful cancellation and feedback failure. Isolation refusal or unreadable options falls back to expiry.

### D-177 — Hash-guarded s6 signal interpreter correction [D-167; §17.2]

Status: authorized by the user on 2026-10-03, for the separate test app's stop warning. Both Linux container checks and the Green graceful-stop test passed without `invalid number '--'`; cleanup and timer completion also succeeded. See `PHASE8_REPORT.md`.

- The pinned base contains `/package/admin/s6-overlay-3.2.3.0/etc/s6-linux-init/skel/CMDSIG`, SHA256 `7debfda814cfe11f6b87492cce523eb6e1a2abdf622d0465b73c6d3ccd4bef72`. Its `kill -s ... -- "$pid"` makes BusyBox sh report `invalid number '--'`, although it then signals the real PID; observed graceful cancellations succeeded.
- The app image changes only that script's interpreter from `/bin/sh` to already-installed `/bin/bash`. Its signal arguments, body and permissions stay unchanged. The Docker build fails on any upstream hash mismatch. No package or security permission is added. Container stop checks must assert both real cleanup and absence of this warning.
- This is a modification to the third-party s6-overlay component, explicitly recorded in notices. Its upstream licensing, original source and this Dockerfile transformation remain part of the mandatory Phase 9 source/licence review; the project does not claim this upstream script as Apache-2.0 code.

## Proposed dependency inventory

Status: **Phase 2 installed** the development tools and Pillow, **Phase 3 installed** `urllib3` 2.8.0 and `certifi` 2026.7.22, and **Phase 5 installed** `samsungtvws` 3.0.6 and its dependencies (each approved by the user on 2026-09-27; the `samsungtvws` row is confirmed at the Phase 5 gate on 2026-10-02), only in the local project environment (`frame_gallery/.venv`, from `uv.lock`). **Phase 6** built the app image from the pinned base image and the hash-pinned `musllinux` wheels (approved on 2026-10-02) and verified the bundled-library and base-image rows in it (D-171, accepted at the Phase 6 gate).

- Versions and licenses were read from PyPI metadata (`https://pypi.org/pypi/<name>/json`) on 2026-09-26.
- In Phase 2 the installed versions and `License-Expression` fields were re-read from each installed distribution's metadata; they match the rows below.
- In Phase 3 the same check was made for `urllib3` (`License-Expression: MIT`, `LICENSE.txt`) and `certifi` (legacy `License: MPL-2.0` with the MPL classifier, no `License-Expression`; `LICENSE`). Both are pure-Python `py3-none-any` wheels with no dependencies; no `urllib3` extra is installed.
- `samsungtvws` was independently re-verified.
- Before each dependency enters (see the per-phase approvals in `STATUS.md`), its `LICENSE` file inside the pinned distribution is checked and this table is updated.
- The final image SBOM must match this table (acceptance item `H4`).

This is an engineering inventory, not legal advice.

**Use** codes:

- **dyn**: imported at runtime, installed unmodified from PyPI with hash pinning.
- **redist**: included in the published image.
- **native**: contains compiled code.

Python dependencies are not modified or vendored. D-177 records the sole s6-overlay script interpreter change made in the image build.

### Runtime: direct

| Package | Source and pin | SPDX (as published) | Use | Obligations | Reason | Enters |
| --- | --- | --- | --- | --- | --- | --- |
| `samsungtvws` | PyPI, `==3.0.6`; later `>=3.0.6,<4` after contract tests. sdist SHA-256 `166111d8370443cd2021b74cdfac9495896dfc41e3a87ea023289f24f922bb91`; wheel SHA-256 `6e3a1b23f928b3035570cc976b64b8c2a218b06022a333855fd7cd02dc74891d`. | `LGPL-3.0` (deprecated short form; treated as `LGPL-3.0-only` until the shipped `LICENSE` says otherwise) | dyn, redist, pure Python; core install only | See the LGPL obligations below | Television transport (D-104) | Phase 5 (installed 2026-09-27; D-160, accepted at the Phase 5 gate on 2026-10-02) |
| `Pillow` | PyPI `musllinux_1_2` wheels for `aarch64` and `x86_64`, `==12.3.0` (`<13` until validated); approved for use from Phase 2 (Codex final approval of Phase 1 at `dda877c`); the exact cp314 wheels are in `requirements/image-runtime.txt` | `MIT-CMU` **for Pillow itself; the wheel bundles third-party libraries and compiles in the `LGPL-2.1-or-later` fribidi-shim** (see the bundled-library table; D-171) | dyn, redist, native | Pillow `LICENSE`; every bundled component's licence and acknowledgement; corresponding source for the fribidi-shim (the Pillow sdist, D-135) | Image pipeline (§11) | Phase 2 |
| `urllib3` | PyPI `==2.8.0` (`<3`), `py3-none-any`; wheel SHA-256 `0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3` | `MIT` (`LICENSE.txt`) | dyn, redist | License text | Gateway transport (D-131); imported only by `net/transport.py` | Phase 3 (approved and installed 2026-09-27) |
| `certifi` | PyPI `==2026.7.22`, `py3-none-any`; wheel SHA-256 `62f22742b58a1a33014a2b6b706588a8d7e2a88ae7bd1a6ebe8c992928483775`; sdist SHA-256 `741e2c3b351ddf169a738da9f2c048608ff7f2c5cc02f1ebc6b118bb090d5d55` | `MPL-2.0` (`LICENSE`) | dyn, redist (CA bundle) | Files kept unmodified under MPL-2.0; identified in the notices; source pointer (D-135) | The gateway's explicit CA bundle (§10); imported only by `net/transport.py` | Phase 3 (approved and installed 2026-09-27) |

### Runtime: bundled in the Pillow wheels

**Authoritative** since Phase 6 (D-171, accepted at the Phase 6 gate): inspected in the exact two runtime wheels, `pillow-12.3.0-cp314-cp314-musllinux_1_2_aarch64.whl` and `…_x86_64.whl` (hashes as in `uv.lock`), and in the built image for both architectures. Both wheels hold the same libraries in the same versions. The provisional Phase 1 table (from the Codex inspection of the wheels' SBOM) is in the git history (`31e3868`); its differences are listed below the table.

| Component (where) | Version | SPDX | Evidence | Obligations |
| --- | --- | --- | --- | --- |
| libavif (`pillow.libs`) | 1.4.2 | `BSD-2-Clause` | SBOM; `avifVersion()` in the image | Licence text |
| dav1d, AV1 decoder (inside libavif) | 1.5.3 | `BSD-2-Clause` | `avifCodecVersions()`; licence file | Licence text |
| aom, AV1 encoder (inside libavif) | 3.14.1 | `BSD-2-Clause` | `avifCodecVersions()`; licence file | Licence text; AOMedia's patent licence is not in the wheel (licence review) |
| libyuv (inside libavif) | 1924 (`LIBYUV_VERSION`) | `BSD-3-Clause` | `avifLibYUVVersion()`; licence file | Licence text |
| Brotli: libbrotlicommon, libbrotlidec | 1.2.0 | `MIT` | library version; licence file | Licence text |
| bzip2 (inside libfreetype) | 1.0.8 | `bzip2-1.0.6` | symbols and build path in the binary; licence file | Licence text |
| FreeType: libfreetype | 2.14.3 | `FTL` | SBOM; Pillow's feature report | Licence text; the FTL credit in `DOCS.md` and the notices |
| HarfBuzz: libharfbuzz | 14.2.1 | `MIT-Modern-Variant` (HarfBuzz's "Old MIT"; Pillow's SBOM says `MIT`) | SBOM; version string; licence file | Licence text |
| libjpeg-turbo: libjpeg | 3.1.4.1 | `IJG AND BSD-3-Clause AND Zlib` (the zlib licence covers the SIMD extensions, which both wheels contain; Pillow's SBOM leaves it out) | SBOM; version string; Pillow's feature report; SIMD names in the binaries | Licence texts (the wheel carries only the IJG text; the licence review confirms and adds the rest); the IJG acknowledgement in `DOCS.md` and the notices |
| Little CMS 2: liblcms2 | 2.19.1 | `MIT` | SBOM (Pillow reports 2.19) | Licence text |
| liblzma (XZ Utils) | 5.8.3 | `0BSD` | version string; upstream licence since 5.6.0 | Licence text (the wheel still carries the older public-domain notice) |
| OpenJPEG: libopenjp2 | 2.5.4 | `BSD-2-Clause` | SBOM; version string | Licence text |
| libpng: libpng16 | 1.6.58 | `libpng-2.0` | version string; licence file | Licence text |
| libsharpyuv (and a copy inside libavif) | 0.1.2, from libwebp 1.6.0 | `BSD-3-Clause` | library version; libwebp's licence | Licence text |
| libtiff | 4.7.1 | `libtiff` | SBOM; version string | Licence text |
| libwebp, libwebpdemux, libwebpmux | 1.6.0 | `BSD-3-Clause` | SBOM; Pillow's feature report | Licence text |
| libxcb | 1.17.0 | `X11` | SBOM | Licence text |
| libXau | 1.0.12 (Alpine 1.0.12-r0) | `MIT-open-group` | auditwheel SBOM; licence file | Licence text |
| libXdmcp | 1.1.5 (Alpine 1.1.5-r1) | `MIT-open-group` | auditwheel SBOM; licence file | Licence text |
| libbsd | 0.12.2 (Alpine 0.12.2-r0) | `BSD-3-Clause` | auditwheel SBOM; the official Alpine package directory (Codex's follow-up check, reported on 2026-10-03); no licence text in the wheel | Licence text, added from upstream for the release |
| libmd | 1.1.0 (Alpine 1.1.0-r0) | `BSD-3-Clause AND BSD-2-Clause AND ISC AND Beerware` and "Public Domain", as Alpine gives it; **"Public Domain" is not an SPDX identifier** | auditwheel SBOM; the official Alpine package directory (Codex's follow-up check, reported on 2026-10-03); no licence text in the wheel | Licence texts, added from upstream for the release; the licence review settles the public-domain part |
| libzstd | 1.5.7 | `BSD-3-Clause` (upstream: `BSD-3-Clause OR GPL-2.0-only`) | version string; licence file | Licence text |
| raqm (inside `_imagingft`) | 0.10.5 | `MIT` | SBOM | Licence text |
| fribidi-shim (inside `_imagingft`) | 1.x | `LGPL-2.1-or-later` | SBOM | **Copyleft.** LGPL-2.1 text; corresponding source: the Pillow 12.3.0 sdist (D-135) |
| Tcl/Tk header code (inside `_imagingtk`) | — | `TCL` | licence file (`TCL_TK`); names in the binary | Licence text |
| pythoncapi_compat (inside the extensions) | per the SBOM | `0BSD` | SBOM | Licence text (courtesy) |

**Not in the wheels**, although the provisional table listed them:

- **libimagequant** 4.4.1 (`GPL-3.0-or-later`): Pillow's SBOM lists it with the scope "optional". No file of the wheels contains it, `_imaging` does not link it, and Pillow reports it as unavailable in the image.
- **FriBiDi** 1.0.16 (`LGPL-2.1-or-later`): also optional in the SBOM. The shim loads it at run time only if the system has it; the image has none, and Pillow reports `fribidi` and `raqm` as unavailable.
- **zlib** (zlib-ng 2.3.3 in the SBOM): Pillow was built against zlib-ng's compatible headers, but its libraries load `libz.so.1` from the system, in the image Alpine's zlib 1.3.2-r0 (`Zlib`, listed with the OS packages).
- **pybind11**: used only to build (the SBOM's scope "excluded").

**Consequences** (accepted with D-171 at the Phase 6 gate; they replace the Phase 1 corrections where those said that the wheels bundle `libimagequant` and FriBiDi):

- The image contains no GPL-3.0 code from Pillow and no FriBiDi. Pillow's only copyleft part in the image is the fribidi-shim, compiled into `_imagingft` (`LGPL-2.1-or-later`).
- The image is still **not** free of GPL components: its Alpine packages include BusyBox, apk-tools, bash, readline, gdbm, and others under the GPL (see *Base image and OS packages*). No project document may claim otherwise.
- The earlier claim that the PyPI wheels omit `libimagequant` was right for these wheels after all; the Phase 1 correction read the SBOM's optional dependencies as the wheels' contents.

### Runtime: transitive (required by `samsungtvws`)

`requirements/runtime.txt`, which carries hashes, is authoritative. The pins below are the current releases. The license files are from PyPI metadata and are re-checked when pinning.

| Package | Source, pin, and wheel | SPDX (license files) | Use | Required by | Obligations |
| --- | --- | --- | --- | --- | --- |
| `websocket-client` | PyPI `==1.9.2`, `py3-none-any` | `Apache-2.0` (`LICENSE` only) | dyn, redist | `samsungtvws` | License text; no NOTICE |
| `requests` | PyPI `==2.34.2`, `py3-none-any` | `Apache-2.0` (`LICENSE`, `NOTICE`) | dyn, redist | `samsungtvws` | License text **and `NOTICE`** |
| `charset-normalizer` | PyPI `==3.5.1`, `cp3xx-musllinux_1_2_{aarch64,x86_64}` | `MIT` (`LICENSE`) | dyn, redist, native | `requests` | License text |
| `idna` | PyPI `==3.20`, `py3-none-any` | `BSD-3-Clause` (`LICENSE.md`) | dyn, redist | `requests`, `yarl` | License text |
| `yarl` | PyPI `==1.25.1`, `cp3xx-musllinux_1_2_{aarch64,x86_64}` | `Apache-2.0` (`LICENSE`, `NOTICE`) | dyn, redist, native | `samsungtvws` | License text **and `NOTICE`** |
| `multidict` | PyPI `==6.9.1`, `cp3xx-musllinux_1_2_{aarch64,x86_64}` | `Apache-2.0` (`LICENSE`) | dyn, redist, native | `yarl` | License text; no NOTICE |
| `propcache` | PyPI `==0.5.4`, `cp3xx-musllinux_1_2_{aarch64,x86_64}` | `Apache-2.0` (`LICENSE`, `NOTICE`) | dyn, redist, native | `yarl` | License text **and `NOTICE`** |

`certifi` is also required by `requests`; it is recorded above as a direct dependency.

The venv is created `--without-pip`, so pip and the packages it vendors are not part of the image.

### LGPL-3.0 obligations for `samsungtvws`

These come from general knowledge of the license; qualified review is recommended.

- State prominently that the image contains `samsungtvws` under LGPL-3.0.
- Include the LGPL-3.0 and GPL-3.0 texts and the package's copyright notices.
- Keep the library replaceable. It stays an unmodified, separately installed package, and the documentation explains how to substitute another version.
- **Attach** the exact sdist to every release (D-135).
- Never modify or vendor the library, and never impose terms that restrict modifying it.

**Provenance caveat (R-04).** Versions before 2.7.0 declared inconsistent licenses: MIT metadata, but a README saying GPL-2.0 for 1.7.0–2.6.0. Excluding those versions does not settle code carried forward into 3.0.6. Phase 5 checks the 3.0.6 sdist's `LICENSE` file and source headers for retained MIT notices or a relicensing statement, and records the result. The pre-release licence review also covers this. *Phase 5 result (D-160):* the 3.0.6 sdist holds only the LGPL-3.0 text and LGPL-3.0 headers; no MIT notice, GPL-2.0 statement, or relicensing statement was found.

### Base image and OS packages

**Verified** in Phase 6 from the built image, for both architectures (D-171, accepted at the Phase 6 gate; `scripts/image_inventory.py`). The complete list, with apk's licence field for each of the 61 packages, is in `THIRD_PARTY_NOTICES.md`.

| Component | Version | SPDX | Notes |
| --- | --- | --- | --- |
| `ghcr.io/home-assistant/base` | `3.24-2026.08.0@sha256:93ef607824e3f27e868f11b10938283a98bf880ed57bcf8eaa81c6c2d521f6f5` | per component | Alpine 3.24.1; 50 apk packages; the app adds `python3` and its closure (11 packages) |
| BusyBox (`busybox`, `busybox-binsh`, `ssl_client`) | 1.37.0-r31 | `GPL-2.0-only` | Copyleft; source via D-135 |
| bash | 5.3.9-r1 | `GPL-3.0-or-later` | Copyleft; in the base for bashio, not used by the app |
| readline | 8.3.3-r1 | `GPL-3.0-or-later` | Copyleft; in the base (bash); also linked by Python's `readline` module, which the app does not import |
| gdbm | 1.26-r0 | `GPL-3.0-or-later` | Copyleft; a dependency of `python3` (the `dbm.gnu` module), not used by the app |
| apk-tools, libapk | 3.0.6-r0 | `GPL-2.0-only` | Copyleft |
| alpine-baselayout, -data | 3.7.2-r1 | `GPL-2.0-only` | Copyleft |
| scanelf (pax-utils) | 1.3.9-r1 | `GPL-2.0-only` | Copyleft |
| musl; musl-utils | 1.2.6-r2 | `MIT`; `MIT AND BSD-2-Clause AND GPL-2.0-or-later` | C library; utilities |
| libgcc, libstdc++ | 15.2.0-r5 | `GPL-2.0-or-later AND LGPL-2.1-or-later` (apk field) | GCC's runtime libraries; their runtime-library exception is checked in the licence review |
| other copyleft or dual-licensed libraries | per package | keyutils-libs, libcom_err, libidn2, libunistring, userspace-rcu, xz and xz-libs, zstd-libs | See `THIRD_PARTY_NOTICES.md` |
| `python3` and its `pyc` packages | 3.14.8-r0 | `PSF-2.0` | The interpreter; the app image removes the pip wheel that it bundles for `ensurepip` (D-167) |
| OpenSSL (`libcrypto3`, `libssl3`) | 3.5.7-r0 | `Apache-2.0` | |
| SQLite (`sqlite-libs`) | 3.53.4-r0 | `blessing` | |
| zlib | 1.3.2-r0 | `Zlib` | Also the zlib that Pillow loads |
| ca-certificates, -bundle | 20260611-r0 | `MPL-2.0 AND MIT` | The system CA store; the gateway uses `certifi` |
| tzdata | 2026c-r0 | "Public-Domain" (apk's notation; not an SPDX identifier) | |
| s6-overlay (outside apk) | 3.2.3.0, with execline 2.9.9.0, s6 2.15.0.0, s6-linux-init 1.2.0.1, s6-linux-utils 2.6.4.1, s6-overlay-helpers 0.1.2.2, s6-portable-utils 2.3.1.2, s6-rc 0.6.1.0 | **to verify** (upstream, GitHub-hosted) | The init system; the image holds no licence text |
| tempio (outside apk) | 2026.07.0 (Go 1.26.5; 11 Go modules) | **to verify** (upstream, GitHub-hosted) | A Home Assistant template tool; not used by the app |
| bashio (outside apk) | not recorded in the image | **to verify** (upstream, GitHub-hosted) | Not used by the app |

### Development-only (not shipped)

| Package | Source and constraint | SPDX (as published) | Purpose |
| --- | --- | --- | --- |
| `uv` | PyPI `==0.12.19` (installed in the git-ignored `.tools/`; wheel SHA-256 `5da0401c0898b5fe767968f5a72f27525276b119d69e0c7c25b721f63ecef650`, checked against PyPI) | `MIT OR Apache-2.0` | Lock and export (D-128, D-142) |
| `pytest` | PyPI `>=9.1,<10`; locked 9.1.1 | `MIT` | Tests |
| `iniconfig` | PyPI 2.3.0 (via pytest) | `MIT` | — |
| `packaging` | PyPI 26.3 (via pytest) | `Apache-2.0 OR BSD-2-Clause` | — |
| `pluggy` | PyPI 1.6.0 (via pytest) | `MIT` (license field) | — |
| `Pygments` | PyPI 2.21.0 (via pytest) | `BSD-2-Clause` | — |
| `pytest-cov` | PyPI `>=7.1,<8`; locked 7.1.0 | `MIT` | Coverage |
| `coverage` | PyPI `>=7.16,<8`; locked 7.16.1 | `Apache-2.0` (ships a `NOTICE.txt`; not distributed) | Branch coverage |
| `ruff` | PyPI `>=0.16,<0.17`; locked 0.16.9 | `MIT` | Lint and format |
| `mypy` | PyPI `>=2.3,<3`; locked 2.3.1 | `MIT` | Typing |
| `typing-extensions` | PyPI 4.16.0 (via mypy) | `PSF-2.0` | — |
| `mypy-extensions` | PyPI 1.1.0 (via mypy) | `MIT`: the official wheel contains a `LICENSE` that states the MIT licence explicitly (Codex final gate review). Development only; not shipped. | — |
| `pathspec` | PyPI 1.1.1 (via mypy) | `MPL-2.0`, per its official PyPI project metadata and licence documentation (Codex final gate review). Development only; not shipped. | — |
| `librt` | PyPI 0.15.0 (via mypy) | `MIT` | — |
| `ast-serialize` | PyPI 0.11.2 (via mypy) | `MIT` | — |

### Build and CI tooling (not shipped)

| Tool | Version | SPDX | Recorded and approved before |
| --- | --- | --- | --- |
| Docker Desktop (local only) | 4.91.0, with Engine 29.8.0, containerd 2.3.4, runc 1.4.3 | Docker Desktop: proprietary (Docker's subscription terms); Engine, containerd, runc: `Apache-2.0` (not re-read; GitHub-hosted) | Phase 6: its start was approved by the user on 2026-10-02 |
| Docker Buildx, BuildKit | 0.37.0, 0.33.0 (bundled with Docker Desktop) | `Apache-2.0` (not re-read; GitHub-hosted) | Phase 6 (D-170) |
| QEMU user-mode emulation | bundled with Docker Desktop; **not used**: `amd64` runs under Apple's Rosetta on this host | — | Phase 6 (D-170) |
| SBOM generator (for example Syft) | **none**; `scripts/image_inventory.py` records the image instead (D-171). A generator needs its own approval. | — | Phase 6; Phase 9 if a release needs one |
| Home Assistant builder composite actions (`build-image`, `publish-multi-arch-manifest`) | not used; native validation plus LABEL-only annotation of its actual checked image (D-193) | — | Phase 9 design refinement; none executed |
| Cosign (release only; not shipped) | 3.1.3, exact ARM/Intel binary SHA256s in D-193 | `Apache-2.0` | D-193, prepared within authorized Phase 9; not executed yet |

The documentation for these tools is largely GitHub-hosted, so it is read only once GitHub access is approved.

### Considered and not proposed

| Package | Reason |
| --- | --- |
| `httpx` 0.28.1 (`BSD-3-Clause`) | Would add a second HTTP stack. The stable line is about 21 months old, and the 1.0 pre-releases are an API rewrite without license metadata. |
| `pip-tools` 7.6.1 | Its PyPI license field is only "BSD", not an SPDX expression. `uv` is preferred. |
| Alpine `py3-pillow` | Older than the PyPI release and lags on security fixes. It also links GPL-3.0-or-later `libimagequant`, just as the PyPI wheel bundles it, so it gives no licensing advantage. *Phase 6 (D-171): the PyPI `musllinux` wheels do not bundle `libimagequant`; the statement about `py3-pillow` was not re-checked.* |
| lxml, BeautifulSoup | Not needed (D-127). |
| `samsungtvws` extras (`async`, `encrypted`, `cli`) | Not needed. |

## Risk register

L = likelihood, I = impact; H = high, M = medium, L = low.

| ID | Risk | L / I | Mitigation | Residual / owner |
| --- | --- | --- | --- | --- |
| R-01 | Google Arts & Culture has no documented API, and its terms and image rights conflict with automated retrieval | — | **Excluded from the beta** (Q-01, resolved). Its researched status is kept. | Only if an official API appears |
| R-02 | Google Arts & Culture page formats change | — | Not applicable while the source is excluded | — |
| R-03 | The Samsung art protocol is undocumented and changes with firmware. The TLS or certificate behaviour and the token scope are unknown. The library connects without verifying the TV's certificate (D-161), so a machine that takes over the TV's address on the LAN could learn the token. | M / H | Isolated, pinned library; surface taken from the installed package (D-161); marker-based classification; the connect guard (D-162); trust-on-first-use pinning is feasible; at the Phase 5 gate (2026-10-02) the decision was deferred until the TV's certificate is observed in the supervised Phase 8 test; Phase 8 live validation | Phase 8 |
| R-04 | `samsungtvws` has a single maintainer, an undocumented 3.x art API, LGPL obligations, and inherited licence provenance | M / M | Hash pin; contract tests; D-135; the Phase 5 check of `LICENSE` and headers found only LGPL-3.0 (D-160) | Licence review |
| R-05 | Bing: undocumented endpoint, a `robots.txt` image-path rule, and restrictive Services Agreement terms | — | **Excluded** (Q-17, resolved) | — |
| R-06 | Loading feedback may be missed when the app cannot notify its timer | M / M | D-176 removes Running dependency. Green delivery, no-match and graceful stop acknowledged completion after cleanup; an unset notification target proved the independent 150 s expiry without manual cancel. HTTP failures/no retries are tested offline. A failed Supervisor start was not forced on Green; expiry also bounds that case. Public-slug/clean-install verification remains Phase 9. See PHASE8_REPORT.md. | Phase 8 correction verified; Phase 9 release setup pending |
| R-07 | **Preview freshness** (release-blocking). Local File refresh timing is not a universal guarantee. | H / H | D-140 candidate 1 selected on HA 2026.9.4 Green: native refresh of atomically replaced latest.jpg, verified on repeated card, actual event-automation, app-page and no-match runs without reload. Recovery refresh observed within a 14-second bound. Evidence: PHASE8_REPORT.md. Loading feedback is separate and remains unresolved. | Phase 8 freshness evidence complete for observed setup; monitor regression across HA versions |
| R-08 | Image decoder vulnerabilities | M / H | Header limits; format allowlist; unprivileged, memory-limited worker; allowlisted environment; bytes-only results; prompt updates | Ongoing |
| R-09 | Memory pressure during decode | M / M | Pixel caps (64 MP JPEG, 40 MP PNG); colour work after resizing; 1 GiB `RLIMIT_AS`; beta renditions ≤ 3400 px. §11.1 and D-121 estimated the worst case at ≈ 450–550 MiB. **Measured in Phase 5** (`scripts/measure_prepare.py`, macOS arm64, the production `prepare` task in a real worker, 2 runs each, every source within 1–4 MiB of the 40 MiB cap, 3840×2160 canvas, **without `RLIMIT_AS`**, which macOS cannot set). Peak resident memory and wall time: 64 MP JPEG baseline 165 MiB and 0.5 s; progressive 318 MiB and 1.1 s; progressive 4:4:4 531 MiB and 1.1 s; CMYK panorama (19 999×3 200) in `cover` 350 MiB and 0.6 s; **progressive CMYK panorama in `cover` 839 MiB and 1.4 s**; progressive 4:4:4 panorama in `cover` 717 MiB and 1.3 s; behind a header flood just under the D-144 caps 190 MiB and 0.4 s; 40 MP PNG RGB 281 MiB, RGBA 434 MiB, palette with transparency 479 MiB, grey with a transparent key 478 MiB, 16-bit grey 451 MiB, behind a chunk flood 297 MiB, each ≤ 0.7 s. The progressive coefficient buffers, which the estimate left out, make the progressive cases the heaviest. A progressive JPEG with very many scans was not generated (Pillow's encoder has a fixed scan script). The address space a worker uses exceeds its resident memory, so the heaviest cases may fail with `memory` under the real 1 GiB limit. *Phase 5 gate (2026-10-02):* the 1 GiB limit stays for now, and any change is decided only from the measurement under the real limit. The same script runs under the real `RLIMIT_AS` in the Linux container, as root (D-165; a condition of the gate, mandatory before any live test on the Home Assistant Green), and on the Green in Phase 8, which is several times slower; if preparation exceeds about 12 s there, the local-media pixel caps are lowered. **Measured in Phase 6 under the real 1 GiB `RLIMIT_AS`** (aarch64 container, as root, workers at 65534; D-170): all 13 cases succeed; the heaviest, the progressive CMYK panorama in `cover`, peaks at 766 MiB of address space (754 MiB resident) in 1.4 s, leaving 258 MiB. The Phase 5 resident figures were inflated by `ru_maxrss`, which on Linux counts the parent's memory before `exec`; the worker now reads `VmHWM` and `VmPeak`. The 1 GiB limit stays (D-170, accepted at the Phase 6 gate). Under Rosetta (amd64 on this host) every process has about 278 MiB more address space, and the heaviest case then fails, reported as `decode`, because Pillow reports libjpeg's failed allocation as a broken data stream (D-170). *Phase 6 gate (2026-10-03):* the native `amd64` measurement is mandatory before an `amd64` version is published, at the latest in Phase 9. | Phase 8 (the Green); Phase 9 (native `amd64`) |
| R-10 | Home Assistant platform churn | M / M | Follow the current docs; re-check them in Phases 6 and 9 | Phase 6/9 |
| R-11 | Pairing friction: prompts on each connection, and the 20 s pairing wait inside the 40 s TV phase | M / M | Token persistence; self-healing reset; *First Time Only* setting; a clear message to accept the prompt and run again | Documentation; Phase 8 |
| R-12 | TV off or on another subnet gives `tv_unreachable` | M / L | Actionable messages; documented network requirement | Documentation |
| R-13 | Restrictive filters or small folders exhaust the available works, giving frequent `no_match` | H / L | Distinct hints; exhausted-page and skip cache; documented behaviour | Accepted |
| R-14 | Branding: "Frame" is part of Samsung's product name | M / M | D-101 review; factual compatibility wording only | User (D-101) |
| R-15 | Watchdog `os._exit` skips normal cleanup | L / M | The worker group is killed first; `PR_SET_PDEATHSIG`; RAM `/tmp`; startup sweep; timing test | Accepted |
| R-16 | Supervisor handling of exit codes and Watchdog restarts for `once` apps is undocumented | M / M | D-133; the documentation says to keep the Watchdog off | Phase 8 (Q-07) |
| R-17 | The image redistributes copyleft OS packages, LGPL `samsungtvws`, and the copyleft components bundled in Pillow (R-25) | M / M | SBOM; D-135; minimal OS packages; copyleft surface is a D-130 criterion. *Phase 6 (D-171):* the image's inventory is taken from the image itself; its copyleft parts are `samsungtvws`, Pillow's fribidi-shim, and the GPL and LGPL Alpine packages. Still to verify before a release: the licences of s6-overlay, tempio with its Go modules, and bashio (in the base image), whose texts the image does not carry; libbsd's and libmd's were read from the official Alpine package directory (Codex, reported on 2026-10-03), and libmd's "Public Domain" is not an SPDX identifier | Phase 7/9 licence audit |
| R-25 | **The Pillow wheels bundle GPL-3.0-or-later `libimagequant` 4.4.1 and LGPL-2.1-or-later FriBiDi 1.0.16.** The distributed image therefore contains GPL-3.0 code, and the runtime is not GPL-free. | H / M | Correct inventory (observed SBOM); D-135 source availability; qualified licence review as a release gate; authoritative re-inspection of the exact runtime wheels once the Python version is fixed; Apache-2.0 scoped to project code only (D-102) | **Closed** at the Phase 6 gate (2026-10-03), with D-171: the exact runtime wheels contain neither `libimagequant` nor FriBiDi; the SBOM lists both only as optional dependencies. The image's remaining copyleft is covered by R-17. |
| R-18 | Provider terms or rate limits violated by accident | L / H | Allowances; 1 s pacing; 403/429 stop; cache; honest headers | Phase 3 review |
| R-19 | Art Institute renditions (1686 px) look soft after upscaling by up to ≈ 2.28×; images can be unpublished | H / M | Honest documentation; HTTP 404 moves to the next candidate; Cleveland renditions (≈ 1.13×) are an in-beta alternative | Accepted |
| R-20 | Provider documentation drifts. Examples: Cleveland's banner date is older than its changelog, and the Cleveland image host appears only in example URLs. | M / L | Re-verified on 2026-09-27 (D-146); re-check before the Phase 8 live test and before each release | Phase 8, each release |
| R-21 | The media browser may not be able to upload into `/media/frame_gallery/library` | M / M | The app creates the folder; the hint names its location; Phase 8 verifies uploads | Phase 8 |
| R-22 | **Provider identifier stability.** Neither the Art Institute nor Cleveland documents its record IDs as permanent. | L / M | IDs validated against patterns; Cleveland's accession number kept as metadata; history and ledger keyed by the documented ID; re-checked when documentation drifts | Phase 3 |
| R-23 | The **Cleveland API terms** reserve future keys, transaction limits, and IP logging | M / M | Room for an optional key (`password` option); 401/403 treated as a stop; conservative pacing; the source stays optional | Monitor |
| R-24 | The **uncertainty quarantine** holds back works that never actually reached the TV (for example after a power loss before upload) for the 30-day quarantine period | M / L | Intents are removed whenever no `upload_started` was seen; the period is documented (Q-23, accepted); large catalogues are unaffected | Accepted |
| R-26 | **Local tests run a different Pillow build.** Phase 2 tests use the macOS `arm64` Pillow wheel and CPython 3.12.14; the runtime uses the Linux `musllinux_1_2` wheels, with other bundled library builds, on the container's Python. Rendering bytes and edge-case behaviour may differ. | M / M | The imaging tests assert properties (size, baseline, components, pixels, metadata) rather than byte-exact output; Phase 6 runs the full suite inside the container image for both architectures; CI covers 3.12–3.14 (Phase 9). *Phase 6:* the whole suite runs in the image on both architectures, on its Python 3.14.8 and the `musllinux` Pillow, as a non-root user and, for the root checks, as root (D-170) | Phase 9 (CI) |
| R-27 | **No pre-emption before Phase 5.** The Phase 2 in-process executor cannot interrupt a hung decode, so the 15 s preparation limit and the 70 s and 120 s bounds hold only when tasks return. A timeout is detected after the fact. | L / M | Resolved in code in Phase 5: the process executor's kill timer ends a worker at its timeout (D-163); the in-process executor remains for tests only. In force since Phase 6: the entry point builds the process executor (D-166). The watchdog (130 s) remains the last resort | Resolved (Phase 6) |
| R-28 | **The credential-pattern redaction is heuristic.** It catches common forms of unregistered secrets but not every serialization (D-145). | L / M | Every real secret (the Supervisor token, the TV token) is registered with the redactor and redacted in all its encodings; worker output passes through the parent's formatter; H3 tests cover both layers; new secrets must be registered where they enter | Ongoing (Phases 3, 5) |
| R-30 | **Another client's upload.** The library takes the first `image_added` event on the art channel as its own (D-161). If another client (for example the SmartThings app) uploads at the same moment, that client's content ID would be selected instead of ours: the TV then shows the other client's image, while the run reports `delivered` and history, `current.json`, and the preview name our work (against E1 and E10). Our upload stays on the TV. | L / L | Rare timing; the ledger still records our upload, so the work is not uploaded again; the content ID is used only for the selection inside the worker and is never stored or logged; no action on the TV deletes by content ID. Recorded as a known limitation. | Phase 8 |
| R-31 | **A worker taken over by an exploit.** A parser exploit in the image worker would run as uid 65534 under the D-163 limits, but it would still have the container's network (the AppArmor profile allows `inet`) and could write to the RAM-backed `/tmp` and `/dev/shm`, which `RLIMIT_AS` does not count. | L / H | Unprivileged; `RLIMIT_NPROC` 0, so no process survives it; file-size and descriptor limits. No secret it could reach: the pairing token is held by the root parent and in `/data/tv/<address>.token` (mode 0600, owned by root; the television worker gets it only through its request pipe), the image worker never runs at the same time as the television worker (each worker is killed and reaped before the next task starts), and its environment is a fixed allowlist. The television worker uploads only bytes with the parent's hash. Phase 9: AppArmor child profiles per worker (confirmed for Phase 9 at the Phase 5 gate, 2026-10-02) | Phase 9 |
| R-29 | **Very old works can come back.** History keeps the latest 20 000 delivered works, and the ledger 20 000 entries (D-153, D-154). When a bound is reached, the oldest entry is dropped, and that work is no longer excluded, so it could in theory be shown again. At one artwork a day this first happens after about 55 years; at one an hour, after about 2.3 years; at one every 15 minutes, after about 7 months. | L / L | Accepted for the first beta at the Phase 4 gate; stated in the user documentation's known limitations (Phase 6). Every more recent work stays excluded. | Accepted |
| R-32 | **A Supervisor build on the Green.** Until images are published (Phase 9), the Supervisor builds the app on the device from the Dockerfile. That build needs the same network sources (the base image, the Alpine package source, PyPI), may take several minutes on the Green (not measured yet), and fails if one of them is unreachable. It also fails once Alpine replaces the pinned `python3` build, because Alpine's stable branch keeps only the newest one, and the packages `python3` pulls in can differ from the inventory (D-167). | M / M | Pinned inputs and hashes make a failed build visible, not silent; the pin follows D-128's monthly review with a new inventory; Phase 8 settles the install route (Q-21) and measures the build; published images remove the on-device build in Phase 9 | Phase 8 |
| R-33 | **The base image's tools outside apk.** s6-overlay, tempio, and bashio come with the Home Assistant base image without licence texts or package metadata; their versions are recorded from the image (D-171), their licences not yet. | L / M | Read the licences from the upstream projects once that access is approved; the licence review is a release gate (D-135) | Phase 9 licence review |

## Open questions

### Resolved in the Codex review of `d42adf5`

| ID | Resolution |
| --- | --- |
| Q-01 | Google Arts & Culture is **removed from the beta scope**. Its researched status stays documented, and undocumented or `robots.txt`-incompatible access is never implemented. |
| Q-02 | Replaced by the 120 s total deadline and its phase split. `no_match` finishes within 70 s (D-114). |
| Q-15 | Only the **installed** `samsungtvws` 3.0.6 distribution is inspected (D-104). |
| Q-16 | The app starts **without `host_network`**. Home Assistant Green-to-TV connectivity is verified in Phase 8 before any change. |
| Q-17 | Bing is **excluded**. |
| Q-18 | The specification is amended in this revision: providers, the filter model, the deadline, the upload ledger, and preview freshness (`PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` amendment logs). Item 4 was resolved in the final gate review (see below). |
| Q-20 | The 30-probe limit means **30 remote dimension requests**. Local header inspection has its own bounded allowance of 300. |

### Resolved in the Codex final gate review of `9352e77`

| ID | Resolution |
| --- | --- |
| Q-03 | **Square band** stays 0.95–1/0.95. **Strict near-16:9** becomes ±1 % in log ratio, `abs(ln(r / (16/9))) ≤ ln(1.01)`, about 1.760–1.796; this may be revisited after Phase 8 visual testing. The **maximum upscale** stays 2.5× (D-116). |
| Q-04 | The proposed bounded local-media fingerprint identifier is accepted (D-118). |
| Q-08 | The Art Institute of Chicago is the default remote source (D-120, D-123). |
| Q-09 | Accepted: the UI-created card, the script, the 150-second timer helper, the enabled Running sensor, and the optional post-run refresh automation (§16.3, D-140). |
| Q-11 | No fallback in `cover` mode. Fallback is available only with `landscape_only` and `contain` (D-117). |
| Q-12 | Only IPv4 literals in **RFC 1918** private ranges are accepted. `169.254/16` link-local is rejected, as are loopback, unspecified, multicast, broadcast, and the container and Supervisor internal networks. `192.168.178.30` stays solely the user-supplied Phase 8 test value (D-125). |
| Q-18 item 4 | The architecture order is adopted: record the confirmed sent history before publishing the preview (D-113). `PRODUCT_SPEC.md` is amended. |
| Q-23 | The uncertainty-quarantine period is **30 days** (D-137). |

### Resolved at the user's approval of Phase 3 (2026-09-27)

| ID | Resolution |
| --- | --- |
| Q-14 | Small, curated, versioned vocabularies, built from the re-checked official documentation only. Labels are distinct across the museums. Normalization, aliases, and uniqueness are tested. A category that the documentation does not map reliably is left out, and the limitation is documented (D-146). |
| Q-22 | The project contact is `volkue@gmail.com` (D-119 as amended). Phase 3 still makes no live API request; the real address is transmitted only in a later, explicitly approved live request. Tests use a placeholder. |

### Resolved at the Phase 3 gate (2026-09-27)

| ID | Resolution |
| --- | --- |
| Q-25 | **Option (a), final.** The first beta ships without a colour filter, and the Art Institute supports only the period filter; Cleveland supports department and period. No live Art Institute observation is approved: neither `category-terms` nor any other provider API endpoint is called. Unsupported filters are reported as B8 requires. `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` (B2, C1) are amended to apply only to the filters the selected source supports. |

### Resolved at the Phase 6 gate (2026-10-03)

| ID | Resolution |
| --- | --- |
| Q-06 | **Not in the beta** (D-172). Uninstalling the app removes its `/data` folder, with the history, the upload ledger, the quarantine, the cache, and the pairing key, so reinstalling is the reset; a new pairing happens on its own once the TV rejects the stored key. `DOCS.md` explains this under "Starting over", and Phase 8 confirms that an uninstall removes `/data`. |
| Q-10 | **Not in the beta** (D-172). The parent stays root: it drops every worker to 65534 and hands it the workspace, with the six capabilities of D-168. Revisited in Phase 9 with the per-worker AppArmor child profiles (R-31). |

### Open

| ID | Question | Recommendation | Needed by |
| --- | --- | --- | --- |
| Q-05 | JPEG parameters (quality 90, standard subsampling, 15 MiB ceiling) | Start here; tune in Phase 8 | Phase 8 |
| Q-07 | Confirm D-133: how `once`-app exits are shown, and how the app Watchdog reacts | Keep D-133; observe in Phase 8 | Phase 8 |
| Q-13 | The final public repository URL, which determines the slug shown in the dashboard YAML | Decide with D-101 | Phase 9 |
| Q-19 | `hassio.app_start` is admin-only. Test the non-admin paths: a script, the Running switch, `continue_on_error`, a mistyped slug. | Document the admin requirement; test in Phase 8 | Phase 8 |
| Q-21 | Install route for Phase 8: (a) copy the folder into `/addons` through a file-share app; (b) a temporary private repository; (c) a development image push | (a) | Phase 8 |
| Q-24 | Cleveland colour filtering by local analysis, for example of the documented 900 px web rendition, counted against the existing download allowance and the content-window time budget, not against the 30 remote dimension requests. Only if it fits the same download and time budgets. | Defer until after the beta | After the beta |

## Review records

### Phase 7 coordination note (user, 2026-10-03)

- During Phase 7 a message reached this session in the user's chat, signed as a coordination note from Codex acting for the user. It said that the user had authorized Codex to coordinate this session for the project, and that Phase 7 continues unchanged, without additional review loops without a concrete finding; Codex reviews the final report and the local results; the work stops at the Phase 7 gate with the commit ID, the test results, and the remaining release prerequisites. The Home Assistant Green, the television, live provider access, and publication stay locked, and the Git identity stays Alexander Wilke `<volkue@gmail.com>`.
- The note changed no scope; Phase 7 followed it.

### Phase 6 gate decision (user, 2026-10-03)

- After the Codex review and its follow-up checks (see below), the user accepted Phase 6. D-166 to D-172 are accepted, including the unchanged 1 GiB `RLIMIT_AS` of the image worker (D-170).
- The native `amd64` memory measurement stays mandatory before an `amd64` version is published; it runs at the latest in Phase 9.
- The qualified licence review (D-135, with the tools outside apk, R-33, and the form of libmd's "Public Domain" part) and the enforcement of the AppArmor profile (D-168) stay release prerequisites.
- With D-171, R-25 is closed, as its row proposed; with D-172, Q-06 and Q-10 are resolved as proposed.
- The outdated line under *Known open decisions* in `STATUS.md`, which still counted the licences of libbsd and libmd as unread, is corrected.
- Phase 7 is authorized under these conditions:
  - only Phase 7 of `TASKS.md`: offline validation with the existing local environments and container images, failure-path tests, and a release-candidate report;
  - no new features, and no additional review loops without a concrete finding;
  - no access to the Home Assistant Green, the television, or a provider API; nothing created, pushed, or published on GitHub; a stop at the Phase 7 gate.
- The decision reached this session as a pasted text, which the user confirmed as their own decision.

### Codex follow-up checks at the Phase 6 gate (external, reported on 2026-10-03)

The user had narrowly approved these checks; Codex ran them, and reported the results to this session. The repository stood unchanged and clean at `4b21f9d` meanwhile.

- **Licences of libbsd and libmd** (D-171), from the official Alpine package directory: libbsd 0.12.2-r0 `BSD-3-Clause` (https://pkgs.alpinelinux.org/package/v3.20/main/x86/libbsd); libmd 1.1.0-r0 "BSD-3-Clause AND BSD-2-Clause AND ISC AND Beerware AND Public Domain" (https://pkgs.alpinelinux.org/package/v3.20/main/x86_64/libmd). "Public Domain" is not an SPDX identifier, and the documents say so instead of presenting it as one.
- **AppArmor syntax** (D-168): `apparmor_parser -Q -T` accepted `frame_gallery/apparmor.txt` in a temporary aarch64 container with exit code 0. The only warning concerned the kernel's AppArmor interface, which the container lacks. This was a syntax check only, not a test of the enforcement on the Home Assistant Green.
- At the user's request, the Phase 6 documents and the inventory were corrected to these results, the outdated Pillow statements in `ARCHITECTURE.md` with them, and the native amd64 memory measurement is recorded as open (D-170). Claude did not re-run the checks and used no network for this.

### Phase 6 internal review (Claude, before the gate)

An independent review of the Phase 6 commits `ff64da8` to `60aed51` ran as a workflow of 8 agents: four reviewers (the entry point; `inspect` over descriptors and the batching; the container image and the packaging; the documents and the inventory against the evidence), each followed by an adversarial verifier. They worked only in the repository, on the container-check outputs in `build/container-checks/`, and on the Pillow wheels in the session's scratch directory, without network access, Docker, or changes to the repository. Of 20 findings, 19 were confirmed and 1 refuted (an unretained earlier timing, which was not shown to be false). By severity after verification: 3 high, 7 medium, 9 low. Two findings were reported twice (the bundled pip wheel; the route table).

- **High.**
  - The candidate allowance ended the pass past the place that measured candidates waiting for a batch: in a library of more than 150 usable images the last batch was lost. Fixed in `4b6a0fd` (D-169).
  - A build without a target, as the Supervisor makes it, produced the test stage, not the app image. Fixed: `runtime` is now the last stage (D-167).
  - The app image held the pip wheel that Python bundles for `ensurepip`, with the packages pip vendors, which neither D-167 nor the inventory listed. Fixed: the app installs `python3` in its own layer and removes the wheel there; the inventory now fails on any wheel (D-167, D-171).
- **Medium.**
  - The library's aggregated warning came before the last batch was inspected, so its failed files were never reported. Fixed in `19ab47b` (D-169).
  - A malformed `/proc/net/route` did not fail closed, although D-166 said so. Fixed in `cd7fd88` (D-166).
  - The parent also needs `CAP_FSETID` and `CAP_DAC_READ_SEARCH`; the AppArmor draft and D-172 named four capabilities. The draft now names six (D-168, D-172).
  - The exact `python3` pin stops resolving once Alpine replaces the package, which breaks later builds, on the Green too; the packages it pulls in are not pinned. Recorded (D-167, R-32).
  - TASKS and D-170 reported the amd64 measurement as passed; under Rosetta its heaviest case fails. Corrected (D-170, TASKS).
  - The `pillow.libs` verification was checked off with two licences open, against the condition of `dda877c`. Reopened, and brought to the gate as a proposal (D-171, TASKS); since settled by Codex's follow-up check, which read both licences (see above).
- **Low.**
  - An event too many from an `inspect` worker escaped as `IndexError`; now a `protocol` failure (`19ab47b`).
  - The early read of the preview fingerprints could quarantine `current.json` without the state lock; it now changes nothing (`bdaf81e`).
  - Five options-file messages did not say what to do; they do now (`1af2b26`).
  - `--isolated` does not skip pip's global and site configuration files; the build now also sets `PIP_CONFIG_FILE=/dev/null` (D-167).
  - HarfBuzz is `MIT-Modern-Variant`, and libjpeg-turbo's SIMD extensions add `Zlib` (D-171, the notices).
  - D-167 overstated the labels and the architecture guard; the base's OCI labels are now replaced, and the text is corrected.
  - `DOCS.md` pointed to installation notes that did not exist and missed one `no_match` hint; `DEVELOPMENT.md` now describes a local install, and the hint is listed.
  - `container_check.sh` printed check (a) without asserting it; it asserts it now.

### Phase 5 gate decision (user, 2026-10-02)

- After the Codex gate review, the user accepted Phase 5. D-160 to D-164 are accepted.
- D-165 is accepted on one condition: the Linux and root isolation tests and the worst-case preparation measurement under the real `RLIMIT_AS` run successfully in Phase 6. They are mandatory before any live test on the Home Assistant Green.
- Art API 0.97 stays `unsupported` in the beta.
- TLS pinning is decided only after the TV's certificate is observed in the supervised Phase 8 test (R-03).
- Local image files for `inspect` are passed, where possible, as read-only descriptors that the parent opened, and `inspect` batching is implemented in Phase 6 (D-149, D-164).
- The 1 GiB `RLIMIT_AS` of the image worker stays for now; any change is decided only from the Linux measurement (R-09).
- AppArmor child profiles per worker stay in Phase 9 (R-31).
- Phase 6 is authorized under these conditions:
  - implement only Phase 6 of `TASKS.md`: the Home Assistant app packaging for Home Assistant OS and the Green, the entry point, the options, the multi-architecture container, tests, the authoritative inventory of the exact Pillow runtime wheels, and plain-language installation and dashboard documentation;
  - run the complete quality gates and the Linux, root, and memory checks named above; document the findings and the open risks; make small commits; stop at the Phase 6 gate for the Codex review;
  - no connection to the Home Assistant Green, the television, a provider API, or GitHub; nothing installed, pushed, or published; the existing Home Assistant configuration, `configuration.yaml` in particular, stays untouched;
  - a base-image pull, or any other network access for the build, needs a separate approval that names the registry, the image, and the purpose.
- **Separate approvals for the build** (user, 2026-10-02):
  - starting Docker Desktop, so that Buildx and QEMU can be used; the approval named that Docker Desktop may itself contact Docker's servers, for example to check for updates;
  - the registry `ghcr.io`, image `ghcr.io/home-assistant/base` for `aarch64` and `amd64`: reading its tags, then pulling it pinned by tag and digest, as the base of the app image, for the D-130 checks, and for the tests and the measurement in the container;
  - the Alpine package source (`dl-cdn.alpinelinux.org`) during the build, for `python3` as an exactly pinned apk package;
  - PyPI (`pypi.org`, `files.pythonhosted.org`) for the exact `musllinux` wheels of the runtime and of the test tools, checked against the lock's hashes, for the build, the test suite in the container, and the authoritative Pillow SBOM inventory.
- The decision reached this session as a hand-over text, which the user confirmed as their own instruction.

### Phase 5 internal reviews (before the gate)

- **Design critique** (before the implementation): four lenses (security, architecture, testability, the installed library), each finding adversarially verified. 34 findings were confirmed and 14 refuted; the confirmed ones shaped D-162 and D-163 (for example the token in the channel, the version check before `upload_started`, the new object per connection attempt, the `ready` handshake, `IsolationFailure`, `RLIMIT_NPROC` 0, the exact environment).
- **Implementation review** (of `7a2d8e5` to `779e341`): five lenses (the executor, bootstrap and security, the television task against the installed library, the tests, the documentation), each finding verified by one or two adversarial reviewers. 45 findings were confirmed (none of high severity) and 4 refuted. All confirmed findings were fixed or recorded before the gate, among them: events decoded before a malformed frame are relayed; a worker start or reap interrupted by a stop request leaks nothing; message bodies are held to 64 KiB in both executors; workers start without `site`; a token issued before a failed ready wait is kept and used for the retry; the pairing wait is one deadline; the connection of a failed attempt is dropped; a malformed answer before `connected` is `protocol`; `insufficient_time` before contact gets no hint; the root and Linux checks became runnable in two container passes; the measurement covers the §11.1 cases and fills the source cap; the documentation was corrected where it claimed more than the code does.
- Both reviews worked on this repository and the installed packages only, without network access; the experiments stayed in the session's scratch directory.

### Phase 4 gate decision (user, 2026-09-27)

- The Phase 4 gate is passed, and D-153 to D-159 are accepted. Codex checked the critical state transitions and ran `scripts/check.sh` itself: 3 850 tests passed, with 100 % line and branch coverage.
- The 20 000-entry bound is accepted for the first beta. The consequence, that very old works can in theory come back once they leave history, is documented in plain language (D-153, R-29) and does not block Phase 5.
- Phase 5 is authorized under these conditions:
  - first check and document the version and the LGPL-3.0 obligations of `samsungtvws` 3.0.6;
  - then implement the isolated process executor and the Samsung adapter, tested against simulations;
  - the installed distribution and the official package information may be inspected, and the pinned version may be installed from PyPI into the git-ignored project environment only;
  - no access to the Home Assistant Green or the television; nothing published to GitHub or pushed;
  - reviewable commits, the complete quality gates, and a stop at the Phase 5 gate for the Codex review; Phase 6 does not start.

### Internal review of `4fcab6e` to `ec9e8a4` (Claude, Phase 4)

A second independent reviewer checked the metadata cache, the exhausted-page hints, the preview and the run records, the runner changes, the fixes of `bb25277`, and the integration tests, on a snapshot of `ec9e8a4` in a scratch directory. It fuzzed the five document parsers with 150 000 random documents and ran mutation tests. It found no high-severity defect and no path to a duplicate upload. Six findings were confirmed, all fixed in the commit that follows `ec9e8a4`:

1. **Low-medium.** A page that offered nothing (an empty response, or only unusable works) was hinted as exhausted for 7 days, and a later run then reported "nothing new left" although nothing had been sent.
2. **Low.** Hints rested on `uncertain` entries too, so a quarantined work could stay hidden up to 7 days after its 30-day quarantine.
3. **Low, latent until Phase 8.** With two preview names, a failure on the second name left the names different; each was written and renamed in turn.
4. **Low (documentation).** Missing preview directories were created with 0755 narrowed by the umask, not exactly 0755.
5. **Low (documentation).** The cache's entry bound evicted by last use only; expired entries did not go first there.
6. **Low (documentation and tests).** D-157 called Cleveland's page indices offsets; a docstring said the lock survives a SIGKILL; every fake delivery had the same bytes; §12.4 rows 2, 3, 4, and 6 were covered only against the fake store.

Each fix has a regression test, checked to fail against the defect. The reviewer confirmed as sound: hints only ever remove pages; only a run that holds the lock writes the cache; keys and page numbers per adapter; unchanged requests, laziness, and allowances when a page is kept as a list; the hint classification order; the cache bounds under load (1 000 entries of about 6 KB flushed to 357 entries below 2 MiB); the preview's path checks, mode, and hash re-check (D8); the 16 KiB record bound and the fingerprint merge; the runner's outcomes against §4.2; the `bb25277` fixes; and that the SIGKILL and pruning tests fail when the sweep or the pruning is disabled.

### Internal review of the store commits `a74ba1c`, `1677ccd`, and `f347ffb` (Claude, Phase 4)

One independent reviewer checked crash safety, the reader, the ledger and the state store, the bounds, test quality, and D-153 to D-155. It ran reproductions against a snapshot of `f347ffb`, in a scratch directory, and injected failures into every system call of a ledger write (9 points), a delivered run (27 points), and the store's whole life cycle (113 points). Seven findings were confirmed, all fixed in the commit that follows `5435d06`:

1. **Medium.** A timestamp at the limits of `datetime` (for example `0001-01-01T00:00:00+05:00`) raised `OverflowError` in the reader and the ledger: every run would have ended as `internal_error`, and the file was never quarantined.
2. **Medium (design interaction).** The ledger pruned a work as soon as the history primary held it. If a later run then committed an intent without recording (the television off) and the primary was damaged afterwards, the one-generation-old `.bak` no longer excluded the newest delivered work.
3. **Low.** The sweep pattern missed the `.bak` temporary files of names of 97 to 100 characters (latent).
4. **Low.** A newer-version file over this version's size bound was quarantined instead of ending the run with `state_error`.
5. **Low.** A failed `RunWorkspace.create` left a half-made run directory for the next sweep.
6. **Low (documentation).** D-154 said every ledger write prunes; only the intent write does.
7. **Low (documentation).** Docstrings claimed that only parse failures are quarantined, and that `decode_json` refuses every infinity (`1e400` passed).

Test gaps, all closed: the guard that keeps a damaged primary from becoming `.bak` was tested only in a case where the quarantine had already removed the primary; the loser's lock descriptor was never checked; the ledger's exact byte bound was untested. Each new test was checked to fail against the defect or the mutation that the reviewer used.

The reviewer confirmed as sound: no interleaving leaves the primary missing or a damaged `.bak`; no descriptor leaks under failure injection; memory always matches the files; the committed intent is durable before success is reported; the lock and the sweep order; the reader on links, FIFOs, sockets, directories, deep nesting, invalid UTF-8, and duplicate keys; and the history and ledger bounds, without off-by-one errors.

### Phase 3 gate decision (user, 2026-09-27)

- Q-25 is decided finally with option (a): the first beta ships without a colour filter.
- No live Art Institute observation is approved. Neither `category-terms` nor any other provider API endpoint may be called. Live provider requests stay reserved for a later, explicitly approved phase (Phase 8, D-150).
- Accepted:
  - D-146 to D-152;
  - the Art Institute supports only the period filter in the beta;
  - Cleveland supports department and period;
  - no source supports colour for now;
  - unsupported filters are visibly reported as B8 requires.
- `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` are amended so that B2 and C1 apply only to the filters the selected source supports. Both amendment logs record the change.
- The Phase 3 gate is passed. Phase 4 does not start until it is authorized.

### Internal review of the helper reader `f614256` and local media `8761cca` (Claude, Phase 3)

One independent reviewer checked security, correctness against the requirements, time bounds, and test quality. Proofs used scratch scripts, with local files and a socket pair only. Six findings were confirmed, and all are fixed in the commit that follows `72dba4a` (amendments to D-147, D-148, and D-149):

1. **Medium.** Symbolic links in the middle of a path were followed. A subfolder swapped for a link during discovery made a file outside the library usable, fetchable, and able to bypass preview guard 1.
2. **Low-medium.** An I/O error while copying a library file ended the run as `internal_error` instead of trying the next candidate.
3. **Low.** The token could reach any private LAN address, or a 6to4 or Teredo address embedding a public IPv4 address.
4. **Low.** An inspection cut off by the discovery deadline was reported as a failed inspection of a healthy file.
5. **Low.** A library cut short by the entry limit got the "no usable images" hint.
6. **Low, test quality.** The aggregated-warning test tolerated six examples, and its hostile-name check depended on directory order.

The reviewer confirmed as sound:

- the helper bounds, measured on the real stack: 3 s per stalled read, 10 s for four dripping helpers;
- exactly one WARNING per fallback;
- token hygiene;
- the depth, entry, and size limits, and the D-118 fingerprint;
- FIFO handling;
- the inspection contract;
- sanitized file names;
- the fetch re-check.

### Internal review of the gateway commit `51d9cf3` (Claude, Phase 3)

One independent reviewer checked security, D-115 correctness, time bounds, and test quality, and verified each finding with a scratch script, using only a local socket pair (no network). Five findings were confirmed, and all are fixed in the commit that follows `8761cca` (D-147 amendment):

1. **High.** The exchange timer and the per-read timeout stopped working after a `Connection: close` response, because the connection's socket reference disappears. A dripping peer held one read for the whole drip: 8.3 s against a 0.5 s limit.
2. **Medium.** urllib3 reset the socket timeout to the connect timeout before sending and before reading the headers, so a slow first byte failed early, and body gaps were bounded by the connect timeout.
3. **Medium-low.** urllib3's own warnings put the request URL, query included, and header data into the log.
4. **Low.** Deprecated site-local IPv6 addresses passed the public-address check.
5. **Low, test quality.** `from http import server` was not flagged in the transport module.

The reviewer also confirmed as sound: the URL policy, the TLS setup (a fresh context, `certifi` only, host-name checking on, SNI, the post-handshake check), the address rules, header injection, gzip handling, file creation, the D-115 retry and stop logic, and the deadline semantics.

Writing the fix's real-stack tests exposed a further defect: once a `Connection: close` body was complete, re-clamping the closed socket's timeout raised `OSError`. That would have failed every such response. It is fixed and tested too.

*Disclosure.* To confirm finding 1, the reviewer once ran `grep` on the standard library's `http/client.py`, which lives with the local interpreter outside the repository. That is language source, not predecessor material; after that it checked behaviour only by running scripts.

### User approval of Phase 3 (2026-09-27)

The user approved Phase 3 with these binding decisions and limits:

1. D-141 to D-145 are accepted.
2. D-108, D-112, D-115, D-124, D-127, D-131, D-134, and the Phase 3 adapter details of D-132 and D-136 are accepted.
3. D-119 is accepted with an amendment: no invented or not-yet-existing project URL; the User-Agent is `FrameGallery/<version> (contact: volkue@gmail.com)` until a public URL is decided; the `AIC-User-Agent` may use the same contact; tests keep a clearly recognizable placeholder; the headers switch to the real repository URL before publication.
4. Q-14 is decided as recommended: small, curated, versioned vocabularies from the re-checked official documentation, with labels distinct across the museums; normalization, aliases, and uniqueness tested; no undocumented values; a category the documentation does not map reliably is left out, and the limitation documented.
5. Q-22 is decided: the project contact is `volkue@gmail.com`. Phase 3 makes no live API request; the real address is transmitted only in a later, explicitly approved live request.
6. The direct dependencies `urllib3` 2.8.0 (MIT) and `certifi` 2026.7.22 (MPL-2.0) are approved, installed only into the git-ignored project environment from PyPI, with the lock, the hash-pinned runtime requirements, the inventory, and `THIRD_PARTY_NOTICES.md` updated and the installed package metadata checked.
7. At the start of Phase 3, only the official Art Institute and Cleveland documentation pages may be re-read. No API endpoint, no image or metadata request, and no recorded live observation. Tests use only independently authored or synthetic fixtures. No predecessor project is consulted.
8. Only Phase 3 of `TASKS.md` is implemented. No connection to Home Assistant Green or the television, nothing pushed or published, no container published, and the local backup branch is neither changed nor published.
9. The work is split into small, focused commits: documentation re-check and approved decisions; network gateway and dependencies; Home Assistant helper reader; local media provider; Art Institute adapter; Cleveland adapter; vocabularies, the shared contract tests, and the closing documentation.
10. Every commit is checked for the identity `Alexander Wilke <volkue@gmail.com>`. SatoshiPay, EBMA, and Marcel accounts, addresses, credentials, organizations, and repositories are never used.

At the end, all quality gates run, `STATUS.md`, `DECISIONS.md`, `TASKS.md`, and the licence and dependency documentation are updated, and the work stops at the Phase 3 gate for the Codex review.

### Phase 2 internal review (Claude, before the Phase 2 commit)

**Method.** Five independent review lenses (architecture conformance, Phase 2 scope and acceptance coverage, control-flow correctness, image pipeline and security, test quality), each followed by an independent skeptical verifier who tried to refute every finding with reproductions.

**Result.** 75 findings: 61 confirmed (after merging duplicates across lenses, about 30 distinct issues), 12 refuted, and 2 uncertain.

**Most important confirmed issues, all fixed with regression tests:**

1. A stop request could be swallowed by a generic `except Exception` (for example inside the standard library's logging handler), after which the run still contacted the television. Fixed by D-141 (stop requests).
2. Worker timeouts at the task's own limit were classified as "search limits reached" whenever the clock moved between two readings. Fixed by deciding from deadlines (D-141, item 2).
3. Camera JPEGs with an MPF index (MPO) were refused (D-144).
4. Header floods could make Pillow use gigabytes before any limit applied (D-144, pre-scan).
5. A FINISH after a PRE-STAGE outcome received an already-expired deadline, so a deadline-honouring store would lose the last-run record.
6. After `selected`, an adapter failure skipped RECORD (D-141, item 5).
7. Redaction gaps: truncation before redaction, and missing credential patterns (D-145).
8. Weak or vacuous tests, including the 70 s bound test, deadline propagation, and the boundary and network guards. Each was strengthened and checked to fail against the defect.

**Recorded rather than changed:**

- the §9.1 and §12.1 port shapes (D-141);
- the D-128 lock workflow (D-142);
- the empty provisional vocabulary (D-143);
- the absence of pre-emption before Phase 5 (R-27);
- the uncertain finding on discovery-endpoint 404s, resolved by D-141 item 3.

**Re-verification.** A focused re-verification then checked every confirmed finding against the current code:

- 57 of 63 were fully fixed; the remaining gaps were closed afterwards.
- Adversarial sweeps found two windows in the first stop-request fix, and header-bomb and redaction bypasses in the new code. They led to:
  - the whole-call deferral of D-141;
  - the TIFF-directory bounds of D-144;
  - the extra redaction patterns of D-145.
- The sweeps inject a stop request, directly and as a real SIGTERM, at every Python function entry (11 641 points) and every traced line (5 429 points) across nine delivery and no-match scenarios. Run again against the final design with the production controller configuration (`start_deferred=True`), they report no violations: no marker, ledger write, RECORD, last-run record, or summary line is lost, and nothing is uploaded after an undeferred stop.

### Codex final approval of Phase 1 at commit `dda877c` (external)

**Outcome:** Phase 1 is approved. Phase 2 (core, deterministic selection, and rendering) is authorized; Phase 3 is not.

**Gate adjustment, explicitly approved by Codex:**

- Verification of the remaining lower-risk `pillow.libs` entries (libXau, libXdmcp, Brotli, libbsd, liblzma, libmd, libpng, libsharpyuv, and libzstd) moved from the Phase 2 approval gate to the authoritative Phase 6 runtime-wheel inspection. The exact runtime wheel cannot be selected until the container's Python version is fixed in Phase 6.
- The provisional notices created in Phase 2 keep the known Pillow inventory, including `libimagequant` and FriBiDi.
- Full verification remains mandatory before packaging or publication.
- The GPL/LGPL licence review and the source-availability obligations remain release blockers and are not weakened.

### Codex final gate review of commit `9352e77` (external)

**Outcome:** the architecture changes were accepted. One factual dependency error had to be corrected before Phase 2. Phase 1 stays open until the gate is approved again.

Applied in the documentation-only commit that follows `9352e77`:

1. **Pillow wheel inventory.**
   - Codex inspected the official Pillow 12.3.0 wheels. The earlier claim that the PyPI wheels omit `libimagequant` was false and has been withdrawn.
   - The wheels bundle GPL-3.0-or-later `libimagequant` 4.4.1 and LGPL-2.1-or-later FriBiDi 1.0.16, with its shim. The full SBOM table is recorded, and the additional `pillow.libs` entries are marked for verification.
   - Apache-2.0 covers project-owned code only (D-102). The runtime image is not GPL-free.
   - Both libraries are added to D-135, and the qualified licence review remains a release gate. R-25 records the risk.
   - Pillow 12.3.0 stays proposed. The inspection is repeated against the exact runtime wheels once the Python version is fixed (D-130 check (a)); that result is authoritative.
2. **Development-only rows.** `mypy-extensions` 1.1.0 (MIT) and `pathspec` 1.1.1 (MPL-2.0) were recorded; neither is shipped.
3. **Accepted decisions.** Q-03, Q-04, Q-08, Q-09, Q-11, Q-12, Q-18 item 4 (D-113), and Q-23. See *Resolved in the Codex final gate review of `9352e77`*. `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` were amended where these decisions are normative.

### Codex review of commit `d42adf5` (external)

**Outcome:** the architecture was conditionally accepted. Phase 2 was **not** approved.

The user's decisions and the review's corrections were applied in the revision-2 commit that follows `d42adf5`:

1. **Beta providers.**
   - Google Arts & Culture and Bing were removed, and their researched status was kept.
   - The beta sources are local media, the Art Institute of Chicago, and the Cleveland Museum of Art. Cleveland is now normative (D-136): CC0 records only, and the documented print JPEG only.
   - The filter dimensions are now distinct: source/museum, department/collection, style/period, and colour. They come with an honest capability matrix and visible reporting (D-124).
2. **Runtime.** A 120 s total, split 10 / 60 / 40 / 10 s. All timeouts are clamped. `no_match` finishes within 70 s. The dashboard timer is 150 s. The 30 probes are remote requests (D-114).
3. **Duplicate prevention after an upload.** A TV-upload exclusion ledger, with a write-ahead uncertainty quarantine (D-137), and acceptance items `E7`–`E10`.
4. **Preview.** The Local File camera stays primary, and its platform basis is recorded (D-111). Freshness is release-blocking, with the mechanism selected in Phase 8 (D-140). Collection Image is optional and does not raise the minimum Home Assistant version.
5. **Approved decisions:**
   - `frame_gallery` as the identifier (D-138);
   - Apache-2.0 (D-102);
   - `uv` (D-128);
   - an IPv4 literal for the TV address (D-125); the test value `192.168.178.30` is not hard-coded;
   - no `host_network` at first (Q-16);
   - inspecting only the installed `samsungtvws` (D-104);
   - `contain`, landscape-only, and strict 16:9 as defaults (D-123), with no crop;
   - bounded cleanup and atomic writes (D-106, D-110);
   - the clean-room rules.
6. **Implementation sequencing.** A vertical slice (D-139). `TASKS.md` was updated.

The corrections were checked by cross-reference and consistency checks and by an independent review of the revision.

### Internal multi-agent review of revision 1: findings not adopted

The Phase 1 multi-lens review produced 98 raw findings. The adjudicator confirmed 58, which are incorporated. It listed 7 entries as not adopted: 6 rejections and 1 severity downgrade. They are listed here so they can be challenged:

1. **Pin third-party GitHub Actions to commit SHAs and apply least-privilege job permissions.** Rejected as general CI hardening, not a specification gap. It belongs to the Phase 9 release work (§17.3), where it is expected to be applied.
2. **Log local media by fingerprint only, since filenames are private data.** Rejected: the log is the user's own app log, and the specification's list of forbidden log content does not cover the user's own filenames. Warnings need the path to be actionable.
3. **"Security rating 6" wording.** Rejected: 6 is achievable and is the scale maximum. The nuance that Ingress would also reach 6 does not affect any decision.
4. **The Ingress comparison overstates "session handling".** Rejected as immaterial: the other listed costs, and the one-shot incompatibility, still hold. The row now says "request handling".
5. **Appendix A item `C4` should name the verifying provider.** Rejected: it already names the counting fake gateway.
6. **Drop the `.bak` generation as a simplification.** Rejected as a design preference. The real defects around `.bak` were fixed.
7. **Rate the probe-limit, watchdog-orphan, and memory findings as major.** Downgraded to minor rather than rejected: a dead option, an orphan that needs a second failure, and rare near-cap images. All three were fixed.
