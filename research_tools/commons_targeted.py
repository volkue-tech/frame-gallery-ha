"""Finite artist/medium discovery in narrower dimension windows.

Public read-only queries, saved raw receipts, unchanged acceptance constraints.
"""

from __future__ import annotations

import argparse
import hashlib
import json

from research_tools.commons_colours import BASELINE, save
from research_tools.commons_expand import OUTPUT, eligible
from research_tools.commons_review import research_channel

WINDOWS = ((3000, 4500), (4501, 6500), (6501, 10000), (10001, 20000), (20001, 100000))
EXTRA_ARTISTS = (
    "Kandinsky",
    "Klee",
    "Delaunay",
    "Mondrian",
    "Doesburg",
    "Kobayashi Kiyochika",
    "Ohara Koson",
    "Hiroshige",
    "Hokusai",
    "Yokoyama Taikan",
    "Macke",
    "Marc",
    "Jawlensky",
    "Af Klint",
    "Rozanova",
    "Popova",
    "Exter",
    "Goncharova",
    "Malevich",
    "El Lissitzky",
    "Schlemmer",
    "Feininger",
    "Kupka",
    "Valadon",
    "Vallotton",
    "Vuillard",
    "Bonnard",
    "Bauer",
    "Nolde",
    "Friesz",
    "Münter",
)


def discover(limit: int) -> None:
    from frame_gallery.net.policy import https_url

    if not 1 <= limit <= 150:
        raise ValueError("finite search pass")
    baseline = json.loads(BASELINE.read_text())
    artists = list(
        dict.fromkeys(EXTRA_ARTISTS + tuple(w["artist"] for w in baseline["included"]))
    )
    path = OUTPUT / "discovery-targeted.json"
    report = (
        json.loads(path.read_text())
        if path.exists()
        else dict(
            schema=1,
            status="unreviewed candidates only",
            candidates=[],
            completed_queries=[],
        )
    )
    seen = {w["id"] for w in baseline["included"] + baseline["previously_deferred"]}
    hashes = {w["sha1"] for w in baseline["included"]}
    for name in (
        "discovery.json",
        "discovery-artwork.json",
        "discovery-paintings.json",
        "discovery-artists.json",
        "discovery-targeted.json",
    ):
        source = OUTPUT / name
        if source.exists():
            for w in json.loads(source.read_text())["candidates"]:
                seen.add(w["id"])
                hashes.add(w["sha1"])
    channel, deadline = research_channel(limit + 1)
    requests = 0
    # Modern artists first; each pass is resumable without blind repeated pages.
    for artist in artists:
        term = artist.replace('"', "").replace("\\", "")
        for low, high in WINDOWS:
            bottom = int(low / (16 / 9) / 1.025)
            top = int(high / (16 / 9) / 0.975) + 1
            query_text = (
                f'filemime:"image/jpeg" filew:{low},{high} fileh:{bottom},{top} '
                f'"{term}"'
            )
            if query_text in report["completed_queries"] or any(
                row["query"] == query_text for row in report.get("deferred_queries", [])
            ):
                continue
            document = channel.get_json(
                https_url(
                    "commons.wikimedia.org",
                    "/w/api.php",
                    (
                        ("action", "query"),
                        ("format", "json"),
                        ("formatversion", "2"),
                        ("generator", "search"),
                        ("gsrnamespace", "6"),
                        ("gsrsearch", query_text),
                        ("gsrlimit", "100"),
                        ("prop", "imageinfo"),
                        ("iiprop", "size|mime|sha1"),
                        ("iilimit", "1"),
                        ("maxlag", "5"),
                    ),
                ),
                deadline,
            )
            if (
                not isinstance(document, dict)
                or "error" in document
                or "warnings" in document
            ):
                key = hashlib.sha256(query_text.encode()).hexdigest()[:20]
                receipt = OUTPUT / f"search-targeted-refusal-{key}.json"
                save(receipt, document)
                report.setdefault("deferred_queries", []).append(
                    dict(
                        query=query_text,
                        reason="API response refused; no automatic retry",
                        receipt=receipt.name,
                    )
                )
                save(path, report)
                raise ValueError("targeted query refused; no blind retries")
            key = hashlib.sha256(query_text.encode()).hexdigest()[:20]
            save(OUTPUT / f"search-targeted-{key}.json", document)
            for page in document.get("query", {}).get("pages", []):
                infos = page.get("imageinfo", [])
                page_id = page.get("pageid")
                if (
                    not isinstance(page_id, int)
                    or isinstance(page_id, bool)
                    or page_id <= 0
                    or page_id in seen
                    or page.get("ns") != 6
                    or page.get("imagerepository") != "local"
                    or len(infos) != 1
                    or not isinstance(page.get("title"), str)
                    or not page["title"].startswith("File:")
                ):
                    continue
                info = infos[0]
                pin = info.get("sha1")
                if (
                    not eligible(info)
                    or not isinstance(pin, str)
                    or len(pin) != 40
                    or any(c not in "0123456789abcdef" for c in pin)
                    or pin in hashes
                ):
                    continue
                seen.add(page_id)
                hashes.add(pin)
                report["candidates"].append(
                    dict(
                        id=page_id,
                        file_title=page["title"],
                        sha1=pin,
                        width=info["width"],
                        height=info["height"],
                        source=f"https://commons.wikimedia.org/w/index.php?curid={page_id}",
                        query=query_text,
                        status="needs rights, artwork-duplicate and visual review",
                    )
                )
            report["completed_queries"].append(query_text)
            save(path, report)
            requests += 1
            print(
                json.dumps(
                    dict(
                        queries=len(report["completed_queries"]),
                        new_candidates=len(report["candidates"]),
                    )
                ),
                flush=True,
            )
            if requests >= limit:
                return


if __name__ == "__main__":
    import sys

    from research_tools.commons_colours import ROOT

    sys.path.insert(0, str(ROOT / "frame_gallery/src"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=150)
    args = parser.parse_args()
    discover(args.limit)
