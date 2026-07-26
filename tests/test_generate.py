from jpvocab.generate import draft_words, finalize_draft, WordDraft


def test_draft_known_word_has_no_gaps():
    drafts = draft_words(["それ"])
    assert len(drafts) == 1
    draft = drafts[0]
    assert draft.expression == "それ"
    assert draft.reading is not None
    assert draft.meaning is not None


def test_draft_always_flags_sentence_kana_gap():
    drafts = draft_words(["それ"])
    assert drafts[0].source["sentence_kana"] == "needs_llm"


def test_draft_unknown_word_flags_gaps():
    drafts = draft_words(["ぞぞぞぞぞ存在しない単語です"])
    draft = drafts[0]
    assert draft.reading is None
    assert draft.meaning is None
    assert draft.source["meaning"] == "needs_llm"


def test_finalize_fills_gaps_and_assembles_fields():
    draft = WordDraft(
        expression="不明語",
        reading=None,
        meaning=None,
        pitch_svg=None,
        sentence=None,
        sentence_kana=None,
        sentence_english=None,
        source={"meaning": "needs_llm", "reading": "needs_llm", "sentence": "needs_llm"},
    )
    fields = finalize_draft(
        draft,
        reading="ふめいご",
        meaning="an unclear term (example)",
        sentence="これは<b>不明語</b>です。",
        sentence_kana="これ は ふめいご です",
        sentence_english="This is an example term.",
    )
    assert fields[0] == "不明語"
    assert fields[1] == "an unclear term (example)"
    assert "不明語" in fields[2]
    assert fields[4] == "これは<b>不明語</b>です。"
