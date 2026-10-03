# Supervised Green validation — in progress

Date: 2026-10-03. Codex performed the checks below, including successful local
and Cleveland TV deliveries, followed by a successful Chicago delivery of the
corrected runtime. The complete dashboard freshness gate remains open;
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

### Corrected build installed and Chicago delivered

The user freed Firefox for the already-approved update and TV test. On
2026-10-03, runtime commit `5d662e1` was transferred as a single named archive,
with SHA256 `8da0fd041941c865145c74023761397ad7be40a406b594e6ee03e5c0a3ba0d10`.
Green verified this hash before extraction. The previous own source directory
was moved recoverably to `/share/frame-gallery-dev-before-5d662e1`; no app
uninstall or private-data reset occurred. `ha apps rebuild local_frame_gallery_dev`
completed successfully. The installed `aic.py` and `diagnostics.py` hashes
matched the staged runtime. Protection stayed enabled, AppArmor remained
`profile`, and host networking stayed off. The one-file transfer exited after
its download.

Only the test app's source, department and period were temporarily changed
through its UI: Chicago, `any`, `any`. All other options were preserved.
One run was started through the existing test dashboard card:

- Search requests on shallow pages succeeded; selection evaluated 150
  candidates and shortlisted two fallbacks, without relaxing the museum filter.
- Chosen: `aic:88793`, **Retable and Frontal of the Life of Christ and the
  Virgin**, Spanish, 1396; landscape fallback, source dimensions 1686 × 971.
- TV result: `connected,upload_started,uploaded,selected`; `status=ok`.
- Final outcome at 09:17:35 UTC: `delivered`, exit 0, **15.5 seconds**.
- Preview SHA256: `505a9a529a4c2b17d088eb8ab9ce4e19523b8f5ac3a8c6567c486f2fe6406aa4`,
  equal to the prepared delivery hash. It replaced, rather than accumulated
  beside, the previous preview.
- The dashboard stayed open while a separate tab displayed the logs. On
  returning, loading had ended but the old preview was initially still visible;
  a subsequent observation showed the new artwork without a page reload or
  manual camera update. Exact refresh latency was not measured. This adds a
  second successful card delivery for the final script, not proof of immediate
  refresh or of automation-started refresh.
- The prior Cleveland / Chinese Art / before-1400 options were saved again.
  The UI offered a restart; it was declined to avoid another TV run. A subsequent
  CLI check confirmed the saved original options, app `stopped`, protected true,
  AppArmor `profile`, and host networking false. No card or script was changed.

The count-only report ran after cleanup in this successful live run:

| Bucket | Status | Regular files | Bytes |
| --- | --- | --- | --- |
| state | ok | 7 | 3 105 |
| cache | ok | 2 | 513 |
| preview | ok | 1 | 1 465 960 |
| scratch | ok | 0 | 0 |
| quarantine | unavailable | not established | not established |
| tv | unavailable | not established | not established |

For every available bucket, temporary files, run directories, other entries
and unreadable entries were zero; no scan was truncated. `unavailable` does
not prove an empty directory. The TV log separately reported no stored token
because the TV directory could not be opened (`ENOENT`). These statistics do
not inspect history/ledger contents or establish crash/forced-stop cleanup.

The shared gallery still contained exactly two files: the retained synthetic
fixture (263 066 bytes) and the one current preview (1 465 960 bytes). `df`
reported about 15.7 GB available. The source backup and 632 KiB transfer archive
are intentional rollback artifacts, not retained artwork downloads. No existing
user media, configuration or history was deleted or reset. The user subsequently
confirmed seeing this Chicago artwork on the physical TV. This confirms the
delivery visually, not the separate synthetic edge/no-crop acceptance check.

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
claimed. User visual confirmation of these later Cleveland TV artworks is still
pending; the subsequent Chicago delivery is visually confirmed as recorded above.

## Still pending

### Follow-up approval and diagnostic results

The user approved continuing Phase 8 with automatic-start, cancellation and
cleanup checks. No release or Phase 9 was authorized. The following checks
were completed on 2026-10-03 before the next live run:

- Public Core connectivity: unauthenticated `/manifest.json` returned HTTP 200
  outside the sandbox before credentials were loaded. Core login and the four
  fixed test-entity REST reads succeeded. Credentials were read only from the
  two approved 1Password fields and kept in process memory.
- An authenticated HTTP `/api/hassio/addons/local_frame_gallery_dev/info`
  request returned 401 and was not retried. Inspection of HA 2026.9.4's official
  `hassio/http.py` showed that this HTTP route is not exposed, even to an admin;
  it is not evidence of invalid Core credentials. App Info in the existing
  Firefox session showed **Gestoppt**. A separate native WebSocket metadata
  attempt failed at transport (`OSError`), without an observed auth reply; it
  was not retried or used to change permissions.
- Core service metadata was read successfully. A subsequent authenticated,
  read-only GET of the proposed new own automation configuration returned 401.
  This is an admin-only configuration endpoint (`config/view.py`). The session
  stopped, without a POST, retry or rights change. No test automation was saved,
  armed or fired, and no new TV run was started by these checks.
- A new blank automation editor was opened in an agent-created Firefox tab,
  but not saved. Browser control then detected parallel user navigation to a
  different app page. Input stopped; a non-blocking request asked the user to
  leave Firefox free for the bounded live test. No input was sent to that page.
- The Running sensor was still `on` with last change 09:17:39.917937 UTC while
  the app was stopped. A later Core snapshot observed `off`, last change
  09:32:39.690473 UTC: about **15 minutes**, not prompt completion feedback.
  HA 2026.9.4's official `hassio/const.py` sets the addon update interval to
  15 minutes, and `hassio/binary_sensor.py` derives Running from that coordinator.
  This supports treating the sensor as coarse status only; the existing test
  script's loading indicator is bounded, but precise start/end tracking is not
  proven and it may cancel early when a short run is missed.
- The already-built `aarch64` Linux test image was run with `--pull never`,
  `--network none`, no host mounts and no HA/TV contact:
  `pytest --no-cov -q tests/integration/test_sigkill.py
  tests/unit/infra/test_signals.py tests/unit/store/test_workspace_and_sweep.py`.
  **44 passed in 0.97 seconds**, exit 0. These include real child SIGKILL,
  exclusion of uncertain uploads and removal of leftovers on the next run,
  using synthetic persistent rigs. They are not a Green crash test or a fresh
  whole-package coverage gate.

Official implementation references:
[HTTP Supervisor routes](https://github.com/home-assistant/core/blob/2026.9.4/homeassistant/components/hassio/http.py),
[configuration API admin requirement](https://github.com/home-assistant/core/blob/2026.9.4/homeassistant/components/config/view.py),
[addon polling interval](https://github.com/home-assistant/core/blob/2026.9.4/homeassistant/components/hassio/const.py),
[Running sensor](https://github.com/home-assistant/core/blob/2026.9.4/homeassistant/components/hassio/binary_sensor.py).

The Core API sessions exited; no persistent relay, automation, polling job or
credential file remains. The next live checks need the existing authenticated
Firefox session to be free, or separately authorized admin access. The planned
automation is a new own unique-event test, initially disabled and self-disabling
before starting the test script; no regular schedule and no existing automation
change. The stopped test app, its options, dashboard and private history were
not changed during this diagnostic round.

Local quality gates were rerun after the documentation changes: Ruff and both
strict mypy passes clean, 4,600 tests passed, 8 Linux/root-only checks skipped,
100 % line and branch coverage, exit 0. The initial sandboxed run passed 4,598
tests but failed the two real supplementary-group/setgid checks; both passed
in a targeted unsandboxed rerun, followed by the complete passing unsandboxed
gate. No runtime code or test was changed to bypass those checks.

Visual edge/no-crop confirmation; pairing-token behaviour and exact Art API
version; automation-started browser freshness and measured refresh latency;
Running-sensor/indicator latency; detailed history and upload-ledger inspection;
crash/forced-stop temporary cleanup and Green memory measurements; AppArmor
attachment/audit. The separate dashboard entities and approved setup are
recorded above. Observed normal-run timings,
local duplicate/no-match, and Cleveland fallback passed as recorded above.

Keep the development app and its data. Removal, publication, and changes to
existing HA configuration require separate direction. Small transfer archives
remain in Terminal & SSH's `/tmp`; the first source copy remains in `/share`
as noted above. These are deployment artifacts, not artwork-download buildup.

After recording the corrected Chicago live results, `check.sh` was rerun:
Ruff and both strict mypy passes clean; 4 614 passed, 8 expected skips;
100 % line and branch coverage (8 995 statements, 1 904 branches), exit 0.
