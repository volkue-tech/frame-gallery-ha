"""Resumable metadata discovery; candidates are NOT accepted artworks.

Documented CirrusSearch file-measure windows reduce irrelevant portrait files.
Only the current public Commons gateway is used. No artwork bytes, credentials,
runtime catalogue changes or automatic rights/visual approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OUTPUT = ROOT / "build/commons-1000-research"
WIDTH_WINDOWS = (
    (3000, 3300),
    (3301, 3700),
    (3701, 4200),
    (4201, 4800),
    (4801, 5500),
    (5501, 6400),
    (6401, 7600),
    (7601, 9500),
    (9501, 12500),
    (12501, 20000),
)
MAX_PAGES_PER_WINDOW = 10
PRECISE_WINDOWS = tuple(
    (low, min(low + step - 1, stop))
    for start, stop, step in (
        (3000, 6000, 100),
        (6001, 12000, 200),
        (12001, 20000, 400),
    )
    for low in range(start, stop + 1, step)
)
HIGH_RES_WINDOWS = tuple((low, low + 1999) for low in range(20001, 100001, 2000))
MEDIA_SUBJECT = (
    'hastemplate:Artwork (insource:"huile" OR insource:"Öl" OR '
    'insource:"tempera" OR insource:"gouache" OR insource:"watercolour" OR '
    'insource:"watercolor" OR insource:"olieverf")'
)
GENRE_SUBJECT = (
    '("digital art" OR illustration OR engraving OR lithograph OR '
    '"art photography" OR "fine art photography" OR Kusama)'
)
# Keep earlier grouped-query receipts as evidence, not a claim of genre/media
# coverage. CirrusSearch explicitly does not support parentheses and warns that
# OR interacts unpredictably with special keywords. New passes use exactly one
# documented subject predicate instead of a Boolean group.
SINGLE_SUBJECTS = {
    "huile": 'hastemplate:Artwork insource:"huile"',
    "olieverf": 'hastemplate:Artwork insource:"olieverf"',
    "gouache": 'hastemplate:Artwork insource:"gouache"',
    "tempera": 'hastemplate:Artwork insource:"tempera"',
    "watercolour": 'hastemplate:Artwork insource:"watercolour"',
    "watercolor": 'hastemplate:Artwork insource:"watercolor"',
    "digital-art": '"digital art"',
    "fine-art-photography": '"fine art photography"',
    "abstract-photography": '"abstract photography"',
    "fractal-art": '"fractal art"',
    "generative-art": '"generative art"',
    "kusama": '"Yayoi Kusama"',
    "engraving": 'hastemplate:Artwork insource:"engraving"',
    "lithograph": 'hastemplate:Artwork insource:"lithograph"',
    # Explicit author/name discovery is not attribution or artwork clearance.
    # These independently retained searches broaden photographic composition;
    # raw source, actual composition and variety still decide each admission.
    "w-carter": '"W.carter"',
    "george-chernilevsky": '"George Chernilevsky"',
    "cekeech": '"CEKeech"',
    "mironov": '"Mironov"',
    "quality-cc0": "hastemplate:QualityImage hastemplate:CC-zero",
    "quality-pd-self": "hastemplate:QualityImage hastemplate:PD-self",
}


def eligible(info: dict) -> bool:
    width, height = info.get("width"), info.get("height")
    return (
        isinstance(width, int)
        and isinstance(height, int)
        and 3000 <= width <= 100000
        and 0 < height <= 100000
        and abs(width / height / (16 / 9) - 1) <= 0.025
        and info.get("mime") == "image/jpeg"
    )


def busy_refusal(response: object) -> bool:
    """Only the retained public search-overload response is scoped deferrable.

    No auth failure or unknown refusal permits continuation, and this never
    authorizes repeating the failed query.
    """
    return (
        isinstance(response, dict)
        and isinstance(response.get("error"), dict)
        and response["error"].get("code") == "cirrussearch-too-busy-error"
    )


def discover(
    artwork: bool = False,
    paintings: bool = False,
    pdart: bool = False,
    precise: bool = False,
    artwork_precise: bool = False,
    paintings_precise: bool = False,
    cc0_art_precise: bool = False,
    highres_pdart: bool = False,
    media_precise: bool = False,
    genre_precise: bool = False,
    single_subject: str | None = None,
) -> None:
    if single_subject is not None and single_subject not in SINGLE_SUBJECTS:
        raise ValueError("unknown independently scoped discovery subject")
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "frame_gallery/src"))
    from frame_gallery.budget.allowance import Allowance
    from frame_gallery.budget.clock import SystemClock
    from frame_gallery.budget.deadline import Deadline
    from frame_gallery.net.gateway import Gateway
    from frame_gallery.net.identity import commons_identity
    from frame_gallery.net.policy import https_url
    from frame_gallery.net.transport import SystemResolver, Urllib3Transport
    from frame_gallery.providers.commons import commons_policy
    from frame_gallery.providers.contract import SourceError
    from frame_gallery.randomness import SeededRandomSource

    from research_tools.commons_colours import BASELINE, save

    OUTPUT.mkdir(parents=True, exist_ok=True)
    name = (
        f"subject-{single_subject}"
        if single_subject is not None
        else "genre-precise"
        if genre_precise
        else "media-precise"
        if media_precise
        else "pdart-highres"
        if highres_pdart
        else "cc0-art-precise"
        if cc0_art_precise
        else "paintings-precise"
        if paintings_precise
        else "artwork-precise"
        if artwork_precise
        else "pdart-precise"
        if precise
        else "pdart-single"
        if pdart
        else "paintings"
        if paintings
        else "artwork"
        if artwork
        else "broad"
    )
    path = OUTPUT / (f"discovery-{name}.json" if name != "broad" else "discovery.json")
    baseline = json.loads(BASELINE.read_text())["included"]
    excluded_ids = {w["id"] for w in baseline}
    excluded_hashes = {w["sha1"] for w in baseline}
    report = (
        json.loads(path.read_text())
        if path.exists()
        else dict(
            schema=1,
            status="unreviewed metadata candidates only",
            candidates=[],
            completed_windows=[],
            scanned_ids=[],
            pages_scanned=0,
            baseline_sha256=hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
        )
    )
    if report["baseline_sha256"] != hashlib.sha256(BASELINE.read_bytes()).hexdigest():
        raise ValueError("baseline changed")
    clock = SystemClock()
    gateway = Gateway(
        resolver=SystemResolver(),
        transport=Urllib3Transport(),
        clock=clock,
        random=SeededRandomSource(20261009),
        identity=commons_identity(),
    )
    channel = gateway.channel(
        commons_policy(), metadata_allowance=Allowance("discovery", 150)
    )
    deadline = Deadline.after(clock, 900, "finite Commons discovery")
    scanned = set(report["scanned_ids"])
    hashes = excluded_hashes | {w["sha1"] for w in report["candidates"]}
    windows = (
        HIGH_RES_WINDOWS
        if highres_pdart
        else PRECISE_WINDOWS
        if precise
        or artwork_precise
        or paintings_precise
        or cc0_art_precise
        or media_precise
        or genre_precise
        or single_subject is not None
        else WIDTH_WINDOWS + ((20001, 35000), (35001, 100000))
        if pdart
        else WIDTH_WINDOWS
    )
    completed_requests = set(report.get("completed_requests", []))
    requests = 0
    for low, high in windows:
        key = f"{low}-{high}"
        if key in report["completed_windows"]:
            continue
        if list(OUTPUT.glob(f"search-{name}-{key}-*-network-deferred.json")):
            # A failed exchange is not an exhausted window. Other independent
            # windows can proceed, but this one needs separately reviewed retry.
            continue
        refusals = list(OUTPUT.glob(f"search-{name}-{key}-*-refused.json"))
        if refusals and all(busy_refusal(json.loads(p.read_text())) for p in refusals):
            # Retain the overloaded rectangle, then work on independent windows.
            # It is not exhausted or retried, even on a later invocation.
            if key not in report.setdefault("busy_deferred_windows", []):
                report["busy_deferred_windows"].append(key)
                save(path, report)
            continue
        # This rectangle is deliberately wider than the exact ratio band;
        # original metadata gets the unchanged exact 2.5% check afterwards.
        bottom, top = int(low / (16 / 9) / 1.025), int(high / (16 / 9) / 0.975) + 1
        subject = (
            SINGLE_SUBJECTS[single_subject]
            if single_subject is not None
            else GENRE_SUBJECT
            if genre_precise
            else MEDIA_SUBJECT
            if media_precise
            else "hastemplate:CC-zero (painting OR watercolor OR gouache "
            'OR "digital art" OR abstract)'
            if cc0_art_precise
            else 'hastemplate:Artwork insource:"oil"'
            if paintings_precise
            else "hastemplate:Artwork"
            if artwork_precise
            else 'hastemplate:"PD-Art"'
            if pdart or precise or highres_pdart
            else 'hastemplate:Artwork insource:"oil"'
            if paintings
            else "hastemplate:Artwork"
            if artwork
            else (
                '(painting OR "oil on canvas" OR "oil on panel" '
                "OR watercolor OR gouache)"
            )
        )
        query_text = (
            f'filemime:"image/jpeg" filew:{low},{high} fileh:{bottom},{top} {subject}'
        )
        for page_index in range(MAX_PAGES_PER_WINDOW):
            request_key = f"{key}:{page_index}"
            if request_key in completed_requests:
                continue
            if (OUTPUT / f"search-{name}-{key}-{page_index}-refused.json").exists():
                raise ValueError("saved refused query needs review; no automatic retry")
            if requests >= 140 or deadline.remaining() < 45:
                print(json.dumps(dict(status="finite pass cap; progress retained")))
                return
            query = (
                ("action", "query"),
                ("format", "json"),
                ("formatversion", "2"),
                ("generator", "search"),
                ("gsrnamespace", "6"),
                ("gsrsearch", query_text),
                ("gsrlimit", "100"),
                ("gsroffset", str(page_index * 100)),
                ("prop", "imageinfo"),
                ("iiprop", "size|mime|sha1"),
                ("iilimit", "1"),
                ("maxlag", "5"),
            )
            try:
                response = channel.get_json(
                    https_url("commons.wikimedia.org", "/w/api.php", query), deadline
                )
            except SourceError as error:
                save(
                    OUTPUT / f"search-{name}-{key}-{page_index}-network-deferred.json",
                    dict(
                        request_key=request_key,
                        kind=error.kind.value,
                        observed_at=clock.utc_now().isoformat(),
                        status="network exchange failed; window NOT exhausted",
                        retry="No automatic retry; separately reviewed retry only",
                    ),
                )
                print(
                    json.dumps(
                        dict(
                            status="network deferred; progress retained",
                            request_key=request_key,
                            kind=error.kind.value,
                        )
                    )
                )
                return
            if (
                not isinstance(response, dict)
                or "error" in response
                or "warnings" in response
            ):
                save(
                    OUTPUT / f"search-{name}-{key}-{page_index}-refused.json", response
                )
                raise ValueError("discovery query refused")
            save(OUTPUT / f"search-{name}-{key}-{page_index}.json", response)
            report["pages_scanned"] += 1
            for page in response.get("query", {}).get("pages", []):
                page_id = page.get("pageid")
                infos = page.get("imageinfo", [])
                if page_id in scanned or len(infos) != 1:
                    continue
                scanned.add(page_id)
                info = infos[0]
                if (
                    not isinstance(page_id, int)
                    or isinstance(page_id, bool)
                    or page_id <= 0
                    or page.get("ns") != 6
                    or page.get("imagerepository") != "local"
                    or not isinstance(page.get("title"), str)
                    or not page["title"].startswith("File:")
                    or not isinstance(info.get("sha1"), str)
                    or len(info["sha1"]) != 40
                    or any(c not in "0123456789abcdef" for c in info["sha1"])
                    or page_id in excluded_ids
                    or info.get("sha1") in hashes
                    or not eligible(info)
                ):
                    continue
                hashes.add(info["sha1"])
                report["candidates"].append(
                    dict(
                        id=page_id,
                        file_title=page["title"],
                        sha1=info["sha1"],
                        width=info["width"],
                        height=info["height"],
                        source=f"https://commons.wikimedia.org/w/index.php?curid={page_id}",
                        query=query_text,
                        status="needs rights, artwork-duplicate and visual review",
                    )
                )
            report["scanned_ids"] = sorted(scanned)
            completed_requests.add(request_key)
            report["completed_requests"] = sorted(completed_requests)
            requests += 1
            report["updated_at"] = clock.utc_now().isoformat()
            save(path, report)
            print(
                json.dumps(
                    dict(
                        window=key,
                        page=page_index,
                        scanned=len(scanned),
                        candidates=len(report["candidates"]),
                    )
                )
            )
            if "continue" not in response:
                report.setdefault("exhausted_windows", []).append(key)
                break
        if key not in report.get("exhausted_windows", []):
            report.setdefault("capped_windows", []).append(key)
        report["completed_windows"].append(key)
        save(path, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artwork", action="store_true")
    parser.add_argument("--paintings", action="store_true")
    parser.add_argument("--pdart", action="store_true")
    parser.add_argument("--precise", action="store_true")
    parser.add_argument("--artwork-precise", action="store_true")
    parser.add_argument("--paintings-precise", action="store_true")
    parser.add_argument("--cc0-art-precise", action="store_true")
    parser.add_argument("--highres-pdart", action="store_true")
    parser.add_argument("--media-precise", action="store_true")
    parser.add_argument("--genre-precise", action="store_true")
    parser.add_argument("--single-subject", choices=tuple(SINGLE_SUBJECTS))
    args = parser.parse_args()
    if (
        sum(
            (
                args.artwork,
                args.paintings,
                args.pdart,
                args.precise,
                args.artwork_precise,
                args.paintings_precise,
                args.cc0_art_precise,
                args.highres_pdart,
                args.media_precise,
                args.genre_precise,
                args.single_subject is not None,
            )
        )
        > 1
    ):
        parser.error("choose one research search scope")
    discover(
        args.artwork,
        args.paintings,
        args.pdart,
        args.precise,
        args.artwork_precise,
        args.paintings_precise,
        args.cc0_art_precise,
        args.highres_pdart,
        args.media_precise,
        args.genre_precise,
        args.single_subject,
    )
