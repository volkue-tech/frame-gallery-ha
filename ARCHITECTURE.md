# Frame Gallery for Home Assistant — Architecture proposal

Status: **Revision 2, with final gate corrections.**

- Revision 1 (commit `d42adf5`) was conditionally accepted in the Codex review.
- Revision 2 (commit `9352e77`) was accepted in the Codex final gate review, subject to one factual dependency correction and eight product decisions. Both are applied here.

- Codex gave final approval of Phase 1 at commit `dda877c` and authorized Phase 2, with one gate adjustment: verification of the remaining `pillow.libs` entries moved to the Phase 6 runtime-wheel inspection (§23).
- Phase 2 (core, deterministic selection, and rendering) is implemented. Where the implementation refines this document, the refinement is recorded in D-141 to D-145 and marked in the text.
- The user approved Phase 3 (provider adapters) on 2026-09-27. At its start, the Art Institute and Cleveland documentation was re-read (documentation pages only, D-146). §8.3, §9.2, §9.5, §9.6, §10, §15.2, and §23 are amended to match.
- Phase 3 is implemented. Its refinements of this document are recorded in D-147 (gateway), D-148 (helper reader), D-149 (local media), D-150 (Art Institute), D-151 (Cleveland), and D-152 (vocabulary version 1, the narrowed capability matrix, and the contract suite).
- The Phase 3 gate passed on 2026-09-27 (user decision). D-146 to D-152 are accepted, and Q-25 is resolved with option (a): the first beta ships without a colour filter, and the Art Institute supports only the period filter. §1, §9.2, §9.3, §15.1, §22.1, §23, and Appendix A are amended to match.
- Phase 4 (bounded state and duplicate prevention) is implemented, and its gate passed on 2026-09-27 (user decision). D-153 to D-159 are accepted, and the 20 000-entry bound is accepted for the first beta (R-29). §4.1, §4.2, §5, §9.1, §12.4, §13.2 to §13.6, §14, §21, §22.1, §23, and Appendix A are amended to match. Phase 5 is authorized (§23).
- Phase 5 (Samsung adapter contract) is implemented, and its gate passed on 2026-10-02 (user decision, after the Codex gate review). D-160 to D-164 are accepted. D-165 is accepted on the condition that the Linux and root isolation tests and the worst-case preparation measurement under the real `RLIMIT_AS` pass in Phase 6; they are mandatory before any live test on the Home Assistant Green. Art API 0.97 stays unsupported in the beta, TLS pinning is decided after the TV's certificate is observed in Phase 8, `inspect` gets parent-opened read-only descriptors (where possible) and batches in Phase 6, the 1 GiB image-worker limit stays until the Linux measurement, and AppArmor child profiles stay in Phase 9. §4.2, §4.3, §5, §7.2, §11.1, §11.3, §12.1, §12.2, §12.4, §13.1, §13.6, §14, §17.6, §18.1, §20.4, §21, §23, §24, and Appendix A are amended to match. Phase 6 is authorized (§23).
- Phase 6 (Home Assistant app packaging) is implemented, and its gate passed on 2026-10-03 (user decision, after the Codex review and its follow-up checks). D-166 to D-172 are accepted, with the 1 GiB image-worker limit unchanged. The native `amd64` memory measurement is mandatory before an `amd64` version is published, at the latest in Phase 9; the qualified licence review and the enforcement of the AppArmor profile stay release prerequisites. Before the gate, at the user's request (2026-10-03), the Pillow statements in §17.2, §23, and §24 were corrected to the authoritative inspection of the exact runtime wheels (D-171): neither `libimagequant` nor FriBiDi is in them. §4.3, §5, §8.3, §9.3, §11.1, §11.3, §15.1, §15.4, §16.3, §17.1 to §17.6, §21, §22.2, §23, §24, and Appendix A are amended to match. Phase 7 is authorized (§23).
- Phase 7 (offline release validation) is done and stopped at its gate: `RELEASE_CANDIDATE.md` reports it, and D-173 (how it validated) awaits the gate.

Date: 2026-09-26 (Phase 3 and Phase 4 amendments: 2026-09-27; Phase 5 amendments: 2026-10-02; Phase 6 amendments: 2026-10-03)
Author: Claude (Phase 1 owner)

This document is documentation only. The YAML fragments, signatures, and pseudo-code below illustrate interfaces and configuration *shape*. They are not application code. Everything is authored and tested in the phases that follow approval.

**Cross-references**

- `D-1xx` decisions, `R-xx` risks, and `Q-xx` open questions are all in `DECISIONS.md`.
- Acceptance items such as `C4` refer to `ACCEPTANCE_TESTS.md`: the section letter, then the item's position within that section. New items are always appended, so IDs stay stable.

**Review history**

1. *Internal review, revision 1.* Four of the five Phase 1 research areas were independently re-checked. The Python-dependency facts are re-verified from the pinned distributions before each dependency enters. A six-lens internal review produced 58 confirmed findings, and all of them were incorporated.
2. *Codex review of `d42adf5`.* The architecture was conditionally accepted. This revision applies the user's decisions and the review's corrections on:
   - beta providers;
   - the filter model;
   - the 120 s deadline;
   - the TV-upload exclusion ledger;
   - preview freshness;
   - approved decisions;
   - implementation sequencing.
3. *Revision 2 research.* The new facts on the Cleveland API and Home Assistant preview options were researched from documentation pages only. The key facts were independently re-checked; the citation guidance and the refresh cadence were not (§25).
4. *Codex final gate review of `9352e77`.* The architecture changes were accepted. Two changes were applied:
   - **Pillow inventory.** Codex inspected the official Pillow 12.3.0 wheels. They bundle GPL-3.0-or-later `libimagequant` and LGPL-2.1-or-later FriBiDi, contrary to revision 2's claim. The inventory, D-102, D-135, and R-25 are corrected. *Superseded in Phase 6 (D-171): the inspection of the exact two runtime wheels found neither library in them; Pillow's SBOM, which that finding came from, lists both only as optional dependencies.*
   - **Accepted decisions.** Q-03 (strict ±1 %), Q-04, Q-08, Q-09, Q-11, Q-12 (RFC 1918 only), Q-18 item 4 (D-113), and Q-23 (30 days) are recorded as accepted.

---

## 1. Summary of the recommendation

Frame Gallery is a **single-shot Python program packaged as a Home Assistant app**. Each start performs exactly one bounded *run*, with a **120-second** default total deadline:

1. validate the options;
2. resolve the filters;
3. shortlist at most two artworks from the selected source;
4. prepare a 3840 × 2160 JPEG;
5. upload it to the television and select it;
6. record the result;
7. publish the same bytes as the dashboard preview;
8. clean up and exit.

A run that finds nothing to show ends within **70 seconds**.

The architecture rests on nine decisions:

1. **Synchronous core with a strict 120 s budget** (D-106, D-114). A normative phase table allots:
   - 10 s to configuration and helpers;
   - 60 s to discovery, download, verification, and preparation;
   - 40 s to the television;
   - 10 s, reserved, to recording and cleanup.

   Every timeout is clamped to the remaining deadline, and a watchdog is the last resort.
2. **Ports and adapters** (D-107). The orchestrator depends only on narrow interfaces. Tests substitute fakes.
3. **One guarded internet gateway** (D-108). It enforces:
   - exact host allowlists;
   - a single DNS resolution, with every address checked as global;
   - TLS verification;
   - re-validated redirects;
   - decoded-byte caps and per-request totals;
   - provider pacing.
4. **Isolated, unprivileged workers** (D-109). All image parsing, and the whole Samsung library interaction, run in spawned child processes. Each worker has:
   - an allowlisted environment;
   - an unprivileged user ID;
   - an address-space ceiling;
   - a kill timer;
   - a bytes-only JSON channel.
5. **Atomic, bounded state with two exclusion records** (D-110, D-137).
   - The *confirmed sent history* changes only after the television confirms selection.
   - A separate *TV-upload exclusion ledger* records every artwork the television confirmed receiving, even if selection then failed.
   - A write-ahead *uncertainty quarantine* covers uploads whose outcome is unknown.
   - Artworks in any of the three are never selected again.
6. **Preview through a UI-configured Local File camera** (D-111, D-140). The camera reads `/media/frame_gallery/preview`. Home Assistant OS creates `/media` itself, and its default media directories are allowlisted, so no `configuration.yaml` edit is needed. Preview freshness is **release-blocking**: Phase 8 must prove one refresh mechanism in repeated live tests.
7. **Distinct, honest filters** (D-123, D-124).
   - *Source/museum* selects the provider.
   - *Department/collection*, *style/period*, and *colour* filter within it.
   - A published capability matrix shows what each source supports. Unsupported filters are visibly reported, never silently claimed.
8. **Smallest useful public beta** (D-120), built for `aarch64` and `amd64`, with three sources:
   - local media;
   - the **Art Institute of Chicago** (D-132): documented API, CC0 public-domain works, with the period filter only in the first beta (D-146; Q-25, option (a));
   - the **Cleveland Museum of Art** (D-136): documented Open Access API, CC0 records only, the documented 3400 px print JPEG, with department and period filters.

   Google Arts & Culture and Bing are excluded, because neither has a documented API compatible with its terms (§9.4).
9. **Vertical-slice implementation order** (D-139). The core behaviour is testable early:
   1. selection and rendering;
   2. provider adapters;
   3. state and duplicate prevention;
   4. Samsung adapter;
   5. packaging;
   6. validation;
   7. AppArmor and release hardening.

   No final acceptance criterion is weakened.

---

## 2. Inputs, principles, and independence

### 2.1 Inputs

This proposal draws only on:

- the repository specifications, as amended after the Codex review;
- the official Home Assistant developer and user documentation;
- package-index metadata and dependency documentation;
- artwork providers' published policy pages, `robots.txt` files, and documented APIs.

No predecessor project, its repository or documentation, or any community write-up about Frame art automation was consulted, and no GitHub-hosted page was fetched. One Microsoft Q&A answer and some search snippets were used, as marked in §9.4 and §25.

### 2.2 Design principles

| Principle | Consequence in this design |
| --- | --- |
| Everything is bounded | Every loop has an allowance, every request a total, every phase a budget, and every worker a kill timer. A watchdog backs them up. |
| Fast feedback | At most 120 s per run; `no_match` within 70 s. |
| The television is touched last | Before any contact, four conditions hold: a validated JPEG exists, the next history generation is written, the upload intent is recorded, and the full television budget remains. |
| Never upload the same work twice | Confirmed history, the upload ledger, and the quarantine are all consulted before selection (D-137). |
| Record displayed works only after success | History, the current artwork, and the preview change only after the `selected` confirmation. |
| All input is untrusted | Options, helper states, metadata, URLs, identifiers, filenames, image bytes, and worker results are all validated where they enter. |
| Least privilege | No host network, privileged mode, Supervisor API role, or configuration-folder mapping. Workers run unprivileged, and AppArmor narrows file access. |
| Honest capabilities | Unsupported filters are reported, not faked (§9.2). |
| Observable outcomes | Every run ends with one classified outcome and one summary line. Every run also writes a last-run record, except watchdog termination, which writes only one log line. |

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

- the local television, reached through its configured IPv4 address;
- the one provider selected for this run, plus its documented image host;
- the Supervisor's Core API proxy, only for configured helpers or an explicit loading timer (D-176).

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
| CONFIGURE | Reduce the environment to the allowlist (§17.5). Take the non-blocking lock (§13.3). Sweep leftovers (§14). Validate the options, including the television's IPv4 address (§15.4). | unchanged |
| RESOLVE_FILTERS | Apply optional helper overrides, with static fallback. | unchanged (never fails) |
| SELECT | Discovery; exclusion by history, ledger, and quarantine; shape and format checks; ranking. Produces a shortlist of at most two candidates (§8.2). | unchanged |
| ATTEMPT | For each shortlisted candidate: FETCH, then the image worker verifies real dimensions and PREPAREs the JPEG. A failure moves on to the next candidate. | unchanged |
| PRE-STAGE | Validate `delivery.jpg` in the parent. Write and `fsync` the next history generation as a temporary file. Re-check the television budget. Only then **commit an `uncertain` upload intent** to the ledger (§13.6). | unchanged |
| DELIVER | The television worker connects, checks art mode, uploads, and selects, reporting markers (§12.1). On `uploaded`, the parent promotes the ledger entry. | see §12.4 |
| RECORD | Only after `selected`: rotate `.bak` (best-effort), then rename the pre-staged history into place. Not cancellable. | changed |
| PUBLISH | Only after `selected`: publish the delivery bytes atomically as the preview, and update `current.json`. | changed |
| FINISH | Write the last-run record (every outcome except watchdog termination), log the summary line, and exit. *Amended at the Phase 4 gate (D-157):* first write the provider's metadata cache once, within FINISH's deadline minus the last-run reserve. | — |

**Ordering (D-113, accepted).** The confirmed sent history is recorded before the preview is published. `PRODUCT_SPEC.md` lifecycle steps 9 and 10 were amended to this order in the final gate review. Duplicate prevention does not depend on the order, because the upload ledger already excludes the work once it is uploaded.

### 4.2 Outcome taxonomy and exit codes (D-133)

| Outcome | Meaning | Television | Sent history | Upload ledger | Log |
| --- | --- | --- | --- | --- | --- |
| `delivered` | Selected, recorded, preview published | changed | +1 | `uploaded` | INFO |
| `delivered_with_warnings` | Selected and recorded; preview or record file not written | changed | +1 | `uploaded` | WARNING |
| `delivered_unrecorded` | Selected; the history rename failed; PUBLISH still attempted | changed | unchanged | `uploaded`, which still excludes the work | ERROR |
| `no_match` | Nothing deliverable and no transport failure (rule below) | unchanged | unchanged | unchanged | INFO with a hint |
| `config_invalid` | Options or television address invalid | unchanged | unchanged | unchanged | ERROR |
| `already_running` | State lock held | unchanged | unchanged | unchanged | WARNING |
| `state_error` | History or ledger written by a newer version, or pre-staging failed (full or read-only `/data`). *Amended at the Phase 4 gate (D-153, D-154):* also a history or ledger file that exists but cannot be read, a lock failure other than contention, and an upload intent that could not be made durable. | unchanged | unchanged | unchanged | ERROR |
| `source_failed` | Provider or network failure, nothing delivered | unchanged | unchanged | unchanged | ERROR |
| `image_failed` | Processing failed for every attempted candidate | unchanged | unchanged | unchanged | ERROR |
| `tv_unreachable` | Connect failure, or a connection lost, timed out, or given an unexpected response before `selected` | per the last marker (§12.4) | unchanged | per the last marker | ERROR |
| `tv_not_authorized` | Pairing not accepted in time, or token rejected | unchanged | unchanged | intent removed | ERROR |
| `tv_rejected` | Art mode unsupported, or an explicit refusal of the upload or selection | per the last marker | unchanged | per the last marker | ERROR |
| `deadline_exceeded` | Not enough budget left for the television phase (PRE-STAGE check), or for the upload after pairing (`insufficient_time`, §12.1), or a CONFIGURE overrun (D-141). *Amended at the Phase 5 gate (D-162):* also `insufficient_time` before the TV is contacted (too little time to connect and upload), without a hint. | unchanged | unchanged | unchanged; any intent removed | ERROR |
| `cancelled` | SIGTERM. If `selected` was already seen, the run finishes as `delivered*` instead (§7.6). | per the markers | unchanged | per the markers | WARNING |
| `internal_error` | A bug | unknown | unchanged, or +1 after RECORD | a committed intent stays as quarantine | ERROR with traceback |
| watchdog termination | Hard cap reached | unknown | unchanged, or +1 after RECORD | a committed intent stays as quarantine | ERROR, one line |

**Exit codes.** Every classified outcome exits 0. `internal_error` exits 70 and watchdog termination exits 71. The documentation tells users to keep the app Watchdog off (Q-07).

**Classification when nothing was delivered.** The first rule that matches wins.

1. **`source_failed`** if any of these holds:
   - discovery ended because of a provider or transport error: connect, TLS, DNS, the request's own timeout, HTTP 5xx, a 403/429 stop (§7.4), or an unexpected format;
   - any probe during SELECT, or any attempt, failed at the transport level. This includes any non-success status other than 404 or 410, and a download over the byte cap or the declared `Content-Length`;
   - the content window (§7.2) expired before the provider returned any candidate at all.

   A request cut off by its *phase deadline*, rather than by its own request timeout, counts as the deadline being reached.
2. **`image_failed`** if any attempt failed in processing: decode, render, encode, or a worker crash, timeout, or memory limit.
3. **`no_match`** otherwise. This covers:
   - an empty result;
   - every candidate already excluded;
   - candidates evaluated and rejected;
   - limits reached after candidates were returned;
   - every attempt answered with HTTP 404 or 410, or failing verification.

   The hints are "filters too restrictive", "nothing new left for these filters", and "search limits reached".

   *Amended at the Phase 4 gate (D-157).* "Nothing new left" also applies when nothing was seen because the adapter skipped pages whose works were all sent already (exhausted-page hints).

### 4.3 Concurrency model

- **Run thread.** One thread runs the whole run.
- **Watchdog thread.** It is armed at `T + 10 s` (130 s by default). When it fires it:
  1. kills the active worker's process group with SIGKILL;
  2. removes the workspace, best-effort;
  3. logs one line;
  4. calls `os._exit(71)`.
- **Workers.** At most one runs at a time, in its own process group. Each sets `PR_SET_PDEATHSIG` *after* dropping privileges (§11.3).
  *Amended at the Phase 5 gate (D-163).* Each worker also runs a lifeline thread that ends it as soon as the parent is gone (macOS has no parent-death signal), and sets `RLIMIT_NPROC` 0 last, so nothing it starts can outlive it. After every task, on every path, the worker's group and the worker are killed and the worker is reaped (waiting at most 2 s) before the executor returns.
- **DNS.** Each lookup runs in a fresh daemon thread, joined with a clamped timeout. The number of such threads is bounded by the request allowances.

There is no `asyncio` and no concurrent provider requests (D-106).

*Amended at the Phase 6 gate (D-166).* The entry point builds **one** process executor, which the runner, the local inspection, the Samsung adapter, and the watchdog share. Worker starts are shielded: a stop request waits until a start is complete. The runner arms the watchdog with its own `RunBudget`; when the watchdog fires, it emits the only summary line, and the entry point waits for its exit (71) instead of returning an exit code. On Linux the app refuses to run unless the isolation is enforced (the parent is root, and every worker drops to 65534 with every limit and the parent-death signal); it then ends as `internal_error` with exit code 70, before it contacts anything.

---

## 5. Component boundaries

The package name follows the accepted provisional identifier `frame_gallery` (D-138).

| Component | Responsibility | Depends on | Must not |
| --- | --- | --- | --- |
| `app` | Run orchestration; outcomes; workspace; lock; SIGTERM handling | ports | Import third-party libraries |
| `config` | Options; IPv4 validation; filter vocabularies and the capability matrix | stdlib | Perform network I/O |
| `ha` | Helper reads and optional fixed timer completion (D-176) | `net.transport`, `budget` | Arbitrary state/configuration/service writes; token sent outside container networks |
| `budget` | Clock, deadlines, allowances, phase calculator, watchdog | stdlib | Contain domain logic |
| `net` | Guarded gateway | `urllib3`, `certifi` | Serve the television or any non-policy host |
| `providers` | Contract; `local_media`, `aic`, `cma` adapters | `net`, `store.cache`, `isolation` | Decide eligibility |
| `selection` | Exclusions, classification, ranking, shortlist | provider contract, `store.history`, `store.upload_ledger`, `budget` | Perform network I/O |
| `imaging` | Worker-side inspect and prepare tasks; stdlib JPEG header validator for the parent | Pillow (worker only) | Run in the parent |
| `tv` | Port; Samsung worker task; token store | `samsungtvws` (worker only) | Be used except through the port |
| `store` | Atomic primitive, history, upload ledger, cache, workspace, preview, run records | stdlib | Know about providers or the television |
| `isolation` | Executor seam: in-process first, then process-based (spawn, rlimits, privilege drop, bytes channel) | stdlib | Unpickle child output |
| `logs` | Parent and worker logging, redaction, summary line | stdlib | Emit bodies, headers, or query strings |

Third-party imports are confined to the `imaging` and `tv` worker tasks and to `net.transport`. An import-boundary check enforces this (D-107). "stdlib" in the table means "no third-party packages"; the permitted internal dependencies that Phase 2 added (for example `budget.watchdog` using `logs.summary`) are recorded in D-141.

*Amended at the Phase 6 gate (D-166).* `__main__` is the composition root, and the only module that imports the real network transport and the process executor. New modules: `app/networks.py` (the container's networks, from the kernel's IPv4 route table) and `store/options_file.py` (the options file).

*Amended at the Phase 5 gate (D-162, D-163).* New modules: `tv/contract.py`, `tv/samsung.py`, `tv/samsung_task.py`, and `tv/token_store.py`; `isolation/framing.py`, `isolation/launch.py`, `isolation/process.py`, `isolation/bootstrap.py`, and `isolation/worker_main.py`. New internal dependencies: `tv.contract`, `tv.samsung`, and `tv.samsung_task` use `isolation.executor`; `tv.samsung`, `tv.samsung_task`, and `tv.token_store` use `logs.redact`, and `tv.samsung` also `logs.summary`; `tv.token_store` uses `store.atomic`; `tv.samsung_task` uses `imaging.contract`; `isolation.bootstrap` uses `logs.redact`; `isolation.process` uses `budget.clock` and `logs.summary`; `isolation.launch` names the worker task modules only as strings. There is no cycle. Besides `net.transport`, `tv/samsung_task.py` imports `socket`, only for its connect guard (amends D-147). `subprocess` and `select` are allowed only in `isolation/process.py`, and `ctypes` only in the bootstrap.

*Amended at the Phase 4 gate (D-153, D-154, D-155, D-156, D-158).* `store` also uses `selection.exclusion` (the `ExclusionSet` value type), `imaging.contract` (`DeliveryArtifact`), and `budget`; it still knows nothing about providers or the television. The direction is the reverse of the `selection` row above: `selection` imports no `store` module, and `store.state` builds the `ExclusionSet` that `selection.exclusion` defines, so there is no cycle. `providers.cache` imports its value type from `store.cache`, as the table lists. The shared top-level modules are now `domain`, `errors`, `randomness`, and `fingerprint` (the D-118 fingerprint); `WorkspacePaths` lives in `domain`, and `PublishError` in `errors`.

---

## 6. Data flow

```text
options.json ─► Options ─► FilterSet(static) ─► ha.resolve_overrides ─► FilterSet(effective + provenance + ignored_filters)
      │
      ▼
providers[source].iter_candidates ──lazy──► Candidate(qualified_id, rights_basis, attribution, dims?)
      │
      ▼
selection.shortlist(): exclude(history ∪ ledger.uploaded ∪ ledger.uncertain) → dims → upscale/shape → strict / first-eligible / fallback → ≤ 2
      │
      ▼  per shortlisted candidate, inside the 60 s content window:
gateway.download(rendition) ─► in/source.bin ─► isolation.run("prepare") ─► out/delivery.jpg ─► parent validation + SHA-256
      │
      ▼
PRE-STAGE: history.prestage(id)  ·  ledger.commit(id, "uncertain")        ← write-ahead upload intent
      │
      ▼
isolation.run("deliver") ─► connected → upload_started → uploaded(content_id) ─► ledger.commit(id, "uploaded") → selected
      │
      ▼  only if selected:
history.commit() ─► preview.publish(bytes, sha256) ─► records.current(attribution, fingerprints)
      │
      ▼
records.last_run(outcome, ignored_filters, stats) ─► cleanup ─► summary line ─► exit code
```

One file and its parent-computed SHA-256 serve as the television payload, the preview, and the recorded fingerprint (acceptance item `D8`).

---

## 7. Deadlines, budgets, and cancellation

### 7.1 Primitives

- An injected `Clock`.
- `Deadline`, with `remaining`, `expired`, `check`, `child`, and `clamp`.
- `Allowance` counters.
- A **phase calculator**. Each phase receives `child(min(budget, remaining − Σ later reserves))`. An early phase can never use a later phase's reserve. Unused time is never added to a later phase's cap; it only ends the run earlier. The one exception is inside the content window, where unused discovery time passes to the attempts (§7.2).

### 7.2 Budget decomposition (normative; D-114)

**Phase budgets** (default total `T` = **120 s**):

| Phase | Budget | Notes |
| --- | --- | --- |
| CONFIGURE + RESOLVE_FILTERS | **10 s** | Options, lock, sweep, and IPv4 validation (no DNS). Up to 4 helper reads of ≤ 3 s each, all within the window. |
| Content window: SELECT + ATTEMPT + PRE-STAGE | **60 s** | See the breakdown below. |
| DELIVER | **40 s** | Worker start; connect ≤ 5 s; pairing wait ≤ 20 s (first run only); upload and select in the remainder, guarded by the upload allowance (§12.1). |
| FINISH (reserved) | **10 s** | RECORD, PUBLISH, run records, cleanup. |
| **Total `T`** | **120 s** | The sum of the phases. A unit test asserts it. |
| Shutdown allowance | 10 s | The watchdog fires at 130 s (acceptance item `C5`). |

*Amended at the Phase 5 gate (D-162).* In DELIVER, "connect ≤ 5 s" bounds each TCP connect. The pairing wait is one deadline per connection attempt, `min(20 s, time left − 15 s)`, which also ends the waits for the TV's first messages. The kill timer is the only total bound of the upload and the selection.

**Content window breakdown:**

- **Discovery** ends at most 30 s into the window. Unused discovery time rolls over to the attempts.
- **Attempts** share the rest. Per attempt, the download gets ≤ 20 s and preparation ≤ 15 s, each clamped. A second attempt starts only if time remains.
- The **last 2 s** of the window are reserved for PRE-STAGE, or for the FINISH of a run with nothing to deliver. `no_match`, `source_failed`, and `image_failed` therefore exit by **70 s** (acceptance item `C11`).

**Allowances and per-request limits:**

| Limit | Value |
| --- | --- |
| Shortlist size (full downloads) | 2 |
| Candidates evaluated after exclusion | 150 |
| Provider metadata requests | 15 |
| Remote dimension requests ("probes") | 30 (Q-20, resolved) |
| Local directory entries | 20 000, depth ≤ 4 |
| Local header inspections (a separate allowance) | 300 |
| Per-request totals | metadata 10 s, probe 5 s, download 20 s, helper 3 s; each clamped to its phase and the total |
| Connect timeout | ≤ 5 s per address, clamped |
| Read timeout | ≤ 10 s between bytes, re-clamped before every receive |
| DNS | ≤ 3 s per host, clamped |
| Worker `RLIMIT_AS` (virtual memory) | image 1 GiB; television 512 MiB |
| Dashboard timer indicator (§16.3) | `T` + 30 s = **150 s** |

There is no user-facing time option in the beta. An advanced total-deadline option may be added later, validated within a safe range, with its phases scaled proportionally. The standard dashboard instructions use the 120 s default.

### 7.3 Television reserve rule

DELIVER's 40 s and FINISH's 10 s are reserved from the start of the run. PRE-STAGE re-checks the reserve **before** committing any upload intent. If the check fails, the outcome is `deadline_exceeded`: the television is untouched, no intent exists yet, and the pre-staged history file is discarded.

### 7.4 Retry and pacing policy (D-115)

| Operation | Retries | Conditions |
| --- | --- | --- |
| Metadata GET | ≤ 1 | Only for a connect error, HTTP 502/503/504, or HTTP 429 with a `Retry-After` (seconds or HTTP-date) of ≤ 5 s. The wait is `max(Retry-After, 1 s)` plus jitter, and the retry is skipped if the wait exceeds the deadline. |
| HTTP 403, or HTTP 429 without the single permitted retry, from any host of the provider | 0 | **403/429 stop**: no further request to any host of that provider in this run. After a retried 429, later requests wait for `Retry-After`. |
| Probe or download | 0 | Move to the next candidate. |
| Helper read | 0 | Fall back to the static value. |
| Television connect | ≤ 1 | Only before `upload_started`, and never after a pairing timeout. |
| Television upload or select | 0 | Never repeated. |

**Pacing.** A `min_interval` of 1 s applies to the Art Institute, as its published guidance asks, and to Cleveland, which publishes no limit and is self-throttled.

### 7.5 Network timing guarantees

- DNS resolution runs once per request, in a daemon thread with `clamp(3 s)`.
- Addresses are tried one at a time, each clamped.
- Body reads are partial, and the timeout is re-clamped before every receive, so a slow-drip response ends at its request total.
- No network operation outlives its phase deadline, except an abandoned DNS thread, which does not delay the run.
- Anything inside a worker is bounded by its kill timer.

### 7.6 Stop requests (SIGTERM)

The SIGTERM handler raises `Cancelled` in the main thread, as PEP 475 requires for interrupting blocking calls.

| When | Handling |
| --- | --- |
| Before DELIVER | `cancelled`; the television is untouched; any committed intent is removed. |
| During DELIVER | Stop requests are deferred for the whole call; the adapter learns of the request, kills the worker group, and returns the markers read (D-141). After `selected`, the run continues to RECORD. After `uploaded`, the ledger holds `uploaded`. After `upload_started`, the intent remains as quarantine. Earlier than that, the intent is removed. |
| After `selected` | SIGTERM is deferred until RECORD's rename is `fsync`ed. PUBLISH may be skipped, which gives `delivered_with_warnings`. |

The stop timeout is 20 s (§17.1).

---

## 8. Candidate selection

### 8.1 Shape and quality classification (D-116)

- `r = w/h` is the ratio of the deliverable rendition after EXIF orientation.
- `s` is the fit mode's scale factor on the 3840 × 2160 canvas.

| Class | Rule (D-116, accepted) |
| --- | --- |
| portrait | `r < 0.95` |
| square | `0.95 ≤ r ≤ 1/0.95` |
| landscape | `r > 1/0.95` |
| near-16:9 (strict) | `abs(ln(r/(16/9))) ≤ ln(1.01)` (about 1.760–1.796); may be revisited after Phase 8 visual testing |
| too small | `s > 2.5` |

In `contain` mode, an Art Institute rendition 1686 px wide and at least 16:9 is upscaled ≈ 2.28×, and a Cleveland 3400 px print ≈ 1.13×. Narrower works are limited by height and upscaled less.

### 8.2 Discovery, shortlist, and attempts

```text
excluded ← history ∪ ledger.uploaded ∪ ledger.uncertain(unexpired)
shortlist ← [];  fallbacks ← top-2 heap keyed by abs(ln(r/(16/9)))
for candidate in provider.iter_candidates(filters, ctx):
    stop if discovery deadline expired
    skip if candidate.qualified_id in excluded                      # not charged to the candidate allowance
    stop if candidate allowance exhausted
    skip if candidate.rights_basis not allowed (D-134)
    dims ← candidate.dims  or  inspect/probe (allowance-counted)
    skip if too small;  skip if landscape_only and shape ≠ landscape
    if not strict_tv_format or near_16_9(dims): shortlist.append(candidate); stop at 2
    elif fallback_permitted: fallbacks.offer(candidate)
end
if strict_tv_format and fallback_permitted: fill the shortlist from fallbacks, best first
```

- **Single pass.** One discovery pass of at most 30 s; the attempts then work through the shortlist in order.
- **Verification.** The prepare worker reports the real dimensions first. A rendition that violates the reason it was chosen is rejected, and the next candidate is tried.
- **Fallback (D-117, accepted).** Fallback is allowed only with `landscape_only` and `contain`, and a fallback image is never cropped. There is **no fallback in `cover` mode**.
- **Provider error.** A non-403/429 error mid-discovery ends discovery, but the shortlisted candidates are still attempted. After a 403/429 stop, there are no further requests, and the outcome is `source_failed`.
- **Randomness.** All random choices use the injected random source.

### 8.3 Probes and inspections

- **Probes.** A *probe* is one remote request made only to learn an image's dimensions. Probes are capped at 30 per run (Q-20, resolved). No beta source needs them: the Art Institute documents native image sizes in its Images resource, and Cleveland documents the size of its print JPEG (§9.5, §9.6). The allowance is still enforced and tested with a counting fake gateway (acceptance item `C4`).
- **Local header inspections** run in the isolated `inspect` worker, in batches of at most 50, against their own allowance of 300.

*Amended at the Phase 6 gate (D-169).* A batch holds at most **16** files, because each descriptor counts against the worker's `RLIMIT_NOFILE` of 32. The parent opens each library file read-only, without following a link, and passes the descriptor only if the file still has the identity the scan saw; the worker never opens a library path. Each file still has 2 s, and a file whose worker stops, crashes, or times out fails alone: the files after it go to a new worker. Selection charges each candidate to the allowance when it arrives, lets it wait until 16 are waiting, a candidate with known dimensions arrives, or the pass ends, and ranks the batch in the original order, so the shortlist is the one a file-by-file pass would build.

---

## 9. Provider adapters

### 9.1 Contract, naming, and rights

```text
Provider
  key: str                                     # persistent history/ledger prefix
  capabilities() -> Capabilities               # per filter dimension; dims-in-metadata; host policy; allowed rights bases
  iter_candidates(filters, ctx) -> Iterator[Candidate]
  probe_ref(candidate) -> ImageRef | None
  full_ref(candidate) -> ImageRef

Candidate
  provider_key, native_id, qualified_id        # "<key>:<native_id>"; native_id fullmatches a provider pattern; ≤ 200 chars
  rights_basis: RightsBasis                    # plus the metadata field it came from
  attribution: title, creator, date_text, credit_line, detail_url
  dims: Size | None                            # of the rendition full_ref delivers
```

| `source` option value | Key (history/ledger prefix) | Module | Allowed rights basis |
| --- | --- | --- | --- |
| `local_media` | `local` | `providers.local_media` | `USER_SUPPLIED` |
| `art_institute_chicago` | `aic` | `providers.aic` | `CC0` (`is_public_domain`) |
| `cleveland_museum_of_art` | `cma` | `providers.cma` | `CC0` (`share_license_status == "CC0"`) |

**Contract rules** (shared suite, §20.1):

- candidates are lazy;
- all traffic goes through the gateway;
- identifiers are stable and never collide across providers;
- every candidate carries an allowed rights basis (D-134);
- filter capabilities are reported per §9.2;
- adapters write only to their own cache namespace.

*Amended at the Phase 4 gate (D-157).* The discovery context also carries `is_excluded_for_good` (history and `uploaded` works, never quarantined ones) and a small `notes` record. Adapters use them only for exhausted-page hints: they still yield every candidate, and selection decides.

### 9.2 Filter model and capability matrix (D-124)

There are four distinct dimensions:

1. **Source/museum.** The `source` option selects the provider. A department is **never** called a museum.
2. **Department/collection.** A department within the selected museum. Values are namespaced `aic_…` or `cma_…`.
3. **Style/period.** A style (movement) key `style_…`, or a period (date range) key `period_…`.
4. **Colour.** The dominant colour.

Landscape-only, strict near-16:9, and fit mode apply to every source.

| Filter | Local media | Art Institute of Chicago | Cleveland Museum of Art |
| --- | --- | --- | --- |
| Department/collection | unsupported | **unsupported in the beta** (the field is documented, its values are not; D-146, Q-25) | **supported** (documented `department` parameter; a curated subset of the 21 documented values, §15.2) |
| Style | unsupported | **unsupported in the beta** (the field is documented, its values are not; D-146, Q-25) | **unsupported** (no documented style field) |
| Period | unsupported | **supported** (`date_start`) | **supported** (`created_after`/`created_before`, in years; the exact range is enforced on `creation_date_earliest`) |
| Colour | unsupported | **unsupported in the beta** (the members of the documented colour object are not documented; D-146, Q-25) | **unsupported in the beta** (no documented colour field; local analysis deferred, Q-24) |
| Landscape-only, strict 16:9, fit | supported | supported | supported |

*Amended at the start of Phase 3 (D-146).* The re-read documentation names the Art Institute's department, style, and colour fields, but not their values or members. Under the user's Q-14 instruction, nothing undocumented is used, so these three filters are unsupported for the Art Institute in the beta. The Phase 3 gate confirmed this: Q-25 is resolved with option (a), so no source offers a colour filter in the first beta.

**Visible reporting, never silent.** Some filters cannot apply to the selected source: an unsupported dimension, or a department of another source. For this run such a filter is ignored and reported in three places:

- one WARNING naming the filter and the reason;
- `ignored_filters=…` in the summary line;
- `ignored_filters` in `last_run.json`.

The option descriptions name the sources each filter applies to (acceptance item `B8`).

**Helper values** follow one rule, with a unit test for each case (acceptance items `B5` and `B8`):

- A value that normalizes to no vocabulary key is invalid. It falls back to the static value with one WARNING, as the specification requires.
- A known key that does not apply to the selected source (for example, a `cma_…` department while the source is AIC) overrides the static value. It is then ignored and reported exactly like a static value.

### 9.3 Local media (`local`)

- **Library.** The fixed, documented folder `/media/frame_gallery/library`. The app creates it at start if it is missing. Users add images through Home Assistant's media browser; whether uploading into this subfolder works is verified in Phase 8 (R-21). The `no_match` hint for an empty library names this location.
- **Enumeration.** An iterative scan, depth ≤ 4 and at most 20 000 entries:
  - hidden entries are skipped, and symbolic links are never followed;
  - each file is opened with `O_NOFOLLOW` and checked with `fstat`: it must be a regular file of ≤ 40 MiB;
  - only `.jpg`, `.jpeg`, and `.png` are accepted;
  - the order is shuffled.
- **Warnings.** Unsupported extensions, oversize files, unreadable files, and inspection failures are summarized in **one aggregated WARNING**. It gives counts per reason and up to 5 sanitized example paths.
- **Identifier.** `local:fp:<sha256(size ‖ first 64 KiB ‖ last 64 KiB)>` (D-118).
- **Preview exclusion** (acceptance item `F7`) uses three guards:
  1. the preview directory is excluded by real path;
  2. the library folder cannot contain the preview directory;
  3. the fingerprints of the last 10 previews, kept in `current.json`, are skipped.
- **Rights basis.** `USER_SUPPLIED`.
- **Filters.** Only landscape-only, strict 16:9, and fit apply. A valid department or period key is ignored and reported as unsupported (§9.2, B8). A value that matches no key, label, or alias, and is not a no-filter term, is invalid (§15.1, B5).

*Amended at the Phase 6 gate (D-169).* The aggregated WARNING is logged once selection is done, through `ProviderBinding.after_discovery`, so that the files of the last inspection batch count too.

### 9.4 Provider access findings (Phase 1 research)

`LEGAL_BOUNDARIES.md` requires connectors to "respect applicable access terms, request limits, and technical restrictions".

The research read policy pages, `robots.txt` files, and official API documentation. It also used one Microsoft Q&A answer, cited as a non-documentation source, and search snippets where a page blocked automated readers. It called no endpoint.

| Source | Documented API? | Access rules found | Image rights | Beta status |
| --- | --- | --- | --- | --- |
| **Art Institute of Chicago** | **Yes**, no key | 60 requests per minute per IP; courtesy `AIC-User-Agent`; images about 1 s apart | Public-domain images are CC0 | **In the beta** (§9.5) |
| **Cleveland Museum of Art** | **Yes**, no key today; the terms reserve future keys | No numeric limit; the terms reserve transaction limits and log IP addresses | CC0 images only for `share_license_status` "CC0" | **In the beta** (§9.6) |
| **Google Arts & Culture** | **No**; only partner ingestion | `robots.txt` allows public HTML and disallows `/api/*`. The Terms prohibit automated access against `robots.txt`, bypassing protective measures, and using the service to violate IP rights. | Partners hold the rights | **Excluded** (§9.7) |
| **Bing daily imagery** | **No**; the Bing Search APIs were retired 2025-08-11 | The `*` group disallows the image path `/th?`; the archive rule is spelled `/HpImageArchive.aspx` | Services Agreement: non-commercial personal use only | **Excluded** (§9.8) |
| **Museum of Modern Art, Musée d'Orsay** | No open API found | — | Agency licensing, or non-commercial use only | Not offered; aggregator coverage not yet checked |
| **Europeana, Rijksmuseum, The Met** | Yes, with conditions | Various | Per item | Later (§9.9) |

### 9.5 Art Institute of Chicago (`aic`) (D-132, D-146)

Re-verified against the live documentation on 2026-09-27 (D-146). No endpoint was called.

- **Discovery.**
  - The documented `/api/v1/artworks/search` endpoint. The Elasticsearch query travels as minified JSON in the `params` GET parameter, which the documentation recommends for production use.
  - Every query requires the term `is_public_domain = true` and the presence of `image_id`.
  - `fields` is limited to `id`, `is_public_domain`, `title`, `artist_display`, `date_display`, `date_start`, `image_id`, and `credit_line`.
  - Every record must also have `is_public_domain == true` and an `image_id` that matches its pattern; otherwise it is skipped.
  - **Count.** One request with `limit = 0` reads `pagination.total`, following a documented example.
  - **Pages (Phase 8 correction, D-174).** `limit = 50`. Each run wraps the filter query in the documented Elasticsearch `function_score` / `random_score`, with a fresh injected integer seed, `field = _seq_no`, and `boost_mode = replace`. Read sequentially at most pages 1–7 of that ordering, never deep pages of the default catalogue. Green probes of pages 199 and 200 returned HTTP 403, "Invalid number of results", despite the documented 10 000-result window; its actual boundary was not established. A fresh shallow random ordering avoids that boundary without permanently restricting discovery to a fixed catalogue prefix.
- **Dimensions.** After each page, one batched request to the documented Images resource, `GET /api/v1/images?ids=<the page's image ids>&fields=id,width,height`, reads the native sizes ("Native width/height of the image"). It counts as a metadata request.
  - The artwork's `image_id` is taken as the image record's `id`, since the documentation uses that identifier for the image in both places. The worker's check of the real dimensions (§8.2) remains the safety net.
  - The artwork's `thumbnail` object is not used, because its members are undocumented.
  - A record without a matching image record carries no dimensions and is skipped (`dims_unavailable`). The adapter has no probe.
- **Requests per run.** One count, then two per page. A typical run makes 3 metadata requests, and never more than 15 (the metadata allowance). Three pages already cover the 150-candidate allowance.
- **Filters.** Only the period (§9.2), as a `range` on the documented numeric `date_start`, which is also checked on every record. Departments, styles, and colours are unsupported in the beta (D-146, Q-25).
- **Rendition.** IIIF `https://www.artic.edu/iiif/2/<image_id>/full/1686,/0/default.jpg`, the largest documented public-domain size. The 4K canvas is the stated need for it.
  - Only images at least 1686 px wide are offered, because the documentation does not say whether the IIIF server upscales.
  - The rendition measures `1686 × round(1686 · h / w)`.
  - An HTTP 404 moves on to the next candidate.
- **Identifiers.** `image_id` must `fullmatch` the UUID form of the documentation's examples and is percent-encoded. Artworks are recorded as `aic:<numeric id>`.
- **Courtesy.**
  - `AIC-User-Agent: FrameGallery/<version> (<project contact>)`, as amended in D-119; never user data.
  - Requests are spaced 1 s apart, the documented scraping rate, well within the documented 60 requests per minute.
  - At most 15 metadata requests per run.
- **Cache.** Counts per filter signature for 1 day. *Amended in Phase 8 (D-174):* AIC no longer reads or writes exhausted-page hints, because page membership changes with the seed. Existing hint entries are left intact and expire normally; sent history and the upload ledger are unchanged. Cleveland's hints remain in use. The persistent cache arrived in Phase 4 (§13.4).
- **Attribution.** "Artist. Title, Date. The Art Institute of Chicago."
- **Hosts.** Exactly `api.artic.edu` and `www.artic.edu`.

### 9.6 Cleveland Museum of Art (`cma`) (D-136, D-146)

This section is based on the documentation at `openaccess-api.clevelandart.org` and the museum's open-access and terms pages. It was re-verified against the live documentation on 2026-09-27 (D-146, R-20); the newest entry in the documentation's release history is version 4.0.3 (2026-07-09). No endpoint was called.

- **Endpoint.** `GET /api/artworks/`, with `?cc0` and `has_image=1` on **every** request.
  - `cc0` is a valueless presence flag: "Filters by works that have share license cc0".
  - `has_image=1` returns only works that have a web image asset.
- **Record check.** Every record must also have `share_license_status == "CC0"` and a present `images.print`, otherwise it is skipped. CC0 images exist only for CC0-status records.
- **Filters.**
  - `department` takes exact values from the documented list of 21 (Appendix B of the documentation, re-checked verbatim), URL-encoded. The vocabulary offers a curated subset (§15.2). "Performing Arts, Music, & Film" is not offered, because the documentation does not say how a value with commas is parsed.
  - The period filter uses `created_after` and `created_before`: integer years, negative for BCE. The documentation says neither whether they are inclusive nor which date they compare. The adapter therefore widens each bound by one year and enforces the exact range on the documented `creation_date_earliest` of every record.
  - `type` (for example Painting) may be used for internal narrowing, but it is not a user filter.
  - Style and colour are unsupported (§9.2).
- **Random selection.**
  1. A request with `limit=1` and minimal `fields` reads the documented `info.total`.
  2. A random `skip` in `[0, total)`, sampled without replacement, fetches a page with `limit` ≤ 25.

  Every request sets `limit` explicitly, because the documented default is the maximum of 1000 records.

  The undocumented `randomize` parameter, which appears only in the auto-generated OpenAPI file, is **not** used.
- **Fields requested.** `id`, `accession_number`, `title`, `creators`, `creation_date`, `creation_date_earliest`, `department`, `share_license_status`, `images`, `url`.
- **Rendition: the documented print JPEG only.** `images.print` is documented as a 3400 px long side, 300 dpi JPEG, with `url`, `width`, `height`, and `filesize`.
  - These fields are strings in the documentation example and are parsed defensively. They give the dimensions, so no probes are needed.
  - **The `full` TIFF is never requested.** A print URL that is not a `.jpg` on the policy host skips the candidate.
  - A 16:9 work is upscaled about 1.13×.
- **Hosts.** Exactly `openaccess-api.clevelandart.org` and `openaccess-cdn.clevelandart.org`. The second appears only in the documentation's example URLs (re-checked on 2026-09-27). A rendition on any other host is skipped with a counted warning.
- **Identifier.** `cma:<id>`, where `id` is the documented "ID in AthenaCCMS" (an integer). The accession number is kept as metadata. Neither is documented as permanent (R-22).
- **Pacing and cache.**
  - Requests are spaced 1 s apart.
  - At most 15 metadata requests per run.
  - Totals per filter signature are cached for 1 day, and exhausted-skip hints for 7 days. The API documentation says the data updates daily, while the open-access page says weekly. The 1-day TTL suits either.
- **Rights and attribution.** CC0 works need no attribution. A shortened form of the museum's suggested citation is used as a courtesy: "Artist. Title. Date. The Cleveland Museum of Art." CMA trademarks are never used, and no endorsement is implied.
- **Terms.** The API may later require keys or transaction limits. The design leaves room for an optional key (a `password` option), and treats HTTP 401 or 403 as a 403/429 stop.

### 9.7 Google Arts & Culture (`gac`): excluded from the beta

There is no documented API (§9.4). The specification now lists this source under *Researched and excluded sources*. It may be reconsidered only if a stable, documented API appears, and then only through a new decision and adapter milestone. Undocumented or `robots.txt`-incompatible access is never implemented (Q-01, resolved).

### 9.8 Bing daily imagery (`bing`): excluded

Bing has no documented API. Its image path is disallowed for general crawlers, and the Services Agreement restricts the photos (Q-17, resolved). Not planned.

### 9.9 Future providers

A new provider needs:

- an adapter with a capability declaration and a rights-basis allowlist;
- a vocabulary mapping;
- a host policy with pacing;
- synthesized fixtures.

It needs no change to `selection`, `imaging`, `tv`, or `store`. The candidates are Europeana (if its key model is resolved), Rijksmuseum, and The Met (after approval to read its GitHub-hosted documentation).

---

## 10. Guarded network access (D-108, D-131)

There is one gateway, built on `urllib3` with its automatic retries and redirects disabled.

**Host policy.** Each provider declares:

- **Hosts.** Exact names; a suffix may match only at a label boundary, after IDNA normalization.
- **URLs.** `https` on port 443, with no user-info and no IP-literal hosts.
- **Content types.** Metadata `application/json`; images `image/jpeg` or `image/png`.
- **Byte caps** on decoded bytes: metadata 2 MiB, probe 256 KiB, image 40 MiB.
- **`min_interval`.**
- **Identifier patterns** for any value placed into a URL, checked with `fullmatch` and then percent-encoded.

**Resolution and connection.**

1. Resolve the host once.
2. Require **every** address to be globally routable, with mapped forms unwrapped. Loopback, private, link-local, CGNAT, multicast, reserved, and unspecified addresses all fail.
3. Connect to the validated IP, using the hostname for SNI, the certificate check, and `Host`.
4. Check `getpeername()` before sending.

**TLS.** `CERT_REQUIRED`, TLS ≥ 1.2, and the explicit `certifi` bundle. `certifi` is a direct dependency from Phase 3.

**Redirects.** At most 3, each re-validated.

**Encoding.** Images use identity encoding. Metadata may have one gzip layer, with the cap applied after decoding. A `Content-Length` over the cap is rejected before the body is read.

**Hygiene.** No cookies. Environment proxies and credential files are ignored (§17.5). The User-Agent is `FrameGallery/<version> (contact: <project contact>)`, plus any courtesy headers the provider asks for (D-119 as amended: no project URL until a public one exists; tests use a placeholder contact).

**Logging.** Host, path without the query string, status, bytes, and duration. Never bodies or header values.

---

## 11. Image preparation

### 11.1 Worker-side pipeline

Steps 2 to 9 run only in the `prepare` worker.

1. **Sniff** (in the parent). The magic bytes must match JPEG or PNG and the declared content type.
2. **Pre-scan, then open** lazily, with `formats=("JPEG", "PNG")` (a JPEG opened as MPO counts as JPEG, frame 0 only). The bounded header pre-scan of D-144 runs first: it caps marker segments, chunks, and header bytes before Pillow parses them. Before decoding, enforce:
   - width and height ≤ 20 000 px each;
   - ≤ 64 MP for JPEG and ≤ 40 MP for PNG (D-121).

   Report the real dimensions and orientation for verification.
3. **Decode with reduction.** JPEG uses the smallest DCT scale that still covers the fitted size, with axes swapped for EXIF orientations 5–8. Multi-frame images use the first frame only.
4. **Pre-normalize.** Palette and bilevel images become RGB or RGBA. Deeper modes are scaled to 8-bit or rejected.
5. **Crop, then resize.** `cover` crops in source coordinates before resizing. From here on, every buffer is at most canvas-sized.
6. **Orient** the image in place and drop all metadata.
7. **Colour.** Convert ICC to sRGB (D-122), convert CMYK, and composite alpha over `background_color`.
8. **Compose.** `contain` places the image on the canvas.
9. **Encode** a baseline JPEG at quality 90 with no EXIF. If the result exceeds 15 MiB, encode once more at quality 85 (Q-05).

**Peak memory.**

- It is roughly: baseline, plus the decoded source, plus one full-resolution conversion or crop copy, plus a reduced intermediate, plus one canvas copy (≤ 33 MiB), plus encoder buffers.
- The worst legal cases are a 40 MP RGBA or palette PNG (≈ 450 MiB) and a 64 MP CMYK JPEG in `cover` mode (≈ 550 MiB).
- The beta renditions are much smaller: 1686 px (AIC) and 3400 px (CMA).
- The worker ceiling is 1 GiB of virtual address space (`RLIMIT_AS`). The worst cases are tested under that real limit, and R-09 records the measured peak.

*Amended at the Phase 5 gate (R-09).* The measurement on the development host, without `RLIMIT_AS`, does not confirm the estimate: progressive JPEGs need the most, up to 839 MiB resident for a 64 MP progressive CMYK panorama in `cover`. The 1 GiB limit stays. Any change is decided only from the measurement under the real limit in the Linux container (Phase 6), which must pass before any live test on the Green (D-165).

*Amended at the Phase 6 gate (D-170).* Measured under the real 1 GiB `RLIMIT_AS` in the `aarch64` container, as root with workers at 65534: all 13 worst cases succeed; the heaviest, the 64 MP progressive CMYK panorama in `cover`, peaks at 766 MiB of address space (754 MiB resident) in 1.4 s. **The 1 GiB limit stays.** Under Rosetta (`amd64` on the development host) every process carries about 278 MiB more address space, and that case fails; Pillow reports the failed allocation as a broken data stream, so it counts as `decode` (a known limitation). The native `amd64` measurement is mandatory before an `amd64` version is published, at the latest in Phase 9; Phase 8 repeats the measurement on the Green.

### 11.2 Fit geometry (pure, table-tested)

- **`contain`** (default): `s = min(W/w, H/h)`, centred on `background_color` (`#000000`). Every source pixel is present.
- **`cover`** (opt-in): `s = max(W/w, H/h)`, with the centre crop taken in source coordinates. It crops one axis only, and only by the overflow.
- Scale factors are always uniform, so the image is never stretched.

### 11.3 Isolation, privilege, and hand-off (D-109)

**Worker bootstrap.** These steps run first in each worker's entry function. `__main__` has no import-time side effects.

1. `setgroups([])`, then change the group and user IDs to 65534. The parent has already created a read-only `in/` and a group-readable, setgid `out/`.
2. `PR_SET_PDEATHSIG(SIGKILL)`, set after step 1. The worker exits if `getppid()` has changed.
3. `umask 027`.
4. `RLIMIT_AS`: 1 GiB for the image worker, 512 MiB for the television worker. Both also get CPU limits.
5. Only the allowlisted environment is present.
6. Logging is configured before any third-party import.
7. Image worker only:
   - `MAX_IMAGE_PIXELS` is set to 64 MP;
   - decompression-bomb warnings are raised as errors;
   - only the allowed formats are opened;
   - the 40 MP PNG cap is an explicit header check.

If dropping privileges fails, the worker refuses to run (`internal_error`).

The `inspect` worker opens each library file itself with `O_NOFOLLOW` and `fstat`, and counts unreadable files in the aggregated warning.

A **bootstrap test** asserts every value from inside the child.

**Channel.**

- Results arrive as bytes only: `recv_bytes(maxlength = 64 KiB)`, then JSON parsing and schema validation.
- Pickle-based transports are never used.
- The parent chooses every path.

**Parent validation of `delivery.jpg`.** The parent opens it with `O_NOFOLLOW` and requires:

- a regular file of ≤ 15 MiB;
- a JPEG header whose dimensions equal the canvas.

It then computes the SHA-256 itself.

| Task | Input | Timeout (clamped) |
| --- | --- | --- |
| `inspect` | ≤ 50 local files | within discovery |
| `prepare` | one source file plus selection constraints | 15 s |
| `deliver` | see §12 | 40 s |

*Amended at the Phase 5 gate (D-163, D-164, D-165).*

- **Start.** Each task runs in a new worker, `python -I -S -B`, in its own process group, with `/` as its working directory, exactly the environment `PATH`, `LC_ALL=C.UTF-8`, and `TZ=UTC`, and six descriptors. The configuration on the command line holds no secret.
- **Bootstrap additions.** On Linux, dumpability 0 and no-new-privileges, then the parent-death signal, each read back, and empty capability sets. On every platform, a lifeline thread. Every limit is set as soft = hard, with `RLIMIT_NPROC` 0 last. The environment must be exactly the one above.
- **Handshake.** The worker's first message is a `ready` report of what it verified; the parent compares it with what it asked for before it sends the request. A worker that cannot be started, refuses to run, or reports values that do not match is an `IsolationFailure`: the run ends as `internal_error`, and no second candidate is tried.
- **Channel.** Frames are a 4-byte length and canonical JSON of at most 64 KiB plus 1 KiB of envelope; each body is held to 64 KiB, as in the in-process executor.
- **Workspace** (D-164). With a worker group, `frame-gallery/` and `run-*/` are 0710, `in/` 2750, and `out/` 2770, all in that group, and checked after creation. Downloads and local copies are 0640.
- **`inspect`.** From Phase 6, the parent opens each library file and passes the read-only descriptor to the worker where possible, and `inspect` runs in batches (§8.3).
- **Verification** (D-165). The root-only and Linux-only checks, and the worst-case measurement under the real `RLIMIT_AS`, run in the Phase 6 container. They must pass there, and they are mandatory before any live test on the Green.

*Amended at the Phase 6 gate (D-169, D-170).* `inspect` gets parent-opened, read-only descriptors (at most 16 per worker), never a path, so the worker at 65534 can measure every file the app can open: the limitation of D-164, that it could read only files readable by others, is resolved, and the `inspect` row of the table above holds at most 16 files. The Linux and root checks passed in the Phase 6 container on both architectures, and the measurement under the real `RLIMIT_AS` on `aarch64`, so the condition of D-165 is met.

**Implementation order (D-139).**

- **Phase 2:** the executor seam, with an in-process executor.
- **Phase 5:** the process executor, including the **complete bootstrap**: `setgroups`, user and group ID 65534, then `PR_SET_PDEATHSIG`, umask, rlimits, the bytes channel, markers, and the bootstrap test. Every later run, including the Phase 8 live runs, therefore decodes images unprivileged.
- **Phase 9:** enforce-mode AppArmor, and verification of the whole isolation design before release.

None of the final requirements is relaxed.

---

## 12. Television communication

### 12.1 Port and progress markers

```text
Television
  deliver(jpeg_path, tv_ipv4, token_seed_path, deadline) -> DeliveryResult
  markers (child → parent, bytes-only): connected · upload_started · uploaded(content_id) · selected
  DeliveryResult: {status: ok | unreachable | not_authorized | unsupported | refused | protocol | insufficient_time,
                   auth: unchanged | new_token | token_rejected, markers_seen}
```

The whole delivery is one coarse operation inside one worker.

*Amended at the Phase 5 gate (D-141, D-162).* The port is `deliver(request, on_marker)`. The request carries the IPv4 literal, the path of `delivery.jpg` and the parent's SHA-256 of it, the deadline, and a stop signal; it carries no token path. The worker receives the stored token in its request message, and reports a token the TV issues as a `token` event before `connected`, at most one per connection attempt. `uploaded` may come without a content ID, which still promotes the ledger entry. `insufficient_time` before `connected` gets no hint; after `connected`, it keeps "paired; start the app again".

- `content_id` must match a strict pattern of at most 64 characters.
- The parent classifies the result from the **last marker seen**.
- On the `uploaded` marker, the parent immediately promotes the ledger entry to `uploaded` (§13.6).
- **Marker ordering.** The worker writes `upload_started` to the channel, and waits for that send to return, **before** calling the library's upload. A fake-library test asserts the order. This makes a missing `upload_started` a proof that nothing was uploaded.
- **Upload allowance guard.** The worker sends `upload_started` and starts the upload only if enough DELIVER time remains for an upload-and-select allowance (proposed now, measured in Phase 8). If not, for example after a long first-run pairing, the worker returns `insufficient_time` before uploading and the intent is removed. The outcome is `deadline_exceeded`, with the hint "paired; start the app again".

### 12.2 Samsung adapter

- **Library.** `samsungtvws` 3.0.6 (LGPL-3.0, D-104), used only by the worker.
  - Samsung does not document Art Mode.
  - The adapter surface comes **only from inspecting the installed 3.0.6 distribution** (Q-15, resolved), without GitHub access.
  - The 2.7.2 README named `art().supported()`, `upload(data, file_type='JPEG')`, `select_image(content_id, show=…)`, and `get_artmode()`. Matte, client name, and constructor details are taken from the installed package.
- **Connection.**
  - The worker connects to the configured **IPv4 literal** (§15.4).
  - Port and TLS behaviour are recorded in Phase 5 (R-03).
  - The app starts **without `host_network`**. Phase 8 verifies Home Assistant Green-to-TV connectivity before any change is considered (Q-16).
- **User setup.** The documentation asks for:
  - Home Assistant and the TV on the same subnet;
  - *Access Notification Settings → First Time Only* on the TV;
  - a DHCP reservation for the TV's IPv4 address.
- **Token.**
  - The parent seeds the token file into the worker's `out/` directory.
  - On `new_token`, the parent installs the new token atomically with mode `0600`. On `token_rejected`, it deletes the token.
  - Only the current address's token is kept.
  - Tokens are excluded from backups through `backup_exclude: tv/**`. This is expected behaviour; Phase 8 inspects a backup to confirm it.
- **First run.** The prompt must be accepted within 20 s. Otherwise the outcome is `tv_not_authorized`, with the message *"Accept the connection prompt on your TV, then start the app again."*

*Amended at the Phase 5 gate (D-160, D-161, D-162).*

- **Library surface** (D-161): `SamsungTVArt` on port 8002, with `token_file=None` and the client name `frame_gallery` (D-138). Each connection attempt uses a new library object, and the connection of a failed attempt is dropped.
- **Token.** It travels in the worker's request and comes back as a `token` event; no token file is seeded into `out/`. The parent registers a new token with the redactor and installs it at once (mode 0600, atomically); it removes a rejected one.
- **TLS** to the TV is not verified, as the library does (R-03). Pinning is decided after the TV's certificate is observed in the supervised Phase 8 test.
- **Art API 0.97** is `unsupported` in the beta, because the library may upload the same image twice there.
- **Network.** A connect guard lets the worker reach only the TV's IPv4 literal, and bounds each TCP connect to 5 s.
- **Licence** (D-160): `samsungtvws` 3.0.6 under `LGPL-3.0`, treated as `LGPL-3.0-only`; it stays an unmodified, replaceable package.

### 12.3 Bounding

- The worker runs inside the 40 s DELIVER budget.
- On timer expiry, the worker group is killed and the outcome is classified from the markers.
- After `selected`, RECORD always runs.

### 12.4 Failure semantics and duplicate prevention (D-137)

| Last marker and result | Outcome | Television | Sent history | Upload ledger |
| --- | --- | --- | --- | --- |
| none, or `connected`; connection refused, timed out, host down, connection lost, kill timer, or `protocol` | `tv_unreachable` | unchanged | unchanged | intent **removed** |
| `connected`; token rejected or prompt not accepted | `tv_not_authorized` | unchanged | unchanged | intent removed |
| `connected`; art mode unsupported | `tv_rejected` | unchanged | unchanged | intent removed |
| `connected`; `insufficient_time` (upload allowance guard) | `deadline_exceeded` | unchanged | unchanged | intent removed |
| `upload_started`; connection lost, kill timer, or `protocol` | `tv_unreachable`: "the upload may have reached the TV" | may hold the upload | unchanged | intent **kept as `uncertain`** (quarantine: 30 days, Q-23) |
| `upload_started`; explicit upload refusal | `tv_rejected` | unchanged | unchanged | intent removed |
| `uploaded`; selection explicitly refused | `tv_rejected` | holds an undisplayed upload | unchanged | **`uploaded`**: never uploaded again (within the bounds, R-29) |
| `uploaded`; connection lost, kill timer, or `protocol` during selection | `tv_unreachable`: "stored on the TV and may be displayed" | holds the upload; may display it | unchanged | **`uploaded`**: never uploaded again (within the bounds, R-29) |
| process killed (SIGKILL, power loss) after PRE-STAGE | *(next run)* | unknown | unchanged | the committed intent remains `uncertain`, or `uploaded` if promoted, so the work is excluded |
| `selected` | `delivered*` | changed | +1 (unless the rename failed) | `uploaded`; pruned once the work is in history |

A later run **never** uploads an artwork whose confirmed upload was durably recorded (promoted to `uploaded` and `fsync`ed).

*Amended at the Phase 4 gate (D-153, D-154; R-29).* "Never" holds within the 20 000-entry bounds of history and the ledger. Once a work leaves history (after 20 000 later deliveries), or its `uploaded` entry is dropped at the ledger's bound, it is no longer excluded and could in theory be shown again.

There is one exception. If the process dies, or the promotion write fails, between receiving `uploaded` and the promotion `fsync`, the entry stays `uncertain` and excludes the work only for the quarantine period.

An artwork whose upload is uncertain is never uploaded on the next run, and not again until the quarantine period ends.

*Amended at the Phase 5 gate (D-162).* Row 6 (explicit upload refusal) is not produced in the beta: the library does not tell a refusal before the transfer from one after it, so after `upload_started` the quarantine is always kept. A failure before `connected` that is not a transport failure (a close frame, a malformed or unexpected answer) is `protocol`. `connected` is sent only once the art channel is open, after pairing, and Frame support is checked before it: a rejected token, an unaccepted prompt, a TV without Frame support, and `insufficient_time` before the TV is contacted therefore come with no marker, and rows 2–4 apply to them with "none" as the last marker. The Art API 0.97 refusal and `insufficient_time` after pairing come after `connected`. The intent is removed in each of these cases; only `insufficient_time` after `connected` gets the hint "paired; start the app again".

**Status → outcome:**

| Status | Outcome |
| --- | --- |
| `ok` | `delivered*` |
| `unreachable` | `tv_unreachable` |
| `protocol` | `tv_unreachable`, handled like a lost connection |
| `not_authorized` | `tv_not_authorized` |
| `unsupported` | `tv_rejected` |
| `refused` | `tv_rejected` |
| `insufficient_time` | `deadline_exceeded` |

The television state and the ledger always follow the last marker seen.

---

## 13. Persistent state and storage

### 13.1 Layout

| Path | Contents | Bound | In HA backups |
| --- | --- | --- | --- |
| `/data/options.json` | Options | — | yes (expected) |
| `/data/state/history.json` (+ `.bak`) | Confirmed sent or displayed identifiers, with timestamps | ≤ 20 000 entries and ≤ 5 MiB | yes (expected) |
| `/data/state/upload_ledger.json` (+ `.bak`) | TV-upload exclusion ledger: `uploaded` and `uncertain` entries (§13.6) | ≤ 20 000 entries and ≤ 5 MiB; `uncertain` expires after the 30-day quarantine period (Q-23) | yes (expected) |
| `/data/state/current.json` | Attribution and SHA-256 of the artwork on the TV, plus the last 10 preview fingerprints. Written only after `selected`. | ≤ 16 KiB | yes (expected) |
| `/data/state/last_run.json` | Outcome, timestamps, stats, and effective and ignored filters (no secrets). Written for every outcome except watchdog termination. | ≤ 16 KiB | yes (expected) |
| `/data/state/.lock` | Advisory lock | — | — |
| `/data/state/quarantine/` | Corrupt state files, kept for diagnostics | ≤ 3 files | excluded (expected) |
| `/data/cache/<provider>.json` | Metadata cache (§13.4) | ≤ 1 000 entries, ≤ 2 MiB, TTL ≤ 7 days | excluded (expected) |
| `/data/tv/<host-id>.token` | Pairing token | 1 file | excluded (expected) |
| `/tmp/frame-gallery/run-<random>/{in,out}/` | RAM-backed scratch | removed every run | n/a |
| `/media/frame_gallery/library/` | User images (read-only for the app) | user-managed | per the user's settings |
| `/media/frame_gallery/preview/` | The published preview | 1–2 files (§16.3) | per the user's settings |

*Amended at the Phase 5 gate (D-164).* With a worker group, `/tmp/frame-gallery/` and `run-*/` are 0710, `in/` 2750, and `out/` 2770, all in the worker's group (65534 when the parent is root).

"Expected" means two assumptions that Phase 8 checks by inspecting a backup: `/data` is included in app backups, and `backup_exclude` paths are relative to `/data`.

History and the ledger store only identifiers and timestamps (`LEGAL_BOUNDARIES`).

### 13.2 Atomic write protocol (D-110, accepted)

Every write uses one primitive that works relative to a directory file descriptor.

1. Open the directory with `O_DIRECTORY | O_NOFOLLOW`, and refuse if it is a symbolic link.
2. Serialize, then re-parse JSON as a self-check.
3. Create `<name>.tmp-<random>` with `O_CREAT | O_EXCL | O_NOFOLLOW`, write it, and `fsync` it.
4. **History and ledger only (best-effort):** refresh `.bak` through a fresh `.bak.tmp-<random>` hard link and a rename. This step never blocks step 5.
5. Rename the temporary file over the target.
6. `fsync` the directory.

**Pre-staging.** Before DELIVER, PRE-STAGE runs steps 2–3 for history and commits the ledger intent. A full or read-only `/data` becomes `state_error` while the TV is still untouched.

After `uploaded`, one small atomic write promotes the ledger entry. After `selected`, recording history is a single rename.

**`.bak` scope.** The `.bak` copy covers primaries that are unparseable or schema-invalid. It does not cover well-formed but wrong data.

**Reader.** Primary, then `.bak`, then empty with a WARNING. Only parse or schema failures are quarantined. The reader never raises.

*Amended at the Phase 4 gate (D-153, D-154, D-158).*

- The self-check (step 2) reads each document back with the reader's own rules, so nothing is written that this code could not read.
- Files that are not regular, or exceed their size bound, count as damaged and are quarantined too. A file that exists but cannot be read, or one written by a newer version, is not quarantined: history and the ledger then end the run with `state_error`, instead of falling back to `.bak` or an empty state.
- `.bak` is refreshed only from a primary that was valid, so a damaged primary never replaces a good backup.
- A failed directory `fsync` after a successful rename: for the upload intent it is an error (`state_error`), so the television is never contacted without a durable intent. For a promotion the file already says `uploaded`, but the runner logs an ERROR and the outcome is unchanged (§13.6 step 4). Recorded history, the preview, and the run records count as written, with a warning.
- Timestamps must lie from 2000 to 8999, and every version writes `format` and `version` first, so a newer file over the size bound is still recognised as newer.

### 13.3 History

- **Format.** `{"format": "frame-gallery-history", "version": 1, "entries": [{"id": "aic:…", "at": "…"}]}`.
- **Bounds.** At most 20 000 entries and 5 MiB; the oldest are dropped first.
- **Known limitation (accepted at the Phase 4 gate; R-29).** Only the latest 20 000 delivered works are remembered. When the bound is reached, the oldest entry is dropped, and that very old work could in theory be shown again. At one artwork a day this first happens after about 55 years; at one an hour, after about 2.3 years.
- **Versions.** A newer version is not treated as corruption; the run ends with `state_error` before the TV is touched.
- **Lock.** `flock(LOCK_EX | LOCK_NB)` in CONFIGURE. Contention gives `already_running`.

### 13.4 Metadata cache

- **Format.** One JSON file per provider. Entries are at most 8 KiB and hold identifiers, counts, and page or skip hints: never images, never whole pages.
- **Bounds.** At most 1 000 entries and 2 MiB, TTL at most 7 days. Expired entries are evicted first, then least-recently-used ones.
- **Writes.** At most one per run; corruption means discard.
- **Beta use.** Counts and hints for the Art Institute and Cleveland (acceptance item `F6`).
- *Amended at the Phase 4 gate (D-156, D-157).* The file holds counts (1 day) and exhausted-page hints (7 days); an entry is at most 8 KiB, and one hint at most 800 pages. A page is hinted only if it offered works and every one of them is in history or uploaded; a hint is valid only for the same result count. The cache is written once, in FINISH, before the last-run record. An expiry more than 7 days ahead (a clock that went back) is cut to 7 days from now. Damage discards the whole file; there is no quarantine and no `.bak`.

### 13.5 Preview publication

- **Write.** The parent copies the validated delivery bytes into the preview directory with the §13.2 primitive and re-checks the SHA-256. Mode `0644`.
- **Guard.** Publication is refused if any path component is a symbolic link.
- **File naming** follows the refresh mechanism chosen in Phase 8 (§16.3): one `latest.jpg`, or two alternating names.
- **Failure.** If `/media` is unavailable, the outcome is `delivered_with_warnings`.
- *Amended at the Phase 4 gate (D-158).* Every name is staged, read back, and hashed before any is renamed, and new directories get exactly mode 0755. `current.json` keeps the D-118 fingerprints of the last 10 previews, newest first, for the local library's guard 3; the fingerprint is recorded even if the preview could not be published.

### 13.6 TV-upload exclusion ledger (D-137)

- **Purpose.** Never re-upload an artwork the TV already received, even if selection was never confirmed. History keeps its specified meaning: confirmed sent or displayed. *Amended at the Phase 4 gate:* within the 20 000-entry bounds of history and the ledger (R-29).
- **Format:**

  ```json
  {"format": "frame-gallery-upload-ledger", "version": 1, "entries": [{"id": "cma:…", "state": "uploaded" | "uncertain", "at": "…"}]}
  ```

- **Lifecycle.**
  1. PRE-STAGE commits an `uncertain` entry as a write-ahead intent. This covers a process killed after the upload.
  2. The `uploaded` marker promotes the entry to `uploaded`.
  3. **Removal rule.** The intent is removed in two cases:
     - no `upload_started` marker was seen, whatever the reason: TV unreachable, pairing not accepted, art mode unsupported, or SIGTERM or the kill timer before `upload_started`;
     - the upload was explicitly refused.

     It remains as an uncertainty quarantine only after `upload_started` without `uploaded`, or when the process dies without classifying the run.

     *Amended at the Phase 5 gate (D-162, D-163).* The second case is not produced in the beta: the installed library does not tell a refusal before the transfer from one after it, so after `upload_started` the intent always stays as quarantine (§12.4). A television worker that fails its isolation (`IsolationFailure`) ends the run as `internal_error`, and a committed intent then stays as quarantine even without `upload_started` (§4.2, §11.3).
  4. **Failed promotion.** If the promotion write after `uploaded` fails (for example, the disk is full), the run logs an ERROR and keeps the `uncertain` intent. The run outcome does not change.
  5. **Pruning.** Once the work is in history, its entry is pruned on the next ledger write.

     *Amended at the Phase 4 gate (D-154).* Only the intent write prunes. It drops `uncertain` intents whose quarantine has ended and, of the works in history, only those that both copies hold (the primary and its `.bak`), so a damaged primary never loses the newest delivery's exclusion.
- **Bounds.**
  - At most 20 000 entries and 5 MiB; the oldest `uploaded` entries are dropped first. A dropped `uploaded` entry no longer excludes its work (R-29, accepted at the Phase 4 gate); entries normally leave the ledger long before, once history holds their work.
  - `uncertain` entries expire after the **30-day** quarantine period (Q-23, accepted).
- **Exclusion.** Selection skips `history ∪ uploaded ∪ unexpired uncertain` (§8.2).
- **Reader and versions.** Same as history.
- **Tests.** Acceptance items `E7`–`E10` (§20.1).

---

## 14. Cleanup guarantees

1. The workspace is removed in `finally`.
2. On every exit path, the worker group is killed first. Workers also die with the parent (`PR_SET_PDEATHSIG`).
3. A startup sweep removes leftover run directories and our own regular `*.tmp-*` and `*.bak.tmp-*` files in `/data/state`, `/data/cache`, `/data/tv`, and the preview directory.
4. The RAM-backed `/tmp` vanishes with the container.
5. Persistent state is bounded: history, ledger, cache, quarantine, and one token.

Tests cover failure injection at every stage (`F1`, `F2`), byte bounds over repeated runs (`F3`), and that no worker survives a watchdog kill.

*Amended at the Phase 4 gate (D-155).* The sweep runs only after the state lock is taken. It removes only exact names of the right kind (regular files `<name>.tmp-<16 hex digits>` and `<name>.bak.tmp-<16 hex digits>`, and directories `run-<16 hex digits>`), never follows a link, and scans at most 1 000 entries per directory. `in/` and `out/` have mode 0700 until Phase 5 gives the unprivileged worker its modes.

*Amended at the Phase 5 gate (D-163, D-164).* The workspace modes are those of §13.1. Workers also end with the parent through their lifeline thread, and after every task the worker's group and the worker are killed and the worker is reaped (waiting at most 2 s).

---

## 15. Configuration and filters

### 15.1 Options (D-123)

| Option | Schema (Supervisor syntax) | Default | Plain-language meaning |
| --- | --- | --- | --- |
| `tv_host` | `match(^(?:\d{1,3}\.){3}\d{1,3}$)` (required; no default) | — | IPv4 address of your Frame TV (reserve it in your router). |
| `source` | `list(art_institute_chicago\|cleveland_museum_of_art\|local_media)` | `art_institute_chicago` (Q-08, accepted) | Which museum or source the artwork comes from. |
| `department` | `list(any\|cma_…)` | `any` | Department or collection within the selected museum. The first beta offers Cleveland departments only; with another source, a department is reported as not applicable. |
| `style` | `list(any\|period_…)` | `any` | Period of creation (both museums). The first beta offers no styles. |
| `color` | `list(any)` | `any` | No source supports a colour filter in the first beta (Q-25, option (a)); the description says so. |
| `landscape_only` | `bool` | `true` | Only choose artworks that are wider than they are tall. |
| `strict_tv_format` | `bool` | `true` | Prefer artworks close to the TV's 16:9 shape. |
| `fit_mode` | `list(contain\|cover)` | `contain` | `contain` shows the whole artwork (no crop); `cover` fills the screen and may crop. |
| `background_color` | `match(^#[0-9A-Fa-f]{6}$)` | `#000000` | Margin colour in `contain` mode. |
| `source_helper`, `department_helper`, `style_helper`, `color_helper` | `match(^(input_select\|select\|input_text)\.[a-z0-9_]{1,64}$)?` | unset | Optional helpers that override the matching option at run time. |
| `log_level` | `list(info\|debug)?` | unset → `info` | Advanced: log detail. |

- **Accepted defaults** (D-123): `contain` (no crop), landscape-only, and strict near-16:9 are all on.
- **`tv_host`** is required (acceptance item `B1`) and re-validated by the app (§15.4, acceptance item `B7`). `192.168.178.30` is only the user's Phase 8 test value: it is never a default and never appears in code.
- **Not options:** there is no time-limit option (§7.2) and no library-path option (§9.3).
- **Descriptions** in `translations/en.yaml` state which sources each filter applies to (§9.2).
- *Amended at the Phase 3 gate (D-146, D-152; Q-25, option (a)).* Vocabulary version 1 ships no `aic_…`, `style_…`, or `color_…` key. A value that matches no key, label, or alias of the option, and is not a no-filter term (`any`, `all`, `random`, `none`, or an empty value), is rejected as invalid (B5); as a helper value it falls back to the static value. A valid key that the selected source does not support is reported as unsupported (B8). Before the gate, the rows read: department `list(any|aic_…|cma_…)`, style "Style (Art Institute only) or period (both museums)", and colour "Dominant colour (Art Institute only)".
- *Amended at the Phase 6 gate (D-166, D-168).* The options are read once per run from `/data/options.json`, below the `/data` anchor, without following a link, at most 64 KiB, as strict JSON; anything else ends the run as `config_invalid`, with a message that says what to do. `config.yaml` and `translations/en.yaml` are written by `scripts/app_config.py` from the app's own definitions, and a test checks every offered value and pattern against the app's parser. `log_level: debug` raises the app's own loggers once the options are read.

### 15.2 Filter vocabularies (D-124, D-146)

- The vocabularies are versioned; each entry has a key, a label, and aliases. The beta ships version `1` (Q-14, resolved). It is built only from values that the official documentation names (D-146).
- **Departments** are namespaced by source.
  - *Cleveland:* a small, curated subset of the 21 documented values, chosen for works suited to a wall display. Each label names the museum, so labels stay distinct across museums (D-143). The verbatim department name is an alias. The adapter maps each key to its exact documented value.
  - *Art Institute:* none in the beta. The documentation names the `department_title` field but not its values (Q-25).
- **Styles:** none in the beta. Cleveland documents no style field; the Art Institute documents `style_title` but not its values (Q-25).
- **Periods:** five project-defined ranges of the earliest creation year, valid for both museums: before 1400, 1400–1599, 1600–1799, 1800–1899, and 1900 and later. They are labelled with years, not style names.
- **Colours:** none in the beta. The Art Institute documents a dominant-colour object "in HSL" but not its members; Cleveland documents no colour field (Q-24, Q-25).
- **Helper normalization.** Values are case-folded, NFKD-normalized with diacritics stripped, and separators become `_`. The result is matched against keys, labels, and aliases. `any`, `all`, `random`, `none`, and an empty value mean "no filter".
- The mapping (keys, labels, aliases, and provider values) is documented in `frame_gallery/VOCABULARY.md`, and a test keeps it identical to the shipped vocabulary.

### 15.3 Helper overrides

Helpers are read only when at least one `*_helper` option is set.

- **Reads.** At most **4 reads**, each ≤ 3 s, all inside the 10 s configuration window.
- **Request safety.** Entity IDs are re-validated with `fullmatch` and percent-encoded. Redirects and retries are off. `Authorization` is sent only to `http://supervisor`.
- **Response limits.** At most 64 KiB, JSON only, and only the `state` field (≤ 255 characters) is used.
- **Fallback.** Any failure falls back to the static value, with one WARNING (acceptance items `B3`–`B5`).
- **`source_helper`** accepts only the three source keys. After the source changes, filters that no longer apply are reported as ignored (§9.2).

### 15.4 Television address (D-125, accepted)

- **Format.** `tv_host` must be an **IPv4 literal**: four octets, each 0–255. Hostnames and IPv6 addresses are not accepted in the beta.
- **Accepted ranges.** RFC 1918 private ranges only: `10/8`, `172.16/12`, `192.168/16`.
- **Rejected.** `169.254/16` link-local addresses; loopback, unspecified, multicast, and broadcast addresses; the container's own interface networks, determined at run time. These include the Supervisor's internal app network, which keeps the TV client and its token away from internal services.
- **Use.** No DNS is involved. The validated literal goes to the TV worker.
- **Failure** gives `config_invalid`.

*Amended at the Phase 6 gate (D-166).* The container's networks come from the kernel's IPv4 route table, `/proc/net/route`: every route except the default one names a network the container reaches. On Linux a table that is missing, oversized, or not in the kernel's form fails closed as `config_invalid`, because this rule and the helper reader's token rule (D-148) depend on it.

---

## 16. Dashboard and filter selection

### 16.1 Comparison of the three approaches

| Criterion | A. Documented HA helpers | B. App Ingress UI | C. Future companion integration |
| --- | --- | --- | --- |
| User effort | UI helpers, pasted lists, entity IDs entered in the options | App panel | A custom integration |
| No SSH, no `configuration.yaml` | Yes | Yes | Only through a third-party store (HACS) or a manual copy |
| Fits the one-shot lifecycle | Yes | **No**: needs a running server | Yes |
| Dynamic option lists | No | Yes | Yes |
| Automations | Excellent | Poor | Excellent |
| Security surface | ≤ 4 helper GETs; optional fixed timer.cancel (D-176) | Web server, request handling, CSRF | Runs inside Home Assistant Core |
| Cost and maintenance | Small and low | High and medium–high | High and high |

### 16.2 Recommendation (D-126)

- **Beta:** static options plus optional helpers (A).
- **Ingress:** not planned.
- **Companion integration:** deferred.

### 16.3 Beta dashboard design (D-111, D-140)

**Platform basis** (recorded in the Codex review):

- Home Assistant OS creates `/media` without user configuration.
- Configured and default media directories are in Home Assistant's default external-directory allowlist. The documentation examples show `/media/…` paths working "without extra setup".
- So a normal Home Assistant Green installation needs **no `configuration.yaml` edit, no configuration-folder mapping, no SSH, and no manual file modification** (acceptance item `G6`).
- Users with a custom `media_dirs` get a documentation note.

**Setup order** (documented):

1. Install through the one-click link and set `tv_host`.
2. Start the app. When the TV prompt appears (once the run reaches the TV step), accept it within 20 s. Repeat until the log shows `outcome=delivered`.
3. Add a **Local File** camera for the preview file, named "Frame Gallery Preview". The expected entity ID is `camera.frame_gallery_preview`; Phase 8 records the actual one.
4. Running is optional diagnostics only: Phase 8 observed about 15-minute lag, so it must not decide loading completion (D-176). Non-admin access still needs separate verification.
5. Create the timer helper (UI), put its exact entity ID in the app's optional `loading_timer` field, and paste the documented script (UI script editor, YAML mode). All of this is UI-created, with no `configuration.yaml` edit.
6. Paste the card.

The acceptance-item `G1` deliverable is therefore **card + script + timer helper**, plus the post-run automation if the chosen freshness mechanism needs one. Each comes with copy-and-paste YAML (Q-09). It is completed after Phase 8 (entity IDs) and finalized with the public slug in Phase 9 (Q-13).

**Start and loading state: the timer is the normative indicator.** The card's tap runs a UI-created **script**, not `hassio.app_start` directly, and the scheduling example uses the same script. The script runs in `single` mode and performs these steps:

1. Start a UI timer helper with a duration of **150 s** (`T` + 30 s).
2. Call `hassio.app_start` with `data: {app: <slug>}` and `continue_on_error: true`.
3. Wait until the timer is no longer active, with a 150-second wait timeout. After its cleanup, the app cancels only its explicitly configured timer via one fixed, guarded service POST (at most 2 seconds within FINISH; D-176). Success, no-match and graceful cancellation all end loading; this is not a success indicator.
4. Delay four seconds in single mode for the base image's shutdown. A failed start, unreadable options, missed completion or hard kill leaves the timer to expire naturally; no sensor cache can end it early.

The freshness step, if any, is **not** part of this script (see below).

The conditional card shows *"Updating artwork…"* while the **timer is `active`**. It may additionally require the Running sensor to be `on` (AND, never OR). The timer expires on its own, so the card returns to idle in every case (acceptance item `G4`), and **the dashboard never shows a loading state for more than 150 s**.

Running is no longer a completion dependency. The timer remains bounded to 150 seconds even when the app cannot notify it. D-176 authorizes the scoped test correction; live results are recorded separately.

Three further constraints:

- The slug is observed after installation (Q-13).
- `hassio.app_start` is admin-only (Q-19).
- A mistyped slug fails only at run time; `continue_on_error` lets the script carry on and cancel the timer.

**Preview freshness is release-blocking (acceptance item `G5`).** The existing installation suffered from stale images, so the dashboard is **not complete** until repeated live tests on the Home Assistant Green show every newly delivered image without a stale browser cache.

Phase 8 selects and documents **one** proven, fully UI/API-based mechanism from these candidates:

1. Local File's documented behaviour ("If the image is updated on the file system, the image displayed in Home Assistant will also be updated"). The mechanism behind it is undocumented.
2. `homeassistant.update_entity` on the camera after the run. Its effect on this entity is undocumented.
3. Two alternating preview names (`preview_a.jpg`, `preview_b.jpg`), switched with `local_file.update_file_path` so that the frontend sees a new file path.
4. Another UI/API-only method found during validation.

**Eligibility.** The chosen mechanism must keep the preview correct on **every documented start path**: card tap, scheduled automation, and a start from the app page.

- **Post-run step placement.** Any post-run step (candidates 2 and 3) lives in **one UI automation triggered by the Running sensor turning `off`**. That automation covers every start path, including starts from the app page, which run no script.
- **Candidate 3.** It is eligible only if the app writes each delivered preview atomically to **both** names, so that switching can never show an older artwork, for example after a `no_match` run. Another scheme qualifies only if it has the same property.
- **Phase 8 tests.** The repeated freshness tests include a card-started run, an automation-started run, an app-page-started run, and a `no_match` run.

The evidence and the choice are recorded under R-07 and D-140. §13.5 then follows the matching file naming.

**Collection Image (optional; Home Assistant 2026.9+).**

- `collection_image` creates an image entity from a media-source folder and shows a randomly chosen file. The only documented way to change it is the `collection_image.shuffle` action. No automatic rotation, and no refresh on file change, is documented.
- It is not documented to reflect an in-place overwrite, and it would need a folder that holds only the latest preview.
- It may be documented as an optional alternative. It does **not** raise the app's minimum version (`2026.2.0`).

**Scheduling.** The documentation includes a UI automation example that runs the same script on a schedule.

*Amended at the Phase 6 gate (D-168).* `DOCS.md` holds the draft as copy-and-paste YAML: the script, the card, and the scheduling example, with the expected entity IDs `camera.frame_gallery_preview`, `binary_sensor.frame_gallery_running`, `timer.frame_gallery_run`, and `script.frame_gallery_new_artwork`, and the app ID `local_frame_gallery` of a local copy. Every entity ID is marked as expected until Phase 8 confirms it, and the freshness mechanism is still open (D-140).

---

## 17. Home Assistant packaging

This section follows the current developer documentation, including the app rename (2026.2) and the builder migration (2026-04).

### 17.1 App metadata: illustrative `config.yaml` (D-129)

```yaml
name: Frame Gallery
version: "0.1.0"                 # = image tag = Git tag = CHANGELOG entry
slug: frame_gallery              # accepted provisional identifier (D-138)
description: Sends one fresh artwork to a Samsung Frame TV each time it is started.
url: <project URL, Q-13>
arch: [aarch64, amd64]
image: ghcr.io/<org>/frame-gallery   # generic multi-arch manifest; omitted for local development builds
startup: once
boot: manual_only
init: false                      # s6-overlay v3 base (D-130)
stage: experimental              # until Phase 8 validation passes
homeassistant: "2026.2.0"        # hassio.app_* actions; NOT raised for Collection Image
homeassistant_api: true          # ≤ 4 helper GETs, plus optional fixed timer.cancel (D-176)
tmpfs: true
timeout: 20
map:
  - type: media
    read_only: false             # grants read-write to ALL of /media; apparmor.txt narrows it (§17.6)
backup_exclude: ["cache/**", "state/quarantine/**", "tv/**"]
options: { … §15.1 … }
schema:  { … §15.1 … }
```

**Deliberately not set:**

- `hassio_api`, `hassio_role`;
- `host_network` (Q-16: start without it);
- `privileged`, `full_access`, `docker_api`;
- `ingress`, `ports`, `devices`, `stdin`, `watchdog`, `advanced`;
- no `build.yaml`.

With the custom AppArmor profile, the security rating is 6.

*Amended at the Phase 6 gate (D-168).* `config.yaml` is written by `scripts/app_config.py`, with the version `0.1.0.dev0`. No `url` and no `image` are set before the release: until images are published (Phase 9), the Supervisor builds the app on the device from the Dockerfile, which needs the same network sources as the development build (R-32); Phase 8 settles the install route (Q-21).

### 17.2 Container image (D-130)

- **Base image.** `ghcr.io/home-assistant/base`, pinned by tag and digest, with `init: false`.
- **Phase 6 checks.** These run after the user approves pulling the image:
  - (a) Alpine and Python versions. Once the Python version is fixed, the Pillow wheel SBOM inspection is repeated on the exact two runtime wheels, and that result is authoritative for the inventory;
  - (b) the container stops when `CMD` exits;
  - (c) SIGTERM arrives with enough grace;
  - (d) `SUPERVISOR_TOKEN` is visible without `with-contenv`.

  If any check fails, the recorded plain-Alpine fallback is used.
- **Packages.**
  - `python3` is pinned to an exact apk version.
  - The venv is created `--without-pip`, from hash-pinned, binary-only wheels, with the lock generated by `uv` (D-128).
  - Pillow comes only from PyPI wheels. *Corrected in Phase 6 (D-171):* the exact runtime wheels (CPython 3.14, `musllinux_1_2`, `aarch64` and `x86_64`) contain neither `libimagequant` nor FriBiDi; Pillow's SBOM lists both only as optional dependencies. They do contain Pillow's **LGPL-2.1-or-later fribidi-shim**, and the image's Alpine packages include **GPL** components (BusyBox, bash, readline, gdbm, and others), so the image is **not** free of GPL components.
- **Labels.**
  - `io.hass.arch` comes from `BUILD_ARCH`, falling back to `TARGETARCH`.
  - `io.hass.version` comes from a required `ARG`.
  - The OCI licenses label is omitted.
- **Notices.** All license texts, including the GPL and LGPL texts of the image's copyleft components (the Alpine packages, `samsungtvws`, and Pillow's fribidi-shim; D-171); the IJG and FreeType acknowledgements; the OS-package list from the image's inventory (R-17); and copyleft source availability (D-135). Apache-2.0 covers only the project-owned code, not the whole image (D-102).

*Amended at the Phase 6 gate (D-167, D-170, D-171).*

- **Base and interpreter.** `ghcr.io/home-assistant/base:3.24-2026.08.0`, pinned by digest (Alpine 3.24.1, s6-overlay 3.2.3.0), and Alpine's `python3=3.14.8-r0`.
- **Stages.** `base`, `python`, `builder`, `app`, `test` (never published), and `runtime`, which is `app` and the last stage, so a build without a target, as the Supervisor makes it, produces the app image. The app image holds no pip, no wheel, and no build tool.
- **Only PyPI.** The venv is filled with `PIP_CONFIG_FILE=/dev/null pip --isolated … --require-hashes --no-deps --only-binary=:all:` from per-platform requirement files that `scripts/image_requirements.py` writes from the lock (`requirements/image-runtime.txt`, `image-test.txt`; amends D-142).
- **Labels.** `BUILD_ARCH` and `BUILD_VERSION` are required, with no fallback to `TARGETARCH`; with BuildKit, `BUILD_ARCH` must match the platform being built (amends D-130 and the bullet above). The app sets its own OCI title, description, and version, and clears the base image's OCI source and build time.
- **The D-130 checks** passed on both architectures: (a) as above; (b) as worded; (c) only with `S6_CMD_RECEIVE_SIGNALS=1`, because s6-overlay otherwise kills the command 3 s after a stop request; (d) only with `with-contenv` in `CMD`, because s6 resets the command's environment. The plain-Alpine fallback is not used.
- **The exact `python3` pin** stops resolving once Alpine replaces the package, which breaks later builds, a Supervisor build on the Green included; the packages it pulls in are not pinned (R-32).
- **Inventory.** `scripts/image_inventory.py` records, inside the image and without an SBOM tool, every Alpine package, the components outside apk, every Python distribution, and Pillow's bundled libraries, held to the wheel's `RECORD` (D-171). The licences of s6-overlay, tempio, and bashio are still to be read from upstream (R-33).

### 17.3 Build, development install, and release gates

- **Builds.** Docker Buildx builds both platforms. Releases use the Home Assistant builder actions and are signed with Cosign (Phase 9).
- **Phase 8 development install (Q-21).** Recommended: the user copies the app folder through a file-share app. Alternatives are a temporary private repository or a development image push, each with approval.
- **Release gates.**
  - The tests pass and their results are attached.
  - The license inventory is complete.
  - Tags are immutable, and `version` = tag = image = CHANGELOG.
  - `stage: stable` only after Phase 8.
  - `G5` passed: one preview refresh mechanism proven in repeated Phase 8 live tests and recorded in D-140 and R-07.
  - The D-102 license (Apache-2.0, accepted) is applied to the project-owned code only.
  - The **qualified licence review** is complete (D-135, R-25), covering the GPL-3.0-or-later and LGPL components in the image.
  - Enforce-mode AppArmor and the verified privilege drop from Phase 9 are in place.

*Amended at the Phase 6 gate (D-170).* `scripts/container_check.sh` builds and checks both platforms locally: the D-130 checks, the inventory, a smoke run, and the two test passes of D-165. The release gates add the native `amd64` memory measurement, mandatory before an `amd64` version is published (at the latest in Phase 9); the licence review and the enforce-mode AppArmor profile stay release prerequisites.

### 17.4 Presentation and installation

- `README.md`, plus `DOCS.md` with the capability matrix, dashboard YAML, and acknowledgements, plus `CHANGELOG.md`.
- Original `icon.png` and `logo.png`.
- `translations/en.yaml`, with each filter description stating which sources it applies to.
- The one-click repository link is `https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=<encoded URL>`.

*Amended at the Phase 6 gate (D-168, D-172).* `DOCS.md` covers installation, the first start and pairing, the options with the capability matrix, the user's own images, the draft dashboard (§16.3), the outcomes of the log line, the known limitations in plain language, starting over (Q-06), privacy, and the licences. The icon and logo are original geometric drawings, made by `scripts/app_images.py` without fonts or trademarks.

### 17.5 Runtime environment

| Item | Handling |
| --- | --- |
| Environment | `SUPERVISOR_TOKEN` is kept in parent memory only for configured helpers or an explicit loading timer (D-176). `os.environ` is reduced to an **allowlist**: `PATH`, `LANG`, `LC_ALL`, `TZ`. Tokens, proxy variables, `NETRC`, and CA overrides are removed. |
| Options | Read directly from `/data/options.json` (mode `0600`) and re-validated. |
| Time | UTC. |
| SIGTERM | See §7.6. |
| User | The parent runs as root. Workers run as user 65534 (§11.3). An unprivileged parent is evaluated later (Q-10). |

*Amended at the Phase 6 gate (D-166, D-172).* The token is registered with the redactor whether or not it is kept, and so is the legacy `HASSIO_TOKEN`. On Linux the app refuses to run unless the isolation is enforced (§4.3). An unprivileged parent is not in the beta (Q-10): the parent needs the six capabilities of §17.6 to drop the workers and hand them the workspace; the question is revisited in Phase 9 with the per-worker AppArmor child profiles.

### 17.6 Required AppArmor policy (D-129; enforced in Phase 9)

| Area | Rule |
| --- | --- |
| `/media/**` | read-only |
| `/media/frame_gallery/preview/**` | read-write (the only writable location under `/media`) |
| Directory creation under `/media` | exactly `/media/frame_gallery/`, `preview/`, and `library/` |
| `/data/**`, `/tmp/**` | read-write |
| Interpreter and spawn | `ix`, `/dev/shm`, `/proc/self/**` |
| Network | `inet`/`inet6` stream and dgram only; raw and packet sockets denied |
| Capabilities | Only what the privilege drop and worker management need (expected: `setuid`, `setgid`, `chown`, `kill`), plus what the s6 base needs; recorded from complain mode |

*Amended at the Phase 5 gate (R-31).* Phase 9 adds AppArmor child profiles per worker (the image worker without network; the television worker with TCP only); the inherited (`ix`) spawn rule for the workers is revisited then.

*Amended at the Phase 6 gate (D-168).* The draft `apparmor.txt` (complain mode) names six capabilities: `setuid` and `setgid` (the drop to 65534), `chown` and `fsetid` (the workspace handed to the worker's group, without losing the setgid bit), `dac_read_search` (the parent reads what a worker wrote), and `kill`. It also allows UNIX stream sockets, which s6-overlay presumably uses; the Phase 8 complain log shows whether that is needed. Its syntax is checked (`apparmor_parser -Q -T`, Codex's follow-up check at the Phase 6 gate); its enforcement is not. Phase 8 reads what it would refuse on the Green, and Phase 9 enforces and verifies it, a release prerequisite.

*Phase 9 correction (D-182):* replace the draft's `dac_read_search` with Docker's
already-present `dac_override`, after the enforced Green parent-output-read probe
failed with EACCES. No container capability is added. This capability covers DAC
read/write/execute checks, not only reads; unchanged AppArmor path rules continue
to restrict writes/execution. Children still lose all capabilities before input.

*Phase 9 correction (D-183):* the parent's history/ledger atomic backup refresh
also needs hard-link permission, not only `rwk`. Two `link subset` pairs allow
each document's `.bak.tmp-*` name to link only its own valid JSON primary in
`/data/state`. No general link permission or worker state access is introduced.

**Sequencing (D-139).**

- Phases 6–8 run the profile in complain mode.
- Phase 9 switches to enforce mode. An approved live check then confirms two things: a fresh install works, and a write outside `preview/` is denied.

**Phase 9 amendment (D-178, D-180).** The table above describes the parent,
not the worker's effective policy. The production entry point requires its own
enforced Supervisor profile. A fresh worker switches one-way into image_worker
or tv_worker before dropping privileges/setting NNP and before any task input.
Neither child may execute, regain the parent profile, access state or write
arbitrary scratch/shared-memory files. The image child reads only code, library
and staged input and writes delivery JPEGs to the output directory; the TV child
reads prepared JPEGs and has IPv4 TCP permission only. The parent retains root
for existing workspace/worker management, with no new container capability or
mount. Interpreter-readable `rix` is required for the existing S6 script paths;
`ix` alone was refused on Green.

Actual Green checks exposed a gap in AppArmor network mediation despite the
enforced image label. A complementary worker-only seccomp filter (D-180) is
therefore mandatory in production: image tasks cannot create sockets; TV tasks
may create IPv4 TCP sockets only. Alternate ABIs/socket creation routes are
refused. It is installed after verified NNP and before the lifeline thread or
untrusted input; the parent checks both guards before sending the request.
Missing profiles or failed transitions/filter installation fail closed.
There is no user-facing bypass. Internal Docker-development wiring is not the
shipped entry point. Combined live negative tests, normal delivery and clean
public installation are still required; syntax/unit/kernel probes alone do not
complete this gate.

---

## 18. Security and privacy

### 18.1 Threat model

| Threat | Mitigation |
| --- | --- |
| SSRF, DNS rebinding | Exact host rules; one resolution with every address checked as global; connect to the validated IP; peer check; identifier `fullmatch`; redirects re-validated |
| Decompression bombs, parser exploits | Byte caps; header limits; unprivileged, memory-limited worker; bytes-only results; parent validation of the output |
| Home Assistant API misuse | Token removed from the environment, never given to workers; ≤ 4 helper GETs and one optional fixed timer.cancel for a validated explicit timer. No arbitrary service/configuration write (D-176). |
| Secret leakage | Formatter-level redaction, including exception text; worker output piped through the parent; third-party loggers capped at WARNING; tokens excluded from backups (expected; Phase 8) |
| Path traversal, symlinks | Fixed paths; `dir_fd` with `O_NOFOLLOW`; `O_EXCL` random temp names; refusal on symlinks |
| TV misuse, internal services | IPv4 literal in LAN ranges only; container networks rejected |
| LAN adversary impersonating the TV | DHCP-reserved IPv4 address; same subnet. Token scope and TLS behaviour are undocumented; trust-on-first-use is decided in Phase 5 (R-03). *Amended at the Phase 5 gate:* the library does not verify the TV's certificate (D-161); pinning is decided after the certificate is observed in the supervised Phase 8 test. |
| Duplicate uploads | History, upload ledger, and write-ahead quarantine (D-137) |
| Supply chain | Hash-pinned wheels; digest-pinned base image; exact apk pins; license inventory |
| Excess privilege | Least-privilege config; AppArmor (§17.6); unprivileged workers |
| Provider content | Parsed as data with stdlib parsers, size-capped |
| Privacy | No telemetry; no user data in headers |

### 18.2 Parsing

Only `json` is used. `html.parser` is allowed only if a provider is ever approved that needs it (D-127).

---

## 19. Logging and diagnostics

**INFO** records:

- a start banner: source, effective filters and their provenance, and **ignored filters with reasons**;
- the aggregated skipped-files warning;
- a selection summary;
- the chosen artwork with its attribution;
- the TV result;
- one final line: `outcome=<name> exit=<code> elapsed=<s> [ignored_filters=<filters>] [hint="…"]` (the key follows §9.2 and D-124; D-141).

**DEBUG** adds per-candidate decisions. Third-party loggers stay at WARNING.

**Redaction** applies to fully formatted lines, including exception text, and covers known secret values and token patterns. Workers use the same logging setup, and their output passes through the parent.

**`no_match` hints** are "filters too restrictive", "nothing new left for these filters", and "search limits reached". Ignored filters are always named.

---

## 20. Testing strategy

### 20.1 Layers

| Layer | Scope |
| --- | --- |
| Unit | Geometry; classification and upscale rule; vocabularies and capability matrix; IPv4 validation; phase sums (120 s total, 70 s no-match bound); atomic store with a crash after every step; history and ledger bounds, TTL, and versions; cache; redaction; symlink attacks |
| Contract | Local, AIC, and CMA adapters on synthesized fixtures: laziness, bounds, identifier stability, deadline, rights basis (AIC `is_public_domain`; CMA `cc0` flag and `share_license_status`), CMA print-JPEG selection and TIFF avoidance, capability reporting |
| Component | Gateway attacks and timing (slow drip, multiple addresses, pacing, 429 and `Retry-After`); helper client; imaging worker under the real memory limit; TV adapter against a double of the installed 3.0.6 surface |
| Integration | Full runner with real workers and fakes; failure injection. **Ledger scenarios** (`E7`–`E10`): selection refused after upload; connection lost during selection; SIGKILL after PRE-STAGE, after `uploaded`, and between marker receipt and the promotion `fsync`; the next run uploads none of these works. Also: kill after `selected`; SIGTERM before RECORD; worker environment allowlist; hostile worker results; redaction of worker output; multi-run exhaustion |
| Timing | Real-time checks: `no_match` finishes within 70 s; the watchdog fires at `T` + 10 s; the prepare time for the D-121 worst cases (including worker spawn and the Pillow import) fits the 15 s budget. If preparation on the Green exceeds about 12 s, the local-media pixel caps are lowered. |
| Container | Both platforms; labels; smoke run; D-130 checks |
| Live (Phase 8, approved) | The §23 checklist, including **repeated preview-freshness tests** |

A `conftest` guard makes any socket connection raise (acceptance item `H2`).

### 20.2 Seams

`Clock`, `RandomSource`, `Transport`, `Resolver`, `Television`, `FileSystemRoots`, `Executor`, `SupervisorClient`.

### 20.3 Fixture policy

- Fixtures are **synthesized**. They keep the documented structure but use invented titles, credit lines, URLs, and identifiers, except for CC0 fields. Each carries a header naming the author, the source documentation, and the date.
- **Recorded observations** need user approval in Phase 3. They fetch metadata only, never images, and are synthesized before they are committed.
- **Test images** are generated. No third-party artwork is committed.

### 20.4 Quality gates

- `ruff check` and `ruff format --check`; `mypy --strict`.
- `pytest` with coverage:
  - at least 90 % overall;
  - 100 % branches in `budget`, `selection`, `store` (including the ledger), `net.gateway`, `providers/*`, `ha`, and `isolation`;
  - 100 % branches in the imaging encode fallback, the runner's attempt loop and outcome classification, and the TV reconnect path.
- CI runs on Python 3.12, 3.13, and 3.14.
- An import-boundary check.
- *Amended at the Phase 5 gate (D-163).* `mypy --strict` also runs as on Linux (`--platform linux`), `tv` joins the 100 % gate, and no coverage exemption is allowed in the worker's code.
- A license-inventory check (acceptance item `H4`).

---

## 21. Proposed repository layout

```text
repository.yaml   README.md   ARCHITECTURE.md   DECISIONS.md   STATUS.md   TASKS.md   …
THIRD_PARTY_NOTICES.md (Phase 2 onward, grows per dependency)   LICENSE (Apache-2.0, added when publication is prepared)
frame_gallery/                      # app directory = Docker build context
  config.yaml   Dockerfile   .dockerignore   apparmor.txt
  DOCS.md   README.md   CHANGELOG.md   icon.png   logo.png   translations/en.yaml
  requirements/runtime.txt          # hash-pinned (uv)
  pyproject.toml
  src/frame_gallery/
    __main__.py                     # Phase 6 (entry point)
    domain.py  errors.py  randomness.py                  # Phase 2 additions (D-141)
    fingerprint.py                                       # Phase 4 addition (D-158): the D-118 fingerprint
    app/         runner, outcomes, ports, records, signals, environment
    config/      options, filters, overrides, vocabulary, capabilities, tv_address
    ha/          supervisor_client                     # helper merging lives in config/overrides
    budget/      clock, deadline, allowance, limits, phases, watchdog
    net/         gateway, policy, resolver, transport
    providers/   contract, rights, local_media, aic/{gateway,parse,vocabulary}, cma/{gateway,parse,vocabulary}
    selection/   exclusion, shortlist, geometry
    imaging/     contract, sniff, delivery, worker_tasks (inspect, prepare), fit, jpeg_header
    tv/          port, samsung_task, token_store
    store/       atomic, fields, history, upload_ledger, state, cache, workspace, sweep, layout, preview, records   # Phase 4 (D-153 to D-158)
    isolation/   executor, channel, in_process, process, bootstrap
    logs/        setup, redact, summary
  tests/  support/  unit/  integration/  contract/  component/  timing/  container/  fixtures/authored/
  scripts/check.sh   DEVELOPMENT.md   uv.lock
```

*Amended at the Phase 5 gate (D-162, D-163; R-09, D-165).* `tv/` also holds `contract` and `samsung`, and `isolation/` also `framing`, `launch`, and `worker_main`; `scripts/` also holds `measure_prepare.py`, the R-09 measurement.

*Amended at the Phase 6 gate (D-166 to D-171).* `app/` also holds `networks`, and `store/` also `options_file`; `requirements/` also holds `image-runtime.txt` and `image-test.txt`; `scripts/` also holds `image_requirements.py`, `image_inventory.py`, `app_config.py`, `app_images.py`, and `container_check.sh`.

---

## 22. First public beta: scope

### 22.1 Included (D-120)

- The one-shot run, with every bound, outcome, and cleanup guarantee: at most 120 s, and `no_match` within 70 s.
- Three sources: local media, the Art Institute of Chicago (the default, Q-08), and the Cleveland Museum of Art.
- Source, department, and period filters, with the capability matrix and visible reporting of unsupported filters. Optional helpers. In the first beta, the `style` option offers periods only, and the `color` option offers no value besides "any" and its no-filter synonyms. No source offers a style or colour filter (D-146, D-152; Q-25, option (a)).
- Landscape-only; strict 16:9 with `contain` fallback; the upscale rule; `contain` (default) and `cover`; background colour.
- Atomic, pre-staged history; the TV-upload exclusion ledger and quarantine; atomic preview; small cache; self-healing pairing.
- Documentation:
  - installation, options, and the capability matrix;
  - the dashboard card and setup order, with the freshness mechanism proven in Phase 8;
  - helpers, scheduling, and troubleshooting;
  - honest limitations: Art Institute images are upscaled up to ≈ 2.28×; the Art Institute offers only the period filter, and Cleveland department and period; no source offers a style or colour filter; Google Arts & Culture, Bing, MoMA, and Orsay are not offered; keep the app's Watchdog off; very old works can come back once they leave the 20 000-entry history (R-29, amended at the Phase 4 gate).
- `aarch64` and `amd64` images.

### 22.2 Deferred

- Companion integration.
- Multi-source rotation.
- Europeana, Rijksmuseum, and The Met.
- Cleveland colour filtering by local analysis (Q-24).
- An advanced total-deadline option.
- Hostname and IPv6 TV addresses.
- Collection Image support.
- Remote-probe machinery.
- Matte selection.
- Helper auto-provisioning.
- An unprivileged parent process (Q-10; not in the beta, D-172).
- A configurable library folder.
- Local colour and style filters.
- History reset (Q-06; reinstalling is the reset, D-172).
- Additional CPU architectures, only if Home Assistant adds them.

### 22.3 Excluded or not planned

- **Google Arts & Culture:** excluded until a documented API exists.
- **Bing.**
- **Ingress.**
- **Managing old images on the TV:** a non-goal.

---

## 23. Implementation sequencing and approvals (D-139)

The vertical slice makes the core behaviour testable before packaging hardening. The final acceptance criteria are unchanged.

| Phase | Delivers | Approvals needed first |
| --- | --- | --- |
| 2: core and deterministic selection and rendering | `budget` (phase calculator, 120 s table); `config` (options, IPv4, vocabularies, capability matrix); outcomes; ports; in-process executor seam; **`app` run-orchestrator skeleton** (lifecycle stages, outcome classification, SIGTERM handling) against fakes; `selection` (exclusion interface, classification, shortlist); `imaging` prepare pipeline and fit geometry; `logs`; tooling (`uv`, `ruff`, `mypy`, `pytest`); network-blocking guard; import-boundary check; the start of `THIRD_PARTY_NOTICES.md` (Pillow and its bundled libraries) | **This revision (Phase 2 gate)**; the dev-dependency rows (complete); the Pillow row, with its corrected bundled-library inventory (GPL-3.0-or-later `libimagequant`, LGPL FriBiDi; *Phase 6, D-171: neither is in the exact runtime wheels*) and the remaining `pillow.libs` entries are verified in Phase 6 (gate adjustment approved by Codex) |
| 3: provider adapters | `net` gateway; `providers.local_media`, `providers.aic`, `providers.cma` with fake and synthesized fixtures, after a live-documentation re-check; **`ha` helper-override client** (≤ 4 reads, static fallback; acceptance items `B3`–`B5`); vocabularies; contract suite; `urllib3` and `certifi` added to the notices | Approved by the user on 2026-09-27: Q-14 and Q-22 resolved, the `urllib3` and `certifi` rows approved, no observation requests. **Gate passed** on 2026-09-27: D-146 to D-152 accepted, Q-25 resolved with option (a) |
| 4: bounded state and duplicate prevention | `store`: atomic primitive, history, **upload ledger and quarantine**, cache, workspace, preview publisher, run records, cleanup and sweep. PRE-STAGE, RECORD, and PUBLISH completed in the runner. `E7`–`E10` tested against a fake TV port that emits markers | — (Q-23 and D-113 accepted). **Gate passed** on 2026-09-27: D-153 to D-159 accepted; the 20 000-entry bound accepted for the first beta (R-29) |
| 5: Samsung adapter contract | Adapter surface from the **installed** `samsungtvws` 3.0.6 only; process executor with the complete §11.3 bootstrap (privilege drop, rlimits, bytes channel, markers); TV worker; token store; mocked and double tests; `E7`–`E10` re-run with the process-based TV worker; worst-case prepare memory and time measured on the development host without `RLIMIT_AS` (under the real limit: moved to Phase 6, D-165) | The `samsungtvws` row and its LGPL-3.0 obligations (D-135). **Authorized** by the user on 2026-09-27, after the Phase 4 gate: first check and document the version and the LGPL-3.0 obligations of `samsungtvws` 3.0.6, then build the executor and the adapter against simulations; the pinned version may be installed from PyPI into the git-ignored environment. The dependency row is recorded in Phase 5 and confirmed at the Phase 5 gate. **Gate passed** on 2026-10-02: D-160 to D-164 accepted; D-165 accepted on the condition that the Linux and root checks and the measurement under the real `RLIMIT_AS` pass in Phase 6 |
| 6: Home Assistant app packaging | `config.yaml`; Dockerfile; translations; `DOCS.md`; draft dashboard YAML; complain-mode `apparmor.txt`; container tests; D-130 checks a–d. *Added at the Phase 5 gate:* `inspect` batches, with parent-opened read-only descriptors where possible (D-149, D-164); the Linux and root checks and the worst-case measurement under the real `RLIMIT_AS` (the condition of D-165) | Pulling the base image; Q-06, Q-10; the Buildx, QEMU, and SBOM-tool rows; the authoritative Pillow runtime-wheel inspection, including verification of the remaining `pillow.libs` entries (mandatory before packaging or publication). **Authorized** by the user on 2026-10-02, after the Phase 5 gate, with separate approvals for starting Docker Desktop, pulling `ghcr.io/home-assistant/base` (pinned by tag and digest), the Alpine package source for `python3`, and PyPI for the hash-checked runtime wheels and test tools. **Gate passed** on 2026-10-03: D-166 to D-172 accepted, the 1 GiB limit unchanged; the native `amd64` measurement is mandatory before an `amd64` version is published, at the latest in Phase 9 |
| 7: offline release-candidate validation | Full gate run; provenance and license audit; failure-path exercises; release-candidate report | **Authorized** by the user on 2026-10-03, after the Phase 6 gate: offline only, with the existing local environments and container images; no new features; no access to the Green, the TV, a provider API, or GitHub; nothing published (gate: the user approves the live test) |
| 8: supervised Home Assistant Green and TV validation | Checklist: install via Q-21; the TV at the user's test value `192.168.178.30`, entered in the options and never hard-coded; **Q-16** (connectivity without `host_network`); **preview freshness, with one mechanism proven over repeated tests (card-started, automation-started, app-page-started, and `no_match` runs) and documented (D-140)**; entity IDs for the card (everything except the public slug); Q-05, Q-07, Q-09, Q-19 (including a mistyped slug); R-09, R-21; a backup without `tv/`; *added at the Phase 5 gate:* the TV's certificate, observed for the TLS-pinning decision (R-03), and its art API version (D-162) | **Explicit user approval**; Q-21 (install route); the Linux and root checks and the worst-case measurement under the real `RLIMIT_AS` have passed in Phase 6 (the condition of D-165) |
| 9: AppArmor, release hardening, public beta | Enforce-mode AppArmor and verification of the isolation design (with an approved live re-check); AppArmor child profiles per worker (R-31; confirmed for Phase 9 at the Phase 5 gate), with an unprivileged parent revisited (Q-10, D-172); the native `amd64` worst-case measurement under the real `RLIMIT_AS`, mandatory before an `amd64` version is published (Phase 6 gate); notices and SBOM; CI; signed multi-architecture images; one-click link; the dashboard card finalized with the public slug (Q-13); release notes; release gates (§17.3) | D-101 (name), Q-13; the builder-action and Cosign rows; publication approval |

---

## 24. Risks and open questions

`DECISIONS.md` has the full lists. The most consequential remaining items:

- **R-03.** Samsung Art Mode is undocumented. The adapter is established from the installed package and validated live in Phase 8. *Amended at the Phase 5 gate:* the library does not verify the TV's certificate; pinning is decided after the Phase 8 observation.
- **R-07 / D-140.** Preview freshness is release-blocking, and its mechanism is unproven until Phase 8.
- **R-06 / Q-09.** The Running sensor's latency is undocumented. The normative 150 s timer indicator does not depend on it.
- **R-22.** Neither museum documents that its provider identifiers are stable.
- **R-25 / D-135.** *Corrected in Phase 6 (D-171):* the exact runtime wheels contain neither `libimagequant` nor FriBiDi (R-25 is closed with D-171 at the Phase 6 gate). The runtime is still not GPL-free: its Alpine packages include GPL components, and Pillow's fribidi-shim is LGPL-2.1-or-later. The qualified licence review is a release gate.

---

## 25. Sources consulted in Phase 1

All research was read-only. It used public documentation pages, package-index metadata, policy pages, and `robots.txt` files. It also used one Microsoft Q&A answer and search-result snippets where a page blocked automated readers; both are marked where cited. No provider API, image URL, Home Assistant instance, television, GitHub page, or container registry was contacted.

**Home Assistant** (developers.home-assistant.io, www.home-assistant.io, my.home-assistant.io):

- App documentation: configuration, publishing, presentation, repository, communication, tutorial, testing, security.
- Supervisor API endpoints and models.
- Builder-migration and s6-overlay blog posts.
- Release notes and changelogs 2026.2, 2026.6, and **2026.9**, which introduced Collection Image.
- Integration pages: `hassio`, `local_file`, **`collection_image`**, `homeassistant`, `media_source`, `template`, `input_select`, `input_text`, `script`, `timer`, `image`, `default_config`.
- The local-media setup page.
- Action pages: `hassio.app_start`, `hassio.app_stdin`, `local_file.update_file_path`, `homeassistant.update_entity`, `image.snapshot`.
- Dashboard pages.
- Developer pages: scripts, REST, auth, image entity, manifest, config flow, selectors.
- The My Home Assistant FAQ.

**Dependencies:**

- PyPI metadata for all listed packages, plus `uv` and `pip-tools`.
- Documentation sites for Pillow, Requests, HTTPX, the Python devguide, and PEPs.
- The Alpine package index and release pages.

**Providers and Samsung:**

- **Google:** Terms, service-specific terms, the Cultural Institute partner pages, and `artsandculture.google.com/robots.txt`.
- **Microsoft:** `www.bing.com/robots.txt`, the Services Agreement (current and upcoming), the Bing Search API retirement notice, and one Q&A answer.
- **The Met:** image policy, terms, and the API article.
- **Art Institute of Chicago:** `api.artic.edu/docs` and the image-licensing page.
- **Cleveland Museum of Art:** **the `openaccess-api.clevelandart.org` documentation (the site root, plus the auto-generated `openapi.json` it links as endpoint documentation, read only to confirm the undocumented `randomize` parameter), `www.clevelandart.org/open-access`, and `www.clevelandart.org/terms-and-conditions`**.
- **Europeana:** API, key, and terms pages.
- **Rijksmuseum:** `data.rijksmuseum.nl` documentation and policy.
- **MoMA and the Musée d'Orsay:** collection and licensing pages.
- **Samsung:** developer.samsung.com Smart TV API references and a support page.
- **SmartThings:** developer.smartthings.com capability references.

**Deliberately not consulted:**

- Any GitHub-hosted page, including the CMA dataset link and the Collection Image author's profile.
- Community forums, apart from the one Q&A answer marked in §9.4.
- All predecessor or community Frame projects.

---

## Appendix A: Acceptance traceability

| ID | Acceptance item (abridged) | Designed in | Verified by |
| --- | --- | --- | --- |
| A1 | Repository addable via the UI or a one-click link | §17.4 | Phase 9 live |
| A2 | Green discovers the app without SSH | §17 | Phase 8/9 live |
| A3 | Green installs the pre-built `aarch64` image | §17.2, §17.3 | Phase 9 live |
| A4 | `amd64` image built from the same source | §17.2, §17.3 | Phase 6 build and label test (passed on both architectures, D-170); Phase 9 CI |
| A5 | No `configuration.yaml` change | §15, §16.3, §17 | Documentation review; Phase 8 |
| A6 | Understandable option names | §15.1, §17.4 | Translation review; Phase 8 |
| B1 | A missing TV IP prevents start | §15.1, §15.4 | Unit; `tv_host` has no default in `config.yaml` (D-168); Phase 8 |
| B2 | Static filters work without helpers, for the filters the selected source supports (capability matrix) | §9.2, §15 | Unit + integration |
| B3 | A valid helper overrides the static value | §15.3 | Component |
| B4 | A missing or unavailable helper falls back | §15.3 | Component |
| B5 | Invalid values are rejected or normalized predictably | §15.2, §9.2 | Unit (normalization; invalid or unmappable helper → static fallback) |
| B6 | Defaults preserve the full artwork | §11.2, §15.1 | Unit + imaging invariants |
| B7 | A TV address that is not an RFC 1918 private IPv4 literal is rejected | §15.4 | Unit (format, RFC 1918 ranges, rejection of 169.254/16 and of container networks) |
| B8 | Unsupported filters are visibly reported | §9.2, §19 | Unit + integration (log, summary line, `last_run.json`) + translation review |
| C1 | Filters the selected source supports combine correctly | §9.2, §9.5, §9.6 | Contract + integration |
| C2 | Portrait and square works are rejected when landscape-only is on | §8.1 | Unit |
| C3 | Sent identifiers are skipped across restarts | §8.2, §13.3 | Integration |
| C4 | At most 30 remote dimension requests; local inspection has a separate allowance | §7.2, §8.3 | Unit (counting fake gateway); local-inspection allowance unit test |
| C5 | The 120 s total plus allowance is never exceeded | §7.2 | Unit (phase sums) + timing |
| C6 | Restrictive filters fall back to landscape works | §8.2 | Unit |
| C7 | No candidate → clean exit, no upload | §4.2, §8.2 | Integration (TV spy) |
| C8 | No infinite retries | §7.4, §10, D-133 | Component |
| C9 | AIC candidates are CC0 only | §9.5 | Contract (`is_public_domain`) |
| C10 | CMA candidates are CC0 records only; print JPEG, never TIFF | §9.6 | Contract (`cc0`, `share_license_status`, rendition choice) |
| C11 | `no_match` finishes within 70 s | §7.2 | Unit (fake clock) + timing |
| D1 | A non-16:9 landscape work is fully visible | §11.2 | Unit + imaging |
| D2 | `contain` crops nothing | §11.2 | Invariants |
| D3 | Black margins by default | §11.2 | Imaging |
| D4 | `cover` crops only when selected | §11.2 | Imaging |
| D5 | EXIF rotation is corrected | §11.1 | Generated images |
| D6 | All image modes become a TV-compatible JPEG | §11.1 | Mode matrix |
| D7 | Excess size, pixels, or bytes are rejected | §10, §11 | Component + worker |
| D8 | The preview bytes equal the TV image | §6, §13.5 | Integration (SHA-256) |
| E1 | Upload and select | §12 | Adapter tests, including the unchanged library against a scripted TV (D-161); Phase 8 |
| E2 | Pairing problems are reported clearly | §12.2, §12.4 | Mapping tests |
| E3 | Timeouts and rejection end cleanly | §12.3, §12.4 | Kill and classification tests |
| E4 | Failed uploads never reach the sent history | §12.4, §13.6 | Integration |
| E5 | A success records exactly one ID | §13.2, §13.3 | Integration |
| E6 | No resend while unsent works remain | §8.2, §13.6 | Integration (multi-run) |
| E7 | Upload OK, selection refused → ledger entry, not resent | §12.4, §13.6 | Integration |
| E8 | Upload OK, connection lost during selection → ledger entry, not resent | §12.4, §13.6 | Integration |
| E9 | Process killed after upload → excluded on the next run | §13.2, §13.6 | Integration: simulated kills, and a real SIGKILL of a child process after the intent, after `uploaded`, after `selected`, and inside the promotion write (D-159); with the process-based TV worker, a real SIGKILL of the runner while its worker runs (Phase 5) |
| E10 | History, current artwork, and preview change only after `selected` | §4.1, §12.4 | Integration |
| F1 | Temporary files are removed after success | §14 | Integration |
| F2 | Temporary files are removed after failures | §14, §4.2 | Failure matrix |
| F3 | Temporary storage does not grow | §14, §13.1 | Byte bounds |
| F4 | History survives restarts and upgrades | §13.2, §13.3 | Unit + Phase 8 |
| F5 | Corrupt history is recovered | §13.2 | Unit |
| F6 | Cache limits are enforced | §13.4 | Unit |
| F7 | The preview is never used as a local source | §9.3 | Unit (three guards) |
| G1 | One copy-paste card (card + script + timer helper, plus a post-run automation if needed; Q-09) | §16.3 | Phase 6 draft; entity IDs after Phase 8; public slug in Phase 9 |
| G2 | The card shows the latest preview | §16.3 | Phase 8 |
| G3 | A tap starts the app | §16.3 | Phase 8 (admin and non-admin) |
| G4 | The loading state returns to idle | §7, §16.3 | Deadline tests + Phase 8; the normative 150 s timer indicator |
| G5 | **Release-blocking:** the preview is fresh in repeated live tests | §16.3, D-140 | Phase 8 repeated tests; mechanism recorded |
| G6 | No `configuration.yaml` edit, config-folder mapping, SSH, or manual files | §16.3 | Documentation review + Phase 8 |
| H1 | Every bounded loop and fallback is unit-tested | §20.4 | Branch gate |
| H2 | No live services in integration tests | §20.1 | Socket guard |
| H3 | No secrets in logs | §18, §19 | Redaction tests (parent and workers) |
| H4 | Licenses and notices are complete | Inventory; §17.3 | The image's own inventory (D-171); inventory check as a publish gate |
| H5 | No predecessor material | §2.1, §20.3 | Phase 7 provenance review |
| H6 | License approved before publication | D-102 (accepted) | Gate |
| H7 | Live run only after approval | §23 | Gate |
