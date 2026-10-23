# 0.1.0b18 — release candidate validation

The user authorized native ARM/Intel checks and green-gated personal publication
on 2026-10-23. This document is a candidate record, not a completed release claim.

## Candidate scope

NEW default-off `standby_resume` permits one bounded read after a continuously
observed 30-second HA off interval and a fresh on stable for 10 seconds. It needs
background mode and the existing Samsung entity. Old saved resume/refresh flags
remain suspended. No startup-on or periodic TV read is enabled. A private atomic
attempt/auth budget enforces six attempts per rolling hour and at least 60 seconds
between attempts across ordinary restarts; invalid state fails closed. Manual
private-data deletion/restore is not protected against historical rollback.

Finite reasons and complete optional native status-card guides in five languages
distinguish standby, passive waiting, expired proof, stopped service and failure.
Existing complete examples, scripts, dependencies, privileges and IDs are retained.
Unknown artworks remain unidentified; current captions/previews still require
fresh exact-device/image proof. Static image confirmations continue to expire.

## Observed local evidence

The versioned host gate is retained locally for this release; the earlier D-250
gate passed 6,354 tests with 16 unchanged Linux/root platform skips, 323-file strict
host/Linux typing and 100% whole/mandatory line and branch coverage. The recorded
20-hour eligibility replay and three guard-removal negative controls are described
in [STANDBY_RESUME_VALIDATION.md](STANDBY_RESUME_VALIDATION.md). These are offline
software checks, not native image results or a physical no-wake guarantee.

## Mandatory publication gates — pending in this frozen candidate

Matching sources must be public and anonymously checked before any image
distribution. Both native validators and both actual publisher images must pass;
all four exact evidence archives, anonymous immutable images and independent
source/workflow-bound signatures must be checked before app release/Store handoff.
Exact identifiers and observed results will be recorded in a runtime-identical
documentation handoff only after those gates pass.

No Home Assistant or TV connection, installed app operation or live card/script
change is authorized by this release. Existing installed state is not modified.
Connection-side effects on physical Samsung firmware remain unresolved; the new
opt-in is experimental and OFF by default. A running app must observe the whole
cycle; it cannot recover while stopped or blindly retry a lost session while HA
stays on. Native CI cannot establish physical standby or no-mode-switch behavior.
