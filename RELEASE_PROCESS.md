# Releasing a reviewed beta

This is the maintainer procedure. Users install the pre-built app through Home
Assistant's app store; they do not run these commands or edit HA configuration.
STATUS/TASKS remain the authoritative current status. A committed workflow is
not evidence that an image has been published or an installation has passed.

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
For 0.1.0b3 and 0.1.0b4, the narrowly allowed `codex/commons-curated` branch can instead publish
the exact approved candidate before its app metadata is merged into `main`.
This prevents store users being offered a version whose image is still missing.
Repository, exact-commit/source-hash, native validation and non-overwrite gates
remain identical. Signatures identify the actual workflow branch; b3/b4 use
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
worked. Colour filtering is not offered. Do not turn those observations into
claims of universal TV/source compatibility, source-byte reproducibility,
patent clearance or legal counsel's approval.
