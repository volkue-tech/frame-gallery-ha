"""The image fetcher: one port over the local library and the providers'
gateway channels (§5, §10, §20.2).

A local reference is copied by the local media provider, which accepts only
files its own scan offered. A remote reference goes to the channel whose host
policy owns the URL, so a download is paced, bounded, and stopped exactly
like that provider's metadata requests (D-115). The rendition's format comes
from the file extension (local) or the ``Content-Type`` (remote); the runner
then checks it against the file's own signature.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Final

from frame_gallery.app.ports import FetchedImage
from frame_gallery.budget.deadline import Deadline
from frame_gallery.imaging.contract import ImageFormat
from frame_gallery.net.gateway import ProviderChannel
from frame_gallery.net.policy import PolicyViolation, validate_url
from frame_gallery.providers.contract import ImageRef, ImageRefKind, SourceError, SourceErrorKind
from frame_gallery.providers.local_media import LocalMediaProvider

_FORMATS: Final = {"image/jpeg": ImageFormat.JPEG, "image/png": ImageFormat.PNG}


class SourceFetcher:
    """The production :class:`~frame_gallery.app.ports.ImageFetcher`."""

    def __init__(
        self,
        *,
        local: LocalMediaProvider | None = None,
        channels: Sequence[ProviderChannel] = (),
    ) -> None:
        hosts = [host for channel in channels for host in channel.policy.hosts]
        if len(hosts) != len(set(hosts)):
            msg = "two provider channels share a host"
            raise ValueError(msg)
        self._local = local
        self._channels = tuple(channels)

    def fetch(self, ref: ImageRef, destination: Path, deadline: Deadline) -> FetchedImage:
        if ref.kind is ImageRefKind.LOCAL:
            if self._local is None:
                raise SourceError(SourceErrorKind.NOT_FOUND, "no local library in this run")
            copy = self._local.fetch(ref, destination, deadline)
            return FetchedImage(copy.path, copy.size_bytes, copy.declared_format)
        channel = self._channel_for(ref.location)
        download = channel.download(ref.location, destination, deadline)
        return FetchedImage(download.path, download.size_bytes, _FORMATS[download.media_type])

    def _channel_for(self, url: str) -> ProviderChannel:
        for channel in self._channels:
            try:
                validate_url(url, channel.policy)
            except PolicyViolation:
                continue
            return channel
        raise SourceError(
            SourceErrorKind.UNEXPECTED_FORMAT, "no provider's host policy allows the URL"
        )
