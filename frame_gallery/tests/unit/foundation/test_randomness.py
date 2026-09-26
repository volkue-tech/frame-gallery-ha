"""Injected randomness (§8.2, §20.2)."""

from __future__ import annotations

import pytest

from frame_gallery.randomness import RandomSource, SeededRandomSource, SystemRandomSource


def _draw(source: RandomSource) -> tuple[list[float], list[int], list[object]]:
    floats = [source.random() for _ in range(20)]
    ints = [source.randrange(1000) for _ in range(20)]
    items: list[object] = list(range(30))
    source.shuffle(items)
    return floats, ints, items


class TestSeededRandomSource:
    def test_same_seed_gives_identical_results(self) -> None:
        assert _draw(SeededRandomSource(42)) == _draw(SeededRandomSource(42))

    def test_different_seeds_give_different_results(self) -> None:
        assert _draw(SeededRandomSource(1)) != _draw(SeededRandomSource(2))

    def test_sequence_continues_across_operations(self) -> None:
        source = SeededRandomSource(7)
        first = source.random()
        second = source.random()
        assert first != second

    def test_ranges(self) -> None:
        source = SeededRandomSource(3)
        for _ in range(200):
            assert 0.0 <= source.random() < 1.0
            assert 0 <= source.randrange(5) < 5
        assert source.randrange(1) == 0

    def test_shuffle_keeps_every_item(self) -> None:
        source = SeededRandomSource(9)
        items: list[object] = ["a", "b", "c", "d", "e", "f"]
        source.shuffle(items)
        assert sorted(str(item) for item in items) == ["a", "b", "c", "d", "e", "f"]

    @pytest.mark.parametrize("stop", [0, -3])
    def test_randrange_rejects_an_empty_range(self, stop: int) -> None:
        with pytest.raises(ValueError, match="empty range"):
            SeededRandomSource(1).randrange(stop)


class TestSystemRandomSource:
    def test_satisfies_the_protocol(self) -> None:
        source: RandomSource = SystemRandomSource()
        floats, ints, items = _draw(source)
        assert all(0.0 <= value < 1.0 for value in floats)
        assert all(0 <= value < 1000 for value in ints)
        assert sorted(items, key=str) == sorted(range(30), key=str)

    def test_ranges(self) -> None:
        source = SystemRandomSource()
        for _ in range(200):
            assert 0.0 <= source.random() < 1.0
            assert 0 <= source.randrange(3) < 3
        assert source.randrange(1) == 0

    def test_shuffle_keeps_every_item(self) -> None:
        source = SystemRandomSource()
        items: list[object] = [1, 2, 3, 4, 5]
        source.shuffle(items)
        assert sorted(str(item) for item in items) == ["1", "2", "3", "4", "5"]

    def test_randrange_rejects_an_empty_range(self) -> None:
        with pytest.raises(ValueError, match="empty range"):
            SystemRandomSource().randrange(0)
