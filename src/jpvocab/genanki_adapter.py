import hashlib
from pathlib import Path

import genanki
from beartype import beartype

from jpvocab.notetype import CORE_NOTETYPE, NotetypeSnapshot


def _stable_id(seed: str) -> int:
    """Derive a stable, deterministic id in genanki's valid range (1<<30 to 1<<31)
    from a seed string, so re-running the generator for the same notetype produces
    the same id (for merge-by-name stability) while different notetypes/decks get
    different ids (avoiding cross-notetype id collisions when multiple .apkg files
    are imported into the same collection)."""
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return (1 << 30) + (int(digest, 16) % ((1 << 31) - (1 << 30)))


def _build_model(notetype: NotetypeSnapshot) -> genanki.Model:
    return genanki.Model(
        _stable_id(notetype.notetype_name),
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
    deck = genanki.Deck(_stable_id(deck_name), deck_name)
    for fields in fields_list:
        deck.add_note(genanki.Note(model=model, fields=fields))
    genanki.Package(deck).write_to_file(str(out_path))
    return out_path
