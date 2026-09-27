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

Status: proposed

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

Status: proposed

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

Status: proposed

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

Status: proposed

**Decision:**

- The User-Agent is `FrameGallery/<version> (+<project URL>)`.
- Provider courtesy headers, such as the Art Institute's `AIC-User-Agent`, carry the project name and a project-owned contact email (Q-22), never user data.
- There is no browser impersonation.

### D-120 — First public beta scope [§22]

Status: **accepted** as amended in the Codex review. `PRODUCT_SPEC.md` is amended accordingly.

**Included:**

- **Sources:**
  - local media;
  - the **Art Institute of Chicago** (D-132), the default remote source (Q-08, accepted);
  - the **Cleveland Museum of Art** (D-136).
- **Filters:** source, department, style/period, and colour, with the capability matrix and visible reporting of unsupported filters (D-124); optional helpers.
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
- `landscape_only`, `strict_tv_format`, `fit_mode`, `background_color`;
- four optional `*_helper` options;
- `log_level`.

There is no time-limit option and no library-path option.

### D-124 — Filter model, vocabularies, and capability matrix [§9.2, §15.2]

Status: proposed, as required by the Codex review.

**Decision:**

- **Four distinct dimensions:**
  1. source/museum, which selects the provider (a department is never called a museum);
  2. department/collection, namespaced by source;
  3. style/period;
  4. colour.
- **Capability matrix**, published in `DOCS.md` and in the option descriptions:
  - Art Institute: department, style, period, and colour.
  - Cleveland: department and period. Style and colour are unsupported in the beta.
  - Local media: none of the four.
- **Visible reporting.** A filter that does not apply to the selected source is ignored for the run and reported in three places:
  - a WARNING;
  - `ignored_filters` in the summary line;
  - `last_run.json`.
- **Helper values.** A helper value that normalizes to no vocabulary key falls back to the static value, with one warning. A known key that does not apply to the selected source overrides the static value, and is then ignored and reported like a static value.
- **Vocabularies.** Versioned, with deterministic normalization. The final lists are fixed in Phase 3 (Q-14).

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

Status: proposed

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

Status: proposed

**Decision:**

- The gateway uses `urllib3` 2.x with retries and redirects disabled, streaming, and explicit timeouts. It enters as a direct dependency in Phase 3.
- `requests` is not used by application code.
- `httpx` is not adopted.

### D-132 — Art Institute of Chicago adapter [§9.5]

Status: **accepted** as a beta source (Codex review). The adapter details are proposed.

**Decision.** Use the documented API:

- public-domain works only. `is_public_domain` is requested in `fields`, and every record must have `is_public_domain == true` and an image id;
- department, style, period, and colour from documented metadata. Colour is filtered server-side if range queries work, and client-side otherwise;
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

Status: proposed

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

Status: **accepted** as a beta source (Codex review). The adapter details are proposed and are re-verified against the live documentation in Phase 3.

**Decision.** Use only the documented Open Access API:

- **Every request** carries the `cc0` flag and `has_image=1`.
- **Every record** must have `share_license_status == "CC0"` and an `images.print` entry.
- **Rendition:** only the documented print JPEG (3400 px long side, JPEG). Its string-typed `width` and `height` are parsed defensively. The `full` TIFF is never requested.
- **Filters:**
  - `department`, using the 21 documented values;
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

## Phase 2 implementation decisions (proposed)

These record how Phase 2 realized the architecture, and every place where it deviates from the text of `ARCHITECTURE.md`. They are proposed for approval at the Phase 3 gate.

### D-141 — Phase 2 layout, seams, and classification details [§4, §5, §9.1, §12, §21]

Status: proposed.

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

Status: proposed.

- **`uv`.** Version 0.12.19, installed from PyPI into the git-ignored `.tools/` directory with its wheel hash checked against PyPI. `pyproject.toml` pins `required-version`, sets `python-downloads = "never"` (interpreters would come from outside the package index), and limits the lock to macOS and Linux.
- **Lock.** A project `uv.lock` with hashes for the whole development environment. `requirements/runtime.txt` is exported from it with `uv export --locked --no-dev --no-emit-project`, hash-pinned. This replaces the separate `uv pip compile --generate-hashes` step of D-128, so the development and runtime pins cannot drift apart. Installs keep `--require-hashes --no-deps --only-binary=:all:`. The Phase 6 container build narrows the runtime file to the chosen Python version and platform.
- **No build backend.** The project is not built as a distribution (`package = false`), so no build backend enters the inventory.
- **Local interpreter.** No Python 3.12+ interpreter was installed on the development machine apart from the CPython 3.12.14 bundled with the local Codex desktop runtime. Phase 2 uses it as the base interpreter of the project environment; nothing was downloaded and nothing outside the repository was modified. Python 3.13 and 3.14 are verified in CI (Phase 9), or earlier if a local interpreter is provided.
- **Gates.** `scripts/check.sh`: Ruff check and format; `mypy --strict` over `src` and `tests`; pytest with branch coverage of at least 90 % overall and 100 % for `budget`, `selection`, `isolation`, `providers`, the outcome classification, the runner, and the imaging worker tasks (§20.4).

### D-143 — Provisional built-in vocabulary [§15.2, D-124]

Status: proposed.

- Phase 2 ships the vocabulary *mechanism*: normalization, keys, labels, aliases, and the per-field lookup. The built-in vocabulary is empty (version `0-provisional`). Tests use synthetic vocabularies.
- Until Phase 3 fixes the real lists (Q-14), any static filter value other than `any` is therefore `config_invalid`.
- Within one option field every normalized key, label, and alias must map to exactly one key. A label shared by both museums (for example a "Photography" department at each) must therefore be made distinct in Phase 3, or the lookup made source-aware.

### D-144 — Image pipeline details [§11.1, D-121, D-122]

Status: proposed.

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

Status: proposed.

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

## Proposed dependency inventory

Status: **Phase 2 installed** the development tools and Pillow, and only in the local project environment (`frame_gallery/.venv`, from `uv.lock`). The runtime rows for later phases are still proposed.

- Versions and licenses were read from PyPI metadata (`https://pypi.org/pypi/<name>/json`) on 2026-09-26.
- In Phase 2 the installed versions and `License-Expression` fields were re-read from each installed distribution's metadata; they match the rows below.
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
| `urllib3` | PyPI `==2.8.0` (`<3`), `py3-none-any` | `MIT` (`LICENSE.txt`) | dyn, redist | License text | Gateway transport (D-131) | Phase 3 |
| `certifi` | PyPI `==2026.7.22`, `py3-none-any` | `MPL-2.0` (`LICENSE`) | dyn, redist (CA bundle) | Files kept unmodified under MPL-2.0; identified in the notices; source pointer (D-135) | The gateway's explicit CA bundle (§10) | Phase 3 |

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
| R-20 | Provider documentation drifts. Examples: Cleveland's banner date is older than its changelog, and the Cleveland image host appears only in example URLs. | M / L | Re-verify the live documentation at the start of Phase 3 | Phase 3 |
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

### Open

| ID | Question | Recommendation | Needed by |
| --- | --- | --- | --- |
| Q-05 | JPEG parameters (quality 90, standard subsampling, 15 MiB ceiling) | Start here; tune in Phase 8 | Phase 8 |
| Q-06 | A user-facing way to reset history or re-pair the TV? | Not in the beta; reinstalling is the reset path | Phase 6 |
| Q-07 | Confirm D-133: how `once`-app exits are shown, and how the app Watchdog reacts | Keep D-133; observe in Phase 8 | Phase 8 |
| Q-10 | Should the parent process also run unprivileged? | Evaluate in Phase 6. The workers are unprivileged from Phase 5 (§11.3). | Phase 6 |
| Q-13 | The final public repository URL, which determines the slug shown in the dashboard YAML | Decide with D-101 | Phase 9 |
| Q-14 | Initial vocabularies: AIC departments, style and period keys, AIC colour bands, and the subset of the 21 CMA departments to offer | Small curated lists after the Phase 3 mapping | Phase 3 |
| Q-19 | `hassio.app_start` is admin-only. Test the non-admin paths: a script, the Running switch, `continue_on_error`, a mistyped slug. | Document the admin requirement; test in Phase 8 | Phase 8 |
| Q-21 | Install route for Phase 8: (a) copy the folder into `/addons` through a file-share app; (b) a temporary private repository; (c) a development image push | (a) | Phase 8 |
| Q-22 | The project-owned contact email for the Art Institute courtesy header. It is needed before any live request; tests use a placeholder. | Decide before any approved observation request | Phase 3 |
| Q-24 | Cleveland colour filtering by local analysis, for example of the documented 900 px web rendition, counted against the existing download allowance and the content-window time budget, not against the 30 remote dimension requests. Only if it fits the same download and time budgets. | Defer until after the beta | After the beta |

## Review records

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
