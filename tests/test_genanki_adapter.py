from pathlib import Path

from jpvocab.apkg_reader import open_collection
from jpvocab.genanki_adapter import build_apkg


def test_build_apkg_round_trip(tmp_path: Path):
    out_path = tmp_path / "test_deck.apkg"
    fields_list = [
        [
            "それ",
            "that, that one",
            "それ<pitch-svg>",
            "",
            "それはいい 話だ。",
            "それ は いい はなし だ",
            "That's nice.",
            "",
        ],
    ]
    build_apkg(
        fields_list,
        deck_name="Core 2k_6k [ Pitch Graphs, Optimized, Links ]",
        out_path=out_path,
    )

    assert out_path.exists()
    con = open_collection(out_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    rows = cur.fetchall()
    assert len(rows) == 1
    parts = rows[0][0].split("\x1f")
    assert parts[0] == "それ"
    assert parts[1] == "that, that one"
    con.close()
