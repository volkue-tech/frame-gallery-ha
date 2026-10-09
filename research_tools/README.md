# Private Commons research, 2026-10-09

This tooling is outside the runtime package. No credentials, original-image
downloads, Home Assistant access or television access are needed. It does not
automatically approve catalogue additions. Explicit second-view choices retain
283 retained local research acceptances; the current released/runtime catalogue
has 400. The earlier provisional 127 were reduced after plain source measurements
exposed additional possible crops; subsequent actual visual reviews added other
works. Use the checkpoint/curation manifest for the current count, not this history.

The project required reading and the D-212/D-213 boundaries apply. Do not weaken
the minimum source width, near-16:9 shape, existing PD/CC0 policy, reproduction
quality or no-duplicate rules to hit a count. Template declarations are source
evidence, not worldwide copyright clearance or a substitute for provenance review.

## Retained state

- `frame_gallery/research/commons-colour-profiles-2026-10-09.json`: full, source-pinned baseline
  colour distributions/palettes/top groups. Metadata only.
  It is available to the container's test stage, but production copies only
  src and the licence bundle, not this evidence or any research images.
- `research/commons-colour-audit-2026-10-09.json`: actual counts and verification.
- `build/commons-colours/`: private thumbnails, pilot checkpoints and gallery.
- `build/commons-1000-research/`: separate discovery passes, raw public metadata
  receipts, saved revisions/hashes, tentative profiles, contact sheets and
  per-ID visual-screen decisions. Never count metadata eligibility as acceptance.
- `frame_gallery/research/commons-expansion-curation-2026-10-09.json`: explicit
  local acceptance decisions and inspected-source hashes, not release approval.
- `frame_gallery/research/commons-expansion-colours-2026-10-09.json`: full
  provisional colour profiles for those accepted additions, metadata only.
- `research/commons-curator-deferrals-2026-10-09.json`: explicit observed
  second-view issues. Dossiers keep these flagged until separately resolved;
  a new search or a lack of automatic flags must not silently approve them.
- `research/commons-baseline-format-audit-2026-10-09.json`: all 400 unchanged
  baseline source revisions and upload pins; 57 physical-measurement scope
  prompts need resolution. This report does not declare 57 crops or approve,
  remove, replace or modify an existing work.

Do not remove the ignored build directories: they are the resumable local
research requested by the user. None belongs in the app image or artwork assets
of a release. The small runtime index contains only IDs, source pins and families.

## Commands from the repository root

Use `frame_gallery/.venv/bin/python`. Run **one** public network phase at a time;
the guarded gateway preserves pacing, TLS, address and host checks. Every pass
has its own finite request/deadline limit, no blind retries after refusals, and
saves progress. Discovery files overlap: never add their totals together.

```sh
frame_gallery/.venv/bin/python research_tools/commons_review.py counts
frame_gallery/.venv/bin/python research_tools/commons_review.py metadata --limit 1000
frame_gallery/.venv/bin/python research_tools/commons_review.py thumbnails --limit 315
frame_gallery/.venv/bin/python research_tools/commons_review.py sheets
frame_gallery/.venv/bin/python -m research_tools.commons_curation fingerprints
frame_gallery/.venv/bin/python -m unittest research_tools.test_commons_colours
frame_gallery/.venv/bin/python -m unittest research_tools.test_commons_dossiers
frame_gallery/.venv/bin/python -m research_tools.commons_targeted --limit 150
frame_gallery/.venv/bin/python -m research_tools.commons_expand --pdart
frame_gallery/.venv/bin/python -m research_tools.commons_expand --precise
frame_gallery/.venv/bin/python -m research_tools.commons_expand --artwork-precise
frame_gallery/.venv/bin/python -m research_tools.commons_expand --paintings-precise
frame_gallery/.venv/bin/python -m research_tools.commons_expand --cc0-art-precise
frame_gallery/.venv/bin/python -m research_tools.commons_identity_review
frame_gallery/.venv/bin/python -m research_tools.commons_baseline_audit
frame_gallery/.venv/bin/python -m research_tools.commons_dossiers
frame_gallery/.venv/bin/python -m research_tools.commons_dossiers sheets
frame_gallery/.venv/bin/python -m research_tools.commons_curate
```

Each decoded JPEG is byte/header/dimension bounded and processed by a fresh
credential-free child with a parent timeout/CPU budget. A Linux memory limit is
not claimed to work on the Mac. Never reuse this pilot as runtime decoding on Green.

The `screen` command is a transcription of **already inspected sheets**, not
an image classifier. Its recorded first 299 positions must stay bound to the
same ordered profiles and thumbnail hashes; inspect new sheets before extending
the list. Deferred cases stay deferred. Fingerprint-distance prompts require an
actual comparison of artwork identity, including against the baseline; they
are not automatic approvals or rejection decisions.

Prior inspected contact sheets are retained by content-hash filenames when a
new batch changes a partial sheet. Before accepting any new work, verify the
complete physical proportions and EXIF-oriented reproduction as well as its
metadata dimensions. A wide file containing a cropped detail is not a wide artwork.
Plain museum/GAP measurements and description dimensions supplement Size
templates. Preserve image/sheet scopes and conflicting measurements for review;
neither physical proportions outside the target band nor separate Art Photo
attribution/share-alike declarations are automatically approved.
Explicit Dutch `h/b` measurements retain their axes and scopes, even when units
repeat or differ. Institution upload credits are not used as artist attribution:
the explicit Rijksmuseum maker field is retained, or the artist is unidentified.
Explicit `core:format` width/height pairs are checked too; decimal commas and
mixed units must not hide conflicting original dimensions.
Fractional-inch pairs, repeated units and explicit H/B semicolon axes also retain
original scopes; they are not ignored because a file itself is near 16:9.

For newly inspected ranges, `commons_resume batch --start N --stop M
--plausible 'positions'` records the actual first viewing, bound to the saved
sheet and JPEG hashes. Never call it on an unseen range or use it as a classifier.
Previously recorded ranges cannot be overwritten. A checkpoint retains the exact
review/profile bytes in hash-named private files, so later discovery passes do
not invalidate the checkpoint's evidence hashes. Run fingerprints only after
the thumbnail writer finishes, because both update `profiles.json`.

Official source notes checked on 2026-10-09: [PD-Art-two-auto](https://commons.wikimedia.org/wiki/Template:PD-Art-two-auto)
documents its combined underlying/US basis, and [PD-old-100-1923](https://commons.wikimedia.org/wiki/Template:PD-old-100-1923)
redirects to PD-old-100-expired. The scanner now records these explicit verified
aliases plus [PD-old-70-expired](https://commons.wikimedia.org/wiki/Template:PD-old-70-expired);
this is evidence screening, not automatic curator acceptance.
[Licensed-PD-Art](https://commons.wikimedia.org/wiki/Template:Licensed-PD-Art)
separates the original work from the photographic reproduction; a reproduction's
licence must not be mistaken for clearance of the original. Ambiguous records
remain manual deferrals, not approvals.

The public revision API also verified PD-old-auto-1923, PD-old-70-1923 and
PD-art-old-100-expired against their canonical declarations. Page/revision IDs
and receipt hashes are in `research/commons-template-evidence-2026-10-09.json`.
Offline `commons_resume refresh` reparses retained source receipts and verifies
existing JPEG hashes, but does not repeat decoding or claim a new decode check.
Narrower discovery windows improve search coverage without changing acceptance.
Each pass makes at most 140 requests and retains completed requests; a capped
window is not called exhausted. A saved API refusal blocks an automatic repeat.
Network transport failures also end the pass and retain the failed request key;
that window is skipped on later automatic passes, not called exhausted or retried.
The separate Artwork-declaration narrow pass retains its own receipts. Preview
priority changes ordering only, never acceptance or permanent exclusion; labelled
documents/archival drawings remain available for separately recorded inspection.
The separate narrow painting pass combines Artwork declarations with the source
word "oil" to prioritize paintings rather than objects and documents. This is a
discovery aid, not a medium, attribution, completeness or rights determination.
The separate CC0/art query also searches for contemporary/original abstract and
digital art without requiring an Artwork declaration. A photographic CC0 label
does not clear the depicted artwork; source ownership, completeness and rights
scope still require individual review. No runtime rights policy is widened.
Absent artist metadata may use Creator names in the explicit artwork artist
field. Do not infer attribution from categories, file titles or uploader identity.
The documented template filter is searched separately: CirrusSearch does not
combine template parameters with word-style OR semantics. The earlier empty
multi-template search receipt remains retained, not overwritten.

After curated additions are genuinely accepted, retain their exact page/upload
identity, full-image/physical-format decision, artist/title provenance and
rights-source evidence. Only then extend the catalogue and complete its colour
profiles. The generated runtime export must match that exact frozen catalogue.

```sh
frame_gallery/.venv/bin/python research_tools/export_commons_colours.py
frame_gallery/.venv/bin/ruff format frame_gallery/src/frame_gallery/providers/commons_colour_data.py
```

The existing complete production gates remain in `frame_gallery/scripts/check.sh`.
Native ARM/Intel release-image checks, publication and Green/TV testing each
remain separately gated. Do not use credentials or claim a 1000-work release
because a local colour draft or research search has completed.
