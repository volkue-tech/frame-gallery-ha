# Engineering licence assessment

Scope: the exact pinned runtime described in THIRD_PARTY_NOTICES and the retained
source manifests; personal public image distribution, not sale of HA/TV hardware.
This is Codex's **engineering assessment requested by the user**, not independent
legal counsel, a title/ownership warranty, patent clearance or an exemption from
any component's terms. Final distribution evidence is recorded in PHASE9_REPORT.

## Findings and distribution controls

| Area | Evidence/assessment | Required distribution control |
| --- | --- | --- |
| Own implementation | Own source/specifications, personal-only main history; no predecessor source used | Apache-2.0 only for own code; preserve root LICENSE/NOTICE; no blanket image-licence label |
| samsungtvws 3.0.6 | Exact PyPI wheel/sdist hashes and current LGPL-3.0 text/source headers (D-160); separate unmodified Python package | LGPL-3.0/GPL-3.0 texts, original copyrights, exact source, documented replacement; no reverse-engineering restriction |
| Pillow/shim | Exact two runtime wheels, inventory and supplier release/build inputs; shim is LGPL-2.1-or-later, optional imagequant/FriBiDi absent | Original Pillow/native texts and patents, full source/build inputs, shim rebuilding/replacement instructions |
| GPL OS/base programs | Exact 61 package/version/origin/build tuples; 45 recipes/local patches and 58 hash-checked upstream files | Supply matching source/recipes/patches and licence texts for shipped copyleft parts; preserve notices; do not call the image GPL-free |
| LGPL OS libraries | Package-specific terms, not apk's aggregate shorthand alone; original sources available | Source/headers/terms retained, shared-library replacement through rebuilt image; original version/changes identified |
| MPL certificates/BIND | Original MPL source/licences, exact certifi sdist and Alpine recipe/source trust data | Preserve covered-file notices and source availability; no relabeling of covered files as own Apache code |
| S6/base tools outside apk | Exact versions/revisions/build scripts; ISC/MIT/Apache/BSD original texts; static musl/BearSSL and Go/module sources | Retain their notices and corresponding build inputs, including the one modified CMDSIG interpreter line |
| Permissive native components | Original full libbsd/libmd, FreeType, JPEG, TIFF, Unicode and other primary/subsidiary texts | Preserve originals, acknowledgements and scope; no endorsement claim or invented copyright |
| Patent grants | Original AOM, libyuv, libwebp and Go patent texts | Preserve conditions/termination clauses; do not advertise unrestricted patent clearance |
| GCC runtime | Original GCC 15.2 source/headers, exception 3.1 and Alpine recipes | Preserve actual exception/terms; no blanket assertion that all compiler output is exempt |

The image aggregates separately installed OS programs/libraries and the own
Python application. It does not incorporate predecessor code under a new
licence. GPL components are **not** made Apache-2.0 by the repository's root
licence. Keep their sources/terms even where the app does not invoke them.

No new contradictory licence declaration was found in the pinned distributions
inspected for this assessment. This is not proof that all upstream contributors
authorized every historical change. In particular **R-04 remains a provenance
risk**: older samsungtvws versions had inconsistent declarations; current 3.0.6
headers/text uniformly say LGPL-3.0 but do not supply a historical relicensing
statement. The recommendation relies on the current supplier's express licence,
as accepted in D-160, not an assertion that its history has been legally cleared.
Do not substitute an old MIT-metadata version or remove these notices to avoid
copyleft. Obtain specialist advice if a concrete rights conflict arises.

## Scope-sensitive details

- libbsd's five-condition Peter Wemm text governs `man/setproctitle.3bsd`, not
  every library function. The supplied source archive retains that file and its
  complete notice; full COPYING also retains the FreeBSD notation. File-specific
  MIT/ISC/BSD/public-domain/Beerware terms are not collapsed to the apk shorthand.
- `LicenseRef-libmd-Public-Domain` names the original MD4/MD5/SHA1 statements,
  not a newly granted licence or an SPDX "Public Domain" identifier.
- The tzdata original dedication explicitly excludes named BSD-derived files.
  SQLite's original LICENSE distinguishes public-domain library code from its
  non-public-domain build tooling. Both texts are preserved with their scope.
- posixtz build source is LGPL despite the data package's Public-Domain field.
  Its executables were absent in the checked ARM runtime. The broader source
  archive and header are supplied anyway; it is not mislabeled as public-domain.
- e2fsprogs' NOTICE distinguishes MIT-style lib/et (libcom_err) from GPL/LGPL
  filesystem tools. The full source retains each relevant header; the complete
  NOTICE is included rather than claiming apk's mixed expression applies equally
  to every installed subpackage. Kerberos and libuv subsidiary notices are retained.
- The supplied compiler/build sources may contain licences for build tools,
  test assets or manuals that are not in the runtime. Their original terms remain
  in the source package; merely retaining them does not identify them as shipped
  runtime code. Binary cross-compilers are not redistributed.

## Source and modification evidence

The original Python/Alpine/native/base/Go sources and supplier recipes are retained
and hashed. The tracked source assembler includes these and the exact clean own
commit, without Git history, credentials, HA state or user artwork. Each source
archive must actually accompany, or be publicly obtainable alongside, the matching
image. An upstream URL, an unuploaded local candidate or a draft/private release
alone does not complete this control. Keep availability for the documented period.

SOURCE_AND_REBUILD explains Python-library and native-shim replacement, supplier
build inputs, the CMDSIG modification and developer installation. The app has no
project vendor-key activation or runtime library-signature lock; the public source
and profiles can be modified and built without an owner-only key. Worker safety/API
checks are not a promise that incompatible modifications will work unchanged.
Ordinary users still install through Supervisor without SSH/config edits.

No bit-identical rebuild of all supplier binaries is claimed. Calculated hashes,
matching source versions, source packaging and a reproducibility result are
different facts. Patent/ownership guarantees are not inferred from any of them.

## Assessment outcome

The exact pinned licences permit an engineering route to distribution with the
controls above. **The image-release gate is still conditional** on matching
public source/notices availability, verified final image bytes/signatures and the
other technical gates. The workflow requires an explicit reviewed commit/source
hash and rejects development versions. Its first numbered image publication
passed source preflight and native tests; public sources and both signed image
digests were subsequently checked independently without authentication (D-196).
The separate clean public Green installation and two live deliveries subsequently
passed (D-198). Neither distribution nor installation evidence is an independent
legal opinion; final corrected CI and the beta announcement remain pending.

This document records the applicability/risk assessment and a practical compliance
plan. It does not declare an unpublished source bundle publicly available, mark
the overall Phase 9 complete, or represent a qualified lawyer's approval.
