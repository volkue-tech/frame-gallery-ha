# Third-party notices (provisional)

**Status: provisional, started in Phase 2; the inventory is authoritative since Phase 6.** This file is not a release notice.

- Project-owned source is now public under `volkue-tech/frame-gallery-ha`. No container image or beta release has been published. Phase 6 built the app image locally, for `aarch64` and `amd64`, from the pinned base image and the hash-pinned wheels; it was not pushed anywhere.
- The runtime inventory below was taken in Phase 6 from the exact two Pillow runtime wheels and from the built image, for both architectures, which hold the same versions (`DECISIONS.md` D-171, accepted at the Phase 6 gate; `frame_gallery/scripts/image_inventory.py`). Entries marked **to verify** still need their licence read from upstream before any release.
- The complete licence texts, and the corresponding source for every copyleft component (D-135), are added before the first release. The qualified licence review (D-135) is a release gate.
- The details and the obligations are recorded in `DECISIONS.md` (*Proposed dependency inventory*).

This is an engineering inventory, not legal advice.

**Local image modification (D-177, 2026-10-03).** The Dockerfile hash-checks the pinned s6-overlay 3.2.3.0 `CMDSIG` script and changes only its interpreter from `/bin/sh` to the base image's `/bin/bash`, to avoid BusyBox's `kill --` warning. The upstream body and signal arguments remain unchanged. This is third-party code, not project-owned Apache-2.0 code. Upstream licence/source verification and preservation of this modification with corresponding source remain mandatory before release.

## Project code

The project-owned source code is licensed under the Apache License 2.0 (D-102, accepted). The root `LICENSE` now contains its full text. Third-party texts are being collected under `LICENSES/`; this is not yet a completed distribution-compliance package.

**Apache-2.0 covers the project-owned code only.** It does not cover the container image as a whole. The image contains third-party components under their own licences, including **GPL-2.0**, **GPL-3.0-or-later**, and **LGPL** components (see *Base image and OS packages*). The runtime is **not** free of GPL components.

## Runtime components

### Pillow 12.3.0

- Source: PyPI, `pillow==12.3.0`, installed unmodified from the hash-pinned binary wheels `pillow-12.3.0-cp314-cp314-musllinux_1_2_aarch64.whl` (SHA-256 `fe3cca2e4e8a592be0f269a1ca4835c25199d9f3ce815c8491048f785b0a0198`) and `pillow-12.3.0-cp314-cp314-musllinux_1_2_x86_64.whl` (SHA-256 `23aceaa007d6172b02c277f0cd359c79492bbb14f7072b4ede9fbcaf20648130`), as `frame_gallery/requirements/image-runtime.txt` names them.
- Licence of Pillow itself: `MIT-CMU` (the `License-Expression` of the installed distribution).
- Used only by the image worker tasks (D-107).

**Components in the Pillow runtime wheels**, verified in Phase 6 in both wheels and in the built image (the two wheels hold the same versions). The wheels' own licence file (`pillow-12.3.0.dist-info/licenses/LICENSE`) carries the texts of most of them.

| Component (where in the wheel) | Version | Licence (SPDX) | Notes |
| --- | --- | --- | --- |
| libavif (`pillow.libs`) | 1.4.2 | `BSD-2-Clause` | Contains, linked statically: dav1d 1.5.3 (`BSD-2-Clause`), aom 3.14.1 (`BSD-2-Clause`; AOMedia's patent licence is checked in the licence review), libyuv (version number 1924, `BSD-3-Clause`), and libsharpyuv |
| Brotli: libbrotlicommon, libbrotlidec | 1.2.0 | `MIT` | |
| FreeType: libfreetype | 2.14.3 | `FTL` | Contains bzip2 1.0.8 (`bzip2-1.0.6`), linked statically. See the acknowledgement below. |
| HarfBuzz: libharfbuzz | 14.2.1 | `MIT-Modern-Variant` | HarfBuzz's "Old MIT" licence, as the wheel's licence file carries it |
| libjpeg-turbo: libjpeg | 3.1.4.1 | `IJG AND BSD-3-Clause AND Zlib` | See the acknowledgement below. The wheel's licence file carries only the IJG text; the zlib licence covers the SIMD extensions, which both wheels contain (upstream's licence file, to confirm in the licence review). |
| Little CMS 2: liblcms2 | 2.19.1 | `MIT` | |
| liblzma (XZ Utils) | 5.8.3 | `0BSD` | The wheel's licence file still carries XZ Utils' older public-domain notice. |
| OpenJPEG: libopenjp2 | 2.5.4 | `BSD-2-Clause` | |
| libpng: libpng16 | 1.6.58 | `libpng-2.0` | |
| libsharpyuv | 0.1.2 | `BSD-3-Clause` | Part of libwebp 1.6.0 |
| libtiff | 4.7.1 | `libtiff` | |
| libwebp, libwebpdemux, libwebpmux | 1.6.0 | `BSD-3-Clause` | |
| libxcb | 1.17.0 | `X11` | |
| libXau | 1.0.12 | `MIT-open-group` | From Alpine's package 1.0.12-r0 |
| libXdmcp | 1.1.5 | `MIT-open-group` | From Alpine's package 1.1.5-r1 |
| libbsd | 0.12.2 | `BSD-3-Clause` (package shorthand, not an exhaustive source-file expression) | From Alpine's package 0.12.2-r0. Full original `LICENSES/libbsd-0.12.2/COPYING` now retained, including ISC/MIT/BSD variants, public-domain and manual-page notices; applicability remains in review (D-187). |
| libmd | 1.1.0 | `BSD-3-Clause AND BSD-2-Clause AND ISC AND Beerware AND LicenseRef-libmd-Public-Domain` (aggregate source description) | From Alpine's package 1.1.0-r0. **"Public Domain" is not an SPDX identifier.** The local LicenseRef denotes exactly the original MD4/MD5/SHA1 statements in the complete `LICENSES/libmd-1.1.0/COPYING`, not a new licence (D-187). |
| libzstd | 1.5.7 | `BSD-3-Clause` | Zstandard is offered as `BSD-3-Clause OR GPL-2.0-only`; the wheel carries the BSD text. |
| raqm (in `_imagingft`) | 0.10.5 | `MIT` | |
| fribidi-shim (in `_imagingft`) | 1.x | `LGPL-2.1-or-later` | **Copyleft.** Pillow's code that loads FriBiDi at run time, if the system has it; the image does not. The LGPL-2.1 text and the corresponding source (the Pillow 12.3.0 sdist) are provided with each release (D-135). |
| Tcl/Tk header code (in `_imagingtk`) | — | `TCL` | |
| pythoncapi_compat (in the extensions) | per the wheel SBOM | `0BSD` | |

**Not in the image**, although an earlier, provisional version of this file listed them: `libimagequant` (`GPL-3.0-or-later`) and FriBiDi (`LGPL-2.1-or-later`), which Pillow's SBOM names only as optional dependencies, and a bundled zlib: Pillow loads the system's zlib, Alpine's `zlib` package below. pybind11 is used only to build Pillow.

**Acknowledgements** (final wording is taken from the shipped licence texts):

- This software is based in part on the work of the Independent JPEG Group.
- Portions of this software are copyright © The FreeType Project (www.freetype.org). All rights reserved.

### urllib3 2.8.0

- Source: PyPI, `urllib3==2.8.0`, the pure-Python wheel `urllib3-2.8.0-py3-none-any.whl` (SHA-256 `0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3`), installed unmodified and hash-pinned (`frame_gallery/requirements/runtime.txt`; in the image, `requirements/image-runtime.txt`). Approved by the user for Phase 3 (2026-09-27).
- Licence: `MIT` (the `License-Expression` of the installed distribution; licence file `LICENSE.txt`, "Copyright (c) 2008-2020 Andrey Petrov and contributors"). Checked in the installed metadata on 2026-09-27.
- No optional extras are installed (`brotli`, `h2`, `socks`, `zstd` are not used).
- Used by `net/transport.py`, the gateway's HTTP transport (D-108, D-131), and, from Phase 5, inside the television worker through `requests`, which `samsungtvws` uses for the TV's REST check (D-161).
- Obligation: the MIT licence text and copyright notice accompany every distribution.

### certifi 2026.7.22

- Source: PyPI, `certifi==2026.7.22`, the pure-Python wheel `certifi-2026.7.22-py3-none-any.whl` (SHA-256 `62f22742b58a1a33014a2b6b706588a8d7e2a88ae7bd1a6ebe8c992928483775`), installed unmodified and hash-pinned. Approved by the user for Phase 3 (2026-09-27).
- Licence: `MPL-2.0` (the legacy `License` field of the installed distribution, which has no `License-Expression`; licence file `LICENSE`). Its licence file states that the package contains a modified version of Mozilla's CA bundle (`ca-bundle.crt`, extracted from Mozilla's `certdata.txt`) under the Mozilla Public License 2.0. Checked in the installed metadata on 2026-09-27.
- Used by `net/transport.py`, as the gateway's explicit CA bundle (§10); `requests` also loads it inside the television worker, where the library turns certificate verification off for the TV (D-161).
- Obligations (MPL-2.0): the files are distributed unmodified; this notice identifies them and their licence; the MPL-2.0 text and a pointer to the source form (the PyPI sdist `certifi-2026.7.22.tar.gz`, SHA-256 `741e2c3b351ddf169a738da9f2c048608ff7f2c5cc02f1ebc6b118bb090d5d55`) accompany every release (D-135).

### samsungtvws 3.0.6

**This image contains `samsungtvws` 3.0.6, which is licensed under the GNU Lesser General Public License version 3 (LGPL-3.0).**

- Source: PyPI, `samsungtvws==3.0.6`, the pure-Python wheel `samsungtvws-3.0.6-py3-none-any.whl` (SHA-256 `6e3a1b23f928b3035570cc976b64b8c2a218b06022a333855fd7cd02dc74891d`), installed unmodified and hash-pinned (`frame_gallery/requirements/runtime.txt`; in the image, `requirements/image-runtime.txt`). Approved by the user for Phase 5 (2026-09-27).
- Licence: `LGPL-3.0` (the `License-Expression` of the installed distribution, a deprecated short form; treated as LGPL-3.0-only). Licence file `LICENSE` (the LGPL-3.0 text). Copyright (C) 2019, 2025 DSR! <xchwarze@gmail.com>; Copyright (C) 2021 Matthew Garrett <mjg59@srcf.ucam.org> (the art module).
- Corresponding source: the sdist `samsungtvws-3.0.6.tar.gz` (SHA-256 `166111d8370443cd2021b74cdfac9495896dfc41e3a87ea023289f24f922bb91`), attached to every release (D-135).
- Used only by the television worker task, as a separate package, through its public API. The library is not modified: at run time the worker only wraps standard-library `socket` functions and `websocket-client`'s `create_connection`, and answers `get_api_version` on its own connection object from its earlier check (D-160, D-162). It can be replaced by another version when the image is built.
- Obligations (D-160): this notice; the LGPL-3.0 and GPL-3.0 texts with every distribution; the corresponding source; replaceability; no terms that restrict modification or reverse engineering to debug such modifications.

### Dependencies of samsungtvws

Installed unmodified from PyPI and hash-pinned (`frame_gallery/requirements/runtime.txt`; in the image, `requirements/image-runtime.txt`); only the core install of `samsungtvws`, no extras. Licences and files were read from the installed distributions on 2026-09-27.

| Package | Version | Licence (SPDX) | Licence files | Obligations |
| --- | --- | --- | --- | --- |
| `websocket-client` | 1.9.2 | `Apache-2.0` | `LICENSE` | Licence text |
| `requests` | 2.34.2 | `Apache-2.0` | `LICENSE`, `NOTICE` | Licence text **and `NOTICE`** |
| `charset-normalizer` | 3.5.1 | `MIT` | `LICENSE` | Licence text |
| `idna` | 3.20 | `BSD-3-Clause` | `LICENSE.md` | Licence text |
| `yarl` | 1.25.1 | `Apache-2.0` | `LICENSE`, `NOTICE` | Licence text **and `NOTICE`** |
| `multidict` | 6.9.1 | `Apache-2.0` | `LICENSE` | Licence text |
| `propcache` | 0.5.4 | `Apache-2.0` | `LICENSE`, `NOTICE` | Licence text **and `NOTICE`** |

`urllib3` and `certifi`, which `requests` also needs, are listed above. `charset-normalizer`, `yarl`, `multidict`, and `propcache` ship native extensions: the image installs their CPython 3.14 `musllinux_1_2` wheels, as `frame_gallery/requirements/image-runtime.txt` names them with their hashes. The Phase 6 inventory read the same versions and licences from the installed distributions in the image (`multidict` gives its licence as "Apache License 2.0").

### Base image and OS packages

- **Base image:** `ghcr.io/home-assistant/base:3.24-2026.08.0@sha256:93ef607824e3f27e868f11b10938283a98bf880ed57bcf8eaa81c6c2d521f6f5` (Alpine Linux 3.24.1), unmodified. The app adds Alpine's `python3` package, pinned to 3.14.8-r0, with what it needs, but without the pip wheel that Python bundles for `ensurepip` (`pip-26.2.1-py3-none-any.whl`), which the app image removes (D-167); the image holds no wheel.
- **Alpine packages**, read from apk's database in the built image, with apk's licence field; the same on both architectures. The last column says whether the base image brings the package or `python3` adds it.

The licence column is apk's own field. It is not always an SPDX expression: "Public-Domain" (in `tzdata`, `xz`, and `xz-libs`) is apk's notation, not an SPDX identifier.

| Package | Version | Licence (apk) | From |
| --- | --- | --- | --- |
| `alpine-baselayout` | 3.7.2-r1 | `GPL-2.0-only` | base |
| `alpine-baselayout-data` | 3.7.2-r1 | `GPL-2.0-only` | base |
| `alpine-keys` | 2.6-r0 | `MIT` | base |
| `alpine-release` | 3.24.1-r0 | `MIT` | base |
| `apk-tools` | 3.0.6-r0 | `GPL-2.0-only` | base |
| `bash` | 5.3.9-r1 | `GPL-3.0-or-later` | base |
| `bind-libs` | 9.20.26-r0 | `MPL-2.0` | base |
| `bind-tools` | 9.20.26-r0 | `MPL-2.0` | base |
| `brotli-libs` | 1.2.0-r1 | `MIT` | base |
| `busybox` | 1.37.0-r31 | `GPL-2.0-only` | base |
| `busybox-binsh` | 1.37.0-r31 | `GPL-2.0-only` | base |
| `c-ares` | 1.34.8-r0 | `MIT` | base |
| `ca-certificates` | 20260611-r0 | `MPL-2.0 AND MIT` | base |
| `ca-certificates-bundle` | 20260611-r0 | `MPL-2.0 AND MIT` | base |
| `curl` | 8.21.0-r0 | `curl` | base |
| `fstrm` | 0.6.1-r4 | `MIT` | base |
| `gdbm` | 1.26-r0 | `GPL-3.0-or-later` | `python3` |
| `jq` | 1.8.1-r0 | `MIT` | base |
| `json-c` | 0.18-r1 | `MIT` | base |
| `keyutils-libs` | 1.6.3-r4 | `GPL-2.0-or-later AND LGPL-2.0-or-later` | base |
| `krb5-conf` | 1.0-r2 | `MIT` | base |
| `krb5-libs` | 1.22.2-r1 | `MIT` | base |
| `libapk` | 3.0.6-r0 | `GPL-2.0-only` | base |
| `libbz2` | 1.0.8-r6 | `bzip2-1.0.6` | `python3` |
| `libcom_err` | 1.47.4-r0 | `GPL-2.0-or-later AND LGPL-2.0-or-later AND BSD-3-Clause AND MIT` | base |
| `libcrypto3` | 3.5.7-r0 | `Apache-2.0` | base |
| `libcurl` | 8.21.0-r0 | `curl` | base |
| `libexpat` | 2.8.5-r0 | `MIT` | `python3` |
| `libffi` | 3.5.2-r1 | `MIT` | `python3` |
| `libgcc` | 15.2.0-r5 | `GPL-2.0-or-later AND LGPL-2.1-or-later` | base |
| `libidn2` | 2.3.8-r0 | `GPL-2.0-or-later OR LGPL-3.0-or-later` | base |
| `libncursesw` | 6.6_p20260516-r0 | `X11` | base |
| `libpanelw` | 6.6_p20260516-r0 | `X11` | `python3` |
| `libpsl` | 0.21.5-r3 | `MIT` | base |
| `libssl3` | 3.5.7-r0 | `Apache-2.0` | base |
| `libstdc++` | 15.2.0-r5 | `GPL-2.0-or-later AND LGPL-2.1-or-later` | base |
| `libunistring` | 1.4.2-r0 | `GPL-2.0-or-later OR LGPL-3.0-or-later` | base |
| `libuv` | 1.52.1-r0 | `MIT` | base |
| `libverto` | 0.3.2-r2 | `MIT` | base |
| `libxml2` | 2.13.9-r2 | `MIT` | base |
| `mpdecimal` | 4.0.1-r0 | `BSD-2-Clause` | `python3` |
| `musl` | 1.2.6-r2 | `MIT` | base |
| `musl-utils` | 1.2.6-r2 | `MIT AND BSD-2-Clause AND GPL-2.0-or-later` | base |
| `ncurses-terminfo-base` | 6.6_p20260516-r0 | `X11` | base |
| `nghttp2-libs` | 1.69.0-r0 | `MIT` | base |
| `oniguruma` | 6.9.10-r0 | `BSD-2-Clause` | base |
| `protobuf-c` | 1.5.2-r2 | `BSD-2-Clause` | base |
| `pyc` | 3.14.8-r0 | `PSF-2.0` | `python3` |
| `python3` | 3.14.8-r0 | `PSF-2.0` | `python3` |
| `python3-pyc` | 3.14.8-r0 | `PSF-2.0` | `python3` |
| `python3-pycache-pyc0` | 3.14.8-r0 | `PSF-2.0` | `python3` |
| `readline` | 8.3.3-r1 | `GPL-3.0-or-later` | base |
| `scanelf` | 1.3.9-r1 | `GPL-2.0-only` | base |
| `sqlite-libs` | 3.53.4-r0 | `blessing` | `python3` |
| `ssl_client` | 1.37.0-r31 | `GPL-2.0-only` | base |
| `tzdata` | 2026c-r0 | `Public-Domain` | base |
| `userspace-rcu` | 0.15.3-r0 | `LGPL-2.1-or-later` | base |
| `xz` | 5.8.3-r0 | `GPL-2.0-or-later AND 0BSD AND Public-Domain AND LGPL-2.1-or-later` | base |
| `xz-libs` | 5.8.3-r0 | `GPL-2.0-or-later AND 0BSD AND Public-Domain AND LGPL-2.1-or-later` | base |
| `zlib` | 1.3.2-r0 | `Zlib` | base |
| `zstd-libs` | 1.5.7-r2 | `BSD-3-Clause OR GPL-2.0-or-later` | base |

- **Outside apk**, installed by the base image; the image carries no licence text or package metadata for them:

| Component | Version | Licence | Notes |
| --- | --- | --- | --- |
| s6-overlay | 3.2.3.0 | `ISC` | [Exact release COPYING](https://github.com/just-containers/s6-overlay/blob/v3.2.3.0/COPYING), copied to `LICENSES/`. Exact source COPYING texts for execline 2.9.9.0, s6 2.15.0.0, s6-linux-init 1.2.0.1, s6-linux-utils 2.6.4.1, s6-overlay-helpers 0.1.2.2, s6-portable-utils 2.3.1.2, and s6-rc 0.6.1.0 are verified as ISC and retained; static dependencies and source/build completeness remain open. |
| s6-dns | 2.4.1.2 | `ISC` | Present under `/package/web`; original source COPYING retained in `LICENSES/s6-dns-2.4.1.2/`. Previously omitted by the admin-only inventory (D-184). |
| s6-networking | 2.8.0.0 | `ISC` | Present under `/package/net`; original source COPYING retained in `LICENSES/s6-networking-2.8.0.0/`. The release build links BearSSL; its exact source/licence and static-toolchain completeness remain open (D-184). |
| skalibs | 2.15.0.0 | `ISC` | Present under `/package/prog` and used by S6 binaries; original source COPYING retained in `LICENSES/skalibs-2.15.0.0/` (D-184). |
| s6-overlay-helpers | 0.1.2.2 | `ISC` | Exact versioned source and original COPYING retained in `LICENSES/s6-overlay-helpers-0.1.2.2/`. |
| tempio | 2026.07.0 | `Apache-2.0` | Built with Go 1.26.5 and 11 Go modules (listed below). [Exact release LICENSE](https://github.com/home-assistant/tempio/blob/2026.07.0/LICENSE), retained from binary VCS revision `56918dfb7db5fec2161b2c5b37ee42f49176d34b`; source/build and subsidiary notices remain to complete; not used by the app |
| bashio | 0.17.5 | `MIT` | [Exact release LICENSE.md](https://github.com/hassio-addons/bashio/blob/v0.17.5/LICENSE.md), copied to `LICENSES/`; version from the pinned base recipe, not an embedded version marker; not used by the app |
| jemalloc | 5.3.1 | `BSD-2-Clause` | [Exact release COPYING](https://github.com/jemalloc/jemalloc/blob/5.3.1/COPYING), copied to `LICENSES/`. Previously omitted from the inventory; the aarch64 app image contains `/usr/local/lib/libjemalloc.so.2` and its two helper scripts. Exact binary/rebuild and amd64 verification remain pending. |

Phase 9 rechecked the official base recipe at [commit 6a3ff4c](https://github.com/home-assistant/docker-base/blob/6a3ff4c10f6ed8564a092c33051024a1b1042ee2/alpine/Dockerfile), the `2026.08.0` tag. It sets bashio 0.17.5 and builds jemalloc 5.3.1. The immutable image digest remains the binary authority; source-version matches and all accompanying texts/sources must be verified before release. The jemalloc helper reports `0.0.0-0-g000000missing_version_try_git_fetch_tags`, not a verified binary version. The automatic inventory now detects the jemalloc library and rejects missing notices; this presence check is not proof of its version or corresponding-source completeness.

On 2026-10-03 the exact upstream sources of execline, s6, s6-linux-init,
s6-linux-utils, s6-portable-utils and s6-rc (versions above) were retained.
Their original COPYING files are all ISC and are copied under `LICENSES/`,
with copyright Laurent Bercot (2011–2026, or 2015–2026 for linux-init/rc).
`LICENSES/skarnet-source-manifest.json` records HTTPS URLs and calculated hashes;
these hashes are not publisher signatures or binary-source equivalence proof.
s6-overlay-helpers COPYING has since been verified as ISC; its source is now retained.
Build dependencies and static library/toolchain completeness still
require verification. This supersedes only the corresponding pending licence
texts in the table, not the complete source/rebuild requirement.

All eleven installed Python packages' original primary licence files and the
requests/propcache/yarl NOTICE files are now retained under `LICENSES/` from exact
PyPI sdists. `LICENSES/python-source-manifest.json` records their source URLs and
PyPI-verified hashes; archives remain local pending a complete release bundle.
This does not cover the separate native libraries bundled in Pillow's wheels.

The additional exact docker-base, bashio, tempio, jemalloc and s6-overlay source
archives, plus helpers/skalibs/dns/networking, are retained locally;
`LICENSES/base-source-manifest.json` records their URLs and calculated SHA256s.
These are calculated download hashes, not publisher signatures. The tempio and
docker-base Apache texts and the four extra ISC COPYING files are preserved in
`LICENSES/`. The original six skarnet archives remain in their separate manifest.
The corrected native ARM image inventory finds eleven versioned S6 packages,
not just eight admin packages. Exact BearSSL, static musl/toolchain, Go toolchain,
Alpine recipes/patches and Pillow-native sources remain part of the open D-135
release gate; these downloads do not prove binary/source or rebuild equivalence.

### Go modules linked into tempio

The observed tempio binary lists the following eleven dependencies. Their exact
source ZIPs from the official Go module proxy were checked with the documented
directory-hash algorithm against `go.sum` in the exact tempio source revision.
All original primary licence files are retained under `LICENSES/go/`.
`LICENSES/go-source-manifest.json` records module versions, SHA256/archive URLs
and verified `h1` hashes, distinguishing linked modules from ten additional
test/build-source modules in upstream `go.sum`. This is not yet a Go-toolchain
or subsidiary-file licensing/rebuild completeness finding.

| Module | Version | Primary licence | Original text |
| --- | --- | --- | --- |
| dario.cat/mergo | v1.0.1 | `BSD-3-Clause` | LICENSE |
| github.com/Masterminds/goutils | v1.1.1 | `Apache-2.0` | LICENSE.txt |
| github.com/Masterminds/semver/v3 | v3.3.0 | `MIT` | LICENSE.txt |
| github.com/Masterminds/sprig/v3 | v3.3.0 | `MIT` | LICENSE.txt |
| github.com/google/uuid | v1.6.0 | `BSD-3-Clause` | LICENSE |
| github.com/huandu/xstrings | v1.5.0 | `MIT` | LICENSE |
| github.com/mitchellh/copystructure | v1.2.0 | `MIT` | LICENSE |
| github.com/mitchellh/reflectwalk | v1.0.2 | `MIT` | LICENSE |
| github.com/shopspring/decimal | v1.4.0 | `MIT` | LICENSE, including Oguz Bilgic attribution |
| github.com/spf13/cast | v1.7.0 | `MIT` | LICENSE (original has no final newline) |
| golang.org/x/crypto | v0.31.0 | `BSD-3-Clause` | LICENSE |

Primary obligations: retain the full texts and copyright notices, the BSD
non-endorsement clauses and any applicable Apache NOTICE/subsidiary attributions.
The original eleven primary files are byte-identical to their checked archives;
this does not assert that these primary files exhaust every source-file notice.
Algorithm/proxy reference: https://go.dev/ref/mod#authenticating .

### Further retained source and notice evidence (D-186/D-187)

All 45 exact installed aports recipe directories and patches are retained:
197 local files and all 58 upstream files verify against recipe SHA512 values.
`LICENSES/alpine-source-manifest.json` identifies the 61 installed packages and
archive hashes; both architecture databases have identical build-commit tuples.
This is not a completed file-level licensing review or binary-reproducibility
result. GCC 15.2.0 libgcc/libstdc++ source headers state GPL-3.0-or-later with
GCC-exception-3.1; apk's broad field above is quoted metadata, not a complete
file-level expression. Original COPYING.RUNTIME is in `LICENSES/gcc-15.2.0/`.

Exact BearSSL source and MIT text (copyright Thomas Pornin), identified static
musl source/full COPYRIGHT, and Go 1.26.5's official SHA256-verified source and
original BSD-3-Clause LICENSE/PATENTS are retained. See
`LICENSES/static-source-manifest.json` and the corresponding versioned directories
under `LICENSES/`. Both documented S6 build toolchains report libc version
`1.2.6-git-11-g5122f9f3`, resolved to full official Git commit
`5122f9f3c99fee366167c5de98b31546312921ab`; their binaries were never executed.
This identifies documented build inputs, not cryptographic linkage proof for
installed S6 binaries. It supersedes only earlier statements that these sources
were not yet retained, not the still-open source/build applicability gate.

libmd's descriptive LicenseRef points to Colin Plumb/Todd C. Miller's original
MD4/MD5 and Steve Reid's SHA1 dedication statements in the unabridged COPYING.
No worldwide legal determination or relicensing is asserted. libbsd's complete
COPYING also preserves source/manual terms not captured by the package shorthand.
Native-Pillow source completeness, subsidiary attributions, distributed licence
materials, replacement/rebuild instructions and final source assembly remain
open; none of these downloads clears D-135.

## Development tools (not distributed)

These tools are used only to develop and test the project. They are not part of any distributed image. Versions and licences below were read from the installed distributions' metadata in the project environment (Phase 2).

| Package | Version | Licence (SPDX, from the installed metadata) |
| --- | --- | --- |
| `uv` | 0.12.19 | `MIT OR Apache-2.0` (PyPI metadata; wheel SHA-256 verified against PyPI) |
| `pytest` | 9.1.1 | `MIT` |
| `iniconfig` | 2.3.0 | `MIT` |
| `packaging` | 26.3 | `Apache-2.0 OR BSD-2-Clause` |
| `pluggy` | 1.6.0 | `MIT` |
| `Pygments` | 2.21.0 | `BSD-2-Clause` |
| `pytest-cov` | 7.1.0 | `MIT` |
| `coverage` | 7.16.1 | `Apache-2.0` (ships a `NOTICE.txt`) |
| `ruff` | 0.16.9 | `MIT` |
| `mypy` | 2.3.1 | `MIT` (bundles typeshed, which carries its own `LICENSE`) |
| `typing-extensions` | 4.16.0 | `PSF-2.0` |
| `mypy-extensions` | 1.1.0 | `MIT` |
| `pathspec` | 1.1.1 | `MPL-2.0` (licence classifier; no `License-Expression` field) |
| `librt` | 0.15.0 | `MIT` |
| `ast-serialize` | 0.11.2 | `MIT` |

Development-only CI actions are pinned by full commit, not shipped in the app:
`actions/checkout` v4 (`11d5960a326750d5838078e36cf38b85af677262`),
`actions/setup-python` v5 (`a26af69be951a213d495a4c3e4e4022e16d87065`), and
`actions/upload-artifact` v4 (`ea165f8d65b6e75b540449e92b4886f43607fa02`).
Their exact upstream LICENSE files are MIT, copyright GitHub, Inc. and
contributors; source links and verification are recorded in D-181.

The container is built on the development host with Docker Desktop 4.91.0 (Buildx 0.37.0, BuildKit 0.33.0); none of these tools is part of the image.

The local development environment installs the Pillow wheel for macOS `arm64`. That wheel bundles a different set of libraries from the Linux runtime wheels. Its contents say nothing about the runtime image, and they are not used for this inventory.
