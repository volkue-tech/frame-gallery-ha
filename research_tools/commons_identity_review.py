"""Bounded public baseline artwork-identity receipts, no artwork downloads."""

from __future__ import annotations

import json
import sys

from research_tools.commons_colours import BASELINE, ROOT, save
from research_tools.commons_expand import OUTPUT
from research_tools.commons_review import research_channel


def collect() -> None:
    from frame_gallery.net.policy import https_url

    baseline = json.loads(BASELINE.read_text())["included"]
    channel, deadline = research_channel(81)
    for offset in range(0, len(baseline), 5):
        batch = baseline[offset : offset + 5]
        target = OUTPUT / f"baseline-identity-{batch[0]['id']}.json"
        if target.exists():
            continue
        document = channel.get_json(
            https_url(
                "commons.wikimedia.org",
                "/w/api.php",
                (
                    ("action", "query"),
                    ("format", "json"),
                    ("formatversion", "2"),
                    ("pageids", "|".join(str(w["id"]) for w in batch)),
                    ("prop", "imageinfo|revisions"),
                    ("rvprop", "ids|timestamp|content"),
                    ("rvslots", "main"),
                    ("iiprop", "sha1|extmetadata"),
                    ("iilimit", "1"),
                    ("iiextmetadatalanguage", "en"),
                    ("iiextmetadatafilter", "ObjectName"),
                    ("maxlag", "5"),
                ),
            ),
            deadline,
        )
        if not isinstance(document, dict) or {"error", "warnings"} & document.keys():
            raise ValueError("identity request refused; no blind retry")
        pages = {p["pageid"]: p for p in document.get("query", {}).get("pages", [])}
        for work in batch:
            page = pages.get(work["id"], {})
            info = page.get("imageinfo", [])
            if len(info) != 1 or info[0].get("sha1") != work["sha1"]:
                raise ValueError("baseline identity upload pin changed")
        save(target, document)
        print(
            json.dumps(dict(baseline_identity_checked=offset + len(batch))), flush=True
        )


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "frame_gallery/src"))
    collect()
