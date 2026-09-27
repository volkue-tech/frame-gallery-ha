# Acceptance tests

These are product-level acceptance criteria. Unit and integration test details should be derived independently during implementation.

## A. Installation and packaging

- [ ] A public test repository can be added through Home Assistant's repository UI or one-click link.
- [ ] Home Assistant Green discovers the app without SSH or local file copying.
- [ ] Home Assistant Green installs the pre-built `aarch64` image.
- [ ] An `amd64` image is built from the same release source.
- [ ] Installation requires no `configuration.yaml` change.
- [ ] The app exposes understandable option names and descriptions in the Home Assistant UI.

## B. Configuration

- [ ] A missing television IP prevents start with a clear validation message.
- [ ] Static source, department, style/period, and colour filters work without helper entities.
- [ ] A valid helper value overrides its static value.
- [ ] A missing or unavailable helper falls back to the static value.
- [ ] Invalid filter values are rejected or normalized predictably.
- [ ] Landscape-only and fit-mode defaults preserve the full artwork.
- [ ] A television address that is not an RFC 1918 private IPv4 literal (including link-local `169.254.0.0/16`, loopback, unspecified, multicast, broadcast, and container or Supervisor network addresses) is rejected with a clear validation message.
- [ ] A filter the selected source does not support is visibly reported as unsupported (option description, log, and run record) and never silently claimed to work.

## C. Candidate selection

- [ ] Combined department, style/period, and colour filters supported by the selected source are applied together.
- [ ] Portrait and square candidates are rejected when landscape-only is enabled.
- [ ] Previously sent identifiers are skipped across app restarts.
- [ ] Strict near-16:9 selection never exceeds its budget of 30 remote dimension requests, and local header inspection stays within its separate allowance.
- [ ] The complete run never exceeds its 120-second default total deadline by more than a small shutdown allowance.
- [ ] A restrictive filter combination can fall back from strict near-16:9 to an eligible landscape work.
- [ ] When no candidate exists, the app exits cleanly and does not call the television upload operation.
- [ ] Provider network, parsing, and empty-result failures do not create infinite retries.
- [ ] Art Institute of Chicago candidates are public-domain (CC0) works only.
- [ ] Cleveland Museum of Art candidates are CC0 / open-access records only, and the downloaded image is the documented print JPEG, never the original TIFF.
- [ ] A run without a matching candidate finishes cleanly within 70 seconds by default.

## D. Image preparation

- [ ] A landscape image with a non-16:9 aspect ratio appears completely on a 3840 × 2160 canvas in `contain` mode.
- [ ] Default `contain` mode does not crop any artwork pixels.
- [ ] Black margins are used by default where necessary.
- [ ] `cover` mode crops only when explicitly selected.
- [ ] EXIF-rotated input is oriented correctly.
- [ ] RGB, RGBA, palette, and grayscale inputs produce a television-compatible JPEG.
- [ ] Excessive dimensions, pixel counts, or download sizes are rejected safely.
- [ ] The preview bytes correspond to the processed television image.

## E. Television behavior

- [ ] A successful run uploads one image and selects it as active art.
- [ ] Pairing or authorization requirements are reported clearly.
- [ ] Connection timeouts and television rejection terminate cleanly.
- [ ] Failed uploads do not enter the image into sent history.
- [ ] A successful run (upload and selection confirmed) enters exactly one provider-qualified identifier into history.
- [ ] Starting the app again does not resend the same work while unused eligible works remain.
- [ ] Upload succeeded but selection was refused: the work enters the TV-upload exclusion ledger, not the sent history, and it is not uploaded again on the next run.
- [ ] Upload succeeded but the connection was lost during selection: the work enters the TV-upload exclusion ledger, and it is not uploaded again on the next run.
- [ ] The process was killed after the upload: the work is excluded on the next run (upload ledger or uncertainty quarantine) and is not uploaded again on the next run.
- [ ] Confirmed sent history, current artwork, and dashboard preview change only after the television confirms selection.

## F. Cleanup and persistence

- [ ] Temporary downloads are removed after success.
- [ ] Temporary downloads are removed after provider, decode, processing, and upload failures.
- [ ] Repeated runs do not grow temporary storage.
- [ ] History survives app restarts and version upgrades.
- [ ] A corrupt history file is quarantined or recovered without crashing the app.
- [ ] Metadata caches enforce documented size and age limits.
- [ ] The generated preview cannot be selected as local source artwork.

## G. Dashboard documentation

- [ ] Documentation contains one complete copy-and-paste-ready dashboard card.
- [ ] The card displays the latest preview.
- [ ] Tapping the card starts the app.
- [ ] The loading indicator always returns to idle after success, clean no-match, or failure.
- [ ] **Release-blocking:** across repeated live tests on Home Assistant Green, each newly delivered image is displayed without a stale browser cache, using the single documented, UI/API-based refresh mechanism.
- [ ] The documented setup requires no `configuration.yaml` edit, no configuration-folder mapping, no SSH step, and no manual file modification.

## H. Quality and compliance

- [ ] Unit tests cover every bounded loop and fallback branch.
- [ ] Integration tests use mocks or independently authored fixtures and require no live provider or television.
- [ ] Logs contain no secrets or private API payloads.
- [ ] Dependency licenses and notices are complete.
- [ ] No code, tests, documentation, assets, or structure from excluded predecessor projects appear in the repository.
- [ ] The chosen project license is approved by the user before publication.
- [ ] A full live run is completed on Home Assistant Green only after explicit user approval.

## Amendment log

- **2026-09-26: Phase 1 Codex review of commit `d42adf5`, with user decisions.**
  - New items were appended at the end of their sections, so the position-based IDs used in `ARCHITECTURE.md` Appendix A stay stable.
  - Added: B7 (local IPv4 address), B8 (unsupported filters visibly reported), C9–C10 (AIC and CMA rights and renditions), C11 (no-match within 70 s), and E7–E10 (TV-upload exclusion ledger scenarios).
  - Reworded in place:
    - B2 and C1: distinct filter dimensions.
    - C4: 30 remote dimension requests.
    - C5: 120 s deadline.
    - E5: history changes only after upload *and* selection are confirmed.
    - G5: preview freshness, now release-blocking.
    - G6: no configuration edits of any kind.
- **2026-09-26: Codex final gate review of commit `9352e77`, with user decisions.**
  - Reworded in place: B7 now requires an RFC 1918 private IPv4 literal and names the rejected ranges (Q-12, D-125). No IDs changed.

