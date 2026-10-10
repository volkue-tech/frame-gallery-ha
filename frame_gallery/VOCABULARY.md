# Filter vocabulary, version 2 (from 0.1.0b6)

This is the vocabulary the app ships (`config/vocabulary.py`, `BUILTIN_VOCABULARY`). It was decided in Q-14 and D-152. A test (`tests/unit/config/test_builtin_vocabulary.py`) keeps this table identical to the code and to the values the adapters send.

**How values are matched.** A static option or a helper state is case-folded, stripped of diacritics, and joined with `_`. The result is then compared with each entry's key, label, and aliases, within one option only. For example, `Prints`, `prints (cleveland)`, and `cma_prints` all select the same department. `any`, `all`, `random`, `none`, and an empty value mean "no filter".

**Source.** Museum values come from official documentation (D-146). Version 2
adds project-defined offline Commons colour families (D-213), not undocumented
museum colour API values. Historical b5 has version 1.

## Departments (`department` option)

Only Cleveland departments are offered. The Art Institute's documentation names its `department_title` field, but not its values. Q-25 is resolved with option (a): none are offered in the first beta.

The label names the museum, so labels stay distinct between museums (D-143). The adapter sends the documented value exactly.

| Key | Label | Aliases | Documented value sent |
| --- | --- | --- | --- |
| `cma_american_painting_sculpture` | American Painting and Sculpture (Cleveland) | American Painting and Sculpture | `department=American Painting and Sculpture` |
| `cma_european_painting_sculpture` | European Painting and Sculpture (Cleveland) | European Painting and Sculpture | `department=European Painting and Sculpture` |
| `cma_modern_european_painting_sculpture` | Modern European Painting and Sculpture (Cleveland) | Modern European Painting and Sculpture | `department=Modern European Painting and Sculpture` |
| `cma_drawings` | Drawings (Cleveland) | Drawings | `department=Drawings` |
| `cma_prints` | Prints (Cleveland) | Prints | `department=Prints` |
| `cma_photography` | Photography (Cleveland) | Photography | `department=Photography` |
| `cma_chinese_art` | Chinese Art (Cleveland) | Chinese Art | `department=Chinese Art` |
| `cma_japanese_art` | Japanese Art (Cleveland) | Japanese Art | `department=Japanese Art` |
| `cma_korean_art` | Korean Art (Cleveland) | Korean Art | `department=Korean Art` |
| `cma_indian_southeast_asian_art` | Indian and South East Asian Art (Cleveland) | Indian and South East Asian Art | `department=Indian and South East Asian Art` |
| `cma_islamic_art` | Islamic Art (Cleveland) | Islamic Art | `department=Islamic Art` |
| `cma_textiles` | Textiles (Cleveland) | Textiles | `department=Textiles` |

Not offered (documented, but mostly objects rather than wall art): African Art; Art of the Americas; Contemporary Art; Decorative Art and Design; Egyptian and Ancient Near Eastern Art; Greek and Roman Art; Medieval Art; and Oceania. "Performing Arts, Music, & Film" is also not offered, because the documentation does not say how a value containing commas is parsed.

## Periods (`style` option)

These are project-defined ranges of a work's earliest creation year, bounds included, and they apply to both museums. They are labelled with years, not style names. The adapters send them as follows:

- **Art Institute:** a `range` on the documented `date_start`, which is also checked on every record.
- **Cleveland:** `created_after` and `created_before`, each widened by one year, with the exact range checked on the documented `creation_date_earliest`.

| Key | Label | Aliases | Earliest year |
| --- | --- | --- | --- |
| `period_before_1400` | Before 1400 | up to 1399 | ≤ 1399 |
| `period_1400_1599` | 1400 to 1599 | 1400-1599; 15th and 16th centuries | 1400–1599 |
| `period_1600_1799` | 1600 to 1799 | 1600-1799; 17th and 18th centuries | 1600–1799 |
| `period_1800_1899` | 1800 to 1899 | 1800-1899; 19th century | 1800–1899 |
| `period_1900_and_later` | 1900 and later | since 1900; 20th century and later | ≥ 1900 |

## Colours (`color` option, Commons only)

Choose one family, or `any` for all colours. A matching family occupies a
noticeable measured area (provisionally >=5%); it need not dominate. Warm ochre
and gold may match yellow. Analysis uses the original preview without added TV
padding. Every family has measured baseline matches, though counts differ.
No-match never substitutes another colour. Full palette/distribution evidence
is retained for future combinations; multiple-colour UI is not offered.
The native configuration list displays the readable labels, such as `Blue`;
internal keys such as `color_blue` and German aliases remain valid helper values.

| Key | Label | Aliases | Local search family |
| --- | --- | --- | --- |
| `color_red` | Red | Rot | red |
| `color_orange` | Orange | — | orange |
| `color_yellow` | Yellow | Gelb | yellow |
| `color_green` | Green | Grün | green |
| `color_blue` | Blue | Blau | blue |
| `color_purple` | Purple | Violet; Violett; Lila | purple |
| `color_pink` | Pink | Rosa | pink |
| `color_brown` | Brown | Braun | brown |
| `color_beige` | Beige | — | beige |
| `color_gray` | Gray | Grey; Grau | gray |
| `color_black` | Black | Schwarz | black |
| `color_white` | White | Weiß | white |

## Styles and museum colours

None in version 1:

- **Styles.** Cleveland documents no style field. The Art Institute documents `style_title`, but not its values.
- **Colours.** The Art Institute documents a dominant-colour object "in HSL", but not its members. Cleveland documents no colour field.

A configured style remains invalid; valid colour choices are applied only to
Commons and visibly reported as unsupported for museum/local sources. Invalid
values (including multiple colours) retain the existing validation/fallback
behaviour. Q-25's original first-beta limitation remains historical; D-213
authorizes the colour implementation; D-217 separately approves b6 publication.

## Capability matrix (beta)

| Filter | Local media | Art Institute of Chicago | Cleveland Museum of Art | Wikimedia Commons |
| --- | --- | --- | --- | --- |
| Department | unsupported | unsupported (values undocumented) | supported | unsupported |
| Style | unsupported | unsupported (values undocumented) | unsupported | unsupported |
| Period | unsupported | supported | supported | unsupported |
| Colour | unsupported | unsupported (members undocumented) | unsupported | supported (offline, pinned) |
