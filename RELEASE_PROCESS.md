# Releasing a reviewed beta

This is the maintainer procedure. Users install the pre-built app through Home
Assistant's app store; they do not run these commands or edit HA configuration.
STATUS/TASKS remain the authoritative current status. A committed workflow is
not evidence that an image has been published or an installation has passed.

## b16 recorded-response parser correction

b16 is the narrow protocol correction to the existing optional state refresh:
pair outgoing getters with the observed artmode_status/current_artwork reply
events, retaining every fresh-ID, same-socket, mode/ID and finite safety guard.
No new option, dependency, privilege, storage format or card/script migration.
Recorded real-reply fixtures must fail against the old request-name comparison;
matching synthetic fakes alone are not sufficient protocol evidence.

The [b16 validation report](BETA16_VALIDATION.md) records the exact source,
native ARM/Intel validators and actual publisher image/root/memory suites,
four independently verified artifacts, public images/imports and signatures.
[Matching b16 sources](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b16)
must be fully anonymously verified before image distribution. Neither this
procedure nor a green native build establishes a new physical no-wake result.
Publish no installed update/start or HA/TV call. Before handback, disable and
read back both exact approvals, verify final public main/Store/release content
and end the memory-only broker with exact PID-absence evidence. Never pre-claim
those later operational closures in an earlier commit.

## b15 optional same-connection synchronization scope

The separate `current_state_refresh` option is experimental, default OFF and
requires background mode. It permits bounded mode/ID coherence checks at most
once per minute over an established Art socket, not a new connection, upload or
power/mode command. Menu/Art-off clears captions while retaining mode-only checks;
fresh Art Mode on is required before IDs, and unknown art gets no borrowed title.
Physical standby, observed HA off and a closed socket still stop the session.
Read requests can affect automatic sleep; offline evidence cannot certify firmware
or no-wake behaviour. Keep existing cards, scripts and installed state unchanged.

For this documentation handoff, the [b15 validation report](BETA15_VALIDATION.md)
must cite the actual final source, native ARM/Intel validator and publisher
artifacts, anonymous images/imports, independent signatures and final main/release
cross-check. Observed b15 run39562816594/all five jobs and four native archives,
both anonymous exact-image imports and independent signatures passed; app
prerelease419307088 targets frozen source ab9e65cb313a8ef05560f182e958a441bc8a44c6.
Both exact approvals were disabled/read back. After the17-document handoff is
pushed to main, record the final anonymous38-file/main/Store readback and exact
broker-PID exit locally before handback; do not claim future closure in a commit.
Do not infer green results or hardware safety from the scope description.
[Matching b15 sources](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b15)
must be verified publicly before image distribution. Retain b14 only as its
source-only intermediate; it was not an app/image/Store release.

## b13 startup/send arbitration scope

The b13 handoff changes only startup ordering: a fixed ten-second window gives an
accepted new-artwork command priority, consuming the remaining initial read
opportunity even on `no_match` or delivery failure. Standalone initial sync and
later genuine off-to-on recovery remain available under their existing guards.
An arbitrarily delayed script can arrive after the window and must first stop
an already running receiver. Keep existing cards and scripts unchanged.
The [b13 validation report](BETA13_VALIDATION.md) must record the observed host,
native ARM/Intel, source, evidence, image and signature checks before handoff;
do not infer green results or hardware safety from the scope description.
The [matching b13 source release](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b13)
must precede image distribution. This release does not establish the cause of
the reported physical switch into TV mode or a general no-wake/mode-safety fix.
No live HA/TV action, app start/update or card/script change is part of publication.

## Before enabling publication

1. Finish the engineering licence assessment and the source/notices obligations
   for the actual build. Preserve the limits/risks recorded in DECISIONS; do not
   describe this as an independent legal opinion. No OCI label calls the whole
   image Apache-2.0. Read `SOURCE_AND_REBUILD.md`.
2. Select an explicit numbered beta version such as `0.1.0b1`; update the own
   runtime/project metadata, lock/generated app metadata as needed, changelog
   and notices. Run all quality gates; commit with the personal identity only.
3. Assemble a matching clean-commit source package with the tracked assembler.
   Record its emitted SHA256/length/commit; independently verify the archive.
   Never upload a failed/partial or earlier-commit candidate.
4. Publish the package as `frame-gallery-sources-<VERSION>.tar` in the own
   **source-only** `sources-v<VERSION>` GitHub release. Its text must say that
   the public app-install candidate is still under verification. Confirm an
   unauthenticated download and hash. This source asset must already exist before
   any image is distributed; a private/draft source release does not qualify.
5. Only after the preceding checks, set the personal repository's variables
   `FRAME_GALLERY_RELEASE_APPROVED_SHA` and
   `FRAME_GALLERY_RELEASE_SOURCE_SHA256` to that exact reviewed commit/archive.
   Unset variables deliberately disable publication. Approving a different
   commit requires fresh assessment/gates; neither variable is a credential.

## Run the manual workflow

Run **Publish reviewed beta images** on `main`, with the matching beta version.
For reviewed candidates such as 0.1.0b6 through 0.1.0b13, 0.1.0b15 and 0.1.0b16, the narrowly allowed
`codex/commons-default` branch can instead publish
the exact approved candidate before its app metadata is merged into `main`.
This prevents store users being offered a version whose image is still missing.
Repository, exact-commit/source-hash, native validation and non-overwrite gates
remain identical. Signatures identify the actual workflow branch; b6 through b13, b15 and b16 use
`https://github.com/volkue-tech/frame-gallery-ha/.github/workflows/publish.yml@refs/heads/codex/commons-default`.
Historical b3/b4/b5 used
`https://github.com/volkue-tech/frame-gallery-ha/.github/workflows/publish.yml@refs/heads/codex/commons-curated`.
Historical b2 used `codex/artwork-info` and retains that certificate identity;
it is not the currently allowed candidate publisher branch.
After both images/signatures pass, fast-forward the same candidate to `main`;
do not overwrite an older image or claim new Green UX validation before testing.
The workflow first checks version/approval, calls same-commit native ARM/Intel
validation with read-only permissions, then each native publisher verifies every
source member and validates the actual runtime image it will upload. Its
LABEL-only annotation cannot change application/filesystem layers.

Only publishing jobs obtain registry-write/OIDC permission. They use the ephemeral
GitHub workflow token, so the personal fine-grained push token does not need
registry privileges. Existing version tags, ambiguous registry responses and
401/403 stop the operation. No `latest` tag or test image is published.

Cosign 3.1.3 is hash-pinned on each architecture and runs only in the release
job. It keylessly signs each immutable digest and verifies the own workflow
certificate identity/issuer. The signing certificate, workflow identity and
digest are public transparency evidence; no Home Assistant or TV secret is sent.
Preserve `published-digest.txt` and the actual native checks for each architecture.

Version tags are kept non-overwriting by this workflow; a registry administrator
can still move them. The signed **digest** is the immutable image identity.
If one architecture/signature step fails after the other image was pushed,
preserve the partial result and investigate. Do not blindly delete or overwrite
the tag to make a rerun green. Its first registry-tested run `37159551965`
completed successfully for both architectures at runtime commit `d736c7a`.

Check package visibility rather than assuming its initial state. In the first
release, the repository-linked packages were already public; no visibility
change was needed. If necessary, explicitly make only the two own Frame Gallery
packages public. Verify anonymous pulls/signatures of their exact digests before
attempting a public HA installation. See the official
[GitHub registry authentication/visibility instructions](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

## Public installation and announcement

Add the correct pre-built `image` mapping to generated app metadata; it must
select the published architecture/version, not a locally built development app.
Verify a clean, separate installation from the public repository on the approved
Green without configuration edits/SSH requirements. Observe the actual public
slug; test pairing scope, normal delivery, preview refresh/loading completion,
no-match/fallback/cleanup and enforced isolation without resetting other state.
Publish complete dashboard YAML using that observed slug, not a guessed prefix.

Only then finalize the one-click link, beginner documentation, beta stage,
known limitations and beta announcement/release notes. Supervisor supports
`experimental`, `stable` and `deprecated`, not a `beta` stage: keep `experimental`
for this numbered beta. Link or attach the exact
source package and keep it available with the matching images. Retain source
for at least three years after the last matching distribution (longer if the
method requires it). Clear the approval variables afterward so later main
changes cannot accidentally reuse an earlier approval.

The initial hardware test used an already-authorized TV; fresh pairing was not
reset. Chicago returned HTTP 403 on the tested network; Cleveland/local media
worked. Colour filtering was not offered in those historical runs. The b6 colour
filter and b7 artist/five-language release passed their separately recorded native
and independent public-image/signature checks; no new hardware/frontend-language
test is inferred. See BETA6_VALIDATION.md and BETA7_VALIDATION.md.
Do not turn those observations into
claims of universal TV/source compatibility, source-byte reproducibility,
patent clearance or legal counsel's approval.
