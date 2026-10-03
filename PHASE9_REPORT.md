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

## Remaining release gates

The user-approved empty public repository was created and verified in the
personal Firefox session: https://github.com/volkue-tech/frame-gallery-ha .
Owner/visibility are exactly volkue-tech/Public, no initialization files or
commits. Its description explicitly labels the beta unreleased. No code was
pushed, hosted CI run or container/release published. Git push needs a separate,
personal, repository-scoped credential; no business credentials were tried.

1. Native amd64 kernel/root/memory evidence.
2. Complete dependency licences, corresponding-source bundle and replacement/
   rebuild instructions; resolve exact licence expressions and retained notices.
3. Personal Git push access, audited source push and actual hosted test execution.
4. Gated immutable multi-architecture images, one-click repository link, clean
   public Green install, final public slug/card and release limitations/notes.

Phase 9 remains active; no beta release is approved by this report.
