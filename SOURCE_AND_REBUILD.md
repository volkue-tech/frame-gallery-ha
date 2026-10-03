# Sources, replacement and rebuilding

This is a **developer** guide, not the installation procedure for a Home
Assistant user. The public beta must install through Supervisor without SSH,
Docker on the user's computer, or changes to `configuration.yaml`. Publication
and the clean public installation remain separate release gates.

## What accompanies a distributed image

Project-owned code is Apache-2.0. The image is **not** licensed as a single
Apache-2.0 work: it also contains GPL, LGPL, MPL and permissively licensed
components. Preserve their original terms, copyrights, notices and patent texts.
`THIRD_PARTY_NOTICES.md` identifies the components; original documents are in
`LICENSES/` and, in the image, `/usr/share/frame-gallery/licenses/`.

For each published version, distribute a matching source package alongside the
image. Its `manifest.json` identifies the exact project commit, archive lengths
and SHA256s. `project-source.tar` contains that clean commit, including this guide,
Dockerfile, dependency locks, profiles, tests, notices and the CMDSIG modification.
Other entries are **inert upstream source archives**, including:

- `alpine-recipes/`: the 45 exact package recipe directories, with their local
  patches and build/install controls for the 61 installed Alpine packages;
- `alpine-sources/`: their 58 upstream files, including external patch files;
- `python/`: all eleven exact Python source distributions, including the
  `samsungtvws` package and Pillow's LGPL fribidi-shim source;
- `pillow-native/` and `pillow-bsd/`: native-library sources, libbsd/libmd,
  Pillow's versioned release/build files and its exact multibuild submodule;
- `base/`, `skarnet/`, `static/` and `go/`: the base's build files, bashio,
  jemalloc, S6 components/helpers, BearSSL, musl, Go source and module sources.

The corresponding nine `LICENSES/*source-manifest.json` files identify upstream
URLs, versions/revisions and hash provenance. Some hashes are publisher-verified;
others are calculated retention hashes. A matching hash proves retained bytes,
**not** byte-identical rebuilding or an ownership/patent clearance. The source
package contains no Git history, private credentials, HA state, pairing tokens,
user artwork or binary cross-compilers. It is intentionally larger than just
the application source because the published container includes an OS.

Do not delete the published source for an image that remains available. Keep
source packages available for at least three years after the last distribution
of their matching images, and longer if a distribution method requires it.
An upstream URL alone is not this project's source-availability mechanism.

## Assemble and verify the retained package

Run from `frame_gallery/`, with the approved development environment. Upstream
archives must already be retained under the repository's ignored `build/phase9/`
and match the fixed manifests. This command makes **no network requests**, executes
no upstream code and extracts no upstream archive:

```bash
.venv/bin/python scripts/source_bundle.py --output-name frame-gallery-sources-candidate.tar
```

It requires a clean committed checkout, includes only the fixed manifests'
named archives, rejects links, missing/tampered sources and excessive input,
and writes exclusively into `build/source-packages/`. It re-reads the completed
package and checks every member. An existing output is preserved, not overwritten.
A failure may leave a partial **unpublished** output for inspection; never upload
it. The emitted result is a local integrity result, not release approval.

After any source, dependency, packaging or notice change, make a new clean
commit, run the gates, and assemble a new uniquely named package. Match the
package's commit to the actual image build commit. A previous candidate is not
the final source package merely because application code did not change.

## Rebuild the application image

On a supported native Linux architecture with Docker Buildx, in the matching
project checkout, run:

```bash
cd frame_gallery
docker buildx build --platform linux/arm64 \
  --build-arg BUILD_ARCH=aarch64 --build-arg BUILD_VERSION=modified-local \
  --target runtime --load -t frame-gallery:modified-local .
```

For Intel replace `linux/arm64` with `linux/amd64` and `aarch64` with `amd64`.
This builds the actual runtime target, not the test image. It uses the digest-
pinned HA base, exact `python3` apk version and hash-pinned wheels. A normal
build therefore still needs the registry, Alpine and PyPI. Availability of the
source package does **not** mean the Dockerfile is a fully offline build.

The own-code regression gates are documented in `frame_gallery/DEVELOPMENT.md`.
Run the host gates and native container/root/memory checks for each architecture
you distribute. AppArmor enforcement must also be verified under Supervisor;
Docker Desktop's unattached profile is not a replacement for that test.

## Replace a separately installed Python library

There is no project-owned signing key, runtime wheel-hash check or EULA preventing
replacement of a library. The download hashes protect the original **build**;
they do not authenticate installed library files on each start. Modification and
reverse engineering for debugging modifications to the LGPL-covered parts are
not prohibited by this project. Preserve compatible public APIs and the trusted
worker protocol, or expect the app's safety/compatibility checks to fail.

For example, an experienced developer can unpack the provided `samsungtvws`
source in a disposable development directory, edit the library, and build a
derived local image. A developer-authored Dockerfile can use:

```dockerfile
FROM frame-gallery:modified-local
COPY samsungtvws /opt/frame-gallery/lib/python3.14/site-packages/samsungtvws
```

Here `samsungtvws/` is the **package directory** from the supplied source, not
the archive's top-level directory or a local HA data folder. Keep the original
licence and publish the modified library source/changes with any distributed
derived image. No additional app permission is needed merely to load a
replacement library. Test compatibility before contacting a television.

For an ordinary dependency upgrade, update the dependency specification and lock,
regenerate `requirements/runtime.txt` and both `requirements/image-*.txt`, review
the new sources/notices, and run the gates as documented in DEVELOPMENT. Do not
change a hash to conceal different bytes under the old version.

## Rebuild Pillow and its native components

The exact Pillow source distribution supplies the shim's `fribidi.c`/`fribidi.h`,
raqm sources, setup/build configuration and the normal Pillow code. The separate
release archive supplies `.github/workflows/`, dependency recipes, patches and
the exact multibuild revision used by the supplier's musllinux build. The retained
native archives supply the corresponding versioned dependencies.

Use those upstream build files as the starting point for a CPython 3.14
musllinux build on the desired architecture. Pillow is native code: merely
copying a changed `.c` file into the installed image does not rebuild it.
Compile a replacement wheel, preserve the native library licences/patent texts,
and unpack the complete wheel into the virtual environment of a derived image,
including its `pillow.libs/` directory and distribution metadata. Alternatively
teach a development-only builder to install the locally rebuilt wheel, then
copy that virtual environment into the runtime stage. Do not include compilers
or a pip installer in the final runtime solely for this task.

The supplied libtiff 4.7.1 patch is upstream commit
`782a11d6b5b61c6dc21e714950a4af5bf89f023c`, already applied by Pillow's supplier,
not a Frame Gallery modification. Preserve it for rebuilding the same inputs.
Neither optional libimagequant nor FriBiDi is in the audited runtime wheels.
The LGPL-covered **fribidi-shim is**; its replacement must rebuild `_imagingft`.

This guide documents how to replace the library and where its build inputs are;
we have **not** reproduced Pillow's wheel bytes from source. The production
image's user-install path does not depend on a user's doing such a rebuild.

## Rebuild OS and base components

For each Alpine component, match the installed package's origin/build commit to
`alpine-source-manifest.json`. Use its retained APKBUILD, local source files and
upstream archives with Alpine's package build tooling for the same release and
architecture. Retain all patches and configuration, not just the original
upstream tarball. Recipe-only packages generate their installed data directly
from the supplied recipe. Do not evaluate untrusted build recipes on a live Green.

The retained Home Assistant base source supplies its Dockerfile/build scripts;
S6 sources and helpers supply their build scripts; tempio includes its Go module
lock. Use the exact revisions and toolchain versions recorded in the manifests.
The identified S6 libc source differs from the shared Alpine musl source and is
retained separately. Binary cross-compilers inspected for provenance are not
redistributed by this project. Rebuilding all base components bit-for-bit has
not been performed and is not claimed.

The sole base-script change made by Frame Gallery is visible in its Dockerfile:
verify the pinned CMDSIG hash and replace only `#!/bin/sh` with `#!/bin/bash`.
Its upstream body remains unchanged. The supplied source and own Dockerfile
therefore describe both the original and the modification.

## Installing a modified version

Use your own repository/image namespace and a distinct app slug/version. Home
Assistant's Supervisor supports custom repositories and developer local apps;
follow the development-install section of DEVELOPMENT for the latter. Do not
overwrite another installation or reset its history/pairing data for a rebuild.
The project supplies no vendor key or activation secret that a modified version
needs to run. Standard HA/Supervisor privileges and the user's TV authorization
are still required; this is not permission to bypass either system.

These are engineering instructions, not a legal opinion. Source distribution,
notice retention, licences, modification disclosures and any applicable
installation-information duties must be assessed for the actual version and
distribution method; publishing an archive alone does not settle every duty.
