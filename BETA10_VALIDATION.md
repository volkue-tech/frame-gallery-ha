# Beta 0.1.0b10 — event-sequence recovery and safe diagnostics

Release candidate, 2026-10-18. The user authorizes publication after actual
green native gates. Nothing in this document claims a completed release,
installed-app update, new TV test or universal no-wake guarantee.

## Scope and compatibility

D-237 distinguishes incomplete sequences of strictly recognized notifications
from fatal protocol/transport failures. Incomplete order or pending expiry
clears all current attribution and pending parts, retaining only the same
bounded receiver. A new whole matching five-second triple is required; no late
halves, discarded event, bare ID or duplicate can create/renew a caption.
Unknown/malformed/stale/future input, off/standby, identity/resource/publication
failures still stop without reconnect. Fixed allowlisted failure codes identify
the failing stage without raw messages, credentials or exception bodies.

No dependency, provider, catalogue, filter, stored association, helper/card ID,
protected app permission or media mapping change. No new query, thumbnail,
client ping, network profile or automatic resume. Background stays default OFF.
Existing last-upload cards stay separate from the optional current-information
card; no installed HA app, TV or card changes are part of this release round.

## Evidence and limitations

Eight authored restart regressions fail on unmodified b9. Offline fixed tests
cover incomplete order/timeout, no late-half/same-ID confirmation, a later valid
cycle, known/unknown per-device metadata and immutable stores, bounded logging
and rejection of arbitrary diagnostic strings. The pinned-library socketpair
replay has one channel, five initial getters, one initial thumbnail and zero
post-baseline application requests. These are offline results, not raw captured
proof of what happened during the b9 live failure.

The saved HA trace on 2026-10-18 confirms a successful initial current caption,
normal expiry, then unavailable at 19:54:55 CEST. The production log has no raw
event/failure reason. The exact cause remains unproven. No new hardware/sleep
pass, all-model/firmware support or guarantee that every failure is fixed.

Full unchanged host gates passed 5773 tests/16 genuine Linux-only skips, strict
host/Linux typing over 296 files and 100% whole/mandatory line/branch coverage.
Two sandbox-only group/setgid failures were retained and the complete unmodified
suite rerun outside that sandbox without exclusions. Repeat after versioning.

## Release gates (pending)

- [ ] Freeze a clean personal exact commit after versioned host checks.
- [ ] Publish matching hash-verified source package; anonymous full preflight.
- [ ] Native aarch64 and amd64 validators and actual publisher images.
- [ ] Exact evidence archive provenance/hash/content, real isolation/root and
  1-GiB image preparation/inspection gates on both architectures.
- [ ] Anonymous immutable-image pulls/imports and independent Cosign signatures.
- [ ] Public app prerelease and only then Store/main handoff.
- [ ] Disable both one-time approval variables and end memory-only token broker.

All release receipts are retained locally under
`build/current-artwork-b10-release`; no private credentials belong in this report.
