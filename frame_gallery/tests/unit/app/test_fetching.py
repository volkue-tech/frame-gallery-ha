"""The image fetcher routes local references to the library and remote ones
to the owning provider's gateway channel (§5, §10)."""

from __future__ import annotations

from pathlib import Path

import pytest

from frame_gallery.app.fetching import SourceFetcher
from frame_gallery.app.ports import FetchedImage, ImageFetcher
from frame_gallery.budget.allowance import Allowance
from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.filters import EffectiveFilters, FilterSet
from frame_gallery.domain import SourceKey
from frame_gallery.imaging.contract import ImageFormat
from frame_gallery.net.gateway import Gateway
from frame_gallery.net.policy import HostPolicy
from frame_gallery.providers.contract import (
    DiscoveryContext,
    ImageRef,
    ImageRefKind,
    SourceError,
    SourceErrorKind,
)
from frame_gallery.providers.local_media import LocalMediaProvider
from frame_gallery.randomness import SeededRandomSource
from tests.support.clock import FakeClock
from tests.support.images import marked, save_jpeg
from tests.support.net import TEST_IDENTITY, FakeResolver, FakeTransport, image_response

MUSEUM = HostPolicy("aaa", frozenset({"api.museum.example", "img.museum.example"}))
OTHER = HostPolicy("bbb", frozenset({"api.other.example"}))


class Rig:
    def __init__(self, tmp_path: Path) -> None:
        self.clock = FakeClock()
        self.transport = FakeTransport(clock=self.clock)
        gateway = Gateway(
            resolver=FakeResolver(),
            transport=self.transport,
            clock=self.clock,
            random=SeededRandomSource(1),
            identity=TEST_IDENTITY,
        )
        self.museum = gateway.channel(MUSEUM, metadata_allowance=Allowance("m", 15))
        self.other = gateway.channel(OTHER, metadata_allowance=Allowance("m", 15))
        root = tmp_path / "library"
        root.mkdir()
        self.image = save_jpeg(marked((64, 36)), root / "a.jpg")
        self.local = LocalMediaProvider(root=root, preview_dir=tmp_path / "preview")
        self.fetcher = SourceFetcher(local=self.local, channels=[self.museum, self.other])
        self.inbox = tmp_path / "in"
        self.inbox.mkdir()

    def deadline(self) -> Deadline:
        return Deadline.after(self.clock, 20, "download")


@pytest.fixture
def rig(tmp_path: Path) -> Rig:
    return Rig(tmp_path)


def test_local_references_are_copied(rig: Rig) -> None:
    filters = EffectiveFilters(
        SourceKey.LOCAL_MEDIA, None, None, None, None, (), FilterSet(SourceKey.LOCAL_MEDIA)
    )
    context = DiscoveryContext(rig.deadline(), SeededRandomSource(1))
    (candidate,) = list(rig.local.iter_candidates(filters, context))
    fetched = rig.fetcher.fetch(
        rig.local.full_ref(candidate), rig.inbox / "source-0.bin", rig.deadline()
    )
    assert fetched == FetchedImage(
        rig.inbox / "source-0.bin", rig.image.stat().st_size, ImageFormat.JPEG
    )
    assert rig.transport.calls == []


@pytest.mark.parametrize(
    ("media", "expected"), [("image/jpeg", ImageFormat.JPEG), ("image/png", ImageFormat.PNG)]
)
def test_remote_references_go_to_the_owning_channel(
    rig: Rig, media: str, expected: ImageFormat
) -> None:
    rig.transport.add(image_response(b"image-bytes", media))
    ref = ImageRef(ImageRefKind.REMOTE, "https://img.museum.example/x/y.jpg")
    fetched = rig.fetcher.fetch(ref, rig.inbox / "source-1.bin", rig.deadline())
    assert fetched.declared_format is expected
    assert fetched.size_bytes == len(b"image-bytes")
    assert rig.transport.calls[0].request.host == "img.museum.example"


def test_a_stopped_provider_stops_its_downloads(rig: Rig) -> None:
    rig.museum._stopped = True
    ref = ImageRef(ImageRefKind.REMOTE, "https://img.museum.example/x.jpg")
    with pytest.raises(SourceError) as excinfo:
        rig.fetcher.fetch(ref, rig.inbox / "a", rig.deadline())
    assert excinfo.value.kind is SourceErrorKind.STOPPED


@pytest.mark.parametrize(
    "url",
    [
        "https://unknown.example/x.jpg",
        "http://img.museum.example/x.jpg",
        "https://img.museum.example:8443/x.jpg",
    ],
)
def test_urls_no_channel_owns_are_refused(rig: Rig, url: str) -> None:
    with pytest.raises(SourceError) as excinfo:
        rig.fetcher.fetch(ImageRef(ImageRefKind.REMOTE, url), rig.inbox / "a", rig.deadline())
    assert excinfo.value.kind is SourceErrorKind.UNEXPECTED_FORMAT
    assert rig.transport.calls == []


def test_without_a_library_local_references_are_not_found(rig: Rig) -> None:
    fetcher = SourceFetcher(channels=[rig.museum])
    with pytest.raises(SourceError) as excinfo:
        fetcher.fetch(ImageRef(ImageRefKind.LOCAL, str(rig.image)), rig.inbox / "a", rig.deadline())
    assert excinfo.value.kind is SourceErrorKind.NOT_FOUND


def test_channels_may_not_share_hosts(rig: Rig) -> None:
    with pytest.raises(ValueError, match="share a host"):
        SourceFetcher(channels=[rig.museum, rig.museum])


def test_conforms_to_the_port(rig: Rig) -> None:
    fetcher: ImageFetcher = rig.fetcher
    assert fetcher is rig.fetcher
