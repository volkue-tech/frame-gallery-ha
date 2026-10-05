"""Independently invented Commons documents, never recorded live responses."""

from __future__ import annotations

from dataclasses import dataclass, field

from frame_gallery.net.wire import WireRequest
from frame_gallery.providers.commons_catalog import CuratedWork
from tests.support.museums import parse
from tests.support.net import FakeResponse, json_response

TEST_CATALOG = tuple(
    CuratedWork(n, f"File:Synthetic artwork {n}.jpg", f"{n:040x}", f"Test Work {n}", "Test Artist")
    for n in range(1, 13)
)


def record(work: CuratedWork) -> dict[str, object]:
    return {
        "pageid": work.page_id,
        "ns": 6,
        "title": work.file_title,
        "imagerepository": "local",
        "imageinfo": [
            {
                "width": 6000,
                "height": 3375,
                "sha1": work.sha1,
                "mime": "image/jpeg",
                "url": f"https://upload.wikimedia.org/wikipedia/commons/a/ab/test{work.page_id}.jpg",
                "thumburl": f"https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/test{work.page_id}.jpg/3840px-test.jpg",
                "thumbwidth": 3840,
                "thumbheight": 2160,
                "thumbmime": "image/jpeg",
                "extmetadata": {
                    "LicenseShortName": {"value": "Public domain"},
                    "Copyrighted": {"value": "False"},
                    "AttributionRequired": {"value": "false"},
                    "Restrictions": {"value": ""},
                },
            }
        ],
    }


@dataclass
class CommonsSite:
    records: dict[int, object] = field(
        default_factory=lambda: {work.page_id: record(work) for work in TEST_CATALOG}
    )
    queries: list[dict[str, str]] = field(default_factory=list)

    def __call__(self, request: WireRequest) -> FakeResponse:
        parsed = parse(request)
        assert parsed.host == "commons.wikimedia.org"
        assert parsed.path == "/w/api.php"
        self.queries.append(parsed.query)
        ids = [int(value) for value in parsed.query["pageids"].split("|")]
        return json_response(
            {"query": {"pages": [self.records.get(n, {"pageid": n, "missing": True}) for n in ids]}}
        )
