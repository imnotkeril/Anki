from beartype import beartype


@beartype
def assemble_note(
    expression: str,
    meaning: str,
    reading_with_pitch: str,
    sentence: str,
    sentence_kana: str,
    sentence_english: str,
) -> list[str]:
    """Field order must match jpvocab.notetype.CORE_NOTETYPE.fields exactly."""
    return [
        expression,
        meaning,
        reading_with_pitch,
        "",  # Audio — left blank, filled locally via AwesomeTTS
        sentence,
        sentence_kana,
        sentence_english,
        "",  # Sentence Audio — left blank, filled locally via AwesomeTTS
    ]
