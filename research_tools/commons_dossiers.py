"""Offline curator dossiers: identity/proportion/duplicate flags, not acceptance.

Reads only retained raw public receipts and the inspected thumbnail ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from fractions import Fraction

from research_tools.commons_colours import BASELINE, ROOT, save
from research_tools.commons_expand import OUTPUT
from research_tools.commons_review import source_markup


def normalized(text: str) -> str:
    return re.sub(
        r"[^a-z0-9]",
        "",
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower(),
    )


def qids(markup: str) -> set[str]:
    return set(re.findall(r"wikidata\.org/wiki/(Q[0-9]+)(?:#P1476|[\"'])", markup))


def declared_artwork_qids(wikitext: str) -> set[str]:
    """Read the work's own field, not a nested Creator's Wikidata identity.

    Retained markup is not expanded. Only a literal QID in a top-level field of
    Artwork/Art Photo is evidence; nested sources, examples and maker IDs stay
    out of the artwork-duplicate map. Ambiguous expressions remain unresolved.
    """
    markup = source_markup(wikitext)
    result = set()
    for outer in re.finditer(r"\{\{\s*(?:Artwork|Art Photo)\b", markup, re.I):
        depth, start = 1, outer.end()
        for token in re.finditer(r"\{\{|}}|\|", markup[outer.end() :]):
            end = outer.end() + token.start()
            if depth == 1 and token[0] in ("|", "}}"):
                field = re.fullmatch(
                    r"\s*wikidata\s*=\s*(Q[0-9]+)\s*", markup[start:end], re.I
                )
                if field:
                    result.add(field[1])
                start = end + len(token[0])
            if token[0] == "{{":
                depth += 1
            elif token[0] == "}}":
                depth -= 1
                if depth == 0:
                    break
    return result


def separate_attribution_declaration(text: str) -> bool:
    """Conservative scope prompt, not a determination of copyright subsistence.

    A separately declared self/CC-BY reproduction does not cease to require
    review merely because its description uses Artwork rather than Art Photo.
    Comments and literal examples are not active declarations.
    """
    markup = source_markup(text)
    if re.search(r"\{\{\s*cc-by(?:-sa)?-[0-9]", markup, re.I):
        return True
    # Self may offer multiple positional licences. Inspect each top-level
    # field, not only the first licence or a named author/example value.
    for outer in re.finditer(r"\{\{\s*self\b", markup, re.I):
        depth, start = 1, outer.end()
        for token in re.finditer(r"\{\{|}}|\|", markup[outer.end() :]):
            end = outer.end() + token.start()
            if depth == 1 and token[0] in ("|", "}}"):
                if re.fullmatch(
                    r"\s*cc-by(?:-sa)?-[0-9]+(?:\.[0-9]+)*(?:-[a-z]+)?\s*",
                    markup[start:end],
                    re.I,
                ):
                    return True
                start = end + len(token[0])
            if token[0] == "{{":
                depth += 1
            elif token[0] == "}}":
                depth -= 1
                if depth == 0:
                    break
    return False


def physical(text: str) -> list[dict]:
    result = []

    def two_unlabelled_axes(field: str, match: re.Match) -> bool:
        # A regex can find the last two numbers of a three-axis frame/object
        # measurement. Depth must never become a painting's height. Explicit
        # h/b or w/h axes below are different: their labels retain meaning.
        before, after = field[: match.start()].rstrip(), field[match.end() :].lstrip()
        return not before.endswith(("x", "X", "×")) and not after.startswith(
            ("x", "X", "×")
        )

    for raw in re.findall(
        r"\{\{size\s*\|[^{}]*\}\}", source_markup(text), re.IGNORECASE
    ):
        fields = raw[2:-2].split("|")[1:]
        named = {
            k.strip().lower(): v.strip()
            for field in fields
            if "=" in field
            for k, v in [field.split("=", 1)]
        }
        width, height = named.get("width"), named.get("height")
        meaning = "named height/width"
        if not width or not height:
            axes = [f.strip() for f in fields[1:] if "=" not in f]
            if len(axes) != 2:
                continue
            width, height = axes
            meaning = "unlabelled two axes; landscape orientation observed visually"
        try:
            a, b = float(width.replace(",", ".")), float(height.replace(",", "."))
        except ValueError:
            continue
        if min(a, b) <= 0 or max(a, b) > 100000:
            continue
        if meaning.startswith("unlabelled"):
            a, b = max(a, b), min(a, b)
        result.append(
            dict(raw=raw, width=a, height=b, ratio=a / b, interpretation=meaning)
        )
    # Some museum/GAP receipts expose plain image/sheet measurements instead
    # of {{Size}}. Keep every scope; never pick just the one matching our target.
    markup = source_markup(text)
    # A dimensions field may list Sheet, Plate and Image on separate lines.
    # Preserve all scopes: reading only the first line can hide a different
    # print/image ratio beneath an apparently matching paper-sheet measurement.
    dimensions = re.findall(
        r"\|\s*(?:commons_)?dimensions\s*=(.*?)(?=\n\s*\||\n\s*}}|\Z)",
        markup,
        re.I | re.S,
    )
    dimensions += re.findall(
        r"\|\s*pretty_dimensions\s*=(.*?)(?=\n\s*\||\n\s*}}|\Z)",
        markup,
        re.I | re.S,
    )
    dimensions += re.findall(
        r"\|\s*core:format\s*=(.*?)(?=\n\s*\||\n\s*}}|\Z)",
        markup,
        re.I | re.S,
    )
    dimensions += re.findall(
        r"\|\s*description\s*=(.*?)(?=\n\s*\||\n\s*}}|\Z)", markup, re.I | re.S
    )
    for field in dimensions:
        labelled = field.replace("'''", "").replace("''", "")
        for match in re.finditer(
            r"\bhoogte\s+(?:ca\.\s*)?([0-9]+(?:[.,][0-9]+)?)\s*(cm|mm)\.?"
            r"\s*[x×]\s*breedte\s+(?:ca\.\s*)?([0-9]+(?:[.,][0-9]+)?)"
            r"\s*(cm|mm)\b",
            labelled,
            re.I,
        ):
            height = float(match[1].replace(",", ".")) * (
                10 if match[2].lower() == "cm" else 1
            )
            width = float(match[3].replace(",", ".")) * (
                10 if match[4].lower() == "cm" else 1
            )
            if min(height, width) > 0:
                result.append(
                    dict(
                        raw=field.strip(),
                        width=width,
                        height=height,
                        ratio=width / height,
                        interpretation="explicit Dutch hoogte/breedte axes; "
                        "original support/frame scope retained",
                    )
                )
        # A Dutch museum description can explicitly label dimensions without
        # specifying units. Preserve only the ratio and say that units are
        # unknown; do not infer centimetres or accept arbitrary number pairs.
        for match in re.finditer(
            r"\bAfmetingen:\s*([0-9]+(?:[.,][0-9]+)?)\s*[x×]\s*"
            r"([0-9]+(?:[.,][0-9]+)?)(?![0-9.,])",
            labelled,
            re.I,
        ):
            if not two_unlabelled_axes(labelled, match):
                continue
            following = labelled[match.end() :].lstrip()
            if re.match(r"(?:cm|mm|in\b|inches\b|\")", following, re.I):
                continue
            a, b = float(match[1].replace(",", ".")), float(match[2].replace(",", "."))
            if min(a, b) > 0:
                result.append(
                    dict(
                        raw=field.strip(),
                        width=max(a, b),
                        height=min(a, b),
                        ratio=max(a, b) / min(a, b),
                        interpretation="explicit Afmetingen pair; units unspecified; "
                        "scope retained, landscape observed visually",
                    )
                )
        for match in re.finditer(
            r"\bHeight:\s*\{\{size\s*\|\s*(cm|mm)\s*\|\s*"
            r"([0-9]+(?:[.,][0-9]+)?)\s*}}\s*(?:drager\s+)?"
            r"Width:\s*\{\{size\s*\|\s*(cm|mm)\s*\|\s*"
            r"([0-9]+(?:[.,][0-9]+)?)\s*}}",
            labelled,
            re.I,
        ):
            height = float(match[2].replace(",", ".")) * (
                10 if match[1].lower() == "cm" else 1
            )
            width = float(match[4].replace(",", ".")) * (
                10 if match[3].lower() == "cm" else 1
            )
            if min(height, width) > 0:
                result.append(
                    dict(
                        raw=field.strip(),
                        width=width,
                        height=height,
                        ratio=width / height,
                        interpretation="explicit Height/Width single-axis Size "
                        "templates; measurement scope retained",
                    )
                )
        # Size templates were read above. Remove just those tokens, not the
        # entire field: a later plain Sheet/Plate/Frame line still matters.
        field = re.sub(r"\{\{size\s*\|[^{}]*\}\}", "", field, flags=re.I)
        # Auction sources also use mixed-number inches. Ignoring these would
        # let a wide file hide a substantially different original proportion.
        inch_number = r"[0-9]+(?:[.,][0-9]+|\s+[0-9]+/[0-9]+|\s*[¼½¾⅛⅜⅝⅞])?"
        for match in re.finditer(
            rf"({inch_number})\s*[x×]\s*({inch_number})\s*(?:in\.?|inches|\")",
            field,
            re.I,
        ):
            if not two_unlabelled_axes(field, match):
                continue

            def inches(value: str) -> float:
                fractions = dict(
                    zip("¼½¾⅛⅜⅝⅞", (0.25, 0.5, 0.75, 0.125, 0.375, 0.625, 0.875))
                )
                value = value.strip()
                if value[-1] in fractions:
                    return float(value[:-1].strip()) + fractions[value[-1]]
                if "/" in value:
                    whole, part = value.split()
                    return float(whole) + float(Fraction(part))
                return float(value.replace(",", "."))

            try:
                a, b = inches(match[1]), inches(match[2])
            except (ValueError, ZeroDivisionError):
                continue
            if min(a, b) > 0:
                result.append(
                    dict(
                        raw=field.strip(),
                        width=max(a, b),
                        height=min(a, b),
                        ratio=max(a, b) / min(a, b),
                        interpretation="plain two axes in inches; "
                        "original measurement scope retained",
                    )
                )
        # Rijksmuseum's retained source description labels h/b explicitly and
        # often repeats units: "h 138 mm × b 254 mm". Keep axes and all scopes;
        # a support/frame measurement is not silently treated as the image.
        for match in re.finditer(
            r"\bh\s+([0-9]+(?:[.,][0-9]+)?)\s*(cm|mm)\.?\s*[x×]\s*"
            r"b\s+([0-9]+(?:[.,][0-9]+)?)\s*(cm|mm)\b",
            field,
            re.I,
        ):
            height = float(match[1].replace(",", ".")) * (
                10 if match[2].lower() == "cm" else 1
            )
            width = float(match[3].replace(",", ".")) * (
                10 if match[4].lower() == "cm" else 1
            )
            if min(height, width) > 0:
                result.append(
                    dict(
                        raw=field.strip(),
                        width=width,
                        height=height,
                        ratio=width / height,
                        interpretation="explicit Dutch h/b axes; "
                        "all measurement scopes retained",
                    )
                )
        for match in re.finditer(
            r"\b(?:H|Height)\.?\s+([^;|\n]+)(?:;\s*|\n\s*)"
            r"(?:W|Width)\.?\s+([^;|\n]+)",
            field,
            re.I,
        ):
            # Museum descriptions often put inches first and metric values
            # in parentheses. Read each explicitly labelled metric axis,
            # rather than silently losing the original-work dimensions.
            axes = [
                re.findall(r"([0-9]+(?:[.,][0-9]+)?)\s*(cm|mm)\b", part, re.I)
                for part in match.groups()
            ]
            if any(len(axis) != 1 for axis in axes):
                continue
            height, width = (
                float(axis[0][0].replace(",", "."))
                * (10 if axis[0][1].lower() == "cm" else 1)
                for axis in axes
            )
            if min(height, width) > 0:
                result.append(
                    dict(
                        raw=field.strip(),
                        width=width,
                        height=height,
                        ratio=width / height,
                        interpretation="explicit English H/W metric axes; "
                        "all measurement scopes retained",
                    )
                )
        for match in re.finditer(
            r"\bH\s+([0-9]+(?:[.,][0-9]+)?)\s*;\s*B\s+"
            r"([0-9]+(?:[.,][0-9]+)?)\s*(cm|mm)\b",
            field,
        ):
            height, width = (
                float(match[1].replace(",", ".")),
                float(match[2].replace(",", ".")),
            )
            if min(height, width) > 0:
                result.append(
                    dict(
                        raw=field.strip(),
                        width=width,
                        height=height,
                        ratio=width / height,
                        interpretation="explicit H/B axes with shared unit",
                    )
                )
        for match in re.finditer(
            r"([0-9]+(?:[.,][0-9]+)?)\s*(cm|mm)\s*[x×]\s*"
            r"([0-9]+(?:[.,][0-9]+)?)\s*(cm|mm)\b",
            field,
            re.I,
        ):
            if not two_unlabelled_axes(field, match):
                continue
            a = float(match[1].replace(",", ".")) * (
                10 if match[2].lower() == "cm" else 1
            )
            b = float(match[3].replace(",", ".")) * (
                10 if match[4].lower() == "cm" else 1
            )
            if min(a, b) > 0:
                result.append(
                    dict(
                        raw=field.strip(),
                        width=max(a, b),
                        height=min(a, b),
                        ratio=max(a, b) / min(a, b),
                        interpretation="plain two axes with repeated units; "
                        "all scopes retained",
                    )
                )
        for match in re.finditer(
            r"([0-9]+(?:[.,][0-9]+)?)\s*[x×]\s*([0-9]+(?:[.,][0-9]+)?)\s*(cm|mm)\b",
            field,
            re.I,
        ):
            if not two_unlabelled_axes(field, match):
                continue
            a, b = float(match[1].replace(",", ".")), float(match[2].replace(",", "."))
            if min(a, b) > 0:
                result.append(
                    dict(
                        raw=field.strip(),
                        width=max(a, b),
                        height=min(a, b),
                        ratio=max(a, b) / min(a, b),
                        interpretation="plain two axes; measurement scope retained, "
                        "landscape observed visually",
                    )
                )
        match = re.search(
            r"w([0-9]+(?:[.,][0-9]+)?)\s*[x×]\s*h([0-9]+(?:[.,][0-9]+)?)\s*(cm|mm)\b",
            field,
            re.I,
        )
        if match:
            a, b = float(match[1].replace(",", ".")), float(match[2].replace(",", "."))
            if min(a, b) > 0:
                result.append(
                    dict(
                        raw=field.strip(),
                        width=a,
                        height=b,
                        ratio=a / b,
                        interpretation="explicit w/h plain dimensions",
                    )
                )
    return result


def scoped_measures(
    work: dict, profile: dict, measures: list[dict], decision: dict
) -> list[dict]:
    """One explicit source-bound subject measurement, not a global exemption.

    The original measurement remains in the dossier. This changes only the
    original-image ratio comparison, never rights, identity or visual flags.
    """
    expected = {
        "id": work["id"],
        "original_sha1": work["sha1"],
        "source_revision": work["source_revision"],
        "source_page_sha256": work["source_page_sha256"],
        "thumbnail_sha256": profile["thumbnail_sha256"],
        "measurements_sha256": hashlib.sha256(
            json.dumps(measures, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
    }
    indices = decision.get("excluded_measurement_indices")
    if (
        any(decision.get(k) != v for k, v in expected.items())
        or decision.get("scope") != "photographed subject, not photographic composition"
        or not isinstance(indices, list)
        or not indices
        or any(type(i) is not int or not 0 <= i < len(measures) for i in indices)
        or len(set(indices)) != len(indices)
        or any(
            not isinstance(decision.get(k), str) or not decision[k].strip()
            for k in ("reason", "limits")
        )
    ):
        raise ValueError("explicit source/preview-bound measurement scope required")
    return [m for i, m in enumerate(measures) if i not in indices]


def dossiers() -> None:
    scope_path = ROOT / "research/commons-photo-measurement-scopes-2026-10-10.json"
    scope_rows = (
        json.loads(scope_path.read_text())["records"] if scope_path.exists() else []
    )
    scopes = {r["id"]: r for r in scope_rows}
    if len(scopes) != len(scope_rows):
        raise ValueError("unique explicit measurement-scope decisions required")
    manual_path = ROOT / "research/commons-curator-deferrals-2026-10-09.json"
    manual = (
        {r["id"]: r["reason"] for r in json.loads(manual_path.read_text())["records"]}
        if manual_path.exists()
        else {}
    )
    baseline = json.loads(BASELINE.read_text())["included"]
    baseline_by_id = {w["id"]: w for w in baseline}
    baseline_qids = {}
    identity_files = list((ROOT / "build/commons-colours").glob("metadata-*.json"))
    identity_files.extend(OUTPUT.glob("baseline-identity-*.json"))
    for file in identity_files:
        for page in json.loads(file.read_text()).get("query", {}).get("pages", []):
            if page.get("pageid") not in baseline_by_id:
                continue
            for info in page.get("imageinfo", []):
                raw = info.get("extmetadata", {}).get("ObjectName", {}).get("value", "")
                for q in qids(raw):
                    baseline_qids[q] = page["pageid"]
            for revision in page.get("revisions", []):
                text = revision.get("slots", {}).get("main", {}).get("content", "")
                for q in declared_artwork_qids(text):
                    baseline_qids[q] = page["pageid"]
    profiles = {
        w["id"]: w
        for w in json.loads((OUTPUT / "profiles.json").read_text())["profiles"]
    }
    metadata = {
        w["id"]: w for w in json.loads((OUTPUT / "review.json").read_text())["records"]
    }
    prompts = json.loads((OUTPUT / "duplicate-prompts.json").read_text())["prompts"]
    seen_qids = dict(baseline_qids)
    seen_labels = {normalized(w["artist"] + w["title"]): w["id"] for w in baseline}
    rows = []
    screens = []
    for file in sorted(OUTPUT.glob("visual-screen-*.json")):
        screens.extend(json.loads(file.read_text())["records"])
    for screen in screens:
        if screen["screen"] != "visual first-pass":
            continue
        work = metadata[screen["id"]]
        profile = profiles[work["id"]]
        evidence = OUTPUT / work["evidence_file"]
        if hashlib.sha256(evidence.read_bytes()).hexdigest() != work["evidence_sha256"]:
            raise ValueError("source receipt changed")
        page = next(
            p
            for p in json.loads(evidence.read_text())["query"]["pages"]
            if p["pageid"] == work["id"]
        )
        text = page["revisions"][0]["slots"]["main"]["content"]
        raw_name = (
            page["imageinfo"][0]
            .get("extmetadata", {})
            .get("ObjectName", {})
            .get("value", "")
        )
        item_qids = qids(raw_name) | declared_artwork_qids(text)
        measures = physical(text)
        compared_measures = (
            scoped_measures(work, profile, measures, scopes[work["id"]])
            if work["id"] in scopes
            else measures
        )
        ratio = work["width"] / work["height"]
        flags = list(work["reasons"])
        if work["id"] in manual:
            flags.append("manual curator deferral: " + manual[work["id"]])
        # A marked frame's additional dimensions need manual scope resolution;
        # don't silently choose whichever measurements fit our desired ratio.
        if compared_measures and any(
            abs(m["ratio"] / ratio - 1) > 0.025 for m in compared_measures
        ):
            flags.append(
                "physical dimensions contradict file shape; "
                "cropping/distortion unresolved"
            )
        if any(abs(m["ratio"] / (16 / 9) - 1) > 0.025 for m in compared_measures):
            flags.append(
                "recorded physical proportions outside requested 2.5% band; "
                "measurement scope/crop unresolved"
            )
        if separate_attribution_declaration(text):
            flags.append(
                "Source declares attribution/share-alike reproduction rights; "
                "PD/CC0-only licence scope unresolved"
            )
        size = profile.get("oriented_dimensions")
        if not size or abs(size[0] / size[1] / (16 / 9) - 1) > 0.025:
            flags.append("oriented thumbnail is not near widescreen")
        comparisons = [p for p in prompts if p["candidate"] == work["id"]]
        if comparisons:
            flags.append("fingerprint artwork-identity comparison required")
        matches = {seen_qids[q] for q in item_qids if q in seen_qids}
        label = normalized(work["artist"] + work["title"])
        if label and label in seen_labels:
            matches.add(seen_labels[label])
        if matches:
            flags.append("artwork identity/label already represented; review required")
        for q in item_qids:
            seen_qids.setdefault(q, work["id"])
        seen_labels.setdefault(label, work["id"])
        rows.append(
            dict(
                id=work["id"],
                position=screen["contact_sheet_position"],
                title=work["title"],
                artist=work["artist"],
                file_title=work["file_title"],
                source=work["source"],
                original_sha1=work["sha1"],
                file_ratio=ratio,
                physical_measures=measures,
                compared_physical_measures=compared_measures,
                measurement_scope_resolution=scopes.get(work["id"]),
                artwork_qids=sorted(item_qids),
                identity_matches=sorted(matches),
                fingerprint_comparisons=comparisons,
                flags=flags,
                source_revision=work["source_revision"],
                source_page_sha256=work["source_page_sha256"],
                evidence_file=work["evidence_file"],
                evidence_sha256=work["evidence_sha256"],
                thumbnail_sha256=profile["thumbnail_sha256"],
                visual_screen=screen,
                rights_basis=work["us_basis_declarations"],
                rights_label=work["rights_label"],
                status="curator dossier only; NOT accepted",
            )
        )
    save(
        OUTPUT / "curator-dossiers.json",
        dict(schema=1, status="not acceptance", records=rows),
    )
    print(
        json.dumps(
            dict(
                dossiers=len(rows),
                no_flags=sum(not r["flags"] for r in rows),
                baseline_artwork_qids=len(baseline_qids),
            )
        )
    )


def sheets(reserve: bool = False) -> None:
    """Render only unresolved low-flag dossiers for a second human inspection."""
    from PIL import Image, ImageDraw, ImageOps

    rows = json.loads((OUTPUT / "curator-dossiers.json").read_text())["records"]
    prior = list(OUTPUT.glob("curator-sheet-*.json"))
    rendered = {
        row["id"] for path in prior for row in json.loads(path.read_text())["records"]
    }
    if reserve:
        accepted_path = (
            ROOT / "frame_gallery/research/commons-expansion-curation-2026-10-09.json"
        )
        selected = {r["id"] for r in json.loads(accepted_path.read_text())["included"]}
        rows = [row for row in rows if row["id"] not in selected]
        rendered = set()
    first = max((int(p.stem.rsplit("-", 1)[1]) for p in prior), default=-1) + 1
    rows = [row for row in rows if not row["flags"] and row["id"] not in rendered]
    for offset in range(0, len(rows), 12):
        batch = rows[offset : offset + 12]
        sheet = Image.new("RGB", (1200, 1160), "#eeeeee")
        draw = ImageDraw.Draw(sheet)
        for position, row in enumerate(batch):
            x, y = position % 3 * 400, position // 3 * 290
            path = OUTPUT / f"{row['id']}.jpg"
            if hashlib.sha256(path.read_bytes()).hexdigest() != row["thumbnail_sha256"]:
                raise ValueError("curator preview changed")
            with Image.open(path) as opened:
                image = ImageOps.exif_transpose(opened).convert("RGB")
                image.thumbnail((390, 230))
                sheet.paste(image, (x + 5, y + 5))
            draw.text(
                (x + 5, y + 237), f"{offset + position}: {row['id']}", fill="black"
            )
            draw.text((x + 5, y + 252), row["artist"][:53], fill="black")
            draw.text((x + 5, y + 267), row["title"][:53], fill="black")
        path = OUTPUT / f"curator-sheet-{first + offset // 12:03}.jpg"
        sheet.save(path, quality=94)
        save(
            path.with_suffix(".json"),
            dict(records=batch, sha256=hashlib.sha256(path.read_bytes()).hexdigest()),
        )
    print(json.dumps(dict(second_review_dossiers=len(rows))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=("dossiers", "sheets"), default="dossiers", nargs="?"
    )
    args = parser.parse_args()
    dossiers() if args.mode == "dossiers" else sheets()
