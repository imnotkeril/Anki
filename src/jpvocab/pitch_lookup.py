import re
from pathlib import Path

from beartype import beartype

# Some kanjium entries tag alternate accents with a leading part-of-speech
# marker, e.g. "(副)0,(名)3" or "(代)1,2,(感)1". The marker is informational
# only (which POS that accent applies to); we keep just the trailing digits.
_TRAILING_DIGITS = re.compile(r"(\d+)$")


@beartype
def parse_accents_file(path: Path) -> dict[tuple[str, str], list[int]]:
    entries: dict[tuple[str, str], list[int]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expression, reading, accents_raw = line.split("\t")
        accents = []
        for segment in accents_raw.split(","):
            match = _TRAILING_DIGITS.search(segment)
            if match:
                accents.append(int(match.group(1)))
        entries[(expression, reading)] = accents
    return entries


class PitchLookup:
    @beartype
    def __init__(self, path: Path) -> None:
        self._entries = parse_accents_file(path)

    @beartype
    def get(self, expression: str, reading: str) -> list[int] | None:
        return self._entries.get((expression, reading))
