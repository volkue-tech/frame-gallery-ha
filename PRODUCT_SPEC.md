# Product specification

## Product vision

Frame Gallery should let a non-technical Home Assistant OS user install an app, choose artwork preferences, and send a fresh artwork to a compatible Samsung Frame television without SSH, shell access, Docker knowledge, or changes to Home Assistant's `configuration.yaml`.

The initial product is a one-shot app: each start selects and uploads at most one artwork, publishes a dashboard preview, records its history, cleans temporary data, and exits.

## Target environment

- Home Assistant OS with Supervisor/apps.
- Home Assistant Green (`aarch64`) is the primary hardware target.
- `amd64` is the secondary target.
- Compatible Samsung Frame television reachable on the same local network.
- Initial live validation television: `192.168.178.30`, but this value must never be shipped as a default or hard-coded into application logic.

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
5. Reject artworks already present in persistent sent history.
6. Download only the selected artwork at the resolution needed for processing.
7. Prepare a television-ready image according to the configured fit policy.
8. Upload and select the image on the television.
9. Atomically publish the processed image as the dashboard preview.
10. Persist sent history only after a successful television upload.
11. Remove temporary files in both success and failure paths.
12. Exit successfully after one upload, or exit cleanly without changing the television when no eligible image can be found.

The app must never remain indefinitely in a loading or searching state.

## Artwork sources

The architecture must support independent provider adapters. Initial providers:

### Google Arts & Culture connector

- Random artwork discovery.
- Optional color filtering using provider metadata where available.
- Optional museum filtering, including at least Museum of Modern Art and Musée d'Orsay if the provider exposes usable results.
- Optional style or period filtering.
- Combined color, museum, and style/period filters.
- Landscape-only selection enabled by default.
- Strict near-16:9 preference configurable and enabled by default for the first public beta.
- Provider failures, markup changes, empty result sets, and rate limits must have bounded handling and useful logs.
- This connector is experimental unless a stable documented provider API becomes available.

### Bing daily imagery

- Random or recent eligible landscape image.
- Persistent duplicate prevention.
- Provider request failures must terminate cleanly.

### Home Assistant media

- Select supported image files from an app-documented media directory.
- Support JPEG and PNG at minimum.
- Ignore unsupported and corrupt files with a useful warning.
- Persistent duplicate prevention.
- Never treat the generated dashboard preview as a new source image.

The provider interface must allow future museum or open-collection APIs without changing the selection and rendering core.

## Filter inputs

Static app options must always work without Home Assistant helpers.

Supported filters:

- color;
- museum or collection;
- style or period;
- landscape-only;
- strict TV-format preference;
- fit policy.

Optional Home Assistant helper entity IDs may override static color, museum, or style values at runtime. Missing, unavailable, or invalid helper entities must fall back to the static option and must not fail the run.

## Selection limits and fallback

- Every remote request must have a finite timeout.
- Strict TV-format inspection must have a finite probe budget.
- A complete selection run must have a finite total deadline.
- Initial target limits for the beta are 30 dimension probes and 60 seconds total; architecture may make these internal constants or validated advanced options.
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
- The history format must be bounded or compactable and recover gracefully from a partially written or corrupt file.
- Temporary high-resolution downloads must not accumulate.
- The app must not build an unbounded local copy of the provider's entire artwork catalog.
- Cached metadata must have explicit size and age limits.

## Dashboard experience

Documentation must provide complete copy-and-paste-ready Home Assistant dashboard YAML that:

- displays the latest preview image;
- starts the app when tapped;
- shows a temporary loading state that always returns to idle;
- avoids stale browser caching after a successful run;
- works without editing `configuration.yaml`.

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
- Claiming affiliation with Samsung, Google, Microsoft, any museum, or Home Assistant.

