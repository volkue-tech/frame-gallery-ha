# Independent-development and licensing boundaries

This document is a project rule, not legal advice.

## Purpose

The project must be an independently authored implementation of user-defined functionality. Acknowledging inspiration does not authorize copying unlicensed material. The new project's license can apply only to material the project authors own or are entitled to license.

## Excluded predecessor material

Agents and contributors must not inspect or use as implementation references:

- `vivalatech/homeassistant-addons`;
- `volkue-tech/homeassistant-addons` and its pull-request branches;
- `gijsvdhoven/homeassistant-addons`;
- `ow/samsung-frame-art`;
- prior local Frame Art repositories, patches, tests, logs containing source excerpts, documentation, icons, logos, or generated diffs.

Do not copy, translate, mechanically rewrite, paraphrase, or imitate any excluded source code, tests, documentation, comments, identifiers, file layout, configuration text, icons, or screenshots.

## Permitted inputs

- Requirements authored by the user and recorded in this repository.
- Independently observed product behavior expressed as black-box inputs and outputs.
- Current official Home Assistant documentation.
- Publicly documented Samsung protocols or APIs.
- Documentation and public APIs of artwork providers.
- Properly licensed third-party packages approved and recorded in `DECISIONS.md`.
- General software engineering knowledge and standard algorithms.

## Third-party dependencies

Before adding a dependency, record:

- exact package and source;
- version or version constraint;
- SPDX license identifier;
- whether it is dynamically used, bundled, modified, or redistributed;
- required notices, source offers, or other obligations;
- reason it is needed.

The current `samsungtvws` package may be evaluated. Its current published license must be verified at implementation time. No source from a predecessor wrapper may be copied.

## Artwork and provider data

- Do not bundle third-party artworks in application source code or runtime/release images.
- User-authorized documentation screenshots of the current independent app may depict verified CC0 artwork. Keep them outside the runtime build context, remove private UI details, record the capture and official rights source, and provide an artwork credit. This does not authorize bundling a provider collection, default artwork, predecessor assets, or restricted images.
- Download artwork only at runtime on the user's Home Assistant system.
- Retain only the selected preview, bounded metadata cache, and identifiers required for duplicate prevention.
- Preserve provider attribution or rights information when required and practical.
- Provider connectors must respect applicable access terms, request limits, and technical restrictions.
- The existence of a publicly reachable image does not imply a right to redistribute it.

## Branding

- Use a distinct project name and original artwork.
- Do not imply endorsement by or affiliation with Samsung, Google, Microsoft, museums, Home Assistant, or predecessor maintainers.
- Product documentation may factually describe compatibility.

## Proposed project license

Apache License 2.0 is recommended for independently authored project code because it is permissive and includes an explicit patent grant. This is not final. The user must approve the license before a `LICENSE` file or public release is created.

Third-party components remain under their own licenses and are not relicensed by this project.

## Attribution language for a future README

Suggested wording, subject to review:

> Inspired by community experimentation around Home Assistant and Samsung Frame art-mode automation. Frame Gallery is an independent implementation and does not incorporate source code or assets from those predecessor projects.

Do not use wording that implies an upstream license grants rights when no such license has been confirmed.
