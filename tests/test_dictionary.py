from jpvocab.dictionary import lookup_word


def test_lookup_taberu():
    result = lookup_word("食べる")
    assert result is not None
    assert result.reading == "たべる"
    assert any("eat" in gloss for gloss in result.glosses)


def test_lookup_not_found_returns_none():
    result = lookup_word("ぞぞぞぞぞ存在しない")
    assert result is None


def test_iru_prefers_common_verb_over_rare_homograph():
    result = lookup_word("いる")
    assert result is not None
    assert not any("shoot" in gloss for gloss in result.glosses[:1])
    assert any("exist" in gloss for gloss in result.glosses)


def test_lookup_exposes_readings_and_kanji_forms():
    result = lookup_word("する")
    assert result is not None
    assert result.reading == "する"
    assert result.readings[0] == result.reading
    assert "為る" in result.kanji_forms


def test_lookup_nihon_primary_reading():
    result = lookup_word("日本")
    assert result is not None
    assert result.readings[0] == "にほん"
    assert "にっぽん" in result.readings
