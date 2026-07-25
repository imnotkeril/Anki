from pathlib import Path

from beartype import beartype


@beartype
def parse_accents_file(path: Path) -> dict[tuple[str, str], list[int]]:
    entries: dict[tuple[str, str], list[int]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expression, reading, accents_raw = line.split("\t")
        accents = [int(a) for a in accents_raw.split(",")]
        entries[(expression, reading)] = accents
    return entries


class PitchLookup:
    @beartype
    def __init__(self, path: Path) -> None:
        self._entries = parse_accents_file(path)

    @beartype
    def get(self, expression: str, reading: str) -> list[int] | None:
        return self._entries.get((expression, reading))
