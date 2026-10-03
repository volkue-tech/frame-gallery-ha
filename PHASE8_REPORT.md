# Supervised Green validation — in progress

Date: 2026-10-03. Codex performed the checks below; none is a completed TV
delivery or museum test. Phase 8 is not complete.

## Approval and scope

The user explicitly approved installing Frame Gallery as a separate test app
on HA Green and then sending Chicago/Cleveland images to the TV. Existing
apps, dashboards, scripts, integrations and `configuration.yaml` stay unchanged.
Nothing is published. No predecessor source or implementation was inspected.

## Observed installation

- Candidate: `a0b1ce734485aae8bb67dfce90b8e281fd61c34c`; runtime `f42f72a`.
- Core REST: HA 2026.9.4 reachable. A Supervisor proxy request returned 401;
  no blind retry or rights change. Privileged app installation used the
  already-running Terminal & SSH web terminal, within the approved scope.
- Read-only TV REST: Samsung GQ50LS03TAUXZG, Frame support true, power on.
- Green storage: about 15.9 GB available before the build.
- This Terminal & SSH version exposes the local app directory at
  `/local_apps`, not `/addons`. The new target did not already exist.
- A `git archive` of the candidate's `frame_gallery` directory was staged,
  without `.venv` or local caches. Only the development display name, slug,
  and AppArmor profile name differ: **Frame Gallery (Test)**,
  **frame_gallery_dev**. Runtime source files are unchanged.
- The first Mac tar transfer added 272 AppleDouble `._*` files. BuildKit
  failed at `compileall`: `._*.py` files contained NUL bytes. The real
  Python source files were unaffected. The first copy was moved, recoverably,
  to `/share/frame-gallery-phase8-mac-metadata-backup`.
- Repackaging with `COPYFILE_DISABLE=1` and `--exclude='._*'` removed the
  metadata from the archive. HA verified its SHA256 before extraction:
  `bae00b324b8ef340af9b67001f43606860eba176edb1edc8116b73444dd97798`.
- Store reload and `ha apps install local_frame_gallery_dev` succeeded.
  Supervisor reports version 0.1.0.dev0, state stopped, protected true,
  AppArmor `profile`, boot manual, watchdog false; no host networking.
  This does not yet prove AppArmor runtime attachment or enforcement.
- Each transfer served only its named archive over the local network and
  stopped after one download. No persistent relay or credentials in files.

## Prepared first test

- `/media/frame_gallery` did not exist before the test preparation.
- A project-generated synthetic 3840 × 2160 JPEG with coloured edge marks
  is now at `/media/frame_gallery/library/phase8-test-edges-3840x2160.jpg`.
  No third-party artwork was used, and no existing media was overwritten.
- Only the new app's options were saved: TV address `192.168.178.30`,
  source local_media, department/style/colour any, landscape and strict
  format true, contain, black margins, debug logging. Supervisor returned OK.
- The TV start command was **not executed**: parallel Firefox navigation
  displaced the terminal before submission. A dedicated Chrome test tab
  was opened instead and is waiting for the user's HA sign-in. No existing
  dashboard action was intentionally invoked.

## Still pending

Local quality gates were rerun after the documentation changes: Ruff and both
strict mypy passes clean, 4,600 tests passed, 8 Linux/root-only checks skipped,
100 % line and branch coverage, exit 0. The initial sandboxed run passed 4,598
tests but failed the two real supplementary-group/setgid checks; both passed
in a targeted unsandboxed rerun, followed by the complete passing unsandboxed
gate. No runtime code or test was changed to bypass those checks.

First local run; pairing and Art API version; upload/selection; live museum
requests and restrictive-filter fallback; actual preview freshness; history
and upload ledger; stop timing and cleanup; Green memory/time measurements;
AppArmor attachment/audit; dashboard entities and exact user-approved setup.

Keep the development app and its data. Removal, publication, and changes to
existing HA configuration require separate direction. Small transfer archives
remain in Terminal & SSH's `/tmp`; the first source copy remains in `/share`
as noted above. These are deployment artifacts, not artwork-download buildup.
