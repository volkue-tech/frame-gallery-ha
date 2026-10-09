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


def discover(artwork: bool = False, paintings: bool = False) -> None:
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
    from frame_gallery.randomness import SeededRandomSource

    from research_tools.commons_colours import BASELINE, save

    OUTPUT.mkdir(parents=True, exist_ok=True)
    name = "paintings" if paintings else "artwork" if artwork else "broad"
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
    for low, high in WIDTH_WINDOWS:
        key = f"{low}-{high}"
        if key in report["completed_windows"]:
            continue
        # This rectangle is deliberately wider than the exact ratio band;
        # original metadata gets the unchanged exact 2.5% check afterwards.
        bottom, top = int(low / (16 / 9) / 1.025), int(high / (16 / 9) / 0.975) + 1
        subject = (
            'hastemplate:Artwork insource:"oil"'
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
            response = channel.get_json(
                https_url("commons.wikimedia.org", "/w/api.php", query), deadline
            )
            if (
                not isinstance(response, dict)
                or "error" in response
                or "warnings" in response
            ):
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
                break
        report["completed_windows"].append(key)
        save(path, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artwork", action="store_true")
    parser.add_argument("--paintings", action="store_true")
    args = parser.parse_args()
    discover(args.artwork, args.paintings)
