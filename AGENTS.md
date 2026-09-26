# Agent instructions

These instructions apply to every coding or review agent working in this repository.

## Independent implementation boundary

- Implement only from the specifications stored in this repository.
- Do not inspect, access, copy, translate, adapt, paraphrase, or derive code, tests, documentation, assets, naming, file structure, or implementation details from predecessor Samsung Frame art-changer projects.
- Do not inspect any sibling directory, especially `../work/homeassistant-addons-fork`, `../work/frame-art-local-repository`, or other prior Frame Art workspaces.
- Do not browse or clone the excluded projects listed in `LEGAL_BOUNDARIES.md`.
- Public behavior, documented protocols, official APIs, and the user-authored requirements in this repository may be implemented independently.
- Third-party dependencies may only be used after their license and version are recorded in `DECISIONS.md` and the eventual third-party notices.

## Scope and safety

- Work only inside this repository unless the user explicitly authorizes another path.
- Do not connect to or modify the live Home Assistant instance, Home Assistant Green, the television, GitHub, a container registry, or any other external system without explicit user confirmation for that step.
- Do not change any Home Assistant `configuration.yaml` file.
- Do not publish releases, containers, repositories, comments, issues, or pull requests without explicit confirmation.
- Preserve user data and avoid destructive commands.

## Development process

- Read all specification files before proposing architecture or writing code.
- Treat `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` as the definition of done.
- Record material technical decisions in `DECISIONS.md`.
- Keep `STATUS.md` current after every milestone.
- Add tests with each behavior; do not postpone the test suite until the end.
- Use small, reviewable commits with descriptive messages.
- Stop at every approval gate in `TASKS.md`.
- Never claim a test passed unless its command was actually run and its result observed.

## Home Assistant requirements

- Target Home Assistant OS with Supervisor/apps, including Home Assistant Green (`aarch64`).
- The installation must not require SSH, shell commands, Docker installation, or edits to `configuration.yaml`.
- All dashboard examples must be supplied as complete copy-and-paste-ready YAML blocks.
- Prefer current official Home Assistant app packaging and multi-architecture container guidance.

