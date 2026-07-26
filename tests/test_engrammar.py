from pathlib import Path

from jpvocab.apkg_reader import open_collection
from jpvocab.genanki_adapter import build_apkg
from jpvocab.engrammar import EN_GRAMMAR_NOTETYPE, build_note


def test_en_grammar_notetype_loaded():
    assert EN_GRAMMAR_NOTETYPE.fields == ["Pattern", "Meaning", "Example", "ExampleRU", "Register"]
    assert EN_GRAMMAR_NOTETYPE.css != "" and "PLACEHOLDER" not in EN_GRAMMAR_NOTETYPE.css


def test_build_note_and_round_trip(tmp_path: Path):
    fields = build_note({
        "Pattern": "on the other hand",
        "Meaning": "с другой стороны",
        "Example": "Some prefer cities. <b>On the other hand</b>, others value quiet.",
        "ExampleRU": "Некоторые предпочитают города. С другой стороны, другие ценят тишину.",
        "Register": "formal / academic",
    })
    assert len(fields) == 5

    out_path = tmp_path / "engrammar_test.apkg"
    build_apkg([fields], deck_name="EN Grammar Collocations", out_path=out_path, notetype=EN_GRAMMAR_NOTETYPE)
    con = open_collection(out_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    rows = cur.fetchall()
    assert len(rows) == 1
    assert rows[0][0].split("\x1f")[0] == "on the other hand"
