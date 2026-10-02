# Third-party notices (provisional)

**Status: provisional, started in Phase 2; the inventory is authoritative since Phase 6.** This file is not a release notice.

- Nothing has been published. Phase 6 built the app image locally, for `aarch64` and `amd64`, from the pinned base image and the hash-pinned wheels; it was not pushed anywhere.
- The runtime inventory below was taken in Phase 6 from the exact two Pillow runtime wheels and from the built image, for both architectures, which hold the same versions (`DECISIONS.md` D-171, proposed for the Phase 6 gate; `frame_gallery/scripts/image_inventory.py`). Entries marked **to verify** still need their licence read from upstream before any release.
- The complete licence texts, and the corresponding source for every copyleft component (D-135), are added before the first release. The qualified licence review (D-135) is a release gate.
- The details and the obligations are recorded in `DECISIONS.md` (*Proposed dependency inventory*).

This is an engineering inventory, not legal advice.

## Project code

The project-owned source code is licensed under the Apache License 2.0 (D-102, accepted). The `LICENSE` file is added when publication is prepared (Phase 9).

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
| libbsd | 0.12.2 | `BSD-3-Clause` | From Alpine's package 0.12.2-r0; its licence as the official Alpine package directory gives it (checked by Codex at the Phase 6 gate, reported on 2026-10-03). The wheel carries no licence text for it; the release adds it. |
| libmd | 1.1.0 | `BSD-3-Clause AND BSD-2-Clause AND ISC AND Beerware` and "Public Domain" | From Alpine's package 1.1.0-r0, whose licence field in the official Alpine package directory reads "BSD-3-Clause AND BSD-2-Clause AND ISC AND Beerware AND Public Domain" (checked by Codex at the Phase 6 gate, reported on 2026-10-03). **"Public Domain" is not an SPDX identifier**; the licence review settles how that part is expressed. The wheel carries no licence text for it; the release adds the texts. |
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
| s6-overlay | 3.2.3.0 | **to verify** | The init system, with execline 2.9.9.0, s6 2.15.0.0, s6-linux-init 1.2.0.1, s6-linux-utils 2.6.4.1, s6-overlay-helpers 0.1.2.2, s6-portable-utils 2.3.1.2, and s6-rc 0.6.1.0 |
| tempio | 2026.07.0 | **to verify** | A Home Assistant template tool, built with Go 1.26.5 and 11 Go modules (recorded in the image's inventory); not used by the app |
| bashio | not recorded in the image | **to verify** | A Home Assistant shell library; not used by the app |

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

The container is built on the development host with Docker Desktop 4.91.0 (Buildx 0.37.0, BuildKit 0.33.0); none of these tools is part of the image.

The local development environment installs the Pillow wheel for macOS `arm64`. That wheel bundles a different set of libraries from the Linux runtime wheels. Its contents say nothing about the runtime image, and they are not used for this inventory.
