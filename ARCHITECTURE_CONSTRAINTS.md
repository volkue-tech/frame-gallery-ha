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

- Read options from the standard app options mechanism.
- Use the Supervisor-provided Home Assistant API token only when optional helper resolution is configured.
- The app must work when no helper entities are configured.
- Do not request access to Home Assistant configuration files.
- Do not require privileged container mode, host networking, Docker socket access, or persistent background execution.
- Default startup mode is manual/one-shot; the app exits after one completed attempt.

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

