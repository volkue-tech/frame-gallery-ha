"""Synthesized museum API documents (independently authored; D-146 shapes).

Nothing here was recorded from a live API. The field names and envelopes
follow the official documentation pages re-read on 2026-09-27; every value
is invented, and titles say so.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlsplit

from frame_gallery.net.wire import WireRequest
from tests.support.net import FakeResponse, json_response, status_response

# --- Art Institute of Chicago ------------------------------------------------


def aic_image_id(number: int) -> str:
    """A synthetic identifier in the UUID form of the documentation's examples."""
    return f"{number:08x}-0000-4000-8000-{number:012x}"


def aic_record(
    artwork_id: int,
    *,
    image: int | None = None,
    public: object = True,
    date_start: object = 1880,
    title: object = None,
) -> dict[str, object]:
    return {
        "id": artwork_id,
        "is_public_domain": public,
        "title": f"Synthetic Work {artwork_id}" if title is None else title,
        "artist_display": f"Synthetic Artist {artwork_id % 7}",
        "date_display": "c. 1880",
        "date_start": date_start,
        "image_id": aic_image_id(artwork_id if image is None else image),
        "credit_line": "Synthetic Fund",
    }


def aic_search(records: Sequence[object], total: int) -> dict[str, object]:
    return {
        "pagination": {
            "total": total,
            "limit": 50,
            "offset": 0,
            "total_pages": 1,
            "current_page": 1,
        },
        "data": list(records),
        "config": {"iiif_url": "https://www.artic.edu/iiif/2"},
    }


def aic_images(sizes: Mapping[str, tuple[object, object]]) -> dict[str, object]:
    return {"data": [{"id": key, "width": w, "height": h} for key, (w, h) in sizes.items()]}


@dataclass
class ParsedRequest:
    host: str
    path: str
    query: dict[str, str]

    @property
    def params(self) -> dict[str, object]:
        """The Art Institute's JSON ``params`` parameter, decoded."""
        document = json.loads(self.query["params"])
        assert isinstance(document, dict)
        return document


def parse(request: WireRequest) -> ParsedRequest:
    parts = urlsplit(f"https://{request.host}{request.target}")
    query = {
        key: values[-1] for key, values in parse_qs(parts.query, keep_blank_values=True).items()
    }
    assert all(len(values) == 1 for values in parse_qs(parts.query).values())
    return ParsedRequest(request.host, parts.path, query)


@dataclass
class AicMuseum:
    """A synthetic Art Institute API: a catalogue of records, paged like the
    documentation describes, and image sizes per image ID."""

    records: list[object] = field(default_factory=list)
    """Record objects; tests may add malformed entries."""
    sizes: dict[str, tuple[object, object]] = field(default_factory=dict)
    total: int | None = None
    """Reported total; defaults to the number of records."""

    overrides: dict[str, Callable[[ParsedRequest], FakeResponse]] = field(default_factory=dict)
    seen: list[ParsedRequest] = field(default_factory=list)

    def add(self, count: int, *, width: int = 3840, height: int = 2160, first: int = 1) -> None:
        for artwork_id in range(first, first + count):
            record = aic_record(artwork_id)
            self.records.append(record)
            self.sizes[str(record["image_id"])] = (width, height)

    def __call__(self, request: WireRequest) -> FakeResponse:
        parsed = parse(request)
        self.seen.append(parsed)
        override = self.overrides.get(parsed.path)
        if override is not None:
            return override(parsed)
        if parsed.host == "api.artic.edu" and parsed.path == "/api/v1/artworks/search":
            params = parsed.params
            total = len(self.records) if self.total is None else self.total
            limit = params["limit"]
            assert isinstance(limit, int)
            if limit == 0:
                return json_response(aic_search([], total))
            page = params["page"]
            assert isinstance(page, int)
            start = (page - 1) * limit
            return json_response(aic_search(self.records[start : start + limit], total))
        if parsed.host == "api.artic.edu" and parsed.path == "/api/v1/images":
            wanted = parsed.query["ids"].split(",")
            return json_response(aic_images({i: self.sizes[i] for i in wanted if i in self.sizes}))
        return status_response(404)

    def paths(self) -> list[str]:
        return [request.path for request in self.seen]


# --- Cleveland Museum of Art -------------------------------------------------

CMA_API = "openaccess-api.clevelandart.org"
CMA_CDN = "openaccess-cdn.clevelandart.org"


def cma_record(
    artwork_id: int,
    *,
    status: object = "CC0",
    department: object = "Prints",
    earliest: object = 1880,
    print_url: object = None,
    width: object = "3400",
    height: object = "1913",
    title: object = None,
) -> dict[str, object]:
    accession = f"1999.{artwork_id}"
    url = f"https://{CMA_CDN}/{accession}/{accession}_print.jpg" if print_url is None else print_url
    return {
        "id": artwork_id,
        "accession_number": accession,
        "share_license_status": status,
        "title": f"Synthetic Work {artwork_id}" if title is None else title,
        "creators": [{"description": f"Synthetic Artist {artwork_id % 5} (invented, 1800-1880)"}],
        "creation_date": "c. 1880",
        "creation_date_earliest": earliest,
        "department": department,
        "url": f"https://clevelandart.org/art/{accession}",
        "images": {
            "web": {
                "url": f"https://{CMA_CDN}/{accession}/{accession}_web.jpg",
                "width": "900",
                "height": "506",
            },
            "print": {"url": url, "filesize": "1000000", "width": width, "height": height},
            "full": {
                "url": f"https://{CMA_CDN}/{accession}/{accession}_full.tif",
                "width": "6000",
                "height": "3375",
            },
        },
    }


@dataclass
class CmaMuseum:
    """A synthetic Cleveland Open Access API over a list of records. The
    ``created_after``/``created_before`` filters are applied exclusively on
    ``creation_date_earliest`` (one possible reading; D-146)."""

    records: list[object] = field(default_factory=list)
    total: int | None = None
    seen: list[ParsedRequest] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    overrides: dict[str, Callable[[ParsedRequest], FakeResponse]] = field(default_factory=dict)

    def add(self, count: int, *, first: int = 1, **options: object) -> None:
        for artwork_id in range(first, first + count):
            self.records.append(cma_record(artwork_id, **options))

    def _matches(self, record: object, query: Mapping[str, str]) -> bool:
        if not isinstance(record, dict):
            return True
        if "department" in query and record.get("department") != query["department"]:
            return False
        earliest = record.get("creation_date_earliest")
        if not isinstance(earliest, int):
            return "created_after" not in query and "created_before" not in query
        if "created_after" in query and earliest <= int(query["created_after"]):
            return False
        return not ("created_before" in query and earliest >= int(query["created_before"]))

    def __call__(self, request: WireRequest) -> FakeResponse:
        parsed = parse(request)
        self.seen.append(parsed)
        self.targets.append(request.target)
        override = self.overrides.get(parsed.path)
        if override is not None:
            return override(parsed)
        if parsed.host != CMA_API or parsed.path != "/api/artworks/":
            return status_response(404)
        matching = [r for r in self.records if self._matches(r, parsed.query)]
        total = len(matching) if self.total is None else self.total
        skip = int(parsed.query.get("skip", "0"))
        limit = int(parsed.query["limit"])
        data = matching[skip : skip + limit]
        return json_response(
            {"info": {"total": total, "parameters": dict(parsed.query)}, "data": data}
        )
