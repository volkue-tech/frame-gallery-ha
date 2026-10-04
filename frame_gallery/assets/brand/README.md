# Frame Gallery brand mark

The user approved the **Living Gallery Window** design on 2026-10-04:
a warm-ivory gallery frame and a folded coral/ochre ribbon on a midnight-blue
tile. It was generated independently with the built-in Imagegen tool; no
competitor image, museum artwork, Samsung mark or Home Assistant mark was used
as an input. The refinement changed the outside corners to alpha transparency.
No font or wordmark is included.

`frame-gallery-mark.png` is the approved 1254 × 1254 RGBA master. It is copied
byte-for-byte to `icon.png` and `logo.png` by `scripts/app_images.py`.
The icon is square as required by Home Assistant. The documentation recommends
128 × 128 for icons and about 250 × 100 for logos but permits other logo sizes
and aspect ratios. Both presentation files deliberately retain the approved
master pixels and alpha instead of a new AI rendering (the tile center is almost
opaque, alpha 254/255; exterior corners are fully transparent). They are repository
presentation assets, not executable app code or bundled museum images; the
runtime Docker stage does not copy this folder.

This provenance is not a trademark registration, clearance search or claim that
no similar mark exists anywhere. The full original design prompt and the
transparent-edge refinement are saved alongside the master.

Official format guidance:
https://developers.home-assistant.io/docs/apps/presentation/
