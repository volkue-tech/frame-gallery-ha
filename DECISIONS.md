# Decision log

Status values:

- `accepted`: binding.
- `proposed`: awaiting approval by the user, and by Codex where `TASKS.md` requires it.
- `superseded`: replaced by a later decision.
- `split`: accepted in part and proposed in part; the decision text says which part is which.

Phase 1 added:

- decisions D-106 onward;
- the proposed dependency inventory;
- the risk register;
- the open questions.

Each architecture decision gives its rationale at the `ARCHITECTURE.md` section named in brackets.

This version (revision 2) records the user decisions and corrections from the **Codex review of commit `d42adf5`** (see *Review records*).

The **user's approval of Phase 3 on 2026-09-27** accepted D-108, D-112, D-115, D-124, D-127, D-131, D-134, the Phase 3 adapter details of D-132 and D-136, and D-141 to D-145. It amended D-119 and resolved Q-14 and Q-22. The documentation re-check at the start of Phase 3 is recorded in D-146.

The **Phase 3 gate on 2026-09-27** accepted D-146 to D-152 and resolved Q-25 with option (a). Phase 3 is complete; Phase 4 has not started.

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

Rationale: distinct, descriptive, and not tied to a predecessor repository name. Branding and trademark wording need review before release (R-14).

The provisional internal identifier `frame_gallery` is **accepted** (D-138), and a later rename would be mechanical.

### D-102 — Project license

Status: **accepted** (Codex review of `d42adf5`, user decision).

The Apache License 2.0 applies to independently authored project code.

**Scope.** Apache-2.0 covers the **project-owned source code only**. It does not cover the complete distributed container image, which also contains third-party components under their own licences. These include:

- GPL-3.0-or-later `libimagequant`, bundled in the Pillow wheels;
- LGPL-2.1-or-later FriBiDi;
- LGPL-3.0 `samsungtvws`;
- GPL-2.0 OS packages such as BusyBox.

The inventory below lists them all.

Rationale: permissive reuse with an explicit patent grant. Third-party dependencies keep their own licenses. The `LICENSE` file is added when publication is prepared (Phase 9).

### D-103 — Implementation language

Status: proposed (refined in Phase 1).

**Decision:**

- Python, with code compatible with **CPython 3.12–3.14**. CI runs all three versions.
- The container runs the Alpine `python3` of the chosen base image, pinned to an exact version.

**Rationale:**

- 3.12 is security-only.
- All runtime dependencies publish `musllinux_1_2` wheels for 3.12–3.14.
- `samsungtvws` 3.0.6 and Pillow 12 need Python ≥ 3.10.

### D-104 — Samsung transport

Status: **accepted for design.** The inspection method was approved in the Codex review. The dependency row is approved before Phase 5.

**Decision:**

- Use `samsungtvws` **3.0.6** (LGPL-3.0, Python ≥ 3.10), core install only.
- Import it only in the isolated TV worker task (D-109).
- Establish the adapter surface **only by inspecting the installed 3.0.6 distribution**: its public signatures and docstrings in a local virtual environment, without GitHub access (Q-15, resolved).

**Phase 1 findings from PyPI.** The release, license, and requirement facts were independently verified. The maintainer, pairing, and subnet notes were not re-verified.

- Since 3.0.0, the README documents no Python art API. The 2.7.2 README named `art().supported()`, `upload(data, file_type='JPEG')`, `select_image(content_id, show=…)`, and `get_artmode()`. No README documents a "no matte" value or a client-name parameter. The constructor form with `port=8002` and `token_file` appears only in READMEs up to 2.7.2.
- No exceptions or timeouts are documented.
- Newer TVs prompt on every connection unless *First Time Only* is set.
- TVs refuse connections from other subnets. The app starts without `host_network`, and Phase 8 verifies connectivity (Q-16).
- The package has a single maintainer, and its releases come in bursts.

**Why a library rather than an own implementation.** Samsung does not document Art Mode or the local protocol, and SmartThings has no art capability. A maintained library under a known license is safer than a new protocol implementation, which would also be the most sensitive area under `LEGAL_BOUNDARIES`.

### D-105 — Release architectures

Status: proposed

Publish `aarch64` and `amd64` first. Add other architectures only after successful builds and explicit support decisions.

Phase 1 note: Home Assistant currently supports only these two app architectures (32-bit support ended with release 2025.12).

## Architecture decisions (Phase 1)

### D-106 — Synchronous core, phase budgets, watchdog [§4.3, §7]

Status: **accepted** (bounded execution and cleanup; Codex review).

**Decision:**

- A single run thread, with no `asyncio`.
- Phase deadlines come from the normative 120 s budget table (D-114), and every blocking call is clamped.
- `Allowance` counters bound the loops.
- A watchdog kills the worker process group and exits at `T + 10 s`.
- DNS resolution runs in a fresh daemon thread per lookup, joined with a clamped timeout. The number of abandoned lookup threads is bounded by the request allowances.

### D-107 — Ports and adapters with an enforced import boundary [§5, §20.2]

Status: proposed

**Decision:** Third-party imports are confined to three places:

- the `imaging` worker tasks (Pillow);
- the `tv` worker task (`samsungtvws`);
- `net.transport` (`urllib3`, `certifi`).

The parent never imports Pillow or `samsungtvws`. An import-boundary check enforces this.

### D-108 — Guarded gateway for all provider traffic [§10, §7.5]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Decision:** The gateway enforces:

- exact or label-boundary host rules;
- HTTPS on port 443 only;
- one resolution, with every address checked as global;
- connection to the validated IP, with SNI and a peer check;
- `CERT_REQUIRED` with TLS ≥ 1.2 and `certifi`;
- at most 3 re-validated redirects;
- identifier `fullmatch` and percent-encoding;
- caps on decoded bytes;
- per-request totals (metadata 10 s, probe 5 s, download 20 s);
- per-address connect timeouts and re-clamped reads;
- pacing;
- no cookies, proxies, or credential files.

### D-109 — Isolated, unprivileged workers [§11.3, §12]

Status: proposed. The target design is unchanged; its delivery is sequenced by D-139.

**Decision.** All image inspection, decoding, rendering, and encoding runs in a spawned worker, and so does the whole TV interaction. Each worker:

- drops to user 65534 with no supplementary groups;
- then sets `PR_SET_PDEATHSIG`;
- sets its umask and `RLIMIT_AS`: 1 GiB for the image worker, 512 MiB for the TV worker, with CPU limits;
- installs logging and Pillow limits before any third-party import;
- sees only the allowlisted environment;
- runs in its own process group;
- returns markers and results as bytes-only JSON.

The parent chooses every path, validates `delivery.jpg`, and computes the SHA-256. The TV worker emits progress markers.

**Delivery.** The complete bootstrap, including the privilege drop, is delivered with the process executor in Phase 5. Enforce-mode AppArmor and final verification come in Phase 9 (D-139).

### D-110 — Atomic state, pre-staging, bounded records [§13]

Status: **accepted** (atomic writes and bounded state; Codex review).

**Decision:**

- **State files.** Plain JSON under `/data`:
  - `history.json`: confirmed sent and displayed works;
  - `upload_ledger.json` (D-137);
  - `current.json` and `last_run.json`;
  - a per-provider cache.
- **Write primitive.** One primitive for every write:
  - directory-descriptor operations with `O_NOFOLLOW`;
  - `O_EXCL` random temporary names;
  - `fsync`, then rename, then directory `fsync`.
- **Pre-staging.** The next history generation is written before DELIVER, and the ledger intent is committed there too. After `selected`, recording history is a single rename.
- **Backups.** History and the ledger keep a best-effort `.bak`, which covers unparseable or schema-invalid primaries.
- **Reader.** Primary, then `.bak`, then empty with a warning. Only parse or schema failures are quarantined (at most 3 files). A newer file version gives `state_error` before the TV is touched.
- **Locking.** A non-blocking lock; contention gives `already_running`.

### D-111 — Preview in `/media` through a Local File camera [§13.5, §16.3]

Status: **accepted** as the primary beta design (Codex review).

**Decision:**

- The exact delivered JPEG is published atomically under `/media/frame_gallery/preview/`. Publication is refused if any path component is a symbolic link.
- A UI-created Local File camera and a `picture-entity` card display it.
- **Platform basis.** Home Assistant OS creates `/media` without user configuration, and configured or default media directories are in the default external-directory allowlist. A normal installation therefore needs no `configuration.yaml` edit, no configuration-folder mapping, no SSH, and no manual file changes.
- Freshness is governed by D-140.

### D-112 — Static options with optional helper overrides [§15.3]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Decision:**

- Static options always work.
- The optional `source_helper`, `department_helper`, `style_helper`, and `color_helper` are each read with at most one request:
  - ≤ 4 reads in total, each ≤ 3 s, within the 10 s configuration window;
  - `fullmatch` validation, no redirects or retries;
  - `Authorization` sent only to `http://supervisor`;
  - a 64 KiB cap, and only the `state` field is used.
- Any failure falls back to the static value, with one warning.
- The app writes nothing to Home Assistant.

### D-113 — Record history before publishing the preview [§4.1]

Status: **accepted** (Codex final gate review of `9352e77`; Q-18 item 4 is resolved and `PRODUCT_SPEC.md` is amended).

**Decision:** Record the confirmed sent history immediately after `selected`, then publish the preview.

**Rationale:** Duplicate prevention no longer depends on this order, because the upload ledger (D-137) excludes the work once it is uploaded. The order only makes history slightly more robust.

### D-114 — Budget decomposition [§7.2]

Status: **split.**

- **Accepted** in the Codex review, replacing the earlier 265 s proposal: the 120 s total, the 10/60/40/10 split, clamping of all timeouts, the 70 s no-match bound, and 30 remote dimension requests with a separate local allowance.
- **Proposed**, to be confirmed by Phase 2, 5, and 8 measurements: the sub-budgets, the allowances, the `RLIMIT_AS` values, and the upload allowance. The 150 s timer helper was accepted in the final gate review (Q-09).
- **Phase 2 result.** The phase arithmetic is confirmed with a fake clock: the phases sum to 120 s, every child deadline stays within its phase and the total, and `no_match`, `source_failed`, and `image_failed` end by 70 s even when every step uses its whole budget. Phase 2 has no real providers, workers, or television, so the real-time measurements move to Phase 5 (preparation under `RLIMIT_AS`) and Phase 8 (the Green and the TV).

The tables in `ARCHITECTURE.md` §7.2 are normative once approved.

**Decision.** The default hard total deadline is **`T` = 120 s**:

| Phase | Budget | Notes |
| --- | --- | --- |
| CONFIGURE + RESOLVE_FILTERS | **10 s** | IPv4 validation needs no DNS; up to 4 helper reads of ≤ 3 s each |
| Content window: SELECT + ATTEMPT + PRE-STAGE | **60 s** | Discovery ≤ 30 s; per attempt, download ≤ 20 s and prepare ≤ 15 s; the last 2 s are reserved for PRE-STAGE or a no-delivery FINISH, so `no_match`, `source_failed`, and `image_failed` all exit **by 70 s** |
| DELIVER | **40 s** | Connect ≤ 5 s; pairing wait ≤ 20 s |
| FINISH | **10 s** reserved | |
| Shutdown allowance | 10 s | Watchdog at 130 s |

**Allowances:**

- a shortlist of 2;
- 150 candidates after exclusion;
- 15 metadata requests;
- **30 remote dimension requests** (Q-20);
- 20 000 directory entries at depth ≤ 4;
- 300 local header inspections.

**Per-request limits:**

- metadata 10 s, probe 5 s, download 20 s, helper 3 s;
- connect ≤ 5 s and read ≤ 10 s, both re-clamped;
- DNS ≤ 3 s.

Every timeout is clamped to the remaining total. The worker `RLIMIT_AS` is 1 GiB for the image worker and 512 MiB for the TV worker. The dashboard timer indicator is **150 s** (`T` + 30 s).

The beta has no user-facing time option. An advanced total-deadline option may come later, validated within a safe range, and the standard instructions use 120 s.

### D-115 — Retry and pacing policy [§7.4]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Decision:**

- **Metadata GETs.** At most 1 retry, and only for a connect error, 502/503/504, or a 429 with `Retry-After` ≤ 5 s (seconds or HTTP-date). The wait is `max(Retry-After, 1 s)` plus jitter, and the retry is skipped if it would exceed the deadline.
- **403/429 stop.** Any 403, or a 429 that is not retried, from any host of a provider stops all requests to that provider for the run. Remote shortlisted candidates are then not attempted.
- **No retries** for probes, downloads, helper reads, uploads, or selects.
- **TV reconnect.** At most 1, only before `upload_started`, and never after a pairing timeout.
- **Pacing.** A `min_interval` of 1 s for both the Art Institute and Cleveland.

### D-116 — Shape and quality thresholds [§8.1]

Status: **accepted** (Codex final gate review; Q-03).

**Decision:**

- **Square band:** 0.95 ≤ w/h ≤ 1/0.95.
- **Strict near-16:9:** ±1 % in log ratio, `abs(ln(r / (16/9))) ≤ ln(1.01)`, about 1.760–1.796. This threshold may be revisited after Phase 8 visual testing.
- **Quality:** reject any work whose upscale factor exceeds 2.5×.

All values are measured after EXIF orientation, on the rendition that will be delivered.

### D-117 — Fallback permission [§8.2]

Status: **accepted** (Codex final gate review; Q-11).

**Decision:** Fallback is permitted only when `landscape_only` is on and `fit_mode` is `contain`. There is **no fallback in `cover` mode**, and a fallback image is never cropped.

### D-118 — Local media identifier [§9.3]

Status: **accepted** (Codex final gate review; Q-04)

**Decision:** `local:fp:<sha256(size ‖ first 64 KiB ‖ last 64 KiB)>`, plus the fingerprints of the last 10 previews.

### D-119 — Honest User-Agent [§10]

Status: **accepted** with the amendment below (user approval of Phase 3, 2026-09-27).

**Decision:**

- ~~The User-Agent is `FrameGallery/<version> (+<project URL>)`.~~ Superseded by the amendment below.
- Provider courtesy headers, such as the Art Institute's `AIC-User-Agent`, carry the project name and a project-owned contact email (Q-22), never user data.
- There is no browser impersonation.

**Amendment (user decision, 2026-09-27).**

- No invented or not-yet-existing project URL is used. Until a public project URL is decided (Q-13), the User-Agent is `FrameGallery/<version> (contact: volkue@gmail.com)`.
- The Art Institute's `AIC-User-Agent` uses the project contact: `FrameGallery/<version> (volkue@gmail.com)`.
- Tests keep using a clearly recognizable placeholder contact, never the real address.
- Before publication (Phase 9), both headers switch to the real public repository URL.
- The real address is transmitted only in a later, explicitly approved live request (Q-22). Phase 3 makes no live request.

### D-120 — First public beta scope [§22]

Status: **accepted** as amended in the Codex review. `PRODUCT_SPEC.md` is amended accordingly.

**Included:**

- **Sources:**
  - local media;
  - the **Art Institute of Chicago** (D-132), the default remote source (Q-08, accepted);
  - the **Cleveland Museum of Art** (D-136).
- **Filters:** source, department, style/period, and colour, with the capability matrix and visible reporting of unsupported filters (D-124); optional helpers. *Amended at the Phase 3 gate (D-146, D-152; Q-25, option (a)):* the first beta offers Cleveland departments and periods for both museums. It offers no style and no colour filter: the style option offers periods only, and the colour option accepts only "any" or a no-filter synonym (`all`, `random`, `none`, or an empty value).
- **Selection:** landscape-only, strict with fallback, the upscale rule, and `contain` (default) or `cover`.
- **State:** atomic, pre-staged history; the TV-upload exclusion ledger and quarantine (D-137); an atomic preview; a small cache; self-healing pairing.
- **Deliverables:** documentation and dashboard YAML; images for `aarch64` and `amd64`.

**Deferred:**

- a companion integration;
- multi-source rotation;
- Europeana, Rijksmuseum, and The Met;
- Cleveland colour filtering by local analysis (Q-24);
- an advanced total-deadline option;
- hostname or IPv6 TV addresses;
- Collection Image support;
- remote-probe machinery;
- matte selection;
- helper auto-provisioning;
- an unprivileged parent process (Q-10);
- a configurable library folder;
- local colour and style filters;
- a history reset (Q-06);
- more architectures.

**Excluded or not planned:**

- Google Arts & Culture (Q-01, resolved) and Bing (Q-17, resolved). Their researched status is kept in `ARCHITECTURE.md` §9.4 and `PRODUCT_SPEC.md`. Undocumented or `robots.txt`-incompatible access is never implemented.
- Ingress.
- Managing the TV's image storage.

### D-121 — Image safety limits [§11]

Status: proposed

**Decision:**

- Width and height ≤ 20 000 px each.
- Pixel limits: ≤ 64 MP for JPEG and ≤ 40 MP for PNG, both checked from the header before decoding. Pillow's global limit is set to 64 MP, and the PNG cap is an explicit check.
- Decompression-bomb warnings are raised as errors; only JPEG and PNG are opened.
- Downloads are capped at 40 MiB.
- The image worker runs under a 1 GiB `RLIMIT_AS` ceiling (virtual memory). The estimated worst-case resident peak is ≈ 450–550 MiB.

### D-122 — Colour management [§11.1]

Status: proposed

**Decision:**

- Convert embedded ICC profiles to sRGB; assume sRGB otherwise.
- Output an 8-bit RGB baseline JPEG without EXIF.
- Normalize palette and bit depth before resizing. Colour-space conversion and alpha compositing happen after resizing.

### D-123 — App options [§15.1]

Status: proposed. The defaults are **accepted** (Codex review): `contain`, with no crop; landscape-only on; strict near-16:9 on. The default `source` is `art_institute_chicago`, which is **accepted** in the final gate review (Q-08).

**Decision.** The options are those in `ARCHITECTURE.md` §15.1:

- `tv_host`: an IPv4 literal, required;
- `source`: `art_institute_chicago`, `cleveland_museum_of_art`, or `local_media`;
- `department`: namespaced `aic_…` or `cma_…`;
- `style`: `style_…` or `period_…`;
- `color`;

  *Amended at the Phase 3 gate (D-146, D-152; Q-25, option (a)):* vocabulary version 1 ships only `cma_…` departments and `period_…` keys, and no `aic_…`, `style_…`, or `color_…` key. `color` therefore accepts only "any" or a no-filter synonym (`all`, `random`, `none`, or an empty value) in the first beta. See `ARCHITECTURE.md` §15.1.
- `landscape_only`, `strict_tv_format`, `fit_mode`, `background_color`;
- four optional `*_helper` options;
- `log_level`.

There is no time-limit option and no library-path option.

### D-124 — Filter model, vocabularies, and capability matrix [§9.2, §15.2]

Status: **accepted** (user approval of Phase 3, 2026-09-27). The documentation re-check amends the Art Institute's column of the matrix (D-146); vocabulary version 1 and the narrowed matrix are implemented (D-152).

**Decision:**

- **Four distinct dimensions:**
  1. source/museum, which selects the provider (a department is never called a museum);
  2. department/collection, namespaced by source;
  3. style/period;
  4. colour.
- **Capability matrix**, published in `DOCS.md` and in the option descriptions:
  - Art Institute: department, style, period, and colour. *Amended by D-146: period only in the beta, because the documentation does not name the department and style values or the colour object's members.*
  - Cleveland: department and period. Style and colour are unsupported in the beta.
  - Local media: none of the four.
- **Visible reporting.** A filter that does not apply to the selected source is ignored for the run and reported in three places:
  - a WARNING;
  - `ignored_filters` in the summary line;
  - `last_run.json`.
- **Helper values.** A helper value that normalizes to no vocabulary key falls back to the static value, with one warning. A known key that does not apply to the selected source overrides the static value, and is then ignored and reported like a static value.
- **Vocabularies.** Versioned, with deterministic normalization. The final lists are fixed in Phase 3 (Q-14, resolved: small, curated lists from documented values only; D-146).

### D-125 — Television address rules [§15.4]

Status: **accepted**. The IPv4 literal was accepted in the Codex review, and the ranges in the final gate review (Q-12).

**Decision:**

- `tv_host` must be an **IPv4 literal in an RFC 1918 private range**: `10/8`, `172.16/12`, or `192.168/16`.
- **Rejected:** `169.254/16` link-local addresses; loopback, unspecified, multicast, and broadcast addresses; the container's own interface networks and the Supervisor's internal network.
- No DNS is involved, and the validated literal goes to the TV worker.
- Hostnames and IPv6 are deferred.
- The user's Phase 8 test value is `192.168.178.30`. It is entered in the options only, never shipped as a default, and never hard-coded.

### D-126 — Dashboard filter approach [§16]

Status: proposed

**Decision:**

- **Beta:** static options plus documented helpers.
- **Ingress:** not planned.
- **Companion integration:** deferred.

### D-127 — Standard-library parsing only [§18.2]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Decision:** Parse `json`, and `html.parser` only if a provider is ever approved that needs it. No lxml or BeautifulSoup.

### D-128 — Reproducible builds and update policy [§17]

Status: **accepted**, including `uv` as the development lock tool (Codex review).

**Decision:**

- **Lock file** generated with `uv pip compile --generate-hashes` (`uv` 0.12.19, `MIT OR Apache-2.0`, development only). *Phase 2 proposes an amendment (D-142): a project `uv.lock` with hashes, and `requirements/runtime.txt` exported from it with `uv export`. The install rules below are unchanged.*
- **Installs** use `--require-hashes --no-deps --only-binary=:all:`.
- **Pinning:** the base image by tag and digest, and `python3` by exact apk version.
- **Reviews:** monthly, and immediately on advisories.
- **Upgrades** need the full test suite and an updated inventory. Pillow and `samsungtvws` are upgraded only in dedicated commits.

### D-129 — App configuration and AppArmor profile [§17.1, §17.6]

Status: proposed

**Decision:**

- **`config.yaml`:**
  - `startup: once`, `boot: manual_only`, `init: false`;
  - `arch: [aarch64, amd64]`;
  - `stage: experimental` until Phase 8;
  - `homeassistant: "2026.2.0"`, which is **not** raised for Collection Image;
  - `homeassistant_api: true`. This grants Core REST and WebSocket access; the app limits its own use to ≤ 4 state GETs;
  - `tmpfs: true`, `timeout: 20`;
  - `map: [{type: media, read_only: false}]`, narrowed by AppArmor;
  - `backup_exclude: cache/**, state/quarantine/**, tv/**`;
  - no `host_network` (Q-16).
- **Custom `apparmor.txt`:**
  - `/media` read-only, except read-write on `/media/frame_gallery/preview/**`;
  - creation allowed only for `/media/frame_gallery/`, `preview/`, and `library/`;
  - read-write on `/data/**` and `/tmp/**`;
  - only the paths spawn needs;
  - `inet` and `inet6` stream and dgram sockets only;
  - minimal capabilities.

  It runs in **complain mode in Phases 6–8** and is **enforced and verified in Phase 9** (D-139).
- **Security rating:** 6.

### D-130 — Container base image and build [§17.2]

Status: proposed

**Decision:**

- **Base image:** `ghcr.io/home-assistant/base`, pinned by tag and digest.
- **Build:**
  - multi-stage;
  - `python3` pinned to an exact apk version;
  - a venv created `--without-pip`, from hash-pinned, binary-only wheels;
  - Pillow from PyPI wheels only.
- **Labels:**
  - `io.hass.arch` from `BUILD_ARCH`, falling back to `TARGETARCH`;
  - `io.hass.version` from a required `ARG`;
  - the OCI `licenses` label omitted.
- **Tooling:** Buildx for builds; the Home Assistant builder actions and Cosign for releases.
- **Selection criteria:** the official guidance, reproducibility, and copyleft surface.

**Open verification (Phase 6).** The image pull needs approval. Then:

- (a) the Alpine and Python versions. Once the Python version is fixed, repeat the Pillow wheel SBOM inspection against the exact two runtime wheels; that result is authoritative for the inventory;
- (b) the container stops when `CMD` exits;
- (c) a stop request delivers SIGTERM with enough grace;
- (d) `SUPERVISOR_TOKEN` is visible without `with-contenv`.

**Fallback:** a plain Alpine base with `init: true`. Its inventory row must be completed first.

### D-131 — HTTP transport: `urllib3` directly [§10]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Decision:**

- The gateway uses `urllib3` 2.x with retries and redirects disabled, streaming, and explicit timeouts. It enters as a direct dependency in Phase 3.
- `requests` is not used by application code.
- `httpx` is not adopted.

### D-132 — Art Institute of Chicago adapter [§9.5]

Status: **accepted** as a beta source (Codex review). The adapter details are **accepted** (user approval of Phase 3, 2026-09-27), as amended by the documentation re-check (D-146): period filter only in the beta, dimensions from the documented Images resource, and renditions only for images at least 1686 px wide.

**Decision.** Use the documented API:

- public-domain works only. `is_public_domain` is requested in `fields`, and every record must have `is_public_domain == true` and an image id;
- department, style, period, and colour from documented metadata. Colour is filtered server-side if range queries work, and client-side otherwise. *Amended by D-146 and the Phase 3 gate (Q-25, option (a)):* the first beta supports only the period, because the department and style values and the colour members are undocumented;
- the documented 1686 px IIIF rendition, with the 4K canvas as the stated need;
- pages sampled without replacement;
- requests paced at 1 s, with the courtesy header;
- at most 15 metadata requests per run;
- a cache of counts and page hints only.

Upscaling is up to ≈ 2.28× in `contain` mode (R-19).

### D-133 — Exit-code policy [§4.2]

Status: proposed (Phase 8 check under Q-07).

**Decision:** Every classified outcome exits 0. Only `internal_error` (70) and watchdog termination (71) exit non-zero. The documentation says to keep the app's Watchdog off.

### D-134 — Rights-basis allowlist [§9.1]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Decision:**

- Every candidate carries a structured `rights_basis`.
- Each provider has an allowlist:
  - local media: `USER_SUPPLIED`;
  - Art Institute: `CC0` (`is_public_domain`);
  - Cleveland: `CC0` (`share_license_status == "CC0"`).
- Selection rejects anything else, and the contract suite checks every adapter.

### D-135 — Copyleft source availability [inventory]

Status: proposed. **The qualified licence review is a release gate (Phase 9).**

**Decision:**

- Each release attaches the corresponding source for every copyleft component in the image:
  - the `samsungtvws` sdist;
  - the exact source releases of **`libimagequant` 4.4.1 (GPL-3.0-or-later)** and **FriBiDi 1.0.16 and fribidi-shim (LGPL-2.1-or-later)**, as bundled in the Pillow wheels. Versions follow the authoritative runtime-wheel inspection;
  - the Alpine aports and distfiles for the GPL and LGPL packages in the image SBOM.
- The qualified licence review specifically covers:
  - the GPL-3.0-or-later `libimagequant` linked into Pillow, and what it means for distributing the image and for the project's Apache-2.0 code;
  - LGPL replaceability for FriBiDi and `samsungtvws`.

  Options the review may weigh:
  - comply as distributed;
  - build Pillow from source without `libimagequant`. This would change D-130's binary-only rule and needs its own decision.

  No option is chosen here.
- The source stays available while the image is distributed, and for at least 3 years. A written offer is the fallback.
- The GPLv3 installation-information duty is assessed as not applicable, pending qualified review.

### D-136 — Cleveland Museum of Art adapter [§9.6]

Status: **accepted** as a beta source (Codex review). The adapter details are **accepted** (user approval of Phase 3, 2026-09-27). They were re-verified against the live documentation on 2026-09-27; D-146 adds an explicit `limit` on every request, leaves out the one department value that contains commas, and enforces period bounds on `creation_date_earliest`.

**Decision.** Use only the documented Open Access API:

- **Every request** carries the `cc0` flag and `has_image=1`.
- **Every record** must have `share_license_status == "CC0"` and an `images.print` entry.
- **Rendition:** only the documented print JPEG (3400 px long side, JPEG). Its string-typed `width` and `height` are parsed defensively. The `full` TIFF is never requested.
- **Filters:**
  - `department`, using the 21 documented values. *Amended by D-146 and D-151:* a curated subset of 12 is offered, and "Performing Arts, Music, & Film" is left out;
  - period, through `created_after` and `created_before` (integer years);
  - style and colour are unsupported in the beta.
- **Random selection:** a random `skip` based on the documented `info.total`. The undocumented `randomize` parameter is not used.
- **Hosts:** exactly `openaccess-api.clevelandart.org` and `openaccess-cdn.clevelandart.org`.
- **Identity and caching:** identifier `cma:<Athena id>`; requests paced at 1 s; ≤ 15 metadata requests per run; a cache of the total per filter (1 day) and skip hints (7 days).
- **Attribution:** a shortened form of the museum's suggested citation, as a courtesy.
- **Terms:** CMA's terms reserve future keys and transaction limits. The adapter allows an optional key later, and treats 401/403 as a stop.

### D-137 — TV-upload exclusion ledger and uncertainty quarantine [§12.4, §13.6]

Status: **accepted** (Codex review; replaces the earlier statement that an uploaded work might be resent).

**Decision:**

- **History unchanged.** The confirmed sent history keeps its meaning and changes only after `selected`. So do the current artwork and the preview.
- **Separate ledger.** A bounded TV-upload exclusion ledger (`upload_ledger.json`) holds two kinds of entry.
  - **`uncertain`**: a write-ahead intent. It is committed at PRE-STAGE, *after* the TV budget re-check and before the TV is contacted.
    - **Removed** whenever no `upload_started` marker was seen: the TV was unreachable, pairing was not accepted, art mode is unsupported, SIGTERM or the kill timer came before `upload_started`, or the upload allowance was insufficient. Also removed on an explicit upload refusal.
    - **Kept** as an uncertainty quarantine only after `upload_started` without `uploaded`, or when the process dies without classifying the run. The period is **30 days** (Q-23, accepted in the final gate review).
    - `upload_started` is sent before the library's upload call, so a missing marker proves nothing was uploaded.
  - **`uploaded`**: promoted immediately when the `uploaded(content_id)` marker arrives, even if selection is then refused, times out, or becomes uncertain.
    - If the promotion write fails, or the process dies before its `fsync`, the entry stays `uncertain`. The run logs an ERROR, and the outcome is unchanged.
    - Confirmed uploads that were durably recorded are never uploaded again. An upload that could not be recorded is excluded for the quarantine period.
- **Exclusion.** Selection skips anything in history, `uploaded`, or an unexpired `uncertain` entry. After a process kill following an upload, the committed intent still excludes the work.
- **Bounds.** At most 20 000 entries and 5 MiB. The ledger uses the same atomic write, `.bak`, reader, and version handling as history. Entries for works that reach history are pruned lazily.
- **Tests.** Acceptance items `E7`–`E10`.

### D-138 — Provisional app identifier `frame_gallery` [§5, §17.1]

Status: **accepted** (Codex review).

**Decision:** `frame_gallery` is the provisional internal identifier. It is used for:

- the Python package name;
- the app slug;
- `/media/frame_gallery`;
- the User-Agent;
- the TV client name, if the installed 3.0.6 API accepts one.

The final public name remains D-101.

### D-139 — Implementation sequencing (vertical slice) [§23]

Status: **accepted** (Codex review).

**Decision.** Implement in this order:

1. Deterministic selection and rendering (Phase 2).
2. The AIC, CMA, and local adapters, with fake or synthesized fixtures (Phase 3).
3. Bounded state and duplicate prevention (Phase 4).
4. The Samsung adapter contract, from the installed package (Phase 5).
5. Home Assistant app packaging (Phase 6), then offline validation (Phase 7).
6. Live Home Assistant Green and TV validation (Phase 8).
7. AppArmor enforcement and final release hardening (Phase 9).

The security and hardening design is unchanged, and no final acceptance criterion is weakened. `TASKS.md` reflects this order.

### D-140 — Preview freshness is release-blocking; refresh mechanism [§16.3]

Status: **accepted** as a requirement (Codex review). The mechanism is selected in Phase 8.

**Decision:**

- The dashboard is not declared complete until repeated live tests on the Home Assistant Green show every newly delivered image without a stale browser cache (acceptance item `G5`).
- The mechanism must keep the preview correct on every documented start path: card tap, scheduled automation, and a start from the app page.
  - Any post-run step lives in one UI automation triggered by the Running sensor turning off, which covers every start path, including starts from the app page.
  - Alternating file names are eligible only if the app writes each delivered preview to both names, so an older artwork can never appear, for example after a `no_match` run.
- Phase 8 tests card-started, automation-started, app-page-started, and `no_match` runs.
- Phase 8 selects and documents one proven, fully UI- or API-based mechanism. The candidates are:
  1. Local File's file-change behaviour;
  2. `homeassistant.update_entity`;
  3. two alternating file names with `local_file.update_file_path`;
  4. another UI- or API-only method.
- The evidence and the chosen mechanism are recorded here and in R-07.
- The Collection Image integration (2026.9+) may be documented as an optional alternative. It must not raise the app's minimum Home Assistant version.

## Phase 2 implementation decisions (accepted)

These record how Phase 2 realized the architecture, and every place where it deviates from the text of `ARCHITECTURE.md`. The user accepted them with the Phase 3 approval on 2026-09-27.

### D-141 — Phase 2 layout, seams, and classification details [§4, §5, §9.1, §12, §21]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

**Layout.** Beyond §21, Phase 2 adds:

- top-level `domain.py` (shared value types), `errors.py` (cross-component errors), and `randomness.py` (the injected random source);
- `app/ports.py`, `app/records.py`, `app/environment.py`, `app/signals.py` (§21's `app/context` is not needed);
- `config/filters.py` (filter value types) and `config/overrides.py`. Helper merging lives in `config`; the Phase 3 `ha` package only reads helper states;
- `budget/limits.py`, `selection/exclusion.py`, `imaging/contract.py`, `imaging/sniff.py`, `imaging/delivery.py`, `isolation/channel.py`, `isolation/in_process.py`, `logs/summary.py`;
- `tests/support/` (fake clock and port fakes), `scripts/check.sh`, and `DEVELOPMENT.md`.

**Internal dependencies beyond the §5 "Depends on" column.** The top-level `domain`, `errors`, and `randomness` modules may be used by every component. Beyond those: `budget.watchdog` uses `logs.summary`; `logs.setup` uses `config.options` (the log level); `isolation.in_process` uses `budget.clock` and `logs.summary`; `imaging.contract` and `imaging.worker_tasks` use `selection.geometry` and `isolation.executor`; `providers.contract` uses `config.filters` and `budget.deadline`; `tv.port` uses `budget.deadline`. There are no cycles. §5's "stdlib" entries are read as "no third-party packages"; the enforced boundary (D-107) is unchanged: Pillow only in `imaging/worker_*`, and no networking or process modules in Phase 2.

**Port shapes.**

- *Provider (§9.1).* `Capabilities` carries the source, the key, and `dims_in_metadata`. The filter capability matrix stays central in `config.capabilities` (it drives the published matrix, B8), and the rights allowlist central in `providers.rights` (D-134). The Phase 3 contract suite asserts that each adapter agrees with both. `probe_ref` is replaced by a `DimensionProbe` bound next to the provider (`ProviderBinding`).
- *Television (§12.1).* `DeliveryRequest` carries no token seed path, and the runner does not act on `DeliveryResult.auth`: the Phase 5 adapter owns the token store (§12.2). The request carries a `stop_requested` signal instead (see *Stop requests*). The port returns or raises only once its worker is dead; the runner also kills every worker before classifying an interrupted delivery.

**Classification details.**

1. The parent validates `delivery.jpg` in ATTEMPT, not in PRE-STAGE, so an invalid output falls through to the next candidate. The parent also re-checks the reported real size against the chosen reason (defence in depth).
2. A request cut off by its *own* time limit (a probe, a download, or the 15 s preparation) is a transport or processing failure. Only a request cut off by the *content window* counts as "search limits reached" (§4.2). The decision uses deadlines, never float comparisons of timeouts.
3. `NOT_FOUND` is for single resources (a rendition or a probe target). An adapter reports a 404 or 410 from a discovery endpoint as `HTTP_ERROR`, so a broken search endpoint is `source_failed`.
4. A `DeadlineExceeded` that no stage handles is classified by the no-delivery rules inside the content window (limits reached). Before the content window it ends the run as `deadline_exceeded` (a CONFIGURE overrun). *This extends the §4.2 meaning of `deadline_exceeded`.*
5. After `selected`, RECORD always runs (§12.3): an adapter failure after `selected` gives `delivered_with_warnings`; any other internal error after `selected` still runs RECORD and reports `internal_error` with history +1.
6. `not_authorized`, `unsupported`, or `insufficient_time` reported *after* `upload_started` keep the quarantine (the upload may have happened), and the status names the outcome. §12.1 says the worker reports them only before `upload_started`.
7. Local header-inspection failures are not transport failures; they only feed the aggregated warning (§9.3). A provider that repeats a work in one pass is not charged twice, and the work never takes two slots.
8. The summary line reports ignored filters as `ignored_filters=…` (D-124 and §9.2; §19 is amended to match).

**Stop requests (§7.6).**

- `Cancelled` derives from `BaseException`, so no `except Exception` (in logging handlers or adapters) can swallow it.
- Before DELIVER, a stop request raises `Cancelled` wherever the run is. Every stage boundary, every attempt, and the points just before the preparation, the upload-intent commit, and the television call also re-check a pending request, so a request that a port swallowed is honoured before new work starts.
- **DELIVER defers stop requests for the whole television call** and for the rest of the run. The request carries a `stop_requested` signal: the adapter polls it while it waits for its worker, kills the worker, relays every marker the worker had sent, and returns. The runner classifies such a run as `cancelled` from the markers. So no SIGTERM can drop a marker, split a marker from its ledger write, or lose the adapter's reply; an adapter that ignores the signal only delays the stop until its own kill timer. (§7.6 "the worker group is killed and the markers are read" now happens inside the adapter.)
- An explicit upload refusal removes the intent even when a stop request is pending: nothing was stored.
- The entry point creates the controller with its stop requests deferred, before it installs the SIGTERM handler. The runner ends that initial deferral inside its classified region, so a stop request that arrives before the run is ready is classified as `cancelled` with a last-run record.
- One runner and one `CancellationController` serve exactly one run.

**FINISH.**

- PUBLISH (preview and current record) may not use FINISH's last 2 s; they are kept for the last-run record.
- A run decided in SELECT or ATTEMPT finishes within its content window (the 70 s bound) as long as the window leaves the 2 s reserve; after an overrun, FINISH gets its own reserve instead of a sliver.
- The summary line is logged last, after CLEANUP and after the watchdog is stopped. If the watchdog had already claimed the run, it emits the only summary line and exits 71 (§4.3, §19).

**Per-candidate decisions.** Selection stays free of I/O and reports one decision per candidate to an optional sink; the runner logs them at DEBUG (§19).

### D-142 — Development environment and lock workflow (amends D-128) [§17, §20.4]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

- **`uv`.** Version 0.12.19, installed from PyPI into the git-ignored `.tools/` directory with its wheel hash checked against PyPI. `pyproject.toml` pins `required-version`, sets `python-downloads = "never"` (interpreters would come from outside the package index), and limits the lock to macOS and Linux.
- **Lock.** A project `uv.lock` with hashes for the whole development environment. `requirements/runtime.txt` is exported from it with `uv export --locked --no-dev --no-emit-project`, hash-pinned. This replaces the separate `uv pip compile --generate-hashes` step of D-128, so the development and runtime pins cannot drift apart. Installs keep `--require-hashes --no-deps --only-binary=:all:`. The Phase 6 container build narrows the runtime file to the chosen Python version and platform.
- **No build backend.** The project is not built as a distribution (`package = false`), so no build backend enters the inventory.
- **Local interpreter.** No Python 3.12+ interpreter was installed on the development machine apart from the CPython 3.12.14 bundled with the local Codex desktop runtime. Phase 2 uses it as the base interpreter of the project environment; nothing was downloaded and nothing outside the repository was modified. Python 3.13 and 3.14 are verified in CI (Phase 9), or earlier if a local interpreter is provided.
- **Gates.** `scripts/check.sh`: Ruff check and format; `mypy --strict` over `src` and `tests`; pytest with branch coverage of at least 90 % overall and 100 % for `budget`, `selection`, `isolation`, `providers`, the outcome classification, the runner, and the imaging worker tasks (§20.4).

### D-143 — Provisional built-in vocabulary [§15.2, D-124]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

- Phase 2 ships the vocabulary *mechanism*: normalization, keys, labels, aliases, and the per-field lookup. The built-in vocabulary is empty (version `0-provisional`). Tests use synthetic vocabularies.
- Until Phase 3 fixes the real lists (Q-14), any static filter value other than `any` is therefore `config_invalid`.
- Within one option field every normalized key, label, and alias must map to exactly one key. A label shared by both museums (for example a "Photography" department at each) must therefore be made distinct in Phase 3, or the lookup made source-aware.

### D-144 — Image pipeline details [§11.1, D-121, D-122]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

- **Header pre-scan** (§11.1 step 2, §18.1 "header limits"). Before Pillow opens a source, the worker walks its header with a bounded standard-library scanner (`imaging/source_scan.py`), because Pillow loops over every marker segment or chunk without a limit, and the D-121 checks look only at the declared dimensions.
  - JPEG, from SOI to the first SOS: at most 1 024 markers, 16 MiB of header bytes, and 4 096 fill bytes. The markers 0xC8 and 0xF0–0xFD are refused, because Pillow reads them without a length and would lose sync with the scan.
  - PNG, from the signature to IEND (Pillow also parses the chunks after the image data): at most 1 024 non-image chunks totalling 16 MiB, and at most 65 536 image-data chunks (`IDAT`, `fdAT`, `fcTL`). Chunk types must be four ASCII letters, and unknown critical chunks are refused.
  - **Metadata TIFF structures.** Pillow also parses TIFF directories inside metadata, and copies every declared value. The scan therefore reads each block exactly as Pillow builds it, before Pillow opens the file:
    - the joined JPEG APP1 EXIF payloads and each APP2 MPF payload;
    - PNG `eXIf` chunks, `tEXt` chunks named `exif`, and "Raw profile type exif" text. That text is decoded within 1 MiB and never inflated without a bound.
  - It walks IFD0, the next-IFD chain, and the Exif, GPS, and Interop IFDs, with a visited set. Caps:
    - 512 entries per IFD, 16 IFDs per structure, and 4 structures per source;
    - 1 MiB of declared value bytes per structure. Pillow turns values into Python objects about 30 times their size; real EXIF fits one 64 KiB segment;
    - 64 images in an MPF index;
    - 1 MiB for one EXIF block, and 8 leading `Exif` headers. These two close two quadratic paths inside Pillow.
  - BigTIFF headers in metadata are refused as `decode`. Blocks whose header Pillow itself ignores are ignored.
  - *Trade-off:* counting *declared* sizes means that a damaged but decodable file with an absurd count in one entry, or a zero sub-IFD pointer, is refused as `limits`, where Pillow would skip the tag. MakerNote internals and SubIFDs are not walked, because the worker never asks Pillow to parse them; a future use of them must extend the walk first.
  - A cap violation gives `limits`; a malformed or truncated header gives `decode`. The parent's validator of `delivery.jpg` keeps its own, stricter rules.
- **MPO.** A JPEG with a multi-image MPF index opens in Pillow as format "MPO". It is accepted when JPEG is declared, and only frame 0 is used (§11.1 step 3).
- **EXIF.** Orientation comes from the metadata already parsed when the file is opened, so a PNG `eXIf` chunk placed after the image data is ignored. Malformed EXIF means orientation 1, never a failure.
- **Colour keys (`tRNS`).** Keys on 1-, 2-, and 4-bit images are applied on the decoded scale; 16-bit grey keys are matched on the 16-bit samples before scaling to 8 bits; 16-bit RGB keys, and keys out of range, are ignored, so the artwork stays opaque. Transparent areas composite over `background_color` after colour conversion (D-122).
- **Classification.** A truncated JPEG header is `decode`, not `format_mismatch`.
- **Strictness.** The pre-scan refuses anything the two parsers could frame differently, so Pillow can never parse past what the scan checked. For example, a JPEG with stray non-marker bytes between header segments is refused as `decode`, although Pillow alone would decode it. Encoders do not write such files.
- **Residual cost.** After the first SOS, libjpeg decodes a progressive JPEG's scans in C, and a file with a huge number of tiny scans costs CPU that the header scan does not bound. The 15 s preparation limit contains it from Phase 5 (R-27); Phase 5 measures it with the D-121 worst cases (R-09).

### D-145 — Redaction scope and test guards [§18, §19, §20.1, H2, H3]

Status: **accepted** (user approval of Phase 3, 2026-09-27).

- **Known secrets.** The Supervisor and TV tokens are registered with one process-wide redactor (installed by `configure_logging`). It also covers their percent-encoded and JSON-escaped forms. `sanitize_for_log` redacts with it *before* truncating, so a cut line can never show a fragment of a registered secret.
- **Credential patterns** (a backstop for secrets that were never registered):
  - after an authorization-type key (`Authorization`, `Proxy-Authorization`, `Cookie`, `Set-Cookie`), the whole rest of the value is redacted, and a standard scheme word (Bearer, Basic, Digest, Negotiate, Token) stays visible;
  - values of credential-named keys: `token`, `password`, `secret`, `auth`, `credentials`, `pwd`, `passphrase`, `session`, any `*_key` or `*-key`, and prefixed forms such as `access_token` or `client_secret`. Quoted values, including spaces, and `b`/`u` prefixes are covered;
  - JWT-shaped strings;
  - the same keys in header tuples (`('Authorization', '…')`), in JSON that is itself JSON-encoded, in camelCase (`accessToken`, `clientSecret`, `privateKey`), and behind percent-encoded separators (`token%3D…`).
  - SHA-256 digests and qualified identifiers stay visible, and a test checks that more than 1 000 lines in the runner's real formats pass unchanged. Consequently, `auth=…`, `session=…`, and `…_key=…` are always redacted in log text; no runner log line uses them for other values.
  - The runner logs fixed fields before untrusted text (for example the digest before the attribution in the `chosen:` line).
  - *Known limits of this heuristic layer* (R-28):
    - unregistered secrets in unusual forms can still pass: unquoted values with commas or spaces, URL user-info, and unusual encodings of a registered secret;
    - some ordinary phrases are over-redacted, for example "Bearer of Bad News".
    - The real secrets (the Supervisor and TV tokens) are registered values and are always redacted.
- **Network guard (H2).** Installed for the whole test session, collection included. It blocks `connect`, `connect_ex`, `sendto`, and `sendmsg` on `socket.socket`, `socket.create_connection`, and the five resolver functions on `socket` and `_socket`.
- **Boundary checks (D-107).** They also ban `_socket`, `_ssl`, `socketserver`, `select`, `selectors`, `ctypes`, `concurrent`, and `pty`, and process creation through `os`. They flag computed dynamic imports outside `isolation`, and allow constant dynamic imports of worker modules only in `isolation`. Self-tests prove that every detector fires. Phase 3 (`net.transport`) and Phase 5 (process isolation) must extend these rules deliberately.

## Phase 3 decisions

### D-146 — Documentation re-check at the start of Phase 3, and its consequences [§9.2, §9.5, §9.6, §15.2]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27). It was applied in Phase 3 under the user's Q-14 instruction: use no undocumented values, and leave out, with a documented limitation, any category that the official documentation does not map reliably. Q-25 is resolved with option (a): the capability changes stand for the first beta, and no live Art Institute observation is approved.

**Method.** On 2026-09-27 the two official documentation pages, `https://api.artic.edu/docs/` and `https://openaccess-api.clevelandart.org/`, were re-read in the in-app browser, and the text was extracted from the rendered pages. No API endpoint, image, or metadata URL was requested, and nothing was recorded from a live response.

**Art Institute of Chicago: documented.**

- *Search.* `GET /api/v1/artworks/search`, with Elasticsearch Query DSL in `query`. "For production use", the whole query travels as minified, URL-encoded JSON in `params`. The `is_public_domain` term query is the documented example.
- *Counting.* A documented example requests `…/artworks/search?query[term][is_public_domain]=true&limit=0`. Every paginated response carries `pagination.total`.
- *Pagination.* `page` (1-based) and `limit`. `limit` cannot exceed 100, and a single search query cannot return more than 10 000 records through any combination of `limit` and `page`.
- *Access.* Anonymous users are throttled to 60 requests per minute per IP. Scraping should stay at no more than one request per second. The `AIC-User-Agent` courtesy header carries "the name of your project and a contact email".
- *Artwork fields.* `id`, `title`, `artist_display`, `date_display`, `date_start` and `date_end` (numbers), `credit_line`, `is_public_domain`, and `image_id`. The fields `department_title`, `style_title`, `style_titles`, and `color` ("Dominant color of this artwork in HSL") exist. Every title-based field has a `.keyword` subfield for filters.
- *Images resource.* `GET /api/v1/images` accepts `ids` (comma-separated) and `fields`. Its `width` and `height` are the "Native width/height of the image".
- *IIIF.* `https://www.artic.edu/iiif/2/{identifier}/full/843,/0/default.jpg` is recommended. For public-domain images, `…/full/1686,/0/default.jpg` may be used, although 843 is still recommended "unless there's a clear need for 1686". The 4K canvas is that need (R-19).
- *Category terms.* Their `subtype` "takes one of the following values: classification, material, technique, style, subject, department, theme". The terms themselves are data behind the `category-terms` endpoints.

**Art Institute of Chicago: not documented.**

- The set of department values and the set of style values. They are API data (category terms), not documentation, and Phase 3 may not call the API.
- The names, ranges, and meaning of the members of the `color` object.
- Any member of the artwork's `thumbnail` object; its description refers only to IIIF conventions. The Phase 1 assumption (§9.5) that the thumbnail carries a documented width and height does not hold.
- Whether the IIIF server upscales a `1686,` request for an image narrower than 1686 px.

**Consequences for the Art Institute adapter** (amends D-132 and §9.5):

1. **Departments, styles, and colours are unsupported in the beta.** No `aic_…`, `style_…`, or `color_…` key is shipped, and the capability matrix lists only the period filter for the Art Institute. Because no such key exists, a configured Art Institute department, style, or colour value is rejected as invalid (B5), and a helper value falls back to the static value. A valid key that the Art Institute does not support, such as a Cleveland department, is ignored and reported (B8). Q-25 is resolved with option (a): the first beta keeps these filters unsupported, and no live observation is approved. Adding them later needs a new decision and explicit approval.
2. **Dimensions come from the documented Images resource.** After each search page, one batched request, `GET /api/v1/images?ids=<the page's image ids>&fields=id,width,height`, reads the native sizes. It counts as a metadata request.
   - The artwork's `image_id` is taken as the image record's `id`, because the documentation uses that identifier for the image in both places. The worker's check of the real dimensions (§8.2) remains the safety net.
   - A record without a matching image record is offered without dimensions and skipped as `dims_unavailable`, since the adapter has no probe.
3. **Rendition.** `full/1686,/0/default.jpg`, only for images at least 1686 px wide; narrower images are skipped. The rendition measures `1686 × round(1686 · h / w)`.
4. **Search shape.** One count request (`limit=0`), then pages of 50 records sampled without replacement from the first `min(total, 10 000)` results. Each page costs two metadata requests (search and images). A typical run therefore needs 3 requests; the allowance of 15 is never exceeded.
5. **Period filter.** An Elasticsearch `range` on the documented numeric `date_start`, which is also checked on every record.

**Cleveland Museum of Art: documented (checked verbatim).**

- *Parameters of `GET /api/artworks/`.*
  - `cc0` takes no value: "Filters by works that have share license cc0".
  - `has_image` is 0 or 1 and returns only works with a web image asset.
  - `department`: the valid values are in Appendix B.
  - `skip`, `limit`, and `fields`. Without a `limit`, the API returns its maximum of 1000 records.
  - The advanced filters `created_after` and `created_before` take integer years; negative years are BCE.
- *Response.* `info.total`, and per record:
  - `id` ("ID in AthenaCCMS");
  - `share_license_status` ("CC0", "Copyrighted", or "Other");
  - `creation_date` (a string), `creation_date_earliest`, and `creation_date_latest`;
  - `creators` (with `description`), `department`, `url`, and `images`.
- *Images.* `images.print` is "3400px at longest side, 300 dpi, jpeg format". The documentation's example gives its `url`, `filename`, `filesize`, `width`, and `height`, all as strings, on `openaccess-cdn.clevelandart.org`. The original TIFF is `images.full`.
- *Rights.* Only works with the CC0 status "additionally provide access to CC0 images".
- *Departments.* Appendix B lists 21, verbatim: African Art; American Painting and Sculpture; Art of the Americas; Chinese Art; Contemporary Art; Decorative Art and Design; Drawings; Egyptian and Ancient Near Eastern Art; European Painting and Sculpture; Greek and Roman Art; Indian and South East Asian Art; Islamic Art; Japanese Art; Korean Art; Medieval Art; Modern European Painting and Sculpture; Oceania; Performing Arts, Music, & Film; Photography; Prints; Textiles.
- *Release history.* The newest entry is version 4.0.3 (2026-07-09).
- *Rate limits.* None is documented.

**Cleveland: not documented.**

- Whether `created_after` and `created_before` are inclusive, and which date field they compare.
- How a `department` value that contains commas is parsed.

**Consequences for the Cleveland adapter** (amends D-136 and §9.6):

1. Every request sets `limit` explicitly: 1 for the count, at most 25 for a page.
2. "Performing Arts, Music, & Film" is not offered.
3. Each period bound is widened by one year on the server side, so either reading of inclusivity is covered. The exact range is then enforced on the documented `creation_date_earliest`.

**Periods, for both museums.** Five project-defined ranges of the earliest creation year: before 1400; 1400–1599; 1600–1799; 1800–1899; and 1900 and later. They are ranges, labelled with years, not styles.

### D-147 — Gateway implementation details [§7.4, §10, D-108, D-115, D-131]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27).

**Module layout.**

- `net/wire.py`: the seam (`WireRequest`, `WireResponse`, `Transport`, `Resolver`, `TransportFailure`).
- `net/policy.py`: host policies, URL and address validation, and header parsing; pure.
- `net/identity.py`: the User-Agent and courtesy header (D-119 as amended).
- `net/gateway.py`: the gateway and one `ProviderChannel` per provider and run.
- `net/transport.py`: the only module that imports `socket`, `ssl`, `http.client`, `urllib3`, and `certifi`. Only the entry point (Phase 6) may import it. `net` modules may import `urllib.parse`; every other `urllib` module stays banned. The boundary test enforces all of this, and a fresh interpreter checks that importing the rest of the package loads no network library.

**Refinements of D-108 and D-115.**

1. **Hosts.** Exact host names only; no suffix rules are needed for the beta. IP-literal hosts, user information, any port but 443, fragments, non-ASCII, and backslashes are refused.
2. **Addresses.** Every resolved address must be public. IPv4-mapped IPv6 addresses are judged by their IPv4 address. 6to4, Teredo, and NAT64 forms are refused, because Python classifies them as not globally reachable. Scoped addresses are refused. Up to 4 addresses are tried in resolver order.
3. **Pacing** is measured from the start of one request to the start of the next. Redirect hops and retries are paced like new requests.
4. **Metadata allowance.** Every wire request (a redirect hop or a retry too) takes one of the 15 metadata requests. When the allowance is spent, the channel raises `AllowanceExhausted`. Selection ends the pass with the new end `metadata_allowance`, which counts as "search limits reached" (`no_match` hint), not as a failure.
5. **Stops.** 401 and 403 stop the provider for the run, for every provider. D-115 names 403 and D-136 adds 401 for Cleveland; applying 401 everywhere is stricter. A 429 without a permitted retry stops too, including a second 429 and a retry that does not fit the deadline or the allowance.
6. **Retry.** At most one, for metadata only: after a failed connect or name resolution, a 502/503/504, or a 429 whose `Retry-After` is at most 5 s. The wait is `max(Retry-After, 1 s)` plus up to 0.25 s of jitter from the injected random source. The retry is skipped unless the caller's deadline still has room for the wait plus one connect timeout. A refused non-public address is never retried.
7. **`Retry-After`** accepts delta-seconds and the IMF-fixdate form of HTTP-date. The obsolete date forms are treated as invalid, which means a stop. `email.utils` is not used, because importing it loads `socket` into the parent.
8. **Time.** Each attempt has its own total (metadata 10 s, image 20 s), clamped to the caller's deadline. If the caller's deadline ran out, the result is `DeadlineExceeded`; if only the request's own limit did, it is `SourceError(TIMEOUT)` (D-141 item 2). The transport enforces the exchange total with a timer that shuts the socket down, so a peer that sends headers or body one byte at a time is bounded too. Body reads use `read1`, at most one socket read per call, with the socket timeout re-clamped before each read.
9. **Bodies.** A declared `Content-Length` over the cap, a body over the cap, or a gzip body that decodes past the cap is `OVER_CAP`. A body shorter than declared is `TRANSPORT`. A truncated, invalid, multi-member, or trailing-data gzip body is `UNEXPECTED_FORMAT`. Only metadata may be gzip. JSON is parsed with the standard library; NaN and Infinity are refused, as is nesting deeper than the interpreter's recursion limit.
10. **404 and 410** from a metadata request are `HTTP_ERROR` (D-141 item 3); from an image download they are `NOT_FOUND`.
11. **Downloads** go to a new file (`O_EXCL`, `O_NOFOLLOW`, mode 0600). A partial file is removed on any failure.
12. **TLS.** A fresh context per connection, trusting only the pinned `certifi` bundle (never the system or environment stores), with `CERT_REQUIRED`, host-name checking, and TLS 1.2 or newer. The connection goes to the validated IP, with SNI and the certificate check on the host name. After the handshake, the negotiated socket's version, verification mode, host-name check, and server name are checked again, and `getpeername()` must equal the validated address before anything is sent. urllib3's own host-name matching (`assert_hostname`) is not used, so Python's check stays on.
13. **Requests** send `Host`, `User-Agent`, `Accept`, `Accept-Encoding`, `Connection: close`, and any courtesy headers. There are no cookies, proxies, pools, retries, or redirects inside urllib3.
14. **Name resolution** runs in a daemon thread that the caller stops waiting for after 3 s (clamped). A lookup that hangs leaves one idle thread behind until the process exits.
15. **No probe path.** No beta source needs a remote dimension probe (§8.3). The 256 KiB probe cap is therefore not implemented yet; the probe allowance stays enforced in selection.
16. **Logs.** Each request is logged at DEBUG with the kind, the host, the path without its query, the status, the byte count, and the duration. A stop is logged at WARNING. Header values, queries, and bodies are never logged.

**Amendment after the internal review of `51d9cf3`** (see *Review records*):

- Item 2: IPv6 site-local addresses (`fec0::/10`) are refused too.
- Item 8, the time bounds. The transport captures the socket right after the connect and uses it for the exchange timer and the per-read timeouts. A response with `Connection: close` makes http.client drop the connection's own reference while the body is still read from it; before this fix, the timer and the re-clamped reads then did nothing. After the connect, the connection's timeout becomes the exchange time, because urllib3 resets the socket timeout to the connection's timeout before sending and before reading the headers. Before this fix, headers and body gaps were bounded by the connect timeout. Once a body is complete, http.client closes the socket, so re-clamping its timeout is skipped. Tests over a local socket pair with the real http.client and urllib3 stack cover a dripping peer, slow headers, slow and stalled bodies, and four body framings.
- Item 16: the `urllib3` logger is silenced completely (`logs/setup.py`). Its warnings quote the full request URL, query included, and unparsed response header data.
- The boundary test lists imports with their members, so `from http import server` in `net/transport.py` is caught like `import http.server`.

**Amendment after the internal review of `f614256` and `8761cca`:** item 4's end is renamed `provider_allowance`. It now covers any allowance of the provider's own: the gateway's metadata requests, and the local library's directory entries (D-149).

### D-148 — Helper reader details [§15.3, D-112; B3–B5]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27).

- **Module.** `ha/client.py`, `SupervisorHelperReader`, implements the `HelperReader` port. It shares the `net.wire` seam, so the real transport serves both the gateway and the reader. It does not go through the gateway, whose rules (HTTPS, public addresses, pacing) do not fit the Supervisor.
- **Request.** `GET http://supervisor/core/api/states/<entity_id>` with `Authorization: Bearer <token>`, `Accept: application/json`, `Accept-Encoding: identity`, `Connection: close`, and `User-Agent: FrameGallery/<version>`. The Supervisor is local, so the User-Agent carries no contact. The entity ID is re-validated with the options pattern (now the public `config.options.HELPER_ENTITY_ID`) and percent-encoded.
- **Where the token may go.** The name `supervisor` is resolved once per run, and every address must be private: not public, loopback, link-local, multicast, reserved, or unspecified. Otherwise nothing is sent. This keeps the token inside the Supervisor's internal network even if name resolution is wrong. Only the first address is used.
- **Bounds.** One request per configured helper (at most four), no redirect (any 3xx fails), and no retry. Each read takes at most 3 s, clamped to the configuration deadline; a read that no longer fits is skipped. The body is at most 64 KiB, `identity` encoding, and JSON. Only `state` is used: a string of at most 255 characters.
- **Failures.** Any failure gives `None` for that helper. The merge then falls back to the static value with exactly one WARNING (B4, B5). The reader logs its own reasons at INFO (no usable token; the Supervisor cannot be reached) and DEBUG (per helper), and never logs the token or a helper's value. Its `repr` hides the token. `unavailable` and `unknown` are returned as they are (B4). Only `Cancelled` propagates.
- **Token.** The entry point (Phase 6) passes the token from the reduced environment and registers it with the redactor (D-145). An empty or non-printable token means no read at all.

**Amendment after the internal review of `f614256`.** A private address alone was not enough: any RFC 1918 LAN address, or a 6to4 or Teredo address embedding a public IPv4 address, would have received the token. Now:

- the reader takes the container's own networks (`NetworkInfo.container_networks()`, which include the Supervisor's internal network);
- every resolved address must be private **and** inside one of those networks, with IPv4 and IPv6 never mixed;
- without known networks, nothing is sent;
- `is_private_address` refuses 6to4, Teredo, and NAT64 forms.

### D-149 — Local media provider details [§8.3, §9.3, D-118; F7]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27).

- **Modules.** `providers/local_media.py` holds `LocalMediaProvider` and `LocalInspectionProbe`. `app/fetching.py` holds `SourceFetcher`, the production image fetcher. Beyond D-141's dependency list, `providers.local_media` uses `imaging.contract`, `isolation.executor`, and `logs.summary`, and `app.fetching` uses `net` and `providers`.
- **Library.** The library is created at the start of discovery (mode 0755, parents included). A library that is a symbolic link, is not a folder, or cannot be created gives one WARNING and no candidate.
- **Scan bounds.**
  - The library itself is level 0, and folders up to 4 levels below it are listed. A deeper folder is skipped as `too_deep`.
  - The 20 000-entry limit counts every listed entry, hidden and skipped ones included, and ends the scan (`entry_limit`).
  - Hidden entries are skipped silently.
  - Symbolic links, special files, unsupported extensions, empty files, files over 40 MiB, unreadable entries, and recent previews are counted by reason.
- **The aggregated WARNING** is emitted once, when discovery ends: when the pass is exhausted, or when selection stops pulling and the generator is closed. It also counts the files that failed inspection. At most 5 example paths are shown, relative to the library, sanitized, and cut to 80 characters.
- **Fingerprint (D-118).** The size is encoded as 8 bytes, big-endian. For a file under 64 KiB, "first" and "last" 64 KiB are both the whole file. `fingerprint_bytes` computes the same value from bytes, so Phase 4 can store the D-118 fingerprints of published previews in `current.json` for guard 3. Identical files share one identifier, and selection counts the repeat as a duplicate (D-141 item 7).
- **Preview guards (F7).**
  - Guard 2 is a construction check: the library may not be or contain the preview folder, otherwise `ValueError`. The production folders are siblings.
  - Guard 1 skips a folder whose real path is the preview folder's.
  - Guard 3 skips the fingerprints that the wiring passes in.
- **Attribution.** Only the title: the file name without its extension, at most 100 characters.
- **Dimensions.** A new `inspect` worker task reads one file's header. It opens, pre-scans, identifies, and limit-checks the file exactly like `prepare` does before decoding, then reads the EXIF orientation; no pixels are decoded.
  - Each inspection may take at most 2 s (`LOCAL_INSPECTION_S`), clamped to the discovery deadline.
  - An unreadable image gives `None`, counted as `unreadable` (the D-141 contract).
  - A worker failure raises `SourceError(UNEXPECTED_FORMAT)`, which selection counts as an inspection failure, never a transport failure.
  - *Deviation from §8.3:* one file per task instead of batches of up to 50. Batching only pays off with the process executor, so it is deferred to Phase 5.
- **Delivery.** The fetcher copies only a file that this scan offered. The file must still be a regular file with the scanned size and fingerprint, and it is copied in 1 MiB steps, with deadline checks, into a new 0600 file. Any change since the scan is `NOT_FOUND`: the next candidate is tried, and it is not a transport failure. Remote references go to the channel whose host policy owns the URL, so downloads share that provider's pacing and 403/429 stop.
- **Empty library.** When the local scan finishes without offering a candidate, the `no_match` hint is "no usable JPEG or PNG images in /media/frame_gallery/library" (new `Hint.LIBRARY_EMPTY`), as §9.3 requires.

**Amendment after the internal review of `8761cca`:**

- **Pinned identities (a symlink race).** A path-based open protects only the last component, so a subfolder swapped for a symbolic link during the run could have led outside the library. Now:
  - each folder is opened with `O_DIRECTORY | O_NOFOLLOW` and listed through its own descriptor;
  - every folder and file is recorded by device and inode as the listing saw it;
  - a folder, when listed, and a file, when offered, copied, or inspected, must still have that identity. The worker's `inspect` task checks the device and inode it is given.
  - A mismatch, or a folder that is now a link or a file, is skipped as the new reason `changed`, or refused as `NOT_FOUND` when copying.
  - Guard 1 now compares identities instead of real paths.
- **Read errors while copying** (`fstat` or `pread` on the library file) are `NOT_FOUND`, so the next candidate is tried. Before, they ended the run as `internal_error`.
- **An inspection cut off by the discovery deadline** raises `DeadlineExceeded` and is not counted as a failed inspection of a healthy file (D-141 item 2).
- **Entry limit.** A scan cut short by the 20 000-entry limit ends by raising `AllowanceExhausted` once its files are offered. The hint is then "search limits reached", not "no usable images". A library larger than the limit is only partly scanned, and it is the same part each run.

### D-150 — Art Institute adapter details [§9.5, D-132, D-146]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27).

- **Modules.** `providers/aic.py`, plus helpers shared with Cleveland:
  - `providers/jsonread.py`: defensive readers for untrusted JSON;
  - `providers/periods.py`: the five period ranges;
  - `providers/cache.py`: the metadata cache port and an in-memory implementation.
- **Query form.** The whole search request travels as minified JSON in `params` (the documented "entire query" form for production use): the Elasticsearch `query`, `fields` as an array, `limit`, and `page`.
  - The query is a `bool` filter: the term `is_public_domain: true`, `exists: image_id`, and, for a period, a `range` on `date_start`.
  - Whether the server honours `fields`, `limit`, and `page` inside `params` exactly as it does as separate parameters is checked in the first approved live observation (Phase 8). Every record is validated either way.
- **Count and pages.**
  - The count request uses `limit` 0 and reads `pagination.total`.
  - Pages hold 50 records. The page numbers `1..ceil(min(total, 10 000) / 50)` are shuffled with the injected random source, so no page is fetched twice in a run.
  - Per run: 1 count, then 2 requests per page (search and sizes). At most 7 pages fit the 15-request allowance, and when it is spent the pass ends as a search limit (D-147 item 4).
- **Sizes.** The Images resource is read with `ids`, `fields=id,width,height`, and an explicit `limit` equal to the number of IDs, because the documented default page size is 12. Repeated image IDs are looked up once. A width and height must be positive and at most 100 000; digit strings are accepted.
  - An image narrower than 1686 px is not offered.
  - A work whose image record is missing is offered without dimensions, and selection counts it as `dims_unavailable`.
- **Record checks.**
  - `id` must be a positive integer of at most 10^10; booleans and strings are refused.
  - `is_public_domain` must be exactly `true`.
  - `image_id` must be a lowercase UUID (the form of the documentation's examples).
  - With a period filter, `date_start` must be an integer year within the range.
  - A record that fails any check is skipped silently; a page summary is logged at DEBUG.
- **Attribution.** Title, artist, date text, and credit line, each cleaned: control and format characters become spaces, whitespace collapses, and the text is cut to 300 characters. No detail URL is stored, because the documentation defines none for artworks.
- **Rendition.** `https://www.artic.edu/iiif/2/<image_id>/full/1686,/0/default.jpg`, built only for works this run offered; the image ID is re-validated and percent-encoded. The size is `1686 × round(1686 · h / w)`, at least 1 px high.
- **Cache.** The count per filter signature (`aic:count:<period key or "any">`) is kept for 1 day through the `MetadataCache` port. Phase 3 uses the in-memory implementation; the bounded, persistent cache is Phase 4 (§13.4). *Deferred to Phase 4:* the exhausted-page hints (§9.5), because they need the exclusion set, which the adapter does not see.
- **Errors.** A structurally malformed response (not an object, a missing list, a total that is not a count) is `UNEXPECTED_FORMAT`. HTTP errors, stops, and time limits come from the gateway (D-147).

### D-151 — Cleveland adapter details [§9.6, D-136, D-146]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27).

- **Module.** `providers/cma.py`. It uses the shared helpers of D-150. `net.policy.https_url` now accepts valueless flags, so `cc0` is sent bare, as the documentation writes it.
- **Every request** starts `?cc0&has_image=1` and sets `limit` explicitly: 1 for the count, 25 for a page.
  - The count request asks only for `fields=id` and reads `info.total`.
  - A page request sends `skip`, `limit=25`, and the D-136 field list, with `creation_date_earliest` added.
- **Random pages.** Page offsets are multiples of 25. Up to 4 096 pages, the page order is a shuffled list. Beyond that, pages are drawn lazily without repeats; 64 repeated draws in a row end the pass. Per run: 1 count and at most 14 pages (the 15-request allowance).
- **Departments.** The vocabulary key maps to the exact documented value, which is sent URL-encoded. Every record's `department` must equal it. The curated list:
  - American Painting and Sculpture;
  - European Painting and Sculpture;
  - Modern European Painting and Sculpture;
  - Drawings; Prints; Photography;
  - Chinese Art; Japanese Art; Korean Art;
  - Indian and South East Asian Art; Islamic Art;
  - Textiles.

  These are the documented departments that hold two-dimensional works suited to a wall display. The other documented departments are mostly objects: African Art, Art of the Americas, Contemporary Art, Decorative Art and Design, Egyptian and Ancient Near Eastern Art, Greek and Roman Art, Medieval Art, and Oceania. "Performing Arts, Music, & Film" is left out as undocumented to parse (D-146). All 21 documented values are kept verbatim in the module, and a test checks that the curated values are a subset.
- **Period.** `created_after = first − 1` and `created_before = last + 1`, sent only for the bounds a period has. The exact range is enforced on `creation_date_earliest`, an integer year.
- **Record checks.**
  - `id` must be a positive integer.
  - `share_license_status` must be exactly `"CC0"`.
  - `images.print` must be an object whose `url` is an `https` URL on `openaccess-cdn.clevelandart.org` (port 443). The path must end in `.jpg` (any case) and contain only letters, digits, `.`, `_`, `-`, and `/`, with no empty, `.`, or `..` segments, and there may be no query.
  - A print that fails the URL check is counted, and the pass ends with one WARNING giving the count. Other failures are skipped silently.
  - `images.full` (the TIFF) is never read.
- **Dimensions** are the print's `width` and `height`: integers or digit strings, positive, at most 100 000. If either is missing or invalid, the work is offered without dimensions.
- **Attribution.**
  - Title and creation date, cleaned (D-150).
  - The first creator's documented `description`.
  - The documented `url` as the detail link, but only in the form `https://(www.)clevelandart.org/art/<accession>`.
  - No CMA trademarks are used.
- **Cache.** The count per filter signature (`cma:count:<department>:<period>`) is kept for 1 day (D-150).
- **Stops.** 401 and 403 stop the provider for the run (D-136, D-147 item 5).

### D-152 — Vocabulary version 1, the narrowed capability matrix, and the contract suite [§9.1, §9.2, §15.2, §20.1, Q-14]

Status: **accepted** (Phase 3 gate, user decision, 2026-09-27).

- **Vocabulary version 1** (Q-14, resolved) is built only from documented values (D-146):
  - *Departments:* the 12 curated Cleveland departments (D-151). Each label is `"<documented value> (Cleveland)"` and names the museum, so labels stay distinct between museums (D-143). The documented value itself is an alias.
  - *Periods:* five periods labelled with years, each with plain aliases such as `1800-1899` and `19th century`. They share their keys with `providers.periods.PERIOD_RANGES`.
  - *Excluded:* no Art Institute department, no style, and no colour (Q-25, resolved with option (a)).
  - Tests check normalization, aliases, uniqueness within each field, that no term is reserved, that no label repeats, and that the entries match the adapters' mappings.
  - `frame_gallery/VOCABULARY.md` documents the whole mapping and the capability matrix. A test parses it and requires it to match the code.
- **Capability matrix.** The Art Institute now supports only the period (D-146, amending D-124). The Phase 2 tests that used Art Institute departments as examples now use Cleveland departments. B2 and C1 therefore hold for the filters a source supports: Cleveland combines department and period; the Art Institute applies the period.
  - A valid key that the selected source does not support, such as a Cleveland department with the Art Institute or a period with local media, is ignored and reported (B8).
  - A value that matches no key, label, or alias of version 1, and is not a no-filter term (any style, any colour other than a no-filter value such as "any", an Art Institute department), is rejected as invalid (B5). As a helper value, it falls back to the static value with a warning.
  - In the first beta, no source offers a colour filter (Q-25, option (a)).
- **`dims_in_metadata`** now means "the documented metadata gives the rendition's size, so no probe is bound". A candidate whose metadata lacks the size carries `None`, and selection counts it as `dims_unavailable`.
- **Contract suite** (`tests/unit/providers/test_contract_suite.py`). Every adapter, over its own synthesized fixture, is checked for:
  - consistent source and key;
  - agreement with `CAPABILITY_MATRIX`: a supported filter changes the requests and narrows the result, and an unsupported one changes nothing;
  - rights bases within `ALLOWED_RIGHTS`;
  - laziness;
  - policy hosts only, for requests and renditions;
  - discovery 404 and 410 → `HTTP_ERROR`, including the Art Institute's size lookup; rendition 404 and 410 → `NOT_FOUND`;
  - (local media) `None` from inspecting an unreadable file (D-141).
- **End-to-end tests** (`tests/integration/test_museum_pipeline.py`) run the runner with the real adapters, gateway, and fetcher over the synthesized APIs:
  - a Cleveland run with department and period combined delivers a CC0 print JPEG, and never requests the TIFF (C1, C10);
  - an Art Institute run with a period delivers the 1686 px IIIF rendition, sends the courtesy header, and reports the unsupported department in the summary line (B8).
- **Fixtures.** The API documents are synthesized in `tests/support/museums.py`: independently authored, with invented values and envelopes that follow the re-read documentation. Nothing was recorded from a live API (§20.3).
- **Layout additions** (beyond §21 and D-141): `net/` (`wire`, `policy`, `identity`, `gateway`, `transport`), `ha/client.py`, `app/fetching.py`, and `providers/` (`aic`, `cma`, `local_media`, `jsonread`, `periods`, `cache`).

## Phase 4 decisions (proposed)

These record how Phase 4 realizes §13 and §14, and every place where it deviates from the text of `ARCHITECTURE.md`. They await the Phase 4 gate.

### D-153 — The atomic primitive, the reader, and history [§13.2, §13.3, D-110]

Status: proposed (Phase 4 gate).

- **Modules.** `store/atomic.py` (the primitive, the reader, and the quarantine), `store/fields.py` (timestamps and identifiers), and `store/history.py`. The rule for qualified identifiers moves from `providers.contract` to `domain.py`, which `providers.contract` now imports, so that the store never imports a provider module (§5).
- **Directories.** The anchor's last component and every part below it are opened with `O_DIRECTORY | O_NOFOLLOW`; a symbolic link or a file in their place is refused. Missing parts are created (mode 0700 below `/data`). Every file operation is relative to the directory descriptor.
- **Writes.**
  - JSON is compact and ASCII-only, so lone surrogates in untrusted text are escaped rather than failing. NaN and Infinity are refused.
  - The self-check (step 2) requires the bytes to parse back to an equal value **and** to pass the reader's own envelope and schema checks. A document that this code could not read back is never written.
  - The temporary file is `<name>.tmp-<16 hex digits>`. Its mode is set exactly with `fchmod`, so the umask cannot change it: 0600 for state, 0644 for the preview.
  - `.bak` is refreshed only from a primary that was valid when it was read, or that this process wrote. A damaged primary therefore never replaces a good backup.
  - A failed directory `fsync` after a successful rename is reported with `replaced = true`: the new content is in place, but its durability is uncertain. The callers decide what that means (D-154).
- **Reader.**
  - A file is *damaged* when it is not JSON; not an object of the expected `format`; has no integer `version`, or an older or unknown one; fails the schema; is not a regular file (a symbolic link is moved aside without being followed); or exceeds its size bound. Damaged files are quarantined.
  - A *newer* version, or a file that exists but cannot be read (`EACCES`, `EIO`), is reported and not quarantined. History and the ledger then end the run with `state_error` before the television is touched (D-154). Falling back to `.bak` or to an empty state in that case could lose exclusions and resend a work.
  - Both copies missing is a first run: an empty result without a warning.
- **Quarantine.** `state/quarantine/<UTC time>-<random>-<name>`. After each move, the oldest entries beyond three are removed; a damaged entry that is a directory is removed as a tree.
- **Schema strictness.** One invalid entry makes the whole document damaged, so the reader falls back to `.bak`. Unknown fields are ignored and are not written back. A repeated identifier keeps its last position.
- **History bounds.** 20 000 entries and 5 MiB; the oldest entries go first, and the new entry is always kept. Identifiers are at most 200 ASCII characters and timestamps have a fixed length, so 20 000 entries take at most about 4.64 MiB: the entry bound is the one that binds (a test checks this).

**Amendment after the internal review of `a74ba1c`, `1677ccd`, and `f347ffb`** (see *Review records*):

- **Timestamps** must lie from 2000 to 8999 (UTC). Dates at the limits of `datetime` raised `OverflowError` when a quarantine period or a time to live was added, and ended every run as `internal_error`. They are now damage, and the reader also treats an arithmetic error in a schema check as damage.
- **Numbers** too large for a finite float (for example `1e400`) are refused like NaN and Infinity.
- **A newer version over the size bound** is recognised by its first 256 bytes, which every version writes as `{"format": …, "version": …`, and is reported as newer instead of being quarantined. Later versions must keep writing these two fields first.
- **The sweep pattern** now matches the `.bak` temporary files of names up to the 100 characters that `check_name` allows.

### D-154 — The upload ledger and the file state store [§13.3, §13.6, D-137]

Status: proposed (Phase 4 gate).

- **Modules.** `store/upload_ledger.py` (the document and its pure transitions) and `store/state.py` (`FileStateStore`, the `StateStore` port). `store.state` uses `selection.exclusion` for the `ExclusionSet` value type. This is an internal dependency beyond §5's "stdlib" column, recorded as D-141 does. There is no cycle: `selection` does not import `store`.
- **Lock.** `/data/state/.lock`, opened with `O_NOFOLLOW` and mode 0600, then `flock(LOCK_EX | LOCK_NB)`. `EWOULDBLOCK` gives `already_running`; any other failure gives `state_error`. The startup sweep runs only once the lock is held; a failing sweep only logs a warning.
- **Loading.** History and the ledger are read once per run, in SELECT (`load_exclusions`). A newer version or an unreadable file ends the run with `state_error` before the television is contacted (D-153).
- **Intent durability.** `commit_upload_intent` raises `StateError` on any failure, **including a failed directory `fsync` after the rename**. The run then ends with `state_error`, and the runner removes the intent, which the file may already hold. The television is therefore never contacted without a durable intent.
- **Promotion.** A failed promotion raises `StateError`. The runner logs an ERROR and keeps the outcome (§13.6 step 4). If only the `fsync` failed, the file already says `uploaded`: stricter than required, never weaker.
- **Recording history.** A failed rename raises `StateError`, which gives `delivered_unrecorded`. A failed directory `fsync` after the rename only logs a WARNING: the history is in place, and the ledger's `uploaded` entry excludes the work anyway.
- **Memory mirrors the files.** After a failure before the rename, the previous entries stay. After a failure only in the `fsync`, the new entries are kept, because the file holds them.
- **Pruning.** Only the intent write prunes. It drops intents whose quarantine has ended, and works that **both** copies of history hold, the primary and its `.bak`. `.bak` is one generation old, so a delivered work keeps its `uploaded` entry until a damaged primary can no longer lose its exclusion (amended after the internal review, see below).
- **Transitions.**
  - An intent never turns an `uploaded` entry back into `uncertain`.
  - A removal only ever removes an `uncertain` entry.
  - A promotion replaces the intent, or adds an `uploaded` entry if the intent is missing.
  - A repeated identifier in a file keeps its strongest entry: `uploaded` over `uncertain`, then the later time.
- **Bounds.** 20 000 entries and 5 MiB. The oldest `uploaded` entries are dropped first, then the oldest `uncertain` ones. The entry being written is never dropped.
- **Quarantine period.** An `uncertain` entry excludes its work until exactly 30 days after `at`. An `at` in the future (a clock that went back) keeps the quarantine until then, so it is never shortened.
- **Leftovers.** `close` discards a pre-staged history file that was never recorded. The startup sweep removes any that a killed run left behind (D-155).

### D-155 — Workspace, startup sweep, and store layout [§13.1, §14]

Status: proposed (Phase 4 gate).

- **Modules.** `store/workspace.py` (`RunWorkspace`, the `Workspace` port), `store/sweep.py` (`StartupSweep`), and `store/layout.py` (`StoreLayout`: the anchors `/data`, `/media`, and `/tmp`, and the store ports built from them for the Phase 6 entry point).
- **Moved types.** `WorkspacePaths` moves from `app.ports` to `domain.py`, and `PublishError` from `app.ports` to `errors.py`. The store can then implement the runner's ports without importing `app` (§5).
- **Workspace.**
  - `/tmp/frame-gallery` must belong to the process's user and is narrowed to mode 0700. `run-<16 hex digits>` and its `in/` and `out/` are created with mode 0700, once per run, in ATTEMPT.
  - Removal is a descriptor-relative `rmtree` that never follows a symbolic link. A failure only logs a warning.
  - Phase 5 sets the modes that the unprivileged worker needs (§11.3).
- **Sweep.**
  - It runs in CONFIGURE, after the lock is taken, so a run that loses the lock sweeps nothing.
  - It removes regular files named `<name>.tmp-<16 hex digits>` or `<name>.bak.tmp-<16 hex digits>` in `/data/state`, `/data/cache`, `/data/tv`, and `/media/frame_gallery/preview`, and directories named `run-<16 hex digits>` in `/tmp/frame-gallery`.
  - Only exact names of the right kind are touched; symbolic links and other kinds are left alone.
  - At most 1 000 entries are scanned per directory. A missing directory is skipped, errors only log a warning, and the number removed is logged at INFO.
  - The quarantine directory is not swept; it has its own bound (D-153).
- **Amendment after the internal review:** a run directory whose `in/` or `out/` could not be created is removed at once, so `create` never leaves a half-made directory for the next sweep.

### D-156 — The bounded metadata cache [§13.4, D-150, D-151; F6]

Status: proposed (Phase 4 gate).

- **Modules.** `store/cache.py` holds `FileMetadataCache`, the value type `ExhaustedPages`, and its merge rule. The port in `providers/cache.py` gains exhausted-page hints (`get_exhausted`, `add_exhausted`, and `HINT_TTL` of 7 days) and imports the value type from `store.cache`, as §5 lists (`providers` depends on `store.cache`). The in-memory cache implements the same port for tests.
- **File.** `/data/cache/<provider>.json` (mode 0600; directory 0700) with `format`, `version`, `provider`, and a list of entries. Each entry has `key`, `expires`, `used`, and either `count` or `total` and `pages`. Keys must start with the provider's own key.
- **Bounds.**
  - 1 000 entries and 2 MiB per file; 8 KiB per entry (an entry that would exceed it is not kept); at most 800 page numbers per hint, the lowest kept.
  - A time to live is clamped to 7 days. On reading, an entry that would expire more than 7 days ahead (a clock that went back) is dropped.
  - Expired entries go first, then the least recently used (by last use, then key).
- **Recency.** Every hit updates `used`, so a run with a cache hit writes the file. That is still at most one write per run.
- **Hints.** A hint belongs to the result count it was computed for; hints for another count replace it, because the pages may have shifted. An entry keeps its first expiry when pages are added, so no hint is older than 7 days.
- **Damage.** Any structural problem (not JSON, another format or provider, an invalid entry, too many entries, oversize) discards the whole file with a WARNING, and the next write replaces it. There is no quarantine and no `.bak`: the cache is excluded from backups and can always be rebuilt. A file of a newer version is discarded and later overwritten too.
- **Writes.** Once per run, through `flush(deadline)`. With no time left, the write is skipped (INFO); a failure only logs a warning. A cache directory that is a symbolic link is never read or written.

### D-157 — Exhausted-page hints and the cache write [§9.5, §9.6, §13.4, R-13; amends D-150]

Status: proposed (Phase 4 gate). It closes the item that D-150 deferred to Phase 4.

- **How an adapter learns about exclusions.** `DiscoveryContext` gains `is_excluded`, the runner's exclusion set (history, `uploaded`, and unexpired `uncertain`), and `notes`, a small record the adapter fills. Adapters still yield every candidate, and selection still decides (§9.1); they use the predicate only to recognise pages that offer nothing new.
- **When a page is exhausted.** A page is exhausted when none of its offered candidates both has dimensions and is outside the exclusions. The adapter's own record checks (rights, identifiers, the period, the rendition host, the Art Institute's minimum width) are part of this, because they do not depend on the options. Shape and format checks do depend on the options and are ignored. A candidate without dimensions counts as nothing new, because selection skips it whatever the options (`dims_unavailable`).
- **Keys.** `aic:exhausted:<period or any>` and `cma:exhausted:<department or any>:<period or any>`, next to the counts. A hint is valid only for the result count it was computed with (D-156). The Art Institute pages are numbered from 1 and Cleveland's offsets from 0, as each adapter already counts them.
- **Use.** Hinted pages are left out before the page order is shuffled, or treated as already drawn in Cleveland's lazy draw beyond 4 096 pages. The number skipped is added to `notes.pages_skipped`. Without hints, the page order and the requests are unchanged.
- **Hint when nothing is seen.** `NoDeliveryEvidence` gains `pages_skipped`. A run in which every candidate seen was excluded (`candidates_seen` may be 0) and at least one page was skipped as exhausted gets the hint "nothing new left for these filters" instead of "filters too restrictive". `last_run.json` reports `pages_skipped` with the selection statistics.
- **Writing the cache.** `ProviderBinding` gains an optional `cache` (a `CacheWriter` with `flush(deadline)`). The runner calls it once in FINISH, before the last-run record, with FINISH's deadline minus the last-run reserve; a failure only logs a warning and never changes the outcome. A run that stopped before SELECT (for example `already_running`) has no binding and never writes the cache. `StoreLayout.metadata_cache` builds the file cache for the Phase 6 wiring, which passes the same object to the adapter and to its binding.
- **Limitation.** The documentation does not promise a stable order of search results. A hinted page that shifts within the 7 days hides its works until the hint expires, and the result count changes the hint's validity only when the total changes. The effect is a missed work, never a duplicate (R-13).

### D-158 — Preview publication and the run records [§13.1, §13.5, D-118, D8, F7]

Status: proposed (Phase 4 gate).

- **Modules.** `store/preview.py` (`PreviewStore`, the `PreviewPublisher` port) and `store/records.py` (`RunRecordStore`, the `RunRecords` port).
- **Fingerprint.** The D-118 fingerprint moves from `providers.local_media` into the shared top-level module `fingerprint.py`, next to `domain`, `errors`, and `randomness` (D-141). `imaging.delivery` and the store can then compute it without importing a provider. `DeliveryArtifact` gains `fingerprint`, which the parent computes over the same bytes as the SHA-256.
- **Preview.**
  - Every directory below `/media` is opened with `O_NOFOLLOW`, so a symbolic link at `frame_gallery` or `preview` is refused. Missing directories are created with mode 0755.
  - `delivery.jpg` is read again without following a link, at most 15 MiB, and its size and SHA-256 must match the values from ATTEMPT.
  - Each name is written with the §13.2 primitive at exactly mode 0644. The temporary file is read back and hashed before the rename.
  - Every name receives the same bytes. The default is `latest.jpg` until Phase 8 chooses the refresh mechanism (D-140).
  - A failed directory `fsync` after the rename only logs a warning. Any other failure raises `PublishError`, which gives `delivered_with_warnings`, for example when `/media` is unavailable.
- **`current.json`.**
  - It holds the runner's record plus `preview_fingerprints`: this delivery's fingerprint merged with the earlier ones, newest first, without repeats, at most 10.
  - The fingerprint is recorded even when the preview could not be published. It only ever keeps a copy of a delivered canvas out of the library.
  - `RunRecordStore.preview_fingerprints()` gives the list to the Phase 6 wiring for the local provider's guard 3. It never raises. A damaged `current.json` is quarantined, and its fingerprints are lost; guards 1 and 2 still apply.
- **Both records.** At most 16 KiB, mode 0600, no `.bak`. A record over the bound is refused with `StateError`. A test shows that the largest possible records fit, with every text field at 200 characters that each escape to 12 bytes. The runner's handling is unchanged: a failed preview or current record gives `delivered_with_warnings`, and a failed last-run record never loses the summary line (D-141).

## Proposed dependency inventory

Status: **Phase 2 installed** the development tools and Pillow, and **Phase 3 installed** `urllib3` 2.8.0 and `certifi` 2026.7.22 (approved by the user on 2026-09-27), only in the local project environment (`frame_gallery/.venv`, from `uv.lock`). The runtime rows for later phases are still proposed.

- Versions and licenses were read from PyPI metadata (`https://pypi.org/pypi/<name>/json`) on 2026-09-26.
- In Phase 2 the installed versions and `License-Expression` fields were re-read from each installed distribution's metadata; they match the rows below.
- In Phase 3 the same check was made for `urllib3` (`License-Expression: MIT`, `LICENSE.txt`) and `certifi` (legacy `License: MPL-2.0` with the MPL classifier, no `License-Expression`; `LICENSE`). Both are pure-Python `py3-none-any` wheels with no dependencies; no `urllib3` extra is installed.
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
| `Pillow` | PyPI `musllinux_1_2` wheels for `aarch64` and `x86_64`, `==12.3.0` (`<13` until validated); approved for use from Phase 2 (Codex final approval of Phase 1 at `dda877c`) | `MIT-CMU` **for Pillow itself; the wheel is a composite that includes GPL-3.0-or-later and LGPL-2.1-or-later components** (see the bundled-library table) | dyn, redist, native | Pillow `LICENSE`; every bundled component's licence and acknowledgement; copyleft source availability for `libimagequant` and FriBiDi (D-135) | Image pipeline (§11) | Phase 2 |
| `urllib3` | PyPI `==2.8.0` (`<3`), `py3-none-any`; wheel SHA-256 `0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3` | `MIT` (`LICENSE.txt`) | dyn, redist | License text | Gateway transport (D-131); imported only by `net/transport.py` | Phase 3 (approved and installed 2026-09-27) |
| `certifi` | PyPI `==2026.7.22`, `py3-none-any`; wheel SHA-256 `62f22742b58a1a33014a2b6b706588a8d7e2a88ae7bd1a6ebe8c992928483775`; sdist SHA-256 `741e2c3b351ddf169a738da9f2c048608ff7f2c5cc02f1ebc6b118bb090d5d55` | `MPL-2.0` (`LICENSE`) | dyn, redist (CA bundle) | Files kept unmodified under MPL-2.0; identified in the notices; source pointer (D-135) | The gateway's explicit CA bundle (§10); imported only by `net/transport.py` | Phase 3 (approved and installed 2026-09-27) |

### Runtime: bundled in the Pillow wheels

**Observed** in the Codex final gate review of `9352e77`. Codex inspected the official Pillow 12.3.0 CPython 3.14 `musllinux_1_2` wheels for `aarch64` and `x86_64` from PyPI, and both wheel SBOMs list the same components.

This inventory is **provisional**. When the container's exact Python version is chosen (D-130, check a), the inspection is repeated against the exact two runtime wheels, and that result becomes authoritative.

| Component | Version (wheel SBOM) | SPDX (wheel SBOM) | Obligations |
| --- | --- | --- | --- |
| libimagequant | 4.4.1 | `GPL-3.0-or-later` | **Copyleft.** GPL-3.0 text; the corresponding source for this exact version attached to each release (D-135); covered by the qualified licence review, which is a release gate (R-25). |
| FriBiDi | 1.0.16 | `LGPL-2.1-or-later` | **Copyleft.** LGPL-2.1 text; corresponding source (D-135). Shipped unmodified as a separately replaceable shared library. |
| fribidi-shim | 1.x | `LGPL-2.1-or-later` | Same as FriBiDi. |
| raqm | 0.10.5 | `MIT` | Licence text. |
| FreeType | 2.14.3 | `FTL` | Licence text. The documentation carries the FTL credit: "Portions of this software are copyright © The FreeType Project (www.freetype.org). All rights reserved." The exact wording is taken from the shipped licence. |
| HarfBuzz | 14.2.1 | `MIT` | Licence text. |
| libavif | 1.4.2 | `BSD-2-Clause` | Licence text. |
| libjpeg / libjpeg-turbo | 3.1.4.1 | `IJG AND BSD-3-Clause` | Licence texts, plus the IJG acknowledgement in `DOCS.md` and the notices: "This software is based in part on the work of the Independent JPEG Group." |
| libtiff | 4.7.1 | `libtiff` | Licence text. |
| libwebp | 1.6.0 | `BSD-3-Clause` | Licence text. |
| libxcb | 1.17.0 | `X11` | Licence text. |
| Little CMS 2 | 2.19.1 | `MIT` | Licence text. |
| OpenJPEG | 2.5.4 | `BSD-2-Clause` | Licence text. |
| pybind11 | per the SBOM | `BSD-3-Clause` | Licence text. |
| pythoncapi_compat | per the SBOM | `0BSD` | Licence text (courtesy). |
| zlib | 2.3.3 | `Zlib` | Licence text. |

**Other shared objects in `pillow.libs/`, verified in Phase 6.** These are libXau, libXdmcp, Brotli, libbsd, liblzma, libmd, libpng, libsharpyuv, and libzstd.

- **Gate adjustment, explicitly approved by Codex** at the final approval of Phase 1 (`dda877c`). Their verification moved from the Phase 2 approval gate to the authoritative Phase 6 runtime-wheel inspection (D-130 check (a)). The exact runtime wheel cannot be selected until the container's Python version is fixed in Phase 6.
- Their exact versions and SPDX identifiers are then taken from the wheel's licence and SBOM material, and the notices must include them.
- **Full verification remains mandatory before packaging or publication.** Nothing is packaged or published before it is complete.
- The provisional notices created in Phase 2 carry the known inventory above, including `libimagequant` and FriBiDi, and list these nine entries as pending verification.
- The GPL/LGPL qualified licence review and the source-availability obligations (D-135, R-25) remain release blockers. They are not weakened by this adjustment.

**Consequences:**

- The runtime image contains **GPL-3.0-or-later** code (`libimagequant`) and **LGPL-2.1-or-later** code (FriBiDi, fribidi-shim), and these come from the PyPI wheel itself. The earlier claim that the PyPI wheels omit `libimagequant` was **wrong** and has been withdrawn.
- Using the PyPI wheel instead of Alpine's `py3-pillow` does **not** avoid this GPL component.
- No project document may claim that the runtime is free of GPL components.

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
| `uv` | PyPI `==0.12.19` (installed in the git-ignored `.tools/`; wheel SHA-256 `5da0401c0898b5fe767968f5a72f27525276b119d69e0c7c25b721f63ecef650`, checked against PyPI) | `MIT OR Apache-2.0` | Lock and export (D-128, D-142) |
| `pytest` | PyPI `>=9.1,<10`; locked 9.1.1 | `MIT` | Tests |
| `iniconfig` | PyPI 2.3.0 (via pytest) | `MIT` | — |
| `packaging` | PyPI 26.3 (via pytest) | `Apache-2.0 OR BSD-2-Clause` | — |
| `pluggy` | PyPI 1.6.0 (via pytest) | `MIT` (license field) | — |
| `Pygments` | PyPI 2.21.0 (via pytest) | `BSD-2-Clause` | — |
| `pytest-cov` | PyPI `>=7.1,<8`; locked 7.1.0 | `MIT` | Coverage |
| `coverage` | PyPI `>=7.16,<8`; locked 7.16.1 | `Apache-2.0` (ships a `NOTICE.txt`; not distributed) | Branch coverage |
| `ruff` | PyPI `>=0.16,<0.17`; locked 0.16.9 | `MIT` | Lint and format |
| `mypy` | PyPI `>=2.3,<3`; locked 2.3.1 | `MIT` | Typing |
| `typing-extensions` | PyPI 4.16.0 (via mypy) | `PSF-2.0` | — |
| `mypy-extensions` | PyPI 1.1.0 (via mypy) | `MIT`: the official wheel contains a `LICENSE` that states the MIT licence explicitly (Codex final gate review). Development only; not shipped. | — |
| `pathspec` | PyPI 1.1.1 (via mypy) | `MPL-2.0`, per its official PyPI project metadata and licence documentation (Codex final gate review). Development only; not shipped. | — |
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
| Alpine `py3-pillow` | Older than the PyPI release and lags on security fixes. It also links GPL-3.0-or-later `libimagequant`, just as the PyPI wheel bundles it, so it gives no licensing advantage. |
| lxml, BeautifulSoup | Not needed (D-127). |
| `samsungtvws` extras (`async`, `encrypted`, `cli`) | Not needed. |

## Risk register

L = likelihood, I = impact; H = high, M = medium, L = low.

| ID | Risk | L / I | Mitigation | Residual / owner |
| --- | --- | --- | --- | --- |
| R-01 | Google Arts & Culture has no documented API, and its terms and image rights conflict with automated retrieval | — | **Excluded from the beta** (Q-01, resolved). Its researched status is kept. | Only if an official API appears |
| R-02 | Google Arts & Culture page formats change | — | Not applicable while the source is excluded | — |
| R-03 | The Samsung art protocol is undocumented and changes with firmware. The TLS or certificate behaviour and the token scope are unknown. | M / H | Isolated, pinned library; surface taken from the installed package (Q-15); marker-based classification; trust-on-first-use decided in Phase 5; Phase 8 live validation | Phase 5/8 |
| R-04 | `samsungtvws` has a single maintainer, an undocumented 3.x art API, LGPL obligations, and inherited licence provenance | M / M | Hash pin; contract tests; D-135; Phase 5 check of `LICENSE` and headers | Phase 5, licence review |
| R-05 | Bing: undocumented endpoint, a `robots.txt` image-path rule, and restrictive Services Agreement terms | — | **Excluded** (Q-17, resolved) | — |
| R-06 | The loading state depends on the Running entity (disabled by default, undocumented polling); short runs may never show it | M / M | 130 s guaranteed exit. The **normative** 150 s timer indicator, started by the card script, does not depend on the sensor. Phase 8 cases: a run under 10 s, a mistyped slug, a non-admin tap. | Phase 8 (Q-09, Q-19) |
| R-07 | **Preview freshness** (release-blocking). The Local File update mechanism and the camera cache refresh are undocumented, and the existing installation had stale images. | H / H | Phase 8 selects one proven mechanism from D-140 through repeated live tests, and the dashboard is not declared complete until then. The platform basis for `/media` and the allowlist is recorded (D-111). | Phase 8; the result is recorded here |
| R-08 | Image decoder vulnerabilities | M / H | Header limits; format allowlist; unprivileged, memory-limited worker; allowlisted environment; bytes-only results; prompt updates | Ongoing |
| R-09 | Memory pressure during decode | L / M | Pixel caps (64 MP JPEG, 40 MP PNG); colour work after resizing; 1 GiB `RLIMIT_AS`; beta renditions ≤ 3400 px; worst case ≈ 450–550 MiB. Peak memory and prepare time for the D-121 worst cases are measured under the real `RLIMIT_AS` in Phase 5 and on the Green in Phase 8, including a header flood just under the D-144 pre-scan caps and a progressive JPEG with very many scans. If preparation exceeds about 12 s, the local-media pixel caps are lowered. | Phase 5/8 |
| R-10 | Home Assistant platform churn | M / M | Follow the current docs; re-check them in Phases 6 and 9 | Phase 6/9 |
| R-11 | Pairing friction: prompts on each connection, and the 20 s pairing wait inside the 40 s TV phase | M / M | Token persistence; self-healing reset; *First Time Only* setting; a clear message to accept the prompt and run again | Documentation; Phase 8 |
| R-12 | TV off or on another subnet gives `tv_unreachable` | M / L | Actionable messages; documented network requirement | Documentation |
| R-13 | Restrictive filters or small folders exhaust the available works, giving frequent `no_match` | H / L | Distinct hints; exhausted-page and skip cache; documented behaviour | Accepted |
| R-14 | Branding: "Frame" is part of Samsung's product name | M / M | D-101 review; factual compatibility wording only | User (D-101) |
| R-15 | Watchdog `os._exit` skips normal cleanup | L / M | The worker group is killed first; `PR_SET_PDEATHSIG`; RAM `/tmp`; startup sweep; timing test | Accepted |
| R-16 | Supervisor handling of exit codes and Watchdog restarts for `once` apps is undocumented | M / M | D-133; the documentation says to keep the Watchdog off | Phase 8 (Q-07) |
| R-17 | The image redistributes copyleft OS packages, LGPL `samsungtvws`, and the copyleft components bundled in Pillow (R-25) | M / M | SBOM; D-135; minimal OS packages; copyleft surface is a D-130 criterion | Phase 6/7/9 licence audit |
| R-25 | **The Pillow wheels bundle GPL-3.0-or-later `libimagequant` 4.4.1 and LGPL-2.1-or-later FriBiDi 1.0.16.** The distributed image therefore contains GPL-3.0 code, and the runtime is not GPL-free. | H / M | Correct inventory (observed SBOM); D-135 source availability; qualified licence review as a release gate; authoritative re-inspection of the exact runtime wheels once the Python version is fixed; Apache-2.0 scoped to project code only (D-102) | Licence review (Phase 9) |
| R-18 | Provider terms or rate limits violated by accident | L / H | Allowances; 1 s pacing; 403/429 stop; cache; honest headers | Phase 3 review |
| R-19 | Art Institute renditions (1686 px) look soft after upscaling by up to ≈ 2.28×; images can be unpublished | H / M | Honest documentation; HTTP 404 moves to the next candidate; Cleveland renditions (≈ 1.13×) are an in-beta alternative | Accepted |
| R-20 | Provider documentation drifts. Examples: Cleveland's banner date is older than its changelog, and the Cleveland image host appears only in example URLs. | M / L | Re-verified on 2026-09-27 (D-146); re-check before the Phase 8 live test and before each release | Phase 8, each release |
| R-21 | The media browser may not be able to upload into `/media/frame_gallery/library` | M / M | The app creates the folder; the hint names its location; Phase 8 verifies uploads | Phase 8 |
| R-22 | **Provider identifier stability.** Neither the Art Institute nor Cleveland documents its record IDs as permanent. | L / M | IDs validated against patterns; Cleveland's accession number kept as metadata; history and ledger keyed by the documented ID; re-checked when documentation drifts | Phase 3 |
| R-23 | The **Cleveland API terms** reserve future keys, transaction limits, and IP logging | M / M | Room for an optional key (`password` option); 401/403 treated as a stop; conservative pacing; the source stays optional | Monitor |
| R-24 | The **uncertainty quarantine** holds back works that never actually reached the TV (for example after a power loss before upload) for the 30-day quarantine period | M / L | Intents are removed whenever no `upload_started` was seen; the period is documented (Q-23, accepted); large catalogues are unaffected | Accepted |
| R-26 | **Local tests run a different Pillow build.** Phase 2 tests use the macOS `arm64` Pillow wheel and CPython 3.12.14; the runtime uses the Linux `musllinux_1_2` wheels, with other bundled library builds, on the container's Python. Rendering bytes and edge-case behaviour may differ. | M / M | The imaging tests assert properties (size, baseline, components, pixels, metadata) rather than byte-exact output; Phase 6 runs the full suite inside the container image for both architectures; CI covers 3.12–3.14 (Phase 9) | Phase 6/9 |
| R-27 | **No pre-emption before Phase 5.** The Phase 2 in-process executor cannot interrupt a hung decode, so the 15 s preparation limit and the 70 s and 120 s bounds hold only when tasks return. A timeout is detected after the fact. | L / M | Phase 2 never runs against real providers or the television; the Phase 5 process executor adds the kill timer, `RLIMIT_AS`, and the unprivileged worker (D-109, D-139); the watchdog (130 s) remains the last resort | Phase 5 |
| R-28 | **The credential-pattern redaction is heuristic.** It catches common forms of unregistered secrets but not every serialization (D-145). | L / M | Every real secret (the Supervisor token, the TV token) is registered with the redactor and redacted in all its encodings; worker output passes through the parent's formatter; H3 tests cover both layers; new secrets must be registered where they enter | Ongoing (Phases 3, 5) |

## Open questions

### Resolved in the Codex review of `d42adf5`

| ID | Resolution |
| --- | --- |
| Q-01 | Google Arts & Culture is **removed from the beta scope**. Its researched status stays documented, and undocumented or `robots.txt`-incompatible access is never implemented. |
| Q-02 | Replaced by the 120 s total deadline and its phase split. `no_match` finishes within 70 s (D-114). |
| Q-15 | Only the **installed** `samsungtvws` 3.0.6 distribution is inspected (D-104). |
| Q-16 | The app starts **without `host_network`**. Home Assistant Green-to-TV connectivity is verified in Phase 8 before any change. |
| Q-17 | Bing is **excluded**. |
| Q-18 | The specification is amended in this revision: providers, the filter model, the deadline, the upload ledger, and preview freshness (`PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` amendment logs). Item 4 was resolved in the final gate review (see below). |
| Q-20 | The 30-probe limit means **30 remote dimension requests**. Local header inspection has its own bounded allowance of 300. |

### Resolved in the Codex final gate review of `9352e77`

| ID | Resolution |
| --- | --- |
| Q-03 | **Square band** stays 0.95–1/0.95. **Strict near-16:9** becomes ±1 % in log ratio, `abs(ln(r / (16/9))) ≤ ln(1.01)`, about 1.760–1.796; this may be revisited after Phase 8 visual testing. The **maximum upscale** stays 2.5× (D-116). |
| Q-04 | The proposed bounded local-media fingerprint identifier is accepted (D-118). |
| Q-08 | The Art Institute of Chicago is the default remote source (D-120, D-123). |
| Q-09 | Accepted: the UI-created card, the script, the 150-second timer helper, the enabled Running sensor, and the optional post-run refresh automation (§16.3, D-140). |
| Q-11 | No fallback in `cover` mode. Fallback is available only with `landscape_only` and `contain` (D-117). |
| Q-12 | Only IPv4 literals in **RFC 1918** private ranges are accepted. `169.254/16` link-local is rejected, as are loopback, unspecified, multicast, broadcast, and the container and Supervisor internal networks. `192.168.178.30` stays solely the user-supplied Phase 8 test value (D-125). |
| Q-18 item 4 | The architecture order is adopted: record the confirmed sent history before publishing the preview (D-113). `PRODUCT_SPEC.md` is amended. |
| Q-23 | The uncertainty-quarantine period is **30 days** (D-137). |

### Resolved at the user's approval of Phase 3 (2026-09-27)

| ID | Resolution |
| --- | --- |
| Q-14 | Small, curated, versioned vocabularies, built from the re-checked official documentation only. Labels are distinct across the museums. Normalization, aliases, and uniqueness are tested. A category that the documentation does not map reliably is left out, and the limitation is documented (D-146). |
| Q-22 | The project contact is `volkue@gmail.com` (D-119 as amended). Phase 3 still makes no live API request; the real address is transmitted only in a later, explicitly approved live request. Tests use a placeholder. |

### Resolved at the Phase 3 gate (2026-09-27)

| ID | Resolution |
| --- | --- |
| Q-25 | **Option (a), final.** The first beta ships without a colour filter, and the Art Institute supports only the period filter; Cleveland supports department and period. No live Art Institute observation is approved: neither `category-terms` nor any other provider API endpoint is called. Unsupported filters are reported as B8 requires. `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` (B2, C1) are amended to apply only to the filters the selected source supports. |

### Open

| ID | Question | Recommendation | Needed by |
| --- | --- | --- | --- |
| Q-05 | JPEG parameters (quality 90, standard subsampling, 15 MiB ceiling) | Start here; tune in Phase 8 | Phase 8 |
| Q-06 | A user-facing way to reset history or re-pair the TV? | Not in the beta; reinstalling is the reset path | Phase 6 |
| Q-07 | Confirm D-133: how `once`-app exits are shown, and how the app Watchdog reacts | Keep D-133; observe in Phase 8 | Phase 8 |
| Q-10 | Should the parent process also run unprivileged? | Evaluate in Phase 6. The workers are unprivileged from Phase 5 (§11.3). | Phase 6 |
| Q-13 | The final public repository URL, which determines the slug shown in the dashboard YAML | Decide with D-101 | Phase 9 |
| Q-19 | `hassio.app_start` is admin-only. Test the non-admin paths: a script, the Running switch, `continue_on_error`, a mistyped slug. | Document the admin requirement; test in Phase 8 | Phase 8 |
| Q-21 | Install route for Phase 8: (a) copy the folder into `/addons` through a file-share app; (b) a temporary private repository; (c) a development image push | (a) | Phase 8 |
| Q-24 | Cleveland colour filtering by local analysis, for example of the documented 900 px web rendition, counted against the existing download allowance and the content-window time budget, not against the 30 remote dimension requests. Only if it fits the same download and time budgets. | Defer until after the beta | After the beta |

## Review records

### Internal review of the store commits `a74ba1c`, `1677ccd`, and `f347ffb` (Claude, Phase 4)

One independent reviewer checked crash safety, the reader, the ledger and the state store, the bounds, test quality, and D-153 to D-155. It ran reproductions against a snapshot of `f347ffb`, in a scratch directory, and injected failures into every system call of a ledger write (9 points), a delivered run (27 points), and the store's whole life cycle (113 points). Seven findings were confirmed, all fixed in the commit that follows `5435d06`:

1. **Medium.** A timestamp at the limits of `datetime` (for example `0001-01-01T00:00:00+05:00`) raised `OverflowError` in the reader and the ledger: every run would have ended as `internal_error`, and the file was never quarantined.
2. **Medium (design interaction).** The ledger pruned a work as soon as the history primary held it. If a later run then committed an intent without recording (the television off) and the primary was damaged afterwards, the one-generation-old `.bak` no longer excluded the newest delivered work.
3. **Low.** The sweep pattern missed the `.bak` temporary files of names of 97 to 100 characters (latent).
4. **Low.** A newer-version file over this version's size bound was quarantined instead of ending the run with `state_error`.
5. **Low.** A failed `RunWorkspace.create` left a half-made run directory for the next sweep.
6. **Low (documentation).** D-154 said every ledger write prunes; only the intent write does.
7. **Low (documentation).** Docstrings claimed that only parse failures are quarantined, and that `decode_json` refuses every infinity (`1e400` passed).

Test gaps, all closed: the guard that keeps a damaged primary from becoming `.bak` was tested only in a case where the quarantine had already removed the primary; the loser's lock descriptor was never checked; the ledger's exact byte bound was untested. Each new test was checked to fail against the defect or the mutation that the reviewer used.

The reviewer confirmed as sound: no interleaving leaves the primary missing or a damaged `.bak`; no descriptor leaks under failure injection; memory always matches the files; the committed intent is durable before success is reported; the lock and the sweep order; the reader on links, FIFOs, sockets, directories, deep nesting, invalid UTF-8, and duplicate keys; and the history and ledger bounds, without off-by-one errors.

### Phase 3 gate decision (user, 2026-09-27)

- Q-25 is decided finally with option (a): the first beta ships without a colour filter.
- No live Art Institute observation is approved. Neither `category-terms` nor any other provider API endpoint may be called. Live provider requests stay reserved for a later, explicitly approved phase (Phase 8, D-150).
- Accepted:
  - D-146 to D-152;
  - the Art Institute supports only the period filter in the beta;
  - Cleveland supports department and period;
  - no source supports colour for now;
  - unsupported filters are visibly reported as B8 requires.
- `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` are amended so that B2 and C1 apply only to the filters the selected source supports. Both amendment logs record the change.
- The Phase 3 gate is passed. Phase 4 does not start until it is authorized.

### Internal review of the helper reader `f614256` and local media `8761cca` (Claude, Phase 3)

One independent reviewer checked security, correctness against the requirements, time bounds, and test quality. Proofs used scratch scripts, with local files and a socket pair only. Six findings were confirmed, and all are fixed in the commit that follows `72dba4a` (amendments to D-147, D-148, and D-149):

1. **Medium.** Symbolic links in the middle of a path were followed. A subfolder swapped for a link during discovery made a file outside the library usable, fetchable, and able to bypass preview guard 1.
2. **Low-medium.** An I/O error while copying a library file ended the run as `internal_error` instead of trying the next candidate.
3. **Low.** The token could reach any private LAN address, or a 6to4 or Teredo address embedding a public IPv4 address.
4. **Low.** An inspection cut off by the discovery deadline was reported as a failed inspection of a healthy file.
5. **Low.** A library cut short by the entry limit got the "no usable images" hint.
6. **Low, test quality.** The aggregated-warning test tolerated six examples, and its hostile-name check depended on directory order.

The reviewer confirmed as sound:

- the helper bounds, measured on the real stack: 3 s per stalled read, 10 s for four dripping helpers;
- exactly one WARNING per fallback;
- token hygiene;
- the depth, entry, and size limits, and the D-118 fingerprint;
- FIFO handling;
- the inspection contract;
- sanitized file names;
- the fetch re-check.

### Internal review of the gateway commit `51d9cf3` (Claude, Phase 3)

One independent reviewer checked security, D-115 correctness, time bounds, and test quality, and verified each finding with a scratch script, using only a local socket pair (no network). Five findings were confirmed, and all are fixed in the commit that follows `8761cca` (D-147 amendment):

1. **High.** The exchange timer and the per-read timeout stopped working after a `Connection: close` response, because the connection's socket reference disappears. A dripping peer held one read for the whole drip: 8.3 s against a 0.5 s limit.
2. **Medium.** urllib3 reset the socket timeout to the connect timeout before sending and before reading the headers, so a slow first byte failed early, and body gaps were bounded by the connect timeout.
3. **Medium-low.** urllib3's own warnings put the request URL, query included, and header data into the log.
4. **Low.** Deprecated site-local IPv6 addresses passed the public-address check.
5. **Low, test quality.** `from http import server` was not flagged in the transport module.

The reviewer also confirmed as sound: the URL policy, the TLS setup (a fresh context, `certifi` only, host-name checking on, SNI, the post-handshake check), the address rules, header injection, gzip handling, file creation, the D-115 retry and stop logic, and the deadline semantics.

Writing the fix's real-stack tests exposed a further defect: once a `Connection: close` body was complete, re-clamping the closed socket's timeout raised `OSError`. That would have failed every such response. It is fixed and tested too.

*Disclosure.* To confirm finding 1, the reviewer once ran `grep` on the standard library's `http/client.py`, which lives with the local interpreter outside the repository. That is language source, not predecessor material; after that it checked behaviour only by running scripts.

### User approval of Phase 3 (2026-09-27)

The user approved Phase 3 with these binding decisions and limits:

1. D-141 to D-145 are accepted.
2. D-108, D-112, D-115, D-124, D-127, D-131, D-134, and the Phase 3 adapter details of D-132 and D-136 are accepted.
3. D-119 is accepted with an amendment: no invented or not-yet-existing project URL; the User-Agent is `FrameGallery/<version> (contact: volkue@gmail.com)` until a public URL is decided; the `AIC-User-Agent` may use the same contact; tests keep a clearly recognizable placeholder; the headers switch to the real repository URL before publication.
4. Q-14 is decided as recommended: small, curated, versioned vocabularies from the re-checked official documentation, with labels distinct across the museums; normalization, aliases, and uniqueness tested; no undocumented values; a category the documentation does not map reliably is left out, and the limitation documented.
5. Q-22 is decided: the project contact is `volkue@gmail.com`. Phase 3 makes no live API request; the real address is transmitted only in a later, explicitly approved live request.
6. The direct dependencies `urllib3` 2.8.0 (MIT) and `certifi` 2026.7.22 (MPL-2.0) are approved, installed only into the git-ignored project environment from PyPI, with the lock, the hash-pinned runtime requirements, the inventory, and `THIRD_PARTY_NOTICES.md` updated and the installed package metadata checked.
7. At the start of Phase 3, only the official Art Institute and Cleveland documentation pages may be re-read. No API endpoint, no image or metadata request, and no recorded live observation. Tests use only independently authored or synthetic fixtures. No predecessor project is consulted.
8. Only Phase 3 of `TASKS.md` is implemented. No connection to Home Assistant Green or the television, nothing pushed or published, no container published, and the local backup branch is neither changed nor published.
9. The work is split into small, focused commits: documentation re-check and approved decisions; network gateway and dependencies; Home Assistant helper reader; local media provider; Art Institute adapter; Cleveland adapter; vocabularies, the shared contract tests, and the closing documentation.
10. Every commit is checked for the identity `Alexander Wilke <volkue@gmail.com>`. SatoshiPay, EBMA, and Marcel accounts, addresses, credentials, organizations, and repositories are never used.

At the end, all quality gates run, `STATUS.md`, `DECISIONS.md`, `TASKS.md`, and the licence and dependency documentation are updated, and the work stops at the Phase 3 gate for the Codex review.

### Phase 2 internal review (Claude, before the Phase 2 commit)

**Method.** Five independent review lenses (architecture conformance, Phase 2 scope and acceptance coverage, control-flow correctness, image pipeline and security, test quality), each followed by an independent skeptical verifier who tried to refute every finding with reproductions.

**Result.** 75 findings: 61 confirmed (after merging duplicates across lenses, about 30 distinct issues), 12 refuted, and 2 uncertain.

**Most important confirmed issues, all fixed with regression tests:**

1. A stop request could be swallowed by a generic `except Exception` (for example inside the standard library's logging handler), after which the run still contacted the television. Fixed by D-141 (stop requests).
2. Worker timeouts at the task's own limit were classified as "search limits reached" whenever the clock moved between two readings. Fixed by deciding from deadlines (D-141, item 2).
3. Camera JPEGs with an MPF index (MPO) were refused (D-144).
4. Header floods could make Pillow use gigabytes before any limit applied (D-144, pre-scan).
5. A FINISH after a PRE-STAGE outcome received an already-expired deadline, so a deadline-honouring store would lose the last-run record.
6. After `selected`, an adapter failure skipped RECORD (D-141, item 5).
7. Redaction gaps: truncation before redaction, and missing credential patterns (D-145).
8. Weak or vacuous tests, including the 70 s bound test, deadline propagation, and the boundary and network guards. Each was strengthened and checked to fail against the defect.

**Recorded rather than changed:**

- the §9.1 and §12.1 port shapes (D-141);
- the D-128 lock workflow (D-142);
- the empty provisional vocabulary (D-143);
- the absence of pre-emption before Phase 5 (R-27);
- the uncertain finding on discovery-endpoint 404s, resolved by D-141 item 3.

**Re-verification.** A focused re-verification then checked every confirmed finding against the current code:

- 57 of 63 were fully fixed; the remaining gaps were closed afterwards.
- Adversarial sweeps found two windows in the first stop-request fix, and header-bomb and redaction bypasses in the new code. They led to:
  - the whole-call deferral of D-141;
  - the TIFF-directory bounds of D-144;
  - the extra redaction patterns of D-145.
- The sweeps inject a stop request, directly and as a real SIGTERM, at every Python function entry (11 641 points) and every traced line (5 429 points) across nine delivery and no-match scenarios. Run again against the final design with the production controller configuration (`start_deferred=True`), they report no violations: no marker, ledger write, RECORD, last-run record, or summary line is lost, and nothing is uploaded after an undeferred stop.

### Codex final approval of Phase 1 at commit `dda877c` (external)

**Outcome:** Phase 1 is approved. Phase 2 (core, deterministic selection, and rendering) is authorized; Phase 3 is not.

**Gate adjustment, explicitly approved by Codex:**

- Verification of the remaining lower-risk `pillow.libs` entries (libXau, libXdmcp, Brotli, libbsd, liblzma, libmd, libpng, libsharpyuv, and libzstd) moved from the Phase 2 approval gate to the authoritative Phase 6 runtime-wheel inspection. The exact runtime wheel cannot be selected until the container's Python version is fixed in Phase 6.
- The provisional notices created in Phase 2 keep the known Pillow inventory, including `libimagequant` and FriBiDi.
- Full verification remains mandatory before packaging or publication.
- The GPL/LGPL licence review and the source-availability obligations remain release blockers and are not weakened.

### Codex final gate review of commit `9352e77` (external)

**Outcome:** the architecture changes were accepted. One factual dependency error had to be corrected before Phase 2. Phase 1 stays open until the gate is approved again.

Applied in the documentation-only commit that follows `9352e77`:

1. **Pillow wheel inventory.**
   - Codex inspected the official Pillow 12.3.0 wheels. The earlier claim that the PyPI wheels omit `libimagequant` was false and has been withdrawn.
   - The wheels bundle GPL-3.0-or-later `libimagequant` 4.4.1 and LGPL-2.1-or-later FriBiDi 1.0.16, with its shim. The full SBOM table is recorded, and the additional `pillow.libs` entries are marked for verification.
   - Apache-2.0 covers project-owned code only (D-102). The runtime image is not GPL-free.
   - Both libraries are added to D-135, and the qualified licence review remains a release gate. R-25 records the risk.
   - Pillow 12.3.0 stays proposed. The inspection is repeated against the exact runtime wheels once the Python version is fixed (D-130 check (a)); that result is authoritative.
2. **Development-only rows.** `mypy-extensions` 1.1.0 (MIT) and `pathspec` 1.1.1 (MPL-2.0) were recorded; neither is shipped.
3. **Accepted decisions.** Q-03, Q-04, Q-08, Q-09, Q-11, Q-12, Q-18 item 4 (D-113), and Q-23. See *Resolved in the Codex final gate review of `9352e77`*. `PRODUCT_SPEC.md` and `ACCEPTANCE_TESTS.md` were amended where these decisions are normative.

### Codex review of commit `d42adf5` (external)

**Outcome:** the architecture was conditionally accepted. Phase 2 was **not** approved.

The user's decisions and the review's corrections were applied in the revision-2 commit that follows `d42adf5`:

1. **Beta providers.**
   - Google Arts & Culture and Bing were removed, and their researched status was kept.
   - The beta sources are local media, the Art Institute of Chicago, and the Cleveland Museum of Art. Cleveland is now normative (D-136): CC0 records only, and the documented print JPEG only.
   - The filter dimensions are now distinct: source/museum, department/collection, style/period, and colour. They come with an honest capability matrix and visible reporting (D-124).
2. **Runtime.** A 120 s total, split 10 / 60 / 40 / 10 s. All timeouts are clamped. `no_match` finishes within 70 s. The dashboard timer is 150 s. The 30 probes are remote requests (D-114).
3. **Duplicate prevention after an upload.** A TV-upload exclusion ledger, with a write-ahead uncertainty quarantine (D-137), and acceptance items `E7`–`E10`.
4. **Preview.** The Local File camera stays primary, and its platform basis is recorded (D-111). Freshness is release-blocking, with the mechanism selected in Phase 8 (D-140). Collection Image is optional and does not raise the minimum Home Assistant version.
5. **Approved decisions:**
   - `frame_gallery` as the identifier (D-138);
   - Apache-2.0 (D-102);
   - `uv` (D-128);
   - an IPv4 literal for the TV address (D-125); the test value `192.168.178.30` is not hard-coded;
   - no `host_network` at first (Q-16);
   - inspecting only the installed `samsungtvws` (D-104);
   - `contain`, landscape-only, and strict 16:9 as defaults (D-123), with no crop;
   - bounded cleanup and atomic writes (D-106, D-110);
   - the clean-room rules.
6. **Implementation sequencing.** A vertical slice (D-139). `TASKS.md` was updated.

The corrections were checked by cross-reference and consistency checks and by an independent review of the revision.

### Internal multi-agent review of revision 1: findings not adopted

The Phase 1 multi-lens review produced 98 raw findings. The adjudicator confirmed 58, which are incorporated. It listed 7 entries as not adopted: 6 rejections and 1 severity downgrade. They are listed here so they can be challenged:

1. **Pin third-party GitHub Actions to commit SHAs and apply least-privilege job permissions.** Rejected as general CI hardening, not a specification gap. It belongs to the Phase 9 release work (§17.3), where it is expected to be applied.
2. **Log local media by fingerprint only, since filenames are private data.** Rejected: the log is the user's own app log, and the specification's list of forbidden log content does not cover the user's own filenames. Warnings need the path to be actionable.
3. **"Security rating 6" wording.** Rejected: 6 is achievable and is the scale maximum. The nuance that Ingress would also reach 6 does not affect any decision.
4. **The Ingress comparison overstates "session handling".** Rejected as immaterial: the other listed costs, and the one-shot incompatibility, still hold. The row now says "request handling".
5. **Appendix A item `C4` should name the verifying provider.** Rejected: it already names the counting fake gateway.
6. **Drop the `.bak` generation as a simplification.** Rejected as a design preference. The real defects around `.bak` were fixed.
7. **Rate the probe-limit, watchdog-orphan, and memory findings as major.** Downgraded to minor rather than rejected: a dead option, an orphan that needs a second failure, and rare near-cap images. All three were fixed.
