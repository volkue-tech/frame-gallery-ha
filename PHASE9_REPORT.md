# Phase 9 progress report

Date: 2026-10-03. **In progress, not a release approval.**

Authorized scope: Frame Gallery hardening, engineering licence audit, publication
preparation and the separate Green test app; final personal repository name
`volkue-tech/frame-gallery-ha`. No predecessor source or business identity used.

## Enforced Green worker probes

Observed via the already authorized Firefox Terminal & SSH path. The own test
app advanced from `0.1.0.dev1` to `0.1.0.dev5`; protection stayed on, no host
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
This proves the listed permissions, not normal artwork delivery or an isolated
unprivileged parent. The parent remains root with existing responsibilities.

**Live handoff:** the test source currently still uses temporary
`frame_gallery.phase9_diagnostic`, not the regular entry point. A supplementary
parent-output-read probe is prepared but not transferred: the Mac locked again
before the transfer. Do not infer that worker read permission proves parent read
permission. Next: check that permission, restore the normal CMD, retain/move the
two temporary diagnostic modules out of the app source, rebuild and run an
ordinary card-started delivery/preview/loading/cleanup check. Preserve all options
and confirmed records. Saved pre-Phase-9 source:
`/share/frame-gallery-dev-before-phase9-v1`; retained app-only backup unchanged.
No existing app/dashboard or `configuration.yaml` changed.

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

1. Parent-output read, restored regular Green app and normal delivery regression.
2. Native amd64 kernel/root/memory evidence.
3. Complete dependency licences, corresponding-source bundle and replacement/
   rebuild instructions; resolve exact licence expressions and retained notices.
4. Personal GitHub access and repository creation; no remote or public writes yet.
5. Gated immutable multi-architecture images, one-click repository link, clean
   public Green install, final public slug/card and release limitations/notes.

Phase 9 remains active; no beta release is approved by this report.
