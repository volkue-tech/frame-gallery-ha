# Frame Gallery 0.1.0b3 validation

Recorded on 2026-10-05. This checkpoint records completed checks only. Image
publication, the in-place Green update and Commons deliveries remain pending.

## Exact runtime and source

Runtime/source commit: `15644bf0f42b24e89621020fce9f511942237832`.
[Publisher run](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/37351792462)
uses the frozen `codex/commons-curated` branch. Later documentation-only main
commits do not change the built runtime or corresponding-source snapshot.

[Matching sources](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b3):
172 retained upstream archives plus the exact clean project snapshot;
522,219,520 bytes; SHA256
`84eeaf5076d2880e76aaf509eaf3a59e468590804c2998ba6a3d2c67c292ef83`.
An independent anonymous download matched the hash and passed the exact-source
and archive-member preflight. No artwork, HA state or credentials are included.
Previous releases and matching source packages remain available.

## Native validation evidence

Both native validation jobs passed. Each actual image passed 4,997 non-root
tests with five root-only skips, followed by all five separate root isolation
checks passing. Both native hosts passed 26 image-preparation measurements
under the real 1 GiB `RLIMIT_AS`, plus 150 inspections across ten workers with
zero failures. The ARM result is not an emulated substitute for Intel.

| Native validation | Largest measured address space | Longest preparation | Evidence ZIP SHA256 |
| --- | --- | --- | --- |
| aarch64 | 765.5 MiB | 2.16 s | `66de6c679351605e28b8533a88819cd02947ffd4289be221ba56565056dfb761` |
| amd64 | 761.8 MiB | 2.67 s | `b71416e4cf013fc12bbb7ef929c306566c7d67a9c06a642e42a96db5c444f8e5` |

Both downloaded evidence ZIPs matched their public artifact hashes. Local ARM
validation also passed separately. Whole-package coverage is 100% line and
branch, 9,420 statements / 2,052 branches. Dependency pins and component notices
are unchanged; there is no new dependency for Commons.

The documentation checkpoint's full local gate passed on the normal Mac host:
4,991 passed / eleven expected Linux/root skips, Ruff/formatting and strict
host/Linux mypy over 248 files. A sandboxed attempt first failed two existing
setgid/group tests; the same unmodified suite passed outside that sandbox.
No code/test relaxation or new skip was introduced.

The metadata-only production adapter check accepted 50/50 curated works in
10.35 seconds over ten requests. This checks identities, sizes and current
CC0/public-domain metadata; it is not a decode or visual-TV test of all 50.

## Green baseline and remaining checks

Before any mutation, authenticated Firefox inspection confirmed the existing
public b2 app, preview, script, timer and artwork-information helper. The app
was stopped, automatic startup/updates were off, and the previous AIC delivery
remained visible. Its latest storage summary reported zero scratch/temporary/
run files. The normal app-info API route returned 401 and was not retried;
the authenticated UI is used instead of denied-endpoint retries.

Still pending: both actual publisher checks/signatures, anonymous tag/digest
verification and pulls, Store update, in-place Green upgrade, two Commons
deliveries, preview/caption/loading/cleanup observations, disabling publisher
approval variables and publication of the final beta announcement.

Physical display confirmation must be recorded separately from a successful
TV `selected` protocol marker. No claim covers every TV model, fresh pairing,
backup restoration, every artwork's visual quality, or all storage on the Green.
