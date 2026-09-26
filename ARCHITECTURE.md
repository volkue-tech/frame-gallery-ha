# Frame Gallery for Home Assistant — Architecture proposal

Status: **Proposed. Awaiting user and Codex approval (Phase 1 gate).**
Date: 2026-09-26
Author: Claude (Phase 1 owner)

This document is documentation only. The YAML fragments, signatures, and pseudo-code below illustrate interfaces and configuration *shape*. They are not application code. Everything is authored and tested in the phases that follow approval.

Cross-references:

- `D-1xx` are decisions, `R-xx` are risks, and `Q-xx` are open questions; all three live in `DECISIONS.md`.
- Acceptance items such as `C4` refer to `ACCEPTANCE_TESTS.md`: the section letter, then the item's position within that section.

How this proposal was checked:

- Four of the five Phase 1 research areas were independently re-checked. The Python-dependency facts were not re-checked; they are verified again from the pinned distributions before each dependency enters.
- The draft was then reviewed by six independent reviewers, each with a different focus: specification traceability, bounded execution, security, platform correctness, licensing, and consistency. An adjudicator verified their findings, and this version incorporates all 58 confirmed findings.

---

## 1. Summary of the recommendation

Frame Gallery is a **single-shot Python program packaged as a Home Assistant app**. Each start performs exactly one bounded *run*:

1. validate options;
2. resolve filters;
3. shortlist at most two artworks from one source;
4. prepare a 3840 × 2160 JPEG for the first candidate that passes;
5. upload and select it on the television;
6. record it in history;
7. publish the same bytes as the dashboard preview;
8. clean up and exit.

The architecture rests on eight decisions:

1. **Synchronous core, explicit budgets, last-resort watchdog** (D-106, D-114).
   - One thread runs the run.
   - Each phase gets a budget from a normative decomposition table. Every blocking call's timeout is derived from its phase's `Deadline`.
   - A watchdog ends the process, and any worker process group, if the total run limit plus a 10 s allowance is ever exceeded.
2. **Ports and adapters** (D-107). The orchestrator depends only on narrow interfaces: clock, random source, HTTP transport, provider, television, file store, and isolated executor. Real adapters sit at the edges; tests substitute fakes.
3. **One guarded internet gateway** (D-108). All provider traffic passes through one gateway. It:
   - resolves each host once and connects only to validated global addresses;
   - enforces HTTPS with certificate verification;
   - applies label-exact host allowlists;
   - re-validates every redirect hop;
   - caps decoded bytes;
   - enforces per-request total timeouts;
   - honours provider pacing.
4. **Unprivileged, isolated workers for everything that parses images or talks to the television** (D-109). Image inspection, decoding, and rendering, and the whole Samsung library interaction, run in spawned child processes with these properties:
   - an allowlisted environment;
   - an unprivileged user ID;
   - an address-space ceiling and a kill timer;
   - a bytes-only JSON result channel.

   The parent process never imports Pillow or the Samsung library. A hostile image or a hung television socket therefore becomes a classified outcome, not a stalled or compromised run.
5. **Plain JSON state with an atomic write protocol** (D-110). All state lives under `/data`: history, current-artwork record, last-run record, and a small metadata cache. Every write is atomic.
   - History additionally keeps a second generation (`.bak`).
   - The next history generation is *pre-staged and fsynced before the television is touched*, so recording after a successful selection is a single rename.
   - Scratch files live on a RAM-backed `/tmp`.
6. **Preview through Home Assistant's own UI-configured Local File camera** (D-111). The exact bytes delivered to the television are published atomically to `/media/frame_gallery/preview/latest.jpg`. A dashboard card shows them and starts the app with `hassio.app_start`.
7. **Filters: static options always, optional helper overrides** (D-112). Helper states are read through the Supervisor's Core API proxy, and only when configured. No Ingress UI. A companion integration is deferred (§16).
8. **Smallest useful public beta** (D-120), built for `aarch64` and `amd64`, with two sources:
   - local media;
   - the Art Institute of Chicago's documented open-access API (CC0 public-domain images).

   The Art Institute's documented metadata includes dominant colour, style, department, and image dimensions, so strict 16:9 selection needs no probes. Phase 4 checks whether colour can be filtered server-side; if not, colour is checked on the returned pages within the same allowances.

   The specification names Google Arts & Culture and Bing as initial sources. Phase 1 found no documented API for either:
   - Google Arts & Culture's `robots.txt` allows public HTML pages and disallows `/api/*`. The main obstacles are Google's Terms and the partner museums' image rights.
   - Bing's `robots.txt` disallows its image path `/th?` for all general crawlers, and its use terms restrict the photos (§9.3).

   Building either would first require changing a rule in `LEGAL_BOUNDARIES.md`. The decision is the user's (Q-01, Q-17).

---

## 2. Inputs, principles, and independence

### 2.1 Inputs

This proposal draws only on:

- the repository specifications: `PRODUCT_SPEC.md`, `ARCHITECTURE_CONSTRAINTS.md`, `ACCEPTANCE_TESTS.md`, `LEGAL_BOUNDARIES.md`, `TASKS.md`, and `DECISIONS.md`;
- the official Home Assistant developer and user documentation;
- package-index metadata and dependency documentation sites;
- artwork providers' published policy pages, `robots.txt` files, and documented APIs.

No predecessor project, its repository, its documentation, or any community write-up about Frame art automation was consulted, and no GitHub-hosted page was fetched. §25 lists the sources.

### 2.2 Design principles

| Principle | Consequence in this design |
| --- | --- |
| Everything is bounded | Every loop has an allowance, every request a total timeout, every phase a budget, and every worker a kill timer. A watchdog backs them up. |
| The television is touched last and only when ready | Before any television connection is opened, three things must be true: a validated JPEG exists; the next history generation is already on disk; and the whole television budget remains. |
| Record only after success | History changes only after the television confirms selection. Once it does, recording cannot be cancelled. |
| All input is untrusted | Options, helper states, provider metadata, URLs, identifiers, filenames, image bytes, and worker results are validated where they enter. |
| Least privilege | No host network, privileged mode, Supervisor API role, or configuration-folder mapping. Workers run unprivileged. An AppArmor profile narrows filesystem access. |
| Observable outcomes | Every run ends with exactly one classified outcome, one summary log line, and a last-run record. The exception is watchdog termination, which writes only one log line before exiting. |
| Replaceable edges | Providers, the television transport, and the HTTP transport can each be swapped without touching selection or rendering. |

---

## 3. System context

```text
┌──────────────────────────── Home Assistant OS host (e.g. Home Assistant Green, aarch64) ────────────────────────────┐
│                                                                                                                      │
│  ┌──────────────── Home Assistant Core ────────────────┐          ┌──────────────── Supervisor ─────────────────┐    │
│  │ Dashboard card ── tap ──► action hassio.app_start ──┼─────────►│ starts the app container (one-shot)          │    │
│  │ Local File camera  ◄── reads preview/latest.jpg     │          │ writes options to /data/options.json         │    │
│  │ Helpers (dropdowns, optional)                       │          │ proxies Core REST API for the app            │    │
│  │ REST API  ◄──── http://supervisor/core/api ◄────────┼──────┐   └──────────────────────┬───────────────────────┘    │
│  └─────────────────────────────────────────────────────┘      │                          │ runs                       │
│                                                               │   ┌──────────────────────▼───────────────────────┐    │
│  /media/frame_gallery/                                        └───┤ Frame Gallery app container (exits after run) │    │
│    library/   user-supplied images  ──── read ───────────────────►│  parent: runner, selection, gateway, store     │    │
│    preview/latest.jpg  ◄──────────── atomic write ────────────────┤  workers: image (Pillow), television (library) │    │
│                                                                   │  /data  state   /tmp  RAM-backed scratch      │    │
│                                                                   └───────────────┬───────────────────┬──────────┘    │
└───────────────────────────────────────────────────────────────────────────────────┼───────────────────┼───────────────┘
                                             LAN, WebSocket (port and TLS per Q-15) │                   │ Internet, HTTPS
                                                                                     ▼                   ▼
                                                                          Samsung Frame TV    Selected provider + its image host
```

Traffic crosses only three boundaries:

- the local television;
- the one provider selected for this run, plus that provider's image host;
- the Supervisor's internal Core API proxy, used only when helper overrides are configured.

There is no telemetry.

---

## 4. Runtime model

### 4.1 Run lifecycle

```text
START ─► CONFIGURE ─► RESOLVE_FILTERS ─► SELECT ─► ┌─ ATTEMPT (≤ 2 shortlisted candidates) ─┐ ─► PRE-STAGE ─► DELIVER ─► RECORD ─► PUBLISH ─► FINISH
            │               │               │      │  FETCH ─► VERIFY/PREPARE (worker)      │        │           │          │          │          │
            ▼               ▼               ▼      │     └── failure: next candidate ◄──────┘        ▼           ▼          ▼          ▼          ▼
     config_invalid   (never fails;    no_match    └────────────────────────────────────────┘   state_error    tv_*   delivered_   delivered_  last-run
     already_running   falls back)     source_failed      source_failed / image_failed / no_match           cancelled unrecorded  with_warnings record
     state_error                                                                                deadline_exceeded
   ────────── every path, including SIGTERM and the watchdog, ends in CLEANUP (worker group killed, workspace removed) ──────────
```

| Stage | Responsibility | Television if the stage fails |
| --- | --- | --- |
| CONFIGURE | Scrub the environment (§17.5). Take the non-blocking state lock (§13.3). Sweep leftovers (§14). Load and validate options. Resolve and validate the television address once (§15.4). Create the run context. | unchanged |
| RESOLVE_FILTERS | Apply optional helper overrides. Any problem falls back to the static value. | unchanged (never fails) |
| SELECT | Discovery, history filtering, shape and format checks, ranking. Produces a **shortlist of at most two** candidates (§8.2). | unchanged |
| ATTEMPT | For each shortlisted candidate in order, bounded by the attempt budget: FETCH the rendition, then have the image worker verify its real dimensions and PREPARE the delivery JPEG. A failure moves on to the next candidate. | unchanged |
| PRE-STAGE | Validate `delivery.jpg` in the parent (§11.3). Write and `fsync` the next history generation, including the new identifier, as a temporary file (§13.2). Check that the full television budget remains. | unchanged |
| DELIVER | The television worker connects, checks art-mode support, uploads, and selects. It reports progress markers (§12.1). | see §12.4 |
| RECORD | Only if the `selected` marker was seen: rotate `.bak` (best-effort), then rename the pre-staged generation into place. Not cancellable. | changed |
| PUBLISH | Atomically publish the exact delivery bytes as the preview, and update the current-artwork record. | changed |
| FINISH | Write the last-run record (every outcome except watchdog termination), log the summary line, and exit. | — |

**Ordering note (D-113).** The product specification lists preview publication (step 9) before history persistence (step 10). This design records history first, immediately after the television confirms selection. If the process died between the two, a missing preview is harmless, but a missing history entry would allow a resend. Both orders satisfy "persist history only after a successful upload". The reordering is listed as a specification deviation (Q-18).

### 4.2 Outcome taxonomy and exit codes (D-133)

Every run ends with exactly one outcome. The outcome name appears in the summary log line, and in the last-run record for every outcome except watchdog termination.

| Outcome | Meaning | Television | History | Exit | Log |
| --- | --- | --- | --- | --- | --- |
| `delivered` | Selected on the television, recorded, and preview published | changed | +1 | 0 | INFO |
| `delivered_with_warnings` | Selected and recorded; the preview or a record file could not be written | changed | +1 | 0 | WARNING |
| `delivered_unrecorded` | Selected, but the history rename failed. The message names the identifier that may be resent. PUBLISH is still attempted. | changed | unchanged | 0 | ERROR |
| `no_match` | Nothing deliverable and no transport failure (see the classification rule below) | unchanged | unchanged | 0 | INFO, with a hint |
| `config_invalid` | Options or television address invalid | unchanged | unchanged | 0 | ERROR |
| `already_running` | The state lock is held by another process | unchanged | unchanged | 0 | WARNING |
| `state_error` | Persistent state cannot be used safely: history written by a newer version, or pre-staging failed (full or read-only `/data`) | unchanged | unchanged | 0 | ERROR |
| `source_failed` | Provider or network failure with nothing delivered (see the classification rule below) | unchanged | unchanged | 0 | ERROR |
| `image_failed` | Sniffing, validation, decoding, rendering, or encoding failed for every attempted candidate (including worker crash or memory limit) | unchanged | unchanged | 0 | ERROR |
| `tv_unreachable` | Could not connect, or the connection was lost, timed out, or returned an unexpected response before `selected` | unchanged; may hold the upload after `upload_started`, and may display it after `uploaded` (§12.4) | unchanged | 0 | ERROR |
| `tv_not_authorized` | Pairing prompt not accepted in time, or stored token rejected | unchanged | unchanged | 0 | ERROR |
| `tv_rejected` | Art mode unsupported, or the television explicitly refused the upload or the selection | unchanged, or holds an undisplayed upload if `uploaded` was seen | unchanged | 0 | ERROR |
| `deadline_exceeded` | Not enough budget left to start the television phase | unchanged | unchanged | 0 | ERROR |
| `cancelled` | SIGTERM (stop from the UI or the Supervisor). If `selected` was already seen, the run completes RECORD and ends as `delivered*` instead. | unchanged before DELIVER; per markers during it | unchanged | 0 | WARNING |
| `internal_error` | Unexpected exception (a bug) | unknown | unchanged, or +1 if raised after RECORD | 70 | ERROR with traceback |
| watchdog termination | Hard cap reached | unknown | unchanged, or +1 if after RECORD | 71 | ERROR, one line |

**Exit-code policy (D-133).** Every *classified* outcome exits 0; only bugs (70) and watchdog termination (71) exit non-zero. The reasons:

- A normal `no_match` must not look like a crash.
- The documentation does not define how the Supervisor treats non-zero exits of `startup: once` apps, or whether the user-facing app Watchdog would restart them. An automatic restart after, say, `tv_rejected` could upload again, outside the app's own bounded retry policy (acceptance item `C8`).

The outcome remains fully distinguishable through the summary line and the last-run record, as the product specification requires. The documentation tells users to keep the app's Watchdog off. Phase 8 verifies the behaviour (Q-07).

**Classification rule when nothing was delivered.** The rules are applied in order; the first that matches wins.

1. **`source_failed`** if any of the following holds:
   - discovery ended because of a provider or transport error: connect, TLS, DNS, its own request timeout, HTTP 5xx, a 403/429 stop (§7.4), or an unexpected format;
   - any probe during SELECT, or any attempt, failed at the transport level. That covers connect, TLS, DNS, request timeout, HTTP 5xx, a 403/429 stop, any non-success status other than 404 or 410, and a download over the decoded-byte cap or the declared `Content-Length`;
   - the SELECT deadline expired before the provider returned any candidate at all.

   A request cut off by its **phase deadline**, rather than by its own request timeout, counts as the deadline being reached, not as a transport error. Rule 3 then applies if candidates had already been returned.
2. **`image_failed`** if any attempt failed in processing: sniffing, decoding, rendering, encoding, or a worker crash, timeout, or memory-limit hit.
3. **`no_match`** otherwise. This covers:
   - an empty provider result;
   - every returned candidate already in history;
   - candidates evaluated and rejected;
   - allowances or the deadline reached after candidates were returned;
   - every attempt answered with HTTP 404 or 410 (the work is unavailable), or failing dimension verification.

   The hint distinguishes three cases: "filters too restrictive", "nothing new left for these filters", and "search limits reached".

The last case of rule 1 applies only when the deadline expires **before any candidate** was returned. If candidates were returned and evaluated before the deadline or an allowance ran out, the outcome is `no_match` with the "search limits reached" hint.

### 4.3 Concurrency model

- **One run thread**: the orchestrator and all parent-side I/O.
- **One watchdog thread**, armed at start with `total run deadline + 10 s`. If it fires, it:
  1. sends SIGKILL to the active worker's process group;
  2. removes the workspace best-effort;
  3. writes one log line;
  4. calls `os._exit(71)`.
- **At most one worker process at a time.**
  - Workers are started in their own process group, so the parent can kill the group on every exit path (normal, SIGTERM, watchdog).
  - Workers set `PR_SET_PDEATHSIG` **after** dropping privileges, because the kernel clears it on credential changes (§11.3). They therefore die if the parent dies.

There is no `asyncio`, no thread pool, and no concurrent provider requests (D-106). The workload is a short sequential pipeline. Pillow and the television library are synchronous, and fake-clock testing of bounded behaviour is simpler without an event loop.

**DNS resolution** is the one exception to the single-thread rule (§7.5):

- Each resolution runs in a fresh daemon thread, joined with a clamped timeout, and is abandoned if it hangs.
- The number of abandoned threads is bounded by the request allowances, and a daemon thread cannot outlive the process.
- CONFIGURE, the `ha` client, and the gateway all use this same resolver.

---

## 5. Component boundaries

The package name follows the working project name, `frame_gallery`. It serves as the provisional internal identifier for the package, the app slug, `/media/frame_gallery`, the User-Agent, and the television client name if the 3.0.6 API accepts one (Q-15). It changes mechanically if D-101 changes.

| Component | Responsibility | Depends on | Must not |
| --- | --- | --- | --- |
| `app` (runner, outcomes, context) | Orchestrates one run; maps results to outcomes; owns the workspace, the state lock, and the SIGTERM handling. | all ports below | Import third-party libraries. |
| `config` | Option parsing and validation, filter vocabularies, television-address validation. | stdlib | Perform network I/O, apart from the bounded address resolution in §15.4. |
| `ha` | Supervisor Core-API proxy client for helper states (§15.3). | `net.transport`, `budget` | Write any Home Assistant state. Run when no helper is configured. |
| `budget` | `Clock`, `Deadline`, `Allowance`, the phase-budget calculator, and the watchdog. | stdlib | Contain domain logic. |
| `net` | Guarded gateway: host policy, resolution, TLS, redirects, pacing, caps, streaming to the workspace. | `urllib3` and `certifi` (transport seam) | Serve the television, or any host outside a provider's policy. |
| `providers` | Provider contract; the local-media and Art Institute of Chicago adapters. | `net`, `store.cache`, `isolation` (the `inspect` task, for local media) | Decide eligibility. That belongs to `selection`. |
| `selection` | Candidate evaluation, shape classification, ranking, shortlist. | `providers` contract, `store.history` (read), `budget` | Perform network I/O itself. |
| `imaging` | Worker-side tasks: header inspection, safe decode, orientation, colour normalization, fit, encode. It also contains a small stdlib-only JPEG header validator that the parent uses. | Pillow (worker side only) | Run in the parent process. Touch the network or the persistent store. |
| `tv` | The `Television` port; the worker-side Samsung task; the parent-side token store. | Samsung library (worker side only) | Be used except through the port. |
| `store` | Atomic file primitives, history, metadata cache, workspace, preview publisher, run records. | stdlib | Know about providers or the television. |
| `isolation` | Spawns a registered task in an unprivileged, resource-limited child process. Streams progress markers and returns a validated bytes-only JSON result. | stdlib `multiprocessing`, `resource`, `os` | Run arbitrary callables, or unpickle anything the child sends. |
| `logs` | Logging setup (parent and workers), formatter-level redaction, sanitization, the summary line. | stdlib | Emit bodies, header values, or query strings. |

Dependency direction is strictly inward: `app` → ports → adapters.

Third-party imports are confined to three places: `imaging` worker tasks (Pillow), the `tv` worker task (Samsung library), and `net.transport` (`urllib3`, `certifi`). An import-boundary check enforces this from Phase 2 (D-107).

---

## 6. Data flow

```text
options.json ─► Options ─► FilterSet(static) ─► ha.resolve_overrides ─► FilterSet(effective + provenance)
                                                                                │
      ┌─────────────────────────────────────────────────────────────────────────┘
      ▼
providers[source].iter_candidates(FilterSet, RunContext) ──lazy──► Candidate(qualified_id, rights_basis, attribution, dims?)
      │                                    local media: dims via isolation "inspect" task (batched, read-only)
      ▼
selection.shortlist(): history → dims → upscale/shape → strict / first-eligible / fallback ranking → Shortlist[≤ 2]
      │
      ▼  for each shortlisted candidate (attempt budget):
net.gateway.download(rendition) ─► workspace/in/source.bin   (decoded-byte cap, SHA-256, provider pacing)
      │
      ▼
isolation.run("prepare", in/source.bin, constraints) ─► JSON {status, actual_dims, geometry}   (bytes-only channel)
      │                                                  writes out/delivery.jpg (path chosen by the parent)
      ▼
parent validates out/delivery.jpg (O_NOFOLLOW, regular file, JPEG header = canvas, ≤ 15 MiB) and computes SHA-256
      │
      ▼
store.history.prestage(qualified_id)   (next generation written + fsynced as a temporary file)
      │
      ▼
isolation.run("deliver", delivery.jpg, validated IP, seeded token) ─► markers: connected → upload_started → uploaded(id) → selected
      │
      ▼  if selected:
store.history.commit() ─► store.preview.publish(bytes, sha256) ─► store.records.current(attribution, fingerprints)
      │
      ▼
store.records.last_run(outcome, stats) ─► workspace removed ─► summary line ─► exit code
```

A single file with a parent-computed SHA-256 serves as the television payload, the published preview, and the input to the recorded fingerprint. That is how the design proves acceptance item `D8`.

---

## 7. Deadlines, budgets, and cancellation

### 7.1 Primitives

- **`Clock`**: `monotonic()`, `utc_now()`, `sleep()`. Injected; tests use a fake clock.
- **`Deadline`**:
  - `remaining()` and `expired()`;
  - `check(stage)` raises `DeadlineReached`;
  - `child(seconds)` never outlives its parent;
  - `clamp(limit)` returns `min(limit, remaining)` and raises if nothing remains.
- **`Allowance`**: a named counter with `take()`. Exhaustion ends the corresponding loop normally, with a logged reason.
- **Phase-budget calculator.** Each phase receives `child(min(phase_budget, remaining − Σ budgets reserved for later phases))`. An early phase can therefore never eat into a later phase's reserve, and unused time rolls forward.

### 7.2 Budget decomposition (normative; D-114)

**Phase budgets.** These sum to the total run deadline.

| Phase | Budget | Notes |
| --- | --- | --- |
| CONFIGURE | 7 s | Includes resolving `tv_host`, `supervisor`, and `homeassistant` (each ≤ 3 s, clamped to the phase), the lock, and the sweep. |
| RESOLVE_FILTERS | 8 s | Up to 3 helper reads, each ≤ 3 s and together clamped to the 8 s phase. **Outside** the selection deadline. |
| SELECT | `S` = 60 s by default | Advanced option `selection_time_limit`, 20–120 s. Covers discovery only, including local-media inspection batches. |
| ATTEMPT | 90 s | Shared by at most 2 attempts. Per attempt: download ≤ 45 s, prepare worker ≤ 30 s, each clamped to what remains of the phase. |
| DELIVER | 90 s | Includes worker start, connect ≤ 10 s, pairing wait ≤ 30 s, upload, and select. |
| FINISH (`publish_reserve`) | 10 s | PRE-STAGE, RECORD, PUBLISH, run records, cleanup. |
| **Total run deadline `T`** | **`S` + 205 s** (265 s with defaults) | The sum of the rows above. A unit test asserts that the phase budgets sum to `T`. |
| Shutdown allowance | 10 s | Watchdog fires at `T` + 10 s (acceptance item `C5`). |

**Allowances and per-request limits.**

| Limit | Value |
| --- | --- |
| Shortlist size (full-rendition downloads per run) | 2 |
| Candidates evaluated after the history filter | 150 |
| Provider metadata requests | 25 |
| Remote dimension probes | 30 (internal constant; see §8.3 and Q-20) |
| Local directory entries enumerated | 20 000, depth ≤ 4 |
| Local files header-inspected | 500 (the local counterpart of the probe budget, Q-20) |
| Per-request total time | metadata 15 s, probe 10 s, artwork download 45 s, helper read 3 s, each clamped to its phase |
| Connect timeout | ≤ 5 s per address attempt, clamped |
| Read timeout | ≤ 10 s between bytes, re-clamped before every receive |
| DNS resolution | ≤ 5 s per provider host; ≤ 3 s in CONFIGURE; always clamped |
| Worker address-space ceilings (`RLIMIT_AS`, virtual memory) | image worker 1 GiB; television worker 512 MiB (§11.3) |
| Dashboard fallback timer (§16.3) | `T` + 35 s (10 s allowance plus a 25 s polling margin): 300 s by default, 360 s at `selection_time_limit` = 120 |

Q-02 asks the user to confirm the interpretation behind this table: the specification's "60 seconds total" means the selection phase, not the whole run including upload.

### 7.3 Television reserve rule

The budget calculator reserves DELIVER's full 90 s and FINISH's 10 s from the start of the run. PRE-STAGE re-checks the reserve. If it fails, the outcome is `deadline_exceeded` and the television is untouched. An upload is therefore never cut off because earlier phases ran long.

### 7.4 Retry and pacing policy (D-115)

| Operation | Retries | Conditions |
| --- | --- | --- |
| Provider metadata GET | ≤ 1 | Only for a connect error, HTTP 502/503/504, or HTTP 429 with a `Retry-After` (delta-seconds or HTTP-date) of ≤ 5 s. The wait is `max(Retry-After, 1 s)` plus jitter, and the retry is skipped if the wait exceeds the remaining deadline. It counts against the request allowance. |
| Any HTTP 403, or any HTTP 429 not followed by the single permitted metadata retry, from **any host in the provider's policy** (including the image host) | 0 | All further requests to **any host of that provider** end for this run (a "403/429 stop"). A retried 429 also delays every later request to that provider until its `Retry-After` has passed. |
| Probe or artwork download | 0 | Move on to the next candidate. |
| Helper state read | 0 | Fall back to the static value. |
| Television connect | ≤ 1 | Only before the `upload_started` marker. |
| Television upload or select | 0 | Prevents duplicate uploads. |

**Pacing.** Each provider policy declares a `min_interval` between requests, enforced with the injected clock and counted against the deadline. For the Art Institute of Chicago it is 1 s, which matches its published 60-per-minute limit and its image-download guidance.

### 7.5 Network timing guarantees

- **DNS.** Each host is resolved **once** per request, in a fresh daemon thread joined with `clamp(5 s)` (§4.3). A resolver timeout maps to `SourceUnavailable`.
- **Connect.** Validated addresses are tried one at a time, each attempt clamped to the remaining request time, so a host with many addresses cannot multiply the connect timeout.
- **Read.** Bodies are read with partial reads, and the socket timeout is re-clamped to `min(10 s, request remaining)` before every receive. A slow-drip server that sends one byte just inside each read timeout still ends when the request's total runs out.
- **Guarantee.** No network operation outlives its phase deadline by more than one scheduling tick. The only exception is an abandoned DNS thread, which does not delay the run.
- **Workers.** Everything inside a worker is bounded by the worker's kill timer, whatever the library does internally.

### 7.6 Stop requests (SIGTERM)

The SIGTERM handler sets a cancel flag and **raises** a `Cancelled` exception in the main thread. Under PEP 475, interrupted system calls are retried only when the handler returns normally, so raising is required to abort a blocking call.

| When SIGTERM arrives | Handling |
| --- | --- |
| Before DELIVER | The outcome is `cancelled` and the television is untouched. |
| During DELIVER | The parent kills the worker's process group and reads the markers received so far. If `selected` was seen, it continues with RECORD. Otherwise the outcome is `cancelled`, with the television state taken from the markers. |
| After `selected` | SIGTERM is deferred until RECORD's rename has been `fsync`ed. PUBLISH may be skipped (→ `delivered_with_warnings`). |

In every case the parent cleans up and exits within the configured 20 s stop timeout (§17.1). Phase 6 verifies that a Supervisor stop really delivers SIGTERM to the process (D-130).

---

## 8. Candidate selection

### 8.1 Shape and quality classification (D-116)

Let `r = width / height`, computed from the deliverable rendition's dimensions **after** EXIF orientation. Let `s` be the scale factor the configured fit mode would apply on the 3840 × 2160 canvas: `min(W/w, H/h)` for `contain`, `max(W/w, H/h)` for `cover`.

| Class | Rule (proposed, Q-03) |
| --- | --- |
| portrait | `r < 0.95` |
| square | `0.95 ≤ r ≤ 1/0.95` (≈ 1.053) |
| landscape | `r > 1/0.95` |
| near-16:9 (strict) | `abs(ln(r / (16/9))) ≤ ln(1.04)`, that is `1.709 ≤ r ≤ 1.849` |
| too small | `s > 2.5`: the image would be upscaled by more than 2.5× |

The quality rule is based on the upscale factor rather than fixed pixel minimums, so it treats wide panoramas fairly. For example, in `contain` mode a 1686 px-wide Art Institute rendition that is at least as wide as 16:9 is upscaled ≈ 2.28×. Narrower works are limited by height and upscaled less. In `cover` mode, works wider than 16:9 are upscaled more. These are pure functions in `selection.geometry`, covered by table-driven tests.

### 8.2 Discovery, shortlist, and attempts

```text
shortlist ← []                              # at most 2 entries, in preference order
fallbacks ← top-2 heap keyed by abs(ln(r/(16/9)))
for candidate in provider.iter_candidates(filters, ctx):        # lazy; provider-bounded
    stop if SELECT deadline expired
    skip if history contains candidate.qualified_id                # not charged to the candidate allowance
    stop if candidate allowance exhausted                          # charged only past the history filter
    skip if candidate.rights_basis not allowed for this provider (D-134)
    dims ← candidate.dims  or  inspect/probe (allowance-counted; skip if exhausted)
    skip if too small;  shape ← classify(dims)
    skip if landscape_only and shape ≠ landscape
    if not strict_tv_format:    shortlist.append(candidate);  stop when len(shortlist) = 2
    elif near_16_9(dims):       shortlist.append(candidate);  stop when len(shortlist) = 2
    elif fallback_permitted:    fallbacks.offer(candidate)
end
if strict_tv_format and fallback_permitted: fill the shortlist from fallbacks, best first
return shortlist  (empty → no_match, or source_failed per §4.2)
```

- **One discovery pass, no back-edge into discovery.**
  - Discovery stops as soon as it has two usable candidates, or when its budget or allowances run out.
  - The ATTEMPT phase then works through the shortlist in order. If the first candidate fails, for example with an HTTP 404, a download failure, a verification mismatch, or a worker failure, the second is tried.
  - The SELECT deadline covers discovery only. Attempt time is charged to the ATTEMPT budget (§7.2).
- **Verification.** The prepare worker first reports the real decoded dimensions. If they violate the reason the candidate was chosen for, it stops without rendering and the parent moves on. Examples: no longer landscape, no longer near 16:9 for a strict choice, or too small.
- **Fallback permission (D-117).**
  - Fallback is permitted only when `landscape_only` is on and `fit_mode` is `contain`, as the specification states. A fallback image is therefore never cropped.
  - In `cover` mode with strict format on, there is no fallback.
  - Q-11 offers the alternative: allow fallback in `cover` mode by forcing `contain` for fallback images.
- **Provider error mid-discovery.**
  - **Any error other than a 403/429 stop:** discovery ends, and candidates already shortlisted, or fallbacks already found, are still attempted with a warning logged.
  - **After a 403/429 stop (§7.4):** no further request goes to any host of that provider. Remote candidates are not attempted, and the outcome is `source_failed`.
- **Randomness.** Providers randomize their discovery order with the injected random source.

### 8.3 Probes and inspections

- A **probe** is one remote request made only to learn dimensions. It is either a small rendition or a byte range (≤ 256 KiB), and is counted against the 30-probe allowance. Neither beta source needs probes: the Art Institute's metadata already carries dimensions. The probe machinery is built when the first provider needs it; until then the allowance is enforced and tested with a counting fake gateway (acceptance item `C4`).
- **Local inspections** read headers from disk inside the isolated `inspect` worker, in batches of up to 50 files, and count against the 500-file local allowance.
- Treating "30 dimension probes" as a remote-request budget, with local header reads bounded separately, is an interpretation of the specification that needs approval (Q-20).

---

## 9. Provider adapters

### 9.1 Contract

Illustrative:

```text
Provider
  key: str                                     # history namespace (see the naming table)
  capabilities() -> Capabilities               # supported filter dimensions, dims-in-metadata?, host policy, allowed rights bases
  iter_candidates(filters, ctx) -> Iterator[Candidate]
  probe_ref(candidate) -> ImageRef | None
  full_ref(candidate) -> ImageRef

Candidate
  provider_key, native_id, qualified_id        # "<key>:<native_id>"; native_id must fullmatch the provider's pattern; ≤ 200 chars
  rights_basis: RightsBasis                    # e.g. CC0, PDM, CC-BY-4.0, USER_SUPPLIED — plus the source field it was read from
  attribution: title, creator, date_text, credit_line, detail_url   (sanitized, length-capped)
  dims: Size | None                            # of the rendition full_ref delivers

Provider errors: SourceUnavailable · SourceChanged · SourceRateLimited   (an empty result is not an error)
```

**Naming.** The provider key becomes the persistent history prefix, so it is fixed now:

| Option value | Provider key and history prefix | Module |
| --- | --- | --- |
| `local_media` | `local` | `providers.local_media` |
| `art_institute_chicago` | `aic` | `providers.aic` |
| (only if Q-01 approves) | `gac` | `providers.gac` |
| (only if Q-17 approves) | `bing` | `providers.bing` |

**Contract rules.** Every adapter must pass the shared contract suite (§20.1):

- Candidates are lazy, with at most one page fetched ahead.
- All network traffic goes through the gateway, using the run's allowances and deadline.
- Qualified identifiers are stable across runs and upgrades, and never collide across providers.
- Every candidate carries a `rights_basis` in the provider's allowlist (D-134), and carries attribution whenever that basis requires it.
- Filter semantics:
  - A filter dimension the source does not support at all (for example, colour for local media) is ignored, with one WARNING.
  - If a **helper-supplied** value cannot be mapped by the selected source, the run falls back to the static option with one WARNING, as the specification requires for invalid helper values.
  - If the static value itself cannot be mapped, the run ends as `no_match` with an actionable hint. This can arise only once vocabularies span several providers.
  - An unmapped value is never silently ignored.
- No adapter writes outside its own cache namespace.

### 9.2 Local media (`local`)

- **Library.** The fixed, documented folder `/media/frame_gallery/library`, which the app creates at every start if it is missing. There is no configurable path in the beta, which keeps to the constraint of using documented media paths only.
  - Users add images with Home Assistant's media browser.
  - That the browser can upload into this subfolder is an assumption Phase 8 verifies (R-21).
  - The `no_match` hint for an empty library names the exact media-browser location.
- **Enumeration.**
  - Iterative scan, depth ≤ 4, ≤ 20 000 entries. Hidden entries are skipped, and symbolic links are never followed.
  - Each file is opened with `O_NOFOLLOW` and then checked with `fstat` on the open descriptor: it must be a regular file of ≤ 40 MiB.
  - Extension allowlist: `.jpg`, `.jpeg`, `.png`.
  - The order is shuffled with the injected random source.
- **Useful warnings.** Unsupported extensions (for example HEIC, WebP, GIF), oversized files, unreadable files, and files that fail inspection are reported in **one aggregated WARNING per run**: counts by reason plus up to 5 sanitized example paths.
- **Identifier.** `local:fp:<hex>`: the SHA-256 of the file size plus its first and last 64 KiB (D-118). It is stable across renames and reads at most 128 KiB per file.
- **Preview exclusion** (acceptance item `F7`), three guards:
  1. the preview directory is excluded by real path;
  2. the library folder does not contain the preview directory;
  3. the fingerprints of the last 10 published previews, kept in the current-artwork record, are skipped.
- **Rights basis.** `USER_SUPPLIED`: the user's own files.
- **Filters.** Colour, museum, and style are not supported and are ignored with one WARNING. Landscape-only, strict format, and the upscale rule apply.

### 9.3 Provider access findings (Phase 1 research)

`LEGAL_BOUNDARIES.md` requires connectors to "respect applicable access terms, request limits, and technical restrictions". Phase 1 read published policy pages, `robots.txt` files, and official API documentation. It also used one Microsoft Q&A answer, cited as a non-documentation source, and search-result snippets where a page blocked automated readers. No provider endpoint was called.

| Source | Documented API? | Access rules found | Image rights | Recommendation |
| --- | --- | --- | --- | --- |
| **Google Arts & Culture** (specified) | **No.** Google documents only a partner *ingestion* programme. | `robots.txt` allows public HTML pages and disallows `/api/*` and `/incognito/*`. The image host's `robots.txt` was not checked. Google's Terms (effective 2026-07-30) treat these as abuse: automated access in violation of `robots.txt`; bypassing protective measures; reverse engineering to extract proprietary information; using the services to violate intellectual-property rights. | Partner institutions keep the rights. No Google Arts & Culture reuse licence was found. | Not in the beta (Q-01). Colour browsing is a website feature, not documented data. |
| **Bing daily imagery** (specified) | **No.** A single Microsoft Q&A answer (not documentation) says there is no supported way to fetch past images. The Bing Search APIs were retired on 2025-08-11. | In the `*` group of `robots.txt`: `Disallow: /HpImageArchive.aspx` (spelled so; path matching is case-sensitive) and the image path `/th?`. Only `msnbot-media` is allowed `/th?`. The code of conduct prohibits "impermissible scraping". | Microsoft Services Agreement, "Bing and MSN Materials" (unchanged in the version effective 2026-09-30): for non-commercial, personal use only. Downloading, or building your own products, only where authorized by Microsoft or rights holders, or allowed by copyright law. | Not planned (Q-17). |
| **Museum of Modern Art** (named in the specification) | No public API; research datasets without images only. | — | Licensed through Art Resource or Scala. | No open-access API or image licence found. Aggregator coverage not yet checked. |
| **Musée d'Orsay** (named in the specification) | None found. | — | Online reproductions are "strictly non-commercial"; publishing requires agency authorization. | As for MoMA. |
| **Art Institute of Chicago** | **Yes** (`api.artic.edu/docs`). No key. | 60 requests per minute per IP. A courtesy `AIC-User-Agent` header is requested. Image downloads one at a time, about 1 s apart. | Metadata CC0 (the description field is CC-BY). Public-domain images CC0. | **Recommended beta museum source** (§9.4). |
| **Cleveland Museum of Art** | **Yes**: Open Access API. No key. | No documented limit, so the app self-throttles. | CC0 dataset; CC0 images for works marked CC0. | Next provider: a near-4K rendition (3400 px long side, ≈ 1.13× upscale). |
| **Europeana** | **Yes.** A key is required and may not be shared. **Personal keys are for "non-production use"**; production use expects a reviewed project key. | Per-key limits, not numerically stated. | Rights are per item; use `reusability=open`. | Later, if the key model is resolved. |
| **Rijksmuseum** | **Yes**: Search, identifier resolver, IIIF (with a `max` size). No key. | No documented limits. | Public Domain Mark or CC0 in most cases; CC BY 4.0 where the museum exercises copyright. | Later. |
| **The Met** | Yes. Its terms have an API section: no key today, but keys, transaction limits, or discontinuation are possible. Technical documentation is GitHub-hosted, which was out of bounds for Phase 1. | No numeric limit published. | Open Access images CC0; others are limited non-commercial use and must not be used. | Later, after approval to read its documentation. |

These findings are architecture inputs. Each adapter's exact parameters are re-verified against the live documentation at the start of Phase 4 (R-20).

### 9.4 Art Institute of Chicago (`aic`), the recommended beta museum source (D-132)

- **Discovery.**
  - The documented search endpoint, `/api/v1/artworks/search`, takes Elasticsearch Query DSL, preferably as a JSON `params` GET.
  - Every query requires `is_public_domain = true` and the presence of an image.
  - The `fields` parameter restricts responses to: id, title, artist, date, image id, thumbnail width and height, dominant colour, style, department, and credit line.
  - `limit` is at most 100, and search paging stops at 10 000 results.
  - Randomness comes from sampling pages **without replacement** within a run, among the first `min(total, 10 000)` results.
  - A typical run makes 2 requests: the count (cacheable), then one page.
- **Filters** (acceptance item `C1`), combined in one query where the API supports it:
  - **Colour.** Dominant-colour HSL hue ranges, with lightness and saturation bands for black, white, and grey. Server-side range filtering on these fields is confirmed in Phase 4; otherwise the check runs on the returned page, within the same allowances.
  - **Style or period.** Style titles or identifiers, and date ranges.
  - **Museum or collection.** Departments.
- **Dimensions without probes.** From the documented native width and height, scaled to the rendition that will be delivered.
- **Rendition.** IIIF `…/{image_id}/full/1686,/0/default.jpg` from `www.artic.edu`.
  - This is the largest size the documentation offers for public-domain works. The Art Institute recommends 843 px "unless there's a clear need for 1686", and a 3840 × 2160 television canvas is that need.
  - In `contain` mode the result is upscaled by up to ≈ 2.28× (§8.1), which the documentation states honestly (R-19).
  - An HTTP 404 (image removed) moves on to the next candidate.
- **Identifier validation.** `image_id` must fullmatch a strict pattern and is percent-encoded before it goes into the URL path. The artwork id must be numeric.
- **Cache use.** Two kinds of entries, within the limits in §13.4:
  - the result count per filter signature (TTL 1 day), which saves the count request;
  - page numbers found to be fully sent (TTL 7 days), which reduces `no_match` on nearly exhausted filters.
- **Courtesy and limits.**
  - An `AIC-User-Agent` header carries the project name and a **project-owned contact email**, never user data. The address is decided under Q-22, before any live request.
  - `min_interval` is 1 s for every request.
  - At most 25 metadata requests per run.
- **Rights basis.** `CC0`, read from `is_public_domain`.
- **Attribution.** The caption format the museum asks for, "Artist. Title, Date. The Art Institute of Chicago.", kept in the current-artwork record and logged. The CC-BY description field is not used.
- **Host policy.** Exactly `api.artic.edu` and `www.artic.edu`.

### 9.5 Google Arts & Culture (`gac`): specified, not in the beta

Phase 1 found no documented API (§9.3). The specification anticipated this: "experimental unless a stable documented provider API becomes available".

Recommendation (Q-01): **defer until an official API exists.** The contract keeps a slot for it.

`LEGAL_BOUNDARIES.md` makes respecting access terms and technical restrictions a binding project rule, and a user's acceptance of risk cannot waive it. Building the connector without an official API would therefore first require the user to amend that rule. Only then would D-120 be reopened with a new adapter milestone. Even in that case, the constraints would be:

- `robots.txt`-allowed HTML pages only, never `/api/*`, and after checking the image host's rules too;
- no circumvention of any kind;
- ≤ 25 requests per run, sequential, at least 1 s apart;
- an honest User-Agent;
- open rights bases only;
- opt-in and labelled experimental;
- fixtures synthesized under §20.3.

### 9.6 Bing daily imagery (`bing`): specified, not planned

No `robots.txt`-compliant implementation exists. The image path `/th?` is disallowed in the `*` group, and the Services Agreement restricts downloading and building products on the materials. As the distributor, the project would be the one building that product.

Recommendation (Q-17): remove it from the specification's initial providers.

### 9.7 Future providers

A new provider needs only an adapter implementing the contract (including the `rights_basis` allowlist), a vocabulary mapping, a host policy with pacing, and synthesized fixtures. It requires no change to `selection`, `imaging`, `tv`, or `store`.

Ranked candidates:

1. **Cleveland Museum of Art.**
   - Near-4K "print" rendition from `openaccess-cdn.clevelandart.org`.
   - Dimensions in the metadata.
   - Department and date filters; no colour field.
2. **Europeana.**
   - Colour-palette and landscape filters, and many museums.
   - Its key terms must be resolved first; a key would be stored as a `password` option.
3. **Rijksmuseum.**
4. **The Met.**

**The `museum` filter.** The specification calls it "museum or collection". For a single-institution source it maps to that institution's departments; for an aggregator, to the contributing museum. The option key stays `museum` to trace to the specification.

---

## 10. Guarded network access (D-108, D-131)

All provider traffic goes through one gateway built on `urllib3`, with its automatic retries and redirects disabled.

**Host policy.** Each provider declares:

- **Hosts.** Allowed hosts are matched **exactly**. A suffix rule may match only on a label boundary, after lowercasing, stripping any trailing dot, and IDNA normalization.
- **URLs.** `https` on port 443 only, with no user-info and no IP-literal hosts.
- **Content types.** Allowed per request kind: metadata `application/json` (plus `text/html` only for a provider approved to need it); images `image/jpeg` or `image/png`.
- **Byte caps**, applied to **decoded** bytes: metadata 2 MiB, probe 256 KiB, image 40 MiB.
- **Pacing.** A `min_interval` (§7.4).
- **Identifier patterns** for any provider value placed into a URL. Values are validated with `fullmatch` and percent-encoded.

**Resolution and connection.**

1. Resolve the host once (§7.5).
2. Reject the request unless **every** address is globally routable, after unwrapping IPv4-mapped, 6to4, and NAT64 forms. Loopback, private, link-local, CGNAT (`100.64/10`), multicast, reserved, and unspecified ranges all fail.
3. Connect to a validated IP, keeping the hostname for SNI, certificate verification, and the `Host` header.
4. Confirm `getpeername()` before sending anything.

This defeats DNS rebinding and SSRF through redirects or misleading metadata.

**TLS.** `CERT_REQUIRED`, hostname checking, TLS ≥ 1.2, and the `certifi` CA bundle named explicitly. `certifi` is a direct dependency from Phase 4.

**Redirects.** Followed manually, at most 3. Every hop goes through the full policy again.

**Encoding.** Image and probe requests send `Accept-Encoding: identity`, and any other `Content-Encoding` is rejected. Metadata may use a single `gzip` layer, with the cap applied after decoding. A declared `Content-Length` above the cap is rejected before the body is read.

**Hygiene.**

- No cookies.
- Environment proxies, `.netrc`, and CA overrides are ignored; the environment is scrubbed at start (§17.5).
- The User-Agent is `FrameGallery/<version> (+<project URL>)` (D-119). Provider courtesy headers, such as the Art Institute's, are added per policy.

**Logging.** Host, path without the query string, status, byte count, and duration. Never bodies or header values.

---

## 11. Image preparation

### 11.1 Worker-side pipeline

Steps 2 to 9 run only in the `prepare` worker (§11.3).

1. **Sniff** (parent, at download). Magic bytes must identify JPEG or PNG and agree with the declared content type.
2. **Open** with `formats=("JPEG", "PNG")`, lazily. Enforce before decoding (D-121):
   - width and height ≤ 20 000 px each;
   - ≤ 64 MP in total for JPEG, which is draft-decoded;
   - ≤ 40 MP for PNG, which has no reduced decode.

   Also report the real dimensions and orientation for **verification** (§8.2).
3. **Decode with reduction.** For JPEG, the decoder is asked for the smallest DCT scale that still covers the fitted size, with axes swapped for EXIF orientations 5–8. PNG decodes at full size, bounded by the pixel cap. Multi-frame inputs use the first frame.
4. **Pre-normalize for resampling.** Palette and bilevel images become RGB or RGBA, so resampling is never nearest-neighbour. Modes deeper than 8 bits are scaled to 8-bit or rejected, as the tests will establish.
5. **Crop, then resize to the fitted size** (§11.2), with a high-quality filter and integer pre-reduction for large factors. In `cover` mode the centre crop is applied in **source coordinates before** resizing. From this point every buffer is therefore at most canvas size in both modes.
6. **Orient in place** (EXIF transpose), and drop all metadata.
7. **Normalize colour to 8-bit sRGB RGB.**
   - Embedded ICC profiles are converted to sRGB (D-122).
   - CMYK is converted.
   - Alpha is composited over `background_color`.
8. **Compose.** `contain` places the image on the canvas. `cover` is already exactly canvas-sized after step 5.
9. **Encode** a baseline JPEG: quality 90, standard chroma subsampling, no EXIF. If the result exceeds 15 MiB, encode once more at quality 85. Phase 8 may tune these values (Q-05).

**Peak memory.** Roughly the sum of:

- the interpreter baseline;
- the decoded source (`w·h·c`, where `c` ≤ 4; JPEG draft decoding divides `w·h` by up to 64);
- **one full-resolution conversion copy** (`w·h·4`), from step 4's pre-normalization or from the premultiplied-alpha copy Pillow makes when resizing RGBA or LA images;
- a reduced intermediate;
- one canvas-sized copy (≤ 33 MiB);
- encoder buffers.

The worst legal cases are:

- a 40 MP RGBA PNG, or a palette PNG with transparency: ≈ 160 + 160 + 33 MiB plus tens of MiB, about 450 MiB;
- a 64 MP CMYK JPEG that draft decoding cannot reduce much (for example in `cover` mode): ≈ 256 MiB source, plus a crop copy of up to that size, plus canvas buffers, about 550 MiB resident.

`RLIMIT_AS` limits *virtual* address space, which also counts library mappings, so the image worker's ceiling is **1 GiB** (D-121). Worker tests run under the real limit with:

- a 40 MP RGBA PNG with an ICC profile;
- a 40 MP palette PNG with transparency;
- a 16-bit PNG;
- a 64 MP CMYK JPEG in both fit modes.

R-09 records the measured peak.

### 11.2 Fit geometry (pure, table-tested)

Given a source `(w, h)`, a canvas `(W, H)` of 3840 × 2160 by default, and a mode:

- **`contain`** (default): `s = min(W/w, H/h)`; scaled size `(round(w·s), round(h·s))`, clamped to `(W, H)`; centred on `background_color` (default `#000000`). Invariant: every source pixel is present.
- **`cover`** (explicit opt-in): `s = max(W/w, H/h)`. The centre crop is computed in source coordinates (`W/s × H/s`) and applied before resizing. Invariant: crops along one axis only, and only by the overflow.
- **No stretching.** Only uniform scale factors exist, and no API accepts independent x and y factors.

### 11.3 Isolation, privilege, and hand-off (D-109)

**Worker bootstrap.** This runs first in every worker's entry function; `__main__` has no import-time side effects.

1. `setgroups([])`, then set the group and user IDs to an unprivileged ID (65534). The parent has already created two directories:
   - a read-only `in/`;
   - an `out/` owned by the worker's user ID and the parent's group, with the setgid bit, so the parent reads results through group permissions and never needs a DAC-override capability.
2. `prctl(PR_SET_PDEATHSIG, SIGKILL)`, set **after** step 1 because the kernel clears it on credential changes. The worker then exits if `getppid()` no longer matches the parent.
3. `umask 027`.
4. `RLIMIT_AS` of 1 GiB for the image worker and 512 MiB for the television worker, plus a CPU limit for both.
5. The environment is already reduced to the allowlist (§17.5).
6. The logging configuration is installed before any third-party import (§19).
7. Image worker only: Pillow limits.
   - `MAX_IMAGE_PIXELS` is set globally to 64 MP, the JPEG cap.
   - `DecompressionBombWarning` is escalated to an error.
   - The format allowlist applies.
   - The 40 MP PNG cap is enforced by an explicit header check before any pixel data is loaded (§11.1 step 2).

If dropping privileges fails, the worker refuses to run and the outcome is `internal_error`. This ties into Q-10 and the AppArmor profile in §17.6.

The `inspect` worker opens each library file itself with `O_NOFOLLOW` and checks it with `fstat`. Files that user 65534 cannot read are counted in the aggregated WARNING (§9.2).

**Bootstrap test.** A diagnostic task runs through the real process executor. From inside the child it reports:

- `getrlimit` (`RLIMIT_AS`, `RLIMIT_CPU`);
- the umask;
- the user ID, group ID, and supplementary groups;
- the parent-death signal;
- the environment keys;
- Pillow's pixel limit, the warning-filter action, and the format allowlist.

The test asserts each value.

**Channel.**

- Progress markers and the final result are sent child → parent **as bytes only**, using `Connection.recv_bytes(maxlength = 64 KiB)`, then `json.loads` and schema validation.
- `recv()`, queues, and pools are never used for results, because they unpickle whatever the child sends.
- The parent chooses every path. Any path a worker reports is ignored.

**Parent-side validation before PRE-STAGE.** `out/delivery.jpg` must:

- open with `O_NOFOLLOW`;
- be a regular file of ≤ 15 MiB;
- carry a JPEG header, checked by a small stdlib-only marker parser, whose dimensions equal the canvas.

The parent then computes the SHA-256 itself. That hash identifies the television payload and the preview.

**Tasks.**

| Task | Input | Timeout |
| --- | --- | --- |
| `inspect` | Batch of ≤ 50 local file paths, read-only | Clamped to the SELECT deadline |
| `prepare` | One source file plus selection constraints | 30 s, clamped to the ATTEMPT budget |
| `deliver` | See §12 | 90 s |

A crash, hang, memory-limit hit, or invalid result turns into a classified outcome, and the parent still performs cleanup and logging. Unit tests use an in-process executor with the same interface. Integration tests use the real process executor and also assert that:

- a worker's environment keys are a subset of the allowlist;
- hostile or non-JSON results are rejected;
- a worker exits when its parent is killed.

---

## 12. Television communication

### 12.1 Port and progress markers

Illustrative:

```text
Television
  deliver(jpeg_path, tv_ip, token_seed_path, deadline) -> DeliveryResult
  markers (child → parent, bytes-only): connected · upload_started · uploaded(content_id) · selected
  DeliveryResult: {status: ok | unreachable | not_authorized | unsupported | refused | protocol,
                   auth: unchanged | new_token | token_rejected, markers_seen}
```

- The port is a single coarse operation, performed inside one worker invocation. The parent never holds a television socket.
- The `content_id` in a marker must match a strict pattern of ≤ 64 characters.
- The parent classifies the outcome from the **last marker seen** together with the result (§12.4). It does not rely only on the result, which a killed worker never sends.

### 12.2 Samsung adapter

- **Library.** `samsungtvws` 3.0.6 (LGPL-3.0, D-104), imported only by the worker task.
  - Samsung publishes no documentation of Art Mode or of the local control protocol.
  - The Python art API was last documented in the library's 2.7.2 README. Documented there: `art().supported()`, `upload(data, file_type='JPEG')`, `select_image(content_id, show=…)`, `get_artmode()`.
  - Matte handling, a client-name parameter, and the 3.x constructor are **unknown until Q-15**. Phase 5 takes every parameter from the installed 3.0.6 package only, and an adapter contract test pins the surface used.
- **Connection.**
  - To the **validated IP literal** from CONFIGURE (§15.4), never a hostname the library would resolve again.
  - The port and TLS behaviour follow what Q-15 confirms. The library does not document its certificate handling; R-03 tracks the trust-on-first-use question for Phase 5.
- **Setup requirements, documented for users:**
  - The television and Home Assistant are on the same subnet; the library notes that televisions refuse connections from other subnets.
  - *Device Connection Manager → Access Notification Settings → First Time Only*, because newer televisions otherwise prompt on every connection.
  - An IP address reserved in the router's DHCP settings.
- **Pairing token.**
  - The parent seeds a copy of `/data/tv/<host-id>.token` into the worker's `out/` directory. The library writes only there.
  - After the worker returns, the parent inspects the structured `auth` field:
    - `new_token`: the parent validates the format (≤ 256 characters, restricted charset) and installs it with the atomic primitive (§13.2) at mode `0600`.
    - `token_rejected`: the parent deletes the stored token, and the outcome is `tv_not_authorized`. The next run prompts again.
  - Tokens for addresses other than the current `tv_host` are deleted at DELIVER.
  - Tokens are meant to be **excluded from backups** (`backup_exclude: tv/**`), so that no clear-text token sits in backup archives. After a restore the user accepts one new prompt. The documentation does not say what `backup_exclude` patterns are relative to, so the patterns are *assumed* to be relative to `/data`. Phase 8 verifies this by inspecting an app backup archive for `tv/`.
- **First run.** The worker waits up to 30 s for the *Allow* prompt. If it is not accepted in time, the outcome is `tv_not_authorized` with the message *"Accept the connection prompt on your TV, then start the app again."* Whether a client name can be shown on that prompt is decided under Q-15.

### 12.3 Bounding

- The worker runs within the 90 s DELIVER budget. Library-level timeouts are also set where the library exposes them.
- On kill-timer expiry the parent kills the process group and classifies from the markers (§12.4).
- Once `selected` has been seen, RECORD always runs, even if the worker is killed afterwards (for example while hanging on socket close).

### 12.4 Failure semantics

| Last marker seen and result | Outcome | Television | History |
| --- | --- | --- | --- |
| none, or `connected`; connection refused, timed out, host down, connection lost, kill timer, or `protocol` | `tv_unreachable` | unchanged | unchanged |
| `connected`; token rejected or prompt not accepted | `tv_not_authorized` | unchanged | unchanged |
| `connected`; art mode unsupported | `tv_rejected` | unchanged | unchanged |
| `upload_started`; connection lost, kill timer, or `protocol` | `tv_unreachable`: "connection lost during upload; the image may already be stored on the TV" | may hold an undisplayed upload | unchanged |
| `upload_started`; explicit refusal | `tv_rejected` | unchanged | unchanged |
| `uploaded`; selection explicitly refused | `tv_rejected` | holds an undisplayed upload (managing TV storage is a non-goal; warning) | unchanged |
| `uploaded`; connection lost, kill timer, or `protocol` | `tv_unreachable`: "the image is stored on the TV and may already be displayed" | holds the upload; **may already display it** if the select command was sent | unchanged. A later run may resend the displayed work; this is accepted as rare. |
| `selected` (any later failure, kill, or SIGTERM) | `delivered`, `delivered_with_warnings`, or `delivered_unrecorded` | changed | +1 unless the rename failed |

**Mapping each `DeliveryResult` status to an outcome:**

| Status | Outcome |
| --- | --- |
| `ok` | `selected` was seen, so `delivered*` |
| `unreachable` (connection refused, timed out, host down, or connection lost) | `tv_unreachable`; the television state follows the last marker |
| `protocol` (unexpected or malformed response) | Treated like a lost connection: `tv_unreachable`, with the television state following the last marker |
| `not_authorized` | `tv_not_authorized` |
| `unsupported` | `tv_rejected` |
| `refused` (the television explicitly refused the upload or the selection) | `tv_rejected` |

In the first row of the failure table, "connection refused" is a refused *connection*. `tv_rejected` is reserved for the statuses `unsupported` and `refused`. Every status therefore has exactly one outcome.

---

## 13. Persistent state and storage

### 13.1 Layout

| Path in container | Contents | Bound | In HA backups |
| --- | --- | --- | --- |
| `/data/options.json` | App options (Supervisor-managed) | — | yes (expected) |
| `/data/state/history.json` (+ `.bak`) | Sent identifiers with timestamps only | ≤ 20 000 entries **and** ≤ 5 MiB serialized | yes (expected) |
| `/data/state/current.json` | Attribution and SHA-256 of the artwork on the television, plus the last 10 preview fingerprints. Written only on delivery. | one record, ≤ 16 KiB | yes (expected) |
| `/data/state/last_run.json` | Outcome, timestamps, stats, effective filters (no secrets). Written for every outcome except watchdog termination. | one record, ≤ 16 KiB | yes (expected) |
| `/data/state/.lock` | Advisory lock file | — | — |
| `/data/state/quarantine/` | Corrupt state files, kept for diagnostics | ≤ 3 files | excluded (expected) |
| `/data/cache/<provider>.json` | Metadata cache (§13.4) | ≤ 1 000 entries, ≤ 2 MiB, TTL ≤ 7 days | excluded (expected) |
| `/data/tv/<host-id>.token` | Television pairing token, current address only | 1 file | **excluded** (expected) |
| `/tmp/frame-gallery/run-<random>/{in,out}/` | Per-run scratch, RAM-backed (`tmpfs: true`) | removed every run | n/a |
| `/media/frame_gallery/library/` | User images (read-only for the app) | user-managed | per the user's HA backup settings |
| `/media/frame_gallery/preview/latest.jpg` | Exact bytes last delivered | 1 file | per the user's HA backup settings |

"Expected" in the backup column means two things are still assumed. The documentation implies, but does not state, that `/data` is included in app backups, and it does not say what `backup_exclude` patterns are relative to. Phase 8 inspects an app backup archive to confirm both.

`LEGAL_BOUNDARIES` allows retaining only the selected preview, a bounded metadata cache, and duplicate-prevention identifiers. History therefore stores only identifiers and timestamps. Attribution exists only for the *current* artwork.

### 13.2 Atomic write protocol (D-110)

Every persistent write uses one primitive, which operates **relative to a directory file descriptor**:

1. Open the target directory with `O_DIRECTORY | O_NOFOLLOW`. If the directory, or `/media/frame_gallery` or `preview/`, is a symbolic link, the primitive refuses.
2. Serialize the data. JSON is re-parsed as a self-check.
3. Create `<name>.tmp-<random>` with `O_CREAT | O_EXCL | O_NOFOLLOW` (mode `0600`, or `0644` for the preview), write it, and `fsync` it.
4. **History only, best-effort:**
   - remove any stale `<name>.bak.tmp-*`;
   - hard-link the current file to `<name>.bak.tmp-<random>`;
   - `rename` it over `<name>.bak`.

   A failure here is logged and **never blocks step 5**.
5. `rename` the temporary file over `<name>`, which is atomic on POSIX filesystems.
6. `fsync` the directory.

**Pre-staging.** For history, steps 2–3 run in PRE-STAGE, before DELIVER, with the new identifier already included. A full or read-only `/data` is therefore detected (`state_error`) before the television is touched. RECORD then performs only steps 4–6.

**What `.bak` protects against.** Steps 3–6 already make each write crash-safe. The previous generation covers damage that leaves the primary **unparseable or schema-invalid** after a successful write: storage corruption, a restore that truncates the file, or a malformed external edit. Well-formed but wrong data is not detected, so `.bak` does not cover it.

**Reader.**

1. Try `<name>`.
2. On a parse or schema failure, move it to quarantine and try `.bak`.
3. If both fail, start empty with the WARNING *"History could not be read and was reset; previously shown works may repeat."*

The reader never raises into the run.

### 13.3 History

- **Format:**

  ```json
  {"format": "frame-gallery-history", "version": 1, "entries": [{"id": "aic:…", "at": "2026-09-26T07:00:00Z"}]}
  ```

- **Bound.** At most 20 000 entries and at most 5 MiB serialized; oldest entries are dropped first. The documentation mentions that a work sent about 20 000 runs ago may reappear.
- **Upgrades.** Readers ignore unknown fields. The version is bumped only for incompatible changes, each with a migration.
- **Downgrades.** A file carrying a **newer** version is not corrupt and is never quarantined. The run ends as `state_error` before the television is touched: *"History was written by a newer Frame Gallery version; update the app."*
- **Lock.** `flock(LOCK_EX | LOCK_NB)` on `/data/state/.lock`, taken in CONFIGURE. If it is contended, the outcome is `already_running`, with no waiting.

### 13.4 Metadata cache

- A per-provider JSON document of `{key, stored_at, value}` entries, each ≤ 8 KiB. Values are identifiers, counts, and page hints: **never image bytes, never whole pages**.
- ≤ 1 000 entries, ≤ 2 MiB serialized, TTL ≤ 7 days. Eviction removes expired entries first, then the least recently used.
- Written at most once per run, and only if changed. It is disposable: corruption means discard and continue.
- The beta uses it only for the Art Institute's result counts and exhausted-page hints (§9.4). This satisfies both "no unbounded local copy of the catalogue" and acceptance item `F6`.

### 13.5 Preview publication

The parent copies the validated delivery bytes into `/media/frame_gallery/preview/` with the §13.2 primitive, re-checks the SHA-256, and renames the copy to `latest.jpg` with mode `0644` so that Core can read it. It refuses if any path component is a symbolic link. If `/media` is unavailable, the outcome is `delivered_with_warnings`.

---

## 14. Cleanup guarantees

1. **Workspace scope.** A context manager removes `/tmp/frame-gallery/run-<random>/` in `finally` on every path.
2. **Worker group.** On every exit path (normal, SIGTERM, watchdog), the parent sends SIGKILL to the active worker's process group before removing the workspace. Workers also set `PR_SET_PDEATHSIG`.
3. **Startup sweep.** Removes leftover `run-*` directories and our own **regular** files named `*.tmp-*` or `*.bak.tmp-*` in `/data/state`, `/data/cache`, `/data/tv`, and the preview directory.
4. **RAM-backed `/tmp`.** `tmpfs: true` makes `/tmp` a memory filesystem. Scratch data vanishes when the container stops and never wears the eMMC.
5. **Bounded persistent state.** History (entries and bytes), cache, quarantine (3 files), and one token file.

Integration tests inject a failure at every stage and assert an empty workspace root (`F1`, `F2`). A repeated-run test asserts that `/tmp` and `/data` stay within the documented caps (`F3`). A timing test asserts that no worker survives a watchdog exit.

---

## 15. Configuration and filters

### 15.1 Options (D-123)

| Option | Schema (Supervisor syntax) | Default | Plain-language meaning |
| --- | --- | --- | --- |
| `tv_host` | `str` (required; no default) | — | IP address of your Frame TV (a reserved address is recommended). |
| `source` | `list(art_institute_chicago\|local_media)` | `art_institute_chicago` | Where artwork comes from. Other values are added only when approved (Q-01, Q-17). |
| `color` | `list(any\|…)` | `any` | Preferred dominant colour (Art Institute of Chicago). |
| `museum` | `list(any\|…)` | `any` | Museum or collection. For the Art Institute of Chicago, one of its departments. |
| `style` | `list(any\|…)` | `any` | Style or period (Art Institute of Chicago). |
| `landscape_only` | `bool` | `true` | Only choose artworks wider than tall. |
| `strict_tv_format` | `bool` | `true` | Prefer artworks already close to the TV's 16:9 shape. |
| `fit_mode` | `list(contain\|cover)` | `contain` | `contain` shows the whole artwork with margins; `cover` fills the screen and may crop edges. |
| `background_color` | `match(^#[0-9A-Fa-f]{6}$)` | `#000000` | Colour of the margins in `contain` mode. |
| `color_helper` | `match(^(input_select\|select\|input_text)\.[a-z0-9_]{1,64}$)?` | unset | Optional helper whose value overrides `color`. |
| `museum_helper` | same pattern, optional | unset | Optional helper overriding `museum`. |
| `style_helper` | same pattern, optional | unset | Optional helper overriding `style`. |
| `selection_time_limit` | `int(20,120)?` | unset → 60 | Advanced: seconds allowed for finding artwork. |
| `log_level` | `list(info\|debug)?` | unset → `info` | Advanced: log detail. |

- `tv_host` is declared in the schema without `?` and without a default, so the Supervisor refuses to start the app until it is set (acceptance item `B1`). The app re-validates it (§15.4). No address is ever shipped as a default.
- Landscape-only and strict format are on by default for every source. The specification states these defaults only in its Google Arts & Culture subsection, so they move to its filter section as part of Q-18.
- The default source works immediately after installation (Q-08).
- There is no `local_folder` option: the library path is fixed (§9.2).
- There is no user-facing probe option: the probe budget is an internal constant (§8.3).
- The schema stays within the Supervisor's two-level nesting limit.

### 15.2 Filter vocabularies (D-124)

- Each filter has a **versioned canonical vocabulary**: lowercase ASCII keys, display labels, and aliases.
- A key is offered only if at least one approved beta provider maps it. For the Art Institute of Chicago:
  - colours map to hue bands;
  - museum/collection values map to its departments;
  - styles and periods map to its style and date data.
- Museum of Modern Art and Musée d'Orsay values are excluded pending Q-01, Q-14, and Q-18. Final lists are fixed in Phase 4 (Q-14).
- **Normalization of helper values:**
  - trim, case-fold, Unicode NFKD with diacritics stripped;
  - spaces, hyphens, and apostrophes become `_`;
  - match against keys, labels, and aliases;
  - `any`, `all`, `random`, `none`, and the empty string all mean "no filter".
- Static options cannot be invalid, because the Supervisor schema restricts them to the list.
- The unsupported and unmapped semantics are those in §9.1.

### 15.3 Helper overrides

Helpers are read only when at least one `*_helper` option is set. The `ha` client:

- re-validates each entity ID with `re.fullmatch`, because in Python `$` also matches before a trailing newline, and percent-encodes it;
- sends at most 3 requests of 3 s each, to `GET http://supervisor/core/api/states/<entity_id>`;
- sets `redirect=False` and `retries=False`, and attaches `Authorization` only for the exact origin `http://supervisor`;
- caps the body at 64 KiB, requires `application/json`, and reads **only** the `state` field (≤ 255 characters).

| Helper situation | Effective value | Log |
| --- | --- | --- |
| Option unset | static option | — |
| State valid after normalization | helper value | INFO: `color = blue (from input_select.frame_gallery_color)` |
| HTTP 404, `unknown`, `unavailable` | static option | one WARNING |
| Value not in vocabulary | static option | WARNING with the sanitized value (≤ 64 characters) |
| Proxy unreachable, timeout, HTTP 30x, 401, or 403, oversize or non-JSON body, token absent | static option | one WARNING |

The resolver never fails the run (acceptance items `B3`, `B4`, `B5`).

### 15.4 Television address validation (D-125)

- Accept an IPv4 or IPv6 literal, or an RFC 1123 hostname. Reject schemes, ports, paths, and whitespace.
- Resolve **once**, in CONFIGURE, and accept only:
  - RFC 1918 (`10/8`, `172.16/12`, `192.168/16`);
  - `169.254/16`;
  - `fc00::/7`;
  - `fe80::/10` with a zone.
- Explicitly reject:
  - loopback, unspecified, and multicast addresses;
  - the container's own networks, and the Supervisor's internal app network. Both are determined at run time from the container's interfaces and the resolved addresses of `supervisor` and `homeassistant`.

  This keeps the television client, which sends the pairing token, away from internal services.
- The validated **IP literal** is what the television worker uses, which removes the validate-then-resolve window.
- The documentation recommends an IP literal with a DHCP reservation.
- Failure → `config_invalid` with a message naming the problem.

---

## 16. Dashboard and filter selection: three approaches compared

### 16.1 Comparison

| Criterion | A. Documented HA helpers | B. App Ingress UI | C. Future companion integration |
| --- | --- | --- | --- |
| What the user does | Creates up to three dropdown helpers in the UI, pastes the documented option lists, enters their entity IDs in the app options, and adds the dashboard card. | Opens the app's panel in the sidebar and picks filters there. | Installs a custom integration and gets native entities. |
| No SSH, no `configuration.yaml` | Yes; helpers and cards are UI-created. | Yes. | Only through a third-party store for custom integrations (HACS) or a manual file copy, which needs file access. The app cannot install it without mapping the HA configuration folder, which the constraints forbid. |
| Fits the one-shot lifecycle | Yes; the app reads helper states at start. | **No.** Ingress needs a running web server (port 8099, accepting only the Supervisor proxy). A `startup: once` app has no UI while stopped, and a resident process contradicts "no persistent background execution". | Yes; the integration starts the app. |
| Dynamic option lists | No; lists are copied from the documentation. | Yes. | Yes. |
| Automations and scripts | Excellent; helpers are native entities. | Poor, unless an extra API is added. | Excellent. |
| Loading state and preview | Supervisor "Running" entity plus Local File camera (§16.3). | Inside the panel only. | Native `image`, `sensor`, and `button` entities with exact state. |
| Security surface | Read-only GET of ≤ 3 state values. | A web server, request handling, CSRF; needs its own threat model. | Runs inside the Core process; a bug affects HA stability. |
| Implementation cost | Small: one module plus documentation. | High: UI, server, state, browser tests. | High: second codebase, HA quality rules, version coupling. |
| Maintenance risk | Low. | Medium to high. | High (HA integration API changes). |
| Dashboard-native feel | Good (entities card plus picture card). | Weak (iframe or web-page card). | Best. |

### 16.2 Recommendation (D-126)

- **Beta:** static options plus optional documented helpers (A). This is the only option that is cheap, secure, compatible with the one-shot lifecycle, and fully UI-based.
- **Ingress (B): not planned.** It would make the product resident, enlarge the attack surface, and still not give native entities.
- **Companion integration (C):** revisit after the beta. Two things keep that path open:
  - the versioned `current.json` and `last_run.json` schemas;
  - the standard Supervisor options mechanism.

### 16.3 Beta dashboard design (full YAML in Phase 6)

Dashboard actions cannot use templates. Because the app reads the helper states itself, the card never passes filter values, and its tap action is a static `hassio.app_start` call.

**Setup order**, written into the documentation:

1. Install the app from the one-click repository link and set `tv_host`.
2. Start the app, accepting the pairing prompt on the TV within 30 s. Repeat until the log's final line shows `outcome=delivered`. Only a delivered run creates `/media/frame_gallery/preview/latest.jpg`, and the Local File config flow's behaviour with a missing file is undocumented.
3. Add the Local File camera under the name **"Frame Gallery Preview"**. This is *expected* to give `camera.frame_gallery_preview`, but the config flow's fields are undocumented, so Phase 8 records the actual entity ID.
4. Enable the app's **Running** binary sensor, plus the Running switch for non-admin users. Both are disabled by default. Their entity IDs are recorded in Phase 8 and then written into the card, so the final copy-and-paste card is completed after Phase 8.
5. Paste the card.

**Preview.**

- **Primary:** the Local File camera shown in a `picture-entity` card.
  - Local File requires an allowlisted path. The documentation says every `media_dirs` folder is allowlisted by default and that local media defaults to `/media` on Home Assistant OS. That this covers our path is an **inference from two pages**, which Phase 8 verifies (R-07).
  - Users with a custom `media_dirs` get a note: their media-source key may not be `local`, and their allowlist may differ.
- **Zero-setup alternative:** a `picture` card with `image: media-source://media_source/local/frame_gallery/preview/latest.jpg`. It requires authentication, but its cache behaviour is undocumented.
- **Not used:** `/config/www`, which is served unauthenticated and needs the forbidden configuration-folder mapping, and a template image helper, which needs a plain HTTP URL that a stopped one-shot app cannot serve.

**Start.**

```text
tap_action:
  action: perform-action
  perform_action: hassio.app_start
  data: {app: <repository-hash>_frame_gallery}
  confirmation: optional
```

- `hassio.app_*` exists since Home Assistant 2026.2. Since 2026.6, the action validates only the slug's *syntax*, so a mistyped slug fails only when tapped; the troubleshooting documentation covers this.
- The slug's hash algorithm is undocumented. The public slug is therefore **observed** after installing through the one-click link and then printed in the documentation (Q-13). Users can read their own slug from the app's page URL. The Phase 8 development slug depends on the install route (Q-21).
- `hassio.app_start` is **admin-only**. The alternative for non-admin household members is the per-app **Running switch**. It is also disabled by default, and it stops a run if toggled while one is in progress. Phase 8 verifies both paths for non-admin users (Q-19).

**Loading state.**

- A conditional card, not per-card Visibility, which is unavailable inside stack and grid cards. It shows *"Updating artwork…"* while the Running binary sensor is `on`.
- The app always exits within `T` + 10 s. That the sensor then returns to `off` is an **inference**: the documentation describes the integration only as "local polling", with no interval.
- A run shorter than the polling interval may never show the loading state. Phase 8 measures this (Q-09, R-06).

**Fallback loading design**, used if Phase 8 shows poor latency. It works without observing an on→off transition:

- A UI-created **timer helper** (`restore` defaults to off) is the loading indicator.
- A UI-created script in `single` mode:
  1. starts the timer with a duration of `T` + 35 s: 300 s by default, 360 s at `selection_time_limit` = 120 (D-114). The documentation gives the value for each setting;
  2. calls `hassio.app_start` with `continue_on_error: true`;
  3. calls `homeassistant.update_entity` on the Running sensor;
  4. uses `wait_for_trigger` for the sensor to turn `off`, with `timeout` equal to the timer duration;
  5. cancels the timer.
- If any step fails, the timer still expires by itself, so the idle state always returns (acceptance item `G4`).
- Whether `continue_on_error` also covers the Unauthorized error is checked in Phase 8 (Q-19).
- If this fallback is needed, the acceptance-item `G1` deliverable becomes "card + script + timer". Q-09 records that trade-off.

**Cache freshness (acceptance item `G5`).**

- The camera proxy uses access tokens that expire, and the frontend refetches stills. The refresh interval and the token rotation are undocumented.
- Candidate remedies, **validated in Phase 8**:
  - `homeassistant.update_entity` on the camera after a run;
  - `local_file.update_file_path`, alternating between two published file names;
  - the media-source picture card.
- The long-term remedy is a native `image` entity, whose documented `image_last_updated` state makes the frontend refetch (companion integration).
- R-07 records the remedy chosen after measurement.

**Scheduling.** The documentation includes a UI automation example: daily at 07:00 → `hassio.app_start`.

---

## 17. Home Assistant packaging

The facts in this section come from the current developer documentation, which reflects the add-on → app rename in 2026.2 and the builder migration in 2026-04 (§25).

### 17.1 App metadata: illustrative `config.yaml` shape (D-129)

```yaml
name: Frame Gallery
version: "0.1.0"                 # must equal the image tag, the Git tag and the CHANGELOG entry
slug: frame_gallery
description: Sends one fresh artwork to a Samsung Frame TV each time it is started.
url: <project URL, decided with D-101 / Q-13>
arch: [aarch64, amd64]           # the only architectures Home Assistant still supports
image: ghcr.io/<org>/frame-gallery   # generic multi-arch manifest; omitted only for local development builds
startup: once                    # "for applications that don't run as a daemon"
boot: manual_only                # never auto-started at boot
init: false                      # required with the s6-overlay v3 base image (D-130)
stage: experimental              # until Phase 8 validation passes (§17.3)
homeassistant: "2026.2.0"        # minimum Core providing the hassio.app_* actions
homeassistant_api: true          # grants Core REST + WebSocket via the proxy on every install; the app
                                 # itself limits use to ≤ 3 state GETs, only when *_helper options are set
tmpfs: true                      # /tmp is a memory filesystem
timeout: 20                      # stop grace period: kill worker, finish RECORD, clean up
map:
  - type: media
    read_only: false             # grants read-write to ALL of /media; apparmor.txt narrows it (§17.6)
backup_exclude:
  - "cache/**"
  - "state/quarantine/**"
  - "tv/**"
options: { … §15.1 defaults … }
schema:  { … §15.1 schema … }
```

**Deliberately not set:**

| Key | Why not |
| --- | --- |
| `hassio_api`, `hassio_role` | Not needed; the default role is least privilege. |
| `host_network` | Lowers the rating. The television should be reachable through NAT (Q-16). |
| `privileged`, `full_access`, `docker_api` | Collapse the rating. |
| `ingress` | Not planned (§16). |
| `ports`, `devices`, `stdin`, `watchdog` | Not applicable. |
| `advanced` | Ignored since Supervisor 2026.03. |
| `build.yaml` | Deprecated. |

**Security rating.** Base 5, +1 for a custom `apparmor.txt` = **6**. `homeassistant_api` does not change the rating, but it does grant the API access described in the comment above. §18.1 treats that as a capability to contain, not as harmless.

**Boot mode.** `manual_only` prevents an unintended artwork change on every reboot. Users who want that behaviour can add an automation.

### 17.2 Container image (D-130)

- **Base.** `FROM ghcr.io/home-assistant/base:<pinned tag>@sha256:<digest>`: the official Alpine-based multi-platform base, pinned as the documentation recommends. Its s6-overlay v3 init requires `init: false`.
- **Open verification (Phase 6).** Pulling the base image from the registry needs the user's confirmation. Phase 6 then checks:
  - (a) the Alpine and Python versions behind the pinned base, which are not stated on any permitted page;
  - (b) that the container reaches "stopped" when the Python `CMD` exits, for exit 0 and for non-zero;
  - (c) that a Supervisor stop delivers SIGTERM to the Python process, with enough grace before SIGKILL;
  - (d) that `SUPERVISOR_TOKEN` is visible without `with-contenv`.

  **If any check fails**, the build switches to the recorded fallback: a plain Alpine base with `init: true`. The fallback also makes the Python version explicit (Alpine 3.24 → Python 3.14). Its inventory row must be completed before adoption, and copyleft surface is one of the selection criteria.
- **Python.**
  - The code targets **3.12–3.14**. CI runs all three; the container smoke test runs the base image's interpreter.
  - `python3` is installed with an **exact apk version pin** (`python3=<ver>-r<n>`), identical in the build and final stages, and recorded in the inventory.
- **Multi-stage build.**
  - The build stage creates a venv with `--without-pip`, then installs the runtime requirements through an external pip with `--require-hashes --no-deps --only-binary=:all:`. Nothing is compiled.
  - The final stage installs the same pinned `python3` and copies only the venv, the application source, and the notices.
- **Pillow comes from the PyPI wheel, never from Alpine's `py3-pillow`.** The Alpine package is older and links GPL-3.0-or-later `libimagequant`.
- **Labels** are declared in the Dockerfile:
  - `io.hass.version` comes from a required `ARG`;
  - `io.hass.arch` comes from `BUILD_ARCH`, or, when that is unset, from BuildKit's `TARGETARCH` (`arm64` → `aarch64`, `amd64` → `amd64`);
  - `io.hass.type="app"`, `io.hass.name`, `io.hass.description`, `io.hass.url`, `org.opencontainers.image.source`;
  - `org.opencontainers.image.licenses` is **omitted**: the image contains Apache-2.0, LGPL, GPL, and other components, and `THIRD_PARTY_NOTICES` describes them.

  A Phase 6 test inspects the labels of both platform images.
- **Entry point.** `CMD` runs `python -m frame_gallery`.
- **Notices.** `/usr/share/doc/frame-gallery/` holds:
  - `THIRD_PARTY_NOTICES`;
  - all license texts, including LGPL-3.0 and GPL-3.0;
  - the acknowledgements required by the libraries bundled in Pillow (for example IJG and FreeType);
  - the OS-package license list from the image SBOM (R-17).

### 17.3 Build, development install, and release gates

- The Dockerfile is the only build definition.
- **Local builds:** `docker buildx build --platform linux/arm64,linux/amd64`, with QEMU for the non-native platform.
- **Development install for Phase 8 (Q-21).** The unpublished app must reach the Home Assistant Green somehow. The options, each needing user approval, are:
  - the user copies the app folder into `/addons` through a file-share app;
  - a temporary private repository;
  - a development image push.

  On-device builds are the slow, storage-wearing mode the documentation discourages. The chosen route determines the development slug.
- **Release (Phase 9).** GitHub Actions using the Home Assistant builder's `build-image` and `publish-multi-arch-manifest` actions, producing `ghcr.io/<org>/frame-gallery:<version>`, signed with Cosign. Exact action inputs are taken from their documentation in Phase 9.
- **Release gates**, each mapped to a check:

  | Gate | Check |
  | --- | --- |
  | Tests | All tests pass before publishing; the test result is attached to the release. |
  | License inventory (acceptance item `H4`) | The inventory check passes, including bundled native libraries and OS packages. Publishing is blocked otherwise. |
  | Versions | `version` equals the Git tag, the image tag, and the CHANGELOG entry. Tags are immutable and never re-pushed. |
  | `stage: stable` | Only after the Phase 8 validation on the Home Assistant Green. |
  | Project license (acceptance item `H6`) | D-102 approved before any public release. |

### 17.4 Presentation and installation

- **App folder files.**
  - `README.md` (store blurb).
  - `DOCS.md` (full documentation, including the dashboard YAML and the IJG and FreeType acknowledgements).
  - `CHANGELOG.md` (Keep a Changelog format).
  - `icon.png` (128 × 128) and `logo.png` (≈ 250 × 100), both original artwork.
  - `translations/en.yaml`, giving a name and description for every option.
- **One-click link.** `https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=<URL-encoded repository URL>`. The redirect kept its add-on-era name.
- **Wording.** User text says "app" and mentions "formerly add-on" once. Technical identifiers keep their add-on-era names.

### 17.5 Runtime environment

| Item | Handling |
| --- | --- |
| Environment | At start, `SUPERVISOR_TOKEN` is read into memory and kept only if a `*_helper` option is set. The parent then reduces `os.environ` to an **allowlist** (`PATH`, `LANG`, `LC_ALL`, `TZ`). Every other variable is removed, including `SUPERVISOR_TOKEN`, the legacy `HASSIO_TOKEN`, proxy variables, `NETRC`, and CA overrides. Spawned workers inherit only the allowlisted environment. |
| Options | Read directly from `/data/options.json` (mode `0600`, readable by root). No bashio. Re-validated by the app. |
| Time | UTC internally. |
| SIGTERM | Raises `Cancelled`, with the handling in §7.6. |
| User | The parent runs as root, the platform default, because it must read `options.json` and write `/data` and the preview. Workers drop to an unprivileged ID (§11.3). Running the parent unprivileged too is evaluated in Phase 6 (Q-10). |

### 17.6 Required AppArmor policy (D-129)

The custom `apparmor.txt` is written from scratch. It is mandatory, not merely a +1 on the rating.

| Area | Rule |
| --- | --- |
| `/media/**` | read-only |
| `/media/frame_gallery/preview/**` | read-write, the only writable location under `/media` |
| Directory creation under `/media` | exactly `/media/frame_gallery/`, `/media/frame_gallery/preview/`, and `/media/frame_gallery/library/`; nothing else |
| `/data/**` and `/tmp/**` | read-write |
| Interpreter and libraries | `ix` for the interpreter; the paths that `multiprocessing` spawn needs (`/dev/shm`, `/proc/self/**`) |
| Network | `inet` and `inet6` stream and dgram only; `raw` and `packet` explicitly denied |
| Capabilities | Only what the privilege drop and worker management need (expected: `setuid`, `setgid`, `chown`, `kill`), plus whatever the s6 base proves to need. Everything else is denied. The final list is recorded in Phase 6 from complain-mode logs. |

The profile is developed in complain mode. It is verified in Phase 8 in enforce mode with two checks:

- a fresh-install first run (directory creation succeeds);
- a write outside `preview/` is denied.

---

## 18. Security and privacy

### 18.1 Threat model

| Threat | Vector | Mitigation |
| --- | --- | --- |
| SSRF, DNS rebinding | Provider metadata, redirects, identifiers inserted into URLs | Exact or label-boundary host rules; one resolution with every address checked as global (mapped forms unwrapped, CGNAT rejected); connect to the validated IP with the SNI hostname; peer check; identifier `fullmatch` and encoding; redirect re-validation (§10) |
| Decompression bomb, parser exploit | Remote or local image bytes | Decoded-byte caps; header limits before decode; bomb guard as an error; **all** Pillow use in an unprivileged worker with a memory ceiling, kill timer, scrubbed environment, and bytes-only results; the parent re-validates output; maintained Pillow (D-128) |
| Home Assistant API misuse | `SUPERVISOR_TOKEN`, which grants the Core REST and WebSocket API on every install | Removed from the environment at start and held in memory only when helpers are configured; never passed to workers; the application restricts itself to ≤ 3 GETs on a fixed URL template, with no redirects, and `Authorization` only for `http://supervisor` |
| Secret leakage | Logs, worker output, backups | Redaction at the formatter on fully formatted lines, including exception text (§19); worker output piped through the parent; third-party loggers capped at WARNING; tokens excluded from backups (expected; verified in Phase 8); token files `0600` |
| Path traversal, symlink attacks | Library files, the preview directory, temporary names | Fixed documented paths; `dir_fd` operations with `O_NOFOLLOW`; `O_EXCL` random temporary names; refusal when the preview path contains a symlink; `fstat` checks on open descriptors; entity-ID `fullmatch` |
| Log injection | Titles, filenames, helper values | Control-character stripping and length caps |
| Television misuse, internal-service exposure | `tv_host` | Resolved once; only LAN ranges accepted, with container and Supervisor networks excluded; the IP literal is passed to the worker (§15.4) |
| LAN adversary impersonating the television | ARP or DNS spoofing on the LAN | IP literal with a DHCP reservation; same-subnet requirement. The token's scope is undocumented; it is *assumed* to grant television control only (R-03). The library's TLS and certificate behaviour is undocumented, so a trust-on-first-use or pinning decision is made in Phase 5 (R-03). |
| Supply chain | Dependencies, base image | Hash-pinned wheels only; digest-pinned base; exact apk pin; license inventory; update cadence (D-128) |
| Excess privilege | Container and filesystem | Least-privilege configuration; mandatory AppArmor policy (§17.6); unprivileged workers |
| Provider content execution | HTML, JSON | Parsed as data with stdlib parsers only; size-capped; never executed or rendered |
| Privacy, telemetry | — | No telemetry; egress limited to the selected provider's hosts and the television; no user data in courtesy headers |

### 18.2 Parsing without extra dependencies

Provider JSON, and HTML only if a provider is ever approved to need it, is parsed with the standard library (`json`, `html.parser`). No lxml or BeautifulSoup (D-127).

---

## 19. Logging and diagnostics

- **Output.** Plain-text lines to stdout, which the Supervisor captures in the app log. INFO by default.
- **INFO** records:
  - a start banner: version, source, and effective filters with their provenance;
  - one aggregated WARNING for skipped local files (§9.2);
  - a selection summary: candidates seen, allowances used, elapsed time, and strict, fallback, or first-eligible;
  - the chosen artwork with its attribution;
  - the television result;
  - exactly one final line: `outcome=<name> exit=<code> elapsed=<s> [hint=…]`.
- **DEBUG** adds per-candidate decisions: identifier, dimensions, rejection reason.
- **Third-party loggers** (`urllib3`, `websocket`, `samsungtvws`, `PIL`) stay at WARNING even in debug mode.
- **Redaction** happens in the handler's formatter, on the **fully formatted line including exception text**. It matches known values (`SUPERVISOR_TOKEN`, and the current television token as read by the parent) and patterns (`token=[^&\s]+`, `Bearer\s+\S+`, `Authorization:`).
- **Workers.**
  - Workers install the same logging setup before importing any third-party code.
  - Each task is wrapped in a catch-all that returns only an error code and a sanitized message.
  - Worker stdout and stderr go to pipes that the parent reads, redacts, and re-emits.
- **Messages.** Error messages are short and actionable. Tracebacks appear only for `internal_error`.
- **`no_match` hints** distinguish four cases: "filters too restrictive", "nothing new left for these filters", "search limits reached", and "this source cannot use the configured filter value" (§9.1).

---

## 20. Testing strategy

### 20.1 Layers

| Layer | Scope | Network |
| --- | --- | --- |
| Unit | Geometry, classification and the upscale rule, vocabularies, options, deadline, allowance, phase-sum invariant, atomic store (crash injected after every step), history bounds and version handling, cache eviction, redaction, and **symlink attacks**: a symlink planted at the temporary name; `preview/` or `/media/frame_gallery` as a symlink; a non-regular file matching the sweep pattern; a library file swapped for a symlink after enumeration | Blocked |
| Contract | Every provider adapter against the shared suite: laziness, bounds, identifier stability, deadline obedience, rights basis, filter semantics | Blocked |
| Component | Gateway against a fake transport: rebinding resolver, IPv4-mapped loopback, suffix confusion, identifier traversal, gzip on an image, slow-drip body, multi-address connect, redirect abuse, 429/`Retry-After`, oversize, pacing. Also: helper client (30x, oversize, trailing-newline ID); imaging worker under the real memory limit; television adapter against a library double | Blocked |
| Integration | Full runner with real workers; temporary directories standing in for `/data`, `/media`, and `/tmp`; fake provider and fake television. Covers: failure injection at every stage; kill after `selected`; SIGTERM between the receipt and RECORD; the worker sees no token; a hostile worker result; a token-bearing exception is never printed; multi-run exhaustion (acceptance item `E6`) | Blocked |
| Timing | Watchdog fires and kills the worker group within the allowance; worker kill timers | Blocked |
| Container | Both platform builds; label inspection; smoke run with local media and the television disabled by a test-only setting; exit and stop behaviour (D-130 checks b–d) | Offline |
| Live (Phase 8, after approval) | Real Home Assistant Green and television, following the Phase 8 checklist (§23) | Only then |

A small `conftest` guard makes socket connections raise, so any accidental network access fails loudly (acceptance item `H2`).

### 20.2 Seams

`Clock`, `RandomSource`, `Transport`, `Resolver`, `Television`, `FileSystemRoots`, `Executor` (in-process or process-based), and `SupervisorClient`.

No module reads the wall clock, the global random generator, environment variables, or absolute paths directly.

### 20.3 Fixture policy

- Every fixture is authored in this repository. Its header records the author, the observed URLs, and the date.
- **Fixtures are synthesized.** They keep the observed structure but replace titles, descriptions, credit lines, URLs, and identifiers with invented values, unless a field is CC0. Observed HTML is never stored verbatim.
- Observation requests, which need user approval in Phase 4, fetch **metadata only, never image files**.
- Test images are generated in the tests: sizes, modes, EXIF orientations 1–8, alpha, palette, 16-bit, CMYK, truncated files, and headers claiming huge dimensions. No third-party artwork is committed.

### 20.4 Quality gates (commands established in Phase 2)

- `ruff check` and `ruff format --check`; `mypy --strict` on `src/`.
- `pytest` with branch coverage:
  - ≥ 90 % overall;
  - **100 % of branches** in `budget`, `selection`, `store`, `net.gateway`, `providers/*`, `ha`, and `isolation`; in the `imaging` encode fallback (the quality-85 re-encode and its failure branch); in the `app` runner's ATTEMPT loop and outcome classification; and on the television reconnect path. These modules contain every bounded loop and fallback (acceptance item `H1`).
- CI runs the suite on Python 3.12, 3.13, and 3.14.
- An import-boundary check (§5).
- A license-inventory check. The image's Python packages, the Pillow-bundled native libraries (from the wheel SBOM), and the OS packages (from the image SBOM) must all match the inventory in `DECISIONS.md` and `THIRD_PARTY_NOTICES` (acceptance item `H4`).

---

## 21. Proposed repository layout

```text
repository.yaml                     # HA app repository metadata (Phase 6)
README.md  ARCHITECTURE.md  DECISIONS.md  STATUS.md  TASKS.md  …   # project docs
THIRD_PARTY_NOTICES.md              # Phase 3 onward, grows per dependency
LICENSE                             # only after the user approves D-102
frame_gallery/                      # the app directory = Docker build context
  config.yaml   Dockerfile   .dockerignore   apparmor.txt
  DOCS.md   README.md   CHANGELOG.md   icon.png   logo.png   translations/en.yaml
  requirements/runtime.txt          # hash-pinned (generated with uv, D-128)
  pyproject.toml                    # tool configuration and dev dependencies
  src/frame_gallery/
    __main__.py                     # no import-time side effects (spawn-safe)
    app/         runner, outcomes, context, signals
    config/      options, vocabulary, tv_address
    ha/          supervisor_client, helper_overrides
    budget/      clock, deadline, allowance, phases, watchdog
    net/         gateway, policy, resolver, transport
    providers/   contract, rights, local_media, aic/{gateway,parse,vocabulary}
    selection/   shortlist, geometry
    imaging/     worker_tasks (inspect, prepare), fit, jpeg_header (stdlib validator)
    tv/          port, samsung_task, token_store
    store/       atomic, history, cache, workspace, preview, records
    isolation/   executor, bootstrap, channel
    logs/        setup, redact
  tests/
    unit/  contract/  component/  integration/  timing/  container/
    fixtures/authored/
```

---

## 22. First public beta: scope

### 22.1 Included (D-120)

- One-shot run with every bound, outcome, and cleanup guarantee in this document.
- Sources: local media and the Art Institute of Chicago (the default).
- Static filters (colour, museum/collection, style/period), plus optional helper overrides.
- Landscape-only; strict 16:9 with the contain fallback; the upscale rule; `contain` and `cover`; background colour.
- Atomic history with pre-staging; atomic preview; the small Art Institute metadata cache; self-healing pairing.
- Documentation:
  - one-click installation;
  - explained options;
  - dashboard card and setup order;
  - helper setup;
  - scheduling automation;
  - troubleshooting for each outcome;
  - honest limitations: Art Institute images are 1686 px wide and upscaled by up to ≈ 2.28× in `contain` mode; no Museum of Modern Art or Musée d'Orsay source was found; keep the app's Watchdog off.
- Pre-built `aarch64` and `amd64` images from one Dockerfile.

### 22.2 Deferred

- Companion integration and native entities.
- Multiple sources with rotation or cross-source fallback.
- Further open-collection providers (§9.7).
- Google Arts & Culture, until an official API exists (Q-01).
- Remote-probe machinery, until a provider needs it (§8.3).
- Matte selection.
- Automatic helper provisioning.
- An unprivileged parent process (Q-10).
- A configurable library folder.
- Local colour or style filtering.
- A history reset option (Q-06).
- Additional CPU architectures, only if Home Assistant adds support for them.

### 22.3 Not planned

- **Ingress UI** (D-126).
- **Bing** (Q-17).
- **Managing old images on the television** (a product non-goal).

---

## 23. Phase mapping and approvals

| Phase | Delivers | Approvals needed first |
| --- | --- | --- |
| 2: skeleton and contracts | `budget` (including the phase calculator), `config`, outcomes, ports, `isolation` skeleton, `logs`, tooling, network-blocking guard, import-boundary check | This architecture; Q-02, Q-12, and Q-18 items 4–5; `frame_gallery` as the provisional identifier; dev dependencies including `uv`, once the `mypy-extensions` and `pathspec` SPDX IDs are recorded |
| 3: history and image pipeline | `store.*`, `imaging` worker tasks, JPEG validator, preview publisher, `THIRD_PARTY_NOTICES` start | Pillow row, including its bundled-library sub-table, verified from the pinned wheels |
| 4: provider framework | `net` gateway, `selection`, `providers.local_media`, `providers.aic` (after a live-documentation re-check), vocabulary tables, contract suite | Q-01, Q-17, Q-18 items 1–3 (the specification and `TASKS.md` amendments), Q-03, Q-04, Q-11, Q-14, Q-20, Q-22; the `urllib3` and `certifi` rows; any observation requests |
| 5: television adapter | `tv` task, markers, token store, error mapping, mocked tests | Q-15; `samsungtvws` row and its LGPL-3.0 obligations |
| 6: packaging | `config.yaml`, Dockerfile, `apparmor.txt`, translations, `DOCS.md`, dashboard YAML, container tests | Base-image pull; D-130 checks a–d; Q-06, Q-08, Q-09, Q-10; the Buildx, QEMU, and SBOM-tool rows |
| 7: offline validation | Full gate run, provenance and license audit, failure-path exercises | — |
| 8: Green validation | Checklist: Q-05, Q-07, Q-09, **Q-16 (go/no-go for `host_network`)**, Q-19 (including a mistyped slug), Q-21, R-07, R-09, R-21; AppArmor in enforce mode (fresh install); entity IDs for the card; backup archive without `tv/` | **Explicit user approval** (the `TASKS.md` Phase 7 gate) |
| 9: public beta | Repository, CI, images, one-click link, release notes, release gates (§17.3) | D-101, D-102, Q-13; the builder-action and Cosign rows |

---

## 24. Risks and open questions

Risks (R-xx) and open questions (Q-xx) are maintained in `DECISIONS.md`. The most consequential:

- **Q-01, Q-17, Q-18 / R-01, R-05.** Neither web source named in the specification has a documented API.
  - Google Arts & Culture's `robots.txt` permits public HTML and disallows `/api/*`. The conflict is with Google's Terms and the partners' image rights.
  - Bing's `robots.txt` disallows its image path `/th?` for general crawlers, which is decisive; an archive rule also exists. Bing's agreement restricts the photos.
  - No open-access API or image licence was found for the Museum of Modern Art or the Musée d'Orsay. Aggregator coverage, for example Europeana, has not been checked yet.

  The recommended beta therefore deviates from the specification's provider list. It also deviates on the step 9/10 order (D-113) and the meaning of the 60 s limit (Q-02). All of these need the user's decision.
- **R-03 / Q-15.** Samsung does not document Art Mode, and the transport library's 3.x art API is undocumented on PyPI.
- **Q-09 / R-06.** The loading indicator depends on an undocumented polling interval; there is a timer-based fallback.

---

## 25. Sources consulted in Phase 1

All research was read-only. The material fetched was public documentation pages, package-index metadata, and policy pages or `robots.txt` files. It also included one Microsoft Q&A answer and search-result snippets where a page blocked automated readers; both are marked where cited. No provider API, image URL, Home Assistant instance, television, GitHub page, or container registry was contacted. Five topic researchers ran, and four were independently re-checked by an agent that tried to refute each decision-critical fact.

**Home Assistant** (developers.home-assistant.io, www.home-assistant.io, my.home-assistant.io):

- App docs: `configuration`, `publishing`, `presentation`, `repository`, `communication`, `tutorial`, `testing`, `security`.
- Supervisor API endpoints and models.
- Builder-migration blog post (2026-04-02) and s6-overlay v3 blog post (2022).
- Release notes 2026.2 and 2026.6; changelogs 2026.2, 2026.6, and 2026.9.
- Integration pages: `hassio`, `local_file`, `homeassistant`, `media_source`, `template`, `input_select`, `input_text`, `script`, `timer`, `default_config`.
- Action pages: `hassio.app_start`, `hassio.app_stdin`, `local_file.update_file_path`.
- Dashboard pages: `picture-entity`, `picture`, `picture-glance`, `button`, `features`, `conditional`, `cards`, `iframe`, `actions`.
- Developer pages: scripts, REST API, auth API, image entity, custom integration manifest, config-flow handler, blueprint selectors.
- `my.home-assistant.io` FAQ and redirect descriptions.

**Dependencies:**

- PyPI metadata for `samsungtvws` (all 35 releases, plus provenance), `pillow`, `requests`, `urllib3`, `idna`, `certifi`, `charset-normalizer`, `websocket-client`, `yarl`, `multidict`, `propcache`, `httpx` and its dependency tree, `pytest` and its dependencies, `pytest-cov`, `coverage`, `ruff`, `mypy` and its dependencies, `uv`, and `pip-tools`.
- Documentation sites: pillow.readthedocs.io, requests.readthedocs.io, www.python-httpx.org, devguide.python.org, peps.python.org (PEP 770).
- pkgs.alpinelinux.org and alpinelinux.org/releases.

**Providers and Samsung:**

- Google: Terms and service-specific terms; the Cultural Institute partner FAQ and metadata pages; `artsandculture.google.com/robots.txt`.
- Microsoft: `www.bing.com/robots.txt`; the Services Agreement (current and upcoming versions); the Bing Search API retirement notice; one Q&A answer, cited only as such.
- The Met: image policy, terms, and API article.
- The Art Institute of Chicago: `api.artic.edu/docs` and image licensing.
- Other museums and aggregators: `openaccess-api.clevelandart.org`; the Europeana API, key, and terms pages (pro.europeana.eu only through search snippets); the `data.rijksmuseum.nl` docs, about page, and policy; the MoMA collection and licensing pages; the Musée d'Orsay collection FAQ.
- Samsung: developer.samsung.com Smart TV API references and the Smart View SDK debugging page; a samsung.com consumer support page.
- SmartThings: developer.smartthings.com capability references and public API.

**Deliberately not consulted:**

- any GitHub-hosted page, including the approved dependencies' repositories, the Met's API documentation site, and the Home Assistant builder and example repositories;
- community forums, except one Microsoft Q&A answer that §9.3 cites explicitly as a non-documentation source;
- all predecessor or community Frame projects. Several forum threads about Frame Art Mode appeared in search results and were **not** opened.

---

## Appendix A: Acceptance traceability

| ID | Acceptance item (abridged) | Designed in | Verified by |
| --- | --- | --- | --- |
| A1 | Repository addable via UI or one-click link | §17.4 | Phase 9 live check |
| A2 | Green discovers the app without SSH | §17 | Phase 8/9 live check |
| A3 | Green installs the pre-built `aarch64` image | §17.2, §17.3 | Phase 9 live check |
| A4 | `amd64` image from the same source | §17.2, §17.3 (release gates) | Phase 6 container build and label test; Phase 9 CI |
| A5 | No `configuration.yaml` change | §15, §16.3, §17 | Documentation review; Phase 8 |
| A6 | Understandable option names and descriptions | §15.1, §17.4 | Translation review; Phase 8 |
| B1 | Missing TV IP prevents start with a clear message | §15.1, §15.4 | Unit; Phase 8 (Supervisor message) |
| B2 | Static filters work without helpers | §15.2, §15.3 | Unit + integration |
| B3 | Valid helper overrides the static value | §15.3 | Component (fake proxy) |
| B4 | Missing or unavailable helper falls back | §15.3 | Component (404, `unavailable`, timeout, 401, 30x, oversize) |
| B5 | Invalid values rejected or normalized predictably | §15.2, §9.1 | Unit (normalization table; an invalid or unmappable helper value falls back to the static value) |
| B6 | Defaults preserve the full artwork | §11.2, §15.1 | Unit + imaging invariants |
| C1 | Combined filters applied together | §9.4, §15.2 | Contract tests with synthesized fixtures |
| C2 | Portrait and square rejected when landscape-only | §8.1, §8.2 | Unit (classification table) |
| C3 | Sent identifiers skipped across restarts | §13.3, §8.2 | Integration (two runs, fresh processes) |
| C4 | Probe budget never exceeded | §7.2, §8.3 | Unit (counting fake gateway); local-inspection allowance unit test |
| C5 | Total deadline plus a small allowance never exceeded | §7 | Unit (phase-sum invariant, fake clock) + timing test (watchdog) |
| C6 | Restrictive filters fall back to landscape | §8.2 | Unit (fallback branches, shortlist fill) |
| C7 | No candidate → clean exit, no upload call | §4.2, §8.2 | Integration (fake television spy) |
| C8 | No infinite retries on provider failures | §7.4, §10, §4.2 (exit policy) | Component (failing transport counts attempts) |
| D1 | Non-16:9 landscape fully visible on 3840 × 2160 | §11.2 | Unit + imaging test |
| D2 | `contain` crops nothing | §11.2 | Invariant tests |
| D3 | Black margins by default | §11.2, §15.1 | Imaging test samples margins |
| D4 | `cover` crops only when selected | §11.2 | Imaging test |
| D5 | EXIF rotation corrected | §11.1 | Generated orientation 1–8 images |
| D6 | RGB, RGBA, palette, greyscale → television-compatible JPEG | §11.1 | Generated mode matrix |
| D7 | Excessive size, pixels, or bytes rejected safely | §10, §11.1, §11.3 | Component + worker tests under the real limit |
| D8 | Preview bytes correspond to the television image | §6, §11.3, §13.5 | Integration (parent SHA-256 of upload = preview) |
| E1 | Upload and select as active art | §12 | Adapter tests with library double; Phase 8 live |
| E2 | Pairing requirement reported clearly | §12.2, §12.4 | Adapter mapping tests |
| E3 | Connection timeouts and rejection end cleanly | §12.3, §12.4 | Worker kill test + marker classification tests |
| E4 | Failed uploads not recorded | §4.1, §12.4 | Integration failure matrix |
| E5 | Success records exactly one qualified identifier | §13.2, §13.3 | Integration (including kill after `selected`) |
| E6 | No resend while unsent eligible works remain | §8.2, §9.4, §13.3 | Integration (multi-run, nearly exhausted fake catalogue) |
| F1 | Temporary files removed after success | §14 | Integration |
| F2 | Temporary files removed after provider, network, decode, processing, and upload failures | §14, §4.2 | Integration failure-injection matrix (one case per §4.2 failure outcome) |
| F3 | Repeated runs do not grow temporary storage | §14, §13.1 | Integration (N runs, byte-bound assertions) |
| F4 | History survives restarts and upgrades | §13.2, §13.3 | Unit (versions, migrations, newer-version refusal) + Phase 8 |
| F5 | Corrupt history quarantined or recovered | §13.2 | Unit (truncated, invalid, wrong schema, `.bak`, stale `.bak.tmp`) |
| F6 | Cache size and age limits enforced | §13.4 | Unit (fake clock) |
| F7 | Preview never selected as local source | §9.2 | Unit (three guards) |
| G1 | One complete copy-paste dashboard card | §16.3 | Phase 6 documentation review. Final entity IDs are inserted after Phase 8. If the fallback is needed, the deliverable becomes card + script + timer (Q-09). |
| G2 | Card shows the latest preview | §16.3 | Phase 8 live |
| G3 | Tapping starts the app | §16.3 | Phase 8 live (admin and non-admin, Q-19) |
| G4 | Loading state always returns to idle | §7, §16.3 | Deadline tests + Phase 8 live (Q-09; timer fallback) |
| G5 | New preview shown without a stale cache | §16.3 | Phase 8 live (remedy chosen and recorded under R-07) |
| G6 | Setup needs no `configuration.yaml` edit | §16.3 | Documentation review + Phase 8 |
| H1 | Unit tests cover every bounded loop and fallback | §20.4 | 100 % branch gate on the listed modules |
| H2 | Integration tests need no live services | §20.1, §20.3 | Network-blocking guard |
| H3 | Logs contain no secrets or payloads | §18, §19 | Redaction tests covering parent and worker output, including exception text |
| H4 | Dependency licenses and notices complete | `DECISIONS.md` inventory; §17.3 | License-inventory check (Python, bundled native, OS) as a publish gate |
| H5 | No excluded predecessor material | §2.1, §20.3 | Phase 7 provenance review |
| H6 | License approved before publication | D-102; §17.3 | Release gate |
| H7 | Live Green run only after approval | §23; `TASKS.md` Phase 7 gate | Gate |
