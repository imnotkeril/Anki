from pathlib import Path

import genanki
from beartype import beartype

from jpvocab.notetype import CORE_NOTETYPE

# Fixed IDs so re-running the generator produces stable, mergeable output.
# genanki matches an existing notetype/deck by name on import, so these
# values don't need to match Anki's internal 64-bit ids.
_MODEL_ID = 1976543210
_DECK_ID = 1976543211


def _build_model() -> genanki.Model:
    return genanki.Model(
        _MODEL_ID,
        CORE_NOTETYPE.notetype_name,
        fields=[{"name": f} for f in CORE_NOTETYPE.fields],
        templates=[
            {"name": t.name, "qfmt": t.qfmt, "afmt": t.afmt}
            for t in CORE_NOTETYPE.templates
        ],
        css=CORE_NOTETYPE.css,
    )


@beartype
def build_apkg(fields_list: list[list[str]], deck_name: str, out_path: Path) -> Path:
    model = _build_model()
    deck = genanki.Deck(_DECK_ID, deck_name)
    for fields in fields_list:
        deck.add_note(genanki.Note(model=model, fields=fields))
    genanki.Package(deck).write_to_file(str(out_path))
    return out_path
