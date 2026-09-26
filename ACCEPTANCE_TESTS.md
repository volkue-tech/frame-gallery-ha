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
- [ ] Static color, museum, and style/period filters work without helper entities.
- [ ] A valid helper value overrides its static value.
- [ ] A missing or unavailable helper falls back to the static value.
- [ ] Invalid filter values are rejected or normalized predictably.
- [ ] Landscape-only and fit-mode defaults preserve the full artwork.

## C. Candidate selection

- [ ] Combined color, museum, and style/period filters are applied together.
- [ ] Portrait and square candidates are rejected when landscape-only is enabled.
- [ ] Previously sent identifiers are skipped across app restarts.
- [ ] Strict near-16:9 selection never exceeds its probe budget.
- [ ] The complete run never exceeds its configured total deadline by more than a small shutdown allowance.
- [ ] A restrictive filter combination can fall back from strict near-16:9 to an eligible landscape work.
- [ ] When no candidate exists, the app exits cleanly and does not call the television upload operation.
- [ ] Provider network, parsing, and empty-result failures do not create infinite retries.

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
- [ ] A successful upload enters exactly one provider-qualified identifier into history.
- [ ] Starting the app again does not resend the same work while unused eligible works remain.

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
- [ ] A newly published preview is displayed without remaining stuck on the prior browser-cached image.
- [ ] The documented setup requires no `configuration.yaml` edit.

## H. Quality and compliance

- [ ] Unit tests cover every bounded loop and fallback branch.
- [ ] Integration tests use mocks or independently authored fixtures and require no live provider or television.
- [ ] Logs contain no secrets or private API payloads.
- [ ] Dependency licenses and notices are complete.
- [ ] No code, tests, documentation, assets, or structure from excluded predecessor projects appear in the repository.
- [ ] The chosen project license is approved by the user before publication.
- [ ] A full live run is completed on Home Assistant Green only after explicit user approval.

