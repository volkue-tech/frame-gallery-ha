"""The honest User-Agent and courtesy header (§10, D-119 as amended)."""

from __future__ import annotations

import pytest

from frame_gallery import __version__
from frame_gallery.net.identity import PROJECT_CONTACT, ClientIdentity, project_identity
from frame_gallery.net.policy import check_header
from tests.support.net import PLACEHOLDER_CONTACT, TEST_IDENTITY


def test_headers_name_the_product_version_and_contact() -> None:
    assert TEST_IDENTITY.user_agent == f"FrameGallery/0.0.0-test (contact: {PLACEHOLDER_CONTACT})"
    assert TEST_IDENTITY.courtesy_agent == f"FrameGallery/0.0.0-test ({PLACEHOLDER_CONTACT})"
    check_header("User-Agent", TEST_IDENTITY.user_agent)
    check_header("AIC-User-Agent", TEST_IDENTITY.courtesy_agent)


def test_no_url_and_no_browser_impersonation() -> None:
    for value in (TEST_IDENTITY.user_agent, TEST_IDENTITY.courtesy_agent):
        assert "http" not in value
        assert "Mozilla" not in value


def test_the_production_identity_uses_the_approved_contact() -> None:
    # The address itself is not spelled out in any test (D-119 as amended).
    identity = project_identity()
    assert identity.contact == PROJECT_CONTACT
    assert identity.version == __version__
    assert identity.contact != PLACEHOLDER_CONTACT


@pytest.mark.parametrize(
    "contact",
    [
        "",
        "no-at-sign",
        "a@b",
        "a b@example.org",
        "a@example.org\r\nX-Injected: 1",
        "a@-example.org",
        "ä@example.org",
        "a@example.org>",
        "x" * 65 + "@example.org",
    ],
)
def test_invalid_contacts_are_refused(contact: str) -> None:
    with pytest.raises(ValueError, match="contact"):
        ClientIdentity("1.0", contact)


@pytest.mark.parametrize("version", ["", " 1", "1 0", "1\n", "v" * 40, "-1"])
def test_invalid_versions_are_refused(version: str) -> None:
    with pytest.raises(ValueError, match="version"):
        ClientIdentity(version, PLACEHOLDER_CONTACT)
