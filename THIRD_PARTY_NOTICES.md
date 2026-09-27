# Third-party notices (provisional)

**Status: provisional, started in Phase 2.** This file is not a release notice.

- Nothing has been packaged or published. No container image exists yet.
- The runtime inventory below is **known but not yet authoritative**. The authoritative inspection runs in Phase 6 against the exact two runtime wheels (`aarch64` and `x86_64` `musllinux_1_2`), once the container's Python version is fixed (D-130 check (a)). Full verification is mandatory before packaging or publication.
- The complete licence texts, and the corresponding source for every copyleft component (D-135), are added before the first release. The qualified licence review (D-135, R-25) is a release gate.
- The details and the obligations are recorded in `DECISIONS.md` (*Proposed dependency inventory*).

This is an engineering inventory, not legal advice.

## Project code

The project-owned source code is licensed under the Apache License 2.0 (D-102, accepted). The `LICENSE` file is added when publication is prepared (Phase 9).

**Apache-2.0 covers the project-owned code only.** It does not cover the distributed container image as a whole. The image will contain third-party components under their own licences, including **GPL-3.0-or-later** and **LGPL** components. The runtime is **not** free of GPL components.

## Runtime components

### Pillow 12.3.0

- Source: PyPI, `pillow==12.3.0`, installed unmodified from hash-pinned binary wheels (`frame_gallery/requirements/runtime.txt`).
- Licence of Pillow itself: `MIT-CMU` (the `License-Expression` of the installed 12.3.0 distribution, checked in Phase 2).
- Used only by the image worker tasks (D-107).

**Libraries bundled in the Pillow runtime wheels.** Observed by Codex in the official Pillow 12.3.0 CPython 3.14 `musllinux_1_2` wheels for `aarch64` and `x86_64` (provisional, see above).

| Component | Version | Licence (SPDX) | Notes |
| --- | --- | --- | --- |
| libimagequant | 4.4.1 | `GPL-3.0-or-later` | **Copyleft.** The GPL-3.0 text and the corresponding source for this exact version are provided with each release (D-135). |
| FriBiDi | 1.0.16 | `LGPL-2.1-or-later` | **Copyleft.** The LGPL-2.1 text and the corresponding source are provided with each release (D-135). Shipped unmodified as a separately replaceable shared library. |
| fribidi-shim | 1.x | `LGPL-2.1-or-later` | As FriBiDi. |
| raqm | 0.10.5 | `MIT` | |
| FreeType | 2.14.3 | `FTL` | See the acknowledgement below. |
| HarfBuzz | 14.2.1 | `MIT` | |
| libavif | 1.4.2 | `BSD-2-Clause` | |
| libjpeg / libjpeg-turbo | 3.1.4.1 | `IJG AND BSD-3-Clause` | See the acknowledgement below. |
| libtiff | 4.7.1 | `libtiff` | |
| libwebp | 1.6.0 | `BSD-3-Clause` | |
| libxcb | 1.17.0 | `X11` | |
| Little CMS 2 | 2.19.1 | `MIT` | |
| OpenJPEG | 2.5.4 | `BSD-2-Clause` | |
| pybind11 | per the wheel SBOM | `BSD-3-Clause` | |
| pythoncapi_compat | per the wheel SBOM | `0BSD` | |
| zlib | 2.3.3 | `Zlib` | |

**Pending Phase 6 verification.** The wheels' `pillow.libs/` directory also contains libXau, libXdmcp, Brotli, libbsd, liblzma, libmd, libpng, libsharpyuv, and libzstd. Their exact versions and SPDX identifiers are taken from the wheel's licence and SBOM material in the Phase 6 inspection, and this file then lists them. (Gate adjustment approved by Codex at the final approval of Phase 1.)

**Acknowledgements** (final wording is taken from the shipped licence texts):

- This software is based in part on the work of the Independent JPEG Group.
- Portions of this software are copyright © The FreeType Project (www.freetype.org). All rights reserved.

### urllib3 2.8.0

- Source: PyPI, `urllib3==2.8.0`, the pure-Python wheel `urllib3-2.8.0-py3-none-any.whl` (SHA-256 `0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3`), installed unmodified and hash-pinned (`frame_gallery/requirements/runtime.txt`). Approved by the user for Phase 3 (2026-09-27).
- Licence: `MIT` (the `License-Expression` of the installed distribution; licence file `LICENSE.txt`, "Copyright (c) 2008-2020 Andrey Petrov and contributors"). Checked in the installed metadata on 2026-09-27.
- No optional extras are installed (`brotli`, `h2`, `socks`, `zstd` are not used).
- Used only by `net/transport.py`, the gateway's HTTP transport (D-108, D-131).
- Obligation: the MIT licence text and copyright notice accompany every distribution.

### certifi 2026.7.22

- Source: PyPI, `certifi==2026.7.22`, the pure-Python wheel `certifi-2026.7.22-py3-none-any.whl` (SHA-256 `62f22742b58a1a33014a2b6b706588a8d7e2a88ae7bd1a6ebe8c992928483775`), installed unmodified and hash-pinned. Approved by the user for Phase 3 (2026-09-27).
- Licence: `MPL-2.0` (the legacy `License` field of the installed distribution, which has no `License-Expression`; licence file `LICENSE`). Its licence file states that the package contains a modified version of Mozilla's CA bundle (`ca-bundle.crt`, extracted from Mozilla's `certdata.txt`) under the Mozilla Public License 2.0. Checked in the installed metadata on 2026-09-27.
- Used only by `net/transport.py`, as the gateway's explicit CA bundle (§10).
- Obligations (MPL-2.0): the files are distributed unmodified; this notice identifies them and their licence; the MPL-2.0 text and a pointer to the source form (the PyPI sdist `certifi-2026.7.22.tar.gz`, SHA-256 `741e2c3b351ddf169a738da9f2c048608ff7f2c5cc02f1ebc6b118bb090d5d55`) accompany every release (D-135).

### samsungtvws 3.0.6

**This image contains `samsungtvws` 3.0.6, which is licensed under the GNU Lesser General Public License version 3 (LGPL-3.0).**

- Source: PyPI, `samsungtvws==3.0.6`, the pure-Python wheel `samsungtvws-3.0.6-py3-none-any.whl` (SHA-256 `6e3a1b23f928b3035570cc976b64b8c2a218b06022a333855fd7cd02dc74891d`), installed unmodified and hash-pinned (`frame_gallery/requirements/runtime.txt`). Approved by the user for Phase 5 (2026-09-27).
- Licence: `LGPL-3.0` (the `License-Expression` of the installed distribution, a deprecated short form; treated as LGPL-3.0-only). Licence file `LICENSE` (the LGPL-3.0 text). Copyright (C) 2019, 2025 DSR! <xchwarze@gmail.com>; Copyright (C) 2021 Matthew Garrett <mjg59@srcf.ucam.org> (the art module).
- Corresponding source: the sdist `samsungtvws-3.0.6.tar.gz` (SHA-256 `166111d8370443cd2021b74cdfac9495896dfc41e3a87ea023289f24f922bb91`), attached to every release (D-135).
- Used only by the television worker task, as a separate package, through its public API. The library is not modified. It can be replaced by another version when the image is built.
- Obligations (D-160): this notice; the LGPL-3.0 and GPL-3.0 texts with every distribution; the corresponding source; replaceability; no terms that restrict modification or reverse engineering to debug such modifications.

### Dependencies of samsungtvws

Installed unmodified from PyPI and hash-pinned (`frame_gallery/requirements/runtime.txt`); only the core install of `samsungtvws`, no extras. Licences and files were read from the installed distributions on 2026-09-27.

| Package | Version | Licence (SPDX) | Licence files | Obligations |
| --- | --- | --- | --- | --- |
| `websocket-client` | 1.9.2 | `Apache-2.0` | `LICENSE` | Licence text |
| `requests` | 2.34.2 | `Apache-2.0` | `LICENSE`, `NOTICE` | Licence text **and `NOTICE`** |
| `charset-normalizer` | 3.5.1 | `MIT` | `LICENSE` | Licence text |
| `idna` | 3.20 | `BSD-3-Clause` | `LICENSE.md` | Licence text |
| `yarl` | 1.25.1 | `Apache-2.0` | `LICENSE`, `NOTICE` | Licence text **and `NOTICE`** |
| `multidict` | 6.9.1 | `Apache-2.0` | `LICENSE` | Licence text |
| `propcache` | 0.5.4 | `Apache-2.0` | `LICENSE`, `NOTICE` | Licence text **and `NOTICE`** |

`urllib3` and `certifi`, which `requests` also needs, are listed above. `charset-normalizer`, `yarl`, `multidict`, and `propcache` ship native extensions; the platform wheels are selected, and re-checked, when the container is built (Phase 6).

### Components that enter in later phases

These are **not yet used**. Each is added here when it enters, after its licence is checked:

- The base image and its OS packages, including GPL and LGPL packages such as BusyBox: Phase 6, from the image SBOM.

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

The local development environment installs the Pillow wheel for macOS `arm64`. That wheel bundles a different set of libraries from the Linux runtime wheels. Its contents say nothing about the runtime image, and they are not used for this inventory.
