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


def _lookup(tmp_path: Path, *pairs: tuple[str, str]) -> TatoebaLookup:
    path = tmp_path / "pairs.tsv"
    path.write_text("".join(f"{jp}\t{en}\n" for jp, en in pairs), encoding="utf-8")
    return TatoebaLookup(path)


def test_short_hiragana_word_returns_none(tmp_path: Path):
    lookup = _lookup(tmp_path, ("君は僕にとてもいらいらしている。", "You annoy me."))
    assert lookup.find("いる") is None
    assert lookup.find("する") is None


def test_does_not_match_inside_longer_kanji_word(tmp_path: Path):
    lookup = _lookup(
        tmp_path,
        ("日本人ならそんなことはけっしてしないでしょう。", "A Japanese would never."),
        ("日本へようこそ。", "Welcome to Japan."),
    )
    result = lookup.find("日本")
    assert result is not None
    assert result.japanese == "日本へようこそ。"
    assert result.matched == "日本"


def test_does_not_match_inside_longer_katakana_word(tmp_path: Path):
    lookup = _lookup(tmp_path, ("コーヒーメーカーを買った。", "I bought a coffee maker."))
    assert lookup.find("メーカ") is None


def test_only_compound_hit_returns_none(tmp_path: Path):
    lookup = _lookup(tmp_path, ("生物学は好きになれません。", "I never liked biology."))
    assert lookup.find("生物") is None


def test_exact_form_preferred_over_stem(tmp_path: Path):
    lookup = _lookup(
        tmp_path,
        ("昨日ケーキを食べた。", "I ate cake yesterday."),
        ("羊は草を食べる。", "Sheep feed on grass."),
    )
    result = lookup.find("食べる")
    assert result is not None
    assert result.japanese == "羊は草を食べる。"
    assert result.matched == "食べる"


def test_verb_stem_fallback_reports_matched_stem(tmp_path: Path):
    lookup = _lookup(tmp_path, ("昨日ケーキを食べた。", "I ate cake yesterday."))
    result = lookup.find("食べる")
    assert result is not None
    assert result.matched == "食べ"


def test_stem_does_not_match_before_more_kanji(tmp_path: Path):
    lookup = _lookup(tmp_path, ("彼は食べ物が好きです。", "He likes food."))
    assert lookup.find("食べる") is None


def test_prefers_readable_length_then_shortest(tmp_path: Path):
    lookup = _lookup(
        tmp_path,
        ("猫だ。", "A cat."),
        ("私の家には猫がいてとても可愛いです。", "My house has a cute cat."),
        ("私の家には猫が二匹いてとても可愛いです。", "My house has two cute cats."),
    )
    result = lookup.find("猫")
    assert result is not None
    assert result.japanese == "私の家には猫がいてとても可愛いです。"
