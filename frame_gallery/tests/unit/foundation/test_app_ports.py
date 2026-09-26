"""The value types of the runner's ports (§5, §20.2, D-107)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from frame_gallery.app.ports import (
    FetchedImage,
    ProviderBinding,
    PublishError,
    WorkspacePaths,
)
from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.filters import EffectiveFilters
from frame_gallery.domain import Size, SourceKey
from frame_gallery.imaging.contract import ImageFormat
from frame_gallery.providers.contract import (
    Candidate,
    Capabilities,
    DimensionSource,
    DiscoveryContext,
    ImageRef,
    ImageRefKind,
)


class _Provider:
    """A structural ``Provider`` that offers nothing."""

    @property
    def key(self) -> str:
        return "cma"

    def capabilities(self) -> Capabilities:
        return Capabilities(SourceKey.CLEVELAND_MUSEUM_OF_ART, "cma", dims_in_metadata=True)

    def iter_candidates(
        self, filters: EffectiveFilters, ctx: DiscoveryContext
    ) -> Iterator[Candidate]:
        return iter(())

    def full_ref(self, candidate: Candidate) -> ImageRef:
        return ImageRef(ImageRefKind.REMOTE, "https://images.example.invalid/print.jpg")


class _Probe:
    """A structural ``DimensionProbe`` that never learns anything."""

    @property
    def source(self) -> DimensionSource:
        return DimensionSource.REMOTE_PROBE

    def measure(self, candidate: Candidate, deadline: Deadline) -> Size | None:
        return None


def test_fetched_image(tmp_path: Path) -> None:
    image = FetchedImage(
        path=tmp_path / "in" / "source.bin", size_bytes=1024, declared_format=ImageFormat.PNG
    )
    assert image.path.name == "source.bin"
    assert image.size_bytes == 1024
    assert image.declared_format is ImageFormat.PNG


def test_provider_binding_defaults_to_no_probe() -> None:
    provider = _Provider()
    binding = ProviderBinding(provider)
    assert binding.provider is provider
    assert binding.probe is None
    assert binding.provider.key == "cma"
    assert binding.provider.capabilities().dims_in_metadata


def test_provider_binding_with_a_probe() -> None:
    probe = _Probe()
    binding = ProviderBinding(_Provider(), probe=probe)
    assert binding.probe is probe
    assert binding.probe.source is DimensionSource.REMOTE_PROBE


def test_workspace_paths(tmp_path: Path) -> None:
    paths = WorkspacePaths(root=tmp_path, inbox=tmp_path / "in", outbox=tmp_path / "out")
    assert paths.inbox.parent == paths.root
    assert paths.outbox.parent == paths.root


def test_publish_error_is_an_exception() -> None:
    error = PublishError("preview directory unavailable")
    assert isinstance(error, Exception)
    assert str(error) == "preview directory unavailable"
