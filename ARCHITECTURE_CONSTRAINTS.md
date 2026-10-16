# Architecture constraints

This file constrains the architecture without prescribing or copying an implementation.

## Required qualities

- Independent design with no predecessor code or structure used as a reference.
- Small, testable components with explicit boundaries between provider discovery, candidate selection, image processing, television communication, persistent state, and Home Assistant runtime integration.
- Dependency injection or equivalent seams for clocks, network clients, random selection, filesystem access, and television transport so tests do not require live services.
- All loops, retries, requests, and subprocesses must be bounded.
- A cancellation or deadline signal must propagate through provider discovery and dimension probing.
- Persistent writes for history and preview must be atomic.
- Temporary files must be owned by a per-run temporary directory and removed reliably.

## Packaging constraints

- Use the current Home Assistant app format and current official build guidance.
- Primary container architecture: `aarch64`.
- Secondary container architecture: `amd64`.
- Additional architectures may be added only after successful builds and dependency verification.
- Use a generic multi-architecture GHCR image reference for releases.
- The Dockerfile must be the build source of truth.
- Do not rely on deprecated Home Assistant builder behavior.
- Pin or constrain runtime dependencies for reproducibility and document upgrade policy.
- Store persistent runtime state under the app data directory provided by Home Assistant.
- Use the Home Assistant media mapping only for documented source and preview paths.

## Technology constraints

- Python is the preferred implementation language unless Phase 1 documents a compelling alternative.
- The current `samsungtvws` package may be proposed as a dependency, subject to LGPL-3.0 compliance and a recorded version.
- Image processing should use a maintained library with explicit licensing and multi-architecture wheel or build availability.
- Network access must use explicit connect/read/total timeouts.
- Provider HTML or metadata parsing must be isolated behind adapters and covered by authored fixtures that do not copy predecessor fixtures.

## Home Assistant constraints

- **2026-10-16 optional background amendment (D-225/D-226):** explicit user
  approval permits an opt-in supervising service, fixed stdin commands and
  ownership-checked GET/POST of only `sensor.frame_gallery_current_artwork`.
  The absent/false option retains the one-shot path. Each delivery and read
  remains bounded and isolated; boot/restart never implicitly sends an image
  in background mode. No additional helpers/configuration/registry writes,
  private HA files, new credentials or Supervisor-management privilege.
- **D-230 experimental exception, explicitly accepted by the user:** automatic
  reads may be armed after a successful explicit delivery only when the
  default-off background mode is enabled. Read-only connections might wake a
  sleeping TV; no-wake behaviour is not validated. Boot/restart never arms
  reads; the first post-delivery read enrolls a bounded persistent device pin,
  all later reads enforce it, and failures/inactive Art Mode stop polling.
- A tokenless Art channel additionally requires an explicit reviewed internal
  grant and exact TV identity (D-228). Missing/rejected stored tokens never
  trigger a tokenless retry; there is no user-configurable grant bypass. D-230
  permits the fresh successful-delivery path to grant it in memory, not at boot.
- Read options from the standard app options mechanism.
- Use the Supervisor-provided Home Assistant API token only for configured filter helpers, explicit loading-timer completion (D-176), the optional artwork-information Text helper (D-202), or the fixed optional current-artwork publication above (D-225). Keep it in trusted parent/delivery-runner memory and out of unprivileged worker environments. No arbitrary configuration or state writes.
- The app must work when no helper entities are configured.
- Do not request access to Home Assistant configuration files.
- Do not require privileged container mode, host networking or Docker socket access.
  Persistent execution is optional only under the amendment above.
- Default execution is still manual/one-shot. Metadata allows the ordinary
  Start on boot control for opt-in users; do not enable it automatically.

## Security constraints

- Treat all remote metadata, image bytes, filenames, and Home Assistant state values as untrusted input.
- Validate URLs, MIME types, file sizes, decoded image dimensions, option values, and paths.
- Prevent path traversal and server-side request forgery through provider-supplied URLs.
- Apply maximum download size and pixel-count limits before expensive decoding.
- Never execute provider-supplied content.
- Run with the minimum container permissions supported by the required television library.

## Release constraints

- No public release until the user approves the project name and license.
- No container publication until the dependency license inventory is complete.
- No stable release until `aarch64` installation and a full one-shot run are validated on Home Assistant Green.
- Every release must have a changelog entry, immutable version tag, test result, and matching multi-architecture image.
