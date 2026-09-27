# Claude Code handoff

You are the primary implementation agent for a new, independently developed Home Assistant app tentatively named **Frame Gallery for Home Assistant**.

Before making any change, read these files completely:

1. `AGENTS.md`
2. `PRODUCT_SPEC.md`
3. `ARCHITECTURE_CONSTRAINTS.md`
4. `ACCEPTANCE_TESTS.md`
5. `LEGAL_BOUNDARIES.md`
6. `TASKS.md`
7. `STATUS.md`
8. `DECISIONS.md`

## Mandatory boundary

This is an independent implementation. Do not inspect or access files outside this repository. Do not search for, browse, clone, or inspect predecessor Samsung Frame art-changer projects. Do not copy or imitate their source code, tests, documentation, assets, names, or repository structure.

You may consult:

- current official Home Assistant developer documentation;
- documentation for explicitly approved third-party dependencies;
- public protocol or API documentation for Samsung televisions and artwork providers;
- language and build-tool documentation.

You must not consult predecessor implementations as examples.

## Current state and next assignment

Phases 0, 1, and 2 are complete. Phase 2 is commit `36cda3d` after the
personal-identity history rewrite. On 2026-09-27 Codex independently reran
`frame_gallery/scripts/check.sh`: Ruff passed, strict mypy passed for 113 files,
and all 2,755 tests passed with 100% line and branch coverage. D-141 to D-145
remain proposed decisions at the Phase 3 approval gate.

Do not begin Phase 3 until the user explicitly authorizes it. Once authorized,
complete only **Phase 3 — Provider adapters** from `TASKS.md`. Do not connect to
the live Home Assistant Green or television, and do not publish or push
anything. Provider tests must use independently authored or synthesized
fixtures unless the user separately approves a recorded observation.

Keep Phase 3 reviewable: prefer focused commits for the guarded network layer,
local media, each museum adapter, and the final vocabulary/contract-test and
documentation work instead of one oversized implementation commit. Stop at the
Phase 3 gate for Codex review.

## Git identity

This is Alex's personal `volkue-tech` project. Before every commit, verify the
repository-local identity is exactly:

```text
Alexander Wilke <volkue@gmail.com>
```

Never use an `@satoshipay.io` address or any SatoshiPay, EBMA, or Marcel account,
credential, repository, remote, organization, or attribution for this project.

After approval, continue milestone by milestone. For every milestone:

1. implement only the approved scope;
2. add and run the relevant tests;
3. update `STATUS.md` and `DECISIONS.md`;
4. create a focused Git commit;
5. stop at the next approval gate.

Never connect to the live Home Assistant Green or television, publish to GitHub, or push container images. Those steps are reserved for an explicitly approved validation or release phase.
