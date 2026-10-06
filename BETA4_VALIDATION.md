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

## Corresponding-source verification

Frozen runtime/source commit: `5011966879d5993d548a54df32e0361da86135ca`.
The public [source-only release](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b4)
contains `frame-gallery-sources-0.1.0b4.tar`, 522,618,880 bytes, including the own
clean source snapshot and 172 retained upstream source archives/notices.

SHA256: `6a3ece93091f52f8d89ee37cb59b63625ccd7ebde6d12b025ac7969ee5c60e16`.
An anonymous download and the tracked release preflight passed: exact version,
commit, archive hash and every source member. Previous sources remain available.

## Native images published and independently verified

Manual [publisher run 37428676044](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/37428676044)
uses the exact commit above on `codex/commons-curated`. Both public, non-secret
approval values were read back in the personal repository UI after the user
completed GitHub's existing-password confirmation. The initial approval job
passed. All five jobs completed successfully on 2026-10-06 at 07:55:30 UTC.

Both native validators have since completed successfully. Each host gate passed
5,001 tests with five root-only skips and 100% statement/branch coverage.
Each actual container also passed 5,001 non-root tests plus all five explicit
root-isolation tests, the native 1 GiB RLIMIT_AS measurements, and 150 inspections
using ten workers. Both publishers repeated the checks on their actual runtime
images and completed publication and signature verification successfully.

Downloaded native evidence ZIPs match their public workflow hashes:

| Evidence | SHA256 |
| --- | --- |
| ARM native validation | `81301d94cc5752a2085f79c815e5d3bf79fe71b7ef5634a9e740ccdbe5c76ddf` |
| Intel native validation | `5acabc15a2d443fb01da310df123a7f9b41274abd62e6b50353aa6087454d722` |

Both were safely retained locally with their logs/inventory/measurement records.

Both actual publisher evidence ZIPs were also downloaded, safely extracted and
matched to the public workflow hashes. Their `published-digest.txt` records
agree with the independently queried registry digests below.

| Actual publisher evidence | Bytes | SHA256 |
| --- | --- | --- |
| ARM (`11397134382`) | 20,190 | `38b741cafbe0d3562f721a54f8063c2027087697941b0ec176ee9b6ce4ca6398` |
| Intel (`11397174743`) | 20,212 | `1bcbb0e43b29fc3f4419cd5998b7cb972cc95a78a89ce72acdfd6ca3d31369b2` |

Actual publisher containers each passed 5,001 non-root tests plus five explicit
root-isolation checks. All 26 preparation measurements passed under the native
1 GiB address-space limit, with no failures in 150 inspections using ten workers.
ARM maximum preparation was 2.15 s / 766.5 MiB peak address space; Intel was
2.65 s / 761.8 MiB. These are native build-host measurements, not new Green tests.

Anonymous registry reads verified that each version tag and immutable digest
resolve to identical manifest bytes. Anonymous pulls verified architecture,
version, source and exact runtime revision. A separate read-only, unprivileged,
network-disabled run of each pulled image confirmed version b4, 166 unique
works, 112 artist labels and the ten-batch ceiling.

| Architecture | Immutable image digest |
| --- | --- |
| aarch64 | `sha256:b5fd77829c8cc330a1ac14897ff2725d6cca2526d25611681cf64801215b8d9c` |
| amd64 | `sha256:e9954b2daf807380f4cc0b515edb7f4d9b7a6da35f9603bd14e352bb885cbee5` |

Independent Cosign 3.1.3 verification passed for both exact digests, including
the claims, transparency-log proof and trusted signing certificate. Identity:
`https://github.com/volkue-tech/frame-gallery-ha/.github/workflows/publish.yml@refs/heads/codex/commons-curated`;
issuer `https://token.actions.githubusercontent.com`; workflow SHA
`5011966879d5993d548a54df32e0361da86135ca`.

## Required before Store publication

- Clean reviewed candidate commit and matching public source package: passed.
- Anonymous source hash/member verification: passed.
- Both native ARM/Intel validations and actual publisher image checks: passed.
- Exact image digests, anonymous registry verification and independent signatures: passed.
- Retain and hash-check both actual publisher evidence ZIPs: passed.
- Both one-time approval variables were set to `DISABLED_AFTER_0.1.0b4` and
  read back after the successful run. No scope or security permission expanded.
- Store main fast-forward and beta announcement follow the completed checks.

No new Green/TV installation or physical display validation is claimed for b4.
The previous [b3 live report](BETA3_VALIDATION.md) remains separate evidence.
No Home Assistant or TV mutation is authorized in this publication request.
