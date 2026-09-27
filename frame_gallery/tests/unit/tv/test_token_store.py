"""The television pairing token (tv/token_store.py, §12.2, §13.1)."""

from __future__ import annotations

import errno
import logging
import stat
from ipaddress import IPv4Address
from pathlib import Path

import pytest

from frame_gallery.errors import StateError
from frame_gallery.logs.redact import Redactor, set_active_redactor
from frame_gallery.store.atomic import Directory
from frame_gallery.tv.token_store import TokenStore, parse_token, token_file_name

HOST = IPv4Address("192.168.1.20")


@pytest.fixture
def data(tmp_path: Path) -> Path:
    root = tmp_path / "data"
    root.mkdir()
    return root


def token_path(data: Path) -> Path:
    return data / "tv" / "192-168-1-20.token"


class TestParsing:
    @pytest.mark.parametrize(
        ("data", "token"),
        [
            (b"12345678", "12345678"),
            (b"12345678\n", "12345678"),
            (b"  abcDEF09  \r\nsecond line", "abcDEF09"),
            (b"a" * 64, "a" * 64),
        ],
    )
    def test_valid_tokens(self, data: bytes, token: str) -> None:
        assert parse_token(data) == token

    @pytest.mark.parametrize(
        "data",
        [b"", b"\n", b"a" * 65, b"a" * 5, b"to-ken", b"tok en", "tökén".encode(), b"\xff\xfe"],
    )
    def test_invalid_tokens(self, data: bytes) -> None:
        assert parse_token(data) is None

    def test_the_file_name_follows_the_address(self) -> None:
        assert token_file_name(HOST) == "192-168-1-20.token"


class TestStore:
    def test_nothing_stored_yet(self, data: Path) -> None:
        assert TokenStore(data, HOST).load() is None

    def test_install_then_load(self, data: Path) -> None:
        store = TokenStore(data, HOST)
        store.install("12345678")
        assert token_path(data).read_bytes() == b"12345678\n"
        assert stat.S_IMODE(token_path(data).stat().st_mode) == 0o600
        assert stat.S_IMODE((data / "tv").stat().st_mode) == 0o700
        assert TokenStore(data, HOST).load() == "12345678"

    def test_only_the_current_address_keeps_a_token(self, data: Path) -> None:
        TokenStore(data, IPv4Address("10.0.0.5")).install("11111111")
        (data / "tv" / "notes.txt").write_text("not a token")
        TokenStore(data, HOST).install("22222222")
        assert sorted(p.name for p in (data / "tv").iterdir()) == [
            "192-168-1-20.token",
            "notes.txt",
        ]

    def test_a_malformed_token_is_never_stored(self, data: Path) -> None:
        with pytest.raises(StateError, match="unexpected form"):
            TokenStore(data, HOST).install("to ken")
        assert not (data / "tv").exists()

    def test_remove(self, data: Path) -> None:
        store = TokenStore(data, HOST)
        store.install("12345678")
        store.remove()
        store.remove()  # idempotent
        assert store.load() is None

    def test_remove_without_a_directory(self, data: Path) -> None:
        TokenStore(data, HOST).remove()
        assert not (data / "tv").exists()

    def test_an_invalid_stored_token_means_pairing_again(
        self, data: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        (data / "tv").mkdir()
        token_path(data).write_bytes(b"not a token!")
        with caplog.at_level(logging.WARNING, "frame_gallery.tv"):
            assert TokenStore(data, HOST).load() is None
        assert "invalid; pairing again" in caplog.text

    def test_a_linked_token_is_never_followed(
        self, data: Path, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        (tmp_path / "elsewhere").write_text("12345678")
        (data / "tv").mkdir()
        token_path(data).symlink_to(tmp_path / "elsewhere")
        with caplog.at_level(logging.WARNING, "frame_gallery.tv"):
            assert TokenStore(data, HOST).load() is None
        assert "not a regular file" in caplog.text

    def test_a_linked_token_directory_is_refused(self, data: Path, tmp_path: Path) -> None:
        (tmp_path / "elsewhere").mkdir()
        (data / "tv").symlink_to(tmp_path / "elsewhere")
        assert TokenStore(data, HOST).load() is None
        with pytest.raises(StateError, match="symbolic link"):
            TokenStore(data, HOST).install("12345678")
        assert list((tmp_path / "elsewhere").iterdir()) == []

    def test_tokens_are_registered_with_the_redactor(self, data: Path) -> None:
        redactor = Redactor()
        set_active_redactor(redactor)
        TokenStore(data, HOST).install("98765432")
        assert redactor.redact("token 98765432 seen") != "token 98765432 seen"
        other = Redactor()
        set_active_redactor(other)
        assert TokenStore(data, HOST).load() == "98765432"
        assert "98765432" not in other.redact("token 98765432 seen")

    def test_an_unlistable_directory_only_warns(
        self, data: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        def failing_names(_self: Directory, _limit: int) -> list[str]:
            raise OSError(errno.EIO, "io")

        monkeypatch.setattr(Directory, "names", failing_names)
        with caplog.at_level(logging.WARNING, "frame_gallery.tv"):
            TokenStore(data, HOST).install("12345678")
        assert "old television tokens were not removed (EIO)" in caplog.text
        assert token_path(data).exists()
