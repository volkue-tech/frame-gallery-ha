"""Publish only our own current-artwork state through the guarded Core proxy.

No helper/configuration/registry writes. The state is ephemeral, is not a registered
entity, and is distinct from the last-delivery caption. An ownership collision
fails closed instead of overwriting a user's entity.
"""

from __future__ import annotations

import html
import json
import re
from typing import Final

from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.ha.client import SupervisorHelperReader, _ReadFailed
from frame_gallery.net.policy import media_type
from frame_gallery.net.wire import IPAddress, TransportFailure, WireRequest
from frame_gallery.observer.model import (
    DEVICE_ID,
    FRESH_S,
    SLIDESHOW_FRESH_S,
    Evidence,
    Observation,
)
from frame_gallery.store.artwork_bindings import Binding
from frame_gallery.store.atomic import decode_json
from frame_gallery.store.delivery_associations import DeliveryAssociation

ENTITY_ID: Final = "sensor.frame_gallery_current_artwork"
PATH: Final = "/core/api/states/" + ENTITY_ID
OWNER_KEY: Final = "frame_gallery_owner"
_TOKEN: Final = re.compile(r"[\x21-\x7e]{1,4096}", re.ASCII)


class CurrentArtworkPublisher(SupervisorHelperReader):
    _authorization_refused = False

    @property
    def authorization_refused(self) -> bool:
        """Latch a rejected credential for the whole trusted service, not just polls."""
        return self._authorization_refused

    def publish(
        self,
        owner: str,
        observation: Observation,
        binding: Binding | DeliveryAssociation | None,
        deadline: Deadline,
    ) -> bool:
        token = self._token
        if token is None or _TOKEN.fullmatch(token) is None:
            return False
        if DEVICE_ID.fullmatch(owner) is None:
            raise ValueError("invalid state owner")
        if binding is not None and not binding.matches(observation):
            raise ValueError("caption does not match the observed TV image")
        attributes: dict[str, str | bool | int] = {
            OWNER_KEY: owner,
            "friendly_name": "Frame Gallery current artwork",
            "icon": "mdi:television-ambient-light",
            "background_mode": True,
        }
        if observation.content_id is not None:
            attributes["tv_content_id"] = observation.content_id
        if observation.evidence is Evidence.SLIDESHOW:
            attributes["confirmation_method"] = "slideshow_events"
            attributes["confirmation_max_age"] = int(SLIDESHOW_FRESH_S)
        elif observation.evidence is Evidence.CURRENT_STATE:
            attributes["confirmation_method"] = "current_state_read"
            attributes["confirmation_max_age"] = int(FRESH_S)
        status = observation.status.value
        if binding is not None:
            attributes["association_method"] = (
                "confirmed_upload"
                if isinstance(binding, DeliveryAssociation)
                else "verified_thumbnail"
            )
            attributes.update(
                {
                    "work_id": binding.work_id,
                    "title": binding.title,
                    "artist": binding.artist,
                    "source": binding.source,
                    "display_title": _markdown(binding.title),
                    "display_artist": _markdown(binding.artist),
                    "display_source": _markdown(binding.source),
                }
            )
            status = "artwork"
        elif status == "artwork":
            status = "unidentified"
        payload = json.dumps({"state": status, "attributes": attributes}).encode("utf-8")
        try:
            addresses = self._resolve(deadline)
            existing = self._exchange("GET", None, addresses[0], deadline)
            if existing is not None:
                attrs = existing.get("attributes")
                if not isinstance(attrs, dict) or attrs.get(OWNER_KEY) != owner:
                    return False
            self._exchange("POST", payload, addresses[0], deadline)
        except (_ReadFailed, TransportFailure, DeadlineExceeded, ValueError):
            return False
        return True

    def _exchange(
        self, method: str, body: bytes | None, address: IPAddress, deadline: Deadline
    ) -> dict[str, object] | None:
        headers = {
            "Host": "supervisor",
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Connection": "close",
        }
        if body is not None:
            headers.update({"Content-Type": "application/json", "Content-Length": str(len(body))})
        response = self._transport.open(
            WireRequest(
                address=address,
                host="supervisor",
                port=80,
                tls=False,
                target=PATH,
                headers=headers,
                method=method,
                body=body,
            ),
            connect_timeout=deadline.clamp(1.0),
            exchange_timeout=deadline.clamp(2.0),
        )
        try:
            if response.status in (401, 403):
                self._token = None
                self._authorization_refused = True
                raise _ReadFailed("observer authorization refused")
            if method == "GET" and response.status == 404:
                return None
            if response.status not in (200, 201):
                raise _ReadFailed("observer HTTP failure")
            if media_type(response.header("content-type")) != "application/json":
                raise _ReadFailed("observer response is not JSON")
            if response.header("content-encoding") not in (None, "identity"):
                raise _ReadFailed("observer encoded response refused")
            document = decode_json(self._read_body(response, deadline))
            if not isinstance(document, dict):
                raise ValueError("observer response must be an object")
            return document
        finally:
            response.close()


def _markdown(text: str) -> str:
    return re.sub(r"([\\`*_{}\[\]()#!|>~])", r"\\\1", html.escape(text, quote=True))
