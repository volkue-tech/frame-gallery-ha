# Wikimedia Commons selection

> **0.1.0b4:** 166 curated near-widescreen works from 112 artist labels.
> Update the existing app; do not uninstall it or reset its history.

## What you get

A broad, colourful selection of modern classics, landscapes, still lifes,
seascapes and older paintings. Each source is at least 3000 pixels wide and
within 2.5% of the 16:9 screen ratio. This replaces b3's 50-work, broad-ratio
selection, including works that previously left substantial side margins.
No account, API key, new helper or dashboard extension is needed.

Select **Artwork source → wikimedia_commons**, keep **Landscape only** on and
**Image fit = contain** to preserve the whole artwork. Leave **Prefer 16:9** on
for the closest matches, or turn it off for the whole curated selection.

**2.5% selection is not the same as the app's strict 16:9 preference.** That
preference still means about 1%; 67 of these 166 sources meet it. The existing
bounded fallback can show the other near-widescreen works without cropping.
Small margins, or margins already present in a source scan, can remain.
There is no new configuration option and no change to your saved options.

![Actual Commons dashboard preview with optional artist/title information](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/dashboard-commons.png)

*Historical b3 Green screenshot: Theo van Doesburg,
[Counter-composition XVI](https://commons.wikimedia.org/w/index.php?curid=3817033).
This work remains in b4. The expanded b4 selection has not been TV-tested
work by work. See the [b3 live-test scope](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA3_VALIDATION.md).*

Department, period, style and colour filters are not supported for Commons.
Set them to `any`; unsupported filters are reported as ignored. Curated artist
labels are not an artist/style-filter API.

## Quality, storage and history

The app obtains a JPEG rendition no wider or taller than 3840 pixels; it never
uses an oversized original as a fallback. A 4K output canvas does not create
detail absent from the source. Very large originals remain on Commons.

Only small metadata entries are bundled. Each run downloads its candidate into
bounded temporary storage and cleans up. It retains the current preview and
bounded history, not 166 downloaded originals. Existing history IDs stay
`commons:<pageid>`: a previously sent work does not become new after updating.

Discovery samples at most ten paced five-record metadata requests per run,
within the existing request/time limits. Permanently sent works are omitted
from those requests. This does not promise an exhaustive catalogue scan in
each run. With no eligible new work, the app ends cleanly rather than retrying
forever or automatically recycling already sent art.

## Rights and research

All 200 research proposals, source identities and deferred-item reasons are
retained in the [metadata-only research manifest](research/commons-wide-selection-2026-10-06.json).
The local scrolling preview remains a research tool, not the release catalogue.
166 proposals are included; 34 remain deferred for source-rights, scan/work
proportion review or PNG/TIFF source format. The adapter remains JPEG-only.
In particular, the 1937 Beckmann proposal is not released:
its displayed licence template conflicts with the artwork date.

Commons public-domain/CC0 labels and source-page evidence were reviewed on
2026-10-05/06. This is **not worldwide legal clearance**; jurisdictions differ.
The app rechecks current rights, exact file/page identity and pinned upload
hash on every run. Missing, restricted, changed or unverifiable files are
skipped. Additional CC BY/CC BY-SA claims remain outside this selection.
Artwork is not relicensed under the project's Apache licence.

The project contact `volkue+commonsapi@gmail.com` is sent to Commons and its
allowed image hosts in request headers. It is not a user's email or an API key.

## The 166 works

Original source dimensions below are not a claim of TV-tested detail.
The runtime downloads bounded renditions, not the listed originals.

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

## Technical references

- [MediaWiki Imageinfo API](https://www.mediawiki.org/wiki/API:Imageinfo)
- [Wikimedia API usage guidelines](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_API_Usage_Guidelines)
- [Commons reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia)
- [Two-country public-domain template](https://commons.wikimedia.org/wiki/Template:PD-Art-two-auto)
- [CC0 dedication](https://creativecommons.org/publicdomain/zero/1.0/)

No image files, raw HTML or arbitrary category queries are bundled. No Home
Assistant configuration or TV state is changed merely by updating the catalogue.
