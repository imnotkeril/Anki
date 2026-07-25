from pathlib import Path
from jpvocab.pitch_lookup import parse_accents_file, PitchLookup

FIXTURE = "1\tいち\t2\n二\tに\t1\nそれ\tそれ\t0\n"

def test_parse_accents_file(tmp_path: Path):
    path = tmp_path / "fixture.txt"
    path.write_text(FIXTURE, encoding="utf-8")
    entries = parse_accents_file(path)
    assert entries[("二", "に")] == [1]
    assert entries[("それ", "それ")] == [0]

def test_pitch_lookup_multiple_accents(tmp_path: Path):
    path = tmp_path / "fixture.txt"
    path.write_text("１\tいち\t2\n１\tひと\t0,2\n", encoding="utf-8")
    lookup = PitchLookup(path)
    assert lookup.get("１", "ひと") == [0, 2]
    assert lookup.get("不明", "ふめい") is None
