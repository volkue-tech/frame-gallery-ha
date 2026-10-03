# Frame Gallery for Home Assistant: the app image (ARCHITECTURE.md §17.2, D-130, D-167).
#
# The build context is this directory. There is no "syntax" line: the
# builder's own Dockerfile frontend is used, so the build pulls nothing but
# the pinned base image. It downloads python3 from the Alpine package source
# and the hash-pinned wheels from PyPI (requirements/image-*.txt).
#
#   docker buildx build --platform linux/arm64 --build-arg BUILD_ARCH=aarch64 \
#       --build-arg BUILD_VERSION=0.1.0.dev0 --target runtime --load -t frame-gallery:dev .
#
# Targets: "runtime" is the app image. It is the last stage, so a build
# without a target, as the Supervisor makes one, produces it. "test" adds
# the test tools and the tests on top of the app, for the container checks
# only (scripts/container_check.sh); it is never published. BuildKit builds
# only the stages a target needs; a builder without BuildKit builds the test
# stage too, but the image it produces is still the app.

# --- the pinned base -------------------------------------------------------------
FROM ghcr.io/home-assistant/base:3.24-2026.08.0@sha256:93ef607824e3f27e868f11b10938283a98bf880ed57bcf8eaa81c6c2d521f6f5 AS base

# --- the interpreter for the build, with the pip wheel it bundles ----------------
FROM base AS python
RUN apk add --no-cache python3=3.14.8-r0

# --- the virtual environment -----------------------------------------------------
FROM python AS builder
COPY requirements/image-runtime.txt /tmp/build/requirements.txt
# The base image points pip at another index (PIP_EXTRA_INDEX_URL). --isolated
# makes pip ignore every PIP_* variable and the user's configuration, and
# PIP_CONFIG_FILE=/dev/null every configuration file, so only PyPI is used;
# the hashes fix what is installed either way.
RUN python3 -m venv /tmp/build/installer \
    && python3 -m venv --without-pip /opt/frame-gallery \
    && PIP_CONFIG_FILE=/dev/null /tmp/build/installer/bin/pip --isolated \
        --disable-pip-version-check \
        --python /opt/frame-gallery/bin/python install --no-cache-dir \
        --index-url https://pypi.org/simple \
        --require-hashes --no-deps --only-binary=:all: \
        -r /tmp/build/requirements.txt
COPY src/frame_gallery /opt/frame-gallery/lib/python3.14/site-packages/frame_gallery
RUN /opt/frame-gallery/bin/python -I -m compileall -q -j 0 \
        /opt/frame-gallery/lib/python3.14/site-packages/frame_gallery

# --- the app ---------------------------------------------------------------------
FROM base AS app
ARG BUILD_ARCH
ARG BUILD_VERSION
ARG TARGETARCH
# BUILD_ARCH and BUILD_VERSION are required: the Supervisor passes both when
# it builds the app; a local build passes them too. With BuildKit, BUILD_ARCH
# must also match the platform being built; a builder without TARGETARCH
# accepts any supported BUILD_ARCH. The interpreter is installed here once
# more, without the pip wheel it bundles for ensurepip, in the same layer, so
# that no layer of the app holds pip or what pip vendors (D-167).
RUN test -n "${BUILD_VERSION}" || { echo "BUILD_VERSION is required" >&2; exit 1; } \
    && case "${BUILD_ARCH}" in aarch64|amd64) ;; \
        *) echo "BUILD_ARCH must be aarch64 or amd64" >&2; exit 1 ;; esac \
    && case "${TARGETARCH:-none}/${BUILD_ARCH}" in none/*|arm64/aarch64|amd64/amd64) ;; \
        *) echo "BUILD_ARCH ${BUILD_ARCH} does not match ${TARGETARCH}" >&2; exit 1 ;; esac \
    && apk add --no-cache python3=3.14.8-r0 \
    && rm -rf /usr/lib/python3.14/ensurepip/_bundled
COPY --from=builder /opt/frame-gallery /opt/frame-gallery
# Current original notices/evidence are committed in the Supervisor build context.
# This includes no downloaded source archives or runtime/user data. D-190.
COPY license_bundle /usr/share/frame-gallery/licenses
# D-177: the pinned s6 CMDSIG uses kill --, unsupported by BusyBox's sh
# builtin. Bash is already in the base. Keep the body/arguments unchanged;
# fail closed if the exact upstream script differs on a future base.
RUN echo '7debfda814cfe11f6b87492cce523eb6e1a2abdf622d0465b73c6d3ccd4bef72  /package/admin/s6-overlay-3.2.3.0/etc/s6-linux-init/skel/CMDSIG' | sha256sum -c - \
    && sed -i '1s|^#!/bin/sh$|#!/bin/bash|' /package/admin/s6-overlay-3.2.3.0/etc/s6-linux-init/skel/CMDSIG
# The base image's own labels describe the base (io.hass.base.*); the OCI
# ones are set for the app, and the base's source and build time cleared.
LABEL \
    io.hass.type="app" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.version="${BUILD_VERSION}" \
    org.opencontainers.image.title="Frame Gallery" \
    org.opencontainers.image.description="Sends one fresh artwork to a Samsung Frame TV each time it is started." \
    org.opencontainers.image.version="${BUILD_VERSION}" \
    org.opencontainers.image.source="" \
    org.opencontainers.image.created=""
# The base image's init (s6-overlay v3) runs the command once; the app exits
# after one run, and the container stops with it (D-130 check b). s6 resets
# the command's environment, so with-contenv restores the container's, which
# carries SUPERVISOR_TOKEN (check d). S6_CMD_RECEIVE_SIGNALS sends a stop
# request (SIGTERM) straight to the app, which then has the whole stop timeout
# of config.yaml (check c); s6's own grace would be 3 s. S6_VERBOSITY=1 keeps
# s6's start-up notes out of the app's log.
ENV S6_CMD_RECEIVE_SIGNALS=1 S6_VERBOSITY=1
CMD ["with-contenv", "/opt/frame-gallery/bin/python", "-I", "-B", "-m", "frame_gallery"]

# --- the container checks (never published) --------------------------------------
FROM app AS test
COPY --from=builder /tmp/build/installer /tmp/build/installer
COPY requirements/image-test.txt /tmp/build/test-requirements.txt
RUN PIP_CONFIG_FILE=/dev/null /tmp/build/installer/bin/pip --isolated \
        --disable-pip-version-check \
        --python /opt/frame-gallery/bin/python install --no-cache-dir \
        --index-url https://pypi.org/simple \
        --require-hashes --no-deps --only-binary=:all: \
        -r /tmp/build/test-requirements.txt \
    && rm -rf /tmp/build \
    && adduser -D -H -u 1000 -s /sbin/nologin checker
COPY . /opt/frame-gallery-checks
WORKDIR /opt/frame-gallery-checks
ENV COVERAGE_FILE=/tmp/.coverage

# --- the app image: the last stage --------------------------------------------
FROM app AS runtime
