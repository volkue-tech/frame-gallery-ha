# Frame Gallery 1.0 readiness plan

Agreed direction, 2026-10-11: retain the public beta while gathering tester
feedback. Freeze the feature scope for 1.0; focus on real-world validation,
targeted fixes and a stable release. No fixed release date or tester count is set.

On 2026-10-16 the user requested one narrow exception: plan a next beta for
per-TV artwork-ID associations and actual-current artist/title information.
The [current artwork plan](current-tv-artwork-update.md) adds its own design,
implementation, validation and publication gates. It does not reopen unrelated
features or authorize implementation. The app remains beta while this scope and
the existing readiness checks are resolved.

## Validation before stable release

- [ ] Validate the current artist and colour selectors on Home Assistant Green:
  each selector alone, their intersection, no matches, preview and caption,
  loading completion, restart and existing dashboard compatibility.
- [ ] Gather external beginner feedback on repository installation, first-time
  TV pairing and complete dashboard setup, ideally on additional Frame models.
  Record the tested models and versions rather than promise universal support.
- [ ] Observe routine operation and in-place updates, including duplicate
  prevention, bounded storage and temporary-file cleanup. Resolve blocking
  defects and document remaining compatibility limits.
- [ ] Review the remaining Samsung protocol, firmware, connection-security and
  provider-access risks. Preserve the engineering licensing assessment and
  source/notices obligations; do not claim independent legal approval.
- [ ] Prepare reviewed stable-version support in metadata and publication
  checks, stable Store status, release notes, matching sources, native ARM/Intel
  validation and signed-image verification without weakening existing gates.

Fresh pairing, latest filter behaviour and live frontend languages are not
established by automated or historical already-paired TV tests. Current evidence
is recorded in [the b7 report](../../BETA7_VALIDATION.md).

## Documentation languages

Setup, colour-picker and artist-picker guides must retain reciprocal links for
English, German, French, Spanish and Italian. The b7 configuration form follows
the Home Assistant interface language; Markdown guides are chosen manually.
Technical values, entity IDs and background documents remain English.

The b7 English setup entry is [DOCS.md](../../frame_gallery/DOCS.md); translated
setup entries are [Deutsch](../../frame_gallery/SETUP.de.md),
[Français](../../frame_gallery/SETUP.fr.md),
[Español](../../frame_gallery/SETUP.es.md) and
[Italiano](../../frame_gallery/SETUP.it.md).
A b6 installed Documentation tab is not the b7 five-language setup guide.

## Outside the 1.0 scope

Additional artwork, new providers, multi-colour UI, automatic TV discovery and
history reset are not prerequisites for 1.0. History reset remains proposal-only;
do not delete history or disable duplicate protection.

## Authorization boundary

This plan records scope, not permission to change the live HA/Green/TV system,
reset pairing, contact testers, alter credentials or publish a stable release.
Implementation, live tests and publication need their respective explicit
approvals. The existing beta stays available; this task schedules no monitoring.
