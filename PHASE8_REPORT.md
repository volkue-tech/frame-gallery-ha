# Supervised Green validation — in progress

Date: 2026-10-03. Codex performed the checks below, including successful local
and Cleveland TV deliveries. Chicago and dashboard freshness remain open;
Phase 8 is not complete.

## Approval and scope

The user explicitly approved installing Frame Gallery as a separate test app
on HA Green and then sending Chicago/Cleveland images to the TV. Existing
apps, dashboards, scripts, integrations and `configuration.yaml` stay unchanged.
The user subsequently approved a separate preview camera, timer, test script
and test dashboard; these new elements are recorded below.
Nothing is published. No predecessor source or implementation was inspected.

## Observed installation

- Candidate: `a0b1ce734485aae8bb67dfce90b8e281fd61c34c`; runtime `f42f72a`.
- Core REST: HA 2026.9.4 reachable. A Supervisor proxy request returned 401;
  no blind retry or rights change. Privileged app installation used the
  already-running Terminal & SSH web terminal, within the approved scope.
- Read-only TV REST: Samsung GQ50LS03TAUXZG, Frame support true, power on.
- Green storage: about 15.9 GB available before the build.
- This Terminal & SSH version exposes the local app directory at
  `/local_apps`, not `/addons`. The new target did not already exist.
- A `git archive` of the candidate's `frame_gallery` directory was staged,
  without `.venv` or local caches. Only the development display name, slug,
  and AppArmor profile name differ: **Frame Gallery (Test)**,
  **frame_gallery_dev**. Runtime source files are unchanged.
- The first Mac tar transfer added 272 AppleDouble `._*` files. BuildKit
  failed at `compileall`: `._*.py` files contained NUL bytes. The real
  Python source files were unaffected. The first copy was moved, recoverably,
  to `/share/frame-gallery-phase8-mac-metadata-backup`.
- Repackaging with `COPYFILE_DISABLE=1` and `--exclude='._*'` removed the
  metadata from the archive. HA verified its SHA256 before extraction:
  `bae00b324b8ef340af9b67001f43606860eba176edb1edc8116b73444dd97798`.
- Store reload and `ha apps install local_frame_gallery_dev` succeeded.
  Supervisor reports version 0.1.0.dev0, state stopped, protected true,
  AppArmor `profile`, boot manual, watchdog false; no host networking.
  This does not yet prove AppArmor runtime attachment or enforcement.
- Each transfer served only its named archive over the local network and
  stopped after one download. No persistent relay or credentials in files.

## Prepared first test

- `/media/frame_gallery` did not exist before the test preparation.
- A project-generated synthetic 3840 × 2160 JPEG with coloured edge marks
  is now at `/media/frame_gallery/library/phase8-test-edges-3840x2160.jpg`.
  No third-party artwork was used, and no existing media was overwritten.
- Only the new app's options were saved: TV address `192.168.178.30`,
  source local_media, department/style/colour any, landscape and strict
  format true, contain, black margins, debug logging. Supervisor returned OK.
- Initially the TV start command was not executed because parallel Firefox
  navigation displaced the terminal. The user subsequently requested Firefox;
  its existing authenticated session was used in a new terminal tab. The
  terminal URL/input was checked before commands. No existing dashboard action
  was intentionally invoked, and Chrome sign-in is no longer required.

## Live runs observed in Firefox

All runs used only `local_frame_gallery_dev`, with protection on and without
host networking. Logs and subsequent Supervisor status were observed.

| Run | Observed result | Elapsed |
| --- | --- | --- |
| Local synthetic 3840 × 2160 edge test | `delivered`, exit 0; connected, upload_started, uploaded, selected; stopped | 7.2 s |
| Same local file again | Candidate excluded; `no_match`, exit 0; no TV delivery stage; stopped | 0.0 s (rounded log) |
| Chicago, all filters `any` | Count request HTTP 200, following search HTTP 403; `source_failed`, exit 0; no TV connection; stopped | 1.3 s |
| Cleveland, all filters `any` | `cma:113878`, Textile Fragment, 1760–1780; strict candidate; all four TV markers; `delivered`, exit 0; stopped | 19.2 s |
| Cleveland, Chinese Art, before 1400 | `cma:136661`, Reclining Dog and Puppy, 1271–1368; fallback candidate 3400 × 1934; all four TV markers; `delivered`, exit 0; stopped | 18.5 s |

The restrictive run reached the 150-candidate evaluation allowance and chose a
landscape fallback with `contain`; it did not loosen the museum/period filter.
The prepared local JPEG and two museum JPEGs were confirmed selected by the
TV API. The user subsequently confirmed seeing the dog artwork on the TV.
That is not a visual confirmation of the synthetic coloured edge marks;
the edge/no-crop check remains pending.

Chicago stopped at its first HTTP 403, with no automatic retry or follow-up
request to that provider during that run. Subsequent approved diagnostics are
recorded below. No DNS,
Tailscale, credentials, security settings, or request identity was changed to
work around it.

### Chicago pagination diagnosis and authorized correction

Read-only diagnostics on 2026-10-03 used the honest Frame Gallery headers,
TLS checks and only public museum metadata; no TV operation or image download.
The Green's page-1 search returned 50 records and total 59 063. Identical
filtered searches at pages 199 and 200 (limit 50) returned HTTP 403,
`Invalid number of results`, with the detail `You have requested too many
results. Please refine your parameters.` The precise live pagination boundary
and the failed page of the original app run are unknown. This reproduces an
API-level query rejection rather than evidence of a general DNS/Tailscale
block; no network setting was changed.

The user authorized a targeted selection fix, own-storage diagnostics and
updating/testing only Frame Gallery (Test), preserving history and protection.
D-174 uses a documented Elasticsearch random ordering and shallow pages 1–7;
D-175 reports only bounded directory metadata after cleanup. One production
gateway request from the Mac validated the new random-score query (seed 41):
50 records, all public domain, total 59 063. That does not yet establish a
successful Green delivery of the changed build.

Local validation of the changed runtime: Ruff clean; strict mypy on both
host and Linux clean (221 files); complete host gate 4 614 passed, 8 skipped,
100 % line/branch coverage (8 995 statements, 1 904 branches). The rebuilt
`aarch64` container passed packaging/inventory, stop handling and smoke checks,
then 4 616 tests as non-root (6 expected skips) and all 5 root-isolation checks.
The no-network smoke run logged an empty scratch directory after its TV failure,
with no temporary files, and the final outcome remained the last log line.
Dependencies and the AppArmor profile did not change. No new amd64 measurement
or full Green cleanup claim is made from those local results.

The shared-media listing contained exactly the retained 263 066-byte fixture
and one 584 565-byte preview. `du` reported 844 KiB including directory
allocation; `df` reported about 15.8 GB free. Private app `/data` and container
scratch were unavailable from protected Terminal & SSH. Their live verification
is pending the authorized in-app count-only report; no protection bypass.

### Preview files and bounded media observations

The first preview was 195,535 bytes, SHA256
`6c2c4ac990a94ac473fce59d811aa10a045715d2b5074d0e032c2b412cea1d0`.
After the duplicate/no-match run, its hash was unchanged. After Cleveland's
strict delivery it was 2,843,370 bytes, SHA256
`c5572a2f97a8022f0ee6f8b29e7bb07ffb86ede6190805f7720453cdb0c6692`.
The restrictive fallback replaced it with SHA256
`ecde80c9f51f83534e03d1aa43c3a20173a3aa857f98ce28396d68315204430f`.
These match the prepared delivery hashes logged by the app.

The media listing after the first Cleveland run contained only the retained
263,066-byte synthetic library fixture and `preview/latest.jpg`, not a series
of downloaded museum images. This demonstrates preview replacement in the
shared media directory; it does **not** independently verify private `/data`
limits or the container's `/tmp` cleanup. No cleanup warning was present in
the observed run tails. The repeated-local-file exclusion demonstrates
persistent exclusion behaviour but does not inspect the full history/ledger.

The TV runs logged no stored pairing token on each delivery. They nevertheless
connected and selected successfully. Whether this TV issues a reusable token
and whether pairing persistence needs adjustment remain unverified. The
successful upload implies its API was not rejected as 0.97; the exact API
version was not logged and must not be inferred.

The test app is retained, stopped, with the last restrictive Cleveland options
and debug logging. The existing Art Changer, dashboards, scripts, integrations,
and `configuration.yaml` were not changed.

### Separate dashboard and preview tests

All setup used the authenticated Firefox UI, with explicit user approval.
Local File accepted `/media/frame_gallery/preview/latest.jpg` without an
allowlist or `configuration.yaml` edit. Only the test app's disabled Running
sensor was enabled. The created IDs are:

| Element | Observed identifier |
| --- | --- |
| Local File camera | `camera.frame_gallery_test_preview` |
| Timer, 150 seconds, restore off | `timer.frame_gallery_test_run` |
| Test script, single mode | `script.frame_gallery_test_new_artwork` |
| Test app Running sensor | `binary_sensor.frame_gallery_test_aktiv` |
| Separate dashboard | `/frame-gallery-test/0`, Frame Gallery Test |

The complete installed card and final script are in
`frame_gallery/examples/phase8-test-card.yaml` and
`frame_gallery/examples/phase8-test-script.yaml`. They use built-in cards,
not a custom-card dependency. The final script updates only the Running
sensor, not the camera; its loading indicator is bounded by the timer.

- First card start: loading appeared, then the dog preview changed to two
  covered bowls with the dashboard left open, without reload. Loading ended.
- Second card start: `cma:154678`, Foliated Saucer: Yaozhou Ware,
  late 1000s–early 1100s, strict 3400 × 1920; `delivered`, exit 0, 15.6 s.
  Returning to the dashboard showed the saucer and no loading note.
  These first two runs still included a redundant script camera update.
- Direct app-page start, without that script or a camera update:
  `cma:147081`, Covered Box: Yue Ware, 907–960, strict 3400 × 1894;
  `delivered`, exit 0, 16.5 s. The open dashboard changed from the saucer to
  the covered box without reload. This independently supports the native
  Local File refresh candidate in architecture §16.3.
- After removing the redundant camera update and verifying the saved script,
  a card start with `local_media` excluded the already-sent fixture:
  `no_match`, exit 0, 0.0 s (rounded), at 08:22:02 UTC. No TV stage occurred.
  The covered-box preview stayed unchanged, and the loading note disappeared
  on a later observation. The Running sensor did not provide a prompt end
  indication; exact sensor and indicator latency was not measured. Do not
  claim immediate completion feedback. The timer prevents indefinite loading.
- The source was restored to Cleveland, Chinese Art, before 1400; other
  test app options were preserved. No scheduled automation was created.
- Final card delivery, using the saved script without a camera update:
  `cma:149954`, Cup and Stand (stand), 1100s, fallback 3400 × 1967;
  `delivered`, exit 0, 16.8 s at 08:24:27 UTC. The dashboard remained open
  and changed from the covered box to the stand without reload; its loading
  note disappeared. The app Info page then showed stopped. This gives a
  successful card delivery as well as no-match coverage for the final script.

Native Local File refresh is a promising candidate, not a completed G5/D-140
gate: automation-started delivery and further repeated final-script delivery
tests remain open. No exact browser refresh latency is
claimed. User visual confirmation of these later TV artworks is also pending.

## Still pending

Local quality gates were rerun after the documentation changes: Ruff and both
strict mypy passes clean, 4,600 tests passed, 8 Linux/root-only checks skipped,
100 % line and branch coverage, exit 0. The initial sandboxed run passed 4,598
tests but failed the two real supplementary-group/setgid checks; both passed
in a targeted unsandboxed rerun, followed by the complete passing unsandboxed
gate. No runtime code or test was changed to bypass those checks.

Visual edge/no-crop confirmation; pairing-token behaviour and exact Art API
version; Chicago rejection diagnosis and successful Chicago delivery;
automation-started and repeated final-script browser freshness; measured
Running-sensor/indicator latency; detailed history and upload-ledger inspection;
container temporary cleanup and Green memory measurements; AppArmor
attachment/audit. The separate dashboard entities and approved setup are
recorded above. Observed normal-run timings,
local duplicate/no-match, and Cleveland fallback passed as recorded above.

Keep the development app and its data. Removal, publication, and changes to
existing HA configuration require separate direction. Small transfer archives
remain in Terminal & SSH's `/tmp`; the first source copy remains in `/share`
as noted above. These are deployment artifacts, not artwork-download buildup.
