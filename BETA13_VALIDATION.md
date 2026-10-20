# Beta 0.1.0b13 validation

## Candidate scope — D-240

Fix reproduced duplicate initial-read dispatch around the existing dashboard
send. The service receives commands before ticking. A fixed ten-second
monotonic handoff defers the initial read while the existing script requests an
image. Claimed NEW_ARTWORK consumes initial and old off-edge evidence before
reap/publication/send; failure, no_match, unchanged receipt or failed post-send
proof cannot revive it. Only a fresh successful delivery arms its receiver.

Without a send, standalone configured initialization remains available once
after the handoff and continued valid cached on. Invalid/missing/off/unknown/
error/gap cancels pending evidence. Fresh later off/on, authentication refusal,
six/hour limits, exact per-device attribution and 90/900-second ages remain.
No field, helper, dependency, special Green permission or installed-card change.

The handoff cannot predict arbitrarily delayed actions. A later explicit send
must still reap an already established standalone receiver. The physical cause
of the reported Art-to-TV incident is not proved by the saved event_rejected
reason or these offline replays. No changed-runtime hardware/no-wake guarantee.

## Offline evidence

The unnumbered D-240 source passed all unchanged host gates: 5,943 tests passed,
16 genuine Linux/root-only skips, strict host/Linux typing over 303 files and
100% whole/mandatory line and branch coverage. Three in-memory negative controls
fail when grace, accepted-send supersession or input priority is removed.
They do not alter source files. Original sandbox group/setgid failures remain
retained; the complete normal-permissions runs pass without weakening tests.

The numbered b13 candidate also passes the unchanged complete gates: 5,943/16
platform skips in 58.48s, 303-file strict host/Linux typing, Ruff/format and
100% coverage (11,491 statements/2,744 branches; mandatory 8,769/2,028).
All five complete current-card YAML blocks are byte-identical to b12.
Preserve existing cards/scripts and
unrelated untracked docs/community. No HA/TV connection, installed-app update/
start or dashboard edit is part of this authorized publication round.

## Frozen matching sources — verified

- Runtime/source commit: `cb4c2e10ddf8e0f0315a7303f126f75883794f1d`.
- Matching public [source-only release](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b13):
  release 418431356, asset 659404550.
- Source archive: 581580800 bytes; SHA256
  `2dbd5327dcd5af3471e4cf7b570c4bddbe0722b8dbae51239e929a4589f93c25`.
- The complete anonymous archive, frozen project snapshot and all
  174 retained source archives passed exact-member verification before image distribution.
- Runtime fingerprint: 117 files; aggregate SHA256
  `69546a3b50cd74814f91a8a34415b0caafdef60f408a1b3ccba801c792041222`.

## Native and public release gates — passed

[Native publisher run 39474600949](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/39474600949)
completed all five jobs successfully on the frozen source commit and
`codex/commons-default`: approval, native ARM/Intel validators and both actual
native publisher images. Each production suite passed **5951 tests/eight
root-only skips**, plus **eight separate root tests**, on Linux/Python 3.14.8.

Four downloaded archives passed exact GitHub byte-hash, run/commit/actor
provenance, bounded ZIP/content and required-file checks:

| Evidence archive | GitHub artifact ID | Bytes | SHA256 |
| --- | --- | --- | --- |
| `native-aarch64-validation` | 12288779786 | 23779 | `5d6d876faf9bd0c46bc9438fda1367564669110b7b53fa58517dbd5f0cf3e69b` |
| `beta-aarch64-evidence` | 12291091584 | 21069 | `dcec815679dad72746714bb2ba6a3a5df41b10a5e56c2d60d239e3b87183f333` |
| `native-amd64-validation` | 12288889627 | 23713 | `bef4609acc52b67f93dcabbc8d84907dad96f97fd72dd103660d91cd56a022e6` |
| `beta-amd64-evidence` | 12290312387 | 21078 | `7fe3ac11d10fd590d3646c684350f6d9527421cdeafbbd4b2a8c88bd9bb402f6` |

Each archive verifies thirteen real preparation cases twice (**26 preparations**
under the 1-GiB limit) and **150 inspections with zero failures**. The following
maxima are calculated across the validator and actual-publisher receipts for
each architecture, not copied from an earlier beta:

| Native architecture | Highest peak VM | Slowest preparation |
| --- | --- | --- |
| ARM/aarch64 | 771.6 MiB | 2.38 s |
| Intel/amd64 | 768.0 MiB | 3.02 s |

### Public immutable images and independent signatures

- ARM: `ghcr.io/volkue-tech/frame-gallery-ha-aarch64@sha256:642e6f72cd1ce8bc101d385c17224da9628dbefecda8d511dcaf12f2eacacf54`.
- Intel: `ghcr.io/volkue-tech/frame-gallery-ha-amd64@sha256:dd820755086de26489a3ee74167c03d96ba1c74506bc7ae85a701e2aa6ad4539`.

Anonymous tag/digest bytes, source/revision labels and isolated imports passed
for both images, including the exact 117-file runtime fingerprint, unchanged
1,000-work catalogue/defaults and D-240 deferred-initial/supersession probes.
The Intel import on this Mac is emulated inspection; the native Intel evidence
is the corresponding GitHub job, not that local import.

Independent pinned Cosign verification passed for both exact immutable digests,
with workflow identity
`https://github.com/volkue-tech/frame-gallery-ha/.github/workflows/publish.yml@refs/heads/codex/commons-default`,
issuer `https://token.actions.githubusercontent.com` and the frozen
`cb4c2e10ddf8e0f0315a7303f126f75883794f1d` workflow commit. Image, signature and publisher
evidence references agree.

### App release and operational handoff

Public [app prerelease v0.1.0b13](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b13)
has ID **418764916** and targets the frozen runtime/source commit.
Both exact approval variables were independently reloaded/read back as
`DISABLED_AFTER_0.1.0b13` at 2026-10-20 19:06:51 UTC.

The documentation-only Store handoff is a later commit, not a new image build.
It preserves all 16 complete YAML/code blocks across exactly 17 documentation
files and leaves runtime/config/workflows/dependencies unchanged. Record its
actual main SHA and final 38-file/public-main/release/source/image cross-check
in local closure receipts after the last push; no future commit is invented here.
End broker and verify exact PID absence before handback. Native Terminal UI
cleanup is technically prohibited, not silently completed.

The fixed ten-second window cannot predict arbitrarily late scripts. These
release gates neither establish the physical Art-to-TV incident's cause nor add
new TV/sleep/no-wake or mode-safety evidence.

Earlier b12 results are historical, not changed-b13 evidence. Publishing never
starts/updates installed HA apps, sends an artwork or edits cards/scripts.
