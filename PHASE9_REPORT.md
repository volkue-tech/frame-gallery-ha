# Phase 9 progress report

Date: 2026-10-03. **In progress, not a release approval.**

Authorized scope: Frame Gallery hardening, engineering licence audit, publication
preparation and the separate Green test app; final personal repository name
`volkue-tech/frame-gallery-ha`. No predecessor source or business identity used.

## Enforced Green worker probes

Observed via the already authorized Firefox Terminal & SSH path. The own test
app advanced from `0.1.0.dev1` to `0.1.0.dev7`; protection stayed on, no host
networking or new Docker capability was granted. Official Supervisor updates
reloaded the profile. Rebuild alone was not treated as proof of reloading it.

Under actual enforcement `/init` and the S6 preinit interpreter scripts required
read permission as well as inherited execute (`rix`). The early starts failed
before artwork/TV work, and the exact rules were corrected. A diagnostic's own
chmod-after-chown failed without FOWNER; its setup order was corrected instead of
granting that capability.

AppArmor's observed file/executable restrictions worked, but image TCP/UDP
socket creation and loopback attempts were allowed despite `deny network`.
The cause is not established. D-180 adds worker-only seccomp; no new runtime
dependency, privileges or public disable switch. Actual combined probes passed:

| Check | Image worker | TV worker |
| --- | --- | --- |
| Kernel label | `local_frame_gallery_dev//image_worker (enforce)` | `local_frame_gallery_dev//tv_worker (enforce)` |
| UID / GID | 65534 / 65534 | 65534 / 65534 |
| No-new-privileges / HA token absent | yes / yes | yes / yes |
| Address-space soft / hard limit | 1 GiB / 1 GiB | 512 MiB / 512 MiB |
| IPv4 TCP | denied | allowed |
| UDP | denied | denied |
| Prepared output read | allowed | allowed |
| Prepared output write | allowed | denied |
| Options and unrelated tmp access | denied | denied |
| Shared-memory write / executable / return transition | denied | denied |

Network probes contacted only closed port 9 on **container loopback**; no TV or
external provider was contacted. The final probe reported two workers passed,
all eight confirmed record/options/preview hashes unchanged and scratch empty.
The supplementary parent-output-read probe initially failed EACCES. D-182
replaced unavailable DAC_READ_SEARCH with Docker's already-existing DAC_OVERRIDE
in the parent AppArmor rule, without cap-add or any child change. After the
official dev6 Supervisor update, parent read passed as well as all listed worker
checks, with all eight hashes unchanged and scratch empty. This proves the listed
permissions, not an unprivileged parent; the parent retains its existing trusted
state/worker-management responsibilities.

## Restored normal app and delivery regression

The two temporary diagnostic modules were moved out of the app source to
`/share/frame-gallery-phase9-diagnostics-used-v4/`; the normal `frame_gallery`
module CMD was restored and rebuilt successfully. A macOS AppleDouble sidecar
that had broken diagnostic compilation was moved to a separate recoverable
holding directory; subsequent transfer archives explicitly disable copyfile and
xattrs and contain only the intended profile.

Two existing-card-started runs used the original Cleveland / Chinese Art /
before-1400 filters, with landscape/strict-TV-format/contain and the explicit
test timer unchanged:

- **16:21:36 UTC, dev6:** delivered `cma:97667`, TV markers connected,
  upload_started, uploaded, selected, exit 0, 19.4 s. Preview changed without
  reload and loading ended. This run exposed EACCES refreshing the two backup
  generations, not the primary history/ledger writes.
- **16:24:29 UTC, dev7:** following D-183's official Supervisor update, delivered
  `cma:123590`, the same positive TV markers, exit 0, 16.9 s. Neither backup
  warning recurred. Preview refreshed again without reload and loading ended.
  State: seven files / 4,323 bytes; preview: one file / 983,879 bytes; cache:
  two files / 513 bytes; all reported temporary/run-directory counts zero,
  scratch zero files/bytes. These are bounded storage statistics, not a deep
  integrity audit.

D-183 grants only two parent `link subset` pairs, each temporary backup name to
its own history/ledger primary. No general link access, worker state permission,
mount or Docker capability is introduced. Original options were reconfirmed;
dev7 stopped, protected true and host networking false. Confirmed records were
not reset and legitimately gained the two deliveries. Saved pre-Phase-9 source
and the original app-only backup remain. No existing app/dashboard or
`configuration.yaml` changed. This is not yet a clean public installation.

### App-only checkpoint and backup-generation verification

The approved local partial-backup route created
`/backup/frame-gallery-test-hardening-20261003.tar`, slug `1273a68b`, 47,022,080
bytes. Its outer archive contains only the own app archive and backup metadata;
no Core/folder archive, cloud upload, Mac download or restore. The original
pre-hardening checkpoint is retained as well.

Only the four fixed history/ledger JSON documents were extracted locally to an
owned temporary directory for count/boolean checks. History has 14 unique IDs,
its backup 13; the backup is a subset and differs by the latest delivery only.
The ledger has three uploaded IDs, all also in history; the ledger backup keeps
the latest delivery's uncertain write-ahead entry. Thus the corrected backup
refresh is proven from the snapshot, not merely inferred from missing warnings.
No token/options/image contents or other app were inspected.
Comparison with the retained pre-hardening checkpoint confirms all twelve older
IDs remain and the only additions are the two observed Cleveland deliveries.
The four derived audit copies and their empty temporary directories were removed;
both recoverable backups remain. Free space afterward: 14.8 GiB (rounded `df`).

## Local verification

- `bash scripts/check.sh`: exit 0, Ruff and strict mypy (host/Linux) clean over
  227 files; 4,712 passed / 11 skipped; full package 100% line/branch coverage
  (9,168 statements / 1,954 branches), mandated subset also 100%
  (7,533 / 1,640). Log: `build/phase9/check-20261003.log` (ignored).
- Three new real-kernel seccomp integration tests: native aarch64 Docker,
  non-root user, network disabled; 3 passed. No connections/packets are made by
  these tests; they only create/refuse sockets in disposable children.
- Updated aarch64 container validation: build/inventory/base init/stop/token and
  smoke checks succeeded; 4,714 user tests passed / 6 skipped, root checks 5/5.
  The build preceded the three new integration tests above. Full command exit 0:
  all 13 worst-case sources passed twice under real 1 GiB RLIMIT_AS, peak address
  space 765.5 MiB, slowest prepare 1.44 s; 150 inspections passed (0.61 s total).
  This is native aarch64 Docker on the Mac, not a new Green or amd64 measurement.
  Docker has no own AppArmor attachment: these decoder memory/root checks are
  separate from the actual enforced Green probes and seccomp kernel tests.
- Workflow YAML parsed and shell syntax checked. The native ARM/Intel CI workflow
  is prepared, with pinned MIT actions and hash-pinned uv, no registry/repository
  write permissions. No hosted execution, native amd64 result or publication is
  claimed. D-181 records the exact versions and sources.
- After D-182/D-183: native local `check.sh` exit 0, Ruff and both strict mypy
  passes clean over 227 files; 4,713 passed / 11 expected skips, full package
  100% line/branch (9,168 / 1,954), mandated subset 100% (7,533 / 1,640).
  Log: `build/phase9/check-dev7-native-20261003.log`. A sandboxed attempt had two
  workspace group/mode failures; the native run in the existing environment
  passed without changing code, tests or relaxing assertions.

## Licence/source engineering audit

Apache-2.0 applies only to project-owned code. Root LICENSE/NOTICE and initial
exact upstream texts are added. Exact Python sdists for all eleven installed
distributions were downloaded from PyPI and SHA256-checked; retained under
ignored `build/phase9/python-sources/` with their source manifest. Original
certifi/samsungtvws licences and requests/propcache/yarl licence/NOTICE files are
preserved in `LICENSES/`, together with all eleven primary package licences and
the public source URL/hash manifest. The Pillow sdist contains the fribidi-shim `.c`/`.h`;
this does not complete corresponding source for its other bundled libraries.
Six version-matched skarnet upstream source archives and ISC COPYING files were
also retained; their public URL/calculated-hash manifest is under `LICENSES/`.
Source-to-binary/build-dependency completeness remains open, not proven by a
download hash.

The audit found previously unlisted jemalloc in the pinned base. 5.3.1 is the
official recipe version; its binary helper reports a missing-tags placeholder.
Inventory now detects its presence and checks the notice row. Binary provenance,
all subsidiary s6/Go/bundled-library texts, Alpine recipes/patches and complete
corresponding sources/rebuild information are still open. This is not a lawyer's
opinion, a GPL-free image, or a completed licence-release gate.

Follow-up D-184 found three further installed S6 packages outside `/package/admin`:
s6-dns 2.4.1.2, s6-networking 2.8.0.0 and skalibs 2.15.0.0. The fixed inventory
scans admin/net/prog/web without following category/version aliases. Its 22 unit
tests pass and execution in the existing native ARM image reports all eleven
packages. This changes only the development inventory and notices, not the app
runtime or privileges. Nine additional official base-component archives are
retained with calculated hashes in `LICENSES/base-source-manifest.json`; four
additional ISC COPYING and tempio/docker-base Apache texts are preserved.
The s6 source build also names statically linked BearSSL and libc: their exact
corresponding sources/build provenance, Go, Alpine and native-Pillow completeness
remain open. The initial hosted run tests `39d25da`, before this inventory fix.

Twenty-one further Go source ZIPs (2,901,790 bytes total) were retained from the
official module proxy, with all directory hashes matching exact tempio `go.sum`.
Eleven are linked in the observed binary; ten are extra test/build-source modules.
The eleven primary licences were read (MIT/BSD-3-Clause/Apache-2.0), their original
files preserved byte-for-byte and their versions/obligations listed in notices.
`LICENSES/go-source-manifest.json` retains archive and directory hashes. No module
was installed or executed. Go toolchain and subsidiary-attribution/source-build
completeness stay open; the corresponding-source release bundle is not complete.

### Further source-availability evidence (D-186/D-187)

Both existing app images have identical 61 name/version/origin/build-commit
tuples in apk metadata (Intel was read under emulation for metadata only, not
claimed as a native test). All 45 exact official aports recipe directories were
retained, 243,307 bytes; 197 local source/patch files match SHA512. All 58 upstream
files also match recipe SHA512 values, 282,359,632 bytes retained on the Mac only.
No recipe was evaluated, code executed or archive symlink followed. Offline
hashes were rechecked before `LICENSES/alpine-source-manifest.json` was generated.

Exact BearSSL source/MIT text, identified static-musl source/full COPYRIGHT and
Go 1.26.5's official hash-verified source/LICENSE/PATENTS are retained. Both
documented S6 toolchains were passively inspected and identify libc
`1.2.6-git-11-g5122f9f3`; this identifies build inputs, not installed-static-object
equivalence. Original GCC Runtime Library Exception 3.1 is preserved after reading
the exact libgcc/libstdc++ headers. `LICENSES/static-source-manifest.json` retains
these records. Original libbsd/libmd COPYING files are read and preserved in full;
the local libmd public-domain LicenseRef denotes its actual dedication statements.

Native-Pillow source completeness, licence applicability, subsidiary attributions,
packaged distribution texts, replacement/rebuild instructions and final
source-bundle assembly remain open. No legal or binary-release clearance claimed.

### Native-Pillow source and patent evidence (D-189)

The official Pillow 12.3.0 build files, exact multibuild submodule and libavif's
codec inputs are retained and passively read. Twelve further native sources,
64,401,436 bytes total, plus five release/build-input archives are SHA256-checked;
four overlapping native sources reuse the SHA512-verified Alpine archives.
The public native-source manifest records their exact versions, URLs and hashes.
Only dav1d's SHA256 is publisher-verified; calculated source hashes do not prove
binary equivalence or reproducible rebuilding.

All 27 new original licence/patent/patch texts are read and byte-compared against
their archives, including full AOM Patent License 1.0, libyuv/webp patent grants,
libjpeg-turbo's complete terms, FreeType FTL and subsidiary licence map, TIFF's
Berkeley notice and the remaining native primary texts. Pillow's libtiff
security cherry-pick `782a11d6b5b61c6dc21e714950a4af5bf89f023c` is retained and
also byte-compared to the decoded installed ARM wheel SBOM patch. It was not
newly applied by this project. The public notice adds the Berkeley acknowledgement.

Three offline repository data regressions plus the existing inventory tests
pass (28 targeted tests). Full unsandboxed local `check.sh` also passed:
4,720 tests / eleven expected skips, Ruff, strict mypy (host/Linux, 228 files),
100% package line/branch coverage (9,168 statements / 1,954 branches), unchanged
100% mandated subset. Log: `build/phase9/check-pillow-native-notices-20261003.log`.
Complete shipped notice packaging, subsidiary
applicability, final corresponding-source assembly and replacement/rebuild
instructions remain open. Nothing was installed on or transferred to the Green;
no HA, TV or provider API was contacted.

## Remaining release gates

### Original notices shipped in the app (D-190)

The Supervisor-compatible build context now includes a mechanically generated,
committed licence payload: the 89 original public evidence files plus a manifest,
not downloaded source archives or any runtime/user data. Host checks reject
stale copies; new tests cover deterministic byte-preserving generation,
missing/changed/extra/symlinked evidence, preservation of unexpected outputs,
CLI errors and the Docker copy. The image stores it at
`/usr/share/frame-gallery/licenses/`. Actual native ARM validation reads all
89 files as UID/GID 65534 and matches their bytes to the checkout manifest.

Latest native ARM rebuild and complete container checks pass (exit 0):
4,734 non-root tests / five root-only skips and all five separate root checks.
All seven repository-notice/source-data checks previously outside the build
context now run successfully against shipped data, with no licence skips.
Log: `build/phase9/container-license-bundle-final-aarch64-20261003.log`.
Latest full unsandboxed host gates also pass: 4,728 tests / eleven expected
platform skips, Ruff/strict mypy on 230 files, unchanged 100% package and mandated
line/branch coverage. Log: `build/phase9/check-license-bundle-final-20261003.log`.
The longer real-limit ARM measurement against the initial notice-layer rebuild
also passed (exit 0): all 26 prepares, peak VM 765.5 MiB, slowest 1.59 s under
the unchanged 1 GiB limit, 150 inspections without failure (0.62 s total).
Runtime code and all dependencies are unchanged across the later documentation/
test refresh; the latest image only adds documentation data. No Green/TV changes
or container publication.
This distribution step does not close the source/rebuild/applicability gates.

### Local corresponding-source candidate (D-191)

An offline candidate was assembled from all retained source manifests and clean
own project commit `40f3e65aad47464ea64590955446446d84a611a7`. All 172 input archive
SHA256s/byte lengths were checked before assembly and each packed archive was
read back and hash-verified. The project snapshot is `git archive`, with no Git
history or backup branch. The output contains regular inert source archives
and its index; no archive was extracted or executed and no binary toolchain is
redistributed. It contains no HA state, tokens, TV data or user artwork.

Candidate: `build/phase9/source-candidate-40f3e65.tar`, 512,204,800 bytes,
SHA256 `bbe95367e669da9cbd4bb647d0bd28459d93b49fcf166bd1a6aaa52aef061992`.
172 original sources total 507,415,363 bytes, plus the own 4,608,000-byte source
snapshot/index. Result: `build/phase9/source-candidate-result.json`. Mac-only;
approximately 20 GiB free remains. Mechanical first-candidate assembly is now
done; engineering applicability, replacement/rebuild documentation, final release
synchronization and public source availability/retention remain gates.

The user-approved public repository was created in the personal Firefox session:
https://github.com/volkue-tech/frame-gallery-ha . Owner/visibility are exactly
volkue-tech/Public. Its description explicitly labels the beta unreleased.
The user created a repository-scoped fine-grained token, stored it themselves in
macOS Passwords and entered it through a hidden `getpass` prompt in Mac Terminal.
The one-use helper verified `/user` as `volkue-tech`, the exact public target and
empty remote, pushed only `refs/heads/main` and verified the remote SHA as
`39d25dac8a407b050c0fd2eb0bff083c316c8ca4`. Token/authorization headers were held
in process memory only, with no credential saving or printed value. Initial
local format rejection made no network request; no business credentials tried.
The pre-push scan of all 92 main commits found only the exact personal author/
committer identity and no matches for the checked GitHub/API-token, private-key
or business-email patterns. This bounded pattern scan is not proof against all
possible secrets. No state/options/image archives are tracked; the only tracked
PNG files are the own icon and logo. The old local backup branch was not pushed.
The first native hosted validation started automatically at 17:43:10 UTC:
https://github.com/volkue-tech/frame-gallery-ha/actions/runs/37141542920 .
Both jobs succeeded: ARM at 17:58:51 UTC, Intel at 18:02:25 UTC. Native host and
Docker architecture assertions passed (no QEMU/Rosetta), host quality/kernel
gates passed, and both container suites passed with 4,718 non-root tests / six
expected skips plus all five root tests. The 13-case twice-repeated measurement
under real 1 GiB RLIMIT_AS passed on both architectures, fulfilling D-170's native
Intel requirement. The ARM log reports 765.5 MiB peak address space, 2.16 s
slowest prepare and 150 inspections without failure; exact Intel peak/time
values are not transcribed. The logged synthetic Supervisor-token presence
check prints a boolean only. Docker lacks the own AppArmor attachment and its
smoke correctly exits 70 without artwork; it does not replace the Green's
enforcement proof. The one ARM annotation is the Node.js 20 deprecation warning,
with the pinned actions forced onto Node.js 24, not an artifact/test failure.
This run precedes D-184's development-inventory correction. Local full gates
after that correction passed with 4,714 tests / 11 skips and unchanged 100%
line/branch coverage (`build/phase9/check-source-notices-20261003.log`). No
container or release published. D-185 records the hosted evidence.

The follow-up main push at `9cd37f8` is verified. Run `37143460336` failed on
both native architectures solely at the notices check: the documentation rewrite
lost the exact tempio Go-version/module-count phrase required by the checker.
Both job logs were inspected: 4,719 non-root passes / six skips, five root passes,
all 26 prepare results and 150 inspections without failure on each architecture.
ARM peak VM 766.5 MiB / slowest 2.15 s; Intel 762.8 MiB / slowest 2.33 s.
D-188 restores the verified metadata, leaving the checker unchanged; a new
repository-notices regression first failed and now passes, including rejection
of mismatched Go version and module count. All 25 inventory tests and both local
retained-image notices checks pass. Hosted validation of the corrected revision
is still required; no images or release are published. Full unsandboxed Mac
gates pass with 4,717 tests / 11 expected skips and 100% line/branch coverage
(`build/phase9/check-tempio-source-native-20261003.log`). The initial sandboxed
run failed two unchanged setgid tests; no test/runtime workaround was added.
The personal main push of the corrected `aaf7016c1afd2a6ca23bdd37354c8713bc6ff192`
is remotely verified. Native run `37145245403` succeeded on both architectures:
ARM job `111267719103` completed at 18:58:37 UTC and Intel job `111267718919`
at 19:01:57 UTC. All host/container/root/notices/memory steps passed. Exact
new hosted suite counts/peak values are not asserted without log inspection.
This verifies `aaf7016`, not later D-189/D-190 changes or release clearance.
Token was held only in the one-use helper process;
no token was saved or logged and the backup branch was not pushed.

1. Validate subsequent release changes; native amd64 kernel/root/memory evidence
   at `39d25da` is now passed, not an outstanding architecture gate.
2. Complete dependency licences, corresponding-source bundle and replacement/
   rebuild instructions; resolve exact licence expressions and retained notices.
3. Repeat hosted validation after the later inventory/release changes (the first
   audited source push and native hosted run are complete).
4. Gated immutable multi-architecture images, one-click repository link, clean
   public Green install, final public slug/card and release limitations/notes.

Phase 9 remains active; no beta release is approved by this report.

## Repeatable source packaging and Alpine original documents (D-192)

The fixed retained Alpine archives supply 111 original licence/notice/patent,
selected source and recipe documents (2,672,323 bytes), read passively and
byte-retained with member/archive hashes. The manifest and two data regressions
cover e2fsprogs/Kerberos NOTICE, libuv subsidiary terms, Unicode, GCC exception,
Mozilla trust-data source, SQLite/tzdata dedications and recipe-only origins.
An original empty Zstd build/LICENSE remains empty and is not a licence grant.
Auxiliary posixtz says LGPL in its source, but an offline check of the existing
native ARM runtime found neither possible executable path; it is not mislabeled
as public-domain installed code. Broader source/build/test terms remain with
their actual scope, not indiscriminately assigned to all binaries.

The source-package assembler is now tracked and typed, with nineteen passing
offline regressions for deterministic read-back integrity, non-overwrite,
dirty/changing checkout, missing/mismatched files, traversal/symlinks, bounds and
unsafe/incomplete/duplicate members. SOURCE_AND_REBUILD describes sources and
library replacement. No upstream build or application behavior was changed.
The committed licence payload contains 201 evidence files; it is regenerated and
checked. Revalidation of this larger payload in the runtime image is pending.

Full native Mac command `bash scripts/check.sh` exited 0: Ruff clean, strict mypy
both host/Linux over 232 files, 4,749 passed / eleven expected platform skips,
unchanged full and mandated 100% line/branch coverage. Log:
`build/phase9/check-source-tool-alpine-notices-20261003.log`. This is local evidence,
not a hosted run, public source upload or legal counsel's clearance.

## Gated publisher preparation and corrected real Linux error path (D-193)

The manual-only publication workflow and release-preflight tool are prepared.
Exact approval commit/source SHA, a matching numbered beta, the public source
asset and fresh native validation of the actual runtime are required. Only the
publishing jobs have registry/OIDC write permissions; fixed own package targets,
non-overwrite/authentication rules, hash-pinned Cosign and exact signature identity
verification are configured. YAML and every embedded shell block parse successfully
with the Mac's existing Psych/bash; no new parser package was installed.
The actual dev0 checkout rejects a nominal beta publication before any network.
No registry request, Cosign execution, image push or hosted publisher run occurred.

First real assembly rejected legitimate Go proxy `!masterminds` escaped names
before creating an archive. The narrow literal basename correction has its own
regression and all 172 retained archives/507,415,363 input bytes hash-check.
The first updated Linux suite had five failing mocked HTTP-error cases: Python
3.14.8 reported implicit response-body cleanup as ResourceWarnings. Authorization
and HEAD error bodies are now explicitly closed; warnings-as-errors and no-retry
remain unchanged, with an additional closure/no-output regression.

Final local commands actually exited 0:

- `bash scripts/check.sh`: Ruff clean, strict host/Linux mypy over 234 files,
  4,778 passed / eleven expected platform skips; full/mandated 100% line+branch.
  Log `build/phase9/check-release-error-close-20261003.log`.
- `bash scripts/container_check.sh aarch64`: 4,784 non-root passes / five
  root-only skips, five root passes; all 201 original notice documents byte-
  verified and readable as UID 65534; init/stop/token/inventory/smoke checks pass.
  Log `build/phase9/container-release-error-close-aarch64-20261003.log`.

The final pass did not repeat decoder memory measurements: decoder/dependencies
are unchanged; D-190's memory evidence remains applicable within its recorded
scope. The actual publisher will require fresh native memory gates before upload.
ENGINEERING_LICENSE_REVIEW records the bounded assessment, including R-04's
unproven historical relicensing, without counsel/ownership/patent guarantees.
SOURCE_AND_REBUILD and RELEASE_PROCESS distinguish source-only distribution from
the final beta/clean-install announcement. Approval variables remain unset;
source/image public availability and clean public installation are not complete.

## Numbered candidate and actual source-assembler proof (D-194)

The clean `a7a99f8` package assembled successfully and the independent release
preflight accepted its entire payload and exact own Git snapshot: 172 original
archives, 518,092,800 bytes, SHA256
`75502e27d7a216e8b8f73f301f713d242f8813e5c105f06dc9fe6058659609e6`.
The own snapshot has 1,079 entries, without Git history or ignored build state.
Result: `build/phase9/source-release-prep-a7a99f8-result.json`.
An actual LABEL-only Docker build succeeded; its six RootFS layers equal the
validated `frame-gallery:dev-aarch64` image exactly. No registry push occurred.

The personal main push is verified at `a7a99f8`; hosted native validation run
`37155043758` was observed in progress. Runtime/project metadata now prepares
`0.1.0b1`, with unchanged dependencies/behavior and experimental installation
metadata. Its matching sources must be newly assembled from the clean numbered
commit. Neither the earlier candidate nor an in-progress CI run clears the
remaining public-source/image/signature/Green-install gates.

Numbered-candidate commands actually exited 0: full `scripts/check.sh` has
4,779 passes / eleven expected platform skips, strict host/Linux mypy 234 files,
100% full/mandated line+branch coverage. Native ARM `container_check.sh aarch64`
has 4,785 non-root passes / five root-only skips and all five root checks;
notice/inventory/init/stop/smoke checks pass. Logs:
`build/phase9/check-beta-b1-20261003.log` and
`build/phase9/container-beta-b1-aarch64-20261003.log`.
The lock's sole change is the virtual own-package version; pinned uv 0.12.19
`lock --offline --check` resolved the unchanged 26 packages successfully.
No new dependency, safety-limit relaxation or live HA/TV mutation occurred.
