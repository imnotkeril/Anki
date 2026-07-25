from jpvocab.notetype import CORE_NOTETYPE


def test_core_notetype_fields():
    assert CORE_NOTETYPE.fields == [
        "Expression", "Meaning", "Reading", "Audio",
        "Sentence", "Sentence-Kana", "Sentence-English", "Sentence Audio",
    ]
    assert CORE_NOTETYPE.deck_name == "Core 2k_6k [ Pitch Graphs, Optimized, Links ]"
    assert len(CORE_NOTETYPE.templates) == 2
    assert CORE_NOTETYPE.css != ""
