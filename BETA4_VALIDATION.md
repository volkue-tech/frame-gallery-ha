# Frame Gallery 0.1.0b4 validation

## Scope

Metadata catalogue update: 166 pinned JPEG works from 112 artist labels, source
width >=3000 and relative 16:9 deviation <=2.5%. The app's stricter 1% preference
is unchanged; 67 originals meet it. Contain remains the no-crop default.
Existing history IDs/options/dashboard helpers remain unchanged.

All 200 private proposals are retained locally and as a metadata-only release
inventory. 34 are deferred: 11 PNG/TIFF sources, five scan/work-proportion cases,
18 rights-review cases. This is not worldwide legal clearance. No artwork files
are bundled, no dependency or permission is added, and no old beta is replaced.

## Completed candidate checks

The actual production adapter offered 166/166 sources in four bounded metadata
passes, 35.61 seconds total (each pass has the existing 30-second discovery
deadline). No artwork image, HA or TV endpoint was contacted by this check.
This audit is not one ordinary exhaustive app run: normal discovery samples at
most ten paced batches, with its existing shared request allowance.

Synthetic regressions cover the expanded 200-entry fixture, ten-request ceiling,
mixed sent/unsent batches, last remaining unsent work, all-sent exhaustion and
rejected rights. Existing delivery/cleanup/no-repeat regressions stay in place.

Final local full gates passed 4,995 tests, eleven platform skips, strict mypy,
Ruff and 100% line/branch coverage (9,426 statements / 2,054 branches).

## Required before Store publication

- Clean reviewed candidate commit and matching public source package.
- Anonymous source hash/member verification.
- Both native ARM/Intel validations and actual publisher image checks.
- Exact image digests, anonymous registry verification and independent signatures.
- Store main fast-forward only after those checks; disable/read back approvals.

No new Green/TV installation or physical display validation is claimed for b4.
The previous [b3 live report](BETA3_VALIDATION.md) remains separate evidence.
No Home Assistant or TV mutation is authorized in this publication request.
