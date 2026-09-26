# Project status

Last updated: 2026-09-26

## Current phase

**Phase 1 (independent architecture proposal) is complete and awaits approval** by the user and Codex, per the gate in `TASKS.md`.

No application code has been written. Phase 2 must not start before approval.

## Completed

### Phase 0: specification package (Codex)

- Created a new, isolated project directory with no predecessor source code.
- Captured the user-facing product requirements.
- Defined the independent-development and licensing boundaries.
- Defined product-level acceptance tests.
- Defined working instructions for Claude Code and Codex.
- Defined the phased implementation plan and its approval gates.

### Phase 1: architecture proposal (Claude)

- Read every specification file in full.
- Researched **permitted sources only**:
  - official Home Assistant documentation;
  - PyPI metadata and dependency documentation;
  - provider policy pages, `robots.txt` files, and official API documentation;
  - one Microsoft Q&A answer, cited as a non-documentation source;
  - search-result snippets, where a page blocked automated readers.
- An independent verifier re-checked the decision-critical facts in four of the five research areas.
- Wrote `ARCHITECTURE.md`. It covers:
  - component boundaries and data flow;
  - the run lifecycle, outcome taxonomy, and exit-code policy;
  - the normative budget table and cancellation;
  - selection (shortlist and attempts);
  - provider adapters and provider access findings;
  - the guarded gateway;
  - image preparation;
  - unprivileged isolated workers;
  - television communication with progress markers;
  - storage, atomic persistence, and cleanup;
  - configuration and filters;
  - a comparison of three dashboard approaches: helpers, Ingress, and a companion integration;
  - Home Assistant packaging, including the AppArmor policy and release gates;
  - security, logging, and testing;
  - the repository layout and beta scope;
  - an acceptance-test traceability matrix.
- Ran a six-lens independent review of the draft; its findings were adjudicated. 58 confirmed findings (17 major, 41 minor) were incorporated. 7 entries were not adopted (6 rejections and 1 severity downgrade), and their reasons are listed at the end of `DECISIONS.md`.
- Ran two further verification passes. They confirmed that all 58 findings are resolved, and the regression issues they raised were fixed as well.
- Updated `DECISIONS.md`:
  - refined D-101 to D-105. D-105 keeps its original clause and adds a note that Home Assistant currently supports only `aarch64` and `amd64`. The accepted decisions D-001 to D-006 are unchanged;
  - proposed D-106 to D-135;
  - added the complete proposed dependency and license inventory, covering bundled native libraries and base-image components;
  - added risks R-01 to R-21 and open questions Q-01 to Q-22;
  - answered the Phase 0 questions.
- Ticked the Phase 1 checklist in `TASKS.md` and listed `ARCHITECTURE.md` in `README.md`.

## Findings that need the user's attention

1. **Neither web source named in the specification has a documented API.**
   - Google Arts & Culture's `robots.txt` permits public HTML pages and disallows `/api/*`. The conflict is with Google's Terms and with the partner museums' image rights.
   - Bing's `robots.txt` disallows its image path `/th?` for general crawlers, and its Services Agreement restricts use of the photos.
   - No open-access API or image licence was found for the Museum of Modern Art or the Musée d'Orsay. Aggregators such as Europeana have not been checked yet.
   - `LEGAL_BOUNDARIES.md` makes respecting access terms a binding rule, so building either source would first require amending that rule.
   - Recommended beta sources: **local media plus the Art Institute of Chicago's documented CC0 API**. Its metadata includes dominant colour, style, department, and image dimensions. Whether colour can be filtered server-side is checked in Phase 4; if not, colour is checked on the returned pages within the same allowances.
2. **Samsung does not publicly document Art Mode.** The proposed library, `samsungtvws` 3.0.6 (LGPL-3.0), no longer documents its art API on PyPI. Phase 5 needs an approved way to confirm it (Q-15). The recommended way reads only the installed package.
3. **Home Assistant platform changes are reflected in the design.**
   - Add-ons are now "apps" (2026.2).
   - `build.yaml` and the legacy builder are deprecated.
   - The start action is `hassio.app_start` with the field `app`, and it is admin-only.
   - Only `aarch64` and `amd64` are supported.
4. **Container packaging** has four things to verify in Phase 6 (D-130 checks a–d). A fallback base image is recorded in case any fails.

## Specification deviations and interpretations (need approval)

| Item | Where |
| --- | --- |
| Provider set: Art Institute of Chicago instead of Google Arts & Culture and Bing; no MoMA or Orsay values | Q-01, Q-17, Q-18 |
| History recorded before the preview is published (reverses lifecycle steps 9 and 10) | D-113 |
| "60 seconds total" read as the selection-phase limit | Q-02 |
| "30 dimension probes" read as a remote-request budget; local header reads bounded separately | Q-20 |
| Landscape-only and strict-format defaults moved out of the Google Arts & Culture subsection | Q-18 |

## Next action

The user and Codex review `ARCHITECTURE.md` and `DECISIONS.md`, then approve or request changes.

**Decisions needed, by phase:**

| Before | Decisions |
| --- | --- |
| Phase 2 | Confirm `frame_gallery` as the provisional internal identifier: package, slug, media folder, User-Agent, and the television client name if one exists (Q-15). Decide Q-02, Q-12, and Q-18 items 4–5. Approve the development-only dependencies, including `uv`, once the `mypy-extensions` and `pathspec` SPDX IDs are recorded from their license files. |
| Phase 3 | Approve the Pillow row, after its bundled-library sub-table is verified from the pinned wheels. |
| Phase 4 | Q-01, Q-17, Q-18 (items 1–3), Q-03, Q-04, Q-11, Q-14, Q-20, Q-22. Approve the `urllib3` and `certifi` rows. Approve any observation requests for fixtures. |
| Phase 5 | Q-15. Approve the `samsungtvws` row and its LGPL-3.0 obligations (D-135). |
| Phase 6 | Approve pulling the base image (D-130). Decide Q-06, Q-08, Q-09, and Q-10. Approve the Buildx, QEMU, and SBOM-tool rows. |
| Phase 8 | Explicit approval for the live run, and Q-21 (install route). |
| Phase 9 | D-101 (name), D-102 (license), Q-13 (repository URL). Approve the builder-action and Cosign rows. |

After approval, Claude continues with Phase 2 (core skeleton and contracts) only.

## External state

- No Home Assistant changes were made, and no `configuration.yaml` was touched.
- No television connection was attempted.
- No GitHub repository was accessed, created, or modified, and no GitHub-hosted page was fetched.
- No container image was pulled, built, or published.
- No provider API or image endpoint was called. The following were read, using web-fetch tools, `curl` (including PyPI's JSON metadata API), and the in-app browser:
  - public documentation pages, policy pages, and `robots.txt` files;
  - one Microsoft Q&A answer, cited as a non-documentation source;
  - search-result snippets, where a page blocked automated readers.
- No project license has been finalized.

## Known open decisions

`DECISIONS.md` has the full list. The most material:

- the provider set for the beta (Q-01, Q-17, Q-18);
- how to confirm the television library API (Q-15);
- the loading-indicator approach and its latency (Q-09);
- the dependency inventory, especially the LGPL-3.0 and copyleft source obligations (D-135);
- the final name (D-101; see R-14 on the trademark wording) and license (D-102), needed before publication.
