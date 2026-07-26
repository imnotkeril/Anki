from pathlib import Path

from beartype import beartype

from jpvocab.assembler import assemble_fields
from jpvocab.notetype import load_notetype

JP_GRAMMAR_NOTETYPE = load_notetype(Path(__file__).parent / "notetype_jpgrammar.json")


@beartype
def build_note(values: dict[str, str]) -> list[str]:
    return assemble_fields(values, JP_GRAMMAR_NOTETYPE.fields)
