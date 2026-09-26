# Decision log

Status values:

- `accepted`: binding.
- `proposed`: awaiting approval by the user, and by Codex where `TASKS.md` requires it.
- `superseded`: replaced by a later decision.

Phase 1 added:

- decisions D-106 onward;
- the proposed dependency inventory;
- the risk register;
- the open questions.

The rationale for each architecture decision is in `ARCHITECTURE.md`, at the section given in brackets. This version incorporates the findings of the Phase 1 multi-lens review (see `ARCHITECTURE.md`, header).

## Accepted constraints

### D-001 — Independent repository

Status: accepted

The new project is not a fork and shares no Git history or source files with predecessor projects.

### D-002 — Specification-only initial handoff

Status: accepted

Claude receives functional requirements, constraints, and acceptance criteria. Phase 1 contains no application implementation.

### D-003 — Primary platform

Status: accepted

Home Assistant OS on Home Assistant Green (`aarch64`) is the primary target. `amd64` is secondary.

### D-004 — User installation boundary

Status: accepted

End users must not need SSH, shell commands, local Docker installation, or changes to `configuration.yaml`.

### D-005 — Default artwork treatment

Status: accepted

The complete artwork is preserved by default. Cropping occurs only through an explicit option. Non-matching aspect ratios are fitted onto a 16:9 canvas, black by default.

### D-006 — One-shot lifecycle

Status: accepted

Each start performs at most one upload attempt outcome and then exits. Selection and network activity are bounded, and a no-match run leaves the television unchanged.

## Proposed decisions requiring approval

### D-101 — Project name

Status: proposed. Needed before Phase 9.

Working name: **Frame Gallery for Home Assistant**.

Rationale: distinct, descriptive, and not tied to a predecessor repository name. Branding and trademark wording require review before release (R-14).

Until the name is decided, `frame_gallery` is used as the provisional internal identifier: package name, app slug, `/media/frame_gallery`, User-Agent, and the television client name if the 3.0.6 API accepts one (Q-15). Confirming it is asked **before Phase 2**. A later rename is mechanical.

### D-102 — Project license

Status: proposed. Needed before Phase 9.

Apache License 2.0 for independently authored project code.

Rationale: permissive reuse with an explicit patent grant. Third-party dependencies keep their own licenses.

### D-103 — Implementation language

Status: proposed (refined in Phase 1)

**Decision:**

- Python, with code compatible with **CPython 3.12–3.14**. CI runs all three versions.
- The container runs the exact-pinned Alpine `python3` of the chosen base image. For reference, Alpine 3.24 ships 3.14.7 and Alpine 3.23 ships 3.12.14.
- The container smoke test runs that interpreter.

**Rationale:**

- CPython 3.12 is already security-only (end of life 2028-10). 3.13 (EOL 2029-10) and 3.14 (EOL 2030-10) still receive bug fixes.
- Every runtime dependency publishes `musllinux_1_2` wheels for `aarch64` and `x86_64` for all three versions.
- `samsungtvws` 3.0.6 and Pillow 12 both require Python ≥ 3.10.

### D-104 — Samsung transport

Status: proposed (refined in Phase 1)

**Decision:**

- Use `samsungtvws` **3.0.6** (PyPI, released 2026-09-11, `LGPL-3.0`, requires Python ≥ 3.10).
- Core install only, without extras.
- It is imported only by the television worker task, which runs isolated and unprivileged (D-109).

**Phase 1 findings from PyPI.** The release, license, and requirement facts were independently verified. The maintainer, pairing, and subnet notes were not re-verified.

- **Documentation gap.**
  - Since 3.0.0 the README documents no Python art-mode API. It says only "Full Art Mode support (Frame TVs)" and points to example files hosted on GitHub.
  - The last README that documented art methods is 2.7.2 (December 2024): `art().supported()`, `upload(data, file_type='JPEG')`, `select_image(content_id, show=…)`, `get_artmode()`, and related calls.
  - No README documents a "no matte" value or a client-name parameter.
- **Constructor.** The `SamsungTVWS(host=…, port=8002, token_file=…)` form appears only in READMEs up to 2.7.2. 3.x documents no constructor. Q-15 confirms it, and Phase 5 takes every parameter from the installed 3.0.6 package only.
- **Errors and timeouts.** None documented.
- **Pairing prompt.** Newer televisions prompt on every connection unless *Access Notification Settings* is set to *First Time Only*. The user documentation must say so.
- **Network placement.** Televisions refuse WebSocket connections from other subnets or VLANs. Whether NAT through the host is accepted is verified in Phase 8 (Q-16).
- **Maintenance.** A single maintainer, with bursty releases.

**Confirming the 3.0.6 art API (Q-15).** Two options:

1. **Recommended:** inspect the *installed* 3.0.6 distribution's public signatures and docstrings (`help()` / `inspect`) in a local virtual environment. This reads only the approved package, with no GitHub access.
2. Read files from the dependency's GitHub repository. **Risk statement:** the `examples/` directory contains Frame art-mode automation scripts. Their provenance cannot be verified without reading them, and they may overlap the category of material the independence boundary excludes. If this option is chosen at all, it must:
   - be limited to API-reference files such as a command reference, excluding example application scripts;
   - not follow links to forks, issues, or other projects;
   - log every file read in this decision log.

**Rationale for depending on a library rather than implementing the protocol:**

- Samsung publishes no documentation of Art Mode or of the local WebSocket control protocol.
- SmartThings has no art-mode capability and no image upload.
- Samsung's consumer documentation describes only manual upload (SmartThings app or USB).

A maintained library under a known license is safer than a new protocol implementation, which would also be the most sensitive area under `LEGAL_BOUNDARIES.md`.

### D-105 — Release architectures

Status: proposed

Publish `aarch64` and `amd64` first. Add other architectures only after successful builds and explicit support decisions.

Phase 1 note: Home Assistant currently supports only these two app architectures (32-bit support ended with release 2025.12).

## Proposed architecture decisions (Phase 1)

### D-106 — Synchronous core, phase budgets, watchdog [§4.3, §7]

Status: proposed

**Decision:**

- A single run thread with no `asyncio`.
- Phase deadlines come from the normative budget table (D-114). Every blocking call's timeout is clamped to its phase deadline.
- `Allowance` counters bound loops.
- A watchdog kills the worker process group and exits at the total run deadline + 10 s.
- DNS resolution runs in a fresh daemon thread per lookup, joined with a clamped timeout. Abandoned threads are bounded in number by the request allowances. CONFIGURE, the `ha` client, and the gateway all use this resolver.

**Rationale:** the workload is short and sequential, fake-clock testing is simpler, and the libraries involved are synchronous.

**Alternative considered:** `asyncio` with task cancellation. It adds complexity and still cannot cancel DNS resolution or native code.

### D-107 — Ports and adapters with an enforced import boundary [§5, §20.2]

Status: proposed

**Decision:** Third-party imports are confined to three places:

- `imaging` worker tasks (Pillow);
- the `tv` worker task (Samsung library);
- `net.transport` (`urllib3`, `certifi`).

The parent process never imports Pillow or the Samsung library. An import-boundary check runs from Phase 2.

### D-108 — Guarded gateway for all provider traffic [§10, §7.5]

Status: proposed

**Decision:** One gateway handles every provider request. It enforces:

- **Hosts.** Exact or label-boundary host rules after IDNA normalization.
- **URLs.** HTTPS on port 443, no user-info, no IP literals.
- **Resolution.** One resolution per request, rejected unless *every* address is global (mapped forms unwrapped, CGNAT rejected). The connection goes to the validated IP with the SNI hostname, and the peer is checked before sending.
- **TLS.** `CERT_REQUIRED`, TLS ≥ 1.2, and an explicit `certifi` bundle.
- **Redirects.** At most 3, each re-validated.
- **Identifiers.** Provider identifiers placed into URLs must `fullmatch` a pattern and are percent-encoded.
- **Byte caps** on decoded bytes. Images use identity encoding; metadata may use a single gzip layer.
- **Timeouts.** A total per request (metadata 15 s, probe 10 s, download 45 s). Per-address connect timeouts. The receive timeout is re-clamped before every read.
- **Pacing.** A per-provider `min_interval`.
- **Hygiene.** No cookies, environment proxies, or credential files.

### D-109 — Isolated, unprivileged workers [§11.3, §12]

Status: proposed

**Decision:** A spawned worker performs all image inspection, decoding, rendering, and encoding. A separate worker performs the whole television interaction. Each worker:

- drops to an unprivileged user ID (65534) with an empty supplementary-group list;
- sets `PR_SET_PDEATHSIG` **after** dropping privileges, because the kernel clears it on credential changes;
- sets its umask and resource limits. `RLIMIT_AS` is 1 GiB for the image worker and 512 MiB for the television worker, plus CPU limits;
- installs logging and Pillow limits before any third-party import;
- inherits only the allowlisted environment (`PATH`, `LANG`, `LC_ALL`, `TZ`), so it has no `SUPERVISOR_TOKEN` or legacy `HASSIO_TOKEN`;
- runs in its own process group;
- returns progress markers and results **as bytes only**, which the parent parses as JSON and validates. Nothing the child sends is ever unpickled.

The parent chooses all paths, re-validates `delivery.jpg` with a stdlib-only JPEG header check, and computes the SHA-256 itself. The television worker reports progress markers (`connected`, `upload_started`, `uploaded`, `selected`), and the parent classifies the outcome from them.

**Rationale:** Native and third-party code handling untrusted input or undocumented protocols is contained. Hangs, crashes, and exploits become classified outcomes.

**Simplification available:** run everything in-process and rely on the watchdog. The guarantees are weaker: a hang becomes a watchdog kill, and the token is exposed to parser exploits.

### D-110 — JSON state with an atomic write protocol and pre-staged history [§13]

Status: proposed

**Decision:**

- **State files.** Plain JSON under `/data`: history, `current.json` (success-only attribution and fingerprints), `last_run.json` (every outcome), and a per-provider cache.
- **Write primitive.** Every write uses one primitive:
  - operations relative to a directory file descriptor opened with `O_NOFOLLOW`;
  - temporary files created with `O_EXCL` and random suffixes;
  - `fsync`, then rename, then directory `fsync`.
- **History.**
  - The next history generation is **pre-staged and fsynced before DELIVER**. A full or read-only `/data` is therefore caught as `state_error` while the television is still untouched.
  - After the television reports `selected`, RECORD is a single rename.
  - A `.bak` generation is rotated best-effort. A failure there is logged and never blocks the rename.
  - `.bak` covers damage that leaves the primary unparseable or schema-invalid after a successful write: storage corruption, a restore that truncates the file, or a malformed external edit. Well-formed but wrong data is not detected, so `.bak` does not cover it.
- **Reader.** Tries primary, then `.bak`, then starts empty with a warning. Only parse or schema failures are quarantined (at most 3 files, kept for diagnostics). A **newer** version is not corruption: the run ends as `state_error` before touching the television.
- **Locking.** A non-blocking lock; contention ends as `already_running`.
- **No database dependency.**

**Alternative considered:** `sqlite3`. It is transactional, but less transparent, and its benefits are small at one write per run.

### D-111 — Preview in `/media`, shown through a Local File camera [§13.5, §16.3]

Status: proposed

**Decision:**

- The exact delivered JPEG is published atomically to `/media/frame_gallery/preview/latest.jpg`, and publication is refused if any path component is a symbolic link.
- The dashboard shows it through a UI-created Local File camera (named "Frame Gallery Preview") and a `picture-entity` card.
- The app never writes into the Home Assistant configuration folder.

### D-112 — Static options with optional helper overrides [§15.3]

Status: proposed

**Decision:**

- Static options always work.
- The optional `*_helper` entity IDs are:
  - re-validated with `fullmatch` and percent-encoded;
  - read with at most 3 `GET /core/api/states/<id>` calls, with no redirects or retries, `Authorization` only for `http://supervisor`, a 64 KiB body cap, and JSON only;
  - read for the `state` field only.
- Any problem falls back to the static value with one warning.
- The app writes nothing to Home Assistant.

### D-113 — Record history before publishing the preview [§4.1]

Status: proposed. This is a specification deviation (Q-18).

**Decision:** History is recorded immediately after the television confirms selection, and the preview is published after that.

**Rationale:** A missing preview is harmless, whereas a missing history entry allows a resend.

### D-114 — Budget decomposition [§7.2]

Status: proposed. **The tables in `ARCHITECTURE.md` §7.2 are normative.**

**Phase budgets:**

| Phase | Budget |
| --- | --- |
| CONFIGURE | 7 s (includes resolving `tv_host`, `supervisor`, and `homeassistant`, each ≤ 3 s and clamped) |
| RESOLVE_FILTERS | 8 s, outside selection; up to 3 helper reads, each ≤ 3 s, clamped to the phase |
| SELECT | `S` = 60 s by default; the advanced option `selection_time_limit` allows 20–120 s |
| ATTEMPT | 90 s, shared by at most 2 attempts; per attempt: download ≤ 45 s, prepare ≤ 30 s |
| DELIVER | 90 s |
| FINISH (`publish_reserve`) | 10 s |
| **Total run deadline `T`** | **`S` + 205 s** (265 s by default); a unit test asserts the sum |
| Shutdown allowance | 10 s |

**Allowances and limits:**

- **Allowances:**
  - shortlist of 2;
  - 150 candidates after the history filter;
  - 25 metadata requests;
  - 30 remote probes;
  - 500 local inspections;
  - 20 000 directory entries at depth ≤ 4.
- **Per-request limits:**
  - totals: metadata 15 s, probe 10 s, helper read 3 s;
  - connect ≤ 5 s per address;
  - read ≤ 10 s between bytes;
  - DNS ≤ 5 s.
- **Other:**
  - worker `RLIMIT_AS`: image worker 1 GiB, television worker 512 MiB;
  - dashboard fallback timer `T` + 35 s: 300 s by default, 360 s at `selection_time_limit` = 120. The documentation gives the value for each setting.

`selection_time_limit` is the only user-adjustable limit.

### D-115 — Retry and pacing policy [§7.4]

Status: proposed

**Decision:**

- **Metadata requests.** At most 1 retry, only for:
  - connect errors;
  - HTTP 502/503/504;
  - HTTP 429 with a `Retry-After` of ≤ 5 s, in either delta-seconds or HTTP-date form.

  The wait is `max(Retry-After, 1 s)` plus jitter, and the retry is skipped if it would exceed the deadline.
- **Refusals.** Any HTTP 403, or any HTTP 429 not followed by the single permitted metadata retry, from any host in a provider's policy (including image hosts), ends all requests to every host of that provider for the run. Remote shortlisted candidates are then not attempted. A retried 429 also delays every later request to that provider until its `Retry-After` has passed.
- **No retries** for probes, downloads, helper reads, uploads, or selects.
- **Television.** At most 1 reconnect, and only before `upload_started`.
- **Pacing.** A per-provider `min_interval`; the Art Institute of Chicago's is 1 s.

### D-116 — Shape and quality thresholds [§8.1]

Status: proposed; the values need approval (Q-03).

**Decision:**

- Square band: 0.95 ≤ w/h ≤ 1/0.95.
- Strict near-16:9: within ±4 % log-ratio, that is 1.709–1.849.
- Quality: reject when the fit mode's upscale factor on the 3840 × 2160 canvas exceeds 2.5.

All values are measured after EXIF orientation, on the deliverable rendition.

### D-117 — Fallback permission [§8.2]

Status: proposed (Q-11 offers an alternative)

**Decision:** Fallback to the landscape works closest to 16:9 is permitted only when `landscape_only` is on and `fit_mode` is `contain`, as the specification states. Fallback images are always fitted without cropping.

### D-118 — Local media identifier [§9.2]

Status: proposed (see Q-04)

**Decision:** `local:fp:<sha256(size ‖ first 64 KiB ‖ last 64 KiB)>`. The last 10 preview fingerprints are also kept in `current.json`, so the preview can be excluded from selection.

### D-119 — Honest User-Agent [§10]

Status: proposed

**Decision:** Requests identify the app as `FrameGallery/<version> (+<project URL>)`. Provider courtesy headers, such as the Art Institute's `AIC-User-Agent`, carry the project name and a project-owned contact email, never user data. There is no browser impersonation.

### D-120 — First public beta scope [§22]

Status: proposed. **This deviates from the specification's initial-provider list; see Q-01, Q-17, and Q-18.**

**Included:**

- Sources: local media and the Art Institute of Chicago (D-132).
- Static filters and optional helpers.
- Landscape-only; strict format with fallback; the upscale rule; `contain` and `cover`.
- Atomic, pre-staged history; atomic preview; the small Art Institute cache; self-healing pairing.
- Documentation and dashboard YAML.
- `aarch64` and `amd64`.

**Deferred:**

- Companion integration.
- Multi-source rotation.
- Further open-collection providers.
- Google Arts & Culture, until an official API exists (Q-01).
- Remote-probe machinery, until a provider needs it.
- Matte selection.
- Helper auto-provisioning.
- An unprivileged parent process (Q-10).
- A configurable library folder.
- Local colour or style filtering.
- A history-reset option.
- More architectures.

**Not planned:**

- Ingress (D-126).
- Bing (Q-17).
- Managing old images on the television (a non-goal).

Choosing Q-01 option (c), or overriding Q-17, first requires the user to amend the `LEGAL_BOUNDARIES.md` rule on respecting access terms and technical restrictions. That would then reopen D-120 with a new adapter milestone. Making a source off by default or opt-in does not satisfy the rule.

### D-121 — Image safety limits [§11]

Status: proposed

**Decision:**

- Width and height ≤ 20 000 px each. Total pixels ≤ 64 MP for JPEG, which is draft-decoded, and ≤ 40 MP for PNG, which has no reduced decode. Both are checked from the header before decoding. Pillow's global `MAX_IMAGE_PIXELS` is set to 64 MP, and the PNG cap is an explicit header check.
- The decompression-bomb warning is escalated to an error, and a format allowlist (JPEG, PNG) applies.
- Downloads are capped at 40 MiB.
- Everything runs in the image worker under a 1 GiB `RLIMIT_AS` ceiling. That limits virtual address space; the estimated worst-case resident peak is ≈ 450–550 MiB (§11.1).

### D-122 — Colour management [§11.1]

Status: proposed

**Decision:**

- Embedded ICC profiles are converted to sRGB; images without one are assumed to be sRGB.
- Output is an 8-bit RGB baseline JPEG with no EXIF.
- Palette and bit-depth normalization happens before resizing, so resampling is never nearest-neighbour. Colour-space conversion (ICC, CMYK) and alpha compositing happen after resizing, to bound memory use.

**Rationale:** Art reproduction benefits noticeably. Pillow's documentation lists littlecms2 among the libraries in its wheels; Phase 3 confirms this with the runtime feature report.

### D-123 — App options [§15.1]

Status: proposed

**Decision:** The option set, schemas, and defaults are those in `ARCHITECTURE.md` §15.1. In particular:

- `tv_host` is required, with no default.
- `selection_time_limit` and `log_level` are optional advanced options.
- There is no `local_folder` option (the path is fixed) and no user-facing probe option.

### D-124 — Filter vocabularies [§15.2, §9.1]

Status: proposed (final lists in Phase 4; see Q-14)

**Decision:**

- Versioned vocabularies, with deterministic normalization.
- A value is offered only if at least one approved beta provider maps it. Museum of Modern Art and Musée d'Orsay values are therefore excluded pending Q-01, Q-14, and Q-18.
- A dimension the source does not support at all is ignored, with one warning.
- A **helper-supplied** value the source cannot map falls back to the static option with one warning, as the specification requires.
- An unmappable **static** value ends as `no_match` with a hint. This is possible only once vocabularies span several providers.
- A value is never silently ignored.

### D-125 — Television address rules [§15.4]

Status: proposed (see Q-12)

**Decision:**

- `tv_host` is resolved once, in CONFIGURE. Only these ranges are accepted: RFC 1918, `169.254/16`, `fc00::/7`, and `fe80::/10` with a zone.
- Explicitly rejected: loopback, unspecified, and multicast addresses; the container's own networks; and the Supervisor's internal app network. The last two are determined at run time.
- The validated IP literal is passed to the television worker.

### D-126 — Dashboard filter approach [§16]

Status: proposed

**Decision:**

- **Beta:** static options plus documented Home Assistant helpers.
- **Ingress:** not planned. It needs a resident process and adds attack surface.
- **Companion integration:** deferred until after the beta. The versioned `current.json` and `last_run.json` schemas and the standard options mechanism keep that path open.

### D-127 — Standard-library parsing only [§18.2]

Status: proposed

**Decision:** Provider JSON, and HTML only if a provider is ever approved to need it, is parsed with `json` and `html.parser`. No lxml or BeautifulSoup.

### D-128 — Reproducible builds and update policy [§17]

Status: proposed

**Decision:**

- **Lock file.** Generated with `uv pip compile --generate-hashes`: `uv` 0.12.19, `MIT OR Apache-2.0`, dev-only.
- **Installation.** `--require-hashes --no-deps --only-binary=:all:`.
- **Pinning.** Base image pinned by tag and digest; `python3` pinned to an exact apk version.
- **Review cadence.** Dependencies are reviewed monthly and immediately on security advisories. The base image is bumped at least with every Alpine stable release.
- **Upgrades.** Each upgrade needs the full test suite and an updated inventory entry. Pillow and the television library are upgraded only in dedicated commits.

### D-129 — App configuration and AppArmor profile [§17.1, §17.6]

Status: proposed

**Decision:**

- **`config.yaml` settings.**
  - `startup: once`, `boot: manual_only`, `init: false`.
  - `arch: [aarch64, amd64]`, `stage: experimental` until Phase 8 passes.
  - `homeassistant: "2026.2.0"`.
  - `homeassistant_api: true`. This grants the Core REST and WebSocket API on every install and has no effect on the security rating. The app restricts itself to ≤ 3 state GETs, and only when helpers are configured.
  - `tmpfs: true`, `timeout: 20`.
  - `map: [{type: media, read_only: false}]`. This grants read-write access to **all** of `/media`, which AppArmor narrows.
  - `backup_exclude: cache/**, state/quarantine/**, tv/**`.
- **Mandatory custom `apparmor.txt`.**
  - `/media` read-only, except read-write on `/media/frame_gallery/preview/**` and creation of exactly the directories `/media/frame_gallery/`, `preview/`, and `library/`.
  - Read-write on `/data/**` and `/tmp/**`.
  - Only the spawn and interpreter paths the worker needs.
  - `inet` and `inet6` stream and dgram only.
  - Minimal capabilities.
  - Verified in enforce mode in Phase 8.
- **Security rating: 6.**
- **Not set:** `hassio_api`, `hassio_role`, `host_network`, `privileged`, `full_access`, `docker_api`, `ingress`, `stdin`, `ports`, `devices`, `watchdog`, `advanced`. No `build.yaml`.

### D-130 — Container base image and build [§17.2]

Status: proposed

**Decision:**

- **Base.** `ghcr.io/home-assistant/base`, pinned by tag and digest.
- **Build.** A multi-stage build:
  - an exact-pinned apk `python3`, identical in both stages;
  - a venv created `--without-pip` and populated with hash-pinned, binary-only wheels;
  - Pillow from PyPI wheels, never from Alpine's `py3-pillow`.
- **Labels.**
  - `io.hass.arch` is derived from `BUILD_ARCH`, falling back to `TARGETARCH`.
  - `io.hass.version` comes from a required `ARG`.
  - The OCI `licenses` label is omitted, because the image is multi-licensed.
- **Tooling.** BuildKit/Buildx for multi-platform builds. Releases use the Home Assistant builder's `build-image` and `publish-multi-arch-manifest` actions, with Cosign signing.

**Selection criteria:**

- alignment with the official guidance;
- reproducibility;
- **copyleft surface.** The Home Assistant base ships bash and bashio, which the app does not use.

**Open verification (Phase 6).** Pulling the base image needs the user's confirmation. Then:

- (a) which Alpine and Python versions sit behind the pinned base;
- (b) the container reaches "stopped" when `CMD` exits, with exit code 0 and non-zero;
- (c) a Supervisor stop delivers SIGTERM, with enough grace before SIGKILL;
- (d) `SUPERVISOR_TOKEN` is visible without `with-contenv`.

**Fallback if any check fails:** a plain Alpine base (for example `alpine:<3.24.x>` with Alpine's `python3`) and `init: true`. Home Assistant's s6-overlay announcement acknowledges plain bases. The fallback's inventory row must be completed before adoption.

### D-131 — HTTP transport: `urllib3` directly [§10]

Status: proposed

**Decision:**

- The gateway uses `urllib3` 2.x with retries and redirects disabled, streaming, and explicit timeouts. It enters as a direct dependency in Phase 4, and `samsungtvws` later reuses it through `requests`.
- `requests` is not used by application code.
- `httpx` is not adopted.

### D-132 — Art Institute of Chicago as the beta museum source [§9.4]

Status: proposed

**Decision:** Implement the Art Institute of Chicago adapter against its documented API as the default beta source. It:

- queries public-domain works only;
- uses the documented dominant-colour, style, department, and image-dimension metadata. Server-side colour filtering is confirmed in Phase 4, with client-side checking as the fallback.
- downloads the documented 1686 px IIIF rendition, with the 4K canvas as the stated need;
- samples pages without replacement;
- paces requests 1 s apart and sends the courtesy header;
- makes at most 25 metadata requests per run;
- caches only counts and exhausted-page hints.

**Rationale:** It is the only surveyed source that is documented, needs no key, has CC0 images, and carries colour, collection, and style metadata. It directly drives acceptance items `C1`, `C2`, and `C6` without scraping.

**Known limitation:** renditions are upscaled by up to ≈ 2.28× in `contain` mode (R-19).

**Next provider:** Cleveland, with a near-4K rendition (3400 px long side, ≈ 1.13× upscale).

### D-133 — Exit-code policy [§4.2]

Status: proposed (Phase 8 check in Q-07)

**Decision:**

- Every classified outcome, including failures, exits **0**. The outcome name appears in the summary line and in `last_run.json`.
- Only bugs (`internal_error`, 70) and watchdog termination (71) exit non-zero.
- The documentation says to keep the app's Watchdog off.

**Rationale:** No documentation defines how the Supervisor treats non-zero exits of `startup: once` apps, or whether the Watchdog restarts them. A restart after a handled failure could re-upload outside the bounded retry policy (acceptance item `C8`).

### D-134 — Rights-basis allowlist [§9.1]

Status: proposed

**Decision:**

- Every `Candidate` carries a structured `rights_basis`, together with the metadata field it was read from.
- Each provider declares an allowlist:
  - Art Institute of Chicago: `CC0`;
  - local media: `USER_SUPPLIED`;
  - future providers: for example `CC0`, `PDM`, or `CC-BY-4.0` with mandatory attribution.
- Selection rejects anything else.
- A shared contract test checks every adapter.

### D-135 — Copyleft source availability [inventory]

Status: proposed; qualified review is recommended before Phase 9.

**Decision:** Each release attaches the corresponding source for every copyleft component in the image:

- the `samsungtvws` sdist;
- the Alpine aports and distfiles for the exact GPL/LGPL package versions in the image SBOM.

The source stays available for as long as the image is distributed, and for at least 3 years. A written offer is the documented alternative if attachment proves impractical.

The GPLv3 "Installation Information" duties are assessed as not applicable to a downloadable container image, pending that qualified review.

## Proposed dependency inventory

Status: **proposed**. Nothing is installed yet.

- Versions and licenses were read from PyPI metadata (`https://pypi.org/pypi/<name>/json`) on 2026-09-26.
- `samsungtvws` was independently re-verified.
- Before each dependency enters (see the per-phase approvals in `STATUS.md`), its `LICENSE` file inside the pinned distribution is checked and this table is updated.
- The final image SBOM must match this table (acceptance item `H4`).

This is an engineering inventory, not legal advice.

**Use** codes:

- **dyn**: imported at runtime, installed unmodified from PyPI with hash pinning.
- **redist**: included in the published image.
- **native**: contains compiled code.

No package is modified or vendored into the source tree.

### Runtime: direct

| Package | Source and pin | SPDX (as published) | Use | Obligations | Reason | Enters |
| --- | --- | --- | --- | --- | --- | --- |
| `samsungtvws` | PyPI, `==3.0.6`; later `>=3.0.6,<4` after contract tests. sdist SHA-256 `166111d8370443cd2021b74cdfac9495896dfc41e3a87ea023289f24f922bb91`; wheel SHA-256 `6e3a1b23f928b3035570cc976b64b8c2a218b06022a333855fd7cd02dc74891d`. | `LGPL-3.0` (deprecated short form; treated as `LGPL-3.0-only` until the shipped `LICENSE` says otherwise) | dyn, redist, pure Python; core install only | See the LGPL obligations below | Television transport (D-104) | Phase 5 |
| `Pillow` | PyPI `musllinux_1_2` wheels for `aarch64` and `x86_64`, `==12.3.0` (`<13` until validated) | `MIT-CMU` **for Pillow itself; the wheel is a composite** (see the bundled-library table) | dyn, redist, native | Pillow `LICENSE`; each bundled library's license and acknowledgement | Image pipeline (§11) | Phase 3 |
| `urllib3` | PyPI `==2.8.0` (`<3`), `py3-none-any` | `MIT` (`LICENSE.txt`) | dyn, redist | License text | Gateway transport (D-131) | Phase 4 |
| `certifi` | PyPI `==2026.7.22`, `py3-none-any` | `MPL-2.0` (`LICENSE`) | dyn, redist (CA bundle) | Files kept unmodified under MPL-2.0; identified in the notices; source pointer (D-135) | The gateway's explicit CA bundle (§10) | Phase 4 |

### Runtime: bundled in the Pillow wheels

**Expected; must be verified before Phase 3** from the pinned wheels' bundled shared objects (`pillow.libs/`), `dist-info` license files, and `dist-info/sboms`. Pillow's documentation names these libraries but publishes no exact list or versions.

| Library | Version (from the wheel SBOM, Phase 3) | Expected SPDX | Obligations |
| --- | --- | --- | --- |
| libjpeg-turbo | tbd | `BSD-3-Clause AND IJG AND Zlib` | Include the licenses. IJG acknowledgement in `DOCS.md` and the notices: "This software is based in part on the work of the Independent JPEG Group." |
| FreeType | tbd | `FTL OR GPL-2.0-or-later`; **FTL elected** | FTL credit in the documentation: "Portions of this software are copyright © The FreeType Project (www.freetype.org). All rights reserved." The exact wording is taken from the shipped license. |
| zlib or zlib-ng | tbd | `Zlib` | License text |
| libpng | tbd | `libpng-2.0` | License text |
| libtiff (and its compression libraries) | tbd | `libtiff` (plus those libraries' licenses) | License texts |
| libwebp | tbd | `BSD-3-Clause` | License text |
| OpenJPEG | tbd | `BSD-2-Clause` | License text |
| Little CMS 2 | tbd | `MIT` | License text |
| libavif (and its codecs) | tbd | `BSD-2-Clause` (plus the codecs' licenses) | License texts |
| HarfBuzz, libraqm, libxcb, brotli, and others as listed in the SBOM | tbd | per the SBOM | License texts |

`libimagequant` (GPL-3.0-or-later) is **not** in the PyPI wheels, according to Pillow's documentation. The inventory check confirms its absence.

### Runtime: transitive (required by `samsungtvws`)

`requirements/runtime.txt`, which carries hashes, is authoritative. The pins below are the current releases. The license files are from PyPI metadata and are re-checked when pinning.

| Package | Source, pin, and wheel | SPDX (license files) | Use | Required by | Obligations |
| --- | --- | --- | --- | --- | --- |
| `websocket-client` | PyPI `==1.9.2`, `py3-none-any` | `Apache-2.0` (`LICENSE` only) | dyn, redist | `samsungtvws` | License text; no NOTICE |
| `requests` | PyPI `==2.34.2`, `py3-none-any` | `Apache-2.0` (`LICENSE`, `NOTICE`) | dyn, redist | `samsungtvws` | License text **and `NOTICE`** |
| `charset-normalizer` | PyPI `==3.5.1`, `cp3xx-musllinux_1_2_{aarch64,x86_64}` | `MIT` (`LICENSE`) | dyn, redist, native | `requests` | License text |
| `idna` | PyPI `==3.20`, `py3-none-any` | `BSD-3-Clause` (`LICENSE.md`) | dyn, redist | `requests`, `yarl` | License text |
| `yarl` | PyPI `==1.25.1`, `cp3xx-musllinux_1_2_{aarch64,x86_64}` | `Apache-2.0` (`LICENSE`, `NOTICE`) | dyn, redist, native | `samsungtvws` | License text **and `NOTICE`** |
| `multidict` | PyPI `==6.9.1`, `cp3xx-musllinux_1_2_{aarch64,x86_64}` | `Apache-2.0` (`LICENSE`) | dyn, redist, native | `yarl` | License text; no NOTICE |
| `propcache` | PyPI `==0.5.4`, `cp3xx-musllinux_1_2_{aarch64,x86_64}` | `Apache-2.0` (`LICENSE`, `NOTICE`) | dyn, redist, native | `yarl` | License text **and `NOTICE`** |

`certifi` is also required by `requests`; it is recorded above as a direct dependency.

The venv is created `--without-pip`, so pip and the packages it vendors are not part of the image.

### LGPL-3.0 obligations for `samsungtvws`

These come from general knowledge of the license; qualified review is recommended.

- State prominently that the image contains `samsungtvws` under LGPL-3.0.
- Include the LGPL-3.0 and GPL-3.0 texts and the package's copyright notices.
- Keep the library replaceable. It stays an unmodified, separately installed package, and the documentation explains how to substitute another version.
- **Attach** the exact sdist to every release (D-135).
- Never modify or vendor the library, and never impose terms that restrict modifying it.

**Provenance caveat (R-04).** Versions before 2.7.0 declared inconsistent licenses: MIT metadata, but a README saying GPL-2.0 for 1.7.0–2.6.0. Excluding those versions does not settle code carried forward into 3.0.6. Phase 5 checks the 3.0.6 sdist's `LICENSE` file and source headers for retained MIT notices or a relicensing statement, and records the result. The pre-release licence review also covers this.

### Base image and OS packages

**Expected; must be verified from the image SBOM in Phase 6.**

| Component | Expected license | Notes |
| --- | --- | --- |
| `ghcr.io/home-assistant/base` (pinned tag + digest) | per SBOM | Official Alpine base with s6-overlay v3, bashio, and tzdata. Its Alpine release is not stated on a permitted page. |
| BusyBox | `GPL-2.0-only` | Copyleft; source via D-135 |
| bash (present because of bashio) | `GPL-3.0-or-later` | Copyleft; source via D-135. Not used by the app, which is a D-130 selection criterion. |
| bashio | to verify | Not used by the app |
| s6-overlay | `ISC` (to verify) | Init system |
| musl | `MIT` | C library |
| apk-tools | `GPL-2.0-only` (to verify) | Copyleft; source via D-135 |
| ca-certificates | `MPL-2.0 AND MIT` (to verify) | CA store |
| tzdata | public domain (to verify) | — |
| `python3` (exact apk pin) | `PSF-2.0` | The interpreter |
| `python3` runtime closure: OpenSSL, libffi, SQLite, expat, ncurses, xz, bzip2, mpdecimal, zlib, and possibly readline or gdbm | per package (for example `Apache-2.0` for OpenSSL, `blessing` for SQLite, `GPL-3.0-or-later` for readline and gdbm if present) | To verify from the SBOM; copyleft members use D-135 |

No OS packages beyond `python3` are planned.

### Development-only (not shipped)

| Package | Source and constraint | SPDX (as published) | Purpose |
| --- | --- | --- | --- |
| `uv` | PyPI `==0.12.19` | `MIT OR Apache-2.0` | Hash-pinned lock files (D-128) |
| `pytest` | PyPI `>=9.1,<10` | `MIT` | Tests |
| `iniconfig` | PyPI 2.3.0 (via pytest) | `MIT` | — |
| `packaging` | PyPI 26.3 (via pytest) | `Apache-2.0 OR BSD-2-Clause` | — |
| `pluggy` | PyPI 1.6.0 (via pytest) | `MIT` (license field) | — |
| `Pygments` | PyPI 2.21.0 (via pytest) | `BSD-2-Clause` | — |
| `pytest-cov` | PyPI `>=7.1,<8` | `MIT` | Coverage |
| `coverage` | PyPI `>=7.16,<8` | `Apache-2.0` | Branch coverage |
| `ruff` | PyPI `>=0.16,<0.17` | `MIT` | Lint and format |
| `mypy` | PyPI `>=2.3,<3` | `MIT` | Typing |
| `typing-extensions` | PyPI 4.16.0 (via mypy) | `PSF-2.0` | — |
| `mypy-extensions` | PyPI 1.1.0 (via mypy) | **no license metadata on PyPI**; take the SPDX identifier from its `LICENSE` file before Phase 2 | — |
| `pathspec` | PyPI 1.1.1 (via mypy) | classifier only: MPL-2.0; take the SPDX identifier from its `LICENSE` file before Phase 2 | — |
| `librt` | PyPI 0.15.0 (via mypy) | `MIT` | — |
| `ast-serialize` | PyPI 0.11.2 (via mypy) | `MIT` | — |

### Build and CI tooling (not shipped)

| Tool | Version | SPDX | Recorded and approved before |
| --- | --- | --- | --- |
| Docker Buildx | tbd | tbd | Phase 6 |
| QEMU user-mode emulation | tbd | tbd | Phase 6 |
| SBOM generator (for example Syft) | tbd | tbd | Phase 6 |
| Home Assistant builder composite actions (`build-image`, `publish-multi-arch-manifest`) | tbd | tbd | Phase 9 |
| Cosign | tbd | tbd | Phase 9 |

The documentation for these tools is largely GitHub-hosted, so it is read only once GitHub access is approved.

### Considered and not proposed

| Package | Reason |
| --- | --- |
| `httpx` 0.28.1 (`BSD-3-Clause`) | Would add a second HTTP stack. The stable line is about 21 months old, and the 1.0 pre-releases are an API rewrite without license metadata. |
| `pip-tools` 7.6.1 | Its PyPI license field is only "BSD", not an SPDX expression. `uv` is preferred. |
| Alpine `py3-pillow` | Older than the PyPI release, and links GPL-3.0-or-later `libimagequant`. |
| lxml, BeautifulSoup | Not needed (D-127). |
| `samsungtvws` extras (`async`, `encrypted`, `cli`) | Not needed. |

## Risk register

Likelihood and impact: H = high, M = medium, L = low.

| ID | Risk | L / I | Mitigation | Residual / owner |
| --- | --- | --- | --- | --- |
| R-01 | Google Arts & Culture has no documented API. Google's Terms prohibit automated access that violates `robots.txt` (which disallows `/api/*`), bypassing protective measures, and using the services to violate intellectual-property rights. Partners hold the image rights. | H / H | Not in the beta. Building it requires amending `LEGAL_BOUNDARIES` first (D-120). | User (Q-01) |
| R-02 | Google Arts & Culture page formats change without notice (applies only if the connector is ever built) | H / M | Tolerant parser, `source_failed`, fixtures, bounded requests | — |
| R-03 | The Samsung art-mode protocol is undocumented and changes with firmware. The library's TLS and certificate behaviour is unknown, so trust-on-first-use or pinning is to be decided in Phase 5. The pairing token's scope is also undocumented; it is assumed to grant television control only. | M / H | Isolated, pinned library behind the port; capability check; marker-based classification; Phase 8 validation on the user's model | Phase 5/8 |
| R-04 | `samsungtvws` has a single maintainer, its 3.x art API is undocumented on PyPI, it carries LGPL obligations, and its **inherited licence provenance** is uncertain | M / M | Hash pin; contract tests; Q-15; D-135; Phase 5 `LICENSE` and source-header check | Phase 5, licence review |
| R-05 | Bing: undocumented endpoint; `robots.txt` (`*` group) disallows the image path `/th?` (the archive rule's spelling differs, see Q-17); the Services Agreement restricts the photos | H / H | Not planned | User (Q-17) |
| R-06 | The loading state depends on the Supervisor Running entity, which is disabled by default and has an undocumented polling interval. Short runs may never show the loading state. | M / M | Guaranteed exit bound; timer-based fallback (`T` + 35 s) that does not need an on→off transition (§16.3). Phase 8 cases: a run under 10 s, a mistyped slug, and a non-admin tap. | Phase 8 (Q-09, Q-19) |
| R-07 | Local File allowlisting (an inference from two documentation pages) and camera cache refresh are undocumented; a custom `media_dirs` may differ | M / M | Phase 8 validation of the candidate remedies (update-entity, alternating `update_file_path`, media-source card); the chosen remedy is recorded here | Phase 8 |
| R-08 | Vulnerabilities in the image decoders | M / H | Header limits; format allowlist; unprivileged, memory-limited worker; scrubbed environment; bytes-only results; prompt updates | Ongoing |
| R-09 | Memory pressure during decode on the Green | L / M | Pixel caps of 64 MP (JPEG, draft-decoded) and 40 MP (PNG); colour-space work after resizing; 1 GiB `RLIMIT_AS` (virtual). The worst-case resident peak, including one full-resolution conversion or crop copy, is estimated at ≈ 450–550 MiB. The measured peak is recorded in Phase 3/8. | Phase 3/8 |
| R-10 | Home Assistant platform churn (app rename, builder deprecation, action renames, 2026.6 slug-syntax-only validation) | M / M | Follow current documentation; re-check at Phase 6 and Phase 9 | Phase 6/9 |
| R-11 | Pairing friction: prompts on every connection, and prompt timeouts | M / M | Token persistence; 30 s wait; self-healing reset; *First Time Only* in the documentation | Documentation |
| R-12 | Television off, in standby, or on another subnet → `tv_unreachable` | M / L | Actionable messages; documented network requirement | Documentation |
| R-13 | Restrictive Art Institute filter combinations or small local folders are exhausted by history → frequent `no_match` | H / L | Distinct `no_match` hints; exhausted-page cache; documented behaviour | Accepted |
| R-14 | Branding: "Frame" is part of Samsung's product naming | M / M | D-101 review; factual compatibility wording only | User (D-101) |
| R-15 | Watchdog `os._exit` skips normal cleanup. An orphaned television worker could otherwise finish an upload after the run has reported its outcome. | L / M | The watchdog kills the worker process group first; `PR_SET_PDEATHSIG`; RAM-backed `/tmp`; startup sweep; timing test | Accepted |
| R-16 | Supervisor treatment of exit codes and **Watchdog restarts** of `once` apps is undocumented | M / M | D-133: all classified outcomes exit 0; the documentation says to keep Watchdog off | Phase 8 (Q-07) |
| R-17 | The image redistributes copyleft OS packages: GPL-2.0 (BusyBox, apk-tools), GPL-3.0-or-later (bash; possibly readline or gdbm), plus LGPL (`samsungtvws`) | M / M | Image SBOM; D-135 source attachment; minimal OS packages; copyleft surface as a D-130 criterion | Phase 6/7 licence audit |
| R-18 | Provider terms or rate limits violated by accident | L / H | Allowances; pacing; stop on HTTP 403/429; cache; honest headers | Phase 4 review |
| R-19 | Art Institute renditions (1686 px wide) look soft when upscaled by up to ≈ 2.28× in `contain` mode; images can be unpublished | H / M | Honest documentation; an HTTP 404 moves to the next candidate; Cleveland (near-4K, ≈ 1.13×) next | Accepted for the beta |
| R-20 | Provider documentation drifts | M / L | Re-verify live documentation at the start of Phase 4 | Phase 4 |
| R-21 | Home Assistant's media browser may not be able to upload into `/media/frame_gallery/library` (assumed, not documented) | M / M | The app creates the folder; the `no_match` hint names the location; Phase 8 verifies | Phase 8 |

## Open questions

### Phase 0 questions: proposed answers

| Phase 0 question | Proposed answer |
| --- | --- |
| Runtime filter changes: helpers, Ingress, or options only? | Static options plus optional documented helpers. Ingress not planned; companion integration deferred (D-126). |
| How should metadata caches be bounded and invalidated? | Per-provider JSON: ≤ 1 000 entries, ≤ 2 MiB, TTL ≤ 7 days; expired entries evicted first, then LRU; discarded on corruption. The beta uses it only for Art Institute counts and page hints (§13.4). |
| Which source identifiers are stable enough? | Local media: `local:fp:<sha256…>` (D-118). Art Institute of Chicago: `aic:<artwork id>` (§9.4). Any later adapter uses the provider's documented identifier, validated against a pattern. |
| What Google Arts & Culture access mechanism is appropriate? | None was found that respects its terms without an official API. See Q-01. |
| Should pairing tokens remain only in private app data, and what is the recovery flow? | Yes: `/data/tv/`, mode `0600`, current television address only, excluded from backups through `backup_exclude` (expected; verified in Phase 8), and installed atomically by the parent. Recovery is self-healing: a rejected token is deleted and the next run prompts again (§12.2). |
| Smallest compelling public beta? | D-120. |

### New questions requiring a decision

| ID | Question | Recommendation | Needed by |
| --- | --- | --- | --- |
| Q-01 | Google Arts & Culture has no documented API. Its `robots.txt` permits public HTML and disallows `/api/*`; the image host's rules were not checked. The real conflict is with Google's Terms (automated access against `robots.txt`, bypassing protective measures, using the services to violate intellectual-property rights) and the partners' image rights. Options: (a) drop it; (b) defer until an official API exists; (c) amend the `LEGAL_BOUNDARIES` access-terms rule, check the image host's rules, then build an HTML-only experimental connector under §9.5. No open-access API or image licence was found for the Museum of Modern Art or the Musée d'Orsay (aggregator coverage not yet checked). | (b) Defer. Ship the Art Institute of Chicago instead (D-132). | Before Phase 4 |
| Q-02 | Does the specification's "60 seconds total" mean the selection phase (proposed) or the whole run? This is a specification interpretation. | Selection phase; the whole run is `S` + 205 s (D-114) | Before Phase 2 |
| Q-03 | Approve the thresholds: strict ±4 %, square band 0.95–1.053, upscale limit 2.5×? | Approve; revisit after Phase 8 | Phase 4 |
| Q-04 | Local identity: quick fingerprint only (proposed), or also a full-content hash? | Fingerprint only | Phase 4 |
| Q-05 | JPEG parameters for the television (quality 90, standard subsampling, 15 MiB ceiling) | Start value; tune in Phase 8 | Phase 8 |
| Q-06 | A user-facing way to reset history or re-pair, beyond the automatic token reset? | Not in the beta; reinstall is the reset path | Phase 6 |
| Q-07 | Confirm the D-133 policy in Phase 8: how the Supervisor shows `once`-app exits, and whether the app's Watchdog restarts them | Keep D-133; observe in Phase 8 | Phase 8 |
| Q-08 | Default `source`? | `art_institute_chicago`, which works immediately | Phase 6 |
| Q-09 | Is enabling the disabled-by-default Running sensor acceptable? If the Phase 8 latency is poor, the deliverable for acceptance item `G1` becomes "card + script + timer". Is that acceptable? | Accept both | Phase 6/8 |
| Q-10 | Should the parent process also run unprivileged? This needs an ownership layout for `options.json` (mode `0600`), `/data`, and the preview folder. | Evaluate in Phase 6; the workers are unprivileged already | Phase 6 |
| Q-11 | In `cover` mode with strict format on, allow fallback by forcing `contain` for fallback images? | Follow the specification (no fallback in `cover` mode) | Phase 4 |
| Q-12 | Accept rejecting IPv6 global addresses, the container networks, and the Supervisor network for `tv_host`? | Accept | Before Phase 2 |
| Q-13 | The final public repository URL, which determines the observed slug in the dashboard YAML | Decide with D-101 | Phase 9 |
| Q-14 | Initial vocabularies: which colours, departments, and styles or periods? | Small curated lists after the Phase 4 mapping | Phase 4 |
| Q-15 | How to confirm the `samsungtvws` 3.0.6 art API (D-104)? | Option 1: inspect the installed package only | Before Phase 5 |
| Q-16 | Does the television accept the app through the host's NAT, without `host_network`? | Expect yes; go/no-go check in Phase 8. Fallback: `host_network: true`, which lowers the rating. | Phase 8 |
| Q-17 | Should Bing be built? No `robots.txt`-compliant implementation exists: the `*` group disallows the image path `/th?` (only `msnbot-media` is allowed it). This rule is decisive. The archive rule is spelled `/HpImageArchive.aspx`, while the endpoint is commonly written `HPImageArchive.aspx`, and `robots.txt` matching is case-sensitive. No official API exists. The Services Agreement limits the photos to non-commercial personal use, with downloading or building products allowed only as authorized or permitted by law. Overriding this would require amending the `LEGAL_BOUNDARIES` rule. | Do not build. Remove it from the specification's providers. | Before Phase 4 |
| Q-18 | Specification amendments, to be made in the same commit that records the decisions. The exact clauses: **(1)** `PRODUCT_SPEC` Google Arts & Culture subsection: the MoMA/Orsay clause; move its "landscape-only by default" and "strict near-16:9 by default" to *Filter inputs* or *Selection limits*. **(2)** `PRODUCT_SPEC` Bing subsection. **(3)** `TASKS.md` Phase 4, bullets 3–4. **(4)** `PRODUCT_SPEC` lifecycle order, steps 9/10 (D-113). **(5)** the meaning of "60 seconds total" (Q-02). | Amend as listed | Before Phase 4 (items 4–5 before Phase 2) |
| Q-19 | `hassio.app_start` is admin-only. Must non-admin household members be able to start the app? The alternative is the Running **switch**, which is disabled by default and stops a run if toggled mid-run. | Document the admin requirement. In Phase 8, test a script, the switch, and `continue_on_error` with a non-admin user and with a mistyped slug. | Phase 8 |
| Q-20 | Specification interpretation: the "30 dimension probes" budget applies to **remote** probe requests, and local header reads are bounded separately (500 files). Neither beta source needs remote probes. | Approve | Phase 4 |
| Q-21 | How does the unpublished app reach the Green for Phase 8? Options: (a) the user copies the folder into `/addons` through a file-share app; (b) a temporary private repository; (c) a development image push. Each needs approval, and the route determines the development slug. | (a), because it touches no external service | Before Phase 8 |
| Q-22 | The project-owned contact email for courtesy headers (the Art Institute's `AIC-User-Agent`, D-119). It is needed before any live Phase 4 request; tests use a placeholder. | Decide before the first approved observation request | Phase 4 |

## Review findings not adopted (Phase 1 review)

The Phase 1 multi-lens review produced 98 raw findings. The adjudicator confirmed 58, which are incorporated. It listed 7 entries as not adopted: 6 rejections and 1 severity downgrade. They are listed here so they can be challenged:

1. **Pin third-party GitHub Actions to commit SHAs and apply least-privilege job permissions.** Rejected as general CI hardening, not a specification gap. It belongs to the Phase 9 release work (§17.3), where it is expected to be applied.
2. **Log local media by fingerprint only, since filenames are private data.** Rejected: the log is the user's own app log, and the specification's list of forbidden log content does not cover the user's own filenames. Warnings need the path to be actionable.
3. **"Security rating 6" wording.** Rejected: 6 is achievable and is the scale maximum. The nuance that Ingress would also reach 6 does not affect any decision.
4. **The Ingress comparison overstates "session handling".** Rejected as immaterial: the other listed costs, and the one-shot incompatibility, still hold. The row now says "request handling".
5. **Appendix A item `C4` should name the verifying provider.** Rejected: it already names the counting fake gateway.
6. **Drop the `.bak` generation as a simplification.** Rejected as a design preference. The real defects around `.bak` were fixed.
7. **Rate the probe-limit, watchdog-orphan, and memory findings as major.** Downgraded to minor rather than rejected: a dead option, an orphan that needs a second failure, and rare near-cap images. All three were fixed.

