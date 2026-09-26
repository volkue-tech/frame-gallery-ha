"""The provider contract and the rights allowlist (§9.1, D-134)."""

from __future__ import annotations

import pytest

from frame_gallery.budget.deadline import Deadline
from frame_gallery.domain import Size, SourceKey
from frame_gallery.errors import FrameGalleryError
from frame_gallery.providers.contract import (
    NATIVE_ID_PATTERN,
    PROVIDER_KEY_PATTERN,
    QUALIFIED_ID_MAX_LENGTH,
    Attribution,
    Candidate,
    Capabilities,
    DimensionSource,
    DiscoveryContext,
    ImageRef,
    ImageRefKind,
    SourceError,
    SourceErrorKind,
)
from frame_gallery.providers.rights import ALLOWED_RIGHTS, RightsBasis
from frame_gallery.randomness import SeededRandomSource
from tests.support.clock import FakeClock


def _candidate(
    provider_key: str = "aic",
    native_id: str = "27992",
    *,
    dims: Size | None = None,
) -> Candidate:
    return Candidate(
        provider_key=provider_key,
        native_id=native_id,
        rights_basis=RightsBasis.CC0,
        rights_field="is_public_domain",
        attribution=Attribution(title="Invented title", creator="Invented creator"),
        dims=dims,
    )


class TestCandidate:
    @pytest.mark.parametrize("provider_key", ["ab", "aic", "cma", "local", "a" * 16])
    def test_accepts_valid_provider_keys(self, provider_key: str) -> None:
        assert _candidate(provider_key).provider_key == provider_key

    @pytest.mark.parametrize(
        "provider_key", ["", "a", "a" * 17, "AIC", "Aic", "a1", "a-b", "a_b", "aic:", " aic", "aïc"]
    )
    def test_rejects_invalid_provider_keys(self, provider_key: str) -> None:
        with pytest.raises(ValueError, match="invalid provider key"):
            _candidate(provider_key)

    @pytest.mark.parametrize(
        "native_id", ["1", "27992", "abc", "A", "a.b_c:d-e", "0.1", "x:y:z", "Z9-"]
    )
    def test_accepts_valid_native_ids(self, native_id: str) -> None:
        assert _candidate(native_id=native_id).native_id == native_id

    @pytest.mark.parametrize(
        "native_id",
        ["", ".a", "-a", "_a", ":a", "a b", "a/b", "a\\b", "a\n", "a?b=c", "é", "a#b", "a%20"],
    )
    def test_rejects_invalid_native_ids(self, native_id: str) -> None:
        with pytest.raises(ValueError, match="invalid native identifier"):
            _candidate(native_id=native_id)

    def test_qualified_id_format(self) -> None:
        assert _candidate("cma", "94979").qualified_id == "cma:94979"

    def test_qualified_id_of_exactly_200_characters_is_accepted(self) -> None:
        assert QUALIFIED_ID_MAX_LENGTH == 200
        native_id = "x" * (200 - len("aic:"))
        candidate = _candidate("aic", native_id)
        assert len(candidate.qualified_id) == 200

    def test_qualified_id_of_201_characters_is_rejected(self) -> None:
        native_id = "x" * (201 - len("aic:"))
        assert NATIVE_ID_PATTERN.fullmatch(native_id) is not None
        with pytest.raises(ValueError, match="qualified identifier too long"):
            _candidate("aic", native_id)

    def test_length_limit_applies_to_the_longest_provider_key(self) -> None:
        key = "a" * 16
        assert len(_candidate(key, "7" * (200 - 17)).qualified_id) == 200
        with pytest.raises(ValueError, match="too long"):
            _candidate(key, "7" * (201 - 17))

    def test_carries_its_fields(self) -> None:
        candidate = _candidate(dims=Size(3000, 1700))
        assert candidate.rights_basis is RightsBasis.CC0
        assert candidate.rights_field == "is_public_domain"
        assert candidate.attribution.title == "Invented title"
        assert candidate.dims == Size(3000, 1700)
        assert candidate == _candidate(dims=Size(3000, 1700))

    def test_patterns_are_used_as_full_matches(self) -> None:
        assert PROVIDER_KEY_PATTERN.fullmatch("aic") is not None
        assert PROVIDER_KEY_PATTERN.fullmatch("aic1") is None
        assert NATIVE_ID_PATTERN.fullmatch("a b") is None


class TestSmallTypes:
    def test_attribution_defaults_to_nothing(self) -> None:
        attribution = Attribution()
        assert (
            attribution.title,
            attribution.creator,
            attribution.date_text,
            attribution.credit_line,
            attribution.detail_url,
        ) == (None, None, None, None, None)

    def test_image_ref(self) -> None:
        ref = ImageRef(ImageRefKind.REMOTE, "https://images.example.invalid/1.jpg")
        assert ref.kind is ImageRefKind.REMOTE
        assert [kind.value for kind in ImageRefKind] == ["remote", "local"]

    def test_dimension_sources(self) -> None:
        assert [source.value for source in DimensionSource] == ["remote_probe", "local_inspection"]

    def test_capabilities(self) -> None:
        capabilities = Capabilities(SourceKey.CLEVELAND_MUSEUM_OF_ART, "cma", dims_in_metadata=True)
        assert capabilities.provider_key == SourceKey.CLEVELAND_MUSEUM_OF_ART.provider_key

    def test_discovery_context(self) -> None:
        clock = FakeClock()
        deadline = Deadline.after(clock, 30.0, "discovery")
        random = SeededRandomSource(1)
        context = DiscoveryContext(deadline=deadline, random=random)
        assert context.deadline is deadline
        assert context.random is random


class TestSourceError:
    @pytest.mark.parametrize("kind", list(SourceErrorKind))
    def test_only_not_found_is_not_a_transport_failure(self, kind: SourceErrorKind) -> None:
        error = SourceError(kind)
        assert error.is_transport_failure is (kind is not SourceErrorKind.NOT_FOUND)

    def test_kinds(self) -> None:
        assert [kind.value for kind in SourceErrorKind] == [
            "transport",
            "timeout",
            "http_error",
            "stopped",
            "not_found",
            "over_cap",
            "unexpected_format",
        ]

    def test_message_without_detail(self) -> None:
        error = SourceError(SourceErrorKind.TIMEOUT)
        assert str(error) == "timeout"
        assert error.kind is SourceErrorKind.TIMEOUT
        assert error.detail == ""

    def test_message_with_detail(self) -> None:
        error = SourceError(SourceErrorKind.HTTP_ERROR, "status 503")
        assert str(error) == "http_error: status 503"
        assert error.detail == "status 503"

    def test_is_a_frame_gallery_error(self) -> None:
        assert isinstance(SourceError(SourceErrorKind.STOPPED), FrameGalleryError)


class TestRights:
    def test_bases(self) -> None:
        assert [basis.value for basis in RightsBasis] == ["user_supplied", "cc0"]

    def test_every_source_has_an_allowlist(self) -> None:
        assert set(ALLOWED_RIGHTS) == set(SourceKey)

    def test_local_media_is_user_supplied_only(self) -> None:
        assert ALLOWED_RIGHTS[SourceKey.LOCAL_MEDIA] == frozenset({RightsBasis.USER_SUPPLIED})

    @pytest.mark.parametrize(
        "source", [SourceKey.ART_INSTITUTE_CHICAGO, SourceKey.CLEVELAND_MUSEUM_OF_ART]
    )
    def test_museums_are_cc0_only(self, source: SourceKey) -> None:
        assert ALLOWED_RIGHTS[source] == frozenset({RightsBasis.CC0})
        assert RightsBasis.USER_SUPPLIED not in ALLOWED_RIGHTS[source]
