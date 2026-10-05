# Wikimedia Commons selection

> Local development branch only: **not available in the published 0.1.0b2 app**.
> A new validated beta is required before selecting this source on the Green.

## What you get

50 curated landscape reproductions: colourful abstraction, expressionism,
geometric compositions and a few quieter works of classical modernism.
Not a promise of contemporary, still-copyrighted artists.

In the source-enabled release, select **Artwork source → wikimedia_commons** in
the app's Configuration tab, save, and use your existing dashboard button.
No account, API key, new helper or extra dashboard extension. Optional title/
artist display continues to use the existing Text helper.

Commons requests identify Frame Gallery with the project contact
`volkue+commonsapi@gmail.com`. This is not your own email or an API key; users
need not configure it. This contact is recorded in project source/documentation
and is sent in request headers to Commons and its allowed image hosts.

**For these works:** keep Landscape only on and Fit mode `contain` (do not crop).
None is near-exact 16:9; the normal bounded fallback can use them with margins.
Turning strict TV format off avoids the search for a 16:9 match that this initial
selection cannot supply. Do not use `cover` with strict format on: that mode
has no safe shape fallback. Source selection does not change your options.

Department, period, style and colour filters are not supported for Commons in
this first implementation. Set them to `any`; otherwise the log reports them
as ignored. Curated labels are not an artist/style-filter API.

## Quality, storage and history

The app asks Commons for a JPEG up to 3840 pixels wide and uses the returned
dimensions, never an oversized original as a fallback. Some sources are between
3000 and 3840 pixels wide: a 4K output canvas does not create additional detail.

Only the small metadata catalogue is bundled. An actual run downloads only its
candidate image into existing bounded scratch storage, prepares the TV image,
and cleans up. The current preview and bounded history remain, not a growing
downloaded library. Original paper/support margins are deliberately retained.

Already uploaded/sent works are excluded by the existing history/ledger.
After all 50 have been sent, the run ends cleanly with no new match; it does not
silently repeat them. Choose another source or your own media then.

## Rights and provenance

Researched on 2026-10-05. Public-domain/CC0 labels were checked on Commons;
these statements are **not worldwide legal clearance**. Rights can vary by
jurisdiction. Images are not relicensed under this project's Apache licence.
Open each linked file page for its rights, source and collection information.

The app rechecks current rights, the curated file/page identity and pinned
original-upload hash. Missing, changed, restricted or unverifiable files are
skipped pending a curation update. CC BY/CC BY-SA works requiring attribution
are deliberately outside this first catalogue.

Two proposed Delaunay files with unresolved US-tag notes were replaced by
Klee's *Before the Town* and *Deep Pathos*, whose pages explicitly document
PD-old-auto-expired. Historical research remains separate from the runtime
catalogue. No files from a predecessor project were consulted.

Eight artists: Wassily Kandinsky (12), Paul Klee (16), Robert Delaunay (4), Franz Marc (4), August Macke (5), Theo van Doesburg (2), Ernst Ludwig Kirchner (4), Paul Signac (3).

## The 50 works

Dimensions below describe the source originals, not a claim of TV-tested detail
or exact 16:9. The runtime downloads a bounded rendition.

| # | Artist | Artwork / Commons file page | Original pixels |
| --- | --- | --- | --- |
| 1 | Wassily Kandinsky | [Gelb-Rot-Blau](https://commons.wikimedia.org/w/index.php?curid=38658125) | 4780 × 3074 |
| 2 | Wassily Kandinsky | [Composition VIII](https://commons.wikimedia.org/w/index.php?curid=77963326) | 3400 × 2380 |
| 3 | Wassily Kandinsky | [Composition VII](https://commons.wikimedia.org/w/index.php?curid=178839132) | 7015 × 4661 |
| 4 | Wassily Kandinsky | [Impression III (Concert)](https://commons.wikimedia.org/w/index.php?curid=29848354) | 3957 × 3085 |
| 5 | Wassily Kandinsky | [Oriental](https://commons.wikimedia.org/w/index.php?curid=63967344) | 4660 × 3271 |
| 6 | Wassily Kandinsky | [Eisenbahn bei Murnau](https://commons.wikimedia.org/w/index.php?curid=64165646) | 4579 × 3353 |
| 7 | Wassily Kandinsky | [Inner Alliance](https://commons.wikimedia.org/w/index.php?curid=81370185) | 3076 × 2647 |
| 8 | Wassily Kandinsky | [Improvisation III](https://commons.wikimedia.org/w/index.php?curid=68718058) | 4000 × 2899 |
| 9 | Wassily Kandinsky | [Improvisation 27 (Garden of Love II)](https://commons.wikimedia.org/w/index.php?curid=57396257) | 3907 × 3338 |
| 10 | Wassily Kandinsky | [Improvisation XIV](https://commons.wikimedia.org/w/index.php?curid=75969059) | 4000 × 2348 |
| 11 | Wassily Kandinsky | [Little Painting with Yellow (Improvisation)](https://commons.wikimedia.org/w/index.php?curid=81502097) | 4096 × 3186 |
| 12 | Wassily Kandinsky | [Untitled (Study for Composition VII, First Abstract Watercolor)](https://commons.wikimedia.org/w/index.php?curid=40213893) | 8001 × 6123 |
| 13 | Paul Klee | [Bird Landscape](https://commons.wikimedia.org/w/index.php?curid=60907495) | 4000 × 2843 |
| 14 | Paul Klee | [Libido of the Forest](https://commons.wikimedia.org/w/index.php?curid=60907266) | 4000 × 3115 |
| 15 | Paul Klee | [Kristall-Stufung](https://commons.wikimedia.org/w/index.php?curid=116266220) | 6539 × 5279 |
| 16 | Paul Klee | [Lovers](https://commons.wikimedia.org/w/index.php?curid=60909655) | 3811 × 2309 |
| 17 | Paul Klee | [Heitere Gebirgslandschaft](https://commons.wikimedia.org/w/index.php?curid=14618617) | 3000 × 2099 |
| 18 | Paul Klee | [Temple Gardens](https://commons.wikimedia.org/w/index.php?curid=57858012) | 3809 × 3085 |
| 19 | Paul Klee | [All Souls' Picture](https://commons.wikimedia.org/w/index.php?curid=60909664) | 3811 × 2623 |
| 20 | Paul Klee | [Episode at Kairouan](https://commons.wikimedia.org/w/index.php?curid=60907263) | 3811 × 2668 |
| 21 | Paul Klee | [Municipal Jewel](https://commons.wikimedia.org/w/index.php?curid=60907260) | 4000 × 2109 |
| 22 | Paul Klee | [Yellow Harbor](https://commons.wikimedia.org/w/index.php?curid=60907365) | 4000 × 2723 |
| 23 | Paul Klee | [Abstract Trio](https://commons.wikimedia.org/w/index.php?curid=60907399) | 3811 × 2591 |
| 24 | Paul Klee | [Cold City](https://commons.wikimedia.org/w/index.php?curid=60909673) | 4000 × 2883 |
| 25 | Paul Klee | [Still Life](https://commons.wikimedia.org/w/index.php?curid=57396122) | 4000 × 2997 |
| 26 | Paul Klee | [Landscape with Bluebirds](https://commons.wikimedia.org/w/index.php?curid=86755478) | 4096 × 3166 |
| 27 | Robert Delaunay | [Nature morte portugaise](https://commons.wikimedia.org/w/index.php?curid=48694617) | 3982 × 3183 |
| 28 | Robert Delaunay | [Window on the City No. 3](https://commons.wikimedia.org/w/index.php?curid=58345593) | 4082 × 3390 |
| 29 | Robert Delaunay | [Windows Open Simultaneously, 1st Part, 3rd Motif](https://commons.wikimedia.org/w/index.php?curid=40026322) | 3000 × 1468 |
| 30 | Robert Delaunay | [Carousel of Pigs](https://commons.wikimedia.org/w/index.php?curid=40181676) | 3000 × 2530 |
| 31 | Franz Marc | [Weidende Pferde I](https://commons.wikimedia.org/w/index.php?curid=63967587) | 4617 × 3102 |
| 32 | Franz Marc | [Deer in a Monastery Garden](https://commons.wikimedia.org/w/index.php?curid=29848498) | 3889 × 2917 |
| 33 | Franz Marc | [Drei Tiere](https://commons.wikimedia.org/w/index.php?curid=5213136) | 3000 × 2252 |
| 34 | Franz Marc | [Liegender Hund (Russi)](https://commons.wikimedia.org/w/index.php?curid=149769813) | 9474 × 7599 |
| 35 | August Macke | [Zoologischer Garten I](https://commons.wikimedia.org/w/index.php?curid=64064543) | 4795 × 2747 |
| 36 | August Macke | [Indianer auf Pferden](https://commons.wikimedia.org/w/index.php?curid=64064766) | 4591 × 3355 |
| 37 | August Macke | [Garten am Thunersee](https://commons.wikimedia.org/w/index.php?curid=10711362) | 4482 × 3708 |
| 38 | August Macke | [Sonniger Garten](https://commons.wikimedia.org/w/index.php?curid=163922085) | 4000 × 3024 |
| 39 | August Macke | [Sandgrube](https://commons.wikimedia.org/w/index.php?curid=158615407) | 4000 × 2925 |
| 40 | Theo van Doesburg | [Counter-composition XVI](https://commons.wikimedia.org/w/index.php?curid=3817033) | 4629 × 2544 |
| 41 | Theo van Doesburg | [Card Players](https://commons.wikimedia.org/w/index.php?curid=21930785) | 5340 × 4293 |
| 42 | Ernst Ludwig Kirchner | [Czardas Dancers](https://commons.wikimedia.org/w/index.php?curid=21925604) | 9660 × 7356 |
| 43 | Ernst Ludwig Kirchner | [Interieur mit Maler](https://commons.wikimedia.org/w/index.php?curid=64580978) | 4330 × 2542 |
| 44 | Ernst Ludwig Kirchner | [Eisenbahnüberführung Löbtauer Straße in Dresden](https://commons.wikimedia.org/w/index.php?curid=103327113) | 4029 × 3098 |
| 45 | Ernst Ludwig Kirchner | [Russisches Tänzerpaar](https://commons.wikimedia.org/w/index.php?curid=177602382) | 8560 × 7315 |
| 46 | Paul Signac | [Portrait de Félix Fénéon (Opus 217)](https://commons.wikimedia.org/w/index.php?curid=489515) | 6229 × 4973 |
| 47 | Paul Signac | [Cassis, Cap Lombard (Opus 196)](https://commons.wikimedia.org/w/index.php?curid=21931618) | 6633 × 5328 |
| 48 | Paul Signac | [Antibes](https://commons.wikimedia.org/w/index.php?curid=80519258) | 4096 × 2886 |
| 49 | Paul Klee | [Before the Town](https://commons.wikimedia.org/w/index.php?curid=60907526) | 3811 × 3045 |
| 50 | Paul Klee | [Deep Pathos](https://commons.wikimedia.org/w/index.php?curid=60907632) | 4000 × 3133 |

## Technical references

- [MediaWiki Imageinfo API](https://www.mediawiki.org/wiki/API:Imageinfo)
- [Wikimedia API usage guidelines](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_API_Usage_Guidelines)
- [Commons reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia)
- [CC0 dedication](https://creativecommons.org/publicdomain/zero/1.0/)

No image file, raw HTML or arbitrary category query is bundled. The provider
uses five metadata records per paced request, existing network guards and hard
deadlines. Native container, image download/decode and approved Green/TV tests
are still required before release; synthetic tests are not substituted for them.
