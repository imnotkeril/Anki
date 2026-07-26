from jpvocab.assembler import assemble_note


def test_assemble_note_field_order():
    fields = assemble_note(
        expression="それ",
        meaning="that, that one",
        reading_with_pitch="それ<!-- accent_start -->...<!-- accent_end -->",
        sentence="<b>それ</b>はとってもいい話だ。",
        sentence_kana="それ は とっても いい はなし だ",
        sentence_english="That's a really nice story.",
    )
    assert fields == [
        "それ",
        "that, that one",
        "それ<!-- accent_start -->...<!-- accent_end -->",
        "",
        "<b>それ</b>はとってもいい話だ。",
        "それ は とっても いい はなし だ",
        "That's a really nice story.",
        "",
    ]
