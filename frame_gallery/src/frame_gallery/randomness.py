"""Injected randomness (§8.2, §20.2).

Every random choice in the run goes through a :class:`RandomSource`, so tests
can use a seeded source and obtain identical results on every run. None of
these choices is security-relevant.
"""

from __future__ import annotations

import random
from collections.abc import MutableSequence
from typing import Protocol


class RandomSource(Protocol):
    """The random operations the core may use."""

    def random(self) -> float:
        """A float in ``[0.0, 1.0)``."""
        ...

    def randrange(self, stop: int) -> int:
        """An integer in ``[0, stop)``; ``stop`` must be positive."""
        ...

    def shuffle[T](self, items: MutableSequence[T]) -> None:
        """Shuffle ``items`` in place."""
        ...


class SeededRandomSource:
    """A deterministic source for tests and reproducible diagnostics."""

    def __init__(self, seed: int) -> None:
        self._random = random.Random(seed)  # noqa: S311 - not used for security

    def random(self) -> float:
        return self._random.random()

    def randrange(self, stop: int) -> int:
        return self._random.randrange(stop)

    def shuffle[T](self, items: MutableSequence[T]) -> None:
        self._random.shuffle(items)


class SystemRandomSource:
    """The production source, seeded from the operating system."""

    def __init__(self) -> None:
        self._random = random.SystemRandom()

    def random(self) -> float:
        return self._random.random()

    def randrange(self, stop: int) -> int:
        return self._random.randrange(stop)

    def shuffle[T](self, items: MutableSequence[T]) -> None:
        self._random.shuffle(items)
