# Decision log

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

Status: proposed

Working name: **Frame Gallery for Home Assistant**.

Rationale: distinct, descriptive, and not tied to a predecessor repository name. Branding and trademark wording require review before release.

### D-102 — Project license

Status: proposed

Apache License 2.0 for independently authored project code.

Rationale: permissive reuse with an explicit patent grant. Third-party dependencies retain their own licenses.

### D-103 — Implementation language

Status: proposed

Python 3.12 or a currently supported Python 3 version compatible with Home Assistant base images and approved dependencies.

### D-104 — Samsung transport

Status: proposed

Evaluate a pinned current release of `samsungtvws` rather than implementing the television protocol from scratch. Confirm its current license and redistribution obligations before adoption.

### D-105 — Release architectures

Status: proposed

Publish `aarch64` and `amd64` first. Add other architectures only after successful builds and explicit support decisions.

## Open questions for Phase 1

- Should runtime filter changes initially use documented Home Assistant helpers, a small Ingress UI, or only app options?
- How should provider metadata caches be bounded and invalidated?
- Which source identifiers remain stable enough for duplicate prevention?
- What provider access mechanism can support Google Arts filters without fragile or inappropriate behavior?
- Should pairing tokens remain only in private app data, and what recovery flow should be documented?
- What is the smallest public beta that still provides a compelling HA Green experience?

