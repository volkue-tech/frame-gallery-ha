# Claude Code project instructions

You are the primary implementation agent for **Frame Gallery for Home Assistant**, an independently developed Home Assistant app.

These instructions are durable. They contain no project status: the current state lives only in `STATUS.md` and `TASKS.md`.

## At the start of every run

1. Read `AGENTS.md` completely, then read every specification file it names completely.
2. Determine the current state **only** from `STATUS.md` and `TASKS.md`: which phases are complete, which gate is open, and which phase comes next. Do not infer the state from memory, earlier conversations, commit messages, or this file.
3. Check whether the user has explicitly approved the next phase. If the approval is missing or unclear, ask before starting any work in that phase.

## Scope and approval gates

- Work only on the next phase from `TASKS.md` that the user has explicitly approved, and only within its approved scope and any conditions attached to the approval.
- Stop at every approval gate in `TASKS.md`. Report what was done and what needs a decision, then wait. Never start the following phase on your own.
- Record decisions that go beyond the approved scope as proposals in `DECISIONS.md`, and bring them to the next gate. Do not act on them before they are approved.

## Clean-room boundary

This is an independent implementation. Do not inspect or access files outside this repository. Do not search for, browse, clone, or inspect predecessor Samsung Frame art-changer projects. Do not copy or imitate their source code, tests, documentation, assets, names, or repository structure. `AGENTS.md` and `LEGAL_BOUNDARIES.md` give the details.

You may consult:

- current official Home Assistant developer documentation;
- documentation for explicitly approved third-party dependencies;
- public protocol or API documentation for Samsung televisions and artwork providers;
- language and build-tool documentation.

You must not consult predecessor implementations as examples.

## No unannounced live access

- Never connect to the live Home Assistant instance, Home Assistant Green, or the television without an announced step that the user has explicitly approved.
- Never call a provider API, request images or metadata, or record a live observation without an announced step that the user has explicitly approved. Reading official documentation pages, as listed above, is not live access.
- Never publish, push, or release anything: no GitHub repositories, remotes, pull requests, issues, comments, container images, or releases. Those steps are reserved for an explicitly approved validation or release phase.
- Install dependencies only when an approval allows it, only from their official package indexes, and only into the git-ignored project environment.
- Provider tests use independently authored or synthesized fixtures, unless the user separately approves a recorded observation.

## Working method for every approved phase

1. Implement only the approved scope.
2. Add tests with each behaviour. Run the relevant tests during the work, and the complete quality gates (`frame_gallery/scripts/check.sh`) before every commit. Never claim a result that was not observed.
3. Keep the documentation current: `STATUS.md`, `DECISIONS.md`, and `TASKS.md` after every milestone, and the licence and dependency documentation (`DECISIONS.md` inventory, `THIRD_PARTY_NOTICES.md`) whenever a dependency changes.
4. Use small, focused, individually reviewable commits with descriptive messages instead of one oversized commit.
5. Stop at the next approval gate and report.

## Git identity

Follow the Git identity rule in `AGENTS.md` before every commit. It applies to every agent in this repository.
