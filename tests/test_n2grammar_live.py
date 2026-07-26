from pathlib import Path

from jpvocab.apkg_reader import open_collection
from jpvocab.genanki_adapter import build_apkg
from jpvocab.n2grammar_live import N2_GRAMMAR_LIVE_NOTETYPE, build_note


def test_n2_grammar_live_notetype_loaded():
    assert N2_GRAMMAR_LIVE_NOTETYPE.fields == [
        "Expression",
        "ExpressionClean",
        "Reading",
        "Meaning",
        "Pattern",
        "Connection",
    ]
    assert N2_GRAMMAR_LIVE_NOTETYPE.css != ""
    assert N2_GRAMMAR_LIVE_NOTETYPE.deck_name == "Japanese Grammar::Shin Kanzen Master N2"


def test_build_note_and_round_trip(tmp_path: Path):
    fields = build_note({
        "Expression": "彼は失敗<b>にもかかわらず</b>諦めなかった。",
        "ExpressionClean": "彼は失敗にもかかわらず諦めなかった。",
        "Reading": "かれは しっぱいにもかかわらず あきらめなかった。",
        "Meaning": "Он не сдался, несмотря на неудачу.",
        "Pattern": "[сущ./гл.] + にもかかわらず",
        "Connection": (
            "<ruby>失敗<rt>しっぱい</rt></ruby> (сущ.) → 失敗にもかかわらず<br>"
            "<ruby>雨<rt>あめ</rt></ruby>が降る (гл.) → 雨が降るにもかかわらず"
        ),
    })
    assert len(fields) == 6

    out_path = tmp_path / "n2grammar_live_test.apkg"
    build_apkg(
        [fields],
        deck_name=N2_GRAMMAR_LIVE_NOTETYPE.deck_name,
        out_path=out_path,
        notetype=N2_GRAMMAR_LIVE_NOTETYPE,
    )
    con = open_collection(out_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    rows = cur.fetchall()
    assert len(rows) == 1
    assert "にもかかわらず" in rows[0][0].split("\x1f")[0]
