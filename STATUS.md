# Project status

Last updated: 2026-10-04 (app-store discoverability; released beta runtime unchanged)

## App-store metadata pass — 2026-10-04

The user explicitly authorized changing and publishing the app display name to
`Frame Gallery – Samsung Frame TV` and putting Samsung at the beginning of its
description (D-200). The generator and generated config are changed together,
with a metadata regression and matching installation instructions. Slug,
repository brand, version `0.1.0b1`, image mapping, release tags, runtime, options,
dashboard entities and live HA/TV configuration are unchanged. No new image,
release or live store refresh is authorized or claimed. Full local quality gates
passed: Ruff, strict mypy for host and Linux (240 files), 4,833 tests passed,
eleven unchanged Linux/root-only skips, and 100% line/branch coverage (9,201
statements / 1,972 branches). The metadata generator's check and `git diff --check`
passed. Official frontend search code was fetched read-only from its pinned
commit; the installed frontend and live refreshed store were not inspected.
The user-approved public push remains pending at this pre-publication checkpoint.

## Documentation improvement pass — 2026-10-04

User-authorized documentation maintenance after the beta release: customer-first
repository/app-store introductions, an original TV/dashboard illustration,
direct installation links, first-use instructions before advanced options,
complete unchanged dashboard YAML, and a troubleshooting FAQ. The hero is
explicitly not a screenshot; the optional card is not installed automatically.
The user explicitly authorized renewed Firefox access. The native region-
screenshot tool captured only the actual beta card, without private UI details.
Its previously delivered `cma:110817` artwork's official object page and CC0
policy were checked and credited; no provider API or new raw artwork download.
LEGAL_BOUNDARIES clarifies the narrow user-authorized CC0 documentation-screenshot
exception, outside application source and runtime/release images. No predecessor
asset was consulted. Public documentation pages supplied presentation patterns.
No Home Assistant/TV setting, runtime, package, image tag or release mutation.
Final local quality gates passed: 4,832 tests, eleven unchanged Linux/root-only
skips, Ruff, strict mypy on host/Linux (240 files), and 100% line/branch coverage
(9,201 statements / 1,972 branches). Two presentation regressions were added.
An offline check validated 37 local links/assets/anchors and byte-identical
script/card/automation YAML compared with the previous committed guide. Both PNGs
were visually inspected; the 505 × 287 screenshot matches Firefox's saved region
byte-for-byte, and the original hero is 1,440 × 860. Combined PNG size is 196,119
bytes. No new container or hosted architecture run is claimed or needed for this
documentation/test-only maintenance; runtime and packaging are unchanged.
The checkpoint above preceded publication approval. On 2026-10-04 the user
explicitly authorized publication including the real dashboard screenshot.
Commit `3906beeeeae39e5292131fb74e478ade7c04b1ca` is now public on the personal
repository's main branch, independently verified through anonymous `ls-remote`.
All three user-facing Markdown pages, both PNGs and the original SVG were fetched
anonymously from public main and matched the local files byte-for-byte. Runtime,
release tag and HA/TV configuration are unchanged. This publication receipt is
local follow-up documentation and was not part of that published commit.

## Current phase

**Phase 9 public-beta work completed in the documented scope (D-199).** `v0.1.0b1` is public at
https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b1 .
Its tag independently resolves to `8a3e7ee`. Final native run `37193338410`
completed successfully on ARM and Intel, including actual container/root and
real-limit memory gates. Public Green installation and live delivery/preview/
loading/fallback/cleanup are verified in the documented scope. The user confirmed
the first artwork on the physical TV. Released runtime/source remains `d736c7a`.
After the user's GitHub confirmation, both one-time publication approval values
are saved and read back as `DISABLED_AFTER_0.1.0b1`; no approval can be reused.
This documentation-only closure does not rebuild, replace or retag the release.
No independent legal counsel, universal fresh pairing or public-install kernel
negative probes are claimed. No new feature or later phase is authorized.

### Earlier Phase 9 progress (historical, superseded by the release above)

**Final corrected run:** `8a3e7ee` is pushed and independently verified. Native
run `37193338410` is in progress; actual ARM/Intel logs both confirm 4,836 suite
passes / five root-only skips plus all five root checks. Real-limit memory
measurements remain in progress. The saved beta draft is explicitly pinned to
`8a3e7ee` and marked prerelease. The previous `115c5e0`-target notes below are
historical, not the current release approval.

**Publication continuation:** personal `main` push of `115c5e0` is verified.
Fresh native validation run `37192835740` is in progress for that exact commit;
both architecture host quality gates have passed. The private beta draft is
now explicitly pinned to `115c5e0` rather than a moving main branch. Announcement
and final phase closure remain pending until the full jobs finish successfully.
The actual Docker context correction adds the beta example directory to the
unpublished test stage. Actual ARM image build and no-mount suite passed 4,836 /
five root-only skips plus all five root checks; full Mac gates passed 4,830 /
eleven unchanged skips, strict mypy 240 files and unchanged 100% coverage.

**Latest checkpoint (D-198):** the separate public `0.1.0b1` app installed
successfully through the official repository link/app store after `60f22c4`.
Observed slug: `a94fc569_frame_gallery`. No SSH/build/configuration-file change
was needed to install it. Two card-started Cleveland deliveries completed in
21.2 s and 17.3 s; the user physically confirmed the first TV image. The second
used the bounded aspect-ratio fallback without cropping. Both refreshed the
native preview without reload, ended loading, and left scratch/tmp/run counts
zero. Invalid TV address `0.0.0.0` ended immediately before discovery/TV contact;
the real address was restored and verified before the second delivery.
Protection/custom profile/no host network/no extra privilege are confirmed.
The installed profile matches the reviewed policy exactly after Supervisor's
slug substitution; public-install kernel negative probes were not repeated.
The app-only local backup `e779415c` holds two unique confirmed history entries
and two consistent uploaded ledger entries. About 14.7 GB remained free.

The root-descriptor regression in `60f22c4` exposed an app-only-container fixture
error in hosted run `37185516101`. D-198 moves actual root-file verification to
a mandatory host gate and uses portable fixture tests in containers, without
adding skips or changing runtime/images. Corrected Mac gates: 4,830 passed /
eleven unchanged platform skips, strict host/Linux mypy 240 files, 100% full and
mandated line/branch coverage. Native ARM: 4,836 passed / five root-only skips,
plus all five separate root checks. Final corrected push/hosted CI and the beta
announcement remain pending. Earlier pending-install entries below are history.
Final Mac rerun and native ARM rerun retain those passing counts/coverage; the
public-slug documentation test cross-checks both installed beta YAML examples.
The announcement is saved as a private untagged prerelease draft only. Its
target/tag will be rechecked after corrected push and hosted success.

**Public repository recognition correction (D-197):** the metadata push of
`0b850e7` is verified. The real one-click link opened the correct add-repository
dialog on the Green, but Supervisor rejected the repository as invalid. The
required root `repository.yaml` was missing locally and publicly. It is now
added with only the own name/URL/maintainer; a regression failed on the missing
file before the correction. Runtime images and their source release remain
unchanged. Public recognition/installation must be retested after the fix is
pushed; no app was installed or started by this failed attempt.
Full local gates exited 0: 4,818 passed / eleven unchanged platform skips,
strict host/Linux mypy 238 files and unchanged 100% full/mandated line+branch.

**Latest publication (D-196):** publisher `37159551965` completed successfully
on runtime commit `d736c7a`: both native validations and both actual-image
publishers, including exact source checks/non-overwrite/signing. The own numbered
ARM/Intel images are public. Independent anonymous tag/digest manifest checks,
full anonymous Docker pulls and pinned Cosign verification of the exact own
workflow/issuer/commit passed for both. Hash-checked evidence ZIPs and their
actual measurements are retained (PHASE9_REPORT). App-store metadata now selects
these existing images; no runtime rebuild/retagging. One-click installation and
guide updates are prepared locally. Clean public Green installation, observed
public app ID/final card and beta announcement remain pending; no live HA changes
at this milestone. Earlier entries below describe prior states.
Full install-metadata gates passed: 4,817 tests / eleven unchanged platform
skips, strict mypy 238 files (host and Linux), unchanged 100% full/mandated
line+branch coverage. Public main synchronization of `0b850e7` is verified;
the newer repository-recognition correction above still needs publication.

**Latest correction (D-195):** personal main `3550186` is pushed, but Intel job
`111301941395` in run `37156871737` failed three JSON-depth tests. Its Python
build accepted extreme nesting that other builds reject. All three JSON input
paths now enforce a 32-container bound before parsing; this fixes the network
and stored-JSON defect and preserves IPC refusal independently of the parser.
Full local gates exited 0: Mac 4,816 / eleven platform skips, strict mypy 238
files, 100% full/mandated line+branch; native ARM 4,822 / five root-only skips
plus all five root checks. Exact-commit hosted run `37157727919` is now completed
successfully for `d736c7a`: native ARM job `111304589397` and native Intel job
`111304589480`, including the container/root/real-limit memory checks.

The matching source package passed assembly and independent preflight:
172 archives, 518,133,760 bytes, SHA256
`8034a982322532b34b0c9893cda5135cb16448dc694e2c59f68ae42fedeb64b5`.
Its source-only prerelease is now public at
https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b1 .
Public metadata, the exact tag commit and an actual unauthenticated download
match the approved bytes and SHA256. This is not the installable-beta announcement.
Both release variables were saved/read back in the personal repository UI.
Publisher run `37159551965` started on `d736c7a`; approval and both native
validations succeeded. Publishers `111313136144` (ARM) and `111313136168`
(Intel) passed the public-source preflight and are checking their actual upload
images. No image/signature/clean-public-install success
is claimed yet. Previous source candidates stay superseded. Publication remains
bound to `d736c7a`, not to these later uncommitted progress-document edits.

**Prior fixture-correction evidence:** the personal main push to `7f20c14` is
verified. Run `37156461763` failed two old local-media fixtures whose
unlink/recreate assumption permits immediate inode reuse on Ubuntu. Their
replacement is now allocated before the old inode is released; all refusal and
no-worker assertions remain. Two deterministic OS-signal-refusal tests address
a timing-dependent coverage hole from the same log. Runtime code is unchanged;
final local gates passed (Mac 4,796 / eleven platform skips, strict mypy 236 files,
100% full/mandated line+branch; native ARM 4,802 / five root-only skips and five
separate root passes). Fresh hosted checks remain pending. Both source uploads
are private superseded drafts, with no published source release or images.

**Phase 9 authorized and in progress (2026-10-03).** The user requested completion
of the next phase and confirmed **Frame Gallery** and the personal repository
**volkue-tech/frame-gallery-ha**. Release hardening, engineering licence review,
release preparation and testing of the separate development app are in scope.
No business account or predecessor material may be used. Codex performs the
evidence-based engineering licence audit, without claiming legal counsel's
approval. No existing technical/compliance release gate is waived.

**Numbered candidate (D-194):** runtime/project/generated app metadata are
aligned to `0.1.0b1`, not announced as a finished installable beta. Experimental
stage/no image mapping remain until actual signed public images are verified.
The prior clean `a7a99f8` source package passed assembly and independent full
preflight (172 archives, 518,092,800 bytes); its LABEL-only local image retains
exactly the validated filesystem layers. That personal main push is verified;
native hosted run `37155043758` was observed in progress. A new exact-commit
source asset is required for the numbered candidate, not reuse of the prior one.
The candidate passed full native Mac gates (4,779 tests / eleven expected skips,
strict mypy 234 files, unchanged 100% line/branch) and native ARM image checks
(4,785 passes / five root-only skips, five root passes). Only the own virtual
project version changes in the lock; the pinned uv 0.12.19 offline lock check
passes for all 26 packages. The dependencies and generated notice payload are
unchanged. No public candidate image or clean public installation is claimed.

**Latest local release preparation (D-193):** the manual-only native publication
workflow is prepared, not dispatched. D-194's final workflow review found and
corrected missing explicit Bash/pipefail defaults: a piped host gate must not be
reported successful merely because tee succeeded. Both workflows select the
documented fail-closed Bash invocation, with nine host/fixture/shell regressions.
The earlier numbered source upload is only a private untagged draft;
it is not distributed. Fresh native fail-closed hosted validation and a matching
source package are required before activating image publication.

The hosted ARM job did fail: an empty Zstd upstream notice and its shipped copy
were ignored by Git's `build/` rule. Narrow exceptions now retain both exact
files. The source assembler verifies originals and shipped copies in the actual
Git archive, not merely the local filesystem (six regressions). Earlier local
source packages are superseded and must not be published. Final full gates for
this correction passed: Mac 4,794 tests / eleven platform skips, strict mypy 236
files and 100% full/mandated line+branch; native ARM 4,800 passes / five root-only
skips and five separate root passes. The Mac run used normal host permissions
after the sandbox blocked two existing group/setgid tests; no skips were added.
Both previous hosted jobs ended in failure. Fresh hosted native validation and
the newly assembled exact-commit source package remain required.

**Prior local release preparation (D-193):** the manual-only native publication
workflow is prepared, not dispatched. Exact reviewed source-commit/package-hash
approval and numbered matching runtime/app beta metadata are mandatory; current
dev0 is observed to fail before publication. Matching public sources, fresh actual
image checks, authenticated non-overwrite check and pinned keyless signing are
wired. Twenty source-package and 27 release-preflight regressions pass. Latest
full Mac gates: 4,778 passed / eleven expected skips, strict mypy 234 files,
100% line/branch. Native ARM image suite: 4,784 passes / five root-only skips and
five separate root passes, all 201 notice documents byte/readability verified.
HTTPError bodies are explicitly closed after the first Linux run exposed resource
warnings; no warning gate was relaxed. Source/rebuild and bounded engineering
assessment/maintainer-release documents are prepared. No app-code/dependency or
live HA change; final public source/images/install evidence remains open.

**Previous local release preparation (D-192):** 111 additional Alpine original
documents and their archive-member manifest are retained; the committed image
payload now holds 201 public evidence files. SOURCE_AND_REBUILD documents source
layout and replaceability; the tracked offline source assembler has 19 passing
integrity/safety tests. Full native Mac gates passed: 4,749 tests / eleven expected
skips, strict mypy over 232 files, unchanged 100% line/branch coverage. No runtime
code/dependency or live HA change. Actual assembly at the clean new commit,
image revalidation, engineering applicability and gated publication remain in
progress, not silently marked complete.

**Earlier Phase 9 work:** enforced parent/image/TV profiles, fail-closed transitions and
worker-only seccomp network restrictions (D-178/D-180). The combined no-TV probes
passed on the Green in `0.1.0.dev6`: both workers UID/GID 65534, enforced child
labels, no-new-privileges, no HA token, exact 1 GiB/512 MiB address-space limits;
image sockets denied, TV IPv4-TCP allowed and UDP denied; options, unrelated tmp,
shared memory, executable and return-transition access denied. Only the image
worker may write the prepared output. The eight confirmed record/preview/options
hashes were unchanged and scratch was empty. AppArmor network rules alone did not
deny these observed sockets; the cause is not established. Seccomp supplies the
verified additional restriction without new packages or privileges. `/init` and
S6 interpreter scripts also required read permission under actual enforcement.
The supplementary parent-output-read probe also passed with Docker's existing
DAC_OVERRIDE permission, without adding a capability (D-182). Latest native local
`check.sh` passed after the tempio-notices correction: 4,717 tests / 11 expected skips,
100% line/branch coverage.
Apache-2.0 and initial official dependency licence
texts are added, but the licence/source bundle is not complete.
The subsequent D-184 inventory fix includes the three installed net/prog/web
S6 packages omitted by the admin-only scan. Twenty-two unit tests and the
existing native ARM image confirm eleven S6 packages. Nine further official
base-source archives and their licence texts/hashes are retained; BearSSL and
static-libc/build provenance remain open along with the other D-135 sources.
Further D-186/D-187 evidence retains all 45 exact Alpine recipes for 61 packages,
197 verified local files and all 58 recipe-hash-verified upstream files (282 MB
on the Mac only). BearSSL, identified static-musl and Go toolchain source/texts,
complete libbsd/libmd COPYING and the GCC runtime exception are retained.
Native-Pillow completeness, applicability, packaged distribution notices and
replacement/rebuild/source-bundle assembly still prevent release clearance.
Further D-189 evidence retains twelve additional native source archives,
Pillow's official wheel build inputs/exact multibuild submodule, and AVIF codec
sources. Twenty-seven unabridged licence/patent/patch texts are archive-byte
checked. AOM/libyuv/libwebp patent grants and the actual Pillow TIFF security
patch are preserved; the TIFF patch also matches the installed ARM SBOM.
Three new repository data regressions and the existing inventory tests pass
(28 targeted tests). Full local gates passed: 4,720 tests / eleven expected skips,
Ruff, strict mypy over 228 files, unchanged 100% line/branch coverage.
No runtime change; notice shipping, subsidiary applicability,
source-bundle assembly and replacement/rebuild documentation remain release gates.
The D-190 notice payload is now implemented in the Supervisor-compatible build
context: 89 original public evidence files plus a generated manifest, copied into
the image and byte/readability-checked as UID 65534 in the new ARM rebuild.
Missing or altered payloads fail the quality gate; new data tests no longer skip
the shipped evidence. Latest full host gates pass (4,728 tests, eleven expected
skips, strict mypy 230 files, 100% line/branch); latest ARM container suite passes
(4,734 non-root tests / five root-only skips; five separate root passes).
The longer ARM measurement also passed: 26 prepare results, peak VM 765.5 MiB,
slowest 1.59 s under the unchanged 1 GiB limit; 150 inspections, no failures.
App code/dependencies are unchanged across the documentation/test refresh. This
does not clear source/rebuild/applicability or public-install release gates.
An offline source candidate for clean own commit `40f3e65` is assembled and
read-back hash-verified: 172 original archives plus the own project snapshot,
512,204,800 bytes, Mac-only. It contains no Git backup history, HA state, tokens
or TV data and redistributes no binary toolchains (D-191). Replacement/rebuild,
subsidiary applicability, final release synchronization and public source/image
availability are still open, not claimed cleared by this candidate.

**Live checkpoint:** the normal entry point is restored and both temporary
diagnostic modules are moved outside the own app source. Two card-started real
Cleveland deliveries under enforcement completed in 19.4 s and 16.9 s with TV
selected/uploaded confirmation, preview refresh without reload, loading completion
acknowledgement and empty scratch. The first revealed EACCES refreshing history/
ledger backups; D-183 adds exactly two parent-only hard-link pairs. The second,
after an official Supervisor update to `0.1.0.dev7`, had no backup warning.
App stopped, protection on, host networking off, original filters/timer unchanged.
The local app-only checkpoint verifies 14 unique history IDs / 13 in its prior
generation and three uploaded ledger entries with a correct latest uncertainty
backup, proving D-183's refresh from actual state.
Confirmed records were not reset; the deliveries legitimately extend them. The
saved pre-Phase-9 source is
`/share/frame-gallery-dev-before-phase9-v1`; the app-only backup is retained.
Native amd64 measurement is now passed; complete source compliance, validation
of subsequent changes, public images and a clean public installation remain
release gates. The approved public repository
`volkue-tech/frame-gallery-ha` is public and the first audited `main` push is
verified at `39d25dac8a407b050c0fd2eb0bff083c316c8ca4`. Native ARM/Intel hosted
validation succeeded on both architectures (run `37141542920`, ARM completed
17:58:51 UTC, Intel 18:02:25 UTC). The native Intel memory gate is passed at this
source revision, without Rosetta or QEMU. The later development-inventory fix
does not change runtime code; its push is verified at `9cd37f8`, and hosted run
`37143460336` failed on both architectures: the rewritten tempio notice omitted
the exact Go-version/module-count phrase required by the existing inventory
gate. Both non-root suites (4,719 passes / six skips), all root checks and both
memory measurements passed; the notices gate alone failed. D-188 restores the
verified metadata and adds a repository-notices regression test, with positive
and mismatched-version/count cases. Local notices checks against both retained
image inventories pass. The corrected `aaf7016` main push is verified; native run
`37145245403` succeeded on both native architectures: ARM completed at 18:58:37
UTC, Intel at 19:01:57 UTC, including host/container/root/notices/memory gates.
This verifies `aaf7016`, not the later source/notice-packaging changes. No
container publication or release. No existing-app change or `configuration.yaml`
edit. The personal fine-grained token was entered privately in the user's Mac
Terminal, held only in process memory and not stored by the helper. The retained
old identity backup branch was not pushed. See `PHASE9_REPORT.md` for actual evidence,
temporary test-app state and remaining gates. Exact Python sdists and initial upstream licences/NOTICE files are
retained, not yet a complete corresponding-source distribution. Full native
aarch64 container checks passed (13 worst cases twice, real 1 GiB limit,
765.5 MiB peak; 150 inspections). These Docker checks have no own AppArmor
attachment and are distinct from the now-passed ordinary enforced Green runs.

### Archived Phase 8 completion notes

**Latest Phase 8 checks completed:** the user-approved temporary, no-TV diagnostic passed all 13 native Green memory cases under the unchanged 1 GiB/15 s worker limits (765.5 MiB peak address space, 11.1 s slowest prepare), plus 150 inspections without failure. SIGKILL with a live isolated worker and a fsynced pre-staged history file was followed by successful real startup sweep and local no-match: 12 exclusions intact, both sent fixtures excluded, confirmed files/options/preview unchanged and scratch empty. AppArmor attachment is proven in parent/worker as `local_frame_gallery_dev (complain)`; enforcement is not. The normal `d1bb654` test source was restored byte-for-byte and rebuilt as `0.1.0.dev1`; original options retained, app stopped/protected, no host networking. About 1 GB of owned diagnostic inputs/archives was removed; 15.5 GB remains free and the app-only backup is retained. Phase 8 checklist is complete within the documented test scope. Fresh pairing/rejection remains a live limitation; Phase 9 hardening and publication still require explicit approval. See the final section of `PHASE8_REPORT.md`.**

**Current approved correction complete:** D-176/D-177 are installed in the separate test app/script, runtime `d1bb654` (local test packaging `0.1.0.dev1`). Loading no longer depends on the delayed Running sensor: one guarded, bounded service call cancels the explicit timer after cleanup. Live delivery (20.9 s), local no-match (0.0 s rounded), and graceful cancellation after a 647755-byte download (14.1 s) acknowledged completion. The dashboard preview updated without reload and loading ended. Missing-notification injection also ended loading through the independent 150 s expiry. The corrected signal interpreter eliminated `invalid number '--'` on the Green stop; no dependency or privilege was added. Original Cleveland options and explicit test timer are restored, app stopped/protected, host networking off. About 15.6 GB is free. See `PHASE8_REPORT.md`.

**Earlier Phase 8 checks:** native Local File preview refresh passed card, event-automation, app-page and no-match tests (D-140). The automation remains disabled, without a schedule. D-176/D-177 corrected loading and the stop-signal shell warning on Green. The user physically confirmed complete edges/corner labels and black margins, without cropping. The local app-only backup confirmed 12 unique history entries, its 11-entry prior-generation copy, two uploaded ledger entries and consistent current/preview. The subsequent hard-kill, native memory and live profile-attachment checks are completed above; fresh pairing/rejection and enforced isolation remain unproven. Only approved separate test elements changed; no existing elements or `configuration.yaml`. Phase 9 and publication remain unapproved.**

**Approved edge-test delivery:** after explicit user confirmation, the new labelled 3:2 fixture was transferred once and delivered through the existing test card in 9.9 s. The Green preview SHA256 exactly matches the locally prepared 3840 × 2160 contain JPEG, including 300-pixel black side margins. The retained dashboard refreshed without reload and loading ended; scratch is empty. Original Cleveland/Chinese Art/before-1400 options and explicit timer were restored, app stopped/protected, host networking off. The user subsequently confirmed all four edges/corner labels and black side margins on the physical TV. The earlier bounded kernel query did not prove AppArmor attachment; the subsequent process probes now do. Enforcement remains a Phase 9 gate. See `PHASE8_REPORT.md`.

- **Phase 6 gate (user decision, 2026-10-03, after the Codex review and its follow-up checks):** passed. D-166 to D-172 are accepted, including the unchanged 1 GiB limit of the image worker (D-170). The native `amd64` memory measurement is mandatory before an `amd64` version is published, at the latest in Phase 9. The qualified licence review and the enforcement of the AppArmor profile stay release prerequisites.
- **Phase 7 conditions:** only Phase 7 of `TASKS.md`: offline validation with the existing local environments and container images, failure-path tests, and a release-candidate report. No new features, and no additional review loops without a concrete finding. The work stops at the Phase 7 gate.
- **Current live scope:** the separate development installation, supervised TV/museum tests, and the explicitly approved separate test camera, timer, script and dashboard. No existing app, dashboard, script, integration, or `configuration.yaml` may be changed. No GitHub publication. No scheduled automation has been installed.
- **Authorized Phase 8 correction completed:** the user approved fixing Chicago selection, count-only storage diagnostics, and updating/testing only Frame Gallery (Test), preserving history and protection. D-174 replaces rejected deep-page queries with documented random ordering and shallow pages; D-175 adds bounded read-only statistics after cleanup. Runtime `5d662e1` was rebuilt without uninstall/reset, with the previous source kept for rollback. Chicago delivery and normal-run storage statistics succeeded on Green; statistics are not a contents/integrity inspection or a crash-cleanup test. See `PHASE8_REPORT.md`.
- **User visual confirmation:** the user confirmed the Chicago retable on the physical TV after the corrected 15.5 s delivery, and subsequently the complete synthetic 3:2 edges/corner labels with black side margins after the 9.9 s contain delivery.
- **Phase 8 continuation completed in approved scope:** 44 offline Linux signal/crash/sweep checks passed, followed by the live event automation, three graceful stops and recovery delivery. The API account's event POST returned 401 and was not retried; the authenticated Firefox Events UI was used instead, without broader rights. Only `automation.frame_gallery_test_one_shot` was created; it has no schedule, initially false, self-disabled before starting the test script and remains disabled. The Running sensor lagged about 15 minutes and does not provide prompt completion feedback. The installed script and runtime were not modified in this continuation. See `PHASE8_REPORT.md`.
- Every commit uses the personal identity `Alexander Wilke <volkue@gmail.com>`.
- **Coordination note (2026-10-03):** a message in the user's chat, signed as Codex acting for the user, confirmed that Phase 7 continues unchanged and that Codex reviews the report and the local results at the gate; the locks and the identity stay as they are (*Review records* in `DECISIONS.md`).

### Phase 7 progress

| Step | Commit |
| --- | --- |
| 0a. `DOCS.md`: how to start over, as D-172 provides (Q-06) | `e3da3f5` |
| 0b. Phase 6 gate decision and Phase 7 authorization recorded; `ARCHITECTURE.md` amended for D-166 to D-172; the outdated libbsd and libmd line under *Known open decisions* corrected | `722bae1` |
| 1. The container checks of the existing images, without a build or network; the notices held to the image (D-173) | `4faa907` |
| 2. The failure paths through the real image (D-173) | `f42f72a` |
| 3. The release-candidate report, with status, tasks, and decisions for the gate | `284e4d3` |
| 4. The commit references in the status | `a0b1ce7` |

### Phase 7 results (for the gate)

The release candidate is `f42f72a`; `RELEASE_CANDIDATE.md` reports every result, with the commands to repeat them.

- **Quality gates** (`check.sh`, on the host): Ruff and `mypy --strict` (for this host and as on Linux) clean; **4 600 passed**, 8 skipped (the Linux-only and root-only checks); **100 % line and branch coverage** (8 940 statements, 1 894 branches; the architecture's gate 7 323 and 1 584).
- **Timing:** the tests of the time bounds (an injected clock for the budget; the real clock for workers, sockets, and the pairing deadline): 725 passed, 3 skipped (Linux-only, which pass in the images). On the real image, a run that found nothing took 0.2 s at most (70 s allowed), every run 7.3 s at most (120 s allowed), and the worst legal source 1.41 s to prepare (15 s allowed).
- **Container checks of the existing images** (`container_check.sh --no-build`; no build, no network; D-173), both architectures: the app images hold exactly the release candidate's `src/frame_gallery` (90 files); D-130 (a) to (d); the inventory; the notices list everything the image ships; the smoke run; the D-165 user pass (4 562 passed, 5 root-only skipped) and root pass (5 of 5). Under the real 1 GiB `RLIMIT_AS` on `aarch64`, all 13 worst cases succeed; the heaviest peaks at 765.5 MiB of address space, as in Phase 6.
- **Failure paths through the real image** (`scripts/failure_paths.py`; D-173): all 10 scenarios as specified on both architectures (no result, failed decode, corrupt history with and without a backup, three ledger states, a museum without a network, and a silent television). A failed upload after `upload_started` is covered by the suite (E7-E10).
- **Provenance** (H5): the names of the excluded projects appear only in the three files that state the boundary, in each of the 72 commits; every commit has the personal identity; no third-party code, header, or asset; the images derive from the pinned base alone.
- **Licences and notices** (H4, H6): complete for what the image ships; Apache-2.0 approved for the project's own code; the licence texts, the corresponding sources, and the open licence questions stay with the qualified licence review (Phase 9).
- **Findings:** none that needed a change of the app's code. One observation: a television that never answers ends after the 5 s REST check, without a second connection, which is within D-115; D-162 point 4 reads as if it were retried, so a clarification is proposed (D-173).

## Completed

### Phase 0: specification package (Codex)

- Created the isolated repository.
- Recorded the product requirements.
- Defined the independent-development boundaries.
- Wrote the acceptance tests.
- Wrote the agent instructions.
- Defined the phases and approval gates.

### Phase 1, revision 1: architecture proposal (Claude, commit `d42adf5`)

- Researched permitted sources only, with independent re-checks.
- Ran an internal multi-agent review; 58 confirmed findings were incorporated.
- Wrote `ARCHITECTURE.md` and the first `DECISIONS.md` (decisions, inventory, risks, questions).

### Phase 1, revision 2: Codex review applied (Claude, commit `9352e77`)

**Beta providers**

- Google Arts & Culture and Bing are removed from the beta. Their researched status is kept in `ARCHITECTURE.md` §9.4 and in the new *Researched and excluded sources* section of `PRODUCT_SPEC.md`.
- The beta sources are now **local media, the Art Institute of Chicago, and the Cleveland Museum of Art**.
- Cleveland is part of the normative design (D-136). Only CC0 records are used, and only the documented 3400 px print JPEG, never the TIFF.

**Filters**

- Four distinct filters: source/museum, department/collection, style/period, and colour.
- A capability matrix shows which source supports which filter.
- Unsupported filters are visibly reported in the log, the summary line, and the run record (D-124).

**Runtime**

- A **120 s** default hard deadline, split 10 / 60 / 40 / 10 s, with all timeouts clamped.
- `no_match` finishes within **70 s**.
- A 150 s dashboard timer indicator.
- 30 remote dimension requests, and a separate allowance for local header reads (D-114).

**Duplicate prevention**

- A **TV-upload exclusion ledger** with a write-ahead uncertainty quarantine (D-137).
- The confirmed sent history, the current artwork, and the preview still change only after the TV confirms selection.
- New acceptance items `E7`–`E10`.

**Preview**

- The Local File camera stays the primary design, and its platform basis is recorded (D-111).
- Freshness is **release-blocking**: Phase 8 must prove one refresh mechanism (D-140).
- Collection Image (2026.9+) is an optional alternative only, and does not raise the minimum Home Assistant version.

**Approved decisions recorded**

- `frame_gallery` as the provisional identifier (D-138).
- Apache-2.0 (D-102).
- `uv` (D-128).
- An IPv4 literal for the TV address (D-125). The test value `192.168.178.30` is never hard-coded.
- No `host_network` initially (Q-16).
- Inspect only the installed `samsungtvws` 3.0.6 (D-104).
- `contain`, landscape-only, and strict 16:9 on by default, with no crop (D-123).
- Bounded cleanup and atomic writes (D-106, D-110).
- Beta scope (D-120), including its three sources (D-132, D-136); the adapter details are still proposed.
- The top-level budget (D-114): 120 s total, split 10/60/40/10, `no_match` within 70 s, 30 remote probes. The sub-budgets are proposed.

**Implementation sequencing**

- A vertical slice (D-139). `TASKS.md` Phases 2–9 are restructured to match.

**Specification amendments**

- `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` are amended as directed, each with an amendment log.
- Unrelated text is preserved.
- New acceptance items are appended, so existing IDs stay stable.

**Research and checks**

- The Cleveland Open Access and Home Assistant preview options were researched from documentation pages only. Key facts were independently re-checked; the citation guidance and the refresh cadence were not.
- Cross-reference and consistency checks were run, followed by an independent review of this revision.

### Phase 1, final gate corrections: Codex final gate review of `9352e77` applied (Claude, commit `dda877c`)

**Pillow licensing correction**

- The earlier claim that the Pillow PyPI wheels omit `libimagequant` was false and has been withdrawn.
- The Pillow 12.3.0 wheels bundle GPL-3.0-or-later `libimagequant` 4.4.1 and LGPL-2.1-or-later FriBiDi 1.0.16 (with its shim). The full bundled-library inventory from the Codex inspection is recorded in `DECISIONS.md`. The remaining `pillow.libs` entries are marked for verification.
- Apache-2.0 covers project-owned code only (D-102). The runtime image is **not** GPL-free.
- `libimagequant` and FriBiDi are added to the copyleft review (D-135). The qualified licence review stays a release gate, and R-25 records the risk.
- Pillow 12.3.0 stays proposed. The inspection will be repeated against the exact runtime wheels once the Python version is fixed; that result is authoritative (D-130, `TASKS.md` Phase 6).

**Development-only rows**

- `mypy-extensions` 1.1.0 (MIT) and `pathspec` 1.1.1 (MPL-2.0) were recorded; neither is shipped.

**Decisions accepted**

- Q-03 (D-116): square band 0.95–1/0.95; strict near-16:9 is ±1 %, `abs(ln(r / (16/9))) <= ln(1.01)` (about 1.760–1.796); maximum upscale 2.5×. The strict threshold may be revisited after Phase 8.
- Q-11 (D-117): fallback only with landscape-only and `contain`; no fallback in `cover`.
- Q-12 (D-125): RFC 1918 IPv4 literals only; link-local, loopback, unspecified, multicast, broadcast, and the container and Supervisor networks are rejected. `192.168.178.30` is used only as the Phase 8 test value.
- Q-23 (D-137): a 30-day uncertainty quarantine.
- Q-18 item 4 (D-113): history is recorded before the preview is published.
- Q-09 (§16.3, D-114, D-140): the UI card, script, 150 s timer helper, enabled Running sensor, and optional post-run automation.
- Q-08 (D-120, D-123): the Art Institute of Chicago is the default remote source.
- Q-04 (D-118): the candidate fingerprint.

**Specification amendments**

- `PRODUCT_SPEC.md`: the RFC 1918 address rule, lifecycle steps 9 and 10 swapped, the strict ±1 % definition, and the 30-day quarantine. Each change is recorded in its amendment log.
- `ACCEPTANCE_TESTS.md`: B7 reworded in place for RFC 1918. No IDs changed.

### Phase 2: core skeleton, deterministic selection and rendering (Claude, commit `36cda3d`)

**Project and tooling** (D-142)

- The Python project lives in `frame_gallery/`: `src/frame_gallery/`, `tests/`, `pyproject.toml`, `uv.lock`, `requirements/runtime.txt` (hash-pinned, exported from the lock), `scripts/check.sh`, and `DEVELOPMENT.md`.
- `uv` 0.12.19 was installed from PyPI into the git-ignored `.tools/`, with its wheel hash checked against PyPI. The locked development environment is `frame_gallery/.venv`, also git-ignored, as are the caches and coverage data.
- The locked versions match the inventory: Pillow 12.3.0; pytest 9.1.1, pytest-cov 7.1.0, coverage 7.16.1, Ruff 0.16.9, mypy 2.3.1, and their recorded dependencies.
- Local interpreter: CPython 3.12.14, the only Python 3.12+ on this machine (bundled with the local Codex desktop runtime). No interpreter was downloaded.
- `THIRD_PARTY_NOTICES.md` is started as a provisional notice. It lists Pillow and its known bundled libraries, including GPL-3.0-or-later `libimagequant` and LGPL-2.1-or-later FriBiDi, marks the nine `pillow.libs` entries as pending Phase 6 verification, and lists the development tools. It states that the runtime is not GPL-free.

**Implemented**

- *Core types and ports:* value types, errors, the injected clock and random source, the provider, exclusion-store, image-executor, and television ports, and the runner's other ports.
- *Budget:* the 120 s phase calculator (10 / 60 / 40 / 10 s), the content window (discovery at most 30 s, 2 s PRE-STAGE reserve), allowances, clamped deadlines, and the watchdog (130 s).
- *Configuration:* option parsing with the accepted defaults; RFC 1918-only television addresses with injected container networks; the vocabulary mechanism (the built-in lists are provisional and empty until Phase 3, D-143); the capability matrix; helper merging; and visible reporting of unsupported filters.
- *Selection:* exclusions, exact-arithmetic shape and 16:9 rules, the 2.5× upscale limit, the shortlist of two, fallback only with landscape-only and `contain`, seeded tie-breaks, separate remote-probe and local-inspection allowances, and explicit end reasons.
- *Image preparation* behind the in-process executor: a bounded header pre-scan, JPEG (including MPO) and PNG only, dimension and pixel limits, EXIF orientation, mode and colour-key handling, ICC-to-sRGB conversion, `contain` and `cover`, an exact 3840 × 2160 baseline JPEG with no metadata, and the q85 fallback. The parent validates the result and computes its SHA-256.
- *Orchestrator skeleton* against fakes: every stage, outcome classification (§4.2, §12.4), deadline propagation, stop-request handling (§7.6), and settling and FINISH on every path.
- *Logging:* redaction (known secrets and credential patterns), UTC formatting, and the summary line.
- *Isolation seam:* the bytes-only JSON channel and the in-process executor. The process executor comes in Phase 5.

**Quality gates** (`scripts/check.sh`, run for this commit):

- Ruff check and format: clean.
- `mypy --strict` over `src` and `tests`: clean.
- pytest: **2 755 passed**, with **100 % line and branch coverage overall** (3 741 statements, 742 branches). The architecture's 100 % gate for `budget`, `selection`, `isolation`, `providers`, the outcome classification, the runner, and the imaging worker, pre-scan, and JPEG header parser also passes (2 400 statements, 476 branches).
- The architecture boundary test (D-107, D-145) and the whole-session network guard (H2) are active.

**Independent review.** Five lenses, each with a skeptical verifier: 75 findings, 61 confirmed (about 30 distinct issues), 12 refuted, and 2 uncertain. All confirmed findings are fixed with regression tests, or recorded as decisions (see *Review records* in `DECISIONS.md`).

**Re-verification.**

- The original reproductions were re-run against the fixes, and adversarial sweeps looked for regressions.
- The sweeps found two remaining stop-request windows, TIFF-directory bombs in image metadata, and redaction bypasses. All are fixed (D-141, D-144, D-145).
- The final design passes exhaustive stop-request sweeps with no violations: a stop request, direct or as a real SIGTERM, at every Python function entry (11 641 points) and every traced line (5 429 points).

### Phase 3: provider adapters (Claude, commits `09d7c46` to `979ef8a`; gate passed 2026-09-27)

**Implemented**

- *Documentation re-check* (D-146). Only the two official documentation pages were read. Consequences:
  - the Art Institute supports only the period filter in the beta, and takes image sizes from its Images resource;
  - Cleveland's 21 departments are confirmed verbatim, and it sends an explicit `limit` on every request.
- *Guarded gateway* (`net/`, D-108, D-115, D-131, D-147):
  - exact host policies, HTTPS on 443, public addresses only, a connection pinned to the validated IP with SNI and a post-handshake TLS and peer check;
  - at most 3 re-validated redirects; pacing; the 401/403/429 stop; the single metadata retry;
  - byte caps with one gzip layer, per-request totals enforced by a socket-shutdown timer, and the metadata allowance;
  - only `net/transport.py` imports `socket`, `ssl`, `http.client`, `urllib3`, and `certifi`.
- *Helper reader* (`ha/client.py`, D-112, D-148): one read per helper, the token sent only to a private Supervisor address inside the container's own networks, 3 s and 64 KiB per read, and the `state` string only, with the static fallback (B3–B5).
- *Local media* (`providers/local_media.py`, D-149):
  - a bounded scan through `O_NOFOLLOW` folder descriptors, with every folder and file pinned by device and inode;
  - the D-118 fingerprint, the three preview guards (F7), and one aggregated warning;
  - a header-only `inspect` worker task;
  - a guarded copy for delivery, and an empty-library hint.
- *Art Institute* (`providers/aic.py`, D-150) and *Cleveland* (`providers/cma.py`, D-151): the documented APIs only, CC0 works only, every record re-checked, the documented renditions only (IIIF `1686,`; the Cleveland print JPEG, never the TIFF), random pages without replacement, and the counts cached behind a cache port.
- *Vocabulary version 1* (D-152): 12 curated Cleveland departments and 5 periods, documented in `frame_gallery/VOCABULARY.md`, which a test keeps identical to the code. The capability matrix is narrowed for the Art Institute.
- *Tests:*
  - the shared contract suite for all three adapters;
  - end-to-end runs through the real adapters, gateway, and fetcher over synthesized APIs;
  - real HTTP-stack tests over a local socket pair.

**Dependencies.** `urllib3` 2.8.0 (MIT) and `certifi` 2026.7.22 (MPL-2.0) were installed from PyPI into the git-ignored environment only. Their installed metadata was checked, and they are recorded in the lock, `requirements/runtime.txt`, the inventory, and `THIRD_PARTY_NOTICES.md`.

**Quality gates** (`frame_gallery/scripts/check.sh`, run for the closing commit):

- Ruff check and format: clean.
- `mypy --strict` over `src` and `tests`: clean.
- pytest: **3 454 passed**, with **100 % line and branch coverage overall** (5 458 statements, 1 162 branches).
- The architecture's 100 % gate, now including `net` and `ha`, also passes (4 037 statements, 884 branches).

**Independent reviews.** Two reviewers checked the gateway (`51d9cf3`) and the helper reader and local media (`f614256`, `8761cca`). They found 11 defects, all verified, and all are fixed with regression tests in `9b736f3` and `37e85d0`. The most serious:

- the transport's time bounds did not hold after a `Connection: close` response;
- a symbolic-link swap during discovery could reach a file outside the library.

Writing the real-stack tests exposed one more transport defect, which is fixed too. See *Review records* in `DECISIONS.md`.

**Commits**

| Step | Commit |
| --- | --- |
| 1. Documentation re-check and the approved decisions (D-146; `ARCHITECTURE.md` §8.3, §9.2, §9.5, §9.6, §10, §15.2, §23) | `09d7c46` |
| 2. Guarded network gateway and the `urllib3` and `certifi` dependencies (D-147) | `51d9cf3` |
| 3. Home Assistant helper reader (D-148) | `f614256` |
| 4. Local media provider (D-149) | `8761cca` |
| 4a. Fixes from the internal review of the gateway (D-147 amendment) | `9b736f3` |
| 5. Art Institute of Chicago adapter (D-150) | `571a210` |
| 6. Cleveland Museum of Art adapter (D-151) | `72dba4a` |
| 6a. Fixes from the internal review of the helper reader and local media (D-147, D-148, D-149 amendments) | `37e85d0` |
| 7. Vocabularies, shared contract tests, and closing documentation (D-152) | `979ef8a` |
| Gate. Phase 3 gate decision: Q-25 resolved with option (a); D-146 to D-152 accepted; `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` (B2, C1) amended | `b6578d8` |

**Documentation re-check (D-146).** On 2026-09-27 the two official documentation pages were re-read in the in-app browser. No endpoint was called and nothing was recorded from a live response.

- *Cleveland:* the parameters, the response fields, the print JPEG, the CDN host, and the 21 departments are confirmed verbatim. The adapter sets `limit` on every request (the default is 1000), leaves out the one department whose name contains commas, and enforces period bounds on `creation_date_earliest`, because the inclusivity of `created_after` and `created_before` is undocumented.
- *Art Institute:* the search, count, pagination, courtesy, IIIF, and Images resource facts are confirmed. The documentation does **not** name the department or style values, the members of the colour object, or the members of the artwork `thumbnail`. Under the user's Q-14 instruction, the Art Institute therefore supports only the period filter in the beta, and it reads image sizes from the documented Images resource instead of the thumbnail. **Q-25** is resolved with option (a) at the Phase 3 gate: this stays so for the first beta, which ships without a colour filter, and no observation is approved.

### Phase 4: bounded state and duplicate prevention (Claude, commits `a74ba1c` to `b1ef7bb`; gate passed 2026-09-27)

**Implemented** (the new `store` package, standard library only)

- *Atomic primitive and reader* (D-153):
  - every write works relative to a directory descriptor: `O_DIRECTORY | O_NOFOLLOW` directories, `O_EXCL` temporary files, `fsync`, `.bak` through a hard link, rename, and directory `fsync`;
  - a self-check reads each document back with the reader's own rules before it is written;
  - the reader tries the primary, then `.bak`, then empty, with a quarantine of at most three files;
  - a newer version, or a file that cannot be read, ends the run with `state_error` before the television is touched.
- *History* (D-153): at most 20 000 entries and 5 MiB, the oldest dropped first. It changes only after `selected` (E10).
- *Upload ledger and state store* (D-154):
  - the write-ahead `uncertain` intent is committed durably before the television is contacted;
  - it is promoted on `uploaded`, and removed only without `upload_started` or on an explicit refusal;
  - the 30-day quarantine; an entry is pruned once both copies of history hold its work;
  - at most 20 000 entries and 5 MiB; the `flock` lock (`already_running`).
- *Workspace and sweep* (D-155): `/tmp/frame-gallery/run-<random>/{in,out}` at mode 0700, removed on every path. The startup sweep runs after the lock and removes only our own temporary files and leftover run directories.
- *Metadata cache and hints* (D-156, D-157):
  - `/data/cache/<provider>.json` holds counts and exhausted-page hints: at most 1 000 entries, 2 MiB, 8 KiB per entry, and 7 days, least recently used first, written once per run in FINISH;
  - the Art Institute and Cleveland adapters skip, for 7 days, pages whose works were all sent already;
  - a run whose skipped pages leave nothing new gets the hint "nothing new left for these filters".
- *Preview and records* (D-158):
  - the preview is the television payload, read again and hashed, and written atomically at mode 0644 below `/media/frame_gallery/preview`, with every path component checked;
  - `current.json` keeps the fingerprints of the last 10 previews for the local library's guard 3 (F7); `last_run.json` records every run; both are at most 16 KiB.
- *Runner and wiring:*
  - PRE-STAGE, RECORD, and PUBLISH run against the real store;
  - the runner tells the adapters which works are excluded for good (history and uploads) for their hints, reports skipped pages, and writes the provider's cache once in FINISH;
  - `StoreLayout` builds every store port from the `/data`, `/media`, and `/tmp` anchors for the Phase 6 entry point.

**Tests** (D-159):

- unit tests with failure injection on every system-call path of the store;
- E7–E10 end to end over the real store, with a fake television that emits its progress markers;
- E9 also with a real SIGKILL of a child process at four points (after the intent, after `uploaded`, after `selected`, and inside the promotion write);
- F1–F7; a full and a read-only `/data`; newer and damaged files;
- the cache across runs, with the real Art Institute adapter over the synthesized API.

**Quality gates** (`frame_gallery/scripts/check.sh`, run for the closing commit):

- Ruff check and format: clean.
- `mypy --strict` over `src` and `tests`: clean.
- pytest: **3 850 passed**, with **100 % line and branch coverage overall** (6 834 statements, 1 416 branches).
- The architecture's 100 % gate, now including `store`, also passes (5 376 statements, 1 134 branches).

**Independent reviews.**

- The store commits (`a74ba1c`, `1677ccd`, `f347ffb`): 7 findings (2 medium, 5 low) and 3 test gaps, all fixed with regression tests in `bb25277`. The most serious: timestamps at the limits of `datetime` would have ended every run as `internal_error`, and pruning could lose the newest delivery's exclusion after the history primary was damaged.
- The later commits (`4fcab6e` to `ec9e8a4`): no high-severity finding and no path to a duplicate upload; 6 low findings, all fixed with regression tests in `86cc82b`. The most material: hints rested on quarantined works and on pages that offered nothing, so a work could stay hidden beyond its quarantine and a run could wrongly report "nothing new left".
- The end-to-end cache test found that a clock step back of a few seconds discarded every full-length hint; fixed in `ec9e8a4`.

See *Review records* in `DECISIONS.md`.

**Commits**

| Step | Commit |
| --- | --- |
| 1. Atomic write primitive, reader and quarantine, and history (D-153) | `a74ba1c` |
| 2. TV-upload ledger and the file state store (D-154) | `1677ccd` |
| 3. Workspace lifecycle, startup sweep, and store layout (D-155) | `f347ffb` |
| 4. Bounded, persistent metadata cache (D-156) | `4fcab6e` |
| 5. Exhausted-page hints and the once-per-run cache write (D-157) | `b8a6c44` |
| 6. Atomic preview publication and the run records (D-158) | `5435d06` |
| 6a. Fixes from the internal review of steps 1 to 3 (D-153 to D-155 amendments) | `bb25277` |
| 7. End-to-end state scenarios E7–E10, with a real SIGKILL (D-159; D-156 amended) | `ec9e8a4` |
| 7a. Fixes from the second internal review (D-153, D-157, D-158, and D-159 amendments) | `86cc82b` |
| 8. Status, tasks, README, and development notes for the gate | `b1ef7bb` |
| Gate. Phase 4 gate decision: D-153 to D-159 accepted; the 20 000-entry bound documented in plain language (R-29); Phase 5 authorized | `13247b8` |

### Phase 5: Samsung adapter contract (Claude, commits `bfc66c7` to `937ce13`; gate passed 2026-10-02)

**Implemented**

- *`samsungtvws` 3.0.6* (D-160, D-161):
  - checked against the official PyPI metadata: the newest release, both hashes match the inventory and the lock, `LGPL-3.0` (treated as `LGPL-3.0-only`), and the sdist holds no MIT notice, GPL-2.0 statement, or relicensing statement (the R-04 check);
  - the LGPL-3.0 obligations and the notices for the library and its seven dependencies are recorded; the pinned version is installed from the lock into the git-ignored environment only, with `multidict` held at the inventoried 6.9.1;
  - the adapter surface was taken only from the installed wheel and from running it offline.
- *Television task* (`tv/samsung_task.py`, worker only; D-162):
  - it uploads only the bytes with the parent's SHA-256, read once without following a link;
  - it checks Frame support, then connects on a new library object per attempt, with every earlier connection dropped; it retries once, never after an unaccepted pairing prompt, which it tells from a silent television by the completed handshake;
  - it reads the Art API version before `upload_started` and answers the library's own version check from it; 0.97 is `unsupported`, because the library may upload twice there;
  - its time is one absolute monotonic deadline, and the pairing wait is one deadline per attempt; a connect guard lets it reach only the television's IPv4 literal and bounds each TCP connect to 5 s;
  - every failure of every step maps to a status (§12.4); the library's loggers are capped at WARNING.
- *Samsung adapter and token store* (`tv/samsung.py`, `tv/token_store.py`; D-162):
  - the stored token goes to the worker in the request, never as a file;
  - every event is checked; markers are relayed at once, and a marker out of order is relayed before the worker is stopped;
  - a new token is registered with the redactor and installed as soon as it arrives (0600, atomically, below `/data/tv/`); a rejected token is removed;
  - the worker's status is accepted only if it fits the markers the parent relayed.
- *Process executor* (`isolation/process.py`; D-163):
  - one new worker per task (`python -I -S -B`), in its own process group, with `/` as its working directory, a fixed environment, and six descriptors;
  - the worker's `ready` report is checked before the request is sent; frames are a 4-byte length and canonical JSON, with bodies held to 64 KiB;
  - the kill timer and stop requests (polled every 50 ms) kill the worker's group and the worker, and every complete event it had written is still relayed;
  - after every worker, on every path, its group and the worker are killed and reaped (waiting at most 2 s), under a lock that `terminate_all` shares; a worker that cannot be isolated is an `IsolationFailure` (`internal_error`).
- *Worker bootstrap* (`isolation/bootstrap.py`, `isolation/worker_main.py`; D-163): the verified drop to 65534 when the parent is root; on Linux dumpability 0, no-new-privileges, the parent-death signal, and empty capability sets; a lifeline thread on every platform; umask 027; every resource limit as soft = hard, `RLIMIT_NPROC` 0 last; the exact environment; logging to the parent, bounded and redacted. Every platform call goes through a seam (`OsOps`).
- *Workspace hand-over* (`store/workspace.py`; D-164): with a worker group, `frame-gallery/` and `run-*/` 0710, `in/` 2750, and `out/` 2770; downloads and local copies 0640.
- *Measurement* (`scripts/measure_prepare.py`; R-09): the §11.1 worst cases, with sources filling the 40 MiB cap, through the production prepare task in real workers.

**Tests** (D-161 to D-165):

- the television task in-process against a stand-in with the installed signatures (a conformance test compares them), and the **unchanged** library over a socket pair against a scripted television, without network: the token in the URL and the token relayed, a prompt against a hang, start-up events, a malformed connect event, the retry on a new connection with the old one dropped, the 0.97 refusal, the D2D address check, and the select refusal;
- the adapter's event checks, its token handling, and the fit of the status to the markers;
- real worker processes: their process group, the group kill, the kill timer and the stop poll with the drain, the `ready` check, the channel limits, and the lifeline; every bootstrap step and refusal in-process;
- E7–E10 over the real store, the real adapter, and the process executor (the worker runs the production delivery logic over the stand-in library), with a real SIGKILL of the runner after `uploaded` and after `selected` while its worker runs;
- every test task in a worker installs the H2 network guard first; the root-only checks run only production tasks that open no socket.

**Quality gates** (`frame_gallery/scripts/check.sh`, run for the closing commit):

- Ruff check and format: clean.
- `mypy --strict` over `src` and `tests`, for this host and as on Linux (`--platform linux`): clean.
- pytest: **4 361 passed** and 6 skipped (the Linux-only and root-only checks, which first run in the Phase 6 container, D-165), with **100 % line and branch coverage overall** (8 422 statements, 1 774 branches).
- The architecture's 100 % gate, now including `tv`, also passes (7 030 statements, 1 498 branches).

**Measured on the development host** (macOS arm64, without `RLIMIT_AS`; R-09): the peak resident memory of a preparation ranged from 165 MiB (a 64 MP baseline JPEG) to 839 MiB (a 64 MP progressive CMYK panorama in `cover`), each case in about 1.4 s or less; 150 local inspections, one worker each, took 6.8 s.

**Independent reviews.**

- A design critique before the implementation (four lenses, adversarially verified): 34 findings confirmed and 14 refuted; they shaped D-162 and D-163.
- An implementation review of `7a2d8e5` to `779e341` (five lenses, each finding verified by one or two adversarial reviewers): 45 findings confirmed, none of high severity, and 4 refuted. All are fixed or recorded in `dfe5be2` to `1c1516c`. The most material: a token the television issued before a failed wait for `ready` was lost for the retry; start-up events could stretch the pairing wait; events decoded before a malformed frame were not relayed; a stop request during a worker's start or reap could leak a descriptor or a worker; `.pth` files could run before the bootstrap.

See *Review records* in `DECISIONS.md`.

**Commits**

| Step | Commit |
| --- | --- |
| 1. `samsungtvws` 3.0.6 checked against the official metadata, its LGPL-3.0 obligations recorded, and the pinned version installed (D-160) | `bfc66c7` |
| 2. Events and stop requests in the executor seam (D-141) | `7a2d8e5` |
| 3. Samsung adapter, television task, and pairing-token store (D-161, D-162) | `33a1b83` |
| 4. The adapter surface and the television task design recorded (D-160 to D-162) | `9fca785` |
| 5. Process executor, worker bootstrap, and worker entry (D-163) | `83602de` |
| 6. Workspace handed to the worker's group (D-164) | `f98c4c8` |
| 7. E7–E10 with the process-based television worker, including a real SIGKILL of the runner | `4d8e87f` |
| 8. The prepare measurement, and Linux type checks in the gates (R-09) | `0f930ce` |
| 9. The executor, the workspace hand-over, and what ran where recorded (D-163 to D-165) | `779e341` |
| 9a. Fixes from the implementation review: the executor, the bootstrap, and runnable container checks | `dfe5be2` |
| 9b. Fixes from the implementation review: the television task, the adapter, and the outcome hint | `d449e64` |
| 9c. Fixes from the implementation review: the measurement covers the §11.1 worst cases and fills the source cap | `98f92ce` |
| 9d. Decisions, status, and development notes after the review (D-160 to D-165 amended) | `1c1516c` |
| 10. Status, tasks, and README for the gate | `937ce13` |
| Gate. Phase 5 gate decision: D-160 to D-164 accepted, D-165 with a condition; the open questions decided; Phase 6 authorized | `31e3868` |

### Phase 6: Home Assistant app packaging (Claude, commits `ff64da8` to `818d803`; gate passed 2026-10-03)

**Implemented** (D-166 to D-171):

- *Entry point* (D-166): `python -m frame_gallery` builds the production ports and runs once: the deferred cancellation before the SIGTERM handler, the environment reduced before anything runs, the token kept only with helpers, logging through the redactor, one process executor with a start shield, the refusal to run unless the isolation is enforced (exit 70), the watchdog at `T` + 10 s (exit 71), the options file (64 KiB, strict JSON, every failure with a remedy), the container's networks from `/proc/net/route` (fail closed on Linux), and the preview fingerprints read without changing state.
- *Container image* (D-167): the pinned Home Assistant base (Alpine 3.24.1, s6-overlay 3.2.3.0); Alpine's `python3=3.14.8-r0`; a venv with the hash-pinned `musllinux` wheels from PyPI only; the app image as the last stage, so a build without a target gives it, and without pip or any wheel; `with-contenv` and `S6_CMD_RECEIVE_SIGNALS=1` meet the D-130 checks (c) and (d), so the plain-Alpine fallback is not needed.
- *App files* (D-168): `config.yaml` and the translations, generated from the app's own definitions; the AppArmor draft in complain mode with the six capabilities the parent needs, whose syntax `apparmor_parser -Q -T` accepts (Codex's follow-up check; its enforcement on the Green is untested); `DOCS.md` (installation, pairing, options, capability matrix, own images, the draft dashboard, the log, limitations, privacy, licences), the store text, the changelog, an icon, and a logo.
- *`inspect`* (D-169): the parent opens each library file read-only and passes up to 16 descriptors to one worker, which never opens a library path; every end of the selection pass measures the waiting batch first; the library's warning comes after the last batch.
- *Inventory* (D-171): from the exact two Pillow runtime wheels and from the image, without an SBOM tool (`scripts/image_inventory.py`). Neither `libimagequant` nor FriBiDi is in the wheels; zlib is Alpine's. libbsd's and libmd's licences come from the official Alpine package directory (Codex's follow-up check); libmd's includes "Public Domain", which is not an SPDX identifier.

**Quality gates** (`frame_gallery/scripts/check.sh`, run for the closing commit):

- Ruff check and format: clean.
- `mypy --strict` over `src`, `tests`, and `scripts`, for this host and as on Linux: clean.
- pytest: **4 559 passed** and 8 skipped (the Linux-only and root-only checks, which run in the container), with **100 % line and branch coverage overall** (8 940 statements, 1 894 branches); the architecture's 100 % gate also passes (7 323 statements, 1 584 branches).

**Container checks** (`scripts/container_check.sh`, at `79dc8f7`; every container with `--network none`, no host directory mounted):

| Check | `aarch64` (native) | `amd64` (Rosetta) |
| --- | --- | --- |
| A build without a target gives the app image | passed | passed |
| D-130 (a) versions | Alpine 3.24.1, Python 3.14.8 | Alpine 3.24.1, Python 3.14.8 |
| Inventory | 61 Alpine packages, 11 Python distributions, 21 Pillow libraries as in `RECORD`, no wheel | the same versions; 21 Pillow libraries as in `RECORD`, no wheel |
| D-130 (b) exit status | 70 came through as 70 | 70 came through as 70 |
| D-130 (c) stop request | at 3.0 s, cleaned up at 11.0 s, stop took 11 s | at 2.6 s, cleaned up at 10.6 s, stop took 11 s |
| D-130 (d) `SUPERVISOR_TOKEN` | visible | visible |
| Smoke run (one library file, no network) | `tv_unreachable`, exit 0 | `tv_unreachable`, exit 0 |
| D-165 user pass (uid 1000, `FRAME_GALLERY_REQUIRE_ISOLATION=user`) | 4 562 passed, 5 root-only skipped | 4 562 passed, 5 root-only skipped |
| D-165 root pass (`FRAME_GALLERY_REQUIRE_ISOLATION=root`) | 5 of 5 passed | 5 of 5 passed |
| Worst case under the real `RLIMIT_AS` 1 GiB, as root (R-09) | 13 of 13 cases succeed; peak 766 MiB of address space (754 MiB resident, 1.4 s), the progressive CMYK panorama in `cover` | not run: under Rosetta every process carries about 278 MiB more address space, and the heaviest case fails (an earlier run; D-170) |
| 150 inspections | 10 workers, 0.61 s | — |

The condition of D-165 is met: the Linux and root isolation tests pass on both architectures, and the measurement passes under the real limit on `aarch64`, the Green's architecture. The native `amd64` memory measurement is open: no native `amd64` host was available, and the result under Rosetta is informative only (D-170). The Phase 6 gate made it mandatory before an `amd64` version is published, at the latest in Phase 9.

**Independent review** (8 agents, before the gate): 20 findings, 19 confirmed (3 high, 7 medium, 9 low) and 1 refuted; all are fixed or recorded in `4b6a0fd` to `79dc8f7`. The high ones: the last batch was lost when the candidate allowance ended the selection pass; a build without a target produced the test stage; the app image held the pip wheel that Python bundles. See *Review records* in `DECISIONS.md`.

**Commits**

| Step | Commit |
| --- | --- |
| 1. The entry point and its production adapters: options file, container networks, watchdog, start shield, refusal without isolation (D-166) | `ff64da8` |
| 2. A worker's memory peaks from `/proc` on Linux (R-09) | `c346c1a` |
| 3. Tests that hold on Linux and in an installed image | `e0e56e7` |
| 4. The container image, its pinned inputs, and its checks (D-167) | `505cc2f` |
| 5. App metadata, translations, the AppArmor draft, and the documentation (D-168) | `1b29e4e` |
| 6. The test stage sees every file the tests check | `d91927a` |
| 7. The descriptor check ignores an emulator's own descriptors | `ec04883` |
| 8. `inspect` reads parent-opened descriptors in batches (D-169) | `0a8379c` |
| 9. Selection inspects local candidates in batches (D-169) | `de69bf6` |
| 10. A root check of `inspect` over a passed descriptor | `247de9b` |
| 11. The entry point uses the executor protocol directly | `0be1cb7` |
| 12. An inventory of what the image ships, without an SBOM tool (D-171) | `9deceff` |
| 13. The documentation names the image's actual copyleft parts (D-171) | `3ef529f` |
| 14. Decisions D-166 to D-172, the authoritative inventory, the notices, and the development notes | `60aed51` |
| 15. Review fix: every end of the selection pass measures the waiting batch (high) | `4b6a0fd` |
| 16. Review fix: the library warning counts the last inspection batch; an extra event is a protocol failure | `19ab47b` |
| 17. Review fix: the early read of the preview fingerprints changes nothing | `bdaf81e` |
| 18. Review fix: a route table the app cannot understand fails closed | `cd7fd88` |
| 19. Review fix: every options-file message says what to do | `1af2b26` |
| 20. Review fix: the app image is the last stage and holds no pip (two high) | `9f8984c` |
| 21. Review fix: the AppArmor draft names the parent's six capabilities | `26d2284` |
| 22. Decisions, notices, tasks, and documentation after the review | `79dc8f7` |
| 23. Status and the final results for the gate | `4b21f9d` |
| 24. Codex's follow-up checks recorded (the libbsd and libmd licences, the AppArmor syntax check); the Pillow statements in `ARCHITECTURE.md` corrected; the native `amd64` measurement recorded as open | `818d803` |
| Gate. Phase 6 gate decision: D-166 to D-172 accepted, the 1 GiB limit unchanged; the native `amd64` measurement mandatory before an `amd64` version is published; Phase 7 authorized | `722bae1` |

## Specification deviations

The Phase 3 and Phase 4 deviations were accepted at their gates (2026-09-27), the Phase 5 deviations at the Phase 5 gate (2026-10-02; D-165 with a condition, met in Phase 6), and the Phase 6 deviations at the Phase 6 gate (2026-10-03); `ARCHITECTURE.md` is amended to match. Phase 7 adds no deviation; D-173, proposed for its gate, records how it validated and proposes a clarification of D-162's wording.

| Accepted item (Phase 6) | Where |
| --- | --- |
| D-130's checks (c) and (d) are met only with two s6-overlay settings (`S6_CMD_RECEIVE_SIGNALS=1`, `with-contenv`); the plain-Alpine fallback is not used. | D-167 |
| `BUILD_ARCH` and `BUILD_VERSION` are required, with no fallback to `TARGETARCH`; the app image sets its own OCI labels (amends D-130). The app image is the last stage, installs `python3` again, and removes the pip wheel that Python bundles. | D-167 |
| The image installs per-platform requirement files generated from the lock (amends D-142). | D-167 |
| The parent needs six capabilities, among them `fsetid` and `dac_read_search`, not only the four the draft first named (§17.6 "minimal capabilities"). | D-168, D-172 |
| `inspect` runs in batches of up to 16 files (§8.3 allows 50), because each descriptor counts against the worker's `RLIMIT_NOFILE` of 32. The library's aggregated warning comes after selection, through the new `ProviderBinding.after_discovery`. | D-169 |
| New modules beyond §21: `app/networks.py`, `store/options_file.py`; scripts `image_requirements.py`, `image_inventory.py`, `app_config.py`, `app_images.py`, `container_check.sh`. | D-166 to D-171 |
| The bundled-library inventory changes: `libimagequant` and FriBiDi are not in the runtime wheels (`ARCHITECTURE.md` §17.2, §23, and §24 are corrected at the user's request). The licences of libbsd and libmd come from the official Alpine package directory (Codex's follow-up check), so the condition of `dda877c` is met; libmd's "Public Domain" is not an SPDX identifier. | D-171 |

| Accepted item (Phase 5) | Where |
| --- | --- |
| The pairing token travels in the request and comes back as a `token` event (at most one per connection attempt), not in a seeded token file (§12.1 `token_seed_path`, §12.2). A token must have 6 to 64 characters. | D-162 |
| `DeliveryRequest` carries the delivery's SHA-256, and the worker uploads only bytes with it; `uploaded` may come without a content ID (port changes, §12.1). | D-162 |
| Art API 0.97 is `unsupported` in the beta; §12.4 row 6 (explicit upload refusal) is not produced; a non-transport failure before `connected` is `protocol`; `insufficient_time` before `connected` gets no hint (§12.4). | D-162 |
| The pairing wait is one deadline per connection attempt; D-114's "connect ≤ 5 s" is the TCP connect; the television client name is `frame_gallery` (D-138). | D-162 |
| `tv/samsung_task.py` imports `socket` for its connect guard (D-147 made `net/transport.py` the only one); new modules and internal dependencies beyond §5 and §21. | D-162 |
| Frames are a 4-byte length and canonical JSON of up to 64 KiB plus 1 KiB of envelope, bodies held to 64 KiB (§11.3 `recv_bytes(maxlength = 64 KiB)`). Workers start with `-I -S -B`. The bootstrap adds dumpability 0, no-new-privileges, a lifeline thread, `RLIMIT_NPROC` 0, and a `ready` handshake; a failed isolation is `IsolationFailure`, reported as `internal_error`. | D-163 |
| The workspace is handed to the worker's group: `frame-gallery/` and `run-*/` 0710, `in/` 2750, `out/` 2770; downloads and local copies 0640 (amends the accepted D-155 and §13.1). | D-164 |
| The root-only and Linux-only checks and the measurement under the real `RLIMIT_AS` run first in the Phase 6 container; the TASKS measurement item is met only in part. Accepted on the condition that they pass in Phase 6; mandatory before any live test on the Green. | D-165 |

Not accepted as a deviation at the Phase 5 gate: `inspect` ran one worker per file, not batches of up to 50 (§8.3). The Phase 5 gate decided to implement batching in Phase 6, with parent-opened read-only descriptors where possible (D-149, D-164). *Implemented in Phase 6, in batches of up to 16 (D-169, accepted at the Phase 6 gate).*

| Accepted item (Phase 4) | Where |
| --- | --- |
| The ledger prunes only when an intent is committed, and only works that both copies of history hold (§13.6 step 5 says: on the next ledger write, once the work is in history). This is stricter: a damaged history primary can never lose the newest delivery's exclusion. | D-154 |
| The reader also quarantines files that are not regular or exceed the size bound (§13.2: "only parse or schema failures"). A file that exists but cannot be read, or one written by a newer version, ends the run with `state_error` instead of falling back to `.bak` or an empty state. | D-153 |
| After a failed directory `fsync` that follows a successful rename, an intent is an error (`state_error`, stricter), while recorded history, a promotion, the preview, and the records count as written, with a warning. | D-153, D-154, D-158 |
| Adapters receive a predicate for the works excluded for good (history or `uploaded`), for the exhausted-page hints only, and still yield every candidate (§9.1). A page is hinted only if it offered works and all of them were sent already. Skipped pages lead to the hint "nothing new left for these filters" (an extension of §4.2), and `last_run.json` reports them. | D-157 |
| The metadata cache is written once per run in FINISH, before the last-run record (§4.1 names only the last-run record there). An expiry more than 7 days ahead is cut to 7 days from now. | D-156, D-157 |
| Internal dependencies beyond §5: `store` uses `selection.exclusion`, `imaging.contract`, and `budget` (`selection` imports no `store` module, so there is no cycle); `providers.cache` imports `store.cache` (as §5 lists). `WorkspacePaths` moves to `domain.py`, `PublishError` to `errors.py`, the qualified-identifier rule to `domain.py`, and the D-118 fingerprint to the shared `fingerprint.py`; `DeliveryArtifact` gains `fingerprint`. | D-153, D-154, D-155, D-156, D-158 |
| Timestamps in state files must lie from 2000 to 8999, and later versions must keep writing `format` and `version` first. | D-153 |
| `in/` and `out/` have mode 0700 until Phase 5 sets the modes that the unprivileged worker needs (§11.3; amended by D-164, accepted at the Phase 5 gate). The preview file is `latest.jpg` until Phase 8 chooses the refresh mechanism (D-140). | D-155, D-158 |

## Next action

**Current Phase 8 action:** address the concrete loading-feedback and stop-warning findings with user-approved changes; complete the remaining supervised checks recorded in `PHASE8_REPORT.md`. Phase 7's installation gate already passed. Phase 9 and publication need separate approval.

**Decisions needed, by phase:**

| Before | Decisions |
| --- | --- |
| Phase 7 gate | The release-candidate report and D-173 (proposed); the user's approval of the live installation on the Home Assistant Green and of the television test (Phase 8). |
| Phase 8 | Explicit approval for the live run, which is also the first live request to the museums and the first time the project contact is transmitted (Q-22); Q-21 (install route). The Linux and root checks and the measurement under the real `RLIMIT_AS` passed in Phase 6 (the condition of D-165). The exact `python3` pin breaks later builds once Alpine replaces the package (R-32), which matters for the install route. The live check of the Art Institute `params` form (D-150). The preview refresh mechanism and file names (D-140). TLS pinning, once the TV's certificate is observed (R-03). |
| Phase 9 | D-101 (final name), Q-13 (repository URL, which also replaces the contact in the User-Agent, D-119); the builder-action and Cosign rows; the native `amd64` memory measurement (mandatory before an `amd64` version is published, D-170); the enforcement of the AppArmor profile (D-168); the qualified licence review (D-135, with R-33 and libmd's "Public Domain" part; a release prerequisite); approval to publish. |

## External state

- No Home Assistant changes; no `configuration.yaml` touched.
- No television connection attempted.
- No GitHub repository accessed, created, or modified; no GitHub-hosted page fetched.
- Phase 5 pulled, built, and published no container image.
- **Phase 6** used only the network steps the user approved on 2026-10-02: Docker Desktop was started (it may contact Docker's own servers, for example to check for updates); the tags of `ghcr.io/home-assistant/base` were read, and the image was pulled for `aarch64` and `amd64`, pinned by tag and digest; every build installed `python3` from `dl-cdn.alpinelinux.org` and the hash-checked `musllinux` wheels of the runtime and the test tools from PyPI; the two Pillow runtime wheels were downloaded from `files.pythonhosted.org` into this session's scratch directory for the inventory (D-171). The images were built locally (`frame-gallery:dev-*`, `frame-gallery-checks:dev-*`) and never pushed. Every container ran with `--network none` and without a host directory mounted; results went to the git-ignored `build/container-checks/`. The local Docker image store also holds images from other, unrelated work; they were neither inspected nor used.
- **Phase 7** used no network and built, pulled, downloaded, and installed nothing. Docker Desktop was still running from Phase 6 (as approved on 2026-10-02, it may contact Docker's own servers). The checks ran in containers of the existing images `frame-gallery:dev-*` and `frame-gallery-checks:dev-*`, each with `--network none` and without a host directory; the silent television of the failure-path runs was a helper container whose own network namespace has no interface but loopback. The runs created the Docker volumes `fg-check-data-<arch>`, `fg-check-media-<arch>`, `fg-paths-<arch>-data`, and `fg-paths-<arch>-media` and the helper `fg-paths-<arch>-tv`, and removed them again; the results went to the git-ignored `build/container-checks/` and `build/failure-paths/`. Two older volumes, `fg-smoke-data` and `fg-smoke-media` (created on 2026-10-02 at 19:01 UTC, not by a committed script), were left untouched. The images of unrelated work in the local Docker store were neither inspected nor used.
- At the Phase 6 gate, Codex ran the follow-up checks the user had narrowly approved, outside this session, and reported them on 2026-10-03: it read the licences of libbsd and libmd in the official Alpine package directory, and ran `apparmor_parser -Q -T` on the profile in a temporary aarch64 container. This session used no network for them and only recorded the results.
- The Phase 6 review (8 agents) worked only in the repository, on the container-check outputs, and on the Pillow wheels in this session's scratch directory, without network access or Docker, and changed nothing in the repository.
- Dependencies were installed only into the git-ignored project environment (`frame_gallery/.venv`) and the git-ignored `.tools/` directory, from PyPI (`pypi.org`, `files.pythonhosted.org`) only. Nothing else was installed or modified on the machine.
- No provider API or image endpoint called. The Phase 3 re-check read only the two official documentation pages (D-146). Every provider test uses synthesized documents (`tests/support/museums.py`); nothing was recorded from a live API.
- Phase 3 installed `urllib3` 2.8.0 and `certifi` 2026.7.22 from PyPI into the git-ignored project environment only.
- The two internal reviewers worked only inside the repository and without network access, using local files and a socket pair. One of them once ran `grep` on the standard library's `http/client.py`, which lives with the local interpreter outside the repository. That is language source, not predecessor material, and the disclosure is recorded in `DECISIONS.md`.
- Earlier research (Phases 1 and 2) read public documentation pages, policy pages, and `robots.txt` files, plus one Microsoft Q&A answer (cited as a non-documentation source) and search-result snippets where a page blocked automated readers. Reading used web-fetch tools, `curl` (including PyPI's JSON metadata API), and the in-app browser.
- Phase 4 worked only in the repository, in temporary directories created by the tests, and in this session's scratch directory. The SIGKILL tests start child processes of the project interpreter on this machine. No dependency was added.
- The two Phase 4 reviewers worked on `git archive` snapshots in the session's scratch directory, without network access, and changed nothing in the repository.
- Phase 5 read the official PyPI metadata of `samsungtvws` 3.0.6 (JSON API) and downloaded its sdist and wheel into this session's scratch directory to check their hashes and licence files (D-160). It installed `samsungtvws` 3.0.6 and its dependencies (`websocket-client`, `requests`, `charset-normalizer`, `idna`, `yarl`, `multidict`, `propcache`) from PyPI into the git-ignored project environment only.
- No television, Home Assistant instance, or provider was contacted in Phase 5. The tests run the unchanged `samsungtvws` over socket pairs against a scripted television, and every test worker installs the H2 network guard.
- The Phase 5 design critique (52 agents) and the implementation review (54 agents) worked only on this repository and the installed packages in the project environment, without network access, and wrote experiments only to the session's scratch directory; they changed nothing in the repository.
- Apache-2.0 is approved. The `LICENSE` file will be added when publication is prepared (Phase 9).

## Known limitations

- **Very old works can come back** (R-29, accepted for the first beta at the Phase 4 gate). The app remembers the latest 20 000 delivered works; an older one could in theory be shown again. At one artwork a day that takes about 55 years.

## Known open decisions

See `DECISIONS.md` for the full list. The most material:

- **Preview freshness mechanism** (D-140). Native Local File refresh of `latest.jpg` is selected on the observed HA 2026.9.4 Green setup; repeated card, real event-automation, app-page and no-match evidence is in `PHASE8_REPORT.md`. The loading indicator remains a separate unresolved issue.
- **D-173** (proposed for the Phase 7 gate): how Phase 7 validated, and a clarification of D-162 point 4 (the REST check before the art channel is not retried, which is within D-115).
- **Copyleft components in the runtime image** (R-17, D-135, D-171). The Phase 6 inspection of the exact runtime wheels found neither `libimagequant` nor FriBiDi in them, so R-25 is closed (Phase 6 gate); the image's copyleft parts are `samsungtvws`, Pillow's fribidi-shim, and GPL and LGPL Alpine packages such as BusyBox, bash, readline, and gdbm. The licences of libbsd and libmd are verified from the official Alpine package directory (Codex's follow-up check at the Phase 6 gate); libmd's "Public Domain" is not an SPDX identifier, and the licence review settles its form. Only the licences of s6-overlay, tempio with its Go modules, and bashio are still to be read from upstream (R-33). The qualified licence review is a release prerequisite.
- **Final name** (D-101). The trademark wording is tracked as R-14.
- **Copyleft source-availability mechanism** (D-135).
- **Local tests versus the runtime build** (R-26): since Phase 6 the full suite runs inside the image on both architectures (D-170); CI follows in Phase 9.
- **TLS pinning** (R-03): decided after the TV's certificate is observed in the supervised Phase 8 test.
- **The image worker's memory limit** (R-09): measured under the real 1 GiB `RLIMIT_AS` in Phase 6, the heaviest case peaks at 766 MiB on `aarch64`; the 1 GiB limit stays (D-170, Phase 6 gate). On `amd64` it was measured only under Rosetta, where every process carries about 278 MiB more address space and the heaviest case fails, reported as `decode`. Phase 8 repeats the measurement on the Green. The native `amd64` measurement is mandatory before an `amd64` version is published, at the latest in Phase 9.
- **Licences still to read** (D-171, R-33): s6-overlay, tempio with its Go modules, and bashio (in the base image); their texts are not in the image, and reading them needs an approved network read. libbsd's and libmd's come from the official Alpine package directory; the licence review settles the exact form of libmd's "Public Domain" part.
- **The AppArmor draft** (D-168): complain mode until Phase 9. Its syntax is checked (`apparmor_parser -Q -T`, Codex); its enforcement is not: Phase 8 reads what it would refuse on the Green, and Phase 9 enforces and verifies it, a release prerequisite.
- **Pre-emption** (R-27): in force since Phase 6; the entry point builds the process executor (D-166).
- **A Supervisor build on the Green** (R-32): until images are published, the Supervisor builds the app on the device, which needs the same network sources; Phase 8 settles the install route (Q-21).
