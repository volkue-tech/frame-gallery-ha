# Beta 0.1.0b10 — event-sequence recovery and safe diagnostics

2026-10-18. The [app prerelease](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b10)
is public (release 416643274), after both native validators, actual publisher
images and independent public-image/signature checks passed. This documentation
handoff does not change frozen runtime/source e2c997be97b55016c46d75941890a6324198cc05.
No installed-app update, new TV test or universal no-wake guarantee is claimed.

## Scope and compatibility

D-237 distinguishes incomplete sequences of strictly recognized notifications
from fatal protocol/transport failures. Incomplete order or pending expiry
clears all current attribution and pending parts, retaining only the same
bounded receiver. A new whole matching five-second triple is required; no late
halves, discarded event, bare ID or duplicate can create/renew a caption.
Unknown/malformed/stale/future input, off/standby, identity/resource/publication
failures still stop without reconnect. Fixed allowlisted failure codes identify
the failing stage without raw messages, credentials or exception bodies.

No dependency, provider, catalogue, filter, stored association, helper/card ID,
protected app permission or media mapping change. No new query, thumbnail,
client ping, network profile or automatic resume. Background stays default OFF.
Existing last-upload cards stay separate from the optional current-information
card; no installed HA app, TV or card changes are part of this release round.

## Evidence and limitations

Eight authored restart regressions fail on unmodified b9. Offline fixed tests
cover incomplete order/timeout, no late-half/same-ID confirmation, a later valid
cycle, known/unknown per-device metadata and immutable stores, bounded logging
and rejection of arbitrary diagnostic strings. The pinned-library socketpair
replay has one channel, five initial getters, one initial thumbnail and zero
post-baseline application requests. These are offline results, not raw captured
proof of what happened during the b9 live failure.

The saved HA trace on 2026-10-18 confirms a successful initial current caption,
normal expiry, then unavailable at 19:54:55 CEST. The production log has no raw
event/failure reason. The exact cause remains unproven. No new hardware/sleep
pass, all-model/firmware support or guarantee that every failure is fixed.

Full unchanged host gates passed 5773 tests/16 genuine Linux-only skips, strict
host/Linux typing over 296 files and 100% whole/mandatory line/branch coverage.
Two sandbox-only group/setgid failures were retained and the complete unmodified
suite rerun outside that sandbox without exclusions. The full versioned rerun
also passed: 5773 tests/16 skips, 296-file typing and 100% line/branch coverage.

The complete unchanged suite was repeated during this publication round after
the five-language handoff edits: 5773 passed/16 Linux-only skips in 48.89s,
strict host/Linux typing over 296 files, Ruff/format and 100% whole/mandatory
line+branch coverage. No test or protection was excluded. Retained log
`build/current-artwork-b10-release/handoff-gates.log`, SHA256
2a9bb7b697b80552136e157d62f21c266fed08003b5a60b76fc100695f3e1ca1.

## Hosted native and actual publisher evidence

[Run 39154228750](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/39154228750)
completed all five jobs successfully at the exact frozen candidate. Each of the
four archives passed completed-run/repository/actor/branch/commit provenance,
API byte count/SHA256 and bounded safe extraction/content checks. Each records
5781 production tests/eight root-only skips, all eight separate root checks,
26 successful preparations under real 1 GiB RLIMIT_AS and 150 inspections with
no failure. Native validator archives also contain the full host quality gates;
each image contains the 202-file original public licence evidence bundle.

| Evidence | Artifact | Peak VM | Slowest preparation | ZIP SHA256 |
| --- | --- | --- | --- | --- |
| Native ARM | 12146986889 | 771.6 MiB | 2.25 s | 9968beeb85a69634b525d1fb7820c39a3df80222eae8213ec687b8b534950067 |
| Native Intel | 12146908152 | 768.0 MiB | 3.04 s | 4a32cd42d3f8b7546ae8dc8c8beb6f7cad0ada44f529be7c9c8e1a5e2704e3c7 |
| Actual ARM publisher | 12147556272 | 771.6 MiB | 2.30 s | 964b8e46eb440454f64918168db2edf0c558ddf8ad269d39e0a4e85c4b2025e3 |
| Actual Intel publisher | 12147755091 | 768.0 MiB | 2.05 s | f91c7efbee2cff97018bf28a8ad54d4cbec7b7f0a96ab90ba016e23a79bf96e9 |

Anonymous tag/digest readback, exact-digest pulls and isolated unprivileged,
read-only/no-network imports passed for both images. Each has version b10,
1000 works/557 artist choices, background default OFF, an empty production
reviewed-policy registry and the exact 116-file runtime fingerprint
bd374026addf0c6db02daf783d013602c52df4eea9f3043024a35345c77d600c.
Intel imports on this ARM Mac are emulated inspections, not the separate native
Intel CI proof. Both immutable digests match their publisher evidence:

- ARM: sha256:d1f64b20a5651dfd56803845ccdbbc82671dc153c5b05b69bea4bca797a2edde
- Intel: sha256:39961822364abb45499f26a95d6fcfdbcd74a701945370341ea7f18e81727e18

Independent Cosign checks bind each digest to the exact source commit,
publish.yml on refs/heads/codex/commons-default and issuer
https://token.actions.githubusercontent.com. No personal registry credentials
were used for these public pulls/signature checks.

## Release gates

- [x] Freeze a clean personal exact commit after versioned host checks:
  e2c997be97b55016c46d75941890a6324198cc05.
- [x] Publish matching hash-verified source package; anonymous full preflight.
  Source release 416618218, asset 654147081, 581416960 bytes, SHA256
  1f9a341990cad9e967fe284e6fe250ea7f30fcd3b40ba7894e2125a39a3dd664.
  All members and the exact clean project commit passed; 174 retained upstream
  archives. This source existed publicly before the image publisher ran.
- [x] Native aarch64 and amd64 validators and actual publisher images.
- [x] Exact evidence archive provenance/hash/content, real isolation/root and
  1-GiB image preparation/inspection gates on both architectures.
- [x] Anonymous immutable-image pulls/imports and independent Cosign signatures.
- [x] Public app prerelease after green checks; this documentation-only commit
  prepares the Store/main handoff without changing the frozen runtime/source.
- [x] Both one-time approval variables saved and independently visually read
  back DISABLED_AFTER_0.1.0b10. No token permission expansion.

The memory-only broker is ended after the final push, not before it. Public
byte-exact Store readback, the additional automatic main validation and process
closure are post-push receipts under the ignored directory below. No completed
post-push result is inferred in this pre-push documentation snapshot.

All release receipts are retained locally under
`build/current-artwork-b10-release`; no private credentials belong in this report.
