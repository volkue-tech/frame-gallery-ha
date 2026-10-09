"""Finite public artist searches; results remain unreviewed candidates."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "frame_gallery/src"))

from frame_gallery.net.policy import https_url  # noqa: E402

from research_tools.commons_colours import BASELINE, save  # noqa: E402
from research_tools.commons_expand import OUTPUT, eligible  # noqa: E402
from research_tools.commons_review import research_channel  # noqa: E402


def discover() -> None:
    baseline = json.loads(BASELINE.read_text())
    artists = list(dict.fromkeys(w["artist"] for w in baseline["included"]))[:150]
    path = OUTPUT / "discovery-artists.json"
    report = (
        json.loads(path.read_text())
        if path.exists()
        else dict(
            schema=1,
            status="unreviewed targeted candidates only",
            candidates=[],
            completed_artists=[],
            baseline_sha256=hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
        )
    )
    if report["baseline_sha256"] != hashlib.sha256(BASELINE.read_bytes()).hexdigest():
        raise ValueError("baseline changed")
    seen = {w["id"] for w in baseline["included"] + baseline["previously_deferred"]}
    hashes = {w["sha1"] for w in baseline["included"]}
    for name in (
        "discovery.json",
        "discovery-artwork.json",
        "discovery-paintings.json",
    ):
        other = OUTPUT / name
        if other.exists():
            for work in json.loads(other.read_text())["candidates"]:
                seen.add(work["id"])
                hashes.add(work["sha1"])
    seen.update(w["id"] for w in report["candidates"])
    hashes.update(w["sha1"] for w in report["candidates"])
    channel, deadline = research_channel(155)
    for artist in artists:
        if artist in report["completed_artists"]:
            continue
        term = artist.replace('"', "").replace("\\", "")
        query_text = (
            f'filemime:"image/jpeg" filew:3000,100000 hastemplate:Artwork "{term}"'
        )
        query = (
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
        )
        document = channel.get_json(
            https_url("commons.wikimedia.org", "/w/api.php", query), deadline
        )
        if (
            not isinstance(document, dict)
            or "error" in document
            or "warnings" in document
        ):
            raise ValueError("targeted search refused; no blind retries")
        key = hashlib.sha256(artist.encode()).hexdigest()[:16]
        save(OUTPUT / f"search-artist-{key}.json", document)
        for page in document.get("query", {}).get("pages", []):
            page_id = page.get("pageid")
            infos = page.get("imageinfo", [])
            if (
                not isinstance(page_id, int)
                or page_id <= 0
                or page_id in seen
                or len(infos) != 1
            ):
                continue
            info = infos[0]
            if (
                page.get("ns") != 6
                or page.get("imagerepository") != "local"
                or not isinstance(page.get("title"), str)
                or not page["title"].startswith("File:")
                or not eligible(info)
                or not isinstance(info.get("sha1"), str)
                or len(info["sha1"]) != 40
                or any(c not in "0123456789abcdef" for c in info["sha1"])
                or info["sha1"] in hashes
            ):
                continue
            seen.add(page_id)
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
        report["completed_artists"].append(artist)
        save(path, report)
        print(
            json.dumps(
                dict(
                    artists=len(report["completed_artists"]),
                    candidates=len(report["candidates"]),
                )
            )
        )


if __name__ == "__main__":
    discover()
