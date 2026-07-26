from dataclasses import dataclass, field
from pathlib import Path

from beartype import beartype

from jpvocab import ankiconnect
from jpvocab.assembler import assemble_note
from jpvocab.dictionary import lookup_word
from jpvocab.genanki_adapter import build_apkg
from jpvocab.notetype import CORE_NOTETYPE, NotetypeSnapshot
from jpvocab.pitch import render_pitch_svg, split_morae
from jpvocab.pitch_lookup import PitchLookup
from jpvocab.tatoeba import TatoebaLookup

DATA_DIR = Path(__file__).parent.parent.parent / "data"
_pitch_lookup = PitchLookup(DATA_DIR / "kanjium_accents.txt")
_tatoeba_lookup = TatoebaLookup(DATA_DIR / "tatoeba_jpn_eng_pairs.tsv")


@dataclass
class WordDraft:
    expression: str
    reading: str | None
    meaning: str | None
    pitch_svg: str | None
    sentence: str | None
    sentence_kana: str | None
    sentence_english: str | None
    source: dict[str, str] = field(default_factory=dict)


@beartype
def draft_words(words: list[str]) -> list[WordDraft]:
    drafts = []
    for expression in words:
        entry = lookup_word(expression)
        reading = entry.reading if entry else None
        meaning = ", ".join(entry.glosses[:3]) if entry else None
        source = {"meaning": "jmdict" if entry else "needs_llm", "reading": "jmdict" if entry else "needs_llm"}

        pitch_svg = None
        if reading:
            accents = _pitch_lookup.get(expression, reading)
            if accents:
                pitch_svg = render_pitch_svg(split_morae(reading), accents[0])
        source["pitch"] = "kanjium" if pitch_svg else "missing"

        sentence_pair = _tatoeba_lookup.find(expression)
        sentence = sentence_pair.japanese if sentence_pair else None
        sentence_english = sentence_pair.english if sentence_pair else None
        source["sentence"] = "tatoeba" if sentence_pair else "needs_llm"
        source["sentence_kana"] = "needs_llm"

        drafts.append(
            WordDraft(
                expression=expression,
                reading=reading,
                meaning=meaning,
                pitch_svg=pitch_svg,
                sentence=sentence,
                sentence_kana=None,
                sentence_english=sentence_english,
                source=source,
            )
        )
    return drafts


@beartype
def finalize_draft(
    draft: WordDraft,
    reading: str | None = None,
    meaning: str | None = None,
    sentence: str | None = None,
    sentence_kana: str | None = None,
    sentence_english: str | None = None,
) -> list[str]:
    final_reading = draft.reading or reading or ""
    final_meaning = draft.meaning or meaning or ""
    if draft.pitch_svg:
        # A rendered pitch-accent diagram is the richest option.
        reading_field = draft.pitch_svg
    elif final_reading:
        # No accent data available — fall back to the conventional
        # Anki "kanji[reading]" furigana bracket notation.
        reading_field = f"{draft.expression}[{final_reading}]"
    else:
        reading_field = ""
    final_sentence = draft.sentence or sentence or ""
    final_sentence_kana = draft.sentence_kana or sentence_kana or ""
    final_sentence_english = draft.sentence_english or sentence_english or ""

    return assemble_note(
        expression=draft.expression,
        meaning=final_meaning,
        reading_with_pitch=reading_field,
        sentence=final_sentence,
        sentence_kana=final_sentence_kana,
        sentence_english=final_sentence_english,
    )


@dataclass
class QuickAddReport:
    added_count: int
    skipped_duplicates: list[str]
    added_note_ids: list[int | None]
    dry_run_preview: list[list[str]] | None = None


@beartype
def quick_add(
    notes_fields: list[list[str]],
    field_names: list[str],
    deck_name: str = CORE_NOTETYPE.deck_name,
    dry_run: bool = False,
    model_name: str = CORE_NOTETYPE.notetype_name,
    dedup_field: str = "Expression",
) -> QuickAddReport:
    expression_index = field_names.index(dedup_field)

    to_add = []
    skipped = []
    for fields in notes_fields:
        expression = fields[expression_index]
        escaped_expression = expression.replace('"', '\\"')
        existing = ankiconnect.find_notes(f'deck:"{deck_name}" {dedup_field}:"{escaped_expression}"')
        if existing:
            skipped.append(expression)
        else:
            to_add.append(fields)

    if dry_run:
        return QuickAddReport(
            added_count=len(to_add),
            skipped_duplicates=skipped,
            added_note_ids=[],
            dry_run_preview=to_add,
        )

    ankiconnect.create_deck(deck_name)
    added_ids: list[int | None] = []
    if to_add:
        added_ids = ankiconnect.add_notes(
            deck_name=deck_name,
            model_name=model_name,
            field_names=field_names,
            notes_fields=to_add,
        )

    return QuickAddReport(
        added_count=len(to_add), skipped_duplicates=skipped, added_note_ids=added_ids
    )


@dataclass
class BuildDeckReport:
    out_path: Path
    skipped_duplicates: list[str]


@beartype
def build_deck(
    notes_fields: list[list[str]],
    deck_name: str,
    out_path: Path,
    existing_words: set[str],
    expression_index: int = 0,
    notetype: NotetypeSnapshot = CORE_NOTETYPE,
) -> BuildDeckReport:
    to_add = []
    skipped = []
    for fields in notes_fields:
        expression = fields[expression_index]
        if expression in existing_words:
            skipped.append(expression)
        else:
            to_add.append(fields)

    build_apkg(to_add, deck_name=deck_name, out_path=out_path, notetype=notetype)
    return BuildDeckReport(out_path=out_path, skipped_duplicates=skipped)
