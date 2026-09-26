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

### Components that enter in later phases

These are **not yet used**. Each is added here when it enters, after its licence is checked in the pinned distribution:

- `urllib3` (`MIT`) and `certifi` (`MPL-2.0`): Phase 3.
- `samsungtvws` 3.0.6 (`LGPL-3.0`) and its dependencies `websocket-client`, `requests` (with its `NOTICE`), `charset-normalizer`, `idna`, `yarl` (with its `NOTICE`), `multidict`, and `propcache` (with its `NOTICE`): Phase 5.
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
