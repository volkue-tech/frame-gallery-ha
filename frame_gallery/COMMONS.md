# Wikimedia Commons: 1000 curated works

Available from **0.1.0b6**. A broad selection of paintings, graphic art,
illustration and artistic photography, with **one optional colour wish**.
No account or API key is needed. Commons is the default for new installations;
updates preserve your existing source choice.

## Start simply

Choose **Artwork source → wikimedia_commons**, keep **Landscape only** on,
**Image fit = contain**, and **Colour wish = any**. Start the app once or tap
your existing dashboard preview. The whole artwork is preserved by default;
no new helper or dashboard extension is required.

Sources are at least **3000 pixels wide** and within **2.5% of 16:9**.
The unchanged **Prefer 16:9** option is stricter, approximately 1%; 566 of the
1000 original source ratios meet it. Leave it on for the closest matches or
turn it off for the whole selection. Bounded shape fallback stays within your
chosen colour. Small margins can remain; `cover` can crop and is not recommended.

![Actual historical Commons preview with optional artwork information](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/dashboard-commons.png)

*Historical b3 Green screenshot: Theo van Doesburg,
[Counter-composition XVI](https://commons.wikimedia.org/w/index.php?curid=3817033).
This is not a screenshot of the new colour dropdown or a new hardware test.
The 1000 works have not been physically TV-tested work by work.*

## Choose a colour

The app configuration offers `any`, Red, Orange, Yellow, Green, Blue, Purple,
Pink, Brown, Beige, Gray, Black and White. A noticeable area of that colour
(about 5%) qualifies; it need not be dominant. A blue-yellow work can therefore
match either group. These are approximate families, not exact HEX matches.

Colours are analysed during catalogue preparation, not by downloading many
images on your Green. Profiles bind to the pinned source upload. TV margins
are not counted as artwork colours. Full palettes, distributions and up to
three significant groups are retained for future combinations; this update
exposes only **one colour at a time**.

With no new match, the run stops cleanly and keeps the previous TV image,
preview and artwork information. It never silently falls back to another
colour. Previously sent/uploaded works remain excluded. Fixed search budgets
mean one unsuccessful run is not an exhaustive scan of all 1000 works.

The [complete native colour-card guide](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_COLOUR.md)
is available in English and [Deutsch](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_COLOUR.de.md). It
adds an optional UI-created dropdown helper, reusing your camera, timer and
script. No HACS or custom card is needed. The minimal standard card still works.

**Colour applies only to Commons.** Chicago, Cleveland and local images remain
available but report a colour wish as ignored. Commons does not offer museum
department, period, artist or art-style filters in this release.

## What changed, and what stays

The active catalogue has **1000 distinct works from 560 artist labels**:
344 unchanged baseline entries plus 656 additions. After manual sample review,
the user approved temporarily holding 56 unresolved baseline entries and
replacing them. This is not a claim that every held source is cropped. Seven
other reviewed additions remain curatorial reserves.

The historical 400-work manifest, all 663 accepted additions and all 1063
research colour profiles are retained. Holds do not delete sources, change
upload pins or reset history. Every ID remains `commons:<pageid>`; previously
sent works do not become new after updating. Update in place, without uninstalling.

- [Active 1000-work source manifest](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/research/commons-1000-selection-2026-10-10.json)
- [Source/profile/runtime freeze audit](https://github.com/volkue-tech/frame-gallery-ha/blob/main/research/commons-1000-freeze-audit-2026-10-10.json)
- [Archived b5 collection and research notes](https://github.com/volkue-tech/frame-gallery-ha/blob/main/frame_gallery/COMMONS_400_ARCHIVE.md)

Only compact metadata and colour-match labels enter the app image. Original
artworks, preview caches and full research palettes are not bundled in runtime.
Each run uses bounded temporary storage, then cleans up. It retains the current
preview and bounded history, not 1000 downloaded originals. Discovery still
uses at most ten paced five-record metadata requests per run, within existing
time and worker limits; sent works are omitted from those requests.

## Rights and evidence

The active sources have reviewed public-domain or CC0 evidence (629 / 371).
CC BY/CC BY-SA prospects remain separate research reserves, not runtime entries.
A photograph's licence alone does not clear a contemporary artwork it depicts.
Commons labels and research are **not worldwide legal clearance**; jurisdictions
differ. The app rechecks current rights, exact page/file identity and pinned
upload hash at every run. Changed, restricted or unverifiable files are skipped.
Artwork is not relicensed under the project's Apache licence.

Local quality gates, source/palette audits and actual thumbnail reviews are
documented separately from native release checks and historical Green tests.
The b6 native validators and actual publisher images, public sources, anonymous
pulls and independent signatures passed; see the
[release checks](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA6_VALIDATION.md).
No new Green or physical TV observation is claimed. The API contact
`volkue+commonsapi@gmail.com` goes only to allowed Commons/image hosts in request
headers; it is not an end user's email or an API key.
