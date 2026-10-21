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

The exact versioned host gates passed6095 tests/16 existing platform skips in
56.94s. Ruff/format and strict host/Linux typing passed for308 files. Whole
line/branch coverage is100% (11705 statements/2826 branches); the mandatory
subset is100% (8937/2088). Native ARM/Intel, source/image/signature and public
promotion results must be recorded after their actual completion, not assumed
from the host result.

These are protocol/build checks, not a new physical no-wake/sleep guarantee or
proof that a particular currently displayed image has a saved association.
