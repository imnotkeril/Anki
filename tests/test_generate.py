from jpvocab.generate import _bold_first_occurrence, draft_words, finalize_draft, WordDraft


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
    assert fields[2] == "ふめいご"
    assert fields[4] == "これは<b>不明語</b>です。"


def test_bold_first_occurrence_wraps_unbolded_expression():
    assert _bold_first_occurrence("彼は推しについて語った。", "推し") == "彼は<b>推し</b>について語った。"


def test_bold_first_occurrence_leaves_already_bolded_text_alone():
    text = "彼は<b>推し</b>について語った。"
    assert _bold_first_occurrence(text, "推し") == text


def test_bold_first_occurrence_leaves_text_without_expression_alone():
    assert _bold_first_occurrence("何もない文章。", "推し") == "何もない文章。"


def test_finalize_draft_auto_bolds_sentence():
    draft = WordDraft(
        expression="推し", reading="おし", meaning="fan",
        pitch_svg=None, sentence="彼は推しについて語った。",
        sentence_kana=None, sentence_english="He talked about his favorite.",
        source={},
    )
    fields = finalize_draft(draft)
    assert fields[4] == "彼は<b>推し</b>について語った。"


def test_finalize_draft_explicit_override_wins_over_dictionary_hit():
    draft = WordDraft(
        expression="それ",
        reading="それ",
        meaning="that, that one",
        pitch_svg=None,
        sentence=None,
        sentence_kana=None,
        sentence_english=None,
        source={"meaning": "jmdict", "reading": "jmdict"},
    )
    fields = finalize_draft(draft, meaning="это, то")
    assert fields[1] == "это, то"


def test_draft_suru_finds_pitch_via_written_form():
    draft = draft_words(["する"])[0]
    assert draft.pitch_svg is not None
    assert draft.source["pitch"] == "kanjium"


def test_draft_short_hiragana_gets_no_wrong_sentence():
    draft = draft_words(["いる"])[0]
    assert draft.sentence is None
    assert draft.source["sentence"] == "needs_llm"


def test_find_pitch_svg_skips_accent_that_does_not_fit_reading(monkeypatch):
    from jpvocab import generate
    from jpvocab.dictionary import DictionaryEntry

    class FakeLookup:
        def get(self, expression, reading):
            return {"ふくざつ": [9], "ほか": [0]}.get(reading, [])

    monkeypatch.setattr(generate, "_pitch_lookup", lambda: FakeLookup())
    entry = DictionaryEntry("語", "ふくざつ", ["x"], readings=("ふくざつ", "ほか"))
    reading, svg = generate._find_pitch_svg("語", entry)
    assert reading == "ほか"
    assert svg.startswith("<svg")


def test_finalize_bolds_matched_stem():
    draft = WordDraft(
        expression="食べる", reading="たべる", meaning="to eat", pitch_svg=None,
        sentence="昨日ケーキを食べた。", sentence_kana=None, sentence_english="I ate.",
        sentence_match="食べ",
    )
    fields = finalize_draft(draft)
    assert "<b>食べ</b>た" in "".join(fields)
