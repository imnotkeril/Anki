from pathlib import Path

import genanki
from beartype import beartype

from jpvocab.notetype import CORE_NOTETYPE, NotetypeSnapshot

# Fixed IDs so re-running the generator produces stable, mergeable output.
# genanki matches an existing notetype/deck by name on import, so these
# values don't need to match Anki's internal 64-bit ids.
_MODEL_ID = 1976543210
_DECK_ID = 1976543211


def _build_model(notetype: NotetypeSnapshot) -> genanki.Model:
    return genanki.Model(
        _MODEL_ID,
        notetype.notetype_name,
        fields=[{"name": f} for f in notetype.fields],
        templates=[
            {"name": t.name, "qfmt": t.qfmt, "afmt": t.afmt}
            for t in notetype.templates
        ],
        css=notetype.css,
    )


@beartype
def build_apkg(
    fields_list: list[list[str]],
    deck_name: str,
    out_path: Path,
    notetype: NotetypeSnapshot = CORE_NOTETYPE,
) -> Path:
    model = _build_model(notetype)
    deck = genanki.Deck(_DECK_ID, deck_name)
    for fields in fields_list:
        deck.add_note(genanki.Note(model=model, fields=fields))
    genanki.Package(deck).write_to_file(str(out_path))
    return out_path
