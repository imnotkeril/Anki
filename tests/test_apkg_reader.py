from pathlib import Path
from jpvocab.apkg_reader import open_collection, existing_expressions

CORE_APKG = Path(r"D:\User\Рабочий стол\Анки\колоды которые нужно сравнить\Core 2k_6k [ Pitch Graphs, Optimized, Links ].apkg")

def test_open_collection_reads_real_apkg():
    con = open_collection(CORE_APKG)
    cur = con.cursor()
    cur.execute("select name from notetypes where id = 1780786985931")
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "Japanese Vocab Dynamic+"
    con.close()

def test_existing_expressions_reads_real_words():
    words = existing_expressions(CORE_APKG, notetype_id=1780786985931, field_index=0)
    assert "それ" in words
    assert len(words) > 5000
