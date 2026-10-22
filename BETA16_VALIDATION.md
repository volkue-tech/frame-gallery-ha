# Beta 0.1.0b16 — correct recorded state-response parsing

This is the narrow D-244/D-245 protocol bugfix. No Home Assistant or television
connection, installed start/update, card/script edit or configuration change is
part of this release task. Existing per-TV associations, options, default-off
switches, privileges, dependencies and complete card YAML remain unchanged.

## Corrected behaviour

The opted-in same-socket state reader now distinguishes outgoing
`get_artmode_status` / `get_current_artwork` from the recorded incoming
`artmode_status` / `current_artwork` events. b15 incorrectly required replies
to repeat the request name, rejecting valid correlated responses and potentially
leaving a known artwork unconfirmed. Only these two explicit pairs are accepted;
an arbitrary matching request ID or mirrored request name is not sufficient.

Every present `id` / `request_id` must match the fresh pending nonce. Mode must
be on before and after two equal content-ID replies on the same Art connection.
Existing five-second/64-frame, minimum-60-second cadence, 480-cycle/eight-hour,
standby/HA-off/cancellation, identity and per-TV archive guards are unchanged.
No new getter, connection, retry, thumbnail, image/power/mode command or keepalive.

## Recorded offline regressions

Four already captured device replies from 17 October are retained as sanitized,
literal test fixtures, independently of the production mapping. Their original
body keys, event/mode/content/matte values and id-only correlation shape remain;
only nonce/client identifiers change. No token, key or thumbnail is included.
The local replay verifies fixture fidelity against the original capture and
tests the original responses, not just the sanitized copies.

Before the source fix, the initial regressions produced 21 failures/24 passes.
The corrected parser accepts all four original replies, rejects all four wrong
request-name controls, and completes the coherent four-getter cycle. There are
48 new recorded-protocol cases plus two installed-library/socketpair variants.
Wrong/cross-command events, stale/missing/conflicting correlation, unknown
requests, mode/navigation/standby, cancellation and finite bounds are covered.

Seven separate in-memory negative controls restore the wrong reply-name
comparison or remove coherence, correlation, policy, Art-off recovery,
backpressure spacing or single-thumbnail guards. Each produces the expected
behaviour-test failure; production and test source files remain unchanged.
An additional eight-hour virtual session with the corrected reply fixture
completes 479 coherent reads / 1,916 GETs, with a minimum 60-second interval
and no outgoing request at the terminal deadline. This is simulation, not a
device connection or hardware-sleep result.

The exact versioned host gates passed 6,095 tests / 16 existing platform skips in
56.94s. Ruff/format and strict host/Linux typing passed for 308 files. Whole
line/branch coverage is 100% (11,705 statements / 2,826 branches); the mandatory
subset is 100% (8,937 / 2,088). Native results below were separately observed
and independently checked; they are not inferred from the host result.

These are protocol/build checks, not a new physical no-wake/sleep guarantee or
proof that a particular currently displayed image has a saved association.

## Exact source and runtime snapshot

- Frozen source commit: `542f30c36a66aece9834c458cd4ea2da474947a5`.
- Matching public source release `420043679`, asset `663757966`:
  `frame-gallery-sources-0.1.0b16.tar`, 581,724,160 bytes,
  SHA256 `ca942d9a12f187503647b66dde8ee1e8c7519d2d411ed652c0650093f157bfce`.
  Full anonymous download, every-member hash/manifest check and exact clean
  project-snapshot preflight passed BEFORE any image distribution.
- Runtime tree: 118 files,
  SHA256 `a97a8f3596d13c5b9918fb9626a8fd2f729dd8e53977e236c95c65eb0ca43541`.
- Exact [native publisher run 39676527130](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/39676527130).
  All five jobs completed successfully: approval, two native validators and
  two actual-image publishers. Native Linux Python 3.14.8 hosts reported
  aarch64 and x86_64 respectively, not Intel emulation on this ARM Mac.

## Independently checked native artifacts

The four authenticated downloads were bounded, hash/provenance/content checked
against this exact run and source. Each passed 6,103 production tests with
eight root-only skips and eight separately executed root checks. Each measured
13 preparation cases twice under the real 1 GiB address-space limit, and
150 inspections with zero failures.

| Artifact | Artifact ID | ZIP bytes | SHA256 | Peak VM MiB | Slowest preparation s |
| --- | --- | --- | --- | --- | --- |
| native-aarch64-validation | 12382329599 | 23781 | `efdf8df80b9bd71d769e226272fbf78294d16afaa5c776a15783a289b5fc039a` | 771.6 | 2.33 |
| native-amd64-validation | 12383351579 | 23739 | `6f1dc4472128a6056fc84c4643aae710286c90b84976219bcd15c9b82e06c0d3` | 768.0 | 3.16 |
| beta-aarch64-evidence | 12383359103 | 21083 | `10b1c9db2669d1ba6dd6a12f7d5738b74478e2761dd19a77950442099a1102c3` | 771.6 | 2.26 |
| beta-amd64-evidence | 12384582043 | 21081 | `af54a8e8878646622394a36fe2d23b4f3cfba1a43c23e9d54a26c5dacae15d8b` | 768.0 | 2.75 |

## Exact public images and signatures

- ARM: `ghcr.io/volkue-tech/frame-gallery-ha-aarch64@sha256:f82cee3417d1b83b45a8f909e9127c8d4cdf048fc68f5fa9fa2ee350b4fdcb22`.
- Intel: `ghcr.io/volkue-tech/frame-gallery-ha-amd64@sha256:553582103a522a8821d25b1e3d45f7e89647ab9c3f40a4bc4706bf573e0b5611`.

Both immutable references match their publisher artifacts and anonymous tag
manifests. Fresh credential-free pulls and isolated read-only/non-root imports
with network disabled verified the exact 118-file runtime hash, corrected
recorded-reply parser, unchanged 1,000-work catalogue and default-OFF settings.
The local Intel import uses emulation; native Intel evidence is the separate
hosted run and checked archives above.

Independent Cosign checks bind each digest to this exact source and
`https://github.com/volkue-tech/frame-gallery-ha/.github/workflows/publish.yml@refs/heads/codex/commons-default`,
with issuer `https://token.actions.githubusercontent.com`. A workflow's own
signature check was not used as the sole independent verification.

## Publication handoff and limits

[Public prerelease v0.1.0b16](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/v0.1.0b16),
release420465314, targets frozen source542f30c36a66aece9834c458cd4ea2da474947a5
and was created only after all checks above. Both one-time approval values
were saved/read back as `DISABLED_AFTER_0.1.0b16`. This 17-document handoff
preserves every runtime/config/workflow/dependency byte and all16 complete
code/YAML fences. Final public main/Store/38-file readback and exact broker
exit follow the handoff commit and are recorded in local closure receipts.

No HA/TV connection, installed update/start or card/script change was made.
Previous releases, source packages and per-TV mappings remain compatible.
The misleading checking-card wording remains a separate task; this narrow fix
does not silently edit users' existing cards. Native Terminal control is
prohibited by the available access path; completed native windows are not
falsely claimed closed or cleared by quitting Terminal.
