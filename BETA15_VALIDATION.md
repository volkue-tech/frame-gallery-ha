# Beta 0.1.0b15 — optional same-connection synchronization

No Home Assistant/TV connection is part of this task. Installed b13 remains
stopped. Existing native cards, scripts, data and privileges stay unchanged.
b14 is retained only as its immutable corresponding-source intermediate;
it was never promoted as an app/image/Store release.

## Behaviour and explicit risk choice

The separate experimental `current_state_refresh` switch defaults OFF and
requires a granted background Art session. At most once per minute it reads
mode/current/current/mode on that SAME socket, requires fresh correlated replies,
matching IDs and mode-on at both ends, and resolves only the pinned TV archive.
Unknown works borrow no title. Static/same/changed art and missed mode-on events
can recover without upload or a replacement Art connection.

Menu/Art-off clears captions but keeps bounded mode-only reads until fresh on.
Art-off is not physical standby. If startup sees off/nav, the original single
initial thumbnail proof is deferred until fresh on, under the shared five-second
deadline; no ID-only first caption or recurring thumbnail download. Standby,
HA-off, cancellation, refusal and closed transport stop without blind reconnect.
After an actual disconnect, only the existing explicitly permitted startup/
fresh HA off-on/delivery grants can open a new session. This is not an unlimited
reconnect mechanism or a literal guarantee after every possible fault.

Attempts share five seconds/64 frames, minimum60s actual attempt spacing even
with parent backpressure, at most480 in the existing eight-hour session.
No power/mode/image setter, keepalive, dependency or special Green privilege.
Fresh current-state proof ages after90s, compatible with unchanged native YAML.
Read connections/requests can affect automatic sleep: offline tests cannot
certify physical no-wake or sleep behaviour across firmware/configurations.

## Observed offline evidence

- Final unchanged check.sh:6045 passed/16 platform skips in52.31s.
- Ruff/306 formatted files and strict host/Linux typing passed.
- Whole line/branch100%:11703 statements/2826 branches.
- Mandatory100%:8935 statements/2088 branches.
- Actual pinned library over socketpair checks same Art URL, fixed getters,
  one original thumbnail, deferred off/nav startup, exact device and shutdown.
- Parent/controller covers caption clearing, single retained opted-in session,
  deferred baseline, known/unknown metadata and terminal standby.
- Earlier development typing/style failures retained, not skipped or weakened.
- Post-documentation repeat: two workspace owner/group/mode assertions failed
  in the Mac sandbox (6043 passed/16 skipped). The identical full suite outside
  that sandbox passed6045/16 in73.91s, with the same100% coverage and typing/
  format gates. Both logs are retained; no source/test change or new skip.
- Six in-memory guard-removal controls produce expected failures: coherent
  equal IDs, correlation, explicit policy, Art-off recovery and actual attempt
  spacing and no repeated thumbnail after initial-proof expiry. They do not
  modify production or test source files.
- Eight virtual hours through the actual worker loop:479 coherent reads,
  1916 read requests, minimum60s spacing and finite shutdown without another
  send at the deadline. No real device or sleep-safety claim.

The b13 rejected frame was not retained; these synthetic cases do not claim
to reconstruct it or prove its physical cause. The release evidence below is
for the final candidate, not b14 or the earlier unpublished b15 candidate.

## Observed release evidence — 2026-10-21

- Frozen final source commit: `ab9e65cb313a8ef05560f182e958a441bc8a44c6`.
- Public corresponding-source archive: 581693440 bytes,
  SHA256 `6c04e57bb16b488bc68ae221c5a9fbe7d6227f1fef8b8829da8b39ab8a771d17`.
  Source release `419269918`, asset `661711952`; anonymous full download, hash,
  archive members and frozen-project preflight passed before image distribution.
- Runtime tree: 118 files,
  SHA256 `e704ca0e1822c6f860280392e6d47c868f0ee38481663fa2ba339d18b35a43c4`.
- [Native run 39562816594](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/39562816594):
  all five jobs succeeded. Each of the four native suites passed 6053 tests,
  skipped the same 8 root-only checks and separately passed all 8 root checks.
  Every archive's own-repository/run/source provenance, byte length, SHA256 and
  bounded contents were independently verified.

| Native artifact | Artifact ID | Bytes | SHA256 | Peak VM MiB | Slowest preparation s |
| --- | --- | --- | --- | --- | --- |
| aarch64 validator | 12329247482 | 23793 | `268981429afa95b605cc41606692afaf9c52f087f21a86f16b9a222847cf4fb4` | 771.6 | 2.26 |
| amd64 validator | 12328954710 | 23777 | `8600885f32ce6026654be4a3b52f6af266a0cf168d2fa25b484d5866d1ea9326` | 768.0 | 3.01 |
| aarch64 publisher | 12329828587 | 21120 | `50d7265f3f3ca2ad3d20f1bf5b68d74086919a183b22d3fd51e66d99263c7dfd` | 771.6 | 2.32 |
| amd64 publisher | 12330114041 | 21118 | `b86ef97ca3f7bea4cf49de707c5adcaf1f71442229a19e4e4ad38bcfc3f22e6c` | 768.0 | 2.93 |

Each suite measured 13 cases twice (26 actual preparations) under the 1-GiB
limit and completed 150 concurrent inspections with zero failures. These are
native Linux results; the later local AMD image-import probe is emulated and
does not substitute for native Intel validation.

Anonymous pulls of both exact public tags/digests and isolated, read-only,
networkless non-root runtime imports passed. Both contain the exact 118-file
runtime above, 1000 works/colour profiles, and default-OFF refresh/background
settings. Immutable images:

- ARM: `ghcr.io/volkue-tech/frame-gallery-ha-aarch64@sha256:e96196f5f3b0c230aee5f5a6a90605ad07bfa8068d2bbaf5b81d878eb5cd57c3`.
- Intel: `ghcr.io/volkue-tech/frame-gallery-ha-amd64@sha256:05869f91bb5a7809b540cde68c8dae307a519c08a8d5439bc28bbaaf965fa534`.

Independent anonymous Cosign verification passed for both immutable digests,
issuer `https://token.actions.githubusercontent.com`, exact source commit above
and certificate identity
`https://github.com/volkue-tech/frame-gallery-ha/.github/workflows/publish.yml@refs/heads/codex/commons-default`.

[App prerelease v0.1.0b15](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b15)
is release `419307088`, targeting the frozen source above. Both exact build
approval variables were disabled and UI-read back as `DISABLED_AFTER_0.1.0b15`.
This 17-document handoff preserves all 16 complete code/YAML blocks and the
runtime/configuration/workflows/dependencies. Immediately after main promotion,
the final anonymous 38-file/release/Store cross-check and broker-PID exit are
recorded locally under `build/current-artwork-b15-release`; this commit does
not pre-claim those subsequent operations. Native Terminal window control is
prohibited: no window-cleanup claim or bypass is made.

[Matching b15 sources](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b15)
must be publicly verified before image distribution. No installed app start,
update, card/script change or new hardware test is part of publication.
