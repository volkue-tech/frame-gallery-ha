"""Curated modern-art metadata, not image assets (D-206).

Selection researched on Commons on 2026-10-05. Two unresolved US-tag files
were replaced by Klee, Before the Town and Deep Pathos (PD-old-auto-expired).
The original image SHA-1 pins the visually selected upload, not a licence.
Runtime separately rechecks the current rights labels and rendition bounds.
Source pages: https://commons.wikimedia.org/w/index.php?curid=<page_id>.
No artwork file is bundled. Artwork metadata is not covered by our code licence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class CuratedWork:
    page_id: int
    file_title: str
    sha1: str
    title: str
    artist: str


CATALOG: Final = (
    CuratedWork(
        38658125,
        "File:Kandinsky - Jaune Rouge Bleu.jpg",
        "c7cbc878c56ebe673ad646330b2d54eb4b2419c7",
        "Gelb-Rot-Blau",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        77963326,
        "File:Wassily Kandinsky Composition VIII.jpg",
        "4b948b6fbb0c963258238eeba08c3b49f5b32e60",
        "Composition VIII",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        178839132,
        "File:Composition VII - Wassily Kandinsky, GAC.jpg",
        "d891d53b6be42e84331dd6af30e44d5f3d38b1bb",
        "Composition VII",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        29848354,
        "File:Wassily Kandinsky - Impression III (Concert) - Google Art Project.jpg",
        "1960047f4b497f57a25d58129a19025161ac6d1f",
        "Impression III (Concert)",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        63967344,
        "File:Kandinsky Oriental PA291007.jpg",
        "801842d4dbf80b114fa7f19caf3c4e3b01fa5d6e",
        "Oriental",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        64165646,
        "File:Kandinsky Eisenbahn bei Murnau PA291090.jpg",
        "2f49400254f3c1e81fe80bc59c51d54119a9ab7e",
        "Eisenbahn bei Murnau",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        81370185,
        "File:Wassily Kandinsky - Inner Alliance - 1929.jpg",
        "51612c90d8b2aec12f35daa779c42fce58128025",
        "Inner Alliance",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        68718058,
        "File:Кандинский Импровизация 3.jpg",
        "d651fef502d1751d7be31b6d93fcf18ee379e146",
        "Improvisation III",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        57396257,
        "File:Improvisation 27 (Garden of Love II) MET DP236124.jpg",
        "437541205afc17d3d7da3c4eaea4c8f01b9cb1dc",
        "Improvisation 27 (Garden of Love II)",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        75969059,
        "File:Improvisation XIV.jpg",
        "c3cf36f50515c8aba270a19c43b4ec2b502d027f",
        "Improvisation XIV",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        81502097,
        "File:Kandinsky - Little Painting with Yellow (Improvisation), 1914.jpg",
        "193af5d93549a20d7d7068cc2f2bd9af5dc1087f",
        "Little Painting with Yellow (Improvisation)",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        40213893,
        "File:Kandinsky, 1913, Sans titre (Etude pour Composition VII, Première abstraction).jpg",
        "23b3cded7da27b331f4e9c01444174ae83b1b833",
        "Untitled (Study for Composition VII, First Abstract Watercolor)",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        60907495,
        "File:Bird Landscape, 1925 - Paul Klee, MET DT7813.jpg",
        "a9fbf50aef51a77b8a5a22f76f0b54e18a17ecec",
        "Bird Landscape",
        "Paul Klee",
    ),
    CuratedWork(
        60907266,
        "File:Libido of the Forest, 1917 - Paul Klee, MET DT7781.jpg",
        "51ba8b6b8b40e9d49ed2ac17a910bb3a320db4ee",
        "Libido of the Forest",
        "Paul Klee",
    ),
    CuratedWork(
        116266220,
        "File:Kristall-Stufung, Paul Klee (1921).jpg",
        "8fb41b936be88613369de81389d4eac14e62017c",
        "Kristall-Stufung",
        "Paul Klee",
    ),
    CuratedWork(
        60909655,
        "File:Lovers, 1920 - Paul Klee, MET DT5833.jpg",
        "65521d75a0b39a8f2f574582f139d34a90ce257c",
        "Lovers",
        "Paul Klee",
    ),
    CuratedWork(
        14618617,
        "File:Heitere Gebirgslandschaft by Paul Klee 1929.jpeg",
        "7af042a5e296f266ccaf57ed114f815f89915302",
        "Heitere Gebirgslandschaft",
        "Paul Klee",
    ),
    CuratedWork(
        57858012,
        "File:Temple Gardens, 1920 - Paul Klee, MET DT1372.jpg",
        "d5f431b961e3ef84238a15b60889b87f016d638d",
        "Temple Gardens",
        "Paul Klee",
    ),
    CuratedWork(
        60909664,
        "File:All Souls' Picture, 1921 - Paul Klee, MET DT5835.jpg",
        "50f251539276b8115464e53b8e6ace59c0cc809b",
        "All Souls' Picture",
        "Paul Klee",
    ),
    CuratedWork(
        60907263,
        "File:Episode at Kairouan, 1920 - Paul Klee, MET DT7787.jpg",
        "3b1e1e5c3887a1bc1fe864851fcbbcfbac5cd724",
        "Episode at Kairouan",
        "Paul Klee",
    ),
    CuratedWork(
        60907260,
        "File:Municipal Jewel, 1917 - Paul Klee, MET DT7782.jpg",
        "caffc6ea1ba1becdd214ff4d7c0358c2d68fbfd5",
        "Municipal Jewel",
        "Paul Klee",
    ),
    CuratedWork(
        60907365,
        "File:Yellow Harbor, 1921 - Paul Klee, MET DT7794.jpg",
        "c5da30e9687158e42589b51b89acaa68c75ca57e",
        "Yellow Harbor",
        "Paul Klee",
    ),
    CuratedWork(
        60907399,
        "File:Abstract Trio, 1923 - Paul Klee, MET DT1769.jpg",
        "8b6a7e30316e0595a1e92e42f766d30060ee08c2",
        "Abstract Trio",
        "Paul Klee",
    ),
    CuratedWork(
        60909673,
        "File:Cold City, 1921 - Paul Klee, MET DP-818-001.jpg",
        "363b32713431bfe6a16205f73520e2da7be2c667",
        "Cold City",
        "Paul Klee",
    ),
    CuratedWork(
        57396122,
        "File:Still Life, 1927 - Paul Klee, MET DP-829-001.jpg",
        "b13dabf83970c307942444a56974c19396f786a0",
        "Still Life",
        "Paul Klee",
    ),
    CuratedWork(
        86755478,
        "File:Landscape with Bluebirds, 1919 - Paul Klee.jpg",
        "ab4393090b3ba403de03963bb8ea73a11f5a3d45",
        "Landscape with Bluebirds",
        "Paul Klee",
    ),
    CuratedWork(
        48694617,
        "File:Robert Delaunay, 1915 - Nature morte portugaise.jpg",
        "1844342b517e380e4bf359e5ebbc3342c46a364d",
        "Nature morte portugaise",
        "Robert Delaunay",
    ),
    CuratedWork(
        58345593,
        "File:Robert Delaunay, 1911-12, Window on the City No. 3, Solomon R. Guggenheim Museum.jpg",
        "dc67490afa07ea2577865099d7c28bacd55c6599",
        "Window on the City No. 3",
        "Robert Delaunay",
    ),
    CuratedWork(
        40026322,
        "File:GUGG Windows Open Simultaneously 1st Part, 3rd Motif.jpg",
        "c5f2cb6e178ea0d441ca8bb5c35aa482ad76704b",
        "Windows Open Simultaneously, 1st Part, 3rd Motif",
        "Robert Delaunay",
    ),
    CuratedWork(
        40181676,
        "File:GUGG Carousel of Pigs.jpg",
        "add346a6d9994af69ff59993a2a3fc5d09d63d84",
        "Carousel of Pigs",
        "Robert Delaunay",
    ),
    CuratedWork(
        63967587,
        "File:Marc Weidende Pferde I PA291029.jpg",
        "b391dfbf2414207beb3806aa472055b76447f9f9",
        "Weidende Pferde I",
        "Franz Marc",
    ),
    CuratedWork(
        29848498,
        "File:Marc, Franz - Deer in a Monastery Garden - Google Art Project.jpg",
        "cad29007580f87c531c4f67434deb556e7e5a133",
        "Deer in a Monastery Garden",
        "Franz Marc",
    ),
    CuratedWork(
        5213136,
        "File:Franz Marc Drei Tiere.jpg",
        "183266bd17f48a4c5eba73ad8ac3308d94d5b7b1",
        "Drei Tiere",
        "Franz Marc",
    ),
    CuratedWork(
        149769813,
        "File:Franz Marc Liegender Hund (Russi) 1909.jpg",
        "eeeea725166d759ef63b3b48c2e68cd9ee38671b",
        "Liegender Hund (Russi)",
        "Franz Marc",
    ),
    CuratedWork(
        64064543,
        "File:August Macke Zoologischer Garten I PA291076.jpg",
        "611acd7f27f50abe21b4ed8832abfdbb73874279",
        "Zoologischer Garten I",
        "August Macke",
    ),
    CuratedWork(
        64064766,
        "File:Macke Indianer auf Pferden PA291080.jpg",
        "5eaf14f9cd149733ec9deaf04603b89bb41b0dfb",
        "Indianer auf Pferden",
        "August Macke",
    ),
    CuratedWork(
        10711362,
        "File:August Macke - Garten am Thunersee.jpeg",
        "ec2fddf1bd70e7187ab973b858ed8ddabb8dc731",
        "Garten am Thunersee",
        "August Macke",
    ),
    CuratedWork(
        163922085,
        "File:August Macke Sonniger Garten 1908.jpg",
        "d15cb6ec4db134931e1fcd7b9669f83fbbaf4cd1",
        "Sonniger Garten",
        "August Macke",
    ),
    CuratedWork(
        158615407,
        "File:August Macke Sandgrube 1911.jpg",
        "5f2d9517b2eb8f7925cf6ea58eca6b6754d715e1",
        "Sandgrube",
        "August Macke",
    ),
    CuratedWork(
        3817033,
        "File:Theo van Doesburg Contra-Composition XVI.jpg",
        "98171a919603525af22fe941950c853922e9c211",
        "Counter-composition XVI",
        "Theo van Doesburg",
    ),
    CuratedWork(
        21930785,
        "File:Theo van Doesburg - Card players - Google Art Project.jpg",
        "6fa47371cc8f5c6d41050dbcb1dcf68e5e57464c",
        "Card Players",
        "Theo van Doesburg",
    ),
    CuratedWork(
        21925604,
        "File:Ernst Ludwig Kirchner - Czardas dancers - Google Art Project.jpg",
        "c7de686468e23f5c0987b3bbd572ddb01fc1c1fc",
        "Czardas Dancers",
        "Ernst Ludwig Kirchner",
    ),
    CuratedWork(
        64580978,
        "File:Ernst Ludwig Kirchner - Interieur mit Mahler 1280945.jpg",
        "418b8a72f0413a0b17459984a9351dfe407f038e",
        "Interieur mit Maler",
        "Ernst Ludwig Kirchner",
    ),
    CuratedWork(
        103327113,
        "File:Ernst Ludwig Kirchner - Eisenbahnüberführung Löbtauer Straße in Dresden.jpg",
        "71fed4c53b783882778c5ddcaf6ca7f335b25f5b",
        "Eisenbahnüberführung Löbtauer Straße in Dresden",
        "Ernst Ludwig Kirchner",
    ),
    CuratedWork(
        177602382,
        "File:Ernst Ludwig Kirchner Russisches Tänzerpaar 1909.jpg",
        "fd45c1b74fdb82793b1b0fa85a558d7be86c1a0d",
        "Russisches Tänzerpaar",
        "Ernst Ludwig Kirchner",
    ),
    CuratedWork(
        489515,
        "File:Signac - Portrait de Félix Fénéon.jpg",
        "178601179935a908dee29598cdbec25646a471ab",
        "Portrait de Félix Fénéon (Opus 217)",
        "Paul Signac",
    ),
    CuratedWork(
        21931618,
        "File:Paul Signac - Cassis, Cap Lombard, Opus 196 - Google Art Project.jpg",
        "453f1a9171a2eea788d267a030a702a91d9e4107",
        "Cassis, Cap Lombard (Opus 196)",
        "Paul Signac",
    ),
    CuratedWork(
        80519258,
        "File:Paul Signac - Antibes - BF729 - Barnes Foundation.jpg",
        "1d17fa722bb8352530404169d44becb3dd3cc6ab",
        "Antibes",
        "Paul Signac",
    ),
    CuratedWork(
        60907526,
        "File:Before the Town, 1915 - Paul Klee, MET DT7777.jpg",
        "18bf9d3a24dbd2ace51f26a4ccbc64c0f950e1c9",
        "Before the Town",
        "Paul Klee",
    ),
    CuratedWork(
        60907632,
        "File:Deep Pathos, 1915 - Paul Klee, MET DT7778.jpg",
        "505fd2d05910e1881bf0da896706bcc04f8ff9bd",
        "Deep Pathos",
        "Paul Klee",
    ),
)
