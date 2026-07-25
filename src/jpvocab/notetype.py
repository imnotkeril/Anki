import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Template:
    name: str
    qfmt: str
    afmt: str


@dataclass(frozen=True)
class NotetypeSnapshot:
    notetype_name: str
    fields: list[str]
    templates: list[Template]
    css: str
    deck_name: str


def _load() -> NotetypeSnapshot:
    path = Path(__file__).parent / "notetype_snapshot.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return NotetypeSnapshot(
        notetype_name=data["notetype_name"],
        fields=data["fields"],
        templates=[Template(**t) for t in data["templates"]],
        css=data["css"],
        deck_name=data["deck_name"],
    )


CORE_NOTETYPE = _load()
