# Frame Gallery 0.1.0b3 validation

Recorded on 2026-10-05. Both images were published and independently verified;
the existing public Green app was updated and two Commons runs were observed.
The user physically confirmed the second work on the TV.

## Exact runtime and source

Runtime/source commit: `15644bf0f42b24e89621020fce9f511942237832`.
[Publisher run](https://github.com/volkue-tech/frame-gallery-ha/actions/runs/37351792462)
uses the frozen `codex/commons-curated` branch. Later documentation-only main
commits do not change the built runtime or corresponding-source snapshot.

All five jobs succeeded. Both actual publishers repeated the native suite
(4,997 passed / five root-only skips), all five root checks and all 26 real
1 GiB preparation measurements, plus 150 inspections with zero failures.
Their maximum measured address spaces were 765.5 MiB (ARM) and 761.8 MiB
(Intel), longest preparations 2.16 s and 2.29 s respectively.

- ARM: `ghcr.io/volkue-tech/frame-gallery-ha-aarch64@sha256:f54ab393aa330897bb05cafe01a190ffeec360616cd901cf349faf9fa8d3864b`
- Intel: `ghcr.io/volkue-tech/frame-gallery-ha-amd64@sha256:34864a0817fa060e4df757475a5800f43486b6db5593b31b99d8196ab58e4db1`

Anonymous pulls verified actual platforms, b3 version and the exact runtime
revision. Each tag and digest returned identical manifest bytes. Independent
Cosign 3.1.3 verification passed against issuer
`https://token.actions.githubusercontent.com`, the exact runtime SHA above,
and certificate identity
`https://github.com/volkue-tech/frame-gallery-ha/.github/workflows/publish.yml@refs/heads/codex/commons-curated`.
The certificates identify the frozen candidate ref, not `main`.

Both downloaded actual-publisher evidence ZIPs matched their public SHA256s:
ARM `5cfb48964d4f182d8693b602bcca8f7779c6af6057c5bab58c51e6f280c4d949`,
Intel `808374a5796aea06d5a4626a46004d031dd3a3f4a219152ecd7fe21e09a46e31`.
The ZIPs' published digests match the independent manifest results. Neither
previous-version tag was overwritten.

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

## Approved in-place Green update and deliveries

Before any mutation, authenticated Firefox inspection confirmed the existing
public b2 app, preview, script, timer and artwork-information helper. The app
was stopped, automatic startup/updates were off, and the previous AIC delivery
remained visible. Its latest storage summary reported zero scratch/temporary/
run files. The normal app-info API route returned 401 and was not retried;
the authenticated UI was used instead of denied-endpoint retries.

After successful native publication and independent image verification, main
was fast-forwarded to expose b3. The Store's **Check for updates** found the new
version. The app was updated from b2 to b3 with **keep the previous version's
backup** enabled, without uninstalling, SSH, data reset or configuration.yaml
edits. The UI confirmed installed/latest version 0.1.0b3. Backup retention was
requested; a backup restore was not tested.

A fresh configuration-page reload showed the new German descriptions. Only
source (`wikimedia_commons`) and strict shape (`false`) were changed. TV address,
landscape selection, `contain`, black margins and the existing timer/information
helper IDs were preserved. Saved options remain supported; no card, script or
helper was recreated or edited. Startup and automatic updates remain off.

| Start (UTC) | Observed result |
| --- | --- |
| 18:45:25 | `delivered`, 19.1 s; `commons:10711362`, August Macke, **Garten am Thunersee**. Started through the existing script; timer countdown was observed. All four TV protocol markers passed. Preview and artist/title/source rendered in the existing native dashboard stack. |
| 18:47:28 | `delivered`, 11.3 s; `commons:3817033`, Theo van Doesburg, **Counter-composition XVI**. Started by tapping the existing dashboard image. Its loading note appeared, then ended. Selection reported `seen=3 excluded=1 evaluated=2`, explicitly skipping the previously delivered Commons work. Preview and caption both changed. |

Both runs reported loading-timer completion acknowledged. Every observed
storage bucket reported zero temporary files and zero run directories; scratch
was `ok` with zero files/bytes. State remained seven small files (2,811 then
3,012 bytes), cache two files/418 bytes, preview exactly one latest image
(2,119,381 then 1,238,340 bytes), not an accumulating download library.
Quarantine and TV buckets were reported `unavailable`, not verified empty.
This is bounded app-run evidence, not an audit of all Green storage or a
byte-for-byte comparison of every pre-existing history entry.

The user confirmed that the second work's black diagonals and blue/yellow/red
planes were actually visible on the TV. The first work has protocol/dashboard
evidence only. Commons remains selected with landscape/contain and strict shape
off for the user's continued testing; unrelated configuration was untouched.

![Actual b3 Commons preview and optional information card](docs/images/dashboard-commons.png)

The native Firefox screenshot selected only these cards before capture; no
address bar, sidebar, account, calendar or camera token is included. Artwork
provenance and current-rights verification are recorded in the
[visual inventory](docs/images/README.md#commons-beta-screenshot).

Both one-time publisher variables were set to `DISABLED_AFTER_0.1.0b3` and
read back in the personal GitHub UI after the successful run. Previous b1/b2
releases, images and corresponding sources were retained.

No claim covers every TV model, fresh pairing, backup restoration, every
artwork's visual quality, or all storage on the Green. Exhausting all 50 works,
changed/revoked source rights, transport failures and finite strict-format
fallback are covered by synthetic tests, not induced in this live pass.
There was no new Core restart or destructive TV cleanup.

## User feedback

The user found Macke's side margins too large. Its 4,482 × 3,708 original is
landscape (about 1.21:1), but containment on 16:9 leaves about 16% of screen
width on each side. Landscape-only currently means wider than tall, not a
minimum widescreen ratio. A broader-ratio filter is a possible follow-up;
the frozen, validated b3 runtime was not changed after publication.

## Final documentation quality gate

After the Green observations and user confirmation were incorporated,
`bash scripts/check.sh` passed on the normal macOS host: Ruff check/format,
strict mypy (248 files), 4,991 tests passed and 11 platform skips. Whole-package
coverage was 100% for 9,420 statements and 2,052 branches; the required subset
was 100% for 7,728 statements and 1,708 branches. This checkpoint changed only
documentation and the native dashboard screenshot, not the frozen runtime.
