"""The runner with the real selection, the in-process executor, and real rendering.

Only the provider, fetcher, state, television, preview, and records are fakes.
Images are generated in the test; nothing is downloaded (§20.1, §20.3).
"""

from __future__ import annotations

import hashlib
import io
import os
import signal
from collections.abc import Iterator
from pathlib import Path

import pytest
from PIL import Image

from frame_gallery.app.outcomes import Outcome
from frame_gallery.app.signals import install_sigterm_handler
from frame_gallery.domain import CANVAS, Size
from frame_gallery.imaging.jpeg_header import parse_jpeg
from frame_gallery.isolation.in_process import default_executor
from frame_gallery.providers.contract import Candidate
from frame_gallery.selection.shortlist import ChoiceBasis
from frame_gallery.tv.port import DeliveryStatus, Marker
from tests.support.fakes import make_candidate
from tests.unit.app.harness import Harness

BRIGHT = (230, 200, 40)


def jpeg(size: Size, colour: tuple[int, int, int] = BRIGHT) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (size.width, size.height), colour).save(buffer, "JPEG", quality=90)
    return buffer.getvalue()


def real_harness(tmp_path: Path, candidates: list[Candidate], **raw: object) -> Harness:
    h = Harness(tmp_path, raw={"tv_host": "10.0.0.5", **raw}, candidates=candidates)
    h.executor = default_executor(h.clock)  # type: ignore[assignment]
    for candidate in candidates:
        if candidate.dims is not None:
            h.fetcher.payloads[candidate.native_id] = jpeg(candidate.dims)
    return h


def decoded(data: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(data))
    image.load()
    return image


def test_a_strict_16_9_work_is_rendered_and_delivered(tmp_path: Path) -> None:
    h = real_harness(tmp_path, [make_candidate("1", size=Size(1600, 900))])
    result = h.run()

    assert result.outcome is Outcome.DELIVERED
    payload = h.tv.payloads[0]
    info = parse_jpeg(payload)
    assert (info.width, info.height) == (CANVAS.width, CANVAS.height)
    assert info.is_baseline
    assert info.components == 3
    # D8: the preview bytes and the recorded fingerprint equal the TV payload.
    assert h.preview.published == [payload]
    assert h.records.current[0]["sha256"] == hashlib.sha256(payload).hexdigest()


def test_fallback_to_a_landscape_work_keeps_every_pixel(tmp_path: Path) -> None:
    """C6, D1, D2, D3: no strict match, so a 4:3 work is fitted with black margins."""
    h = real_harness(tmp_path, [make_candidate("43", size=Size(1600, 1200))])
    result = h.run()

    assert result.outcome is Outcome.DELIVERED
    assert h.last_run["stats"]["attempts"][0]["basis"] == ChoiceBasis.FALLBACK.value  # type: ignore[index]
    image = decoded(h.tv.payloads[0]).convert("RGB")
    # 1600x1200 scaled by 1.8 is 2880x2160, centred: 480 px black margins.
    left_margin = image.getpixel((200, 1080))
    right_margin = image.getpixel((3640, 1080))
    centre = image.getpixel((1920, 1080))
    assert isinstance(left_margin, tuple)
    assert isinstance(right_margin, tuple)
    assert isinstance(centre, tuple)
    assert max(left_margin) < 16
    assert max(right_margin) < 16
    assert all(abs(c - e) < 24 for c, e in zip(centre, BRIGHT, strict=True))
    # The artwork reaches the top and bottom edges: nothing was cropped.
    top = image.getpixel((1920, 2))
    assert isinstance(top, tuple)
    assert max(top) > 100


def test_cover_crops_only_when_selected(tmp_path: Path) -> None:
    """D4: in cover mode the 16:10 work fills the canvas; no margins remain."""
    h = real_harness(
        tmp_path,
        [make_candidate("1610", size=Size(1600, 1000))],
        fit_mode="cover",
        strict_tv_format=False,
    )
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    image = decoded(h.tv.payloads[0]).convert("RGB")
    for point in ((2, 2), (3837, 2), (2, 2157), (3837, 2157), (1920, 1080)):
        pixel = image.getpixel(point)
        assert isinstance(pixel, tuple)
        assert max(pixel) > 100


def test_metadata_that_lies_is_caught_by_the_worker(tmp_path: Path) -> None:
    """The prepare task verifies the real size before decoding (§8.2)."""
    liar = make_candidate("liar", size=Size(1600, 900))
    honest = make_candidate("honest", size=Size(1600, 900))
    h = real_harness(tmp_path, [liar, honest])
    h.fetcher.payloads["liar"] = jpeg(Size(900, 1600))  # really portrait
    result = h.run()
    assert result.delivered_id == "aic:honest"
    notes = h.last_run["stats"]["attempts"]  # type: ignore[index]
    assert notes[0]["result"] == "rejected:not_landscape"


def test_too_small_renditions_are_never_shortlisted(tmp_path: Path) -> None:
    h = real_harness(tmp_path, [make_candidate("tiny", size=Size(960, 540))])
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert "executor.run:prepare" not in h.events


def test_a_second_run_never_resends_a_delivered_work(tmp_path: Path) -> None:
    """C3 and E6 against the fake store: the second run picks the next work."""
    candidates = [make_candidate(str(i), size=Size(1600, 900)) for i in (1, 2, 3)]
    h = real_harness(tmp_path, candidates)
    assert h.run().delivered_id == "aic:1"
    assert h.next_run().delivered_id == "aic:2"
    assert h.state.history == ["aic:1", "aic:2"]


def test_an_uploaded_but_unselected_work_is_not_resent(tmp_path: Path) -> None:
    """E7 against the fake store: selection refused after upload."""
    candidates = [make_candidate(str(i), size=Size(1600, 900)) for i in (1, 2)]
    h = real_harness(tmp_path, candidates)
    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED]
    h.tv.status = DeliveryStatus.REFUSED
    assert h.run().outcome is Outcome.TV_REJECTED
    assert h.state.ledger == {"aic:1": "uploaded"}

    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED, Marker.SELECTED]
    h.tv.status = DeliveryStatus.OK
    assert h.next_run().delivered_id == "aic:2"


def test_an_uncertain_upload_is_quarantined_for_the_next_run(tmp_path: Path) -> None:
    """E8/E9 groundwork: a lost connection after upload_started excludes the work."""
    candidates = [make_candidate(str(i), size=Size(1600, 900)) for i in (1, 2)]
    h = real_harness(tmp_path, candidates)
    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED]
    h.tv.status = DeliveryStatus.UNREACHABLE
    assert h.run().outcome is Outcome.TV_UNREACHABLE
    assert h.state.ledger == {"aic:1": "uncertain"}

    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED, Marker.SELECTED]
    h.tv.status = DeliveryStatus.OK
    assert h.next_run().delivered_id == "aic:2"


@pytest.fixture
def sigterm_handler(tmp_path: Path) -> Iterator[Harness]:
    candidates = [make_candidate(str(i), size=Size(1600, 900)) for i in (1, 2)]
    h = real_harness(tmp_path, candidates)
    restore = install_sigterm_handler(h.cancellation)
    try:
        yield h
    finally:
        restore()


def test_a_real_sigterm_before_delivery_cancels_the_run(sigterm_handler: Harness) -> None:
    h = sigterm_handler
    original = h.provider._generate

    def generate_then_signal() -> Iterator[Candidate]:
        for index, candidate in enumerate(original()):
            if index == 1:
                os.kill(os.getpid(), signal.SIGTERM)
            yield candidate

    h.provider._generate = generate_then_signal  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert "tv.deliver" not in h.events
    assert h.state.ledger == {}
    assert h.records.last_run[0]["outcome"] == "cancelled"
    assert h.workspace.removed == 1


def test_a_real_sigterm_after_selected_only_skips_the_preview(sigterm_handler: Harness) -> None:
    h = sigterm_handler

    def signal_after_selected(marker: Marker) -> None:
        if marker is Marker.SELECTED:
            os.kill(os.getpid(), signal.SIGTERM)

    h.tv.during = signal_after_selected
    result = h.run()
    assert result.outcome is Outcome.DELIVERED_WITH_WARNINGS
    assert h.state.history == ["aic:1"]
    assert h.preview.published == []
