# Commons artist selection and Italian documentation — next update

Human authorization: 2026-10-10. Implement optional artist selection and its
native dashboard variant. Separately add Italian as an official documentation
language in this update. This is not publication, native-build or live HA/TV
authorization. Keep English default; the later human clarification additionally
approves French/Spanish/Italian configuration UI (D-222).

## Included

- One artist wish, Commons only, default unrestricted. Accept only offered
  whole catalogue labels/keys under established normalization. Preserve all
  catalogue pins, attribution, permanent IDs and history; no identity guesses.
- Optional static artist text and dedicated Dropdown/Text helper, with existing
  unavailable/invalid-helper fallback. Keep the five basic settings unchanged.
- Intersect artist, colour and shape constraints; shape fallback never changes
  artist or colour. Exhaustion/no match preserves TV, preview and artwork info.
- Native complete card with optional favourite-artist Dropdown and colour
  Dropdown; reuse existing camera/timer/script. No HACS, SSH/configuration.yaml,
  automatic helper creation or all-557 radio list. Standard card stays unchanged.
- Full searchable documentation list with catalogue counts (not unsent counts).
  Clearly distinguish anonymous, attributed and multiple-contributor labels.
- Document the new artist feature in EN/DE/FR/ES/IT before release, with complete
  translated card examples whose entity IDs/actions/options stay identical.
- Italian setup and colour guides, reciprocal links at README, Info, Docs and
  all language entry points. English remains canonical; technical reference
  remains English. Also provide complete en/de/fr/es/it configuration names/help
  selected by the HA frontend; technical values remain unchanged.
- Required targeted/regression tests, full unchanged quality gates, then exact
  native ARM/Intel source/signature/build gates before an approved release.
  Live update/helper/card/TV checks need separate confirmation.

## Deliberately not included yet

- Multi-colour selection, automatic TV discovery, new sources or catalogue
  content changes.
- Implementing history/cache deletion or disabling duplicate protection.
- Automatic installation or modification of user's helpers/cards/scripts.

## History reset proposal (discussion only, not implementation approval)

The user suggested an advanced reset to allow old works again. Do not call this
"Delete cache": temporary-file cleanup is independent of sent history,
confirmed-upload ledger and 30-day uncertainty quarantine. Clearing just history
would not re-enable already uploaded works. Clearing all protections might upload
duplicate TV copies and would remove safety around uncertain uploads.

Suggested user-facing name: "Allow previously used artworks again" / "Bereits
verwendete Werke wieder zulassen". Investigate selecting an existing TV content
ID without re-uploading; current persisted state must first be checked for that
ability. Before implementation choose explicit semantics, scope, confirmation
and recoverable backup. Do not imply deleting TV pictures, preview or media.
No reset operation or live-state change is authorized by this discussion.

## Local progress

- [x] Inspect actual 1000-work labels and record boundaries: 560 attributions,
  557 normalized choices; four long labels abbreviated only for selection.
- [x] Implement options, helper resolution, capability/reporting and offline
  prefilter; add candidate vocabulary version 3.
- [x] Complete targeted/production regression and full quality gates: 5116 passed,
  eleven existing platform skips, strict mypy on Mac/Linux, 100% line/branch.
- [x] Finish five-language artist docs and Italian setup/colour/language links;
  also add a complete German setup guide for consistent five-language coverage.
- [x] Review and prepare the personal local commit; the separate native/publication
  gate is the next action and has not been approved for this candidate.
- [ ] Run authorized native/publication/live gates; no public availability claim
  before they actually pass.
