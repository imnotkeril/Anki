from jpvocab.dictionary import lookup_word


def test_lookup_taberu():
    result = lookup_word("食べる")
    assert result is not None
    assert result.reading == "たべる"
    assert any("eat" in gloss for gloss in result.glosses)


def test_lookup_not_found_returns_none():
    result = lookup_word("ぞぞぞぞぞ存在しない")
    assert result is None
