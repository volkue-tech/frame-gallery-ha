# Private Commons research, 2026-10-09

This tooling is outside the runtime package. No credentials, original-image
downloads, Home Assistant access or television access are needed. It does not
automatically approve catalogue additions. Explicit second-view choices retain
127 local research acceptances; the current released/runtime catalogue has 400.

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
frame_gallery/.venv/bin/python -m research_tools.commons_identity_review
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

Official source notes checked on 2026-10-09: [PD-Art-two-auto](https://commons.wikimedia.org/wiki/Template:PD-Art-two-auto)
documents its combined underlying/US basis, and [PD-old-100-1923](https://commons.wikimedia.org/wiki/Template:PD-old-100-1923)
redirects to PD-old-100-expired. The scanner now records these explicit verified
aliases plus [PD-old-70-expired](https://commons.wikimedia.org/wiki/Template:PD-old-70-expired);
this is evidence screening, not automatic curator acceptance.
[Licensed-PD-Art](https://commons.wikimedia.org/wiki/Template:Licensed-PD-Art)
separates the original work from the photographic reproduction; a reproduction's
licence must not be mistaken for clearance of the original. Ambiguous records
remain manual deferrals, not approvals.

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
