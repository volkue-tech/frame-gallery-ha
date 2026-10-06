# Frame Gallery 0.1.0b5 validation

## Released scope

400 pinned Commons JPEG works from 299 artist labels: all 166 b4 entries
unchanged plus 234 visually reviewed additions. Original width >=3000 pixels;
relative 16:9 deviation <=2.5%. The stricter 1% preference is unchanged (152
original source ratios meet it). Contain remains the no-crop default.
Commons is first/default for new installations; saved sources, sent-history
IDs and dashboard helpers remain compatible. Five basic options remain.
The Info/setup hero is an authentic credited historical b3 Green screenshot,
not fabricated UI or a new b5 hardware test.

The dated private research retains caches, identities, source-page evidence,
visual decisions, 26 reserves and all 34 older deferred proposals. Public
metadata-only manifests are under `frame_gallery/research/commons-400-*.json`.
No artwork files, dependencies, permissions or discovery scans are added.
Commons rights metadata is not worldwide legal clearance.

## Observed local checks

The production guarded gateway and Commons adapter accepted 400/400 records
in eight bounded metadata-only passes, 74.45 seconds in total. This is not a
single normal app run, full image decoding or TV evidence.
Local full gates: 5,006 tests passed, eleven platform skips, 100% line/branch
coverage (9,426 statements / 2,054 branches), Ruff and strict mypy (248 files
on Mac and Linux). Existing AIC-only fixtures explicitly select their source;
missing/null-source Commons runtime wiring is separately tested.

The publication-documentation recheck initially failed two Mac file-mode/group
tests inside the execution sandbox (the expected setgid inbox mode did not
persist). The same complete gates outside the sandbox passed 5,006 tests,
eleven platform skips, strict mypy/Ruff and 100% line/branch coverage. No runtime
code, skip rule or coverage threshold changed. Native Linux evidence below
independently passed the same file-mode/group checks.

## Corresponding sources and native pipeline

Frozen runtime/source commit: `44b727881981fd158f1f4fa9293f9d6a793ba1ee`.
The public [source-only release](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b5)
contains `frame-gallery-sources-0.1.0b5.tar`, 523,089,920 bytes, including the
own clean source snapshot and 172 retained upstream archives/notices.
SHA256: `d810c71ed634f3936e5761032c694e7fd9413374349acd5a1b41dd50e04f8637`.
Anonymous download and tracked preflight verified version, exact commit/hash
and every source member. Earlier public source releases remain unchanged.

Both exact approval values were read back in the personal repository UI.
Manual [run 37536546471](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/37536546471)
on `codex/commons-curated` completed successfully: approval, both native
validators and both actual image publishers, total duration 35m 42s. The final
success/commit/job counts were read in the existing personal Firefox session;
the anonymous watcher stopped after an API rate-limit 403 and was not retried.
No new token permissions were granted to work around that limit.

Both native validation ZIPs were downloaded through the personal GitHub UI,
matched the public SHA256/commit, and were safely extracted. Each host and
non-root container suite passed 5,012 tests (five root-only skips); the separate
root pass passed all five checks. All 13 worst-case image scenarios, twice each,
passed with the unchanged real 1 GiB limit: peak address space 765.5 MiB on ARM,
761.8 MiB on Intel; slowest observed preparations 2.16 s / 2.30 s. The 150
batched inspections per architecture had zero failures. These are native CI
measurements, not new HA Green or TV observations.

## Actual published images and independent checks

Each actual publisher image repeated the 5,012-test non-root pass, five-check
root pass, all 13 memory cases twice and 150 batched inspections with no
failures. Publisher peak address space: ARM 765.5 MiB / Intel 761.8 MiB;
slowest image preparations 2.16 s / 2.64 s, under unchanged 1 GiB/15 s limits.
The label-only publication verified unchanged root filesystem layers.

| Architecture | Immutable published digest |
| --- | --- |
| aarch64 | `sha256:f0a7af783856a1bf5478802cf4f29628d1c8523674af650805993da9b12629fc` |
| amd64 | `sha256:e237440afeb8892cc972f85200d8a46e9157bc14c064e63036fe809dfa81fef6` |

Anonymous registry tag/digest bytes, image pulls, architecture/version/source/
revision labels and isolated catalogue imports passed on both images: b5,
400 unique page IDs/hashes, 299 artist labels, Commons default and ten metadata
batches. Catalogue imports ran read-only as uid 65534, with no network or host
data mounted. The Mac's Intel import is emulated inspection, not native Intel
validation; native Intel evidence is from CI above.

Independent Cosign 3.1.3 verification passed for both exact digests, GitHub's
OIDC issuer and certificate identity
`https://github.com/volkue-tech/frame-gallery-ha/.github/workflows/publish.yml@refs/heads/codex/commons-curated`.
Only the hash-verified signing tool was mounted read-only; no GitHub, Docker,
Home Assistant or TV credential was supplied to these checks.

All four evidence ZIPs were downloaded and matched their displayed public run
hashes/approved commit, safely extracted and retained locally. Native metadata
was additionally read through the anonymous API before its rate limit; both
publisher artifact IDs, exact byte sizes and hashes were read from their UI
upload logs. Both retained published-digest files match anonymous registry
readback exactly.

| Evidence | Artifact ID | Bytes | SHA256 |
| --- | --- | --- | --- |
| native-aarch64-validation | 11448010610 | 22674 | `770c1911c749c3f5a5663436a6514e4dde055c378dd104660a6caafb094b30a9` |
| native-amd64-validation | 11448030662 | 22586 | `182f8295e35ff90eae9148f96c9c7fe5c587d9166ab401dabe7be9e5179f8925` |
| beta-aarch64-evidence | 11448207700 | 20195 | `937a0d42d2468333ca78e1f0435051f3b5681973ea74bd3649dfc2307c9624d5` |
| beta-amd64-evidence | 11447194448 | 20206 | `60b373c9cb49f4cbe4f79272f3dfe6463a729554c9c967bf7228c7c5c089ef7a` |

## Publication receipt

The user explicitly approved publication and a bounded memory-only personal
volkue-tech credential session on 2026-10-06. All image/source/signature gates
passed. Public prerelease
[v0.1.0b5](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b5)
was created at 2026-10-06 22:26:34 UTC (2026-10-07 00:26:34 Europe/Berlin),
release ID `405188764`, `draft=false`, `prerelease=true`, exact frozen target
`44b727881981fd158f1f4fa9293f9d6a793ba1ee`. Its source-only release description
now links this beta. Public Store main handoff completed at
`6a79f8cc6b7d54a174d4ac6f45eb8f4625138940`; authenticated ref readback returned
HTTP 200 with the exact commit at 2026-10-06 22:30:23 UTC. The final nine-file
documentation gate passed 5,006 tests and 100% line/branch coverage before push.
Both one-time approval variables were set to `DISABLED_AFTER_0.1.0b5` and read
back in the personal repository UI after both publisher jobs completed.

Existing releases, sources, tags and images remain unchanged. No new HA Green
or TV access/test is authorized or claimed for b5; historical hardware evidence
remains separate. Samsung IP discovery remains deferred. The bounded personal
credential process closes after the final documentation push, without saving
the token. Browserless personal release access is recorded only as a later task.
