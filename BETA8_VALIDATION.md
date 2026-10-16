# Beta 0.1.0b8 — local candidate validation

2026-10-16. **Not published, not installed on the user's HA, not a release
clearance.** D-230 authorizes local building and explicitly accepts experimental
default-off observation while natural no-motion sleep remains untested.

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

## Intel/AMD limitation — not a green native validation

The local amd64 runtime/test images built successfully. Container inventory,
notices, exit/stdin/stop/environment/smoke checks and the seven root checks passed.
The **overall emulated container check failed**: 5380 tests passed, 7 skipped,
5 real-kernel seccomp tests failed (prepare, inspect, deliver, observe and
verify_thumbnail). One fixed, network-disabled diagnostic reproduced
`OSError: [Errno 22] network_filter_install` at PR_SET_SECCOMP under this Mac's
amd64 emulation. No protection or test was weakened or newly skipped.

Native ARM passes these same kernel tests. This evidence does not approve
native amd64; an actual x86_64 validator remains mandatory before publication.

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
transitions, sustained polling/Recorder impact, real b8 migration and card layout,
native x86_64 validation, separate publication approval, matching public source
package/images/signatures and Store handoff. None is represented as passed by
this local candidate. No GitHub credentials were read or publication attempted.
