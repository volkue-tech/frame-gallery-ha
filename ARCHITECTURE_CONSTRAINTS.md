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

- **2026-10-20 D-240 local arbitration:** defer only the initial automatic
  read for a fixed ten-second command handoff; missing/invalid/off/error/gap
  clears pending evidence. Claimed NEW_ARTWORK spends startup and old off-edge
  evidence before send/reap failures without resetting attempt/auth limits.
  No hidden startup retry after a failed/no_match send. Existing cards/scripts,
  later genuine edges and all worker/attribution guards remain unchanged.
  Local/offline only; installed b12 remains stopped, no TV access/publication.

- **2026-10-19 D-239 explicit exception:** with background and the existing
  resume entity opted in, first cached HA on may trigger one initial read even
  with old last_changed. Consume the first sample on error/off too; no delayed
  retry. Reuse exact archived target/device/token and isolated real Art/image
  proof; preserve sender separation, privileges, current cards and freshness.
  HA on is not Art Mode proof or a no-wake guarantee. Later edges retain D-238.

- **2026-10-18 D-235 superseding complete-feature scope:** archive every selected
  upload in one-shot/background mode, per actual device identity captured from
  the existing capability response, with no extra TV request. Bound private
  atomic state to 2,048 associations/32 MiB plus one backup; tiny RGB references
  are generated in the existing image worker. No new privileges/mounts/helpers.
  An opted-in service can consume one fresh, exact persisted-delivery grant for
  an experimental strict slideshow session; no personal-ID registry entry or
  user-managed mapping. This replaces the old empty-profile-only restriction
  for that path, not the default OFF, no-reconnect or no-wake warning. Current
  observation and historical metadata provenance remain separate. Native ARM/
  Intel must pass before the now-authorized beta publication. b8/cards stay.

- **2026-10-18 D-234 local integration:** bind new background receipts to the
  actual delivery target by a hash, reuse the exact receipt bytes for parsing,
  and reject legacy/missing/mismatched receipts for arming without connecting.
  Every state-publication failure latches stop/no-retry, not only 401/403.
  Exact captured standby under the slideshow contract pauses/closes normally.
  Do not add user-profile bypasses or ship a personal TV ID; production profiles
  stay empty. Native candidate checks move to the separately approved release
  round, not a claim from local Mac results. b8/cards remain unchanged.

- **2026-10-17 D-233 local/offline amendment:** the exact lab4 slideshow
  event contract can corroborate selected/shown ID + matching automatic-rotation
  ID + mode-on within five seconds. Host-only per-TV binding lookup is read-only,
  marked slideshow evidence, never a new byte proof or association. Unknown IDs
  have no artist. Selection/navigation invalidate old metadata; off/failure ends.
  Baseline proof expires at 90 seconds and changed-ID event proof at 15 minutes,
  with no duplicate/on/pong freshening. Expiry clears display, not the listener.
  No post-baseline request/reconnect, runtime profile bypass, active hardware
  policy, live update or publication. Existing confinement and cards stay intact.

- **2026-10-17 D-232 local-only exception:** an exact internal policy may opt
  into at most one five-second same-websocket ID probe after validated mode-on.
  No new transport, library reconnect/getter loop, timer/polling, retry, image
  transfer or freshened ID-only attribution. Emit invalidation before the request;
  the parent clears metadata on receipt, without a synchronous HA acknowledgement.
  Parent bounds pending checking and ends on success/failure. Off still closes;
  expired initial proof cannot trigger a request.
  Existing worker isolation, resource/cancel limits and empty live-policy table
  remain. No live/test-app update or release is authorized by this amendment.

- **2026-10-17 local event-session amendment (D-231):** local implementation
  and offline testing only. Replace the periodic observer in real service wiring
  with a dedicated unprivileged event worker, using the existing TV-worker
  bootstrap, 512 MiB/CPU/descriptor/LSM/seccomp restrictions and parent lifeline.
  The long-lived session is finite (eight hours); bootstrap is bounded to five
  seconds, incomplete frames to five seconds, text frames to 64 KiB and the
  parent event queue to 64. Child cancellation first attempts a bounded graceful
  close, then kills/reaps; an unreaped worker forbids replacement/delivery.
  No thread or child process is created by the unprivileged event task.
  A trusted parent thread relays framed JSON only; no Supervisor token crosses
  into the worker. All one-shot delivery deadlines/watchdogs remain unchanged.
  An exact reviewed device-event profile and fresh explicit delivery are both
  required; the production profile table is empty pending separate validation.
  Do not substitute the earlier D-230 opt-in for that event/sleep approval.
  No live reactivation, new HA read permission, pairing, polling or reconnect.
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
