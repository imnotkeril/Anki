from dataclasses import dataclass
from pathlib import Path

from beartype import beartype


@dataclass(frozen=True)
class SentencePair:
    japanese: str
    english: str


class TatoebaLookup:
    @beartype
    def __init__(self, path: Path) -> None:
        self._pairs: list[SentencePair] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            jp, en = line.split("\t", maxsplit=1)
            self._pairs.append(SentencePair(japanese=jp, english=en))

    @beartype
    def find(self, expression: str) -> SentencePair | None:
        for pair in self._pairs:
            if expression in pair.japanese:
                return pair
        return None
