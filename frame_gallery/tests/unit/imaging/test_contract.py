"""The ``prepare`` request and result at the executor seam (§11, §11.3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from frame_gallery.domain import BLACK, CANVAS, FitMode, Rgb, Size
from frame_gallery.imaging.contract import (
    MAX_OUTPUT_BYTES,
    ColourHandling,
    DeliveryArtifact,
    ImageFormat,
    PrepareFailure,
    PrepareRequest,
    PrepareResult,
    PrepareStatus,
)
from frame_gallery.isolation.executor import JsonObject
from frame_gallery.selection.geometry import Rejection


def _request() -> PrepareRequest:
    return PrepareRequest(
        source_path="/work/in/source.bin",
        output_path="/work/out/delivery.jpg",
        declared_format=ImageFormat.PNG,
        fit_mode=FitMode.COVER,
        background=Rgb(0x12, 0xAB, 0xEF),
        landscape_only=True,
        require_near_16_9=False,
        canvas=Size(1920, 1080),
    )


def _through_json(obj: JsonObject) -> JsonObject:
    """What crosses the channel: a JSON text, parsed again."""
    parsed = json.loads(json.dumps(obj))
    assert isinstance(parsed, dict)
    return parsed


def test_request_round_trip() -> None:
    request = _request()
    payload = _through_json(request.to_json())
    assert payload["background"] == "#12abef"
    assert payload["canvas"] == [1920, 1080]
    assert PrepareRequest.from_json(payload) == request


def test_request_defaults_to_the_canvas() -> None:
    request = PrepareRequest("a", "b", ImageFormat.JPEG, FitMode.CONTAIN, BLACK, True, True)
    assert request.canvas == CANVAS
    assert PrepareRequest.from_json(_through_json(request.to_json())) == request


def _mutated(key: str, value: Any) -> JsonObject:
    payload = _request().to_json()
    payload[key] = value
    return payload


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("source_path", 5, "non-empty string"),
        ("source_path", "", "non-empty string"),
        ("source_path", "x" * 4097, "non-empty string"),
        ("output_path", None, "non-empty string"),
        ("declared_format", 1, "must be a string"),
        ("declared_format", "GIF", "unknown value"),
        ("fit_mode", "stretch", "unknown value"),
        ("background", "#1234567", "non-empty string"),
        ("background", "red", "#RRGGBB"),
        ("background", "#12345g", "#RRGGBB"),
        ("landscape_only", 1, "boolean"),
        ("require_near_16_9", "yes", "boolean"),
        ("canvas", "3840x2160", r"\[width, height\]"),
        ("canvas", [3840], r"\[width, height\]"),
        ("canvas", [3840, 2160, 3], r"\[width, height\]"),
        ("canvas", [True, 2160], "positive integers"),
        ("canvas", [3840, False], "positive integers"),
        ("canvas", [3840.0, 2160], "positive integers"),
        ("canvas", [3840, "2160"], "positive integers"),
        ("canvas", [0, 2160], "positive integers"),
        ("canvas", [3840, 1_000_001], "positive integers"),
    ],
)
def test_request_rejects_invalid_fields(key: str, value: Any, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        PrepareRequest.from_json(_mutated(key, value))


@pytest.mark.parametrize(
    "key",
    [
        "source_path",
        "output_path",
        "declared_format",
        "fit_mode",
        "background",
        "landscape_only",
        "require_near_16_9",
        "canvas",
    ],
)
def test_request_rejects_missing_fields(key: str) -> None:
    payload = _request().to_json()
    del payload[key]
    with pytest.raises(ValueError, match=f"missing field '{key}'"):
        PrepareRequest.from_json(payload)


OK = PrepareResult(
    status=PrepareStatus.OK,
    source_size=Size(1000, 1600),
    oriented_size=Size(1600, 1000),
    orientation=6,
    output_bytes=123_456,
    jpeg_quality=90,
    colour=ColourHandling.CONVERTED,
)
REJECTED = PrepareResult(
    status=PrepareStatus.REJECTED,
    source_size=Size(900, 1600),
    oriented_size=Size(900, 1600),
    orientation=1,
    rejection=Rejection.NOT_LANDSCAPE,
    detail="oriented size 900x1600",
)
FAILED = PrepareResult(
    status=PrepareStatus.FAILED,
    failure=PrepareFailure.DECODE,
    detail="OSError: image file is truncated",
)


@pytest.mark.parametrize("result", [OK, REJECTED, FAILED])
def test_result_round_trip(result: PrepareResult) -> None:
    assert PrepareResult.from_json(_through_json(result.to_json())) == result


def test_failed_result_serializes_nulls() -> None:
    payload = FAILED.to_json()
    assert payload["source_size"] is None
    assert payload["rejection"] is None
    assert payload["colour"] is None
    assert payload["failure"] == "decode"


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"status": PrepareStatus.OK, "output_bytes": 1, "jpeg_quality": 90}, "ok result needs"),
        (
            {"status": PrepareStatus.OK, "oriented_size": Size(1, 1), "jpeg_quality": 90},
            "ok result needs",
        ),
        (
            {"status": PrepareStatus.OK, "oriented_size": Size(1, 1), "output_bytes": 1},
            "ok result needs",
        ),
        (
            {
                "status": PrepareStatus.OK,
                "source_size": Size(1, 1),
                "oriented_size": Size(1, 1),
                "orientation": 1,
                "output_bytes": 1,
                "jpeg_quality": 90,
                "colour": ColourHandling.ASSUMED_SRGB,
                "rejection": Rejection.TOO_SMALL,
            },
            "neither rejection nor failure",
        ),
        (
            {
                "status": PrepareStatus.OK,
                "source_size": Size(1, 1),
                "oriented_size": Size(1, 1),
                "orientation": 1,
                "output_bytes": 1,
                "jpeg_quality": 90,
                "colour": ColourHandling.ASSUMED_SRGB,
                "failure": PrepareFailure.IO,
            },
            "neither rejection nor failure",
        ),
        ({"status": PrepareStatus.REJECTED, "oriented_size": Size(1, 1)}, "rejected result"),
        ({"status": PrepareStatus.REJECTED, "rejection": Rejection.TOO_SMALL}, "rejected result"),
        (
            {
                "status": PrepareStatus.REJECTED,
                "oriented_size": Size(1, 1),
                "rejection": Rejection.TOO_SMALL,
                "failure": PrepareFailure.IO,
            },
            "rejected result",
        ),
        ({"status": PrepareStatus.FAILED}, "failed result"),
        (
            {"status": PrepareStatus.FAILED, "failure": PrepareFailure.IO, "output_bytes": 1},
            "only an ok result reports output details",
        ),
        (
            {
                "status": PrepareStatus.REJECTED,
                "oriented_size": Size(1, 1),
                "rejection": Rejection.TOO_SMALL,
                "jpeg_quality": 90,
            },
            "only an ok result reports output details",
        ),
        (
            {
                "status": PrepareStatus.OK,
                "oriented_size": Size(1, 1),
                "orientation": 1,
                "output_bytes": 1,
                "jpeg_quality": 90,
                "colour": ColourHandling.ASSUMED_SRGB,
            },
            "ok result needs",
        ),
        (
            {
                "status": PrepareStatus.FAILED,
                "failure": PrepareFailure.IO,
                "rejection": Rejection.TOO_SMALL,
            },
            "failed result",
        ),
    ],
)
def test_result_invariants(fields: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        PrepareResult(**fields)


def _mutated_result(key: str, value: Any) -> JsonObject:
    payload = OK.to_json()
    payload[key] = value
    return payload


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("status", "done", "unknown value"),
        ("status", None, "must be a string"),
        ("source_size", [1], r"\[width, height\]"),
        ("oriented_size", [-1, 5], "positive integers"),
        ("orientation", 0, r"1\.\.8"),
        ("orientation", 9, r"1\.\.8"),
        ("orientation", True, r"1\.\.8"),
        ("orientation", "6", r"1\.\.8"),
        ("rejection", "ugly", "unknown value"),
        ("failure", 3, "must be a string"),
        ("detail", 42, "string or null"),
        ("detail", "x" * 513, "string or null"),
        ("output_bytes", 0, "integer in"),
        ("output_bytes", MAX_OUTPUT_BYTES + 1, "integer in"),
        ("jpeg_quality", 101, "integer in"),
        ("colour", "vivid", "unknown value"),
    ],
)
def test_result_rejects_invalid_fields(key: str, value: Any, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        PrepareResult.from_json(_mutated_result(key, value))


def test_result_rejects_missing_fields() -> None:
    for key in OK.to_json():
        payload = OK.to_json()
        del payload[key]
        with pytest.raises(ValueError, match="missing field"):
            PrepareResult.from_json(payload)


def test_result_accepts_optional_values() -> None:
    payload = _mutated_result("detail", "a" * 512)
    assert PrepareResult.from_json(payload).detail == "a" * 512
    payload = _mutated_result("output_bytes", MAX_OUTPUT_BYTES)
    assert PrepareResult.from_json(payload).output_bytes == MAX_OUTPUT_BYTES


def test_rejected_result_from_json_is_validated() -> None:
    payload = REJECTED.to_json()
    payload["rejection"] = None
    with pytest.raises(ValueError, match="rejected result"):
        PrepareResult.from_json(payload)


def test_delivery_artifact_holds_its_fields() -> None:
    artifact = DeliveryArtifact(
        path=Path("delivery.jpg"),
        sha256="ab" * 32,
        size_bytes=10,
        dims=CANVAS,
        fingerprint="cd" * 32,
    )
    assert artifact.dims == CANVAS
    assert artifact.size_bytes == 10
    assert artifact.fingerprint == "cd" * 32


@pytest.mark.parametrize("canvas", [[20_001, 100], [100, 20_001], [5000, 4000]])
def test_request_rejects_an_oversized_canvas(canvas: list[int]) -> None:
    payload = PrepareRequest(
        source_path="in/source-0.bin",
        output_path="out/delivery-0.jpg",
        declared_format=ImageFormat.JPEG,
        fit_mode=FitMode.CONTAIN,
        background=Rgb(0, 0, 0),
        landscape_only=True,
        require_near_16_9=True,
    ).to_json()
    payload["canvas"] = list(canvas)
    with pytest.raises(ValueError, match="canvas"):
        PrepareRequest.from_json(payload)
