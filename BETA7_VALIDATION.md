# Frame Gallery 0.1.0b7 validation

## Publication gate — verified beta; Store documentation handoff prepared

The app beta, corresponding sources and both signed images are public. All five
native pipeline jobs, four evidence ZIPs and independent public image/signature
checks passed. Both one-time approval values were disabled and read back. The
Store metadata/documentation handoff is prepared after these checks; its exact
push/ref readback is recorded separately rather than inventing a self-referential
current commit hash.
No new HA Green, television or live frontend-language test is authorized or
claimed for this release. Only observed results are recorded here.

## Reviewed scope

Optional Commons artist selection accepts offered whole catalogue names/keys,
or a dedicated optional helper. The 560 original attribution strings yield 557
normalized selectable labels; selection-only abbreviations retain the original
captions/pins. This is a catalogue choice list, not an artist authority database.
Displayed counts are catalogue totals, not remaining unsent matches.

Artist and colour are intersected before artwork requests. Shape fallback never
widens either filter. Missing/invalid helper values warn and use the static wish;
other sources report Commons artist/colour as ignored. Genuine exhausted-artist
tests preserve the TV, preview and caption, finish cleanly and never reset history.
The 1,000 works, source pins/rights, saved IDs, sent/upload/quarantine protections,
defaults, request/worker/deadline limits, dependencies and privileges are unchanged.

Complete artist-only and artist-plus-colour cards use native cards and optional
favourite Dropdown helpers. Existing camera/timer/script and standard cards remain
unchanged. No automatic card/helper writes, HACS or configuration.yaml changes.
All eighteen configuration fields have generated English/German/French/Spanish/
Italian names and help. The HA frontend chooses configuration language; Markdown
guides use manual links. Technical values/IDs remain English. Setup, colour and
artist instructions and matching complete examples cover all five languages.

History reset is discussion-only (D-223), not a shipped cache-delete control.
No catalogue expansion, new source, IP discovery or multi-colour UI is included.

## Observed local checks

The numbered candidate passed the unchanged full gates with observed exit 0:
Ruff/format, strict host/Linux mypy over 255 files, 5,116 tests passed with eleven
unchanged platform skips, 100% whole-package line/branch coverage (9,468 statements,
2,068 branches) and mandatory-package coverage (7,751 / 1,714).
`build/artist-b7-release/local-quality-commit.log` records the precommit run.
The documentation-preparation full run also passed with the same counts and
coverage (`local-quality-doc-prep.log`). No test, skip or threshold was relaxed.

The first numbered-candidate run found stale own-package b6 versions in
pyproject.toml/uv.lock (5,115 passed, one failed, eleven skips). Only those own
version fields were synchronized; the unchanged full rerun passed. Earlier
implementation regression and genuine exhaustion/retention results are retained
in STATUS.md. No local result is relabelled as a native Linux or hardware result.

## Corresponding sources

Frozen runtime/source commit: `d15c1ffec63c3af0ad8ec2599b58d07e748cec15`.
The public [source-only prerelease](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b7)
contains `frame-gallery-sources-0.1.0b7.tar`, 580,116,480 bytes, including the clean
own-source snapshot and 172 retained upstream archives/notices.
SHA256: `a5ecbf2ba5ebc057d20e1546a99dffa4f8ef0a60f86848b70e60993cb9a207bc`.
Source release ID: `409469678`; asset ID: `629983716`.

GitHub's asset size/digest matched. An anonymous public download and exact clean
snapshot preflight passed: version, approved commit/hash, project archive, fixed
upstream records and every archive member. No downloaded upstream code was
executed. The first private verification invocation used the system Python and
then a relative path rejected by the path guard; the existing project Python
and absolute guarded package path passed without changing sources or guards.
Integrity verification is not a claim of byte-identical rebuilding. Earlier
source releases remain available.

## Native pipeline — completed successfully

[Run 38118401015](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/38118401015)
was manually started on 2026-10-11 at 08:32 Europe/Berlin, branch
`codex/commons-default`, exact frozen commit above. All five jobs passed:
approval, both native validators and both actual-image publishers. The run
completed at 2026-10-11 07:07:14 UTC (09:07:14 Europe/Berlin).

Both downloaded validator ZIPs matched the exact public API metadata, size,
SHA256, run, personal repository, branch and frozen commit. Safe bounded
extraction executed no archive contents. Each native host passed its complete
quality gates. Each test container passed 5,122 tests with five root-only skips,
then all five separate root tests. Thirteen worst-case image inputs passed
twice under the unchanged 1 GiB address-space limit; 150 inspections with ten
workers completed without failure. A private verifier's transformation-count
guard initially expected three old count literals; inspection showed exactly
two. The guard was corrected to two before extraction. The required b7 suite
count, archive hashes/sizes, safe extraction and measurement checks were unchanged.

| Native host | Peak address space | Slowest preparation | 150 inspections |
| --- | --- | --- | --- |
| Linux aarch64, Python 3.14.8 | 765.5 MiB | 2.15 s | 1.27 s, zero failures |
| Linux x86_64, Python 3.14.8 | 761.8 MiB | 1.94 s | 1.03 s, zero failures |

- `native-aarch64-validation`: artifact `11694767945`, 22,717 bytes,
  SHA256 `a95818787cdf06ea8f87ed07f2a18b011fb0ecc319f28f8d97b8140720f4e94f`.
- `native-amd64-validation`: artifact `11694219422`, 22,676 bytes,
  SHA256 `6762503e88c5c8265510c243577236163814253981184676ddbc323c6c59cb53`.

Public metadata, ZIPs, extracted logs and verification receipts are retained
under `build/artist-b7-release/`.

## Independent public-image checks — both architectures passed

The ARM publisher passed and its exact evidence ZIP matched public metadata:
artifact `11695130275`, 20,233 bytes, SHA256
`debb494649dc1a3b4643029f4745211c6af4db05ef7e0517e3d7b34f97125b58`.
It repeated 5,122 container tests/five root skips, all five separate root tests,
thirteen inputs twice within 1 GiB and 150 inspections with zero failures.
Peak address space was 765.5 MiB; slowest preparation 2.18 s; inspections 1.35 s.

Anonymous ARM version-tag/immutable-digest manifest readback, digest bytes,
pull, exact architecture/version/source/revision labels and isolated imports
passed with exit 0. Import used uid 65534, read-only/no-network/no-capabilities
and no host data. The actual image has exactly 1,000 pinned works/profiles,
560 original artist strings, 557 offered normalized choices, twelve colours
and 385 blue matches. Known artist lookup, unchanged Commons default/ten
five-record batches and exact unchanged catalogue/palette source hashes passed.

ARM immutable digest:
`sha256:42290c4f9e5e6440b0cca27f5cf7a0289f2677e12661548914cfe5cfab8c76af`.
Independent hash-pinned Cosign 3.1.3 verification passed with exit 0 for that exact
digest, frozen workflow SHA, issuer `https://token.actions.githubusercontent.com`
and certificate identity
`https://github.com/volkue-tech/frame-gallery-ha/.github/workflows/publish.yml@refs/heads/codex/commons-default`.
No personal GitHub/HA/TV credential was supplied to these public image/signature
checks.

The Intel publisher's exact archive also passed bounded integrity/provenance
verification: artifact `11695285928`, 20,241 bytes, SHA256
`1428a33f646171885dd2201eefd409e60e807bcd8c96f7d00a002e9c430f9713`.
Its actual image repeated 5,122 container tests/five root skips, all five root
checks, thirteen cases twice within 1 GiB and 150 inspections without failure.
Peak address space 761.8 MiB; slowest preparation 2.63 s; inspections 1.69 s.
Independent anonymous tag/digest, pull, exact labels, isolated imports/catalogue/
palette/artist lookup and exact frozen-workflow signature checks passed with
exit 0. This Mac's Intel import is emulated inspection, not native Intel evidence;
the successful native CI job is the native evidence.

Intel immutable digest:
`sha256:a0ecd563d2ed48f67f847f894eec266c184757616c1e9183bc36c0cee79ce3a8`.
The publisher label-only stage retained the validated runtime filesystem layers.
GitHub emitted a Node.js-20 action-runtime migration warning; the pinned actions
ran successfully under the platform's Node.js-24 execution. No action/dependency
pin or test/permission gate was relaxed in this release.

## Publication receipt

[Public prerelease v0.1.0b7](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b7),
ID `409494522`, was published at 2026-10-11 07:10:09 UTC (09:10:09 Europe/Berlin),
`draft=false`, `prerelease=true`, exact frozen runtime/source target above.
The existing source-release asset is retained unchanged; its description links
the app beta. After all publisher jobs finished, both existing approval values
were set to `DISABLED_AFTER_0.1.0b7` and visibly read back in the personal
repository. `build/artist-b7-release/approvals-disabled.png` records that result.

The publication-documentation descendant keeps runtime/source/images at the
frozen commit. Its full local gate and exact main/ref readback are required for
Store handoff; closure records follow the observed push, not an invented future
result. No previous release/source asset or user HA state is replaced/deleted.

## Credential handling and external scope

Only the existing personal volkue-tech token was used, constrained to the personal
public repository and held at most four hours in broker process memory. No token
was persisted or printed. Actions-variable and workflow-dispatch API writes were
refused; the user-confirmed Firefox session performed those authorized steps
without changing token permissions or retrying refused API writes. Public source
checks use no personal credentials. The initial anonymous metadata monitor hit
the public API quota (remaining 0 of 60, independently read back); it stopped.
Subsequent read-only metadata requests use the already-verified personal broker,
which returned HTTP 200 without any permission change. A private helper transformation
typo stopped before Git transfer; the corrected session pushed and verified the
exact candidate without changing application code.

Both one-time approval values are disabled. The memory-only broker must be
explicitly ended after the final authorized push/readback. HA state, dashboards
and television remain unchanged; this release does not authorize live HA mutations.
