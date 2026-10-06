"""Pinned near-widescreen Commons metadata (D-209, researched 2026-10-05/06).

166 reviewed entries from 200 private proposals; no image bytes are bundled.
Research/provenance and deferred entries:
frame_gallery/research/commons-wide-selection-2026-10-06.json.
This catalogue replaces b3's broad-ratio set without changing permanent history IDs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class CuratedWork:
    page_id: int
    file_title: str
    sha1: str
    title: str
    artist: str


CATALOG: Final = (
    CuratedWork(
        3817033,
        "File:Theo van Doesburg Contra-Composition XVI.jpg",
        "98171a919603525af22fe941950c853922e9c211",
        "Counter-composition XVI",
        "Theo van Doesburg",
    ),
    CuratedWork(
        84632826,
        "File:Kandinsky - Ev\xe9nement doux (Milder Vorgang), 1928.jpg",
        "485470519a0fbeac2b941da57aad4b5b2c314f74",
        "Milder Vorgang / Gentle Event",
        "Wassily Kandinsky",
    ),
    CuratedWork(
        176674544,
        (
            "File:Edvard Munch - Two Human Beings. The Lonely Ones (The Reinhardt Friez"
            "e) (1906-07).jpg"
        ),
        "5d6415d4bda00d07f18c5d894386dd991e853248",
        "Zwei Menschen. Die Einsamen (Reinhardt-Fries)",
        "Edvard Munch",
    ),
    CuratedWork(
        65361933,
        "File:Pierre bonnard plage.jpg",
        "79f514a50ebc5ad6939c2453652e723794dde912",
        "Plage",
        "Pierre Bonnard",
    ),
    CuratedWork(
        180643370,
        (
            "File:L'\xe9glise rose - Tilloloy - Maurice Denis - Wallraf-Richartz-Museum"
            " & Fondation Corboud (without frame)-5973 (without frame).jpg"
        ),
        "43020e2307d8bfeafaf573b14bb2975da7118660",
        "L\u2019\xe9glise rose \u2013 Tilloloy",
        "Maurice Denis",
    ),
    CuratedWork(
        65236294,
        "File:Hassam - california.jpg",
        "235825ccde19e31648123354d0148a34d40af41d",
        "California",
        "Childe Hassam",
    ),
    CuratedWork(
        39846917,
        "File:Montmartre molens en moestuinen - s0015V1962 - Van Gogh Museum.jpg",
        "0336841ee751a179863e49acc447e9f5c819393d",
        "Montmartre: Windmills and Allotments",
        "Vincent van Gogh",
    ),
    CuratedWork(
        21897337,
        "File:Camille Pissarro - The Harvest - Google Art Project.jpg",
        "77e197d97bcf67e80be33997737f42c842ec2a61",
        "La Moisson / The Harvest",
        "Camille Pissarro",
    ),
    CuratedWork(
        76401733,
        "File:Renoir - Le sentier dans la for\xeat, 1901-1902.jpg",
        "cfa6a421b2e1f71938a465ce6858abe9e022a287",
        "Le sentier dans la for\xeat, trois personnages",
        "Pierre-Auguste Renoir",
    ),
    CuratedWork(
        57673290,
        "File:Three Tahitian Women MET DT1954.jpg",
        "d218d81078165ee74a86f78e8f9b6762aacb4c12",
        "Three Tahitian Women",
        "Paul Gauguin",
    ),
    CuratedWork(
        149144,
        "File:Pichet et fruits sur une table, par Paul C\xe9zanne, Yorck.jpg",
        "366686bee1516bdfb5525ba2a8255fb146980a90",
        "Krug und Fr\xfcchte auf einem Tisch",
        "Paul C\xe9zanne",
    ),
    CuratedWork(
        67540714,
        (
            "File:Paul C\xe9zanne - Plate with Fruit and Pot of Preserves (Assiette ave"
            "c fruits et pot de conserves) - BF50 - Barnes Foundation.jpg"
        ),
        "b4303dd0d95d08f9cc45a0f051c344fab3e2943d",
        "Plate with Fruit and Pot of Preserves",
        "Paul C\xe9zanne",
    ),
    CuratedWork(
        67540512,
        (
            "File:Pierre-Auguste Renoir - Apples and Lemons on a Cloth (Pommes et citro"
            "ns sur une nappe) - BF27 - Barnes Foundation.jpg"
        ),
        "5bb243cd7daf86ca7210d41c4bdd8d76fe85d270",
        "Apples and Lemons on a Cloth",
        "Pierre-Auguste Renoir",
    ),
    CuratedWork(
        67540290,
        (
            "File:Pierre-Auguste Renoir - Strawberries and Almonds (Fraises et amandes)"
            " - BF99 - Barnes Foundation.jpg"
        ),
        "48fabac920348071775b48acad078a143cddcdab",
        "Strawberries and Almonds",
        "Pierre-Auguste Renoir",
    ),
    CuratedWork(
        67540189,
        ("File:Pierre-Auguste Renoir - Pomegranates (Grenades) - BF29 - Barnes Foundation.jpg"),
        "56e6a8fcb51e6ef765a44af3a58228c0ec99d296",
        "Pomegranates",
        "Pierre-Auguste Renoir",
    ),
    CuratedWork(
        76362525,
        "File:Renoir - NATURE MORTE AUX ROSES, 1918.jpg",
        "e139548fb1e1dc1073fcd6af255c17f97b6b4685",
        "Nature morte aux roses",
        "Pierre-Auguste Renoir",
    ),
    CuratedWork(
        76401773,
        "File:Renoir - Mandarines et tasse, circa 1910.jpg",
        "8df548c44f9443b5ee2104be49964389377e98d0",
        "Mandarines et tasse",
        "Pierre-Auguste Renoir",
    ),
    CuratedWork(
        67540557,
        (
            "File:Pierre-Auguste Renoir - Pomegranate and Figs (Grenade et figues) - BF"
            "24 - Barnes Foundation.jpg"
        ),
        "322ab270cb6cc5889a9f918e0b27104072d574e1",
        "Pomegranate and Figs",
        "Pierre-Auguste Renoir",
    ),
    CuratedWork(
        124030464,
        "File:The Meteor of 1860.jpg",
        "f38e53d58696a66b2527187851dea9a341ad25b6",
        "The Meteor of 1860",
        "Frederic Edwin Church",
    ),
    CuratedWork(
        4766414,
        "File:Cotopaxi church.jpg",
        "f21a82279effd4ca39ce506cbf585d2730a9c39b",
        "Cotopaxi",
        "Frederic Edwin Church",
    ),
    CuratedWork(
        25702837,
        "File:The Icebergs (Frederic Edwin Church), 1861 (color).jpg",
        "2a15af6ccaa6d12400b7f8b51c68e253ed9a026e",
        "The Icebergs",
        "Frederic Edwin Church",
    ),
    CuratedWork(
        21885969,
        (
            "File:Thomas Moran, American (born England) - Grand Canyon of the Colorado "
            "River - Google Art Project.jpg"
        ),
        "50151b5be6520aa2b2b4d9c15134608c6ab0b36e",
        "Grand Canyon of the Colorado River",
        "Thomas Moran",
    ),
    CuratedWork(
        30592536,
        (
            "File:Thomas Moran - Great Blue Spring of the Lower Geyser Basin, Firehole "
            "River, Yellowstone (1872).jpg"
        ),
        "c60c77358e0ee17f00cfad3165fc6ed4bf1caf17",
        "Great Blue Spring, Yellowstone",
        "Thomas Moran",
    ),
    CuratedWork(
        185171326,
        "File:Whistler - Note in Red and Violet. Nets (1884) y269.jpeg",
        "6612e84f49b6e665401b84ffa3e3b918945b439c",
        "Note in Red and Violet: Nets",
        "James McNeill Whistler",
    ),
    CuratedWork(
        119873988,
        (
            "File:James Abbott McNeill Whistler - Blue and Silver, Dieppe - 1948.23 - N"
            "ew Britain Museum of American Art.jpg"
        ),
        "7c9c4f53523faa9e5589391e1b9b86f7414f6271",
        "Blue and Silver, Dieppe",
        "James McNeill Whistler",
    ),
    CuratedWork(
        8825940,
        "File:Fox Hunt 1893 Winslow Homer.jpg",
        "8fbc018b5b2d559546f4c68a36152c6415fd81e1",
        "Fox Hunt",
        "Winslow Homer",
    ),
    CuratedWork(
        24834545,
        "File:Winslow Homer - Boy with Anchor.jpg",
        "e5ecc57c4b964965e6089e83bfbeb879056169f7",
        "Boy with Anchor",
        "Winslow Homer",
    ),
    CuratedWork(
        38429749,
        "File:Winslow Homer - Surf at Prout's Neck (c.1895).jpg",
        "4a81ab0f18a682c581836e34298b6ec91f513ed1",
        "Surf at Prout\u2019s Neck",
        "Winslow Homer",
    ),
    CuratedWork(
        24175357,
        "File:Winslow Homer - The Watcher, Tynemouth.jpg",
        "37d4b552c5a70fdb070540492648d9c452840b49",
        "The Watcher, Tynemouth",
        "Winslow Homer",
    ),
    CuratedWork(
        118810806,
        "File:Winslow Homer - Woodland Stream (1895).jpg",
        "5d0fa0518edf8eaecde5d886aa90084b25d0267b",
        "Woodland Stream",
        "Winslow Homer",
    ),
    CuratedWork(
        114234017,
        "File:Winslow Homer - Towing the Boat (1878).jpg",
        "d532eb1f08310fee30c5ab441f91c31a5e797342",
        "Towing the Boat",
        "Winslow Homer",
    ),
    CuratedWork(
        173692244,
        "File:John Singer Sargent - On his Holidays, Norway (1901).jpg",
        "f40c28b1df3e963a660613fc91d270b3840db972",
        "On his Holidays, Norway",
        "John Singer Sargent",
    ),
    CuratedWork(
        57366268,
        "File:Cliffs at Deir el Bahri, Egypt MET DT212014.jpg",
        "c0f75375353e026c17e632cd8e935fab1b7850c3",
        "Cliffs at Deir el Bahri, Egypt",
        "John Singer Sargent",
    ),
    CuratedWork(
        149657860,
        "File:Joaqu\xedn Sorolla - Velas, Playa de Valencia.jpg",
        "6e479a8419f0a9a4cd6ed841aa8c0574415052b8",
        "Velas, Playa de Valencia",
        "Joaqu\xedn Sorolla",
    ),
    CuratedWork(
        19456667,
        "File:Joaqu\xedn Sorolla - Paisaje marino.jpg",
        "995fb527775270f5b484c57f18355e173c25d8da",
        "Paisaje marino",
        "Joaqu\xedn Sorolla",
    ),
    CuratedWork(
        34254029,
        "File:Een geit met haar jong Rijksmuseum SK-A-3346.jpeg",
        "1318f99da2201fcc1144be3841577e90c5cf8508",
        "Eine Ziege mit ihrem Jungen",
        "Giovanni Segantini",
    ),
    CuratedWork(
        21897036,
        "File:Giovanni Segantini - Bagpipers of Brianza - Google Art Project.jpg",
        "98cabb0e290acaf8d53e0a4d76e5d9c4855b9fc7",
        "Bagpipers of Brianza",
        "Giovanni Segantini",
    ),
    CuratedWork(
        82042536,
        ("File:Paul Gauguin, Mahna no Varua Ino (The Devil Speaks), 1894-1895, NGA 39312.jpg"),
        "373a78db38450bf522bab3e70d0b35eb4250ee67",
        "Mahna no Varua Ino (The Devil Speaks)",
        "Paul Gauguin",
    ),
    CuratedWork(
        72118951,
        "File:Tom Thomson Decorative Landscape.jpg",
        "5034579586f9ce58d3ce763ac2c6ed4d110285e2",
        "Decorative Landscape \u2013 Blessing by Robert Burns",
        "Tom Thomson",
    ),
    CuratedWork(
        138748673,
        "File:Lovis Corinth - Bacchantenzug (1896).jpg",
        "9e102bb369d2878d8e0dc1c8aba786fa82240cb7",
        "Bacchantenzug",
        "Lovis Corinth",
    ),
    CuratedWork(
        13507795,
        (
            "File:Mikhail Vrubel - \u0414\u0435\u043c\u043e\u043d (\u0441\u0438\u0434"
            "\u044f\u0449\u0438\u0439) - Google Art Project.jpg"
        ),
        "c991281b2de0edffd257bf2f81c5317b1a51b8f4",
        "D\xe4mon sitzend",
        "Mikhail Vrubel",
    ),
    CuratedWork(
        34313529,
        "File:Stilleven met vruchten en bloemen Rijksmuseum SK-A-2152.jpeg",
        "61faf32b56d9014bf037c2177e87cffb33e37ad0",
        "Still Life with Fruits and Flowers",
        "Balthasar van der Ast",
    ),
    CuratedWork(
        34321133,
        "File:Tulpenvelden Rijksmuseum SK-A-2890.jpeg",
        "10988763c2978f10ed855cac254dbac8a5182bd4",
        "Tulip Fields",
        "Gerrit Willem Dijsselhof",
    ),
    CuratedWork(
        44719383,
        "File:Modersohn Otto Mondaufgang im Moor@Weimar Schlossmuseum.JPG",
        "a8b362aed35564936b29f808f4efe9e2e4279757",
        "Mondaufgang im Moor",
        "Otto Modersohn",
    ),
    CuratedWork(
        80486236,
        (
            "File:Bruno Liljefors - Zilvermeeuwen en sterns op de scheren voor de Scand"
            "inavische kust - 0213 - Rijksmuseum Twenthe.jpg"
        ),
        "03543566c7dea6acea803770beb184388aed82cb",
        "Zilvermeeuwen en zeezwaluwen op de scheren voor de Scandinavische kust",
        "Bruno Liljefors",
    ),
    CuratedWork(
        178668227,
        "File:Carl Spitzweg Auf der Alm.jpg",
        "e0461ec0e581758d5da587ab1a95f65135abd3c6",
        "Auf der Alm",
        "Carl Spitzweg",
    ),
    CuratedWork(
        93485233,
        "File:Charles-Fran\xe7ois Daubigny - Alders.jpg",
        "71ea64331ee81b569db37b528d699905356bb3f9",
        "Alders",
        "Charles-Fran\xe7ois Daubigny",
    ),
    CuratedWork(
        153743085,
        "File:Environs d'Honfleur, paturage - EUG\xc8NE BOUDIN.jpg",
        "c1fe1008ec6936f64a138b75d1ed3ccb5308f66c",
        "Environs d\u2019Honfleur, p\xe2turage",
        "Eug\xe8ne Boudin",
    ),
    CuratedWork(
        45589856,
        (
            "File:Claude Monet - The Seashore at Sainte-Adresse - 53.13 - Minneapolis I"
            "nstitute of Arts.jpg"
        ),
        "e855f411b9dcfda265e265a8fefbaf28ba8cad88",
        "The Seashore at Sainte-Adresse",
        "Claude Monet",
    ),
    CuratedWork(
        150081,
        "File:Edgar Germain Hilaire Degas 041.jpg",
        "4cad8c0ffd457f01795753e36e8d14af0036ff5b",
        "Kleines M\xe4dchen wird am Meeresstrand von seiner Bonne gek\xe4mmt",
        "Edgar Degas",
    ),
    CuratedWork(
        81309991,
        "File:Edouard Manet, At the Races, c. 1875, NGA 1180.jpg",
        "af683776f22c1c2468ad6ef7247eb187f847328f",
        "At the Races",
        "\xc9douard Manet",
    ),
    CuratedWork(
        57364471,
        "File:Heart of the Andes MET DT78.jpg",
        "f4b94b14f7a20308b64aa49c70b1018413bb42ea",
        "Das Herz der Anden",
        "Frederic Edwin Church",
    ),
    CuratedWork(
        122873779,
        "File:Henry moret pecheurs au large064046).jpg",
        "5a4220cd2cadd6a260292cf77e0abcdc32e0b364",
        "P\xeacheurs au large",
        "Henry Moret",
    ),
    CuratedWork(
        13502218,
        "File:Ivan Shishkin - \u0420\u043e\u0436\u044c - Google Art Project.jpg",
        "7c38fbdddcc924f63d37dc1be7ba414d2c60e8b3",
        "Roggenfeld",
        "Ivan Shishkin",
    ),
    CuratedWork(
        60846777,
        "File:Road near La C\xf4te-Saint-Andr\xe9 MET DP800438.jpg",
        "9d199181c677d0b49cef4ebd5491a383f71169d8",
        "Road near La C\xf4te-Saint-Andr\xe9",
        "Johan Barthold Jongkind",
    ),
    CuratedWork(
        74332535,
        "File:John Atkinson Grimshaw - A Wet Moon, Putney Road (1886).jpg",
        "e26c0bbf6e1c025685b221162f510f0ddd01197e",
        "A Wet Moon, Putney Road",
        "John Atkinson Grimshaw",
    ),
    CuratedWork(
        22153299,
        "File:John Constable - Ploughing Scene in Suffolk - Google Art Project.jpg",
        "8a8077b8302a744d4c3c353c407adcf9e2fcaafe",
        "Ploughing Scene in Suffolk",
        "John Constable",
    ),
    CuratedWork(
        22135067,
        ("File:Adam Willaerts, attributed to - Harbour scene - Google Art Project.jpg"),
        "0ad6b6219016633e4f660a689a2ed067950ae359",
        "Harbour scene",
        "Adam Willaerts",
    ),
    CuratedWork(
        95149294,
        (
            "File:Adrien-manglard-a-mediterranean-harbour-with-stevedores-unloading-the"
            "ir-ships,-figures-selling-fish-in-the.jpg"
        ),
        "ff274f2e5956efef5e31faf0d894d814c673ce3a",
        "Szene im Mittelmeerhafen",
        "Adrien Manglard",
    ),
    CuratedWork(
        795544,
        "File:The Cr\xe8che.jpg",
        "2ba8a8d2be98d8a2c40b8e95f241a50183051298",
        "Die Kinderkrippe I",
        "Albert Anker",
    ),
    CuratedWork(
        66313896,
        "File:Albert Edelfelt - Lugano - A III 2648 - Finnish National Gallery.jpg",
        "13832f304293568dbfc783909deb3c11bf4f5d67",
        "Lugano",
        "Albert Edelfelt",
    ),
    CuratedWork(
        20279913,
        (
            "File:A Still Life with Roses, a Jug, a Loaf of Bread, a Filled Wine Glass,"
            " Two Plates with Prawns and Crabs, a Knife, a Partly-Peeled Lemon and Grap"
            "es over a Partly-Draped Table.jpg"
        ),
        "45665ba91d8cf76639f5fee09b46c9e570c8a30b",
        (
            "A Still Life with Roses, a Jug, a Loaf of Bread, a Filled Wine Glass, Two "
            "Plates with Prawns and Crabs, a Knife, a Partly-Peeled Lemon and Grapes ov"
            "er a Partly-Draped Table"
        ),
        "Alexander Adriaenssen",
    ),
    CuratedWork(
        20264780,
        "File:Alexandre Cabanel - The Birth of Venus - Google Art Project 2.jpg",
        "cdbe3474820ef7426938a078de3bc9edc374b71e",
        "Die Geburt der Venus",
        "Alexandre Cabanel",
    ),
    CuratedWork(
        118446129,
        ("File:Amaldus Nielsen - Den gamle Frognerseterveien - Oslo Museum - OB.01081.jpg"),
        "c7aaea1124028b4d077c9806b7a89e09bbd59763",
        "Den gamle Frognerseterveien",
        "Amaldus Nielsen",
    ),
    CuratedWork(
        81304229,
        (
            "File:American 19th Century, Imaginary Regatta of America's Cup Winners, 18"
            "89 or after, NGA 42493.jpg"
        ),
        "04c611884dae1eb241face6d2902229cd8f51664",
        "Imaginary Regatta of America's Cup Winners",
        "Unbekannt (USA, 19. Jahrhundert)",
    ),
    CuratedWork(
        68010997,
        "File:Antal Ligeti - Pusta - M 199 - Ernest Zmet\xe1k Art Gallery.jpg",
        "8b1780cd047ab3a2c5bf70f2d79669193ae131d2",
        "Pusta",
        "Antal Ligeti",
    ),
    CuratedWork(
        75034224,
        "File:Anton Perko - Lighthouse Grebeni, Dubrovnik.jpg",
        "caa35128567e5b2dce2c7b53d5be73431adf8df1",
        "Lighthouse Grebeni, Dubrovnik",
        "Anton Perko",
    ),
    CuratedWork(
        26814547,
        ("File:Apertura de las Cortes en 1919 (Asterio Ma\xf1an\xf3s Mart\xednez).jpg"),
        "de0581da59d01d40d0c660069409807c7953b074",
        "Apertura de las Cortes en el a\xf1o 1919 (Plaza del Senado)",
        "Asterio Ma\xf1an\xf3s Mart\xednez",
    ),
    CuratedWork(
        82931652,
        ("File:Bernardo Bellotto - Festung K\xf6nigstein (National Gallery of Art).jpg"),
        "f5c2f188d351d9c4ae7410d40060d176bd62554d",
        "Festung K\xf6nigstein",
        "Bernardo Bellotto",
    ),
    CuratedWork(
        81307464,
        ("File:Bernardo Bellotto and Workshop, View of Munich, c. 1761, NGA 46163.jpg"),
        "2420319c2830155d5bf3fccbb2ea9edad5e72544",
        "Blick auf M\xfcnchen",
        "Bernardo Bellotto und Werkstatt",
    ),
    CuratedWork(
        66316393,
        ("File:Berndt Lindholm - Forest Interior - A II 1708 - Finnish National Gallery.jpg"),
        "d353558bb53dc074b2d978a36ac2da81146ecabf",
        "Forest Interior",
        "Berndt Lindholm",
    ),
    CuratedWork(
        57384516,
        "File:Saint Nicholas Providing Dowries MET DT273088.jpg",
        "fab2b0453f3511836ebe7829e356476bca5eb04a",
        "Der hl. Nikolaus gibt die Aussteuer",
        "Bicci di Lorenzo",
    ),
    CuratedWork(
        81308465,
        "File:Canaletto, The Porta Portello, Padua, c. 1741-1742, NGA 46152.jpg",
        "c6e88c07fc6987e32693b3089f0609372ed73332",
        "Die Porta Portello, Padua",
        "Canaletto",
    ),
    CuratedWork(
        128454257,
        "File:Carl Frederik Aagaard - Strandparti fra Saltholm - 1890 - NK 288.JPG",
        "671b9f5c699b469e5a148088016cad3783427ba8",
        "The coast at Saltholm.",
        "Carl Frederik Aagaard",
    ),
    CuratedWork(
        22264267,
        (
            "File:Carl Larsson - Open-Air Painter. Winter-Motif from \xc5s\xf6gatan 145"
            ", Stockholm - Google Art Project.jpg"
        ),
        "784c3ae318d331a817475f7cce5bea68612b5c86",
        "Open-Air Painter. Winter-Motif from \xc5s\xf6gatan 145, Stockholm",
        "Carl Larsson",
    ),
    CuratedWork(
        60939098,
        "File:Funeral Ritual in a Garden, Tomb of Minnakht MET DT10880.jpg",
        "d3e40f80c87b9a04c03ba09fd81c4ea38033583c",
        "Funeral Ritual in a Garden, Tomb of Minnakht",
        "Charles Wilkinson",
    ),
    CuratedWork(
        22199619,
        ("File:Mountain River Scene Autumn of the Hudson-Charles Wilson Knapp-1870.jpg"),
        "4721355e9a1c796395bb23731b49068fe8ea8792",
        "Mountain River Scene (Autumn on the Hudson)",
        "Charles Wilson Knapp",
    ),
    CuratedWork(
        81415687,
        "File:Charles \xc9mile Jacque, The Shepherdess, c. 1869, NGA 95742.jpg",
        "59028ec4b1db6602c808bbc2c1cd3f3d594f3dcc",
        "The Shepherdess",
        "Charles \xc9mile Jacque",
    ),
    CuratedWork(
        57377196,
        (
            "File:\u660e \u4eff\u9673\u6df3 \u96dc\u82b1\u5716 \u518a-Garden Flowers ME"
            "T DP161169 CRD.jpg"
        ),
        "f0e1676647e8266edab0f6838c9cb02f7db01312",
        "Gartenblumen (Albumblatt)",
        "Nach Chen Chun",
    ),
    CuratedWork(
        43317016,
        ("File:'Snow Clearing by the Seine' by Christian Skredsvig, Bergen Kunstmuseum.JPG"),
        "67ff17358f4f8014a6502ba2a95bef983857b4f3",
        "Snow Dumping on the Seine",
        "Christian Skredsvig",
    ),
    CuratedWork(
        141394807,
        "File:Along the Tiber (1881), by Enrico Coleman.jpg",
        "1d130d85e15ceebe375374992ee0a987da2704e5",
        "Along the Tiber",
        "Enrico Coleman",
    ),
    CuratedWork(
        81434598,
        "File:Eug\xe8ne Delacroix, Tiger, c. 1830, NGA 6493.jpg",
        "b485261a5c3d554ddd9b81d55ef7a4e974908905",
        "Tiger",
        "Eug\xe8ne Delacroix",
    ),
    CuratedWork(
        65096460,
        "File:Camp de Compi\xe8gne, 1698 MET DP874498.jpg",
        "ac897fb43c81b6b17ae317c0e6f8abb42b1c1ee0",
        "Camp de Compi\xe8gne, 1698",
        "Eug\xe8ne Lami",
    ),
    CuratedWork(
        21881964,
        ("File:Ferdinand Richardt - Independence Hall in Philadelphia - Google Art Project.jpg"),
        "09ddf80d145fc5877e0edeebd2482ece9b155c2c",
        "Independence Hall in Philadelphia",
        "Ferdinand Richardt",
    ),
    CuratedWork(
        81310473,
        "File:Fitz Henry Lane, Becalmed off Halfway Rock, 1860, NGA 76213.jpg",
        "8ff506e4cc2d6e1d574830e9b6386b9923e5a317",
        "Becalmed off Halfway Rock",
        "Fitz Henry Lane",
    ),
    CuratedWork(
        57669562,
        "File:Venice- The Dogana and Santa Maria della Salute MET DT8847.jpg",
        "0048e36475f5c11cc9151320ff283be9b0b038bf",
        "Venice: The Dogana and Santa Maria della Salute",
        "Francesco Guardi",
    ),
    CuratedWork(
        81314166,
        (
            "File:Gian Antonio Guardi and Francesco Guardi, Erminia and the Shepherds, "
            "1750-1755, NGA 50256.jpg"
        ),
        "61b2a9b14df85817418896d2e0fc85b9d5ca4561",
        "Erminia und die Hirten",
        "Francesco Guardi / Giovanni Antonio Guardi",
    ),
    CuratedWork(
        58728087,
        "File:Olive Trees at Tivoli MET DT5579.jpg",
        "32f6bcb6c8e9ef8a670c623a8853557a549e9e5f",
        "Olive Trees at Tivoli",
        "George Inness",
    ),
    CuratedWork(
        18160885,
        "File:Hans Thoma - Der Rhein bei S\xe4ckingen.jpg",
        "6d9ba2b0725e13e7cab5220f38ba589f4e6100e8",
        "Der Rhein bei S\xe4ckingen",
        "Hans Thoma",
    ),
    CuratedWork(
        88804323,
        "File:Henryk Siemiradzki - Scena przy studni.jpg",
        "9cc260fb2b69e3561b73c7a196185cec582f55d2",
        "Scena przy studni",
        "Henryk Siemiradzki",
    ),
    CuratedWork(
        22605738,
        "File:The Garden of Earthly Delights by Bosch High Resolution.jpg",
        "ba84458a07641d1f5514b3507382411f0854cb31",
        "Der Garten der L\xfcste",
        "Hieronymus Bosch",
    ),
    CuratedWork(
        66322831,
        (
            "File:Hjalmar Munsterhjelm - Morning Mood (Island View) - A II 845 - Finnis"
            "h National Gallery.jpg"
        ),
        "d26d1c39dfb367df69899381dca3addf7cda03d5",
        "Morning Mood (Island View)",
        "Hjalmar Munsterhjelm",
    ),
    CuratedWork(
        66323064,
        ("File:Hugo Simberg - Piru muuttaa - A IV 3678 - Finnish National Gallery.jpg"),
        "055ec31680b79193e3abc46c43c29a596a210d2c",
        "Piru muuttaa",
        "Hugo Simberg",
    ),
    CuratedWork(
        114833882,
        "File:Frederick McCubbin - The gardener (c. 1910).jpg",
        "e1c42d3a832623b243fd589fe3b5101aa5217a51",
        "The gardener",
        "Frederick McCubbin",
    ),
    CuratedWork(
        81325026,
        'File:James Bard, Towboat "John Birkbeck", 1854, NGA 52947.jpg',
        "04294b2e5dbd12dfc941d086efa86d77db34aff4",
        'Towboat "John Birkbeck"',
        "James Bard",
    ),
    CuratedWork(
        57398214,
        "File:A Woodland Road with Travelers MET DT10768.jpg",
        "00726031334da5aff086ef3f92ebcc1f350efb69",
        "A Woodland Road with Travelers",
        "Jan Brueghel the Elder",
    ),
    CuratedWork(
        327727,
        "File:Autumn--On the Hudson River-1860-Jasper Francis Cropsey.jpg",
        "cd8e57bb6c0b3dafa6d0f75bf90b3c01249688aa",
        "Herbst - am Hudson River",
        "Jasper Francis Cropsey",
    ),
    CuratedWork(
        27367362,
        ("File:John Frederick Kensett - Almy's Pond, Newport, Rhode Island (1859).jpg"),
        "f16e327240fb74133bb7213a7b4e4f867c21a3d0",
        "Almy's Pond, Newport, Rhode Island",
        "John Frederick Kensett",
    ),
    CuratedWork(
        23596858,
        "File:John Henry Twachtman - Summer - Google Art Project.jpg",
        "9f9a556e75b44ce8f698cea11dd5ae21eeab1084",
        "Summer",
        "John Henry Twachtman",
    ),
    CuratedWork(
        21878879,
        "File:John William Waterhouse - Echo and Narcissus - Google Art Project.jpg",
        "a69838b0b5ca93948713ee69cce129294302bb64",
        "Echo und Narcissus",
        "John William Waterhouse",
    ),
    CuratedWork(
        57673092,
        ("File:Harbor Scene with a Grotto and Fishermen Hauling in Nets MET DP312862.jpg"),
        "f057734d41f401209756809db052303fc5c633d3",
        "Harbor Scene with a Grotto and Fishermen Hauling in Nets",
        "Joseph Vernet",
    ),
    CuratedWork(
        15696680,
        "File:Jos\xe9 Malhoa - Gozando os rendimentos.jpg",
        "9dbb87d65d5e0fb66aad7bcd5b428d2079be92a2",
        "Boasting incomes",
        "Jos\xe9 Malhoa",
    ),
    CuratedWork(
        57384716,
        "File:The Weeders MET DT2155.jpg",
        "53e78740509b175e5a94e1fedcc6dbc135fe59db",
        "The Weeders",
        "Jules Breton",
    ),
    CuratedWork(
        27216200,
        "File:Jules Dupr\xe9 - Vaches traversant un gu\xe9 (1836).jpg",
        "a89b39388e5e23b95e45b98354df28cddcfe9794",
        "K\xfche \xfcberqueren eine Furt",
        "Jules Dupr\xe9",
    ),
    CuratedWork(
        44569993,
        "File:Karel Ooms - Aristocratic family enjoying winter landscape.jpg",
        "580d468c1779e68c2b578d81d991314f24a8c14a",
        "Aristocratic family enjoying winter landscape",
        "Karel Ooms",
    ),
    CuratedWork(
        57669998,
        "File:A Mountainous Landscape with a Waterfall MET DT7563.jpg",
        "6cd6e67f5217d2b74f4d53778b86c93e99dea6c0",
        "A Mountainous Landscape with a Waterfall",
        "Kerstiaen de Keuninck",
    ),
    CuratedWork(
        21959590,
        "File:Cherokee Roses on a Purple Cloth-Martin Johnson Heade-1894.jpg",
        "894b61a43c3563cf3b2e18f5a859265d32b0595a",
        "Cherokee Roses on a Purple Cloth",
        "Martin Johnson Heade",
    ),
    CuratedWork(
        26563390,
        "File:Max Liebermann Arbeiter im R\xfcbenfeld \xd6lstudie 1873.jpg",
        "1df638aa168ad6d8935030372eda94abacc72f10",
        "Arbeiter im R\xfcbenfeld (\xd6lstudie)",
        "Max Liebermann",
    ),
    CuratedWork(
        65140182,
        ("File:Menna and Family Hunting in the Marshes, Tomb of Menna MET DT10878.jpg"),
        "b9da982534f13f3c5f50d8199c7363ef1afe49e4",
        "Menna and Family Hunting in the Marshes, Tomb of Menna",
        "Nina M. Davies",
    ),
    CuratedWork(
        60854281,
        "File:Mountains of Auvergne MET DP806735.jpg",
        "a594211cdba8e704ccdd8f4ae5e5906c2674be51",
        "Mountains of Auvergne",
        "Paul Huet",
    ),
    CuratedWork(
        60909660,
        "File:Where the Eggs and the Good Roast Come From MET DT5836.jpg",
        "fb8821ac7b2a3bc9a474468899c06fb3827c90c8",
        "Where the Eggs and the Good Roast Come From",
        "Paul Klee",
    ),
    CuratedWork(
        116261686,
        ("File:Peder Severin Kr\xf8yer - Kunstnerfrokost i Cernay-la-Ville - 1879 - SKM1096.jpg"),
        "a38dc04c2cbc27c9fbc6a5b962907ea3cc254518",
        "Artists' lunch. Cernay-la-Ville.",
        "Peder Severin Kr\xf8yer",
    ),
    CuratedWork(
        67540168,
        ("File:Pierre-Auguste Renoir - Apples (Pommes) - BF55 - Barnes Foundation.jpg"),
        "ec567b8f0454d12553193c23f665cda1c20063b8",
        "Apples (Pommes)",
        "Pierre-Auguste Renoir",
    ),
    CuratedWork(
        15885145,
        "File:Piero di Cosimo - The Myth of Prometheus - WGA17652.jpg",
        "5ed2f818ede0ee16c5313c60b2785ebd463bf749",
        "Prometheus erschafft den ersten Menschen",
        "Piero di Cosimo",
    ),
    CuratedWork(
        57672440,
        "File:The Building of Westminster Bridge MET DP169565.jpg",
        "3a6d2bc9e60f94cdb54a02e51ba14d47cf94857b",
        "The Building of Westminster Bridge",
        "Samuel Scott",
    ),
    CuratedWork(
        81332363,
        ("File:Stanislas L\xe9pine, A Plow Horse in a Field, 1870-1874, NGA 89680.jpg"),
        "acda963e4df626a5f8ae6574f5a887f47a01dd5e",
        "A Plow Horse in a Field",
        "Stanislas L\xe9pine",
    ),
    CuratedWork(
        13496330,
        (
            "File:Viktor Borisov-Musatov - \u0418\u0437\u0443\u043c\u0440\u0443\u0434"
            "\u043d\u043e\u0435 \u043e\u0436\u0435\u0440\u0435\u043b\u044c\u0435 - Goog"
            "le Art Project.jpg"
        ),
        "8ca553c06091897c8233ca06a7dd3c971cbdecdd",
        "The Emerald Necklace",
        "Viktor Borisov-Musatov",
    ),
    CuratedWork(
        138007676,
        "File:Vincent van Gogh-Vorabend-04257 (cropped).jpg",
        "d842ad82ac2e9fb90777ef0e88f388c4cf88dfac",
        "Vorabend / Autumn Landscape at Dusk",
        "Vincent van Gogh",
    ),
    CuratedWork(
        25031017,
        "File:Near Cape St Johns Coast of Labrador-William Bradford 1874.jpg",
        "dddbb36b1fc29f044262e32a31f9e4ed114f302b",
        "Near Cape St. Johns, Coast of Labrador",
        "William Bradford",
    ),
    CuratedWork(
        21276801,
        "File:British Coastal View-William Trost Richards.jpg",
        "e28e7e66fe76fb005c3fc4a357d74659c0b8be49",
        "British Coastal View (Coast of Cornwall)",
        "William Trost Richards",
    ),
    CuratedWork(
        190237599,
        "File:Winslow Homer - Lobster Cove, Manchester, Massachusetts (1869).jpg",
        "878e27899c5f41dc05318815d898bd6e2d6b7c22",
        "Lobster Cove, Manchester, Massachusetts",
        "Winslow Homer",
    ),
    CuratedWork(
        81302575,
        (
            "File:After Marco Ricci, View of the Mall in Saint James's Park, after 1709"
            "-1710, NGA 52276.jpg"
        ),
        "dabde4b262242fd616607d7389ed85a61d8c817a",
        "View of the Mall in Saint James's Park",
        "Nach Marco Ricci",
    ),
    CuratedWork(
        34319635,
        "File:Rivierlandschap met ruiters Rijksmuseum SK-A-4118.jpeg",
        "e2ddb4c660d0fa7e28839c9fa1c712fff0b8ac64",
        "Flusslandschaft mit Reitern",
        "Aelbert Cuyp",
    ),
    CuratedWork(
        34313914,
        "File:De hemelvaart van Elia Rijksmuseum SK-A-1617.jpeg",
        "12292e041fbf3d205e5c0343f4f3557ff3542ba3",
        "The ascension of Elijah",
        "David Colijns",
    ),
    CuratedWork(
        131942228,
        "File:De buitenpartij Rijksmuseum SK-A-1796FXD.jpg",
        "84dd4df53145ad6425652f19cfa5a7570be1d569",
        "Fest im Freien",
        "Dirck Hals",
    ),
    CuratedWork(
        34317675,
        ("File:Voornaam gezelschap, dinerend in de buitenlucht Rijksmuseum SK-A-1765.jpeg"),
        "45160bc283000a1d4e803c33e6b47d497129700c",
        "Elegant company dining in the open air",
        "Esaias van de Velde",
    ),
    CuratedWork(
        34405178,
        "File:Watervogels Rijksmuseum SK-A-1322.jpeg",
        "473533fe849e83c5b00ad337ecc03becdfadfc07",
        "Waterfowl",
        "Gijsbert d'Hondecoeter",
    ),
    CuratedWork(
        34313531,
        "File:De landweg Rijksmuseum SK-A-1502.jpeg",
        "566abc1a887326946e2b0477012e4d7af3ebb6e2",
        "The country road",
        "Gillis Claesz. de Hondecoeter",
    ),
    CuratedWork(
        34313842,
        "File:Rivierdal Rijksmuseum SK-A-3120.jpeg",
        "a51d94be908c55a3dfd0323badc6e5a5f7872512",
        "River Valley",
        "Hercules Segers (1589\u20131637)",
    ),
    CuratedWork(
        34250590,
        "File:Vier musicerende vrouwen Rijksmuseum SK-C-1353.jpeg",
        "7076f7891834b6c88344d24e09d45cb3d37eb94d",
        "Four Female Musicians",
        "Luca Giordano",
    ),
    CuratedWork(
        83529871,
        (
            "File:Het afdanken der waardgelders door prins Maurits op de Neude te Utrec"
            "ht, 31 juli 1618, SK-A-155.jpg"
        ),
        "162dabda21f92b6aa8945a2c13c4965ec7d26678",
        "Prinz Moritz auf der Neude in Utrecht, 31. Juli 1618",
        "Pauwels van Hillegaert",
    ),
    CuratedWork(
        34320072,
        "File:Gezicht op Tunis Rijksmuseum SK-A-1397.jpeg",
        "1e51ba16a73127192b2290c383a1a1b13ab15428",
        "View of Tunis",
        "Reinier Nooms",
    ),
    CuratedWork(
        34249872,
        ("File:Stilleven met vruchten en bloemguirlandes Rijksmuseum SK-A-4254-7.jpeg"),
        "bef98d8685a2266291d5fb04e436deb1772a4b58",
        "Still Life with Fruit and Flower Garlands",
        "Jacob van Campen",
    ),
    CuratedWork(
        34258147,
        "File:Een kudde schapen Rijksmuseum SK-A-3080.jpeg",
        "8e7b2391d370c1d322277233da27a1ac71f67f1e",
        "A Flock of Sheep",
        "William Charles Estall",
    ),
    CuratedWork(
        159288815,
        "File:Otto Modersohn Sturm im Teufelsmoor (1927).jpg",
        "78218410245a7383ece7bb4115b1c169e7d549e4",
        "Sturm im Teufelsmoor",
        "Otto Modersohn",
    ),
    CuratedWork(
        141281704,
        "File:Bruno Liljefors - Hare in Winter Landscape 1917.jpg",
        "ef009f0de668a30071cfa1d4080a43bf701a711c",
        "Hare in Winter Landscape",
        "Bruno Liljefors",
    ),
    CuratedWork(
        149827428,
        "File:Carl Spitzweg B\xe4uerin vor einer Almh\xfctte c1870.jpg",
        "1999f9697da18f798bb688054e2d6df8c7b1f498",
        "B\xe4uerin vor einer Almh\xfctte",
        "Carl Spitzweg",
    ),
    CuratedWork(
        81310320,
        ("File:Eug\xe8ne Boudin, Concert at the Casino of Deauville, 1865, NGA 66401.jpg"),
        "332e646e08babf88cfdbabd5dc1c20b36927c20a",
        "Concert at the Casino of Deauville",
        "Eug\xe8ne Boudin",
    ),
    CuratedWork(
        81309955,
        "File:Edgar Degas, The Loge, c. 1883, NGA 57514.jpg",
        "a2000fb469fe0b0211d673a9a31aa1878be30f5b",
        "The Loge",
        "Edgar Degas",
    ),
    CuratedWork(
        140222439,
        (
            "File:Camille Corot - The Chaise-Marie Quarry at Fontainebleau - 1914-DI - "
            "Museum of Fine Arts Ghent (MSK).jpg"
        ),
        "00be7cc3d5c9ff9e9e6f8ceea6bf1f005b21170d",
        "Carri\xe8re de la Chaise-Marie, Fontainebleau",
        "Jean-Baptiste-Camille Corot",
    ),
    CuratedWork(
        81307433,
        ("File:Bernardo Bellotto and Workshop, Nymphenburg Palace, Munich, c. 1761, NGA 46162.jpg"),
        "56f0e03c261ebd26566d94a3c4e21f2d1e723231",
        "Ansicht von M\xfcnchen, Schlo\xdf Nymphenburg, von Westen aus gesehen",
        "Bernardo Bellotto und Werkstatt",
    ),
    CuratedWork(
        66316398,
        (
            "File:Berndt Lindholm - Corn Harvest (Landscape from Western Sweden) - A I "
            "559 - Finnish National Gallery.jpg"
        ),
        "708c6a5545cb717a5e26a2027c5fa92ef79b05ed",
        "Oat Harvest on the Hisingen Island",
        "Berndt Lindholm",
    ),
    CuratedWork(
        57669569,
        "File:Venice- The Rialto MET DT8848.jpg",
        "2f4739c83d11d33fe1c6c6ddeeb755dc417e1034",
        "Venice: The Rialto",
        "Francesco Guardi",
    ),
    CuratedWork(
        115455905,
        "File:John frederick kensett lake erie094323).jpg",
        "da3ce0f258061005740281789fc6c4fd6d5dbccc",
        "Lake Erie",
        "John Frederick Kensett",
    ),
    CuratedWork(
        76001413,
        "File:Clevelandart 1970.161.jpg",
        "fc226933480aed33ef55c236e2a2a3c1a63a4054",
        "Point Judith, Rhode Island",
        "Martin Johnson Heade",
    ),
    CuratedWork(
        11155871,
        "File:Skagens j\xe6gere (p. s. kR\xd8YER).jpg",
        "0aea21ecaf50f313118de6914d6ffbad999a1da4",
        "Hunters of Skagen",
        "Peder Severin Kr\xf8yer",
    ),
    CuratedWork(
        76362260,
        (
            "File:Renoir - BAIGNEUSE ALLONG\xc9E DE DOS AVEC UN CHAPEAU DE PAILLE OR FE"
            "MME COUCH\xc9E SUR L'HERBE, 1892.jpg"
        ),
        "e8bfb3aeedf143870b89219438df9b39cb2bf1af",
        "Femme couch\xe9e sur l\u2019herbe",
        "Pierre-Auguste Renoir",
    ),
    CuratedWork(
        57365081,
        "File:Isola Bella in Lago Maggiore MET DT1550.jpg",
        "7153d42bd4398e1e5467d05c85864fd6dd8c5da6",
        "Isola Bella In Lago Maggiore",
        "Sanford Robinson Gifford",
    ),
    CuratedWork(
        115455733,
        "File:William trost richards summer sea045309).jpg",
        "7f4c1e54bc3df7397fb65483594554f51b5f8963",
        "Summer Sea",
        "William Trost Richards",
    ),
    CuratedWork(
        10629177,
        "File:A Rainy Day in Camp by Winslow Homer 1871.jpeg",
        "51dd2b7f8818eea001b0eebd44774b864184ae57",
        "Rainy Day in Camp",
        "Winslow Homer",
    ),
    CuratedWork(
        93485240,
        "File:Charles-Fran\xe7ois Daubigny - View on the Oise.jpg",
        "85697d0a0f117319cc5f3bcf34b066a556370370",
        "View on the Oise",
        "Charles-Fran\xe7ois Daubigny",
    ),
    CuratedWork(
        81310326,
        "File:Eug\xe8ne Boudin, Fair in Brittany, 1874, NGA 178080.jpg",
        "f10ef0790d8a00e0473d92936f480197f870a490",
        "Markt in der Bretagne",
        "Eug\xe8ne Boudin",
    ),
    CuratedWork(
        66322211,
        "File:Berndt Lindholm - Rantakuva - A II 772 - Finnish National Gallery.jpg",
        "597cc298284dc686b694fc10723e0a16b5990375",
        "Rantakuva",
        "Berndt Lindholm",
    ),
    CuratedWork(
        76401796,
        "File:Renoir - Nature morte aux grenades et figues.jpg",
        "e48d65512ff50ccd2333e2bd64f45c2393d9a95d",
        "Nature morte aux grenades et figues",
        "Pierre-Auguste Renoir",
    ),
    CuratedWork(
        30489671,
        "File:Gifford Sanford Robinson - Sunset Over New York Bay (1873).jpg",
        "800fd0b22718a5d07c74967265183ad3548fb411",
        "Sunset over New York Bay",
        "Sanford Robinson Gifford",
    ),
    CuratedWork(
        101606839,
        "File:Winslow Homer - The Country School (1871).jpg",
        "20a9a1e9f8f92c2a9ad92d1c425e2f597c3038af",
        "The Country School",
        "Winslow Homer",
    ),
    CuratedWork(
        128008817,
        (
            "File:Charles-Fran\xe7ois Daubigny (1817 - 1878), Villerville - Ondergaande"
            " zon bij Villerville - hwm0091 - The Mesdag Collection.jpg"
        ),
        "243558c5883009d3496db3f5718538906ce51176",
        "Sunset at Villerville",
        "Charles-Fran\xe7ois Daubigny",
    ),
    CuratedWork(
        81310336,
        "File:Eug\xe8ne Boudin, On the Beach, 1894, NGA 46481.jpg",
        "9a8618d083ba081754e34e8635196985ce5d01d6",
        "On the Beach",
        "Eug\xe8ne Boudin",
    ),
    CuratedWork(
        74897839,
        (
            "File:Sanford Robinson Gifford, The Artist Sketching at Mount Desert, Maine"
            ", 1864-1865, NGA 121618.jpg"
        ),
        "ff2bfc516d1ed45e345b76c859573994fc230182",
        "The Artist Sketching at Mount Desert, Maine",
        "Sanford Robinson Gifford",
    ),
    CuratedWork(
        23855425,
        "File:Winslow Homer - The Gulf Stream (watercolour).jpg",
        "300d34c65885b5cd7778cb4f41171ed9a9581cfa",
        "The Gulf Stream",
        "Winslow Homer",
    ),
    CuratedWork(
        74389941,
        (
            "File:Charles-Fran\xe7ois Daubigny - Sluice in the Optevoz Valley - 79.122 "
            "- Museum of Fine Arts.jpg"
        ),
        "d71c8e426a578bebe1fea6c131891a1561603314",
        "Sluice in the Optevoz Valley",
        "Charles-Fran\xe7ois Daubigny",
    ),
    CuratedWork(
        81310338,
        "File:Eug\xe8ne Boudin, On the Beach, Trouville, 1887, NGA 46480.jpg",
        "d674696dc80a0756e3096b7d36f6e256abb6ff6a",
        "On the Beach, Trouville",
        "Eug\xe8ne Boudin",
    ),
    CuratedWork(
        21894912,
        "File:Winslow Homer - Two Figures by the Sea - Google Art Project.jpg",
        "e1f3509cd9b658b80acd2750ecccd1c759f1ae0e",
        "Two Figures by the Sea",
        "Winslow Homer",
    ),
    CuratedWork(
        85067082,
        (
            "File:Charles Fran\xe7ois Daubigny - The Painter\u2019s Barge at the Ile de"
            " Vaux on the Oise River - 2017.5 - Dallas Museum of Art.jpg"
        ),
        "9ece3532f4f3632f82b9d4229a0b881141b1528b",
        "The Painter\u2019s Barge at the Ile de Vaux on the Oise River",
        "Charles-Fran\xe7ois Daubigny",
    ),
    CuratedWork(
        178770689,
        "File:Eug\xe8ne Boudin Le Havre La F\xeate des r\xe9gates 1869.jpg",
        "041540933bc6169e17215cad07ad47649bcbcc10",
        "Le Havre, La F\xeate des r\xe9gates",
        "Eug\xe8ne Boudin",
    ),
    CuratedWork(
        115423103,
        "File:Eugene boudin honfleur voiliers115616).jpg",
        "3590ac30e255ac04bc2b60c9b5ac7ae5d18f9c7f",
        "Honfleur. Voiliers",
        "Eug\xe8ne Boudin",
    ),
)
