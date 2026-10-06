"""Pinned near-widescreen Commons metadata (D-209/D-211).

400 reviewed entries: all 166 b4 pins retained, plus 234 new works.
No image bytes are bundled. Metadata-only provenance:
frame_gallery/research/commons-400-selection-2026-10-06.json.
Permanent Commons history IDs and the strict-ratio rule are unchanged.
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
    CuratedWork(
        64525652,
        "File:Adalbert Waagen - Motif of the Alps.jpg",
        "cca659e399684c9ebaa2bee94add89f25b2d0269",
        "Motif of the Alps",
        "Adalbert Waagen",
    ),
    CuratedWork(
        23595716,
        (
            "File:Adolphe Monticelli (attributed to) - Landscape with Figures - Google "
            "Art Project.jpg"
        ),
        "f4c4da3397399232b808760dbede4c85902ee32a",
        "Landscape with Figures",
        "Adolphe Joseph Thomas Monticelli",
    ),
    CuratedWork(
        49911139,
        ("File:Adrien Bas - Vase de digitales - huile sur contreplaqu\xe9 (1918) 03.jpg"),
        "c64893abefdaa397e8144c3f22078778e46d5f8d",
        "Vase de digitales",
        "Adrien Bas",
    ),
    CuratedWork(
        21878850,
        "File:Albert Joseph Moore - A Summer Night - Google Art Project.jpg",
        "8e96c8f602eb5574b88e0cc10384f502cdf25443",
        "A Summer Night",
        "Albert Joseph Moore",
    ),
    CuratedWork(
        121561562,
        ("File:Albert Joseph Moore - Beads - NG 1019 - National Galleries of Scotland.jpg"),
        "cd4ae8a1b01c9418d670bfa994762040191bc37e",
        "Beads",
        "Albert Joseph Moore",
    ),
    CuratedWork(
        74546310,
        (
            "File:Julius Olsson-The Night Patrol - Canadian Motor Torpedo Boats Enterin"
            "g Dover Harbour (CWM 19710261-0538).jpeg"
        ),
        "277532f16aa2d7fc6a3e268f21a2812edeb5b6eb",
        "The Night Patrol - Canadian Motor Torpedo Boats Entering Dover Harbour",
        "Albert Julius Olsson",
    ),
    CuratedWork(
        4003728,
        "File:Mroczkowski Aleksander, W \u017cniwa.JPG",
        "6d69e01cbecd00bb17fcde83a838b8e07af712f0",
        "W \u017cniwa",
        "Aleksander Mroczkowski",
    ),
    CuratedWork(
        45607698,
        ("File:Alexis Jean Fournier - September - 2006.71.1 - Minneapolis Institute of Arts.jpg"),
        "cd63076c5038f3d62ed7ba560854eb6e95994226",
        "September",
        "Alexis Jean Fournier",
    ),
    CuratedWork(
        41052077,
        "File:'Kauai Coastal View' by Alfred Richard Gurrey, Sr., 1923.jpg",
        "6961fc87627ad1d0093c20429b124319fc392d34",
        "Kauai Coastal View",
        "Alfred Richard Gurrey, Sr.",
    ),
    CuratedWork(
        75030787,
        "File:Alfred Steinacker - Kutsche bei Scheegest\xf6ber.jpg",
        "18aa6465d8d2001b39ec04ad5a07076b4601875a",
        "Kutsche bei Scheegest\xf6ber",
        "Alfred Steinacker",
    ),
    CuratedWork(
        18410668,
        "File:Alfred Steinacker Ungarische Bauernhochzeit.jpg",
        "9a1fecc815974c86bee9a4d8ae82c710308ed338",
        "Ungarische Bauernhochzeit",
        "Alfred Steinacker",
    ),
    CuratedWork(
        64501070,
        "File:Alfred Steinacker - Winter Ride.jpg",
        "01e4b81dceade9d0c2ebf1e9b55922c72078acd3",
        "Winter Ride",
        "Alfred Steinacker",
    ),
    CuratedWork(
        77663284,
        "File:Andr\xe1s Mark\xf3 - View of Rome from Villa Madama.jpg",
        "b3fffe65e8d12fe73fe00f2764abfcdf718388ae",
        "View of Rome from Villa Madama",
        "Andr\xe1s Mark\xf3",
    ),
    CuratedWork(
        38869178,
        "File:Angelo Dall'Oca Bianca - Foglie cadenti.jpg",
        "76415920dba1bb303493c75c3c23e7b11411bdfa",
        "Foglie cadenti",
        "Angelo Dall'Oca Bianca",
    ),
    CuratedWork(
        178891565,
        "File:Boat on Lake Maggiore (1915), by Angelo Morbelli.jpg",
        "76fea2fe27fb9bc099cd668b785df648557707c9",
        "Battello sul Lago Maggiore Boat on Lake Maggiore",
        "Angelo Morbelli",
    ),
    CuratedWork(
        101282268,
        ("File:Antoine Guillemet - Le Quai de Bercy - P1914 - Mus\xe9e Carnavalet.jpg"),
        "7eed57b5296dc4c0a1e1a989d976d7e56bc9aff0",
        "Le Quai de Bercy",
        "Antoine Guillemet",
    ),
    CuratedWork(
        18652488,
        "File:Anton Braith Rinder an der Tr\xe4nke 1883.jpg",
        "ae11e7e683d2f63467ad63ddf77a551f95b2286c",
        "Rinder an der Tr\xe4nke",
        "Anton Braith",
    ),
    CuratedWork(
        20972263,
        "File:Antonio Ermolao Paoletti The melon sellers.jpg",
        "a679b75537ec8333f19bc155ca1e6f64f9b723d5",
        "The melon sellers.",
        "Antonio Ermolao Paoletti",
    ),
    CuratedWork(
        22530995,
        "File:Antonio Jacobsen - 'The Jefferson', 1914.jpg",
        "5e2ca83d400d8ec0b841c04e10bfaf26a9438eeb",
        "'The Jefferson', 1914",
        "Antonio Jacobsen",
    ),
    CuratedWork(
        128007932,
        ("File:Antonio Mancini (1852 - 1930) - De broers - hwm0184r - The Mesdag Collection.jpg"),
        "eb7a45864d691a95e7b1e9eae5d7e442e6fb9539",
        "The brothers",
        "Antonio Mancini",
    ),
    CuratedWork(
        98348102,
        (
            "File:Arnold Peter Weisz-Kub\xedn\u010dan - Winter Landscape - O 4497 - Slo"
            "vak National Gallery.jpg"
        ),
        "c4916313d3ef0680f5ef008a35749d70864bdece",
        "Slovak: Zimn\xe1 krajina Winter Landscape",
        "Arnold Peter Weisz-Kub\xedn\u010dan",
    ),
    CuratedWork(
        53997339,
        "File:Arthur Quartley - Morning off Marblehead (1877).jpg",
        "5fab562ad9a8e368618893c55d830bd4802a4d6a",
        "Morning off Marblehead",
        "Arthur Quartley",
    ),
    CuratedWork(
        163461953,
        (
            "File:A schooner yacht of the New York Yacht Club racing off Ryde, Isle of "
            "Wight (by Arthur Wellington Fowles).jpg"
        ),
        "4c9877dacb6ecb3716a88dcf263e9b27a111f27e",
        "A schooner yacht of the New York Yacht Club racing off Ryde, Isle of Wight",
        "Arthur Wellington Fowles",
    ),
    CuratedWork(
        76696020,
        "File:Ascan Lutteroth - A view of Capri.jpg",
        "ebbb1c111bff8b612b216bbe21b27eb887786b49",
        "A view of Capri",
        "Ascan Lutteroth",
    ),
    CuratedWork(
        67893605,
        ("File:August Ignatz Grosz - Krajina na Capri - M 156 - Ernest Zmet\xe1k Art Gallery.jpg"),
        "cca8e98b4456e6c80054efc16cfe2bb569eef891",
        "Krajina na Capri",
        "August Ignaz Grosz",
    ),
    CuratedWork(
        37948976,
        ("File:'Still Life with Apples and a Pomegranate' by Th\xe9odule-Augustin Ribot.JPG"),
        "65322378679783f7bd0f5e097145319481f37b7b",
        "Still Life with Apples and a Pomegranate",
        "Augustin Th\xe9odule Ribot",
    ),
    CuratedWork(
        123889433,
        "File:Benedito Calixto - Enseada com barcos, SP, 1907.jpg",
        "2b7834c54e1424860b620bf5125622ffc2a1c302",
        "Enseada com barcos",
        "Benedito Calixto",
    ),
    CuratedWork(
        124914944,
        "File:Bernard Boutet de Monvel Les Haleurs.jpg",
        "edc50dd8b654565987f05fa6accf30955e74f0d8",
        "The Haulers",
        "Bernard Boutet de Monvel",
    ),
    CuratedWork(
        60278301,
        ("File:View of Norba from the North, towards San Felice Circeo MET DP869305.jpg"),
        "34998c2fab2d198557fddce9054b90d6cb128379",
        "View of Norba from the North, towards San Felice Circeo",
        "Carl Werner",
    ),
    CuratedWork(
        21956171,
        "File:Carlos de Haes - Flemish Landscape - Google Art Project.jpg",
        "fa3ab3b5591dfdf225a2a59fb692445812f582a4",
        "Flemish Landscape",
        "Carlos de Haes",
    ),
    CuratedWork(
        66350586,
        ("File:Carolus-Duran - Promenade in the Woods - 1983.185 - Indianapolis Museum of Art.jpg"),
        "96984a185a13fc3a578f54e367c49fc3c7b0133e",
        "Promenade in the Woods",
        "Carolus-Duran",
    ),
    CuratedWork(
        22264624,
        "File:Charles Conder - The Yarra, Heidelberg - Google Art Project.jpg",
        "87a5f2614b7aab9d6cfd81d4f9390dae16aa8f4a",
        "The Yarra, Heidelberg",
        "Charles Conder",
    ),
    CuratedWork(
        38876479,
        ("File:Charles Courtney Curran, Fair Critics, The Metropolitan Museum of Art.jpg"),
        "39e41657fbf1af907ebc754f903460a557b7cb28",
        "Fair Critics",
        "Charles Courtney Curran",
    ),
    CuratedWork(
        97110464,
        "File:Charles victor guilloux bord de la riviere021847).jpg",
        "8daec9703fd83700e3f92c7290c9b9e0ef0bfa38",
        "Riverside",
        "Charles Guilloux",
    ),
    CuratedWork(
        97453046,
        (
            "File:David Cox the elder (1783-1859) - Rhyl Sands - 1885P2489 - Birmingham"
            " Museums Trust.jpg"
        ),
        "b56fc632a403995150e3e68342d4f08f4a4a5451",
        "Rhyl Sands",
        "David Cox",
    ),
    CuratedWork(
        26373125,
        "File:1870 Gruetzner Hinter den Kulissen anagoria.JPG",
        "b8472a980db1f510c6fd8bfa511863d9a06f23cf",
        "Behind the Scenes",
        "Eduard von Gr\xfctzner",
    ),
    CuratedWork(
        21938974,
        "File:Eduardo de Martino - Botafogo Beach - Google Art Project.jpg",
        "f43e12b81e0dba2f95254f988969d6ef2882d82a",
        "Botafogo Beach",
        "Eduardo de Martino",
    ),
    CuratedWork(
        134181389,
        "File:Edward Lear, Tarxien, Malta.jpg",
        "39a0c935a5cbb7792d6755b6add082d36cdcb670",
        "Edward Lear, Tarxien, Malta",
        "Edward Lear",
    ),
    CuratedWork(
        22250995,
        ("File:Edward Lear - Maharraka, 7-15 am, 14 February 1867 (462) - Google Art Project.jpg"),
        "45dffe919fd9a1c0ffea6e26967692c415fe1d20",
        "Maharraka, 7:15 am, 14 February 1867 (462)",
        "Edward Lear",
    ),
    CuratedWork(
        22205181,
        "File:Edward Lear - Near Wady Halfeh - Google Art Project.jpg",
        "54ed8f94a62ad27b716d3ccd0d2745357416aa34",
        "Near Wady Halfeh",
        "Edward Lear",
    ),
    CuratedWork(
        22204845,
        "File:Edward Lear - Shelaal - Google Art Project.jpg",
        "b9933e0a72561f2435e968aaaad8d7ac756f3a5a",
        "Shelaal",
        "Edward Lear",
    ),
    CuratedWork(
        17224019,
        "File:Edward William Cooke Venezia 1851.jpg",
        "524b50e16896770ecd841c3d28aba5924d980c49",
        "Venice",
        "Edward William Cooke",
    ),
    CuratedWork(
        2152784,
        "File:Babylonian marriage market.jpg",
        "4fdd2dcefeffd443eb2fd74da8d26d4230338a66",
        "The Babylonian Marriage Market",
        "Edwin Long",
    ),
    CuratedWork(
        21987965,
        "File:Egon Schiele - Reclining Woman - Google Art Project.jpg",
        "130d5c995094a761fbf76b4a0d3d3b99ab85ca73",
        "Reclining Woman",
        "Egon Schiele",
    ),
    CuratedWork(
        73882709,
        ("File:Emil Carlsen, Nantasket Beach, 1876, 1940.1087, Art Institute of Chicago.jpg"),
        "cde54e7c525db8a7d7b88f8e4d956dfb94e62f5d",
        "Nantasket Beach",
        "Emil Carlsen",
    ),
    CuratedWork(
        79951735,
        "File:Eugen Bracht - Abendd\xe4mmerung am Toten Meer (1881).jpg",
        "1d48926271924cdc0da98c403fa8a93c4e1988d3",
        "Dusk on the Dead Sea",
        "Eugen Bracht",
    ),
    CuratedWork(
        22007414,
        (
            "File:Eug\xe8ne von Gu\xe9rard - Lake Wakatipu with Mount Earnslaw, Middle "
            "Island, New Zealand - Google Art Project.jpg"
        ),
        "89201b679ab15189d0cdf3a03947cde31e2d6e1b",
        "Lake Wakatipu with Mount Earnslaw, Middle Island, New Zealand",
        "Eugene von Guerard",
    ),
    CuratedWork(
        74249300,
        (
            "File:Eug\xe8ne Fromentin - On the Nile, Near Philae - 1900.580 - Art Insti"
            "tute of Chicago.jpg"
        ),
        "8a19fc59a58614d8a069c574e7c2a1c2cb1130b8",
        "On the Nile, Near Philae",
        "Eug\xe8ne Fromentin",
    ),
    CuratedWork(
        63935711,
        "File:NantesMAIsabey.jpg",
        "8015f57b82371bdaba3352e8b47034ddb81a02c4",
        "Shipwrecking of three-masted ship Emily 1823",
        "Eug\xe8ne Isabey",
    ),
    CuratedWork(
        81434273,
        ("File:Eug\xe8ne Boudin, Beach House with Flags at Trouville, c. 1865, NGA 66472.jpg"),
        "33036ddb8554c1a13a15c7f1f92d5b239ca3f906",
        "Beach House with Flags at Trouville",
        "Eug\xe8ne Louis Boudin",
    ),
    CuratedWork(
        164265708,
        (
            "File:Femmes de p\xeacheurs au repos - Eug\xe8ne Boudin - Museum Langmatt-8"
            "541 (without frame).jpg"
        ),
        "050cc4d9fb63d0346737460f84c1a46376774f88",
        "Fishwomen Seated on the Beach at Berck",
        "Eug\xe8ne Louis Boudin",
    ),
    CuratedWork(
        18581296,
        "File:Eug\xe8ne Boudin - Sur la plage \xe0 Trouville.jpg",
        "f52f6b0621f15a3842167fc42fcfe2fc926bc40d",
        "On the Beach at Trouville",
        "Eug\xe8ne Louis Boudin",
    ),
    CuratedWork(
        146082144,
        ("File:Eugene boudin trouville scene de plage2024 CKS 22658 0218 000(100645).jpg"),
        "3e9d799821d708ff4f1304ac2be0b3e1e714bb46",
        "Trouville, sc\xe8ne de plage",
        "Eug\xe8ne Louis Boudin",
    ),
    CuratedWork(
        156053939,
        (
            "File:1892 Boudin Washerwomen on the Bank of the Touques Tel Aviv Museum of"
            " Art anagoria.jpg"
        ),
        "8d98296c3f31ed3c0f8ac26e95bd20852773cb0a",
        "Washerwomen on the Bank of the Touques",
        "Eug\xe8ne Louis Boudin",
    ),
    CuratedWork(
        77816836,
        "File:Fabius Brest - A capriccio of Constantinople.jpg",
        "5ab9a75e376b687d59b23e2385cb57abc74aad6f",
        "A capriccio of Constantinople",
        "Fabius Brest",
    ),
    CuratedWork(
        66317047,
        ("File:Fanny Churberg - Birches by the Water - A II 1343 - Finnish National Gallery.jpg"),
        "9ffd962ff20d41be022ca026a1f1415fb0de6e6d",
        "Birches by the Water",
        "Fanny Churberg",
    ),
    CuratedWork(
        97701737,
        ("File:Milan Flori\xe1n - Na p\xfati v Levo\u010di - O 357 - East Slovak Gallery.jpg"),
        "5e6048a896513c71017c329f1ed5d964c3c71d8b",
        "Slovak: Na p\xfati v Levo\u010di",
        "Florian Milan",
    ),
    CuratedWork(
        21911881,
        ("File:Francis Augustus Silva - The Hudson at the Tappan Zee - Google Art Project.jpg"),
        "77d742882195caabbe1e53c852661297c5bb1586",
        "The Hudson at the Tappan Zee",
        "Francis A. Silva",
    ),
    CuratedWork(
        17224098,
        "File:Francois Musin Marinebild.jpg",
        "4f9415b96d07d19572afb186d38ba1fc19b28064",
        "Marine",
        "Fran\xe7ois Musin",
    ),
    CuratedWork(
        45559316,
        "File:Greek-girls-playing-at-ball.jpg",
        "c08e906b198841a292b879b24368d479c2f40708",
        "Greek Girls Playing Ball",
        "Frederic Leighton",
    ),
    CuratedWork(
        48209049,
        "File:A Dash for the Timber by Frederic Remington.jpg",
        "fdb98d03d713ead593be5b67a93d71b0a49a66ee",
        "A Dash for the Timber",
        "Frederic Remington",
    ),
    CuratedWork(
        31585705,
        "File:The Volunteers YORAG-271.jpg",
        "cc753a9191a81608aa969a57ea3ab1f276632a86",
        "The Volunteers",
        "Frederick Daniel Hardy",
    ),
    CuratedWork(
        140184404,
        (
            "File:F\xe9licien Rops - Landscape in Sweden - 1947-D - Museum of Fine Arts"
            " Ghent (MSK).jpg"
        ),
        "7c320e1e7f66b4c3bf358dc287f9a1145b8d3793",
        "Landscape in Sweden",
        "F\xe9licien Rops",
    ),
    CuratedWork(
        98847197,
        (
            "File:F\xe9lix Ziem - Constantinople, le ca\xefque de la sultane - PPP217 -"
            " Mus\xe9e des Beaux-Arts de la ville de Paris.jpg"
        ),
        "44147937dc10bae3116cde06acb3ae9bd1b6f994",
        "Constantinople, le ca\xefque de la sultane",
        "F\xe9lix Ziem",
    ),
    CuratedWork(
        83513302,
        "File:Bouwterrein, SK-A-2977.jpg",
        "24d5f7cf6fe9761d31f6ea496854d04e017d996c",
        "Bouwterrein, SK-A-2977",
        "George Hendrik Breitner",
    ),
    CuratedWork(
        5635463,
        "File:George Luks - Houston Street.jpg",
        "cb908b4e936c46e4a72f6dcf43196dd8d9b5fe1b",
        "Houston Street",
        "George Luks",
    ),
    CuratedWork(
        148767443,
        (
            "File:1885 Jakobides Church in blooming field in Bavaria National Gallery -"
            " Corfu Annex anagoria.jpg"
        ),
        "ef4a2ad86e9efefbc1024822c3697ec6de046c51",
        "Church in blooming field in Bavaria",
        "Georgios Jakobides",
    ),
    CuratedWork(
        39680145,
        "File:Giovanni Battista Castagneto - Porto do Rio de Janeiro (2).jpg",
        "41adf1fc261aeed061ff1a10997e67053164e1a3",
        "The port of Rio de Janeiro",
        "Giovanni Battista Castagneto",
    ),
    CuratedWork(
        147230027,
        "File:The Palace of Westminster, London (1878), by Giuseppe De Nittis.jpg",
        "b4fd5512f1f412c286239bfef4812d9301b86e77",
        "The Palace of Westminster, London",
        "Giuseppe De Nittis",
    ),
    CuratedWork(
        164784050,
        "File:The Victoria Embankment, London (1875), by Giuseppe De Nittis.jpg",
        "7c0292992075f4ca8db1f4685fa75bb7b7182fb1",
        ("Veduta di Londra (Il Victoria Embankment, Londra) The Victoria Embankment, London"),
        "Giuseppe De Nittis",
    ),
    CuratedWork(
        140216695,
        (
            "File:Gustave Den Duyts - Village Street in the Rain - 1942-W - Museum of F"
            "ine Arts Ghent (MSK).jpg"
        ),
        "ce7a8831406758682416803191b5ac55e52b091b",
        "Village Street in the Rain",
        "Gustave Den Duyts",
    ),
    CuratedWork(
        66351503,
        (
            "File:Gustave Dor\xe9 - Torrent in the Highlands - 72.17 - Indianapolis Mus"
            "eum of Art.jpg"
        ),
        "d068f119919159da49e02ea97f84082bf0d15e30",
        "Torrent in the Highlands",
        "Gustave Dor\xe9",
    ),
    CuratedWork(
        48192935,
        "File:L'arriv\xe9e de Champlain \xe0 Qu\xe9bec.jpg",
        "84e59f3e511164c2234c558273416b4fb245d86a",
        "L'Arriv\xe9e de Champlain \xe0 Qu\xe9bec",
        "Henri Beau",
    ),
    CuratedWork(
        98262508,
        (
            "File:Henri Joseph Harpignies - Le Colis\xe9e \xe0 Rome - PPP615 - Mus\xe9e"
            " des Beaux-Arts de la ville de Paris.jpg"
        ),
        "15481d9d6e24bb06a8a0884fe339a92c85b38a4a",
        "Le Colis\xe9e \xe0 Rome",
        "Henri Harpignies",
    ),
    CuratedWork(
        98922913,
        (
            "File:Henry Brokman - Poupe de l'Alda, mer d\xe9mont\xe9e - PPP3644 - Mus"
            "\xe9e des Beaux-Arts de la ville de Paris.jpg"
        ),
        "53493f04cbd88e8e9ad8af581eabee55f96a14c0",
        "Poupe de l'Alda, mer d\xe9mont\xe9e",
        "Henry Brokmann",
    ),
    CuratedWork(
        99879445,
        (
            "File:Henryk Pillati - Eastern scene \u2013 Selling horses - MP 2527 MNW - "
            "National Museum in Warsaw.jpg"
        ),
        "4930e1a779c3294203440aa7c36a76caf6f33c2a",
        "Eastern scene \u2013 Selling horses",
        "Henryk Pillati",
    ),
    CuratedWork(
        21878594,
        (
            "File:Sir Hubert von Herkomer - Eventide- A Scene at the Westminster Union "
            "- Google Art Project.jpg"
        ),
        "a35b3cb4142f180bc3c0453a77a8aa3e5b1ab4e1",
        "Eventide- A Scene at the Westminster Union",
        "Hubert von Herkomer",
    ),
    CuratedWork(
        148442005,
        "File:The Dance XI (Bal Bullier) (Ida Gerhardi) DSC5684 (cropped).jpg",
        "e78d5a78d083ca861de003519c08ab0a63c0f2c2",
        "Ida Gerhardi",
        "Ida Gerhardi",
    ),
    CuratedWork(
        66352146,
        (
            "File:James Crawford Thom - Landscape with Boatman - 74.164 - Indianapolis "
            "Museum of Art.jpg"
        ),
        "c09e7440ef66403da3fe06f44a91452e7154fd9f",
        "Landscape with Boatman",
        "J. C. Thom",
    ),
    CuratedWork(
        22007097,
        "File:Jacob Maris - View at Montigny-sur-Loing - Google Art Project.jpg",
        "e8b2e4595bc717202e6966cfae82f28fa9871e4c",
        "View at Montigny-sur-Loing",
        "Jacob Maris",
    ),
    CuratedWork(
        98110746,
        (
            "File:James Jacques Joseph Tissot - Le retour de l'enfant prodigue - PPP485"
            "6 - Mus\xe9e des Beaux-Arts de la ville de Paris.jpg"
        ),
        "3bd292e78980cca86df3a92b86e7789aa573f9b5",
        "Le retour de l'enfant prodigue",
        "James Tissot",
    ),
    CuratedWork(
        67711,
        "File:Alchemik Sedziwoj Matejko.JPG",
        "2f677567eabb7802454a784437142e85a252d29c",
        "Alchemist Sendivogius",
        "Jan Matejko",
    ),
    CuratedWork(
        98844586,
        (
            "File:Jan Stanis\u0142awski - Fields at Proszowice - MNK II-b-634 - Nationa"
            "l Museum Krak\xf3w.jpg"
        ),
        "95beca63e264bfd63b1531aaf9857277a8c503fe",
        "Fields at Proszowice",
        "Jan Stanis\u0142awski",
    ),
    CuratedWork(
        98843700,
        ("File:Jan Stanis\u0142awski - Sun - MNK II-b-845 - National Museum Krak\xf3w.jpg"),
        "53beb7bf87cd6156ca705681adff7defb4016fa7",
        "Sun",
        "Jan Stanis\u0142awski",
    ),
    CuratedWork(
        115802349,
        "File:Jan Van Beers - After the ball.jpg",
        "028801a7d6a8cbf030c7d223a9bff82b3ab8a076",
        "After the ball",
        "Jan van Beers",
    ),
    CuratedWork(
        57670691,
        "File:1807, Friedland MET DT2144.jpg",
        "7d2f3f0c85a10d2330218ef725fa1a10dc39884c",
        "1807, Friedland",
        "Jean-Louis-Ernest Meissonier",
    ),
    CuratedWork(
        74945568,
        ("File:Jean L\xe9on G\xe9r\xf4me - Chariot Race - 1983.380 - Art Institute of Chicago.jpg"),
        "586b46e20a229bcc14b674d446ceccbd779b2c7b",
        "Chariot Race",
        "Jean-L\xe9on G\xe9r\xf4me",
    ),
    CuratedWork(
        139236388,
        ("File:Johannes Warnardus Bilders-Der Teich von Oosterbeek-04224 (cropped).jpg"),
        "c03eea33782bbeb8351971dbf455c91340b09f5b",
        "The pond at Oosterbeek",
        "Johannes Warnardus Bilders",
    ),
    CuratedWork(
        140453043,
        ("File:Johannes Wilhjelm, Idyl p\xe5 heden, 1908, KMS2077, Statens Museum for Kunst.jpg"),
        "ddae9fc24033e2914c346d7c9a735c21149ec504",
        "Idyl p\xe5 heden",
        "Johannes Wilhjelm",
    ),
    CuratedWork(
        29660609,
        "File:John Brett - Southern Coast of Guernsey - Google Art Project.jpg",
        "6aff051909b466fe78411c043fc6a90178cf0cab",
        "Southern Coast of Guernsey",
        "John Brett",
    ),
    CuratedWork(
        22008059,
        "File:John Frederick Herring - Harvest - Google Art Project.jpg",
        "b33977175d058928727d940bb55cd6ded90ad885",
        "Harvest",
        "John Frederick Herring, Jr.",
    ),
    CuratedWork(
        57365122,
        "File:A Bachelor's Drawer MET DT11198.jpg",
        "cf8fa77ff083d7d50f3f7f9900f9210b9b77cc7a",
        "A Bachelor's Drawer",
        "John Haberle",
    ),
    CuratedWork(
        21911817,
        (
            "File:John La Farge - Flowers on a Japanese Tray on a Mahogany Table - Goog"
            "le Art Project.jpg"
        ),
        "cf53cbfe3884250b678aeb15bc096e968a6a0c7c",
        "Flowers on a Japanese Tray on a Mahogany Table",
        "John La Farge",
    ),
    CuratedWork(
        22029372,
        "File:Jos\xe9 Llovera Bofill - The Christening - Google Art Project.jpg",
        "3e770069344271ee5360070fbe0918870f666497",
        "The Christening",
        "Josep Llovera i Bufill",
    ),
    CuratedWork(
        92531946,
        "File:Joseph Alanen - Conquest of H\xe4me.jpg",
        "ea4a643812da3c43b8815fdde349ee24e910d4ce",
        "Conquest of H\xe4me",
        "Joseph Alanen",
    ),
    CuratedWork(
        23603036,
        "File:Joseph Severn - The deserted village - Google Art Project.jpg",
        "d2ee24c6c97913636d6647a53f2ff6d067ef8263",
        "The deserted village",
        "Joseph Severn",
    ),
    CuratedWork(
        35102868,
        "File:Jo\u017eka Uprka - J\xedzda kr\xe1l\u016f ve Vl\u010dnov\u011b.jpg",
        "de5782c033d3f994fcfefe8c63cc419225cda105",
        "Ride of the Kings",
        "Jo\u017ea Uprka",
    ),
    CuratedWork(
        165011548,
        "File:Julia Beck, Portrait de Mademoiselle Cecilia Lewenhaupt, 1886.jpg",
        "9935c8e2cf1d8c0ae85af5159d46caca84eb8623",
        "Julia Beck, Portrait de Mademoiselle Cecilia Lewenhaupt, 1886",
        "Julia Beck",
    ),
    CuratedWork(
        83539260,
        "File:Landschap in Drenthe, SK-A-1185.jpg",
        "2f8692217ca2313bd99191e167b38704d8c57dc5",
        "Landschap in Drenthe",
        "Julius van de Sande Bakhuyzen",
    ),
    CuratedWork(
        99880781,
        (
            "File:J\xf3zef Che\u0142mo\u0144ski - Burial mound - MP 958 MNW - National "
            "Museum in Warsaw.jpg"
        ),
        "11d6d44487cb337ea8efb128f4e273badce24c87",
        "Kurhan A Barrow",
        "J\xf3zef Che\u0142mo\u0144ski",
    ),
    CuratedWork(
        148542357,
        (
            "File:J\xf8rgen V Sonne, Aff\xe6ren ved Vorbasse den 29 februar 1864, 1877,"
            " KMS1429, Statens Museum for Kunst.jpg"
        ),
        "9543931167e5a8de246b580a76d3fb946911a42b",
        "The Skirmish at Vorbasse February the 29th, 1864",
        "J\xf8rgen Sonne",
    ),
    CuratedWork(
        97754997,
        (
            "File:Karol Miloslav Lehotsk\xfd - Sl\xe1vi\u010d\xed ostrov pri Iloku - O "
            "624 - Slovak National Gallery.jpg"
        ),
        "1f7f394a7b31e4be51b3b73ef910a4171b9ef009",
        "Nightingale Isle by Ilok",
        "Karol Miloslav Lehotsk\xfd",
    ),
    CuratedWork(
        97678005,
        (
            "File:Karol Miloslav Lehotsk\xfd - Dedinsk\xfd potok - O 719 - Slovak Natio"
            "nal Gallery.jpg"
        ),
        "9bde1f09532f8bcbe1bf5bd40e3806b32b887a4e",
        "Slovak: Dedinsk\xfd potok A Village Brook",
        "Karol Miloslav Lehotsk\xfd",
    ),
    CuratedWork(
        38212701,
        "File:'Meeting of Women' by Ker-Xavier Roussel, Norton Simon Museum.JPG",
        "d98fbfcf5cb5f7ac1a427e722ff0c0625e426507",
        "Meeting of Women",
        "Ker-Xavier Roussel",
    ),
    CuratedWork(
        25149244,
        "File:1909 Gestel liegender Akt anagoria.JPG",
        "9fbbd276d2b353d300106174d114f67cb432bd91",
        "Reclining nude",
        "Leo Gestel",
    ),
    CuratedWork(
        23604298,
        "File:Bernard Hall - After dinner - Google Art Project.jpg",
        "a817aa01abdc3311c1f1df61c55f0d3583484bba",
        "After dinner",
        "Lindsay Bernard Hall",
    ),
    CuratedWork(
        50496417,
        "File:A Fairy Under Starry Skies, by Luis Ricardo Falero.jpg",
        "ce3c09e54bf3617a188a4986c0260f13f89e374c",
        "A Fairy Under Starry Skies",
        "Luis Ricardo Falero",
    ),
    CuratedWork(
        17528965,
        "File:Countryside at Munk\xe1cs (Watering).jpg",
        "3072864f0da104c5285ebe8f4590dc53dc7ebd15",
        "Muka\u010devo's Surrounding (Watering Trough)",
        "L\xe1szl\xf3 Medny\xe1nszky",
    ),
    CuratedWork(
        77904320,
        (
            "File:Ladislav Medny\xe1nszky - Jarn\xe1 krajina (Jar v ovocnom sade) - O 2"
            "819 - East Slovak Gallery.jpg"
        ),
        "d1b47c6cb250c7c700be2a62e1c58cc7c7aeaf33",
        "Slovak: Jarn\xe1 krajina (Jar v ovocnom sade)",
        "L\xe1szl\xf3 Medny\xe1nszky",
    ),
    CuratedWork(
        67893332,
        (
            "File:Ladislav Medny\xe1nszky - Ve\u013ek\xe1 letn\xe1 krajina s riekou. K"
            "\xfapanie - O 4212 - Slovak National Gallery.jpg"
        ),
        "38c9f07ac390942bcb463b5c06b6f8f5bb34b67b",
        "Ve\u013ek\xe1 letn\xe1 krajina s riekou. K\xfapanie",
        "L\xe1szl\xf3 Medny\xe1nszky",
    ),
    CuratedWork(
        76412216,
        "File:Salome's Dance.jpg",
        "3c72709e296733795058c5fcb4f62a7572e6679a",
        "Salome's Dance",
        "Maurycy Gottlieb",
    ),
    CuratedWork(
        22029214,
        "File:Modest Urgell - Landscape - Google Art Project (359249).jpg",
        "37c2948da2e65cea76b12ae1fa024b8e39cc0d33",
        "Landscape",
        "Modest Urgell",
    ),
    CuratedWork(
        21952919,
        "File:Modest Urgell - The Bell for Prayer - Google Art Project.jpg",
        "d865dcf3c88af12262274f90ae617e45a1a41a82",
        "The Bell for Prayer",
        "Modest Urgell",
    ),
    CuratedWork(
        76362098,
        "File:Boerenerf met liggend varken RP-T-1972-50.jpg",
        "56fed5e7917dd6b498054abac32f18fe3399f523",
        "Boerenerf met liggend varken",
        "Nicolaas Bastert",
    ),
    CuratedWork(
        148565486,
        (
            "File:Niels Larsen Stevns, Udsigt fra Bokul Gudhjem, 1929, KMS3998, Statens"
            " Museum for Kunst.jpg"
        ),
        "8ee2207096df6eeed00282a40d6fb1795ec3186a",
        "View from Bokul, Gudhjem",
        "Niels Larsen Stevns",
    ),
    CuratedWork(
        80335575,
        "File:Niels Skovgaard - Landscape from Foldalen in Norway (1911).jpg",
        "2dc2f539358d622f3218d401f477d9658b08f81f",
        "Landscape from Foldalen in Norway",
        "Niels Skovgaard",
    ),
    CuratedWork(
        98925019,
        ("File:Ferdinand Katona - Horsk\xe1 krajina - O 1033 - East Slovak Gallery.jpg"),
        "94c119c6c810f83dd31d5b552191ccb83008db19",
        "Slovak: Horsk\xe1 krajina",
        "N\xe1ndor Katona",
    ),
    CuratedWork(
        80512390,
        ("File:Ferdinand Katona - Winter Landscape - O 2912 - Slovak National Gallery.jpg"),
        "c1fc0fb647f2a49fae0355251f5961c2a32f39e9",
        "Winter Landscape",
        "N\xe1ndor Katona",
    ),
    CuratedWork(
        66315025,
        (
            "File:Oscar Kleineh - Rantamaisema, Flor\xf6 - A III 2554-82 - Finnish Nati"
            "onal Gallery.jpg"
        ),
        "63b5b493beeb409f3cc1c0ae7959ea7fbdd294c5",
        "Rantamaisema, Flor\xf6",
        "Oscar Kleineh",
    ),
    CuratedWork(
        148507877,
        (
            "File:Otto Sinding, En for\xe5rsdag i Lofoten, 1882, KMS1230, Statens Museu"
            "m for Kunst.jpg"
        ),
        "3f030884bf383a163c31f263fb4cf46a51a3a07a",
        "Spring Day in Lofoten",
        "Otto Sinding",
    ),
    CuratedWork(
        76558058,
        "File:The Menin Road.jpg",
        "80742067de7d0671b31fd5c3bc69b5bfbb4e69b5",
        "The Menin Road",
        "Paul Nash",
    ),
    CuratedWork(
        102641108,
        (
            "File:Marang\xe9 - Les ruines du palais des Tuileries, apr\xe8s l'incendie "
            "de 1871 - P1803 - Mus\xe9e Carnavalet.jpg"
        ),
        "f7c378578b8294acd3ce553bcf11becc5567c2a3",
        "Les ruines du palais des Tuileries, apr\xe8s l'incendie de 1871",
        "Pierre-Fran\xe7ois Marang\xe9",
    ),
    CuratedWork(
        148738953,
        "File:Piet Verhaert - Vlissingen.jpg",
        "f000a603beb04d97e251ae7883a1f1ee11edfd9b",
        "Vlissingen",
        "Piet Verhaert",
    ),
    CuratedWork(
        21880968,
        "File:Prilidiano Pueyrredon - La lavandera - Google Art Project.jpg",
        "1f1ff685126e16ab00cfcdd946ad03a4b69acfcf",
        "La lavandera",
        "Prilidiano Pueyrred\xf3n",
    ),
    CuratedWork(
        107396060,
        "File:Sorbi - Bacchanal.jpg",
        "a02e61d20fe637790f61a418b2f1636bc4b1373b",
        "Bacchanal",
        "Raffaello Sorbi",
    ),
    CuratedWork(
        21925802,
        ("File:Ramon Mart\xed i Alsina - Ruins of the Palace - Google Art Project.jpg"),
        "822cd393f3299ef4edfa0e4caeedf0ca2505e948",
        "Ruins of the Palace",
        "Ramon Mart\xed Alsina",
    ),
    CuratedWork(
        100486076,
        ("File:Raoul Arus - Enl\xe8vement d'un ballon - P367 - Mus\xe9e Carnavalet.jpg"),
        "28840d1dabc468251a62eb0c597f7b6c70433d09",
        "Enl\xe8vement d'un ballon",
        "Raoul Arus",
    ),
    CuratedWork(
        45326162,
        "File:Landschap met hutten op de heide SK-A-1639.jpg",
        "a943f73803d02d95a3fc3c58218cb6be9a87fdb8",
        "Landscape with Cottages on the Heath",
        "Remigius Adrianus Haanen",
    ),
    CuratedWork(
        41242543,
        "File:Haanen-Open Landscape in the Evening Light.jpg",
        "0712b476f6a32e7437e9a95686aca0c770e20cac",
        "Open Landscape in the Evening Light",
        "Remigius Adrianus Haanen",
    ),
    CuratedWork(
        29864826,
        (
            "File:Arredondo y Calmache, Ricardo - Tanners Workshop - Tanners Workshop o"
            "f Ubide - Google Art Project.jpg"
        ),
        "7d0ba80ab82633c3d4c01413afea8b49c315c9d2",
        "Tanners Workshop - Tanners Workshop of Ubide",
        "Ricardo Arredondo Calmache",
    ),
    CuratedWork(
        32777215,
        "File:Richard Ansdell - At the well (1870s).jpg",
        "796e9a82dba33d3d0fa4799caaac5bfbc1ce0c82",
        "At the well",
        "Richard Ansdell",
    ),
    CuratedWork(
        67541656,
        ("File:Richard Friese - Gemengd bos in Canada - 0218 - Rijksmuseum Twenthe.jpg"),
        "c6a04a7f97c705e591f87b06c0abd1241fe20f6b",
        "Mixed forest in Canada",
        "Richard Friese",
    ),
    CuratedWork(
        22144408,
        (
            "File:Robert Dowling - A Sheikh and his son entering Cairo on their return "
            "from a pilgrimage to Mecca - Google Art Project.jpg"
        ),
        "f7c9923972cefa7b52fb94ce61afa1c71cd47823",
        ("A Sheikh and his son entering Cairo on their return from a pilgrimage to Mecca"),
        "Robert Hawker Dowling",
    ),
    CuratedWork(
        18532915,
        "File:'Buffalo Hunt' by Robert Jenkins Onderdonk, c. 1898.JPG",
        "512e1588450f95454b0ce19275852cf04df99bdd",
        "Buffalo Hunt",
        "Robert Jenkins Onderdonk",
    ),
    CuratedWork(
        142201718,
        "File:Landscape with Rainbow SAAM-1983.95.160 1-000001.jpg",
        "efc1193b91cba5848285881cbb6dc97bb7f0031e",
        "Landscape with Rainbow",
        "Robert Seldon Duncanson",
    ),
    CuratedWork(
        130381235,
        "File:Robert Warthm\xfcller - Der K\xf6nig \xfcberall (1886).jpg",
        "d8cf1f451c4aa6e93e7f3a8bea05faddd3a86548",
        "The King everywhere",
        "Robert Warthm\xfcller",
    ),
    CuratedWork(
        18399258,
        "File:N\xe1dler Grand Market Hall in Budapest 1898.jpg",
        "d2685c0a064267273188229de4536267e8696a6c",
        "The Building of Grand Market Hall in Budapest",
        "R\xf3bert N\xe1dler",
    ),
    CuratedWork(
        116223919,
        "File:At the villa of Poggiopiano (1888-89), by Silvestro Lega.jpg",
        "cf6d256399cfbc74ffec6b6a4ac1a088b88085d3",
        "At the villa in Poggio Piano",
        "Silvestro Lega",
    ),
    CuratedWork(
        149174803,
        "File:Rest on the hill (c.1894), by Silvestro Lega.jpg",
        "a84d258bb714dc169ff4f0ec7f72a180ab7efd05",
        "Riposo in collina Rest on the hill",
        "Silvestro Lega",
    ),
    CuratedWork(
        199676,
        (
            "File:Stanis\u0142aw Mas\u0142owski - Wsch\xf3d ksi\u0119\u017cyca (ol n p"
            "\u0142 1884).jpg"
        ),
        "c706617245b3e35e3a452da11071217edef298da",
        "Moonrise",
        "Stanis\u0142aw Mas\u0142owski",
    ),
    CuratedWork(
        72020929,
        "File:1853 05-10 Skelia Chernets' (copy by Zaleski).jpg",
        "15983dcec594032a605262609937e4f26f6cd9b0",
        "Skelia Chernets'",
        "Taras Shevchenko",
    ),
    CuratedWork(
        98344118,
        (
            "File:Th\xe9obald Chartran - Esquisse pour l'escalier de la Sorbonne , Ambr"
            "oise Par\xe9 au si\xe8ge de Metz - PPP4634 - Mus\xe9e des Beaux-Arts de la"
            " ville de Paris.jpg"
        ),
        "d0c6a28ded2a50e21b8dd78e313183aa93aac687",
        ("Esquisse pour l'escalier de la Sorbonne : Ambroise Par\xe9 au si\xe8ge de Metz"),
        "Th\xe9obald Chartran",
    ),
    CuratedWork(
        13502594,
        (
            "File:Vasily Surikov - \u0423\u0442\u0440\u043e \u0441\u0442\u0440\u0435"
            "\u043b\u0435\u0446\u043a\u043e\u0439 \u043a\u0430\u0437\u043d\u0438 - Goog"
            "le Art Project.jpg"
        ),
        "0c0f48f670000ed05aa97e387fa89e5355eda36b",
        "Morning of the Execution of the Streltsy",
        "Vasily Surikov",
    ),
    CuratedWork(
        13955306,
        "File:Westerholm Vinterlandskap fr\xe5n Kymmene bruk.jpg",
        "03ed9c0e5e0b8f387c691f4a4aaabacce5b44060",
        "Winter Landscape from Kymintehdas",
        "Victor Westerholm",
    ),
    CuratedWork(
        146757712,
        (
            "File:\u0412.\u041c. \u0412\u0430\u0441\u043d\u0435\u0446\u043e\u0432. "
            "\u041a\u043e\u0432\u0435\u0440-\u0441\u0430\u043c\u043e\u043b\u0435\u0442 "
            "(2024).jpg"
        ),
        "023bee8f3f82a6e1c9dbb31d3a8797a3dd0f6231",
        "Flying Carpet",
        "Viktor Vasnetsov",
    ),
    CuratedWork(
        98807899,
        (
            "File:Vilhelm Melbye - Marine landscape with sail boats - M.Ob.1989 - Natio"
            "nal Museum in Warsaw.jpg"
        ),
        "3f22a3ff52d74cac07b54be14c7db521a40b0833",
        "Marine landscape with sail boats",
        "Vilhelm Melbye",
    ),
    CuratedWork(
        38939353,
        "File:Walter T. Crane - Neptune's Horses (ca.1892).jpg",
        "99412cc8c6f80a8308f3f78980021d6e8583a2f9",
        "Neptune's Horses",
        "Walter Crane",
    ),
    CuratedWork(
        40937667,
        "File:Wilhelm Kotarbinski - The Nile Mist.jpg",
        "ca8a66f64d5e1b4bdd9692ab74dfa527bf18a36c",
        "The Nile Mist",
        "Wilhelm Kotarbi\u0144ski",
    ),
    CuratedWork(
        141802237,
        "File:William Frederick de Haas - Cliffs of Star Island (1878).jpg",
        "048980a6db4ebbbd4cd063c4a65b2a7d19d3dd6a",
        "Cliffs of Star Island",
        "Willem Frederik de Haas",
    ),
    CuratedWork(
        34402003,
        "File:Koeien bij een plas Rijksmuseum SK-A-3689.jpeg",
        "5abffdb3387f7af2528f72fb8be7cc01d8e66684",
        "Koeien bij een plas",
        "Willem Maris",
    ),
    CuratedWork(
        83488675,
        "File:De brug over de IJssel bij Doesburg, SK-A-3606.jpg",
        "8a6f97145b6e8a3a26dfc89b6f5a2c895ed5b913",
        "De brug over de IJssel bij Doesburg",
        "Willem Roelofs",
    ),
    CuratedWork(
        119915189,
        (
            "File:William Logsdail - The Piazza of Saint Mark's, Venice - 1898P59 - Bir"
            "mingham Museums Trust.jpg"
        ),
        "e61291cab05d3dd05121353acb91e1c1db2366a6",
        "The Piazza of Saint Mark's, Venice",
        "William Logsdail",
    ),
    CuratedWork(
        39655981,
        "File:'Noon' by William Penhallow Henderson, New Mexico Museum of Art.JPG",
        "e243e8b342c7df3a6e6edaf57e3cf3dae018269b",
        "Noon",
        "William Penhallow Henderson",
    ),
    CuratedWork(
        5702693,
        "File:Amaldus Nielsen - Fjordparti (1890).jpg",
        "0aff71828ca489df569dcdbd22014e3fa45b059d",
        "Norwegian: Fjordparti",
        "Amaldus Nielsen",
    ),
    CuratedWork(
        5703012,
        "File:Amaldus Nielsen - Mennesker p\xe5 en strand (1894).jpg",
        "5bed0b35c9976b5ab35664becf443f1f4711608d",
        "People on a Beach",
        "Amaldus Nielsen",
    ),
    CuratedWork(
        28939444,
        "File:Henryk Siemiradzki - By the Fountain.jpg",
        "2403e76415b16c2fb85fa5e734d4f12ae499f189",
        "By the fountain",
        "Henryk Siemiradzki",
    ),
    CuratedWork(
        93161707,
        "File:Hjalmar Munsterhjelm - November Evening.jpg",
        "1a1b744fc2f05d773528d80fd2feb7d540651593",
        "November Evening",
        "Hjalmar Munsterhjelm",
    ),
    CuratedWork(
        93166146,
        "File:Hjalmar Munsterhjelm - Shepherd in the Alps.jpg",
        "fe381d293b71de91dae2c14efb9186230dffa095",
        "Shepherd in the Alps",
        "Hjalmar Munsterhjelm",
    ),
    CuratedWork(
        3734328,
        "File:Max Liebermann, Kinderspielplatz im Tiergarten zu Berlin, 1885.jpg",
        "9e4f7144a42994b6bb6d90fcc1dda92f532d0d48",
        "Max Liebermann, Kinderspielplatz im Tiergarten zu Berlin, 1885",
        "Max Liebermann",
    ),
    CuratedWork(
        111254556,
        "File:Bruno Liljefors - Vinterjakt med r\xe4v och st\xf6vare 1898.jpg",
        "b1d0227b809ad07279cf2dec0ea311042f5b914e",
        "Winter hunting with fox and scent hound",
        "Bruno Liljefors",
    ),
    CuratedWork(
        29456789,
        "File:1859 Spitzweg Badende Frauen am Meer bei Dieppe anagoria.JPG",
        "45da1a81b9a8424c5d6ea3ea1757883a2768bc3f",
        "Woman bath in Dieppe I",
        "Carl Spitzweg",
    ),
    CuratedWork(
        13318993,
        "File:James McNeill Whistler - Chelsea Shops - Google Art Project.jpg",
        "421dda23b1e382ed826c7a9badc785b239042ce1",
        "Chelsea Shops",
        "James McNeill Whistler",
    ),
    CuratedWork(
        97946973,
        (
            "File:James McNeill Whistler - The Note in Orange and Blue (Sweet Shop) - P"
            "25e6 - Isabella Stewart Gardner Museum.jpg"
        ),
        "3c341228968f8a466c35c88044a4c898a048c56e",
        "The Note in Orange and Blue (Sweet Shop)",
        "James McNeill Whistler",
    ),
    CuratedWork(
        91996431,
        ("File:P.S. Kr\xf8yer, Kunstnerfrokost i Cernay-la-Ville, 1879, 1096, Skagens Museum.jpg"),
        "0d95f727de562c60b67f1ccd8a694deed785e792",
        "Artists' lunch. Cernay-la-Ville",
        "Peder Severin Kr\xf8yer",
    ),
    CuratedWork(
        66316616,
        (
            "File:Berndt Lindholm - View from Hisingen near Gothenburg - A I 179 - Finn"
            "ish National Gallery.jpg"
        ),
        "a250226aa705dc44a9a91cfdbb7410c1d11e275f",
        "View from Hisingen near Gothenburg",
        "Berndt Lindholm",
    ),
    CuratedWork(
        74317600,
        "File:C F d'Aubigny coucher de soleil \xe0 Villerville 1874.jpg",
        "73dc61641c5a6a02ae88a6aa8062e1e4fe666123",
        "C F d'Aubigny coucher de soleil \xe0 Villerville 1874",
        "Charles-Fran\xe7ois Daubigny",
    ),
    CuratedWork(
        148294579,
        (
            "File:La Tamise \xe0 Erith - Charles-Fran\xe7ois Daubigny - Mus\xe9e du Lou"
            "vre Peintures RF 1365.jpg"
        ),
        "582a7447e7e07e6640ca1c258ca60ad3f48d80d9",
        "La Tamise \xe0 Erith.",
        "Charles-Fran\xe7ois Daubigny",
    ),
    CuratedWork(
        31231760,
        "File:Charles-Fran\xe7ois Daubigny - Les p\xe9niches (1865).jpg",
        "5e7de326438ab81f6a725e9385c292ef73d4c357",
        "The Barges",
        "Charles-Fran\xe7ois Daubigny",
    ),
    CuratedWork(
        84964046,
        (
            "File:Charles-Fran\xe7ois Daubigny - The Edge of the Pond - 33-1974 - Saint"
            " Louis Art Museum.jpg"
        ),
        "18082dba82a2d71949051cf73592ee41e775e10e",
        "The Edge of the Pond",
        "Charles-Fran\xe7ois Daubigny",
    ),
    CuratedWork(
        38305052,
        ("File:'Beach at Trouville' by Eug\xe8ne Boudin, 1880, Norton Simon Museum.JPG"),
        "0c28fc8bdf63abd018f1a6505505af44bcc61f23",
        "Beach at Trouville",
        "Eug\xe8ne Boudin",
    ),
    CuratedWork(
        156053927,
        "File:1886 Boudin Trouville, Umbrellas Tel Aviv Museum of Art anagoria.jpg",
        "589792341ea7fe1ca1af47e01823f0acca0b3cc6",
        "Trouville, Umbrellas on the Beach",
        "Eug\xe8ne Boudin",
    ),
    CuratedWork(
        3418534,
        "File:Pierre-Auguste Renoir - Odalisque.jpg",
        "469e83f23d9bac3024e01af1e24a36ea0bda15e8",
        "Odalisque",
        "Pierre-Auguste Renoir",
    ),
    CuratedWork(
        24834582,
        "File:Winslow Homer - A Clam-Bake.jpg",
        "51021ec5bb51412c078d961fb9cf45f2e4e9d143",
        "A Clam-Bake",
        "Winslow Homer",
    ),
    CuratedWork(
        81494329,
        "File:Winslow Homer, View of Santiago de Cuba, 1885, NGA 64553.jpg",
        "60460b1b46620c41c7df27fc43b8e3ec1a7605c4",
        "View of Santiago de Cuba",
        "Winslow Homer",
    ),
    CuratedWork(
        36994951,
        "File:Abraham Govaerts - Forest View with Travellers.jpg",
        "25f83f285d92a72790f243cf8410f64903ebf0e3",
        "Forest View with Travellers",
        "Abraham Govaerts",
    ),
    CuratedWork(
        168187155,
        ("File:Aert van der Neer - Panoramic landscape, circa 1645-1655, 40 van der neer 5504.jpg"),
        "f5aec1141a9aba7dda264f18837045f8311d193e",
        "Panoramic landscape",
        "Aert van der Neer",
    ),
    CuratedWork(
        34249308,
        "File:Riviergezicht bij zonsopgang Rijksmuseum SK-A-3330.jpeg",
        "95cf2a6773c9debfbedc204618ffcb6aa4f25d71",
        "River view at sunrise",
        "Aert van der Neer",
    ),
    CuratedWork(
        98844700,
        (
            "File:Aleksander Gierymski - Piazza di Dante in Verona - MNK II-a-833 - Nat"
            "ional Museum Krak\xf3w.jpg"
        ),
        "4ece8d0ddd0a63b1b5e0eb675c7bf7b443a77a01",
        "Piazza di Dante in Verona Piazza di Dante in Verona",
        "Aleksander Gierymski",
    ),
    CuratedWork(
        48912323,
        "File:Waldlandschaft, um 1622.jpg",
        "df01b190b40558e87ef32a23fb8e50c2f00b1ff5",
        "Forest landscape",
        "Alexander Keirincx",
    ),
    CuratedWork(
        140185641,
        (
            "File:Alfred Elsen - Heath Landscape in the Kempen - 1938-J - Museum of Fin"
            "e Arts Ghent (MSK).jpg"
        ),
        "f3d50494a2407aee679c679fc6f0fd9c82ed2020",
        "Heath Landscape in the Kempen",
        "Alfred Elsen",
    ),
    CuratedWork(
        94228640,
        "File:Andries van Eertvelt - River view with boats, a pier and figures.jpg",
        "bb23aea9fbacd61410dc1ff06662936e757e1267",
        "River view with boats, a pier and figures",
        "Andries van Eertvelt",
    ),
    CuratedWork(
        38800278,
        "File:Anton Altmann - Flusslandschaft.jpg",
        "dfeef8e5a6e766406ade26b5470a342174a4da6b",
        "River landscape",
        "Anton Altmann",
    ),
    CuratedWork(
        21926206,
        "File:Antoni Viladomat - Spring - Google Art Project.jpg",
        "94f5be30daa369f331bffc4174a3b207d7c4fd13",
        "Spring",
        "Antoni Viladomat i Manalt",
    ),
    CuratedWork(
        56403724,
        "File:2017-02 Archibald Thorburn - Wigeon and Teal by the water's edge.jpg",
        "61ab52e37855cb66097028f3b0b54258b6e894e7",
        "Wigeon and Teal by the water's edge",
        "Archibald Thorburn",
    ),
    CuratedWork(
        127787179,
        "File:Kopisch, August - Pontine Marshes at Sunset - 3rd version.jpg",
        "8c577ae2e8e046d372ecabefafe5846e950d9955",
        "The Pontine Marshes at Sunset",
        "August Kopisch",
    ),
    CuratedWork(
        22131271,
        (
            "File:Auguste Borget - Moonlit Scene of Indian Figures and Elephants among "
            "Banyan Trees, Upper India (probably Lucknow) - Google Art Project.jpg"
        ),
        "ee87dbc039dd7c68fc4b2cf5664286f7e2b6d582",
        (
            "Moonlit Scene of Indian Figures and Elephants among Banyan Trees, Upper In"
            "dia (probably Lucknow)"
        ),
        "Auguste Borget",
    ),
    CuratedWork(
        95308144,
        (
            "File:Bonaventura Peeters (I) - Entrance to a port with merchant ships and "
            "fishing boats.jpg"
        ),
        "58bb8e3ab612c4a2d60f1a637f706314f714af08",
        "Entrance to a port with merchant ships and fishing boats",
        "Bonaventura Peeters the Elder",
    ),
    CuratedWork(
        87535883,
        (
            "File:The Capture of the 'Marquise d'Antin' and 'Louis Erasme' by the Engli"
            "sh Privateers 'Duke' and 'Prince Frederick', 10 July 1745 RMG BHC0366.jpg"
        ),
        "4b335a990891d4c286c7b00560f5ccf4f7d2c06d",
        (
            "The Capture of the 'Marquise d'Antin' and 'Louis Erasme' by the English Pr"
            "ivateers 'Duke' and 'Prince Frederick', 10 July 1745"
        ),
        "Charles Brooking",
    ),
    CuratedWork(
        97649391,
        "File:Charles william wyllie roi on the way to the festival 102340).jpg",
        "20e346b251f4cd0f7bf264a44cd1a309e7b4e0d1",
        "On the way to the festival",
        "Charles William Wyllie",
    ),
    CuratedWork(
        84982407,
        ("File:Chen Chun - Garden Flowers - 1986.266.1a\u2013u - Metropolitan Museum of Art.jpg"),
        "f494b3bc2964f80321018e1b9704dc5704773338",
        "Garden Flowers",
        "Chen Chun",
    ),
    CuratedWork(
        38742234,
        (
            "File:Worship of the Golden Calf - Claude Gell\xe9e, called Le Lorrain - Go"
            "ogle Cultural Institute.jpg"
        ),
        "235fcb098716401194ef5cacb806ea37b7939ff9",
        ("Die Anbetung des Goldenen Kalbes Landscape with the Adoration of the Golden Calf"),
        "Claude Lorrain",
    ),
    CuratedWork(
        50712491,
        "File:The Enchanted Castle.jpg",
        "755be064f94526a67de78030145b67576b6fbc00",
        "Landscape with Psyche Outside the Palace of Cupid",
        "Claude Lorrain",
    ),
    CuratedWork(
        98555386,
        "File:Conrad wise chapman mexico city110544).jpg",
        "9535cdbf70f94ead5b16f2aecc09d45e0c6e2d3c",
        "Mexico City",
        "Conrad Wise Chapman",
    ),
    CuratedWork(
        82345341,
        ("File:Cornelis van Poelenburch - Psyche Is Carried to the Olympus by Mercury.jpg"),
        "eec50dcc53d5e16f965bf2f2c8f9410669b191cb",
        "Mercury bringing Psyche to Mount Olympus",
        "Cornelius van Poelenburgh",
    ),
    CuratedWork(
        21974819,
        "File:David Roberts - Edinburgh from the Castle - Google Art Project.jpg",
        "2c7ccf02c7a1cc4590e1cc8c50ccf69af67f6fef",
        "Edinburgh from the Castle",
        "David Roberts",
    ),
    CuratedWork(
        47820766,
        "File:Dirck Dalens III - Mountain landscape with shepherds.jpg",
        "1f85437b9ae8aa9b954cf240956be4310b94d01e",
        "Mountain landscape with shepherds",
        "Dirck Dalens III",
    ),
    CuratedWork(
        6352691,
        "File:Eosanderhof des Koeniglichen Schlosses Berlin Gaertner.jpg",
        "75f050a47c9d45d747efe88b20c7aa77c1e37ebf",
        "Eosanderhof des Koeniglichen Schlosses Berlin",
        "Eduard Gaertner",
    ),
    CuratedWork(
        91895724,
        (
            "File:Eduard Gaertner (1801-1877) - The Friedrichsgracht, Berlin - NG6524 -"
            " National Gallery.jpg"
        ),
        "88b87557986942b49bf1c5c28b818c324383c0bd",
        "The Friedrichsgracht, Berlin",
        "Eduard Gaertner",
    ),
    CuratedWork(
        36687919,
        "File:Erasmus Quellinus II - Labore et Constantia.jpg",
        "cef4e70553ce37f6fbd07bfd8e12e935a2b1e551",
        "Labore et constantia",
        "Erasmus Quellinus II",
    ),
    CuratedWork(
        22080926,
        "File:Ercole Calvi - Famiglia pescatore a Lecco sul lago di Como.jpg",
        "34c4783fd2ae9116d257a5d546f5560d83cfed6c",
        "Famiglia pescatore a Lecco sul lago di Como",
        "Ercole Calvi",
    ),
    CuratedWork(
        64222325,
        "File:Ferdinand Bellermann - Badende am Fluss.jpg",
        "891c24feaca06e600012124b899a138f1bcec629",
        "Bathers on the river (evening on the Orinoco?)",
        "Ferdinand Bellermann",
    ),
    CuratedWork(
        99178392,
        "File:Floral Still-life with Roses in a Basket by Florine Hyer.jpg",
        "6802cc037e831651dd3ca3e9c16747eeb77d5e97",
        "Floral Still Life with Roses",
        "Florine Hyer",
    ),
    CuratedWork(
        17486199,
        "File:Casanova Cattle on pasture.jpg",
        "4652aef061e7903861399448724c500032192a68",
        "Cattle on pasture.",
        "Francesco Giuseppe Casanova",
    ),
    CuratedWork(
        22000304,
        "File:Casanova, Francesco Giuseppe - Ferry Boat - Google Art Project.jpg",
        "c2af53e3d5a864fcaa879def5f8ce99f88f5c2e3",
        "Ferry Boat",
        "Francesco Giuseppe Casanova",
    ),
    CuratedWork(
        144713672,
        "File:Franz Bunke - Lastk\xe4hne auf der Warnow.jpg",
        "c69133b7bb34ef4c27af6d4fdb8666460b16c12c",
        "Dinghies at the bank of the Warnow river",
        "Franz Bunke",
    ),
    CuratedWork(
        76004561,
        "File:Clevelandart 1948.181.jpg",
        "984ab51422eaae8ab2824d21c84faae03985f418",
        "Music and Dance and Cupids in Conspiracy",
        "Fran\xe7ois Boucher",
    ),
    CuratedWork(
        67488003,
        (
            "File:Friedrich Carl von Scheidlin - View of St. Johann - K 269 - Slovak Na"
            "tional Gallery.jpg"
        ),
        "ddeccc6960243aa9b7443bdee49cbd30ae600b1f",
        "View of St. Johann",
        "Friedrich Carl von Scheidlin",
    ),
    CuratedWork(
        98111580,
        (
            "File:F\xe9lix Ziem - L'\xe9l\xe9phant - PPP266 - Mus\xe9e des Beaux-Arts d"
            "e la ville de Paris.jpg"
        ),
        "b2cafa5496e96fbcb08eff4741cb61d266f2d3a3",
        "L'\xe9l\xe9phant",
        "F\xe9lix Ziem",
    ),
    CuratedWork(
        74092705,
        (
            "File:Gaspard Dughet - Landscape with a Herdsman and Goats - 1973.669 - Art"
            " Institute of Chicago.jpg"
        ),
        "fd8ea0e051cb62a8645fac387bd066b3134391df",
        "Landscape with a Herdsman and Goats",
        "Gaspard Dughet",
    ),
    CuratedWork(
        22155057,
        (
            "File:George Cuitt - Easby Hall and Easby Abbey with Richmond, Yorkshire in"
            " the Background - Google Art Project.jpg"
        ),
        "f5de85c715d3c9faf76b04ca1ce216ea76588737",
        "Easby Hall and Easby Abbey with Richmond, Yorkshire in the Background",
        "George Cuitt",
    ),
    CuratedWork(
        23600762,
        (
            "File:George Hamilton - The first steeplechase in South Australia, 25 Septe"
            "mber 1846 - Google Art Project.jpg"
        ),
        "7c100fde79adb9a5632c530b4acd82d8c1462616",
        "The first steeplechase in South Australia, 25 September 1846",
        "George Hamilton",
    ),
    CuratedWork(
        56396968,
        "File:2017-02 Georges Washington - The hunt.jpg",
        "a7fdd29b245c7f335c1030bda26e64da2c0f2d33",
        "The hunt",
        "Georges Washington",
    ),
    CuratedWork(
        22007023,
        (
            "File:Canaletto - London- The Thames from Somerset House Terrace towards th"
            "e City - Google Art Project.jpg"
        ),
        "5c7fb2963e9500551af5e4fa1d3e5ee7d820a522",
        "London: The Thames from Somerset House Terrace towards the City",
        "Giovanni Antonio Canal",
    ),
    CuratedWork(
        21997566,
        "File:Canaletto - The Piazza San Marco, Venice - Google Art Project.jpg",
        "d71262bdae51fdfc40245d582359ede24d0479f9",
        "The Piazza San Marco, Venice",
        "Giovanni Antonio Canal",
    ),
    CuratedWork(
        152417,
        "File:Antonio Guardi 030.jpg",
        "c932249a1d0716f1d2068e9317e25a58b82449c0",
        "Tobias fishing with the Archangel Raphael",
        "Giovanni Antonio Guardi",
    ),
    CuratedWork(
        145712376,
        ("File:Madonna and Child with Saints - Giovanni Bellini - Louvre RF 2097 source.jpg"),
        "3600f45b211cbefede4b88694763db6476709c1c",
        "Madonna and Child with Saints",
        "Giovanni Bellini",
    ),
    CuratedWork(
        81323136,
        "File:Giovanni di Paolo, The Adoration of the Magi, c. 1450, NGA 15.jpg",
        "78b4765fd4e217993e894eef9318fc240374c6ee",
        "The Adoration of the Magi",
        "Giovanni di Paolo",
    ),
    CuratedWork(
        64156385,
        "File:Winter landscape near a village, by Hendrick Avercamp.jpg",
        "537700cb4829327934dcb4d3dda303ea44e8e439",
        "Winter Landscape with Skaters near a Village",
        "Hendrick Avercamp",
    ),
    CuratedWork(
        21909482,
        ("File:Hendrick Avercamp - Winter Scene on a Frozen Canal - Google Art Project.jpg"),
        "0b3d6b6499b0d1339bd8f2c3a3b92d6e53b610dc",
        "Winter Scene on a Frozen Canal",
        "Hendrick Avercamp",
    ),
    CuratedWork(
        164566500,
        (
            "File:Hendrik Cornelisz. Vroom (1562-63 - 1640) - Dutch Ships in the Danish"
            " Sound in Front of Kronborg Castle - 2245 - Gem\xe4ldegalerie.jpg"
        ),
        "8145d5a9352747fe68ef126e538fbe8f74586370",
        "Arrival of a Dutch Three master at Schloss Kronberg",
        "Hendrick Cornelisz Vroom",
    ),
    CuratedWork(
        87218467,
        (
            "File:Le Guerre (War) by Henri Rousseau, c. 1894, oil on canvas - The Carni"
            "val of Being (Alfred Jarry at the Morgan) - Morgan Library & Museum - New "
            "York City - DSC06832.jpg"
        ),
        "8e509f5b7566ee6edbbfcbde37244208f5f38bd6",
        (
            "Le Guerre (War) by Henri Rousseau, c. 1894, oil on canvas - The Carnival o"
            "f Being (Alfred Jarry at the Morgan) - Morgan Library & Museum - New York "
            "City - DSC06832"
        ),
        "Henri Rousseau",
    ),
    CuratedWork(
        97326195,
        "File:(hippolyte camille delpy le champ de coquelicot093550).jpg",
        "0ae45dc0604666782584daf1c837dc780b0e01bb",
        "The poppy field",
        "Hippolyte Camille Delpy",
    ),
    CuratedWork(
        82980105,
        "File:Ippolito Caffi, L'eclissi di sole a Venezia dell'8 luglio 1842.jpg",
        "64acb1a74870510954d39cea74345c40499d88bb",
        "Eclips of the Sun in Venice in July 8, 1842",
        "Ippolito Caffi",
    ),
    CuratedWork(
        22213382,
        "File:Joseph Mallord William Turner - Carlisle - Google Art Project.jpg",
        "05085ac79d0d54485e3eeae0da5d26aebaacae6a",
        "Carlisle",
        "J. M. W. Turner",
    ),
    CuratedWork(
        83508719,
        "File:Een Frans eskader bij een rotsachtige kust, SK-A-2674.jpg",
        "7356cd4a01f674cab132df3f2390124fc0f69fde",
        "A French squadron near a rocky coast",
        "Jacob Adriaensz Bellevois",
    ),
    CuratedWork(
        126454056,
        (
            "File:Jacob Gerritsz. Cuyp - Herderin met kind in een landschap - DM-002-79"
            "9 - Dordrechts Museum.jpg"
        ),
        "93e2b9fa6e5b632970a3d3527b85671158298ecb",
        "Herderin met kind in een landschap",
        "Jacob Gerritsz. Cuyp",
    ),
    CuratedWork(
        21793150,
        (
            "File:Jakob Alt - View of Vienna from the Spinner on the Cross, 1817 - Goog"
            "le Art Project.jpg"
        ),
        "366d95dc96735cdd87da26425d1f5aa04a75afd8",
        "View of Vienna from the Spinner on the Cross, 1817",
        "Jakob Alt",
    ),
    CuratedWork(
        21994867,
        (
            "File:James Ward - A Harvest Scene with Workers Loading Hay on to a Farm Wa"
            "gon - Google Art Project.jpg"
        ),
        "cac9c957c9807f5de7583a9a31b509a446285a79",
        "A Harvest Scene with Workers Loading Hay on to a Farm Wagon",
        "James Ward",
    ),
    CuratedWork(
        97342281,
        ("File:John wilson carmichael a blustery day on the brill near rotterdam094806).jpg"),
        "42e0caa80e17fce96a997efae0023729cb716fd9",
        "A blustery day on the Brill, near Rotterdam",
        "James Wilson Carmichael",
    ),
    CuratedWork(
        98812941,
        ("File:Jan Victors - In front of a tavern - M.Ob.2660 - National Museum in Warsaw.jpg"),
        "54323da9885898abf6cb8173dc060f0035f8f0c0",
        "In front of a tavern",
        "Jan Victors",
    ),
    CuratedWork(
        164565576,
        (
            "File:Jan Josephsz van Goyen (1596 - 1656) - Dune Landscape - 865 - Gem\xe4"
            "ldegalerie.jpg"
        ),
        "ce257a6543d5826fe4d056a0b26adb39524334dd",
        "Dunelandscape",
        "Jan van Goyen",
    ),
    CuratedWork(
        162395660,
        (
            "File:La grande odalisque - Jean-Auguste Dominique Ingres - Mus\xe9e du Lou"
            "vre Peintures RF 1158.jpg"
        ),
        "0456a678a0b8cfe38c5b6c4dff348daac63c72bf",
        "Grande Odalisque",
        "Jean-Auguste-Dominique Ingres",
    ),
    CuratedWork(
        15417145,
        "File:Joachim Patinir - St Jerome in the Desert - WGA17100.jpg",
        "8b893dd8bc2cc618ef436f3c3039ffe685584615",
        "Saint Jerome in the Desert",
        "Joachim Patinir",
    ),
    CuratedWork(
        65673517,
        ("File:J. Th. Lundbye, Outside the cowshed, 1847, 0211NMK, Nivaagaards Malerisamling.jpg"),
        "1b58669dbd805ea104ec453ae83c98d8ddf862a5",
        "Outside the cowshed",
        "Johan Lundbye",
    ),
)
