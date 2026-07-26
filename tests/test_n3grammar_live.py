from pathlib import Path

from jpvocab.apkg_reader import open_collection
from jpvocab.genanki_adapter import build_apkg
from jpvocab.n3grammar_live import N3_GRAMMAR_LIVE_NOTETYPE, build_note


def test_n3_grammar_live_notetype_loaded():
    assert N3_GRAMMAR_LIVE_NOTETYPE.fields == [
        "Expression",
        "Reading",
        "Meaning",
        "Pattern",
        "Connection",
        "ExpressionClean",
    ]
    assert N3_GRAMMAR_LIVE_NOTETYPE.css != ""
    assert N3_GRAMMAR_LIVE_NOTETYPE.deck_name == "Japanese Grammar::Shin Kanzen Master N3"


def test_build_note_and_round_trip(tmp_path: Path):
    fields = build_note({
        "Expression": "電車が<b>着いたばかり</b>だ。",
        "Reading": "でんしゃが ついたばかりだ。",
        "Meaning": "Поезд только что прибыл.",
        "Pattern": "[гл. прош. вр.] + ばかり",
        "Connection": (
            "<ruby>着<rt>つ</rt></ruby>く (прош. вр.) → 着いたばかり<br>"
            "<ruby>食<rt>た</rt></ruby>べる (прош. вр.) → 食べたばかり"
        ),
        "ExpressionClean": "電車が着いたばかりだ。",
    })
    assert len(fields) == 6

    out_path = tmp_path / "n3grammar_live_test.apkg"
    build_apkg(
        [fields],
        deck_name=N3_GRAMMAR_LIVE_NOTETYPE.deck_name,
        out_path=out_path,
        notetype=N3_GRAMMAR_LIVE_NOTETYPE,
    )
    con = open_collection(out_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    rows = cur.fetchall()
    assert len(rows) == 1
    assert "ばかり" in rows[0][0].split("\x1f")[0]
