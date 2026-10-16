from __future__ import annotations

import hashlib
from types import SimpleNamespace
from typing import Any

import pytest

from frame_gallery.isolation.executor import JsonObject
from frame_gallery.observer.model import Observation, Status
from frame_gallery.tv import samsung_task as module
from frame_gallery.tv.samsung_task import TvLibrary

IDENTITY = "uuid:synthetic-tv-one"
DEVICE = hashlib.sha256(IDENTITY.encode()).hexdigest()
HOST = "192.168.1.20"
TOKEN = "12345678"  # noqa: S105


class Unauthorized(Exception):
    pass


class Art:
    def __init__(self) -> None:
        self.info: Any = {"device": {"id": IDENTITY}}
        self.mode: list[str] = ["on", "on"]
        self.current: list[Any] = [{"content_id": "MY_TEST"}, {"content_id": "MY_TEST"}]
        self.thumbnails: Any = {"MY_TEST.jpg": bytearray(b"synthetic thumbnail")}
        self.connection: Any = None
        self.requests: list[str] = []
        self.opened = self.closed = 0
        self.failure: Exception | None = None
        self.bad_method = False
        self.read_size = 5

    def _get_rest_api(self) -> Art:
        return self

    def rest_device_info(self) -> Any:
        return self.info

    def _send_art_request(self, data: dict[str, Any]) -> None:
        self.requests.append(data["request"])

    def _recv_exact(self, _socket: object, size: int) -> bytes:
        return b"x" * size

    def open(self) -> None:
        self.opened += 1
        if self.failure is not None:
            raise self.failure
        self.connection = self

    def shutdown(self) -> None:
        self.closed += 1

    def get_artmode(self) -> str:
        self._send_art_request(
            {"request": "set_artmode_status" if self.bad_method else "get_artmode_status"}
        )
        return self.mode.pop(0)

    def get_current(self) -> Any:
        self._send_art_request({"request": "get_current_artwork"})
        return self.current.pop(0)

    def get_thumbnail(self, content: str, *, as_dict: bool) -> Any:
        assert content == "MY_TEST"
        assert as_dict
        self._send_art_request({"request": "get_thumbnail"})
        self._recv_exact(None, self.read_size)
        return self.thumbnails


def library(art: Art) -> TvLibrary:
    return TvLibrary(
        art_class=lambda *_args, **_kwargs: art,
        websocket=SimpleNamespace(),
        unauthorized=Unauthorized,
        response_error=ValueError,
        websocket_timeout=TimeoutError,
        transport_errors=(OSError,),
    )


def observe(art: Art) -> JsonObject:
    return module.run_observation(library(art), HOST, TOKEN, DEVICE)


def test_fixed_getters_and_exact_targeted_thumbnail() -> None:
    art = Art()
    result = observe(art)
    encoded = result.pop("thumbnail")
    assert isinstance(encoded, str)
    seen = Observation.from_json(result)
    assert seen == Observation(
        Status.UNIDENTIFIED, DEVICE, "MY_TEST", hashlib.sha256(b"synthetic thumbnail").hexdigest()
    )
    assert art.requests == [
        "get_artmode_status",
        "get_current_artwork",
        "get_thumbnail",
        "get_current_artwork",
        "get_artmode_status",
    ]
    assert art.opened == art.closed == 1


@pytest.mark.parametrize(
    "info",
    [
        {},
        {"device": {"id": None}},
        {"device": {"id": "wrong"}},
        {"device": {"id": "x" * 129}},
        None,
    ],
)
def test_unknown_device_is_not_connected(info: object) -> None:
    art = Art()
    art.info = info
    assert observe(art)["status"] == "unavailable"
    assert art.opened == 0


def test_art_mode_off_makes_no_content_or_thumbnail_request() -> None:
    art = Art()
    art.mode = ["off"]
    assert observe(art)["status"] == "tv_in_use"
    assert art.requests == ["get_artmode_status"]


@pytest.mark.parametrize("current", [None, {}, {"content_id": 3}, {"content_id": "../bad"}])
def test_bad_current_ids_fail_closed(current: object) -> None:
    art = Art()
    art.current = [current]
    assert observe(art)["status"] == "unavailable"


@pytest.mark.parametrize(
    "value",
    [
        None,
        {},
        {"WRONG.jpg": b"x"},
        {"MY_TEST.jpg": None},
        {"MY_TEST.jpg": b""},
        {"MY_TEST.jpg": b"x" * (40 * 1024 + 1)},
        {"MY_TEST.jpg": b"x", "other.jpg": b"y"},
    ],
)
def test_untrusted_thumbnails_are_limited(value: object) -> None:
    art = Art()
    art.thumbnails = value
    assert observe(art)["status"] == "unavailable"
    assert art.closed == 1


@pytest.mark.parametrize("size", [-1, True, 40 * 1024 + 1])
def test_d2d_lengths_are_bounded_before_read(size: int) -> None:
    art = Art()
    art.read_size = size
    assert observe(art)["status"] == "unavailable"


def test_write_methods_are_rejected_before_library_send() -> None:
    art = Art()
    art.bad_method = True
    assert observe(art)["status"] == "unavailable"
    assert art.requests == []


def test_changing_id_or_mode_does_not_publish_a_snapshot() -> None:
    art = Art()
    art.current[-1] = {"content_id": "MY_CHANGED"}
    assert observe(art)["status"] == "unavailable"
    art = Art()
    art.mode[-1] = "off"
    assert observe(art)["status"] == "unavailable"


@pytest.mark.parametrize(
    ("error", "status"),
    [(Unauthorized(TOKEN), "not_authorized"), (TimeoutError(TOKEN), "unavailable")],
)
def test_failures_do_not_retry_or_expose_secret(error: Exception, status: str) -> None:
    art = Art()
    art.failure = error
    result = observe(art)
    assert result["status"] == status
    assert TOKEN not in str(result)
    assert art.opened == 1


def test_worker_validates_before_loading_library(monkeypatch: pytest.MonkeyPatch) -> None:
    art = Art()
    monkeypatch.setattr(module, "load_library", lambda: library(art))
    undone: list[bool] = []
    monkeypatch.setattr(
        module,
        "install_connect_guard",
        lambda _host: SimpleNamespace(undo=lambda: undone.append(True)),
    )
    payload: JsonObject = {
        "host": HOST,
        "token": TOKEN,
        "device_id": DEVICE,
        "tokenless_grant": False,
        "enroll_device": False,
    }
    assert module.observe_task(payload)["status"] == "unidentified"
    assert undone == [True]
    changes: list[JsonObject] = [
        {"host": 1},
        {"token": None},
        {"token": "bad"},
        {"tokenless_grant": None},
        {"tokenless_grant": 1},
        {"tokenless_grant": "true"},
        {"tokenless_grant": True},
        {"device_id": None},
        {"device_id": "bad"},
        {"enroll_device": True},
        {"enroll_device": None},
        {"enroll_device": 1},
        {"enroll_device": "true"},
        {"extra": 1},
    ]
    for change in changes:
        with pytest.raises(ValueError, match="invalid read-only TV request"):
            module.observe_task(dict(payload, **change))


def test_tokenless_worker_requires_explicit_grant_and_keeps_getter_guards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    art = Art()
    creations: list[dict[str, Any]] = []

    def create(_host: str, **kwargs: Any) -> Art:
        creations.append(kwargs)
        return art

    pinned = library(art)
    pinned = TvLibrary(
        create,
        pinned.websocket,
        pinned.unauthorized,
        pinned.response_error,
        pinned.websocket_timeout,
        pinned.transport_errors,
    )
    monkeypatch.setattr(module, "load_library", lambda: pinned)
    undone: list[bool] = []
    monkeypatch.setattr(
        module,
        "install_connect_guard",
        lambda _host: SimpleNamespace(undo=lambda: undone.append(True)),
    )
    payload: JsonObject = {
        "host": HOST,
        "token": None,
        "device_id": DEVICE,
        "tokenless_grant": True,
        "enroll_device": False,
    }
    assert module.observe_task(payload)["status"] == "unidentified"
    assert creations == [
        {"token": None, "port": 8002, "timeout": 2.0, "key_press_delay": 0, "name": "frame_gallery"}
    ]
    assert undone == [True]
    assert art.opened == art.closed == 1
    assert all(request in module._READ_REQUESTS for request in art.requests)

    del payload["tokenless_grant"]
    with pytest.raises(ValueError, match="invalid read-only TV request"):
        module.observe_task(payload)
    assert len(creations) == 1


@pytest.mark.parametrize("tokenless", [False, True])
def test_enrollment_is_an_explicit_validated_worker_contract(
    monkeypatch: pytest.MonkeyPatch, tokenless: bool
) -> None:
    art = Art()
    monkeypatch.setattr(module, "load_library", lambda: library(art))
    monkeypatch.setattr(
        module, "install_connect_guard", lambda _host: SimpleNamespace(undo=lambda: None)
    )
    payload: JsonObject = {
        "host": HOST,
        "token": None if tokenless else TOKEN,
        "device_id": None,
        "tokenless_grant": tokenless,
        "enroll_device": True,
    }
    assert module.observe_task(payload)["device_id"] == DEVICE
    assert art.opened == art.closed == 1
    assert art.requests == [
        "get_artmode_status",
        "get_current_artwork",
        "get_thumbnail",
        "get_current_artwork",
        "get_artmode_status",
    ]
    payload["enroll_device"] = False
    with pytest.raises(ValueError, match="invalid read-only TV request"):
        module.observe_task(payload)
    assert art.opened == 1
