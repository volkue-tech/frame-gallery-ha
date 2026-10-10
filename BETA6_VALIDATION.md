# Frame Gallery 0.1.0b6 validation

## Current publication gate

The source-only prerelease, reviewed candidate branch and both signed images
are public. The complete native pipeline and independent anonymous image /
signature checks passed; **the app beta and Store main are not published yet**.
Downloading the two publisher evidence ZIPs and the final release/Store handoff
remain pending because the Mac is locked and the fresh token prompt is unanswered.
Only observed checks are recorded below. No new HA Green or TV test is authorized
or claimed for this release.

## Reviewed scope

Exactly 1,000 active pinned Commons works: 344 retained baseline entries and 656
visually reviewed additions. The exact 56 unresolved baseline entries are held
with human approval, not relabelled as proven crops; their identities, original
source evidence and sent-history IDs remain retained. Seven reviewed additions
remain reserves. All 1,063 full colour profiles and the historical 400-work
manifest remain available for research.

Every active original has width >=3,000 pixels and relative 16:9 deviation <=2.5%.
The existing approximately 1% preference remains unchanged (566 active source
ratios meet it). Contain remains the no-crop default. The active rights inventory
is 629 Public Domain and 371 CC0 records; freely licensed contemporary-art leads
remain research-only until an appropriate runtime attribution design is approved.
Commons rights evidence is not a guarantee of worldwide legal clearance.

One optional colour selector is available only for Commons, with `any` as default
and twelve named families. Matching means a noticeable >=5% colour area, not
necessarily the dominant colour. Full distributions and the top three meaningful
groups are retained for future combinations; this release exposes only one colour.
The optional documented native Dropdown helper/card reuses the existing camera,
timer and script. No custom dashboard extension or new mandatory helper is needed.
Other providers remain available and unsupported colour is recorded as ignored.
There is no silent fallback to another colour; no-match preserves the previous
preview, caption and history. Request budgets, source/upload pin checks and history
compatibility remain unchanged. No IP discovery, multi-colour UI, new provider,
dependency or configuration.yaml change is included.

## Observed local checks

Ruff and format checks passed; strict mypy passed for both host and Linux
configurations (252 files). The final numbered-candidate suite passed 5,028 tests
with eleven unchanged Linux/root platform skips, 100% whole-package line/branch
coverage (9,440 statements / 2,056 branches) and required-package coverage
(7,748 / 1,712), observed exit 0. All 106 offline research tests passed.
Evidence: `build/commons-1000-release/local-quality-final.log`.

The native-evidence documentation recheck initially failed two macOS filesystem
mode/group handover tests inside the local sandbox (5,026 passes, eleven skips).
The identical complete command outside that sandbox passed all 5,028 tests and
100% coverage with exit 0; no code, test, skip or limit changed. Both logs remain
retained (`check-native-evidence-docs.log` and its `-elevated` counterpart).

The first publication-documentation gate found a missing test-context allowlist
entry for the archived b5 list (one failure, 5,026 passes). The explicit allowlist
was corrected and the whole gate rerun; the original failing log remains retained.
No runtime limit, test skip or coverage threshold was relaxed. The only raised
bound is the offline clean project-source snapshot limit: 32 MiB to 128 MiB,
because retained full-profile provenance exceeds the older archive cap (D-218).

The frozen source/runtime audit recomputed all 1,063 colour profiles and matched
the active runtime to the 1,000-work source/profile manifests. The local preview
showed separate sets of 1,000 active / 56 held / seven reserve works and 385 active
blue matches with zero wrong-colour/status inclusions. These are source/palette
and browser checks, not work-by-work physical TV evidence.

## Corresponding sources

Frozen runtime/source commit: `0c2d77d75dba29eebc4c306a174630059448d879`.
The public [source-only prerelease](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b6)
contains `frame-gallery-sources-0.1.0b6.tar`, 579,829,760 bytes, including the clean
own-source snapshot and 172 retained upstream archives/notices.
SHA256: `8073c60f0b63c0ae73ef8f409adc5a06c65cf65ec0b0fb41a7f6fe6985f1e173`.
Source release ID: `408974721`; asset ID: `628067794`.

An anonymous download and the tracked release preflight passed: exact version,
approved commit/hash, project snapshot, fixed upstream records and every archive
member. GitHub's asset digest and byte size match. No upstream code was executed.
This is integrity evidence, not a claim of byte-identical rebuilding. Sources,
images and tags for earlier versions remain available.

## Native pipeline — completed successfully

Both exact approval values were saved and read back in the personal repository
UI. Manual [run 38056898224](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/38056898224)
started at 2026-10-10 15:44:42 Europe/Berlin on `codex/commons-default`, exact frozen
commit above. All five jobs passed: approval, both native validators and both
actual image publishers. The run completed at 2026-10-10 14:20:42 UTC
(16:20:42 Europe/Berlin). Store main remains on b5 at this checkpoint.

Both downloaded native ZIPs were checked against the exact run's public API
metadata, including size, SHA256, repository, branch and source SHA, then safely
extracted without executing their contents. Each native host passed its complete
quality gates. Each actual test container passed 5,034 tests with five root-only
skips, followed by all five separate root tests. All thirteen worst-case image
inputs passed twice under the unchanged 1 GiB address-space limit; 150 inspections
with ten workers completed without failure.

| Native host | Peak address space | Slowest preparation | 150 inspections |
| --- | --- | --- | --- |
| Linux aarch64, Python 3.14.8 | 766.5 MiB | 2.15 s | 1.30 s, zero failures |
| Linux x86_64, Python 3.14.8 | 761.8 MiB | 2.64 s | 1.62 s, zero failures |

Native evidence records (run `38056898224`):

- `native-aarch64-validation`: artifact `11672150216`, 22,684 bytes,
  SHA256 `9089f295a602b6ae2a52c827491c3f24474bcb640412be5bca182a7a89fdc4e8`.
- `native-amd64-validation`: artifact `11671929548`, 22,629 bytes,
  SHA256 `d54c91825cf9b610069b2186f9ade0700f62080428aaea13f6d3f9a5a684918b`.

Local verification receipts and extracted logs are retained under
`build/commons-1000-release/`.

## Independent public-image checks

Both anonymous version-tag and immutable-digest manifest bytes matched their
SHA256 headers. Anonymous pulls, architecture/version/repository/revision labels
and isolated actual-image imports passed with exit 0. Each import used a
read-only container, uid 65534, no network, no capabilities and no host data.
Both images contain exactly 1,000 distinct pinned works/profiles, 560 artist
labels, twelve colour families and 385 blue matches; source-file hashes match
the frozen candidate. Commons default and ten five-record metadata batches are
unchanged. The Intel import on this Mac is emulated inspection, not native Intel
validation; native Intel evidence is the successful CI job above.

| Architecture | Immutable public image digest |
| --- | --- |
| aarch64 | `sha256:7a4d721d91671fc9be9d85b4dbbf5ab7a039a9d68a5a964f70d0735e09e40469` |
| amd64 | `sha256:ac19e05d2e155088da649028e227e0ecb8e38b4d27245f23b6c145c7dd9a7421` |

Independent hash-pinned Cosign 3.1.3 verification passed with exit 0 for both
exact digests, the frozen workflow SHA, GitHub OIDC issuer
`https://token.actions.githubusercontent.com` and certificate identity
`https://github.com/volkue-tech/frame-gallery-ha/.github/workflows/publish.yml@refs/heads/codex/commons-default`.
No personal GitHub/HA/TV credential was supplied to these public checks.

Public API metadata for the two publisher evidence ZIPs is retained and binds
both to the exact approved run/branch/commit. Download/hash checking of their
contents remains pending; these are not yet claimed as locally verified archives:

- `beta-aarch64-evidence`: artifact `11672796139`, 20,208 bytes,
  SHA256 `cb82a1e04351ef6bab5225be96c92bdcbc39bf25cac94d4e5c2fb0660b0977bb`.
- `beta-amd64-evidence`: artifact `11672846097`, 20,210 bytes,
  SHA256 `ade10f890177e2c3e1c3dc0016bc076f6b7c558aea5a434dbd099dcfb6553c76`.

## Credential handling and external scope

The expired personal token was replaced with unchanged repository-only code /
workflow permissions and a 30-day expiry. One subsequently generated token was
accidentally exposed in a browser tool output; the user replaced it again before
publication. The affected session ended without push/publication. The active
credential is entered through the hidden Terminal prompt, retained only in the
bounded 45-minute process memory and never saved in repository files/logs.
No corporate account or credential is used, and token rights were not expanded.

The user approved autonomous publication only under `volkue-tech/frame-gallery-ha`.
No new HA/Green/TV mutation, source-history reset or configuration.yaml change is
authorized or performed here. The unrelated untracked `docs/community/` is untouched.
