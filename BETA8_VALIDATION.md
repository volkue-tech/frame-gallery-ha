# Beta 0.1.0b8 — native validation and publication

2026-10-16. **Both native architectures, public images/signatures and matching
sources passed the release checks. App prerelease 415386298 is public; this
documentation accompanies the Store main handoff. No b8 installation on the
user's HA.** D-230's subsequent user approval covers native Intel validation
and conditional publication.
Experimental observation remains default-off; natural no-motion sleep is untested.

## Observed hosted native validation and public sources

[Native run 38949768486](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/38949768486)
passed both real ARM and Intel jobs in 17m 1s for exact frozen commit
842a8ce3c26c436c3228db1a307e4f84750184a2. Both downloaded evidence ZIPs matched
GitHub's artifact digest and passed bounded, safe extraction and content checks.
Each actual Linux container passed 5385 non-root tests with seven root-only
skips, and all seven separate root checks. Thirteen preparation cases ran
twice under a real 1 GiB RLIMIT_AS, plus 150 inspections with zero failures.

| Native architecture | Peak virtual memory | Slowest preparation | Evidence ZIP SHA256 |
| --- | --- | --- | --- |
| ARM/aarch64 | 771.6 MiB | 2.16 s | b9334248f0d3c844dfb33ef1c8a0ec7b89909cfa429d8038a8f1b88e0f99377e |
| Intel/amd64 | 768.0 MiB | 2.31 s | ade2f3df6fb6baea154ed587d3b010449475b46a46068b130ffef2ca86b92249 |

[Corresponding sources](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b8)
are public: release 415290337, asset 648311285, 580403200 bytes, SHA256
d81b3196d3d17a1d99c3eae245183a2e87f88a49b7f3777d936c4fd4aff625b2.
The independent anonymous download and full every-member/exact-clean-snapshot
preflight passed. This contains 172 upstream source archives, not user state,
credentials or original artwork files. Native hosts emitted non-failing
Node.js 20 action-deprecation warnings; a future workflow-maintenance pass must
review the pinned action versions rather than silently weakening checks.

The personal Firefox workflow start worked; the token intentionally lacks
Actions-write/variable permissions. After the user's existing-password GitHub
confirmation, both exact approvals were saved/read back and
[publisher 38953833709](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/38953833709)
started on codex/commons-default at frozen 842a8ce/version 0.1.0b8.
All five jobs passed, including both actual native publishers. Both public
images independently passed anonymous tag/digest readback, pull/import,
catalogue/artist/default-off and exact 107-file source assertions. Cosign
independently verified both digests against the candidate-workflow certificate
identity, OIDC issuer and frozen source SHA:

- ARM: sha256:9fc3a7ef9775d512c8885926352028c580c2f757a5aedb1bcf86407f19914d3b
- Intel: sha256:e1e27e748a5a012b6e985350eac14a256752fefdb5bf7924c1a2f5ffba08592b

Both reusable-native ZIPs from this publisher also passed exact digest/provenance,
bounded extraction and content checks. Their SHA256s are
5ef5cd76ea17e08c0f0a2675fbcf5f7128b39e54ad8d300e622216a88e69ffe0 (ARM) and
f659bb376380ca3e983add358d9b685e7b51e50ffd0d8cbb85de917a37857949 (Intel).
Both actual-publisher ZIPs also passed exact digest/provenance, bounded safe
extraction and content checks. Their embedded published-image digests exactly
match the independently verified public images above:

| Actual publisher | Artifact | Peak virtual memory | Slowest preparation | Evidence ZIP SHA256 |
| --- | --- | --- | --- | --- |
| ARM/aarch64 | 12071012393 | 771.6 MiB | 2.16 s | 217d5a6f36f49836ebe5049dc7bdcc06056e74047c06d5af95155f7439c9b2a9 |
| Intel/amd64 | 12072290343 | 768.0 MiB | 2.93 s | ea97d17f864e01ef2f3a2cc4013da3934eec9c7fb4d95ea25ebafb0b6b9a9d5f |

Each actual image passed 5385 non-root tests, seven separate root checks,
13 preparations twice within 1 GiB and 150 inspections without failures.
[App prerelease v0.1.0b8](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b8)
is release 415386298, explicitly experimental/default-off and not the source-only
release. Images and corresponding sources remain tied to frozen 842a8ce;
this later documentation-only handoff does not change their runtime source.
Release receipts and all six verified ZIPs are retained under the git-ignored
build/current-artwork-b8-release/ directory. Documentation handoff 295f7c0 was
fast-forwarded to Store main without force. All 37 public Store/guide files
matched byte-for-byte; anonymous readback also confirmed the unchanged app
release/tag/source and all five polished guide links. Closure receipts are
recorded there separately; this does not claim a live app upgrade on HA.
The additional automatic native validation of documentation handoff 295f7c0,
run 38968787213, also passed both real ARM and Intel jobs. It did not rebuild
or replace either published image.
Both one-time GitHub release approvals were disabled and visibly read back as
DISABLED_AFTER_0.1.0b8 in the personal Firefox session after publication.
No credential, permission scope, installed HA app or TV state was changed.

## Scope and compatibility

- Default/missing/null background mode keeps the one-shot path and old cards.
- Opting in requires one send-script body update, not new card IDs or helpers.
  Optional current information uses an app-owned ephemeral HA state and a
  native Markdown card. The old preview/caption still means last delivered.
- Start/boot/restart never connects to the TV. A successful explicit send and
  a freshly changed valid current record with TV ID arm observation. Exit 0
  alone cannot arm it: no_match and several error outcomes also exit 0.
- The first post-delivery read can enroll an exact hashed device identity;
  later reads enforce a persistent per-address pin before opening Art Mode.
  Pins are limited to 32/16 KiB, never silently evicted/replaced, and do not
  persist a permission to resume. Damaged/newer pin files fail closed.
- A tokenless channel grant is session-only after that successful send, not a
  rejected-token fallback. Read/auth/mode failures disarm without reconnecting.
- Reads use fixed getters only, a five-second worker deadline and targeted
  thumbnails. Initial association additionally needs isolated five-second
  proof against the exact processed preview. No guessed legacy captions.
- Startup cleans interrupted temporary writes under the existing state lock;
  history/quarantine protections, catalogue, filters and dependencies are unchanged.
- Configuration warnings and complete current-information guides are supplied
  in EN/DE/FR/ES/IT. Read-only connections may wake a sleeping TV. No power,
  Wake-on-LAN or Art-Mode setters are part of the observer.

## Observed local results

`frame_gallery/scripts/check.sh`, observed exit 0:

The final documentation handoff rerun also passed with these unchanged counts;
its log is build/current-artwork-b8-release/final-gates.log.

- Ruff check and format passed.
- Strict host and Linux mypy passed over 273 files, without relaxations.
- 5377 tests passed; 15 platform-only cases skipped on macOS.
- Whole package: 100% line/branch coverage, 10246 statements/2304 branches.
- Mandatory gate: 100%, 8197 statements/1864 branches; no gate reduced.

`scripts/container_check.sh aarch64`, observed exit 0, native ARM Linux:

- Runtime/test/default Dockerfile targets built; default equals runtime.
- Exact pinned dependency inventory and 201 original notice/evidence files
  verified; no new dependency or external artwork bundled.
- Exit propagation, real stdin transport, Supervisor-token environment and
  SIGTERM cleanup passed. Stop took 11 seconds, within the 20-second budget.
- The shipped entry point refused an unprofiled Docker container. The separate
  internal no-network smoke wiring completed its expected unreachable outcome.
- Unprivileged Linux suite: 5385 passed, 7 root-only skips. All 7 separately
  executed root-isolation checks passed, including observe/verify_thumbnail.
- Containers ran with `--network none`; no HA or TV call was made.

## Historical local Intel/AMD emulation limitation

The local amd64 runtime/test images built successfully. Container inventory,
notices, exit/stdin/stop/environment/smoke checks and the seven root checks passed.
The **overall emulated container check failed**: 5380 tests passed, 7 skipped,
5 real-kernel seccomp tests failed (prepare, inspect, deliver, observe and
verify_thumbnail). One fixed, network-disabled diagnostic reproduced
`OSError: [Errno 22] network_filter_install` at PR_SET_SECCOMP under this Mac's
amd64 emulation. No protection or test was weakened or newly skipped.

Native ARM passes these same kernel tests. The emulated evidence did not approve
native amd64; the subsequent actual x86_64 validation above now satisfies that
separate gate without changing a protection or test.

## Exact local runtime source check

The checkout and both runtime images contain the same 107 non-bytecode runtime
package files, verified after the final code build. Aggregate SHA256:

`302cbb4d2948b23517e6d5e807b3f479b2ac6cdeac9b38fa0f3e661a8e877ce7`

This digest concatenates sorted relative UTF-8 paths, a NUL byte and each file's
binary SHA256, then hashes the concatenation. It is a local source-tree check,
not a public signature or proof of a published image/source package.

Local Docker configuration IDs (not registry digests):

- ARM: `90b4fde3682e09c892355ccea23fcf210e1b671e5bba4d49ab7d34e1bba0e9db`
- AMD64: `30f7b9fd6c3412c8a38eb7f6a746f668c5dea903e377faada861de16c12a0efe`

Evidence is retained locally under `build/current-artwork-live-20261016/`:
`b8-final-gates.log`, `b8-container-arm64-final.log` and
`b8-container-amd64-emulated.log`. Detailed container outputs remain under
`build/container-checks/{aarch64,amd64}/`. Build artifacts are git-ignored.

## Earlier hardware evidence and remaining checks

Before D-230 activation wiring, an explicitly authorized disposable Green test
completed one read-only Art-Mode identity/ID/thumbnail cycle, strict preview
comparison, persisted mapping and independently verified HA title/artist.
The actual native template displayed that attribution, then hid it after expiry.
Existing dashboard hashes and preview bytes were unchanged; the temporary app
was removed. This is narrow getter/mapping/template evidence, not a b8 upgrade.

Still open: natural no-motion sleep/no-wake, automatic mode/ID/slideshow
transitions, sustained polling/Recorder impact, real b8 migration and card layout.
Native x86_64 validation, explicit publication approval, matching public sources
and independent public image/signature checks are completed above; no remaining
hardware check is represented as passed.
