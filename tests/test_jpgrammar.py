from pathlib import Path

from jpvocab.apkg_reader import open_collection
from jpvocab.genanki_adapter import build_apkg
from jpvocab.jpgrammar import JP_GRAMMAR_NOTETYPE, build_note


def test_jp_grammar_notetype_loaded():
    assert JP_GRAMMAR_NOTETYPE.fields == [
        "Expression",
        "Reading",
        "Construction",
        "Meaning",
        "PatternForm",
        "PatternMeaning",
        "Connection",
        "ExpressionClean",
    ]
    assert JP_GRAMMAR_NOTETYPE.css != ""


def test_build_note_and_round_trip(tmp_path: Path):
    fields = build_note({
        "Expression": "日本にいる<b>うちに</b>富士山に登ってみたい。",
        "Reading": "にほんにいるうちにふじさんにのぼってみたい。",
        "Construction": "うちに",
        "Meaning": "Пока я в Японии, хочу подняться на Фудзи.",
        "PatternForm": "[отриц. форма гл.] + うちに",
        "PatternMeaning": "сделай, пока состояние не изменилось",
        "Connection": (
            "<ruby>食べる<rt>たべる</rt></ruby> (словарная форма) → 食べるうちに<br>"
            "<ruby>見<rt>み</rt></ruby>ている (длительная форма) → 見ているうちに<br>"
            "<ruby>溶<rt>と</rt></ruby>けない (отриц. форма) → 溶けないうちに"
        ),
        "ExpressionClean": "日本にいるうちに富士山に登ってみたい。",
    })
    assert len(fields) == 8

    out_path = tmp_path / "grammar_test.apkg"
    build_apkg([fields], deck_name="N3 Grammar", out_path=out_path, notetype=JP_GRAMMAR_NOTETYPE)
    con = open_collection(out_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    rows = cur.fetchall()
    assert len(rows) == 1
    parts = rows[0][0].split("\x1f")
    assert "うちに" in parts[0]
