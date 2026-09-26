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

## First assignment

Complete only **Phase 1 — Independent architecture proposal** from `TASKS.md`.

Produce an original architecture proposal in `ARCHITECTURE.md`, update `DECISIONS.md` with proposed decisions and unresolved questions, update `STATUS.md`, and commit those documentation changes. Do not write application code during Phase 1. Stop after the commit and ask the user to approve the architecture.

After approval, continue milestone by milestone. For every milestone:

1. implement only the approved scope;
2. add and run the relevant tests;
3. update `STATUS.md` and `DECISIONS.md`;
4. create a focused Git commit;
5. stop at the next approval gate.

Never connect to the live Home Assistant Green or television, publish to GitHub, or push container images. Those steps are reserved for an explicitly approved validation or release phase.

