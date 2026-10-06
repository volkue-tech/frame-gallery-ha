# Wikimedia Commons selection

> **Next release, not published yet:** 400 curated near-widescreen works from 299 artist labels.
> Public **0.1.0b4** contains 166 works; every one is retained unchanged in this expansion.
> Update the existing app; do not uninstall it or reset its history.

## What you get

A broad, colourful selection of modern classics, landscapes, still lifes,
seascapes and older paintings. Each source is at least 3000 pixels wide and
within 2.5% of the 16:9 screen ratio. The next catalogue adds 234 visually
reviewed works without removing or repinning any of the 166 b4 entries.
Commons is first/default for new installations in that next release; saved
source choices on upgrades stay unchanged.
No account, API key, new helper or dashboard extension is needed.

Select **Artwork source → wikimedia_commons**, keep **Landscape only** on and
**Image fit = contain** to preserve the whole artwork. Leave **Prefer 16:9** on
for the closest matches, or turn it off for the whole curated selection.

**2.5% selection is not the same as the app's strict 16:9 preference.** That
preference still means about 1%; 152 of the prepared 400 sources meet it
(b4: 67 of 166). The existing
bounded fallback can show the other near-widescreen works without cropping.
Small margins, or margins already present in a source scan, can remain.
There is no new configuration option and no change to your saved options.

![Actual Commons dashboard preview with optional artist/title information](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/dashboard-commons.png)

*Historical b3 Green screenshot: Theo van Doesburg,
[Counter-composition XVI](https://commons.wikimedia.org/w/index.php?curid=3817033).
This work remains unchanged in the next catalogue. The 400-work selection
has not been TV-tested work by work. See the [b3 live-test scope](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA3_VALIDATION.md).*

Department, period, style and colour filters are not supported for Commons.
Set them to `any`; unsupported filters are reported as ignored. Curated artist
labels are not an artist/style-filter API.

## Quality, storage and history

The app obtains a JPEG rendition no wider or taller than 3840 pixels; it never
uses an oversized original as a fallback. A 4K output canvas does not create
detail absent from the source. Very large originals remain on Commons.

Only small metadata entries are bundled. Each run downloads its candidate into
bounded temporary storage and cleans up. It retains the current preview and
bounded history, not 400 downloaded originals. Existing history IDs stay
`commons:<pageid>`: a previously sent work does not become new after updating.

Discovery samples at most ten paced five-record metadata requests per run,
within the existing request/time limits. Permanently sent works are omitted
from those requests. This does not promise an exhaustive catalogue scan in
each run. With no eligible new work, the app ends cleanly rather than retrying
forever or automatically recycling already sent art.

## Rights and research

The [400-work metadata manifest](research/commons-400-selection-2026-10-06.json)
retains all 166 b4 pins and adds 234 works. The unchanged
[original 200-proposal manifest](research/commons-wide-selection-2026-10-06.json)
preserves the 34 older deferred cases for source-rights, scan/work proportions
or PNG/TIFF format. Those cases are not silently restored to fill a quota.
The 1937 Beckmann proposal remains excluded because its displayed licence
template conflicts with the artwork date. The adapter remains JPEG-only.

Public metadata searches, source-page hashes/revisions, known physical-size
checks, actual thumbnail-review decisions, 26 reserve works and the expanded
scrolling preview are saved in a separate dated private local research folder.
No original artwork files are bundled or stored there. Visible big frames,
paper surrounds, details and poor reproductions were rejected; unknown historic
crop remains a limitation of thumbnail review, not a guarantee of completeness.

The existing production gateway and Commons adapter accepted **400/400** in
eight bounded metadata-only passes, 74.45 seconds total, on 2026-10-06.
[Receipt](research/commons-400-adapter-audit-2026-10-06.json).
This is not one normal app run, an image-decode test, a native release-image
validation or a TV test. Normal runs retain their ten-request discovery cap.

Commons public-domain/CC0 labels and source-page evidence were reviewed on
2026-10-05/06. This is **not worldwide legal clearance**; jurisdictions differ.
The app rechecks current rights, exact file/page identity and pinned upload
hash on every run. Missing, restricted, changed or unverifiable files are
skipped. Additional CC BY/CC BY-SA claims remain outside this selection.
Artwork is not relicensed under the project's Apache licence.

The project contact `volkue+commonsapi@gmail.com` is sent to Commons and its
allowed image hosts in request headers. It is not a user's email or an API key.

## The 400 prepared works

Original source dimensions below are not a claim of TV-tested detail.
The runtime downloads bounded renditions, not the listed originals.
Entries 1–166 retain the released b4 pins; entries 167–400 are new and unreleased.

| # | Artist | Artwork / Commons file page | Original pixels |
| --- | --- | --- | --- |
| 1 | Theo van Doesburg | [Counter-composition XVI](https://commons.wikimedia.org/w/index.php?curid=3817033) | 4629 × 2544 |
| 2 | Wassily Kandinsky | [Milder Vorgang / Gentle Event](https://commons.wikimedia.org/w/index.php?curid=84632826) | 4000 × 2287 |
| 3 | Edvard Munch | [Zwei Menschen. Die Einsamen (Reinhardt-Fries)](https://commons.wikimedia.org/w/index.php?curid=176674544) | 4435 × 2500 |
| 4 | Pierre Bonnard | [Plage](https://commons.wikimedia.org/w/index.php?curid=65361933) | 3200 × 1768 |
| 5 | Maurice Denis | [L’église rose – Tilloloy](https://commons.wikimedia.org/w/index.php?curid=180643370) | 4456 × 2472 |
| 6 | Childe Hassam | [California](https://commons.wikimedia.org/w/index.php?curid=65236294) | 3200 × 1775 |
| 7 | Vincent van Gogh | [Montmartre: Windmills and Allotments](https://commons.wikimedia.org/w/index.php?curid=39846917) | 7824 × 4296 |
| 8 | Camille Pissarro | [La Moisson / The Harvest](https://commons.wikimedia.org/w/index.php?curid=21897337) | 4178 × 2316 |
| 9 | Pierre-Auguste Renoir | [Le sentier dans la forêt, trois personnages](https://commons.wikimedia.org/w/index.php?curid=76401733) | 3200 × 1835 |
| 10 | Paul Gauguin | [Three Tahitian Women](https://commons.wikimedia.org/w/index.php?curid=57673290) | 3811 × 2198 |
| 11 | Paul Cézanne | [Krug und Früchte auf einem Tisch](https://commons.wikimedia.org/w/index.php?curid=149144) | 3200 × 1833 |
| 12 | Paul Cézanne | [Plate with Fruit and Pot of Preserves](https://commons.wikimedia.org/w/index.php?curid=67540714) | 4096 × 2255 |
| 13 | Pierre-Auguste Renoir | [Apples and Lemons on a Cloth](https://commons.wikimedia.org/w/index.php?curid=67540512) | 4096 × 2354 |
| 14 | Pierre-Auguste Renoir | [Strawberries and Almonds](https://commons.wikimedia.org/w/index.php?curid=67540290) | 4096 × 2274 |
| 15 | Pierre-Auguste Renoir | [Pomegranates](https://commons.wikimedia.org/w/index.php?curid=67540189) | 4096 × 2248 |
| 16 | Pierre-Auguste Renoir | [Nature morte aux roses](https://commons.wikimedia.org/w/index.php?curid=76362525) | 4000 × 2213 |
| 17 | Pierre-Auguste Renoir | [Mandarines et tasse](https://commons.wikimedia.org/w/index.php?curid=76401773) | 3200 × 1823 |
| 18 | Pierre-Auguste Renoir | [Pomegranate and Figs](https://commons.wikimedia.org/w/index.php?curid=67540557) | 4096 × 2337 |
| 19 | Frederic Edwin Church | [The Meteor of 1860](https://commons.wikimedia.org/w/index.php?curid=124030464) | 6000 × 3408 |
| 20 | Frederic Edwin Church | [Cotopaxi](https://commons.wikimedia.org/w/index.php?curid=4766414) | 5076 × 2874 |
| 21 | Frederic Edwin Church | [The Icebergs](https://commons.wikimedia.org/w/index.php?curid=25702837) | 4000 × 2266 |
| 22 | Thomas Moran | [Grand Canyon of the Colorado River](https://commons.wikimedia.org/w/index.php?curid=21885969) | 5665 × 3192 |
| 23 | Thomas Moran | [Great Blue Spring, Yellowstone](https://commons.wikimedia.org/w/index.php?curid=30592536) | 4827 × 2730 |
| 24 | James McNeill Whistler | [Note in Red and Violet: Nets](https://commons.wikimedia.org/w/index.php?curid=185171326) | 4096 × 2296 |
| 25 | James McNeill Whistler | [Blue and Silver, Dieppe](https://commons.wikimedia.org/w/index.php?curid=119873988) | 3520 × 1943 |
| 26 | Winslow Homer | [Fox Hunt](https://commons.wikimedia.org/w/index.php?curid=8825940) | 5000 × 2788 |
| 27 | Winslow Homer | [Boy with Anchor](https://commons.wikimedia.org/w/index.php?curid=24834545) | 6828 × 3820 |
| 28 | Winslow Homer | [Surf at Prout’s Neck](https://commons.wikimedia.org/w/index.php?curid=38429749) | 3000 × 1689 |
| 29 | Winslow Homer | [The Watcher, Tynemouth](https://commons.wikimedia.org/w/index.php?curid=24175357) | 4230 × 2379 |
| 30 | Winslow Homer | [Woodland Stream](https://commons.wikimedia.org/w/index.php?curid=118810806) | 7780 × 4326 |
| 31 | Winslow Homer | [Towing the Boat](https://commons.wikimedia.org/w/index.php?curid=114234017) | 3000 × 1727 |
| 32 | John Singer Sargent | [On his Holidays, Norway](https://commons.wikimedia.org/w/index.php?curid=173692244) | 6987 × 3939 |
| 33 | John Singer Sargent | [Cliffs at Deir el Bahri, Egypt](https://commons.wikimedia.org/w/index.php?curid=57366268) | 3811 × 2123 |
| 34 | Joaquín Sorolla | [Velas, Playa de Valencia](https://commons.wikimedia.org/w/index.php?curid=149657860) | 3200 × 1828 |
| 35 | Joaquín Sorolla | [Paisaje marino](https://commons.wikimedia.org/w/index.php?curid=19456667) | 3200 × 1808 |
| 36 | Giovanni Segantini | [Eine Ziege mit ihrem Jungen](https://commons.wikimedia.org/w/index.php?curid=34254029) | 4014 × 2270 |
| 37 | Giovanni Segantini | [Bagpipers of Brianza](https://commons.wikimedia.org/w/index.php?curid=21897036) | 4309 × 2383 |
| 38 | Paul Gauguin | [Mahna no Varua Ino (The Devil Speaks)](https://commons.wikimedia.org/w/index.php?curid=82042536) | 4000 × 2295 |
| 39 | Tom Thomson | [Decorative Landscape – Blessing by Robert Burns](https://commons.wikimedia.org/w/index.php?curid=72118951) | 3465 × 1969 |
| 40 | Lovis Corinth | [Bacchantenzug](https://commons.wikimedia.org/w/index.php?curid=138748673) | 4000 × 2208 |
| 41 | Mikhail Vrubel | [Dämon sitzend](https://commons.wikimedia.org/w/index.php?curid=13507795) | 4000 × 2199 |
| 42 | Balthasar van der Ast | [Still Life with Fruits and Flowers](https://commons.wikimedia.org/w/index.php?curid=34313529) | 6018 × 3380 |
| 43 | Gerrit Willem Dijsselhof | [Tulip Fields](https://commons.wikimedia.org/w/index.php?curid=34321133) | 5344 × 3024 |
| 44 | Otto Modersohn | [Mondaufgang im Moor](https://commons.wikimedia.org/w/index.php?curid=44719383) | 3983 × 2226 |
| 45 | Bruno Liljefors | [Zilvermeeuwen en zeezwaluwen op de scheren voor de Scandinavische kust](https://commons.wikimedia.org/w/index.php?curid=80486236) | 11302 × 6386 |
| 46 | Carl Spitzweg | [Auf der Alm](https://commons.wikimedia.org/w/index.php?curid=178668227) | 4824 × 2780 |
| 47 | Charles-François Daubigny | [Alders](https://commons.wikimedia.org/w/index.php?curid=93485233) | 7461 × 4226 |
| 48 | Eugène Boudin | [Environs d’Honfleur, pâturage](https://commons.wikimedia.org/w/index.php?curid=153743085) | 3200 × 1803 |
| 49 | Claude Monet | [The Seashore at Sainte-Adresse](https://commons.wikimedia.org/w/index.php?curid=45589856) | 6676 × 3729 |
| 50 | Edgar Degas | [Kleines Mädchen wird am Meeresstrand von seiner Bonne gekämmt](https://commons.wikimedia.org/w/index.php?curid=150081) | 6000 × 3406 |
| 51 | Édouard Manet | [At the Races](https://commons.wikimedia.org/w/index.php?curid=81309991) | 4000 × 2305 |
| 52 | Frederic Edwin Church | [Das Herz der Anden](https://commons.wikimedia.org/w/index.php?curid=57364471) | 3811 × 2099 |
| 53 | Henry Moret | [Pêcheurs au large](https://commons.wikimedia.org/w/index.php?curid=122873779) | 3200 × 1778 |
| 54 | Ivan Shishkin | [Roggenfeld](https://commons.wikimedia.org/w/index.php?curid=13502218) | 4000 × 2254 |
| 55 | Johan Barthold Jongkind | [Road near La Côte-Saint-André](https://commons.wikimedia.org/w/index.php?curid=60846777) | 3898 × 2170 |
| 56 | John Atkinson Grimshaw | [A Wet Moon, Putney Road](https://commons.wikimedia.org/w/index.php?curid=74332535) | 3200 × 1825 |
| 57 | John Constable | [Ploughing Scene in Suffolk](https://commons.wikimedia.org/w/index.php?curid=22153299) | 6900 × 3916 |
| 58 | Adam Willaerts | [Harbour scene](https://commons.wikimedia.org/w/index.php?curid=22135067) | 5276 × 3028 |
| 59 | Adrien Manglard | [Szene im Mittelmeerhafen](https://commons.wikimedia.org/w/index.php?curid=95149294) | 3200 × 1845 |
| 60 | Albert Anker | [Die Kinderkrippe I](https://commons.wikimedia.org/w/index.php?curid=795544) | 6267 × 3551 |
| 61 | Albert Edelfelt | [Lugano](https://commons.wikimedia.org/w/index.php?curid=66313896) | 4000 × 2272 |
| 62 | Alexander Adriaenssen | [A Still Life with Roses, a Jug, a Loaf of Bread, a Filled Wine Glass, Two Plates with Prawns and Crabs, a Knife, a Partly-Peeled Lemon and Grapes over a Partly-Draped Table](https://commons.wikimedia.org/w/index.php?curid=20279913) | 4000 × 2249 |
| 63 | Alexandre Cabanel | [Die Geburt der Venus](https://commons.wikimedia.org/w/index.php?curid=20264780) | 4032 × 2290 |
| 64 | Amaldus Nielsen | [Den gamle Frognerseterveien](https://commons.wikimedia.org/w/index.php?curid=118446129) | 3000 × 1656 |
| 65 | Unbekannt (USA, 19. Jahrhundert) | [Imaginary Regatta of America's Cup Winners](https://commons.wikimedia.org/w/index.php?curid=81304229) | 3542 × 1974 |
| 66 | Antal Ligeti | [Pusta](https://commons.wikimedia.org/w/index.php?curid=68010997) | 5000 × 2820 |
| 67 | Anton Perko | [Lighthouse Grebeni, Dubrovnik](https://commons.wikimedia.org/w/index.php?curid=75034224) | 3108 × 1776 |
| 68 | Asterio Mañanós Martínez | [Apertura de las Cortes en el año 1919 (Plaza del Senado)](https://commons.wikimedia.org/w/index.php?curid=26814547) | 3440 × 1936 |
| 69 | Bernardo Bellotto | [Festung Königstein](https://commons.wikimedia.org/w/index.php?curid=82931652) | 8128 × 4493 |
| 70 | Bernardo Bellotto und Werkstatt | [Blick auf München](https://commons.wikimedia.org/w/index.php?curid=81307464) | 3499 × 1998 |
| 71 | Berndt Lindholm | [Forest Interior](https://commons.wikimedia.org/w/index.php?curid=66316393) | 4000 × 2230 |
| 72 | Bicci di Lorenzo | [Der hl. Nikolaus gibt die Aussteuer](https://commons.wikimedia.org/w/index.php?curid=57384516) | 3811 × 2101 |
| 73 | Canaletto | [Die Porta Portello, Padua](https://commons.wikimedia.org/w/index.php?curid=81308465) | 4000 × 2270 |
| 74 | Carl Frederik Aagaard | [The coast at Saltholm.](https://commons.wikimedia.org/w/index.php?curid=128454257) | 7993 × 4465 |
| 75 | Carl Larsson | [Open-Air Painter. Winter-Motif from Åsögatan 145, Stockholm](https://commons.wikimedia.org/w/index.php?curid=22264267) | 6337 × 3635 |
| 76 | Charles Wilkinson | [Funeral Ritual in a Garden, Tomb of Minnakht](https://commons.wikimedia.org/w/index.php?curid=60939098) | 3811 × 2169 |
| 77 | Charles Wilson Knapp | [Mountain River Scene (Autumn on the Hudson)](https://commons.wikimedia.org/w/index.php?curid=22199619) | 3000 × 1652 |
| 78 | Charles Émile Jacque | [The Shepherdess](https://commons.wikimedia.org/w/index.php?curid=81415687) | 4000 × 2251 |
| 79 | Nach Chen Chun | [Gartenblumen (Albumblatt)](https://commons.wikimedia.org/w/index.php?curid=57377196) | 3774 × 2145 |
| 80 | Christian Skredsvig | [Snow Dumping on the Seine](https://commons.wikimedia.org/w/index.php?curid=43317016) | 3360 × 1880 |
| 81 | Enrico Coleman | [Along the Tiber](https://commons.wikimedia.org/w/index.php?curid=141394807) | 5019 × 2792 |
| 82 | Eugène Delacroix | [Tiger](https://commons.wikimedia.org/w/index.php?curid=81434598) | 4000 × 2266 |
| 83 | Eugène Lami | [Camp de Compiègne, 1698](https://commons.wikimedia.org/w/index.php?curid=65096460) | 3794 × 2139 |
| 84 | Ferdinand Richardt | [Independence Hall in Philadelphia](https://commons.wikimedia.org/w/index.php?curid=21881964) | 7153 × 4069 |
| 85 | Fitz Henry Lane | [Becalmed off Halfway Rock](https://commons.wikimedia.org/w/index.php?curid=81310473) | 4000 × 2305 |
| 86 | Francesco Guardi | [Venice: The Dogana and Santa Maria della Salute](https://commons.wikimedia.org/w/index.php?curid=57669562) | 3811 × 2139 |
| 87 | Francesco Guardi / Giovanni Antonio Guardi | [Erminia und die Hirten](https://commons.wikimedia.org/w/index.php?curid=81314166) | 3531 × 1980 |
| 88 | George Inness | [Olive Trees at Tivoli](https://commons.wikimedia.org/w/index.php?curid=58728087) | 3811 × 2171 |
| 89 | Hans Thoma | [Der Rhein bei Säckingen](https://commons.wikimedia.org/w/index.php?curid=18160885) | 3346 × 1856 |
| 90 | Henryk Siemiradzki | [Scena przy studni](https://commons.wikimedia.org/w/index.php?curid=88804323) | 3403 × 1908 |
| 91 | Hieronymus Bosch | [Der Garten der Lüste](https://commons.wikimedia.org/w/index.php?curid=22605738) | 30000 × 17078 |
| 92 | Hjalmar Munsterhjelm | [Morning Mood (Island View)](https://commons.wikimedia.org/w/index.php?curid=66322831) | 4000 × 2222 |
| 93 | Hugo Simberg | [Piru muuttaa](https://commons.wikimedia.org/w/index.php?curid=66323064) | 4000 × 2278 |
| 94 | Frederick McCubbin | [The gardener](https://commons.wikimedia.org/w/index.php?curid=114833882) | 7018 × 4000 |
| 95 | James Bard | [Towboat "John Birkbeck"](https://commons.wikimedia.org/w/index.php?curid=81325026) | 3000 × 1681 |
| 96 | Jan Brueghel the Elder | [A Woodland Road with Travelers](https://commons.wikimedia.org/w/index.php?curid=57398214) | 3811 × 2114 |
| 97 | Jasper Francis Cropsey | [Herbst - am Hudson River](https://commons.wikimedia.org/w/index.php?curid=327727) | 4000 × 2201 |
| 98 | John Frederick Kensett | [Almy's Pond, Newport, Rhode Island](https://commons.wikimedia.org/w/index.php?curid=27367362) | 3025 × 1695 |
| 99 | John Henry Twachtman | [Summer](https://commons.wikimedia.org/w/index.php?curid=23596858) | 4001 × 2290 |
| 100 | John William Waterhouse | [Echo und Narcissus](https://commons.wikimedia.org/w/index.php?curid=21878879) | 4903 × 2797 |
| 101 | Joseph Vernet | [Harbor Scene with a Grotto and Fishermen Hauling in Nets](https://commons.wikimedia.org/w/index.php?curid=57673092) | 3919 × 2160 |
| 102 | José Malhoa | [Boasting incomes](https://commons.wikimedia.org/w/index.php?curid=15696680) | 7720 × 4353 |
| 103 | Jules Breton | [The Weeders](https://commons.wikimedia.org/w/index.php?curid=57384716) | 3811 × 2149 |
| 104 | Jules Dupré | [Kühe überqueren eine Furt](https://commons.wikimedia.org/w/index.php?curid=27216200) | 3804 × 2183 |
| 105 | Karel Ooms | [Aristocratic family enjoying winter landscape](https://commons.wikimedia.org/w/index.php?curid=44569993) | 3000 × 1730 |
| 106 | Kerstiaen de Keuninck | [A Mountainous Landscape with a Waterfall](https://commons.wikimedia.org/w/index.php?curid=57669998) | 3811 × 2172 |
| 107 | Martin Johnson Heade | [Cherokee Roses on a Purple Cloth](https://commons.wikimedia.org/w/index.php?curid=21959590) | 3000 × 1653 |
| 108 | Max Liebermann | [Arbeiter im Rübenfeld (Ölstudie)](https://commons.wikimedia.org/w/index.php?curid=26563390) | 6541 × 3623 |
| 109 | Nina M. Davies | [Menna and Family Hunting in the Marshes, Tomb of Menna](https://commons.wikimedia.org/w/index.php?curid=65140182) | 3811 × 2098 |
| 110 | Paul Huet | [Mountains of Auvergne](https://commons.wikimedia.org/w/index.php?curid=60854281) | 3866 × 2191 |
| 111 | Paul Klee | [Where the Eggs and the Good Roast Come From](https://commons.wikimedia.org/w/index.php?curid=60909660) | 3811 × 2196 |
| 112 | Peder Severin Krøyer | [Artists' lunch. Cernay-la-Ville.](https://commons.wikimedia.org/w/index.php?curid=116261686) | 3000 × 1655 |
| 113 | Pierre-Auguste Renoir | [Apples (Pommes)](https://commons.wikimedia.org/w/index.php?curid=67540168) | 4096 × 2343 |
| 114 | Piero di Cosimo | [Prometheus erschafft den ersten Menschen](https://commons.wikimedia.org/w/index.php?curid=15885145) | 3000 × 1656 |
| 115 | Samuel Scott | [The Building of Westminster Bridge](https://commons.wikimedia.org/w/index.php?curid=57672440) | 3913 × 2148 |
| 116 | Stanislas Lépine | [A Plow Horse in a Field](https://commons.wikimedia.org/w/index.php?curid=81332363) | 3530 × 1980 |
| 117 | Viktor Borisov-Musatov | [The Emerald Necklace](https://commons.wikimedia.org/w/index.php?curid=13496330) | 5651 × 3258 |
| 118 | Vincent van Gogh | [Vorabend / Autumn Landscape at Dusk](https://commons.wikimedia.org/w/index.php?curid=138007676) | 3782 × 2165 |
| 119 | William Bradford | [Near Cape St. Johns, Coast of Labrador](https://commons.wikimedia.org/w/index.php?curid=25031017) | 3000 × 1716 |
| 120 | William Trost Richards | [British Coastal View (Coast of Cornwall)](https://commons.wikimedia.org/w/index.php?curid=21276801) | 3000 × 1649 |
| 121 | Winslow Homer | [Lobster Cove, Manchester, Massachusetts](https://commons.wikimedia.org/w/index.php?curid=190237599) | 7234 × 4144 |
| 122 | Nach Marco Ricci | [View of the Mall in Saint James's Park](https://commons.wikimedia.org/w/index.php?curid=81302575) | 3490 × 2003 |
| 123 | Aelbert Cuyp | [Flusslandschaft mit Reitern](https://commons.wikimedia.org/w/index.php?curid=34319635) | 6476 × 3632 |
| 124 | David Colijns | [The ascension of Elijah](https://commons.wikimedia.org/w/index.php?curid=34313914) | 3808 × 2118 |
| 125 | Dirck Hals | [Fest im Freien](https://commons.wikimedia.org/w/index.php?curid=131942228) | 6476 × 3640 |
| 126 | Esaias van de Velde | [Elegant company dining in the open air](https://commons.wikimedia.org/w/index.php?curid=34317675) | 6014 × 3406 |
| 127 | Gijsbert d'Hondecoeter | [Waterfowl](https://commons.wikimedia.org/w/index.php?curid=34405178) | 6392 × 3602 |
| 128 | Gillis Claesz. de Hondecoeter | [The country road](https://commons.wikimedia.org/w/index.php?curid=34313531) | 4604 × 2528 |
| 129 | Hercules Segers (1589–1637) | [River Valley](https://commons.wikimedia.org/w/index.php?curid=34313842) | 5964 × 3304 |
| 130 | Luca Giordano | [Four Female Musicians](https://commons.wikimedia.org/w/index.php?curid=34250590) | 3674 × 2020 |
| 131 | Pauwels van Hillegaert | [Prinz Moritz auf der Neude in Utrecht, 31. Juli 1618](https://commons.wikimedia.org/w/index.php?curid=83529871) | 5040 × 2884 |
| 132 | Reinier Nooms | [View of Tunis](https://commons.wikimedia.org/w/index.php?curid=34320072) | 7138 × 4038 |
| 133 | Jacob van Campen | [Still Life with Fruit and Flower Garlands](https://commons.wikimedia.org/w/index.php?curid=34249872) | 6252 × 3496 |
| 134 | William Charles Estall | [A Flock of Sheep](https://commons.wikimedia.org/w/index.php?curid=34258147) | 7662 × 4394 |
| 135 | Otto Modersohn | [Sturm im Teufelsmoor](https://commons.wikimedia.org/w/index.php?curid=159288815) | 4000 × 2243 |
| 136 | Bruno Liljefors | [Hare in Winter Landscape](https://commons.wikimedia.org/w/index.php?curid=141281704) | 3000 × 1699 |
| 137 | Carl Spitzweg | [Bäuerin vor einer Almhütte](https://commons.wikimedia.org/w/index.php?curid=149827428) | 4275 × 2403 |
| 138 | Eugène Boudin | [Concert at the Casino of Deauville](https://commons.wikimedia.org/w/index.php?curid=81310320) | 4000 × 2251 |
| 139 | Edgar Degas | [The Loge](https://commons.wikimedia.org/w/index.php?curid=81309955) | 4000 × 2293 |
| 140 | Jean-Baptiste-Camille Corot | [Carrière de la Chaise-Marie, Fontainebleau](https://commons.wikimedia.org/w/index.php?curid=140222439) | 3705 × 2121 |
| 141 | Bernardo Bellotto und Werkstatt | [Ansicht von München, Schloß Nymphenburg, von Westen aus gesehen](https://commons.wikimedia.org/w/index.php?curid=81307433) | 3516 × 1988 |
| 142 | Berndt Lindholm | [Oat Harvest on the Hisingen Island](https://commons.wikimedia.org/w/index.php?curid=66316398) | 4000 × 2276 |
| 143 | Francesco Guardi | [Venice: The Rialto](https://commons.wikimedia.org/w/index.php?curid=57669569) | 3811 × 2159 |
| 144 | John Frederick Kensett | [Lake Erie](https://commons.wikimedia.org/w/index.php?curid=115455905) | 3200 × 1758 |
| 145 | Martin Johnson Heade | [Point Judith, Rhode Island](https://commons.wikimedia.org/w/index.php?curid=76001413) | 3400 × 1891 |
| 146 | Peder Severin Krøyer | [Hunters of Skagen](https://commons.wikimedia.org/w/index.php?curid=11155871) | 5281 × 2984 |
| 147 | Pierre-Auguste Renoir | [Femme couchée sur l’herbe](https://commons.wikimedia.org/w/index.php?curid=76362260) | 4000 × 2303 |
| 148 | Sanford Robinson Gifford | [Isola Bella In Lago Maggiore](https://commons.wikimedia.org/w/index.php?curid=57365081) | 3811 × 2141 |
| 149 | William Trost Richards | [Summer Sea](https://commons.wikimedia.org/w/index.php?curid=115455733) | 3200 × 1788 |
| 150 | Winslow Homer | [Rainy Day in Camp](https://commons.wikimedia.org/w/index.php?curid=10629177) | 5862 × 3237 |
| 151 | Charles-François Daubigny | [View on the Oise](https://commons.wikimedia.org/w/index.php?curid=93485240) | 7438 × 4226 |
| 152 | Eugène Boudin | [Markt in der Bretagne](https://commons.wikimedia.org/w/index.php?curid=81310326) | 4000 × 2307 |
| 153 | Berndt Lindholm | [Rantakuva](https://commons.wikimedia.org/w/index.php?curid=66322211) | 4000 × 2273 |
| 154 | Pierre-Auguste Renoir | [Nature morte aux grenades et figues](https://commons.wikimedia.org/w/index.php?curid=76401796) | 3200 × 1779 |
| 155 | Sanford Robinson Gifford | [Sunset over New York Bay](https://commons.wikimedia.org/w/index.php?curid=30489671) | 3200 × 1838 |
| 156 | Winslow Homer | [The Country School](https://commons.wikimedia.org/w/index.php?curid=101606839) | 4632 × 2572 |
| 157 | Charles-François Daubigny | [Sunset at Villerville](https://commons.wikimedia.org/w/index.php?curid=128008817) | 3840 × 2172 |
| 158 | Eugène Boudin | [On the Beach](https://commons.wikimedia.org/w/index.php?curid=81310336) | 4000 × 2294 |
| 159 | Sanford Robinson Gifford | [The Artist Sketching at Mount Desert, Maine](https://commons.wikimedia.org/w/index.php?curid=74897839) | 4000 × 2303 |
| 160 | Winslow Homer | [The Gulf Stream](https://commons.wikimedia.org/w/index.php?curid=23855425) | 3000 × 1683 |
| 161 | Charles-François Daubigny | [Sluice in the Optevoz Valley](https://commons.wikimedia.org/w/index.php?curid=74389941) | 3200 × 1775 |
| 162 | Eugène Boudin | [On the Beach, Trouville](https://commons.wikimedia.org/w/index.php?curid=81310338) | 4000 × 2240 |
| 163 | Winslow Homer | [Two Figures by the Sea](https://commons.wikimedia.org/w/index.php?curid=21894912) | 4801 × 2748 |
| 164 | Charles-François Daubigny | [The Painter’s Barge at the Ile de Vaux on the Oise River](https://commons.wikimedia.org/w/index.php?curid=85067082) | 9321 × 5271 |
| 165 | Eugène Boudin | [Le Havre, La Fête des régates](https://commons.wikimedia.org/w/index.php?curid=178770689) | 8153 × 4530 |
| 166 | Eugène Boudin | [Honfleur. Voiliers](https://commons.wikimedia.org/w/index.php?curid=115423103) | 3200 × 1830 |
| 167 | Adalbert Waagen | [Motif of the Alps](https://commons.wikimedia.org/w/index.php?curid=64525652) | 3814 × 2185 |
| 168 | Adolphe Joseph Thomas Monticelli | [Landscape with Figures](https://commons.wikimedia.org/w/index.php?curid=23595716) | 4001 × 2244 |
| 169 | Adrien Bas | [Vase de digitales](https://commons.wikimedia.org/w/index.php?curid=49911139) | 5184 × 2958 |
| 170 | Albert Joseph Moore | [A Summer Night](https://commons.wikimedia.org/w/index.php?curid=21878850) | 3721 × 2143 |
| 171 | Albert Joseph Moore | [Beads](https://commons.wikimedia.org/w/index.php?curid=121561562) | 7611 × 4333 |
| 172 | Albert Julius Olsson | [The Night Patrol - Canadian Motor Torpedo Boats Entering Dover Harbour](https://commons.wikimedia.org/w/index.php?curid=74546310) | 6702 × 3864 |
| 173 | Aleksander Mroczkowski | [W żniwa](https://commons.wikimedia.org/w/index.php?curid=4003728) | 3507 × 1999 |
| 174 | Alexis Jean Fournier | [September](https://commons.wikimedia.org/w/index.php?curid=45607698) | 6859 × 3856 |
| 175 | Alfred Richard Gurrey, Sr. | [Kauai Coastal View](https://commons.wikimedia.org/w/index.php?curid=41052077) | 4306 × 2390 |
| 176 | Alfred Steinacker | [Kutsche bei Scheegestöber](https://commons.wikimedia.org/w/index.php?curid=75030787) | 3812 × 2092 |
| 177 | Alfred Steinacker | [Ungarische Bauernhochzeit](https://commons.wikimedia.org/w/index.php?curid=18410668) | 3996 × 2292 |
| 178 | Alfred Steinacker | [Winter Ride](https://commons.wikimedia.org/w/index.php?curid=64501070) | 3556 × 2040 |
| 179 | András Markó | [View of Rome from Villa Madama](https://commons.wikimedia.org/w/index.php?curid=77663284) | 4814 × 2743 |
| 180 | Angelo Dall'Oca Bianca | [Foglie cadenti](https://commons.wikimedia.org/w/index.php?curid=38869178) | 3017 × 1721 |
| 181 | Angelo Morbelli | [Battello sul Lago Maggiore Boat on Lake Maggiore](https://commons.wikimedia.org/w/index.php?curid=178891565) | 3543 × 2022 |
| 182 | Antoine Guillemet | [Le Quai de Bercy](https://commons.wikimedia.org/w/index.php?curid=101282268) | 6381 × 3522 |
| 183 | Anton Braith | [Rinder an der Tränke](https://commons.wikimedia.org/w/index.php?curid=18652488) | 4825 × 2775 |
| 184 | Antonio Ermolao Paoletti | [The melon sellers.](https://commons.wikimedia.org/w/index.php?curid=20972263) | 3699 × 2133 |
| 185 | Antonio Jacobsen | ['The Jefferson', 1914](https://commons.wikimedia.org/w/index.php?curid=22530995) | 3000 × 1648 |
| 186 | Antonio Mancini | [The brothers](https://commons.wikimedia.org/w/index.php?curid=128007932) | 3840 × 2198 |
| 187 | Arnold Peter Weisz-Kubínčan | [Slovak: Zimná krajina Winter Landscape](https://commons.wikimedia.org/w/index.php?curid=98348102) | 5000 × 2804 |
| 188 | Arthur Quartley | [Morning off Marblehead](https://commons.wikimedia.org/w/index.php?curid=53997339) | 3000 × 1683 |
| 189 | Arthur Wellington Fowles | [A schooner yacht of the New York Yacht Club racing off Ryde, Isle of Wight](https://commons.wikimedia.org/w/index.php?curid=163461953) | 3030 × 1716 |
| 190 | Ascan Lutteroth | [A view of Capri](https://commons.wikimedia.org/w/index.php?curid=76696020) | 4621 × 2609 |
| 191 | August Ignaz Grosz | [Krajina na Capri](https://commons.wikimedia.org/w/index.php?curid=67893605) | 5000 × 2832 |
| 192 | Augustin Théodule Ribot | [Still Life with Apples and a Pomegranate](https://commons.wikimedia.org/w/index.php?curid=37948976) | 3264 × 1880 |
| 193 | Benedito Calixto | [Enseada com barcos](https://commons.wikimedia.org/w/index.php?curid=123889433) | 6670 × 3824 |
| 194 | Bernard Boutet de Monvel | [The Haulers](https://commons.wikimedia.org/w/index.php?curid=124914944) | 5540 × 3086 |
| 195 | Carl Werner | [View of Norba from the North, towards San Felice Circeo](https://commons.wikimedia.org/w/index.php?curid=60278301) | 3701 × 2058 |
| 196 | Carlos de Haes | [Flemish Landscape](https://commons.wikimedia.org/w/index.php?curid=21956171) | 3859 × 2215 |
| 197 | Carolus-Duran | [Promenade in the Woods](https://commons.wikimedia.org/w/index.php?curid=66350586) | 3767 × 2087 |
| 198 | Charles Conder | [The Yarra, Heidelberg](https://commons.wikimedia.org/w/index.php?curid=22264624) | 4960 × 2763 |
| 199 | Charles Courtney Curran | [Fair Critics](https://commons.wikimedia.org/w/index.php?curid=38876479) | 6279 × 3565 |
| 200 | Charles Guilloux | [Riverside](https://commons.wikimedia.org/w/index.php?curid=97110464) | 3200 × 1801 |
| 201 | David Cox | [Rhyl Sands](https://commons.wikimedia.org/w/index.php?curid=97453046) | 3998 × 2210 |
| 202 | Eduard von Grützner | [Behind the Scenes](https://commons.wikimedia.org/w/index.php?curid=26373125) | 4752 × 2693 |
| 203 | Eduardo de Martino | [Botafogo Beach](https://commons.wikimedia.org/w/index.php?curid=21938974) | 5005 × 2865 |
| 204 | Edward Lear | [Edward Lear, Tarxien, Malta](https://commons.wikimedia.org/w/index.php?curid=134181389) | 3200 × 1786 |
| 205 | Edward Lear | [Maharraka, 7:15 am, 14 February 1867 (462)](https://commons.wikimedia.org/w/index.php?curid=22250995) | 6251 × 3505 |
| 206 | Edward Lear | [Near Wady Halfeh](https://commons.wikimedia.org/w/index.php?curid=22205181) | 4870 × 2798 |
| 207 | Edward Lear | [Shelaal](https://commons.wikimedia.org/w/index.php?curid=22204845) | 3712 × 2047 |
| 208 | Edward William Cooke | [Venice](https://commons.wikimedia.org/w/index.php?curid=17224019) | 6414 × 3696 |
| 209 | Edwin Long | [The Babylonian Marriage Market](https://commons.wikimedia.org/w/index.php?curid=2152784) | 3069 × 1720 |
| 210 | Egon Schiele | [Reclining Woman](https://commons.wikimedia.org/w/index.php?curid=21987965) | 4897 × 2717 |
| 211 | Emil Carlsen | [Nantasket Beach](https://commons.wikimedia.org/w/index.php?curid=73882709) | 3000 × 1704 |
| 212 | Eugen Bracht | [Dusk on the Dead Sea](https://commons.wikimedia.org/w/index.php?curid=79951735) | 3618 × 2029 |
| 213 | Eugene von Guerard | [Lake Wakatipu with Mount Earnslaw, Middle Island, New Zealand](https://commons.wikimedia.org/w/index.php?curid=22007414) | 5679 × 3177 |
| 214 | Eugène Fromentin | [On the Nile, Near Philae](https://commons.wikimedia.org/w/index.php?curid=74249300) | 3000 × 1704 |
| 215 | Eugène Isabey | [Shipwrecking of three-masted ship Emily 1823](https://commons.wikimedia.org/w/index.php?curid=63935711) | 3995 × 2299 |
| 216 | Eugène Louis Boudin | [Beach House with Flags at Trouville](https://commons.wikimedia.org/w/index.php?curid=81434273) | 4000 × 2254 |
| 217 | Eugène Louis Boudin | [Fishwomen Seated on the Beach at Berck](https://commons.wikimedia.org/w/index.php?curid=164265708) | 3328 × 1843 |
| 218 | Eugène Louis Boudin | [On the Beach at Trouville](https://commons.wikimedia.org/w/index.php?curid=18581296) | 3811 × 2116 |
| 219 | Eugène Louis Boudin | [Trouville, scène de plage](https://commons.wikimedia.org/w/index.php?curid=146082144) | 3200 × 1778 |
| 220 | Eugène Louis Boudin | [Washerwomen on the Bank of the Touques](https://commons.wikimedia.org/w/index.php?curid=156053939) | 15686 × 9000 |
| 221 | Fabius Brest | [A capriccio of Constantinople](https://commons.wikimedia.org/w/index.php?curid=77816836) | 4829 × 2717 |
| 222 | Fanny Churberg | [Birches by the Water](https://commons.wikimedia.org/w/index.php?curid=66317047) | 4000 × 2233 |
| 223 | Florian Milan | [Slovak: Na púti v Levoči](https://commons.wikimedia.org/w/index.php?curid=97701737) | 5000 × 2870 |
| 224 | Francis A. Silva | [The Hudson at the Tappan Zee](https://commons.wikimedia.org/w/index.php?curid=21911881) | 5840 × 3343 |
| 225 | François Musin | [Marine](https://commons.wikimedia.org/w/index.php?curid=17224098) | 5336 × 3015 |
| 226 | Frederic Leighton | [Greek Girls Playing Ball](https://commons.wikimedia.org/w/index.php?curid=45559316) | 3746 × 2148 |
| 227 | Frederic Remington | [A Dash for the Timber](https://commons.wikimedia.org/w/index.php?curid=48209049) | 4236 × 2400 |
| 228 | Frederick Daniel Hardy | [The Volunteers](https://commons.wikimedia.org/w/index.php?curid=31585705) | 4572 × 2542 |
| 229 | Félicien Rops | [Landscape in Sweden](https://commons.wikimedia.org/w/index.php?curid=140184404) | 3641 × 2049 |
| 230 | Félix Ziem | [Constantinople, le caïque de la sultane](https://commons.wikimedia.org/w/index.php?curid=98847197) | 5975 × 3388 |
| 231 | George Hendrik Breitner | [Bouwterrein, SK-A-2977](https://commons.wikimedia.org/w/index.php?curid=83513302) | 4032 × 2290 |
| 232 | George Luks | [Houston Street](https://commons.wikimedia.org/w/index.php?curid=5635463) | 4184 × 2384 |
| 233 | Georgios Jakobides | [Church in blooming field in Bavaria](https://commons.wikimedia.org/w/index.php?curid=148767443) | 12000 × 6899 |
| 234 | Giovanni Battista Castagneto | [The port of Rio de Janeiro](https://commons.wikimedia.org/w/index.php?curid=39680145) | 5667 × 3268 |
| 235 | Giuseppe De Nittis | [The Palace of Westminster, London](https://commons.wikimedia.org/w/index.php?curid=147230027) | 5000 × 2858 |
| 236 | Giuseppe De Nittis | [Veduta di Londra (Il Victoria Embankment, Londra) The Victoria Embankment, London](https://commons.wikimedia.org/w/index.php?curid=164784050) | 3200 × 1820 |
| 237 | Gustave Den Duyts | [Village Street in the Rain](https://commons.wikimedia.org/w/index.php?curid=140216695) | 3877 × 2221 |
| 238 | Gustave Doré | [Torrent in the Highlands](https://commons.wikimedia.org/w/index.php?curid=66351503) | 5686 × 3184 |
| 239 | Henri Beau | [L'Arrivée de Champlain à Québec](https://commons.wikimedia.org/w/index.php?curid=48192935) | 4277 × 2348 |
| 240 | Henri Harpignies | [Le Colisée à Rome](https://commons.wikimedia.org/w/index.php?curid=98262508) | 5762 × 3290 |
| 241 | Henry Brokmann | [Poupe de l'Alda, mer démontée](https://commons.wikimedia.org/w/index.php?curid=98922913) | 5814 × 3226 |
| 242 | Henryk Pillati | [Eastern scene – Selling horses](https://commons.wikimedia.org/w/index.php?curid=99879445) | 4000 × 2280 |
| 243 | Hubert von Herkomer | [Eventide- A Scene at the Westminster Union](https://commons.wikimedia.org/w/index.php?curid=21878594) | 3053 × 1679 |
| 244 | Ida Gerhardi | [Ida Gerhardi](https://commons.wikimedia.org/w/index.php?curid=148442005) | 3642 × 2051 |
| 245 | J. C. Thom | [Landscape with Boatman](https://commons.wikimedia.org/w/index.php?curid=66352146) | 6338 × 3613 |
| 246 | Jacob Maris | [View at Montigny-sur-Loing](https://commons.wikimedia.org/w/index.php?curid=22007097) | 5868 × 3290 |
| 247 | James Tissot | [Le retour de l'enfant prodigue](https://commons.wikimedia.org/w/index.php?curid=98110746) | 5917 × 3267 |
| 248 | Jan Matejko | [Alchemist Sendivogius](https://commons.wikimedia.org/w/index.php?curid=67711) | 5554 × 3095 |
| 249 | Jan Stanisławski | [Fields at Proszowice](https://commons.wikimedia.org/w/index.php?curid=98844586) | 4000 × 2206 |
| 250 | Jan Stanisławski | [Sun](https://commons.wikimedia.org/w/index.php?curid=98843700) | 4000 × 2303 |
| 251 | Jan van Beers | [After the ball](https://commons.wikimedia.org/w/index.php?curid=115802349) | 4590 × 2556 |
| 252 | Jean-Louis-Ernest Meissonier | [1807, Friedland](https://commons.wikimedia.org/w/index.php?curid=57670691) | 3811 × 2100 |
| 253 | Jean-Léon Gérôme | [Chariot Race](https://commons.wikimedia.org/w/index.php?curid=74945568) | 3000 × 1659 |
| 254 | Johannes Warnardus Bilders | [The pond at Oosterbeek](https://commons.wikimedia.org/w/index.php?curid=139236388) | 3735 × 2118 |
| 255 | Johannes Wilhjelm | [Idyl på heden](https://commons.wikimedia.org/w/index.php?curid=140453043) | 5530 × 3138 |
| 256 | John Brett | [Southern Coast of Guernsey](https://commons.wikimedia.org/w/index.php?curid=29660609) | 6381 × 3546 |
| 257 | John Frederick Herring, Jr. | [Harvest](https://commons.wikimedia.org/w/index.php?curid=22008059) | 6249 × 3557 |
| 258 | John Haberle | [A Bachelor's Drawer](https://commons.wikimedia.org/w/index.php?curid=57365122) | 3811 × 2135 |
| 259 | John La Farge | [Flowers on a Japanese Tray on a Mahogany Table](https://commons.wikimedia.org/w/index.php?curid=21911817) | 3316 × 1903 |
| 260 | Josep Llovera i Bufill | [The Christening](https://commons.wikimedia.org/w/index.php?curid=22029372) | 3031 × 1739 |
| 261 | Joseph Alanen | [Conquest of Häme](https://commons.wikimedia.org/w/index.php?curid=92531946) | 3632 × 2028 |
| 262 | Joseph Severn | [The deserted village](https://commons.wikimedia.org/w/index.php?curid=23603036) | 4725 × 2670 |
| 263 | Joža Uprka | [Ride of the Kings](https://commons.wikimedia.org/w/index.php?curid=35102868) | 5777 × 3214 |
| 264 | Julia Beck | [Julia Beck, Portrait de Mademoiselle Cecilia Lewenhaupt, 1886](https://commons.wikimedia.org/w/index.php?curid=165011548) | 3000 × 1730 |
| 265 | Julius van de Sande Bakhuyzen | [Landschap in Drenthe](https://commons.wikimedia.org/w/index.php?curid=83539260) | 3816 × 2188 |
| 266 | Józef Chełmoński | [Kurhan A Barrow](https://commons.wikimedia.org/w/index.php?curid=99880781) | 3000 × 1720 |
| 267 | Jørgen Sonne | [The Skirmish at Vorbasse February the 29th, 1864](https://commons.wikimedia.org/w/index.php?curid=148542357) | 4183 × 2320 |
| 268 | Karol Miloslav Lehotský | [Nightingale Isle by Ilok](https://commons.wikimedia.org/w/index.php?curid=97754997) | 5000 × 2828 |
| 269 | Karol Miloslav Lehotský | [Slovak: Dedinský potok A Village Brook](https://commons.wikimedia.org/w/index.php?curid=97678005) | 5000 × 2780 |
| 270 | Ker-Xavier Roussel | [Meeting of Women](https://commons.wikimedia.org/w/index.php?curid=38212701) | 3355 × 1932 |
| 271 | Leo Gestel | [Reclining nude](https://commons.wikimedia.org/w/index.php?curid=25149244) | 3100 × 1716 |
| 272 | Lindsay Bernard Hall | [After dinner](https://commons.wikimedia.org/w/index.php?curid=23604298) | 5173 × 2849 |
| 273 | Luis Ricardo Falero | [A Fairy Under Starry Skies](https://commons.wikimedia.org/w/index.php?curid=50496417) | 3200 × 1784 |
| 274 | László Mednyánszky | [Mukačevo's Surrounding (Watering Trough)](https://commons.wikimedia.org/w/index.php?curid=17528965) | 3534 × 1991 |
| 275 | László Mednyánszky | [Slovak: Jarná krajina (Jar v ovocnom sade)](https://commons.wikimedia.org/w/index.php?curid=77904320) | 5000 × 2847 |
| 276 | László Mednyánszky | [Veľká letná krajina s riekou. Kúpanie](https://commons.wikimedia.org/w/index.php?curid=67893332) | 5000 × 2850 |
| 277 | Maurycy Gottlieb | [Salome's Dance](https://commons.wikimedia.org/w/index.php?curid=76412216) | 3180 × 1778 |
| 278 | Modest Urgell | [Landscape](https://commons.wikimedia.org/w/index.php?curid=22029214) | 3022 × 1735 |
| 279 | Modest Urgell | [The Bell for Prayer](https://commons.wikimedia.org/w/index.php?curid=21952919) | 5130 × 2853 |
| 280 | Nicolaas Bastert | [Boerenerf met liggend varken](https://commons.wikimedia.org/w/index.php?curid=76362098) | 6448 × 3708 |
| 281 | Niels Larsen Stevns | [View from Bokul, Gudhjem](https://commons.wikimedia.org/w/index.php?curid=148565486) | 4950 × 2778 |
| 282 | Niels Skovgaard | [Landscape from Foldalen in Norway](https://commons.wikimedia.org/w/index.php?curid=80335575) | 3105 × 1713 |
| 283 | Nándor Katona | [Slovak: Horská krajina](https://commons.wikimedia.org/w/index.php?curid=98925019) | 5000 × 2793 |
| 284 | Nándor Katona | [Winter Landscape](https://commons.wikimedia.org/w/index.php?curid=80512390) | 5000 × 2865 |
| 285 | Oscar Kleineh | [Rantamaisema, Florö](https://commons.wikimedia.org/w/index.php?curid=66315025) | 4000 × 2290 |
| 286 | Otto Sinding | [Spring Day in Lofoten](https://commons.wikimedia.org/w/index.php?curid=148507877) | 5012 × 2830 |
| 287 | Paul Nash | [The Menin Road](https://commons.wikimedia.org/w/index.php?curid=76558058) | 5338 × 3078 |
| 288 | Pierre-François Marangé | [Les ruines du palais des Tuileries, après l'incendie de 1871](https://commons.wikimedia.org/w/index.php?curid=102641108) | 5363 × 3050 |
| 289 | Piet Verhaert | [Vlissingen](https://commons.wikimedia.org/w/index.php?curid=148738953) | 3125 × 1757 |
| 290 | Prilidiano Pueyrredón | [La lavandera](https://commons.wikimedia.org/w/index.php?curid=21880968) | 4945 × 2725 |
| 291 | Raffaello Sorbi | [Bacchanal](https://commons.wikimedia.org/w/index.php?curid=107396060) | 3200 × 1826 |
| 292 | Ramon Martí Alsina | [Ruins of the Palace](https://commons.wikimedia.org/w/index.php?curid=21925802) | 3599 × 2059 |
| 293 | Raoul Arus | [Enlèvement d'un ballon](https://commons.wikimedia.org/w/index.php?curid=100486076) | 5569 × 3200 |
| 294 | Remigius Adrianus Haanen | [Landscape with Cottages on the Heath](https://commons.wikimedia.org/w/index.php?curid=45326162) | 6242 × 3600 |
| 295 | Remigius Adrianus Haanen | [Open Landscape in the Evening Light](https://commons.wikimedia.org/w/index.php?curid=41242543) | 3876 × 2230 |
| 296 | Ricardo Arredondo Calmache | [Tanners Workshop - Tanners Workshop of Ubide](https://commons.wikimedia.org/w/index.php?curid=29864826) | 3421 × 1890 |
| 297 | Richard Ansdell | [At the well](https://commons.wikimedia.org/w/index.php?curid=32777215) | 3354 × 1844 |
| 298 | Richard Friese | [Mixed forest in Canada](https://commons.wikimedia.org/w/index.php?curid=67541656) | 5753 × 3315 |
| 299 | Robert Hawker Dowling | [A Sheikh and his son entering Cairo on their return from a pilgrimage to Mecca](https://commons.wikimedia.org/w/index.php?curid=22144408) | 6313 × 3584 |
| 300 | Robert Jenkins Onderdonk | [Buffalo Hunt](https://commons.wikimedia.org/w/index.php?curid=18532915) | 3016 × 1705 |
| 301 | Robert Seldon Duncanson | [Landscape with Rainbow](https://commons.wikimedia.org/w/index.php?curid=142201718) | 3000 × 1725 |
| 302 | Robert Warthmüller | [The King everywhere](https://commons.wikimedia.org/w/index.php?curid=130381235) | 12686 × 7314 |
| 303 | Róbert Nádler | [The Building of Grand Market Hall in Budapest](https://commons.wikimedia.org/w/index.php?curid=18399258) | 3099 × 1727 |
| 304 | Silvestro Lega | [At the villa in Poggio Piano](https://commons.wikimedia.org/w/index.php?curid=116223919) | 4500 × 2500 |
| 305 | Silvestro Lega | [Riposo in collina Rest on the hill](https://commons.wikimedia.org/w/index.php?curid=149174803) | 5446 × 3086 |
| 306 | Stanisław Masłowski | [Moonrise](https://commons.wikimedia.org/w/index.php?curid=199676) | 4000 × 2229 |
| 307 | Taras Shevchenko | [Skelia Chernets'](https://commons.wikimedia.org/w/index.php?curid=72020929) | 3425 × 1903 |
| 308 | Théobald Chartran | [Esquisse pour l'escalier de la Sorbonne : Ambroise Paré au siège de Metz](https://commons.wikimedia.org/w/index.php?curid=98344118) | 5300 × 3039 |
| 309 | Vasily Surikov | [Morning of the Execution of the Streltsy](https://commons.wikimedia.org/w/index.php?curid=13502594) | 4000 × 2301 |
| 310 | Victor Westerholm | [Winter Landscape from Kymintehdas](https://commons.wikimedia.org/w/index.php?curid=13955306) | 5848 × 3220 |
| 311 | Viktor Vasnetsov | [Flying Carpet](https://commons.wikimedia.org/w/index.php?curid=146757712) | 5335 × 2953 |
| 312 | Vilhelm Melbye | [Marine landscape with sail boats](https://commons.wikimedia.org/w/index.php?curid=98807899) | 4000 × 2258 |
| 313 | Walter Crane | [Neptune's Horses](https://commons.wikimedia.org/w/index.php?curid=38939353) | 4000 × 2260 |
| 314 | Wilhelm Kotarbiński | [The Nile Mist](https://commons.wikimedia.org/w/index.php?curid=40937667) | 4044 × 2332 |
| 315 | Willem Frederik de Haas | [Cliffs of Star Island](https://commons.wikimedia.org/w/index.php?curid=141802237) | 3198 × 1758 |
| 316 | Willem Maris | [Koeien bij een plas](https://commons.wikimedia.org/w/index.php?curid=34402003) | 7852 × 4398 |
| 317 | Willem Roelofs | [De brug over de IJssel bij Doesburg](https://commons.wikimedia.org/w/index.php?curid=83488675) | 5636 × 3102 |
| 318 | William Logsdail | [The Piazza of Saint Mark's, Venice](https://commons.wikimedia.org/w/index.php?curid=119915189) | 3999 × 2276 |
| 319 | William Penhallow Henderson | [Noon](https://commons.wikimedia.org/w/index.php?curid=39655981) | 3476 × 1944 |
| 320 | Amaldus Nielsen | [Norwegian: Fjordparti](https://commons.wikimedia.org/w/index.php?curid=5702693) | 3654 × 2103 |
| 321 | Amaldus Nielsen | [People on a Beach](https://commons.wikimedia.org/w/index.php?curid=5703012) | 3688 × 2044 |
| 322 | Henryk Siemiradzki | [By the fountain](https://commons.wikimedia.org/w/index.php?curid=28939444) | 4000 × 2258 |
| 323 | Hjalmar Munsterhjelm | [November Evening](https://commons.wikimedia.org/w/index.php?curid=93161707) | 4000 × 2255 |
| 324 | Hjalmar Munsterhjelm | [Shepherd in the Alps](https://commons.wikimedia.org/w/index.php?curid=93166146) | 4738 × 2679 |
| 325 | Max Liebermann | [Max Liebermann, Kinderspielplatz im Tiergarten zu Berlin, 1885](https://commons.wikimedia.org/w/index.php?curid=3734328) | 3000 × 1725 |
| 326 | Bruno Liljefors | [Winter hunting with fox and scent hound](https://commons.wikimedia.org/w/index.php?curid=111254556) | 3000 × 1666 |
| 327 | Carl Spitzweg | [Woman bath in Dieppe I](https://commons.wikimedia.org/w/index.php?curid=29456789) | 4774 × 2656 |
| 328 | James McNeill Whistler | [Chelsea Shops](https://commons.wikimedia.org/w/index.php?curid=13318993) | 3459 × 1965 |
| 329 | James McNeill Whistler | [The Note in Orange and Blue (Sweet Shop)](https://commons.wikimedia.org/w/index.php?curid=97946973) | 3000 × 1720 |
| 330 | Peder Severin Krøyer | [Artists' lunch. Cernay-la-Ville](https://commons.wikimedia.org/w/index.php?curid=91996431) | 3000 × 1655 |
| 331 | Berndt Lindholm | [View from Hisingen near Gothenburg](https://commons.wikimedia.org/w/index.php?curid=66316616) | 4000 × 2210 |
| 332 | Charles-François Daubigny | [C F d'Aubigny coucher de soleil à Villerville 1874](https://commons.wikimedia.org/w/index.php?curid=74317600) | 3675 × 2047 |
| 333 | Charles-François Daubigny | [La Tamise à Erith.](https://commons.wikimedia.org/w/index.php?curid=148294579) | 10755 × 6048 |
| 334 | Charles-François Daubigny | [The Barges](https://commons.wikimedia.org/w/index.php?curid=31231760) | 3714 × 2126 |
| 335 | Charles-François Daubigny | [The Edge of the Pond](https://commons.wikimedia.org/w/index.php?curid=84964046) | 4083 × 2308 |
| 336 | Eugène Boudin | [Beach at Trouville](https://commons.wikimedia.org/w/index.php?curid=38305052) | 3420 × 1960 |
| 337 | Eugène Boudin | [Trouville, Umbrellas on the Beach](https://commons.wikimedia.org/w/index.php?curid=156053927) | 17452 × 10000 |
| 338 | Pierre-Auguste Renoir | [Odalisque](https://commons.wikimedia.org/w/index.php?curid=3418534) | 11263 × 6306 |
| 339 | Winslow Homer | [A Clam-Bake](https://commons.wikimedia.org/w/index.php?curid=24834582) | 5000 × 2862 |
| 340 | Winslow Homer | [View of Santiago de Cuba](https://commons.wikimedia.org/w/index.php?curid=81494329) | 4000 × 2197 |
| 341 | Abraham Govaerts | [Forest View with Travellers](https://commons.wikimedia.org/w/index.php?curid=36994951) | 6000 × 3422 |
| 342 | Aert van der Neer | [Panoramic landscape](https://commons.wikimedia.org/w/index.php?curid=168187155) | 5093 × 2871 |
| 343 | Aert van der Neer | [River view at sunrise](https://commons.wikimedia.org/w/index.php?curid=34249308) | 6554 × 3634 |
| 344 | Aleksander Gierymski | [Piazza di Dante in Verona Piazza di Dante in Verona](https://commons.wikimedia.org/w/index.php?curid=98844700) | 4000 × 2217 |
| 345 | Alexander Keirincx | [Forest landscape](https://commons.wikimedia.org/w/index.php?curid=48912323) | 5757 × 3317 |
| 346 | Alfred Elsen | [Heath Landscape in the Kempen](https://commons.wikimedia.org/w/index.php?curid=140185641) | 3433 × 1965 |
| 347 | Andries van Eertvelt | [River view with boats, a pier and figures](https://commons.wikimedia.org/w/index.php?curid=94228640) | 3689 × 2029 |
| 348 | Anton Altmann | [River landscape](https://commons.wikimedia.org/w/index.php?curid=38800278) | 3842 × 2142 |
| 349 | Antoni Viladomat i Manalt | [Spring](https://commons.wikimedia.org/w/index.php?curid=21926206) | 4801 × 2744 |
| 350 | Archibald Thorburn | [Wigeon and Teal by the water's edge](https://commons.wikimedia.org/w/index.php?curid=56403724) | 3308 × 1901 |
| 351 | August Kopisch | [The Pontine Marshes at Sunset](https://commons.wikimedia.org/w/index.php?curid=127787179) | 4016 × 2235 |
| 352 | Auguste Borget | [Moonlit Scene of Indian Figures and Elephants among Banyan Trees, Upper India (probably Lucknow)](https://commons.wikimedia.org/w/index.php?curid=22131271) | 3802 × 2188 |
| 353 | Bonaventura Peeters the Elder | [Entrance to a port with merchant ships and fishing boats](https://commons.wikimedia.org/w/index.php?curid=95308144) | 6149 × 3418 |
| 354 | Charles Brooking | [The Capture of the 'Marquise d'Antin' and 'Louis Erasme' by the English Privateers 'Duke' and 'Prince Frederick', 10 July 1745](https://commons.wikimedia.org/w/index.php?curid=87535883) | 7200 × 4073 |
| 355 | Charles William Wyllie | [On the way to the festival](https://commons.wikimedia.org/w/index.php?curid=97649391) | 3200 × 1826 |
| 356 | Chen Chun | [Garden Flowers](https://commons.wikimedia.org/w/index.php?curid=84982407) | 3774 × 2145 |
| 357 | Claude Lorrain | [Die Anbetung des Goldenen Kalbes Landscape with the Adoration of the Golden Calf](https://commons.wikimedia.org/w/index.php?curid=38742234) | 6699 × 3807 |
| 358 | Claude Lorrain | [Landscape with Psyche Outside the Palace of Cupid](https://commons.wikimedia.org/w/index.php?curid=50712491) | 7404 × 4226 |
| 359 | Conrad Wise Chapman | [Mexico City](https://commons.wikimedia.org/w/index.php?curid=98555386) | 3200 × 1814 |
| 360 | Cornelius van Poelenburgh | [Mercury bringing Psyche to Mount Olympus](https://commons.wikimedia.org/w/index.php?curid=82345341) | 6260 × 3540 |
| 361 | David Roberts | [Edinburgh from the Castle](https://commons.wikimedia.org/w/index.php?curid=21974819) | 4045 × 2269 |
| 362 | Dirck Dalens III | [Mountain landscape with shepherds](https://commons.wikimedia.org/w/index.php?curid=47820766) | 4231 × 2382 |
| 363 | Eduard Gaertner | [Eosanderhof des Koeniglichen Schlosses Berlin](https://commons.wikimedia.org/w/index.php?curid=6352691) | 3629 × 2057 |
| 364 | Eduard Gaertner | [The Friedrichsgracht, Berlin](https://commons.wikimedia.org/w/index.php?curid=91895724) | 6000 × 3387 |
| 365 | Erasmus Quellinus II | [Labore et constantia](https://commons.wikimedia.org/w/index.php?curid=36687919) | 4178 × 2391 |
| 366 | Ercole Calvi | [Famiglia pescatore a Lecco sul lago di Como](https://commons.wikimedia.org/w/index.php?curid=22080926) | 4941 × 2836 |
| 367 | Ferdinand Bellermann | [Bathers on the river (evening on the Orinoco?)](https://commons.wikimedia.org/w/index.php?curid=64222325) | 3339 × 1845 |
| 368 | Florine Hyer | [Floral Still Life with Roses](https://commons.wikimedia.org/w/index.php?curid=99178392) | 3000 × 1720 |
| 369 | Francesco Giuseppe Casanova | [Cattle on pasture.](https://commons.wikimedia.org/w/index.php?curid=17486199) | 3000 × 1729 |
| 370 | Francesco Giuseppe Casanova | [Ferry Boat](https://commons.wikimedia.org/w/index.php?curid=22000304) | 3301 × 1869 |
| 371 | Franz Bunke | [Dinghies at the bank of the Warnow river](https://commons.wikimedia.org/w/index.php?curid=144713672) | 4465 × 2480 |
| 372 | François Boucher | [Music and Dance and Cupids in Conspiracy](https://commons.wikimedia.org/w/index.php?curid=76004561) | 3400 × 1896 |
| 373 | Friedrich Carl von Scheidlin | [View of St. Johann](https://commons.wikimedia.org/w/index.php?curid=67488003) | 4747 × 2649 |
| 374 | Félix Ziem | [L'éléphant](https://commons.wikimedia.org/w/index.php?curid=98111580) | 5763 × 3189 |
| 375 | Gaspard Dughet | [Landscape with a Herdsman and Goats](https://commons.wikimedia.org/w/index.php?curid=74092705) | 3000 × 1668 |
| 376 | George Cuitt | [Easby Hall and Easby Abbey with Richmond, Yorkshire in the Background](https://commons.wikimedia.org/w/index.php?curid=22155057) | 6504 × 3743 |
| 377 | George Hamilton | [The first steeplechase in South Australia, 25 September 1846](https://commons.wikimedia.org/w/index.php?curid=23600762) | 5757 × 3313 |
| 378 | Georges Washington | [The hunt](https://commons.wikimedia.org/w/index.php?curid=56396968) | 3756 × 2066 |
| 379 | Giovanni Antonio Canal | [London: The Thames from Somerset House Terrace towards the City](https://commons.wikimedia.org/w/index.php?curid=22007023) | 5501 × 3092 |
| 380 | Giovanni Antonio Canal | [The Piazza San Marco, Venice](https://commons.wikimedia.org/w/index.php?curid=21997566) | 4995 × 2785 |
| 381 | Giovanni Antonio Guardi | [Tobias fishing with the Archangel Raphael](https://commons.wikimedia.org/w/index.php?curid=152417) | 3200 × 1809 |
| 382 | Giovanni Bellini | [Madonna and Child with Saints](https://commons.wikimedia.org/w/index.php?curid=145712376) | 5506 × 3163 |
| 383 | Giovanni di Paolo | [The Adoration of the Magi](https://commons.wikimedia.org/w/index.php?curid=81323136) | 4000 × 2277 |
| 384 | Hendrick Avercamp | [Winter Landscape with Skaters near a Village](https://commons.wikimedia.org/w/index.php?curid=64156385) | 3600 × 2015 |
| 385 | Hendrick Avercamp | [Winter Scene on a Frozen Canal](https://commons.wikimedia.org/w/index.php?curid=21909482) | 5659 × 3230 |
| 386 | Hendrick Cornelisz Vroom | [Arrival of a Dutch Three master at Schloss Kronberg](https://commons.wikimedia.org/w/index.php?curid=164566500) | 4000 × 2218 |
| 387 | Henri Rousseau | [Le Guerre (War) by Henri Rousseau, c. 1894, oil on canvas - The Carnival of Being (Alfred Jarry at the Morgan) - Morgan Library & Museum - New York City - DSC06832](https://commons.wikimedia.org/w/index.php?curid=87218467) | 4659 × 2648 |
| 388 | Hippolyte Camille Delpy | [The poppy field](https://commons.wikimedia.org/w/index.php?curid=97326195) | 3200 × 1784 |
| 389 | Ippolito Caffi | [Eclips of the Sun in Venice in July 8, 1842](https://commons.wikimedia.org/w/index.php?curid=82980105) | 4134 × 2301 |
| 390 | J. M. W. Turner | [Carlisle](https://commons.wikimedia.org/w/index.php?curid=22213382) | 3160 × 1820 |
| 391 | Jacob Adriaensz Bellevois | [A French squadron near a rocky coast](https://commons.wikimedia.org/w/index.php?curid=83508719) | 6352 × 3504 |
| 392 | Jacob Gerritsz. Cuyp | [Herderin met kind in een landschap](https://commons.wikimedia.org/w/index.php?curid=126454056) | 4288 × 2416 |
| 393 | Jakob Alt | [View of Vienna from the Spinner on the Cross, 1817](https://commons.wikimedia.org/w/index.php?curid=21793150) | 3738 × 2114 |
| 394 | James Ward | [A Harvest Scene with Workers Loading Hay on to a Farm Wagon](https://commons.wikimedia.org/w/index.php?curid=21994867) | 4582 × 2572 |
| 395 | James Wilson Carmichael | [A blustery day on the Brill, near Rotterdam](https://commons.wikimedia.org/w/index.php?curid=97342281) | 3200 × 1766 |
| 396 | Jan Victors | [In front of a tavern](https://commons.wikimedia.org/w/index.php?curid=98812941) | 4000 × 2203 |
| 397 | Jan van Goyen | [Dunelandscape](https://commons.wikimedia.org/w/index.php?curid=164565576) | 4000 × 2258 |
| 398 | Jean-Auguste-Dominique Ingres | [Grande Odalisque](https://commons.wikimedia.org/w/index.php?curid=162395660) | 9311 × 5196 |
| 399 | Joachim Patinir | [Saint Jerome in the Desert](https://commons.wikimedia.org/w/index.php?curid=15417145) | 4508 × 2517 |
| 400 | Johan Lundbye | [Outside the cowshed](https://commons.wikimedia.org/w/index.php?curid=65673517) | 5785 × 3245 |
