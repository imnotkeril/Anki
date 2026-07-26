from pathlib import Path

from jpvocab.tatoeba import TatoebaLookup

FIXTURE = "彼は血に飢えた獣だ。\tHe is a beast thirsty for blood.\n猫が好きです。\tI like cats.\n"


def test_find_sentence_containing_word(tmp_path: Path):
    path = tmp_path / "pairs.tsv"
    path.write_text(FIXTURE, encoding="utf-8")
    lookup = TatoebaLookup(path)
    result = lookup.find("獣")
    assert result is not None
    assert result.japanese == "彼は血に飢えた獣だ。"
    assert result.english == "He is a beast thirsty for blood."


def test_no_match_returns_none(tmp_path: Path):
    path = tmp_path / "pairs.tsv"
    path.write_text(FIXTURE, encoding="utf-8")
    lookup = TatoebaLookup(path)
    assert lookup.find("存在しない単語") is None
