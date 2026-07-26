from pathlib import Path

from jpvocab.apkg_reader import open_collection
from jpvocab.genanki_adapter import build_apkg
from jpvocab.envocab import EN_VOCAB_NOTETYPE, build_note


def test_en_vocab_notetype_loaded():
    assert EN_VOCAB_NOTETYPE.fields == [
        "Word",
        "Transcription",
        "POS",
        "Meaning",
        "ExampleEN",
        "ExampleRU",
    ]
    assert EN_VOCAB_NOTETYPE.css != "" and "PLACEHOLDER" not in EN_VOCAB_NOTETYPE.css
    assert len(EN_VOCAB_NOTETYPE.templates) == 1


def test_build_note_and_round_trip(tmp_path: Path):
    fields = build_note(
        {
            "Word": "collateral",
            "Transcription": "/kəˈlætərəl/",
            "POS": "noun",
            "Meaning": "залог, обеспечение",
            "ExampleEN": "The bank asked for <b>collateral</b>.",
            "ExampleRU": "Банк потребовал залог.",
        }
    )
    assert len(fields) == 6

    out_path = tmp_path / "envocab_test.apkg"
    build_apkg(
        [fields],
        deck_name="EN Vocab",
        out_path=out_path,
        notetype=EN_VOCAB_NOTETYPE,
    )
    con = open_collection(out_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    rows = cur.fetchall()
    assert len(rows) == 1
    assert rows[0][0].split("\x1f")[0] == "collateral"
