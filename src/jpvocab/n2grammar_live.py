from pathlib import Path

from beartype import beartype

from jpvocab.assembler import assemble_fields
from jpvocab.notetype import load_notetype

N2_GRAMMAR_LIVE_NOTETYPE = load_notetype(Path(__file__).parent / "notetype_n2grammar_live.json")


@beartype
def build_note(values: dict[str, str]) -> list[str]:
    return assemble_fields(values, N2_GRAMMAR_LIVE_NOTETYPE.fields)
