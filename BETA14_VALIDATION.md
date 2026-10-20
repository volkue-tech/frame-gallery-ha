# Beta 0.1.0b14 — current-state synchronization candidate

This report records offline evidence, not a new hardware test. Installed b13
remains stopped; no Home Assistant/TV connection, app/card/script mutation or
power/mode/image command is part of this development/publication task.

## Behaviour and opt-in

`current_state_refresh` is a separate experimental switch, OFF by default,
requiring background mode and an already granted pinned-device Art session.
It reads mode/current/current/mode coherently on the same socket at most once
per minute, with fresh correlation, equal image IDs and mode-on at both ends.
Unknown images have no invented title. Menu, same-image, changed-image and
unknown bounded notifications recover without a new upload or connection.
Standby/HA-off/cancellation/refusal/closed transport does not blindly reconnect.

Attempts share five seconds/64 frames, minimum60s spacing, at most480 in the
existing eight-hour session. There is no new client/socket, thumbnail, setter,
power/mode command or client keepalive. The current-state age is90s; installed
native cards and send script remain compatible and unchanged. Read requests can
affect automatic sleep; offline/native tests cannot prove firmware/no-wake safety.

## Observed host evidence

- Unchanged full check.sh:6031 passed,16 platform skips in50.96s.
- Ruff/306 formatted files, strict host and Linux typing:passed.
- Whole line/branch coverage:100%,11674 statements/2818 branches.
- Mandatory subset:100%,8910 statements/2082 branches.
- Actual pinned library over socketpair:one URL, one initial thumbnail,
  existing five initial getters followed by only four coherent same-socket
  getters. A queued standby produces no refresh getter.
- Actual entry simulates known/unknown current-state metadata; per-device
  archive, wrong-ID/device/evidence/stale guards remain tested.
- In-memory negative controls: removing equal-ID coherence fails1 assertion;
  correlation removal fails2; policy removal fails1. Source files unchanged.

Earlier style, assertion-regex and missing-coverage failures are retained under
build/current-artwork-b14-release. They were fixed, not skipped or weakened.
The b13 rejected raw notification was not retained; no claim to reproduce its
unknown event name. The normal remote-menu workflow is now explicitly covered
synthetically, not certified on hardware.

## Remaining publication gates

Frozen source, corresponding licensed-source archive, native ARM/Intel actual
images, root/memory checks, artifact provenance, anonymous image/import and
independent signatures remain required before public app/Store promotion.
Exact commits, run/asset IDs and hashes are recorded only after observed results.
