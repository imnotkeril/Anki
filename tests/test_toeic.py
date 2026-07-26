from pathlib import Path

from jpvocab.apkg_reader import open_collection
from jpvocab.genanki_adapter import build_apkg
from jpvocab.toeic import TOEIC_NOTETYPE, build_note


def test_toeic_notetype_loaded():
    assert TOEIC_NOTETYPE.fields == ["Front", "Back"]
    assert TOEIC_NOTETYPE.css != ""
    assert TOEIC_NOTETYPE.deck_name == "TOEIC 1600 Essential Words"


def test_build_note_and_round_trip(tmp_path: Path):
    fields = build_note({
        "Front": "meeting",
        "Back": "встреча<br><br>The meeting was scheduled for Monday morning.<br>Встреча была запланирована на утро понедельника.",
    })
    assert len(fields) == 2

    out_path = tmp_path / "toeic_test.apkg"
    build_apkg([fields], deck_name=TOEIC_NOTETYPE.deck_name, out_path=out_path, notetype=TOEIC_NOTETYPE)
    con = open_collection(out_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    rows = cur.fetchall()
    assert len(rows) == 1
    assert rows[0][0].split("\x1f")[0] == "meeting"
