from jpvocab.assembler import assemble_note, assemble_fields


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


def test_assemble_fields_in_order_with_missing_defaults_empty():
    fields = assemble_fields(
        values={"Pattern": "on the other hand", "Meaning": "с другой стороны"},
        field_order=["Pattern", "Meaning", "Example", "Register"],
    )
    assert fields == ["on the other hand", "с другой стороны", "", ""]
