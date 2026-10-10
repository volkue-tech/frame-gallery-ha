"""Local, resumable colour research only; never imported or shipped by the app.

Fetch uses the existing public-HTTPS gateway and reviewed catalogue pins. Image
decoding runs in a time-bounded child with no inherited credentials. Research
JPEGs and review pages live below ignored build/, not in the release payload.
"""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import html
import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "frame_gallery/research/commons-400-selection-2026-10-06.json"
OUTPUT = ROOT / "build/commons-colours"
METHOD = "commons-colours-pilot-v2"
GROUPS = (
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "purple",
    "pink",
    "brown",
    "beige",
    "gray",
    "black",
    "white",
)
LABELS = dict(
    zip(
        GROUPS,
        (
            "Rot",
            "Orange",
            "Gelb",
            "Grün",
            "Blau",
            "Violett",
            "Rosa",
            "Braun",
            "Beige",
            "Grau",
            "Schwarz",
            "Weiß",
        ),
    )
)
MIN_SHARE = 0.05
MAX_BYTES = 2 * 1024 * 1024
MAX_AXIS = 1024


def group(rgb: tuple[int, int, int]) -> str:
    """Provisional human colour buckets; keep the full palette for recalibration."""
    r, g, b = (v / 255 for v in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h *= 360
    # Perceptual lightness, rather than a bright channel masking darkness.
    linear = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in (r, g, b)]
    y = sum(x * w for x, w in zip(linear, (0.2126, 0.7152, 0.0722)))
    light = 116 * (y ** (1 / 3) if y > 216 / 24389 else y * 24389 / 27 / 116 + 16 / 116) - 16
    if light < 16 and (s < 0.45 or v < 0.22):
        return "black"
    if s < 0.085:
        return "white" if light >= 84 else "gray"
    if 12 <= h < 65:
        if (light >= 65 and s < 0.22) or (light >= 72 and s < 0.35):
            return "beige"
        if (light < 42 or (light < 55 and h < 32)) and v < 0.78:
            return "brown"
    if h < 12 or h >= 345:
        return "pink" if light >= 65 and s < 0.6 else "red"
    if h < 34:
        return "orange"
    if h < 70:
        return "yellow"
    if h < 170:
        return "green"
    if h < 265:
        return "blue"
    if h < 315:
        return "purple"
    return "pink" if light >= 58 else "purple"


def aggregate(palette: list[tuple[int, tuple[int, int, int]]]) -> dict:
    """Count distinct colour families; no invented second/third monochrome colour."""
    total = sum(count for count, _ in palette)
    if total <= 0 or any(count <= 0 for count, _ in palette):
        raise ValueError("empty or invalid palette")
    counts = dict.fromkeys(GROUPS, 0)
    representatives = {}
    for count, rgb in sorted(palette, key=lambda item: (-item[0], item[1])):
        key = group(rgb)
        counts[key] += count
        representatives.setdefault(key, "#" + "".join(f"{v:02x}" for v in rgb))
    distribution = [
        dict(
            group=key,
            pixels=counts[key],
            share=counts[key] / total,
            representative=representatives.get(key),
        )
        for key in GROUPS
    ]
    meaningful = sorted(
        (item for item in distribution if item["share"] >= MIN_SHARE),
        key=lambda item: (-item["pixels"], GROUPS.index(item["group"])),
    )
    return dict(
        sample_pixels=total,
        distribution=distribution,
        top_colours=meaningful[:3],
        top_chromatic_colours=[
            item for item in meaningful if item["group"] not in ("black", "white", "gray")
        ][:3],
        search_colours=[item["group"] for item in meaningful],
        palette=[
            dict(pixels=count, rgb=list(rgb), group=group(rgb))
            for count, rgb in sorted(palette, key=lambda item: (-item[0], item[1]))
        ],
    )


def analyse(path: Path) -> dict:
    """Child-only decoding: bounded JPEG, actual dimensions and colour-space record."""
    import io
    import resource

    from PIL import Image, ImageCms, ImageOps

    sys.path.insert(0, str(ROOT / "frame_gallery/src"))
    from frame_gallery.imaging.source_scan import scan_source

    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    if sys.platform == "linux":
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)
    Image.MAX_IMAGE_PIXELS = MAX_AXIS * MAX_AXIS
    with path.open("rb") as source:
        data = source.read(MAX_BYTES + 1)
    if not 0 < len(data) <= MAX_BYTES or not data.startswith(b"\xff\xd8"):
        raise ValueError("thumbnail byte bound")
    scan_source(io.BytesIO(data))
    with Image.open(io.BytesIO(data)) as opened:
        if opened.format != "JPEG" or max(opened.size) > MAX_AXIS or min(opened.size) < 1:
            raise ValueError("thumbnail format/dimension bound")
        original_size = list(opened.size)
        orientation = opened.getexif().get(274, 1)
        image = ImageOps.exif_transpose(opened)
        oriented_size = list(image.size)
        icc = image.info.get("icc_profile")
        if icc:
            if len(icc) > 256 * 1024:
                raise ValueError("ICC byte bound")
            image = ImageCms.profileToProfile(
                image,
                ImageCms.ImageCmsProfile(io.BytesIO(icc)),
                ImageCms.createProfile("sRGB"),
                outputMode="RGB",
            )
            colour_space = "ICC converted to sRGB"
        else:
            if image.mode not in ("RGB", "L"):
                raise ValueError("unprofiled non-RGB thumbnail")
            image = image.convert("RGB")
            colour_space = "untagged JPEG assumed sRGB"
        # No border trimming, crop, TV padding or removal of neutral composition.
        image.thumbnail((256, 256), Image.Resampling.LANCZOS)
        fingerprint_image = image.convert("L").resize((17, 16), Image.Resampling.LANCZOS)
        samples = list(fingerprint_image.getdata())
        fingerprint = 0
        for y in range(16):
            for x in range(16):
                fingerprint = (fingerprint << 1) | int(
                    samples[y * 17 + x] > samples[y * 17 + x + 1]
                )
        quantized = image.quantize(
            colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE
        )
        rgb_palette = quantized.getpalette()
        palette = [
            (count, tuple(rgb_palette[index * 3 : index * 3 + 3]))
            for count, index in quantized.getcolors()
        ]
        result = aggregate(palette)
        result.update(
            method=METHOD,
            dimensions=original_size,
            oriented_dimensions=oriented_size,
            exif_orientation=orientation,
            sample_dimensions=list(image.size),
            thumbnail_sha256=hashlib.sha256(data).hexdigest(),
            bytes=len(data),
            colour_space=colour_space,
            pillow_version=Image.__version__,
            minimum_search_share=MIN_SHARE,
            palette_size=128,
            review_dhash256=f"{fingerprint:064x}",
        )
        return result


def run_worker(path: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "worker", str(path)],
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        capture_output=True,
        timeout=15,
        check=False,
    )
    if result.returncode or len(result.stdout) > 64 * 1024:
        raise ValueError("colour worker failed or exceeded output bound")
    return json.loads(result.stdout)


def save(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".pending")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def selection(works: list[dict], count: int) -> list[dict]:
    """First modern works plus evenly-spaced catalogue, duplicate IDs removed."""
    chosen = works[: min(16, count)]
    for index in range(count * 2):
        item = works[round(index * (len(works) - 1) / max(1, count * 2 - 1))]
        if item["id"] not in {w["id"] for w in chosen}:
            chosen.append(item)
        if len(chosen) == count:
            break
    return chosen


def fetch(count: int) -> None:
    """Explicit user-approved public thumbnail research; no keys or local systems."""
    sys.path.insert(0, str(ROOT / "frame_gallery/src"))
    from frame_gallery.budget.allowance import Allowance
    from frame_gallery.budget.clock import SystemClock
    from frame_gallery.budget.deadline import Deadline
    from frame_gallery.net.gateway import Gateway
    from frame_gallery.net.identity import commons_identity
    from frame_gallery.net.policy import RequestKind, https_url
    from frame_gallery.net.transport import SystemResolver, Urllib3Transport
    from frame_gallery.providers.commons import RIGHTS_FIELDS, _rights, commons_policy
    from frame_gallery.randomness import SeededRandomSource

    if not 1 <= count <= 400:
        raise ValueError("research count bound")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    works = selection(json.loads(BASELINE.read_text())["included"], count)
    report_path = OUTPUT / "pilot.json"
    report = (
        json.loads(report_path.read_text())
        if report_path.exists()
        else dict(
            schema=1,
            purpose="private colour pilot, not release-approved",
            baseline_sha256=hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
            method=METHOD,
            profiles=[],
            refused=[],
        )
    )
    if report["baseline_sha256"] != hashlib.sha256(BASELINE.read_bytes()).hexdigest():
        raise ValueError("baseline changed")
    if report["method"] != METHOD:
        raise ValueError("recalibrate existing evidence before continuing")
    clock = SystemClock()
    gateway = Gateway(
        resolver=SystemResolver(),
        transport=Urllib3Transport(),
        clock=clock,
        random=SeededRandomSource(20261009),
        identity=commons_identity(),
    )
    channel = gateway.channel(commons_policy(), metadata_allowance=Allowance("pilot metadata", 90))
    deadline = Deadline.after(clock, 900, "private colour pilot")
    remaining = [w for w in works if w["id"] not in {p["id"] for p in report["profiles"]}]
    for offset in range(0, len(remaining), 5):
        batch = remaining[offset : offset + 5]
        query = (
            ("action", "query"),
            ("format", "json"),
            ("formatversion", "2"),
            ("prop", "imageinfo"),
            ("pageids", "|".join(str(w["id"]) for w in batch)),
            ("iiprop", "size|mime|sha1|url|extmetadata|thumbmime"),
            ("iilimit", "1"),
            ("iiurlwidth", "512"),
            ("iiextmetadatafilter", RIGHTS_FIELDS),
            ("maxlag", "5"),
        )
        document = channel.get_json(
            https_url("commons.wikimedia.org", "/w/api.php", query), deadline
        )
        if not isinstance(document, dict) or "warnings" in document or "error" in document:
            raise ValueError("metadata refused")
        pages = {page["pageid"]: page for page in document["query"]["pages"]}
        save(OUTPUT / f"metadata-{batch[0]['id']}.json", document)
        for work in batch:
            page = pages.get(work["id"], {})
            infos = page.get("imageinfo", [])
            info = infos[0] if len(infos) == 1 else {}
            if (
                page.get("title") != work["file_title"]
                or page.get("ns") != 6
                or page.get("imagerepository") != "local"
                or info.get("sha1") != work["sha1"]
                or _rights(info.get("extmetadata")) is None
                or info.get("mime") != "image/jpeg"
                or info.get("thumbmime") != "image/jpeg"
                or not 0 < info.get("thumbwidth", 0) <= MAX_AXIS
                or not 0 < info.get("thumbheight", 0) <= MAX_AXIS
            ):
                report["refused"].append(
                    dict(id=work["id"], reason="metadata/pin/rights/rendition")
                )
                save(report_path, report)
                continue
            url = info.get("thumburl", "")
            from frame_gallery.providers.commons import _image_url

            if _image_url(url, channel.policy) is None:
                raise ValueError("thumbnail host/path refused")
            path = OUTPUT / f"{work['id']}.jpg"

            # Same DNS/TLS/redirect/pacing rules, but a stricter research byte sink.
            class Sink:
                def __init__(self) -> None:
                    self.data = bytearray()

                def write(self, data: bytes) -> None:
                    if len(self.data) + len(data) > MAX_BYTES:
                        raise ValueError("thumbnail research byte bound")
                    self.data.extend(data)

            sink = Sink()
            channel._request(url, RequestKind.IMAGE, deadline, sink)
            path.write_bytes(sink.data)
            profile = run_worker(path)
            reported = [info["thumbwidth"], info["thumbheight"]]
            # Commons may serve a standard rendition larger than iiurlwidth;
            # the child verified the actual JPEG against the independent cap.
            actual = profile["dimensions"]
            if abs(actual[0] / actual[1] / (reported[0] / reported[1]) - 1) > 0.015:
                raise ValueError("actual thumbnail shape disagrees")
            profile["reported_thumbnail_dimensions"] = reported
            profile["rendition_dimensions_differ"] = actual != reported
            profile.update(
                id=work["id"],
                title=work["title"],
                artist=work["artist"],
                file_title=work["file_title"],
                original_sha1=work["sha1"],
                source=work["source"],
                thumbnail_url=url,
                rights=info["extmetadata"],
                analysed_at=clock.utc_now().isoformat(),
            )
            report["profiles"].append(profile)
            save(report_path, report)
            print(
                json.dumps(
                    dict(
                        id=work["id"],
                        completed=len(report["profiles"]),
                        top=[p["group"] for p in profile["top_colours"]],
                    )
                )
            )
    report["metadata_requests_last_pass"] = channel.metadata_requests
    report["updated_at"] = datetime.now(UTC).isoformat()
    save(report_path, report)


def gallery() -> None:
    report = json.loads((OUTPUT / "pilot.json").read_text())
    profiles = [dict(p, gallery_kind="baseline") for p in report["profiles"]]
    additions_path = ROOT / "frame_gallery/research/commons-expansion-curation-2026-10-09.json"
    if additions_path.exists():
        from research_tools.commons_expand import OUTPUT as candidate_output

        additions = json.loads(additions_path.read_text())
        if additions["baseline_sha256"] != hashlib.sha256(BASELINE.read_bytes()).hexdigest():
            raise ValueError("preview baseline changed")
        candidates = {
            p["id"]: p
            for p in json.loads((candidate_output / "profiles.json").read_text())["profiles"]
        }
        selected = []
        for work in additions["included"]:
            p = candidates[work["id"]]
            path = candidate_output / f"{work['id']}.jpg"
            if (
                p["original_sha1"] != work["sha1"]
                or p["thumbnail_sha256"] != work["thumbnail_sha256"]
                or hashlib.sha256(path.read_bytes()).hexdigest() != p["thumbnail_sha256"]
                or p["method"] != METHOD
            ):
                raise ValueError("accepted preview pin/profile changed")
            shutil.copyfile(path, OUTPUT / path.name)
            selected.append(dict(p, gallery_kind="new"))
        save(
            ROOT / "frame_gallery/research/commons-expansion-colours-2026-10-09.json",
            dict(
                schema=1,
                method=METHOD,
                status="partial accepted research only; NOT release-approved",
                curation_sha256=hashlib.sha256(additions_path.read_bytes()).hexdigest(),
                count=len(selected),
                profiles=selected,
            ),
        )
        modern = ("klee", "vuillard", "cézanne", "simberg", "renoir")
        selected.sort(
            key=lambda p: (
                not any(name in p["artist"].lower() for name in modern),
                p["id"],
            )
        )
        profiles = selected + profiles
    selection_path = ROOT / "frame_gallery/research/commons-1000-selection-2026-10-10.json"
    active, held, reserves = set(), set(), set()
    if selection_path.exists():
        selection = json.loads(selection_path.read_text())
        active = {w["id"] for w in selection["included"]}
        held = set(selection["held_ids"])
        reserves = {w["id"] for w in selection["reserve"]}
        if (
            len(active) != 1000
            or len(held) != 56
            or len(reserves) != 7
            or active & held
            or active & reserves
            or held & reserves
            or active | held | reserves != {p["id"] for p in profiles}
        ):
            raise ValueError("preview selection partition changed")
    cards = []
    for profile in profiles:
        status = (
            "held"
            if profile["id"] in held
            else "reserve"
            if profile["id"] in reserves
            else "active"
        )
        chips = " ".join(
            f'<span><i style="background:{colour["representative"]}"></i>'
            f"{LABELS[colour['group']]} {colour['share']:.0%}</span>"
            for colour in profile["top_colours"]
        )
        cards.append(
            '<article data-colours="'
            f'{html.escape(" ".join(profile["search_colours"]))}" '
            f'data-kind="{profile["gallery_kind"]}" data-status="{status}">'
            f'<img src="{profile["id"]}.jpg" loading="lazy" '
            f'alt="{html.escape(profile["title"])}"><h2>{html.escape(profile["title"])}</h2>'
            f'<p>{html.escape(profile["artist"])}</p><div class="chips">{chips}</div>'
            + (
                "<p>Vorläufig zurückgestellt · nicht in der Zufallsauswahl</p>"
                if status == "held"
                else "<p>Geprüfte Reserve · nicht in der Zufallsauswahl</p>"
                if status == "reserve"
                else ""
            )
            + (
                "<p>Neu kuratiert · noch nicht veröffentlicht</p>"
                if profile["gallery_kind"] == "new"
                else ""
            )
            + "<details><summary>Alle Farbanteile</summary><p>"
            + " · ".join(
                f"{LABELS[c['group']]} {c['share']:.1%}"
                for c in profile["distribution"]
                if c["pixels"]
            )
            + "</p></details>"
            + f'<p><a href="{html.escape(profile["source"])}">'
            "Commons-Quelle</a></p></article>"
        )
    choices = "".join(f'<option value="{key}">{LABELS[key]}</option>' for key in GROUPS)
    markup = (
        '<!doctype html><html lang="de"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Frame Gallery · Farbpilot</title><style>"
        ":root{color-scheme:light dark;font-family:system-ui;"
        "background:light-dark(#fafafa,#101317);color:light-dark(#17202a,#eef2f6)}"
        "body{max-width:1200px;margin:24px auto;padding:0 16px}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:28px}"
        "img{width:100%;aspect-ratio:16/9;object-fit:contain;background:#181818}"
        "h2{font-size:16px;margin-bottom:4px}p{margin:6px 0}"
        "i{display:inline-block;width:15px;"
        "height:15px;border-radius:50%;margin-right:5px}.chips{display:flex;gap:12px;flex-wrap:wrap}"
        "select{padding:10px;margin:12px 0 24px;font:inherit}"
        "a{color:light-dark(#005c92,#8ecdfa)}"
        "[hidden]{display:none}</style><h1>Lokale Sammlung · "
        + str(len(active) if active else len(cards))
        + " aktive Werke</h1>"
        + (
            "<p>1000 Werke im lokalen Update-Katalog: 344 aus dem Bestand und 656 "
            "Neuzugänge. 56 Bestandsfälle sind mit deiner Freigabe vorläufig "
            "zurückgestellt; sieben geprüfte Neuzugänge bleiben Reserve. "
            "Quellen, IDs und Farbprofile sind weiterhin separat sichtbar. "
            "Noch nicht veröffentlicht; die öffentliche App enthält weiterhin 400.</p>"
            if active
            else "<p>Lokale Recherche, noch keine abschließende Auswahl oder Veröffentlichung.</p>"
        )
        + (
            '<p><a href="cc-gallery.html">Moderne CC-Motive · '
            "separate Recherchevorschau"
            " (noch nicht aufgenommen)</a></p>"
            if (OUTPUT / "cc-gallery.html").exists()
            else ""
        )
        + "<p>Vorläufige Farbanalyse · vollständiges Bild "
        "ohne zugesetzte TV-Ränder.</p>"
        '<label>Farbwunsch <select id="colour"><option value="any">Alle Farben</option>'
        + choices
        + '</select></label> <label>Auswahl <select id="kind">'
        '<option value="any">Bestand und Neuzugänge</option>'
        '<option value="new">Nur Neuzugänge</option>'
        '<option value="baseline">Nur Bestandswerke</option></select></label>'
        ' <label>Katalog <select id="status"><option value="active">1000 aktive Werke</option>'
        '<option value="held">56 zurückgestellte Bestandsfälle</option>'
        '<option value="reserve">7 geprüfte Reserven</option>'
        '<option value="any">Alle 1063 Rechercheeinträge</option></select></label>'
        '<p id="count" aria-live="polite"></p><div class="grid">'
        + "".join(cards)
        + '</div><script>const s=document.getElementById("colour");'
        'const k=document.getElementById("kind");'
        'const t=document.getElementById("status");'
        'function apply(){let n=0;for(const a of document.querySelectorAll("article")){'
        'a.hidden=(s.value!=="any"&&!a.dataset.colours.split(" ").includes(s.value))'
        '||(k.value!=="any"&&a.dataset.kind!==k.value)'
        '||(t.value!=="any"&&a.dataset.status!==t.value);'
        'if(!a.hidden)n++;}document.getElementById("count").textContent=n+" Treffer";}'
        's.addEventListener("change",apply);k.addEventListener("change",apply);'
        't.addEventListener("change",apply);apply();</script></html>'
    )
    (OUTPUT / "gallery.html").write_text(markup)


def sheets() -> None:
    """Private contact sheets for manual inspection of analysed thumbnails."""
    from PIL import Image, ImageDraw, ImageFont

    report = json.loads((OUTPUT / "pilot.json").read_text())
    font = ImageFont.load_default(size=16)
    for offset in range(0, len(report["profiles"]), 16):
        canvas = Image.new("RGB", (1600, 1080), "#f0f0f0")
        draw = ImageDraw.Draw(canvas)
        for index, profile in enumerate(report["profiles"][offset : offset + 16]):
            x, y = (index % 4) * 400, (index // 4) * 270
            with Image.open(OUTPUT / f"{profile['id']}.jpg") as image:
                image = image.convert("RGB")
                image.thumbnail((390, 215))
                canvas.paste(image, (x, y))
            draw.text((x + 3, y + 217), profile["title"][:43], font=font, fill="black")
            caption = " / ".join(f"{c['group']} {c['share']:.0%}" for c in profile["top_colours"])
            draw.text((x + 3, y + 239), caption, font=font, fill="black")
        canvas.save(OUTPUT / f"sheet-{offset // 16 + 1}.jpg", quality=90)


def recalibrate() -> None:
    report_path = OUTPUT / "pilot.json"
    report = json.loads(report_path.read_text())
    if report["method"] == METHOD:
        raise ValueError("already using this method")
    archive = OUTPUT / f"{report['method']}.json"
    if archive.exists():
        raise ValueError("earlier method evidence already archived")
    save(archive, report)
    for old in report["profiles"]:
        result = run_worker(OUTPUT / f"{old['id']}.jpg")
        if result["thumbnail_sha256"] != old["thumbnail_sha256"]:
            raise ValueError("thumbnail changed since first analysis")
        old.update(result, recalibrated_at=datetime.now(UTC).isoformat())
    report["method"] = METHOD
    save(report_path, report)


def refresh() -> None:
    """Recheck every cached baseline in the current pre-scan/isolated worker.

    No network or method change: colour results and thumbnail hash must match.
    Only additional review fingerprints and the offline verification receipt
    are added. This is resumable through checkpointed batches.
    """
    path = OUTPUT / "pilot.json"
    report = json.loads(path.read_text())
    for index, old in enumerate(report["profiles"]):
        if old.get("offline_prescan_reverified"):
            continue
        result = run_worker(OUTPUT / f"{old['id']}.jpg")
        for key in ("thumbnail_sha256", "method", "distribution", "palette"):
            if old[key] != result[key]:
                raise ValueError("offline recheck changed existing evidence")
        old.update(result, offline_prescan_reverified=datetime.now(UTC).isoformat())
        if index % 20 == 0:
            save(path, report)
            print(json.dumps(dict(rechecked=index + 1)))
    save(path, report)


def audit() -> None:
    report = json.loads((OUTPUT / "pilot.json").read_text())
    baseline = {w["id"]: w for w in json.loads(BASELINE.read_text())["included"]}
    ids = set()
    for profile in report["profiles"]:
        work = baseline[profile["id"]]
        if profile["id"] in ids or profile["original_sha1"] != work["sha1"]:
            raise ValueError("duplicate ID or original pin changed")
        ids.add(profile["id"])
        path = OUTPUT / f"{profile['id']}.jpg"
        if hashlib.sha256(path.read_bytes()).hexdigest() != profile["thumbnail_sha256"]:
            raise ValueError("thumbnail evidence changed")
        if (
            profile["method"] != METHOD
            or max(profile["dimensions"]) > MAX_AXIS
            or profile["bytes"] > MAX_BYTES
        ):
            raise ValueError("method or bounds disagree")
        distribution = profile["distribution"]
        if (
            [c["group"] for c in distribution] != list(GROUPS)
            or sum(c["pixels"] for c in distribution) != profile["sample_pixels"]
            or abs(sum(c["share"] for c in distribution) - 1) > 1e-9
        ):
            raise ValueError("distribution does not conserve image area")
        if any(c["share"] < MIN_SHARE for c in profile["top_colours"]):
            raise ValueError("invented meaningful colour")
        if len(profile["top_colours"]) > 3:
            raise ValueError("top-three bound")
    pilot = selection(list(baseline.values()), 48)
    summary = dict(
        schema=1,
        method=METHOD,
        analysed_count=len(ids),
        baseline_count=len(baseline),
        visually_reviewed_pilot_ids=[work["id"] for work in pilot],
        visual_review="Three contact sheets inspected; "
        "v1 dark-blue/ochre/muted-tone issues calibrated in v2. "
        "Broader labels remain provisional, not user approval.",
        source_pins_unchanged=True,
        distribution_area_verified=True,
        offline_prescan_reverified_count=sum(
            bool(p.get("offline_prescan_reverified")) for p in report["profiles"]
        ),
        thumbnail_bytes=sum(p["bytes"] for p in report["profiles"]),
        group_counts={
            key: sum(key in p["search_colours"] for p in report["profiles"]) for key in GROUPS
        },
        blue_yellow_count=sum(
            {"blue", "yellow"}.issubset(p["search_colours"]) for p in report["profiles"]
        ),
        refused=report["refused"],
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        baseline_sha256=report["baseline_sha256"],
        updated_at=datetime.now(UTC).isoformat(),
        status=(
            "research metadata; local colour-filter draft exists; "
            "public beta unchanged; 600 additions not yet accepted"
        ),
    )
    save(OUTPUT / "audit.json", summary)
    save(ROOT / "research/commons-colour-audit-2026-10-09.json", summary)
    save(ROOT / "frame_gallery/research/commons-colour-profiles-2026-10-09.json", report)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=(
            "worker",
            "fetch",
            "gallery",
            "sheets",
            "recalibrate",
            "audit",
            "refresh",
        ),
    )
    parser.add_argument("argument", nargs="?", default="48")
    args = parser.parse_args()
    if args.mode == "worker":
        print(json.dumps(analyse(Path(args.argument))))
    elif args.mode == "fetch":
        fetch(int(args.argument))
    elif args.mode == "gallery":
        gallery()
    elif args.mode == "sheets":
        sheets()
    elif args.mode == "recalibrate":
        recalibrate()
    elif args.mode == "refresh":
        refresh()
    else:
        audit()
