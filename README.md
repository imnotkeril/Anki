# jpvocab

A note generator for a personal Anki deck set. It builds notes that match the
existing Core 2k/6k-style deck design, either by auto-filling fields from
public data sources (JP vocab: JMdict for readings/glosses, Kanjium for pitch-accent
diagrams, Tatoeba for example sentence pairs) or by taking already-authored
content and assembling it into the right field order (JP grammar, EN vocab,
EN grammar/collocations). Finished notes are delivered two ways:

- **Live push via [AnkiConnect](https://ankiweb.net/shared/info/2055492159)** — adds notes
  directly into a running Anki instance (`quick_add`).
- **`.apkg` file export via [genanki](https://github.com/kerrickstaley/genanki)** — builds a
  deck file you import by hand (`build_deck`).

## Setup

```bash
uv sync
```

That's enough to use JP Grammar, EN Vocab, and EN Grammar/Collocations right away —
they don't depend on any external data.

JP Vocab's automated lookups (readings, pitch accent, example sentences) need a
one-time local data fetch:

```bash
uv run python scripts/fetch_pitch_data.py      # Kanjium pitch-accent data -> data/kanjium_accents.txt
uv run python scripts/fetch_tatoeba_data.py    # Tatoeba raw exports -> data/*.tar.bz2
uv run python scripts/build_tatoeba_pairs.py   # builds data/tatoeba_jpn_eng_pairs.tsv from the exports above
```

Run tests with:

```bash
uv run pytest
```

## Usage: JP Vocab

JP Vocab is the fully automated pipeline: draft a word, fill any gaps the
automated lookups couldn't cover, then deliver it.

```python
from pathlib import Path
from jpvocab.generate import draft_words, finalize_draft, quick_add, build_deck
from jpvocab.notetype import CORE_NOTETYPE

# 1. Draft — looks up JMdict (reading/meaning), Kanjium (pitch accent),
#    Tatoeba (example sentence) for each word.
drafts = draft_words(["食べる", "新語"])

# 2. Finalize each draft — fills in anything the automated lookups missed
#    (e.g. sentence_kana is never auto-filled, so supply it here) and
#    returns the field list in CORE_NOTETYPE.fields order:
#    Expression, Meaning, Reading, Audio, Sentence, Sentence-Kana,
#    Sentence-English, Sentence Audio
notes_fields = [
    finalize_draft(draft, sentence_kana="たべる")  # only needed for gaps
    for draft in drafts
]

# 3a. Push straight into a running Anki (requires the AnkiConnect add-on):
report = quick_add(
    notes_fields,
    field_names=CORE_NOTETYPE.fields,
    deck_name=CORE_NOTETYPE.deck_name,   # default already points at CORE_NOTETYPE
)
print(report.added_count, report.skipped_duplicates)

# 3b. ...or build an .apkg file to import by hand instead:
result = build_deck(
    notes_fields,
    deck_name=CORE_NOTETYPE.deck_name,
    out_path=Path("core_vocab.apkg"),
    existing_words=set(),   # expressions already in your collection, to skip re-adding
)
```

## Usage: JP Grammar / EN Vocab / EN Grammar-Collocations

These three notetypes have no automated lookups — you (or an agent) author the
field values directly as a dict, then `build_note` assembles them into the
correct field order for that notetype. `quick_add`/`build_deck` then need the
matching `model_name`/`field_names` and a `dedup_field` (the field that
identifies a unique note — not every notetype calls it "Expression"):

```python
from pathlib import Path
from jpvocab.jpgrammar import JP_GRAMMAR_NOTETYPE, build_note as build_jpgrammar_note
from jpvocab.envocab import EN_VOCAB_NOTETYPE, build_note as build_envocab_note
from jpvocab.engrammar import EN_GRAMMAR_NOTETYPE, build_note as build_engrammar_note
from jpvocab.generate import quick_add, build_deck

# JP Grammar — fields: Expression, Reading, Construction, Meaning, PatternForm,
# PatternMeaning, Connection
fields = build_jpgrammar_note({
    "Expression": "日本にいる<b>うちに</b>富士山に登ってみたい。",
    "Reading": "にほんにいるうちにふじさんにのぼってみたい。",
    "Construction": "うちに",
    "Meaning": "Пока я в Японии, хочу подняться на Фудзи.",
    "PatternForm": "[отриц. форма гл.] + うちに",
    "PatternMeaning": "сделай, пока состояние не изменилось",
    "Connection": "食べるうちに / 見ているうちに / 溶けないうちに",
})

# EN Vocab — fields: Word, Transcription, POS, Meaning, ExampleEN, ExampleRU
fields = build_envocab_note({
    "Word": "ubiquitous",
    "Transcription": "/juːˈbɪkwɪtəs/",
    "POS": "adjective",
    "Meaning": "вездесущий",
    "ExampleEN": "Smartphones are ubiquitous today.",
    "ExampleRU": "Смартфоны сегодня повсеместны.",
})

# EN Grammar/Collocations — fields: Pattern, Meaning, Example, ExampleRU, Register
fields = build_engrammar_note({
    "Pattern": "on the other hand",
    "Meaning": "с другой стороны",
    "Example": "On the other hand, the new plan costs more.",
    "ExampleRU": "С другой стороны, новый план стоит дороже.",
    "Register": "formal",
})

# Push to a running Anki:
quick_add(
    [fields],
    field_names=EN_GRAMMAR_NOTETYPE.fields,
    deck_name=EN_GRAMMAR_NOTETYPE.deck_name,
    model_name=EN_GRAMMAR_NOTETYPE.notetype_name,
    dedup_field="Pattern",   # "Word" for EN Vocab, "Expression" for JP Grammar
)

# ...or export an .apkg instead:
build_deck(
    [fields],
    deck_name=EN_GRAMMAR_NOTETYPE.deck_name,
    out_path=Path("engrammar_deck.apkg"),
    existing_words=set(),
    notetype=EN_GRAMMAR_NOTETYPE,
)
```

## Project layout

- `generate.py` — top-level delivery pipeline: `draft_words`/`finalize_draft` (JP vocab
  automation) and `quick_add`/`build_deck` (push-to-Anki or export-to-apkg, for any notetype).
- `notetype.py` — loads a `NotetypeSnapshot` (fields, templates, CSS, deck name) from a
  JSON file; `CORE_NOTETYPE` is the JP Vocab snapshot.
- `jpgrammar.py`, `envocab.py`, `engrammar.py` — each defines its notetype snapshot and a
  `build_note(values: dict) -> list[str]` field assembler.
- `assembler.py` — turns raw values into an ordered field list (`assemble_note` for the
  fixed JP Vocab layout, `assemble_fields` as the generic by-name version used by the
  other three notetypes).
- `dictionary.py` — JMdict lookups (reading + glosses) via `jamdict`.
- `pitch.py` — splits kana into morae and renders a pitch-accent SVG diagram.
- `pitch_lookup.py` — parses the Kanjium accents data file into an (expression, reading)
  lookup table.
- `tatoeba.py` — looks up a Japanese/English example sentence pair for a word from the
  built Tatoeba pairs file.
- `ankiconnect.py` — thin HTTP client for the AnkiConnect add-on (create deck, find/add
  notes, store media).
- `genanki_adapter.py` — builds a `genanki` model/deck from a `NotetypeSnapshot` and
  writes it out as an `.apkg`.
- `apkg_reader.py` — opens an `.apkg`'s internal SQLite collection (handles both the
  zstd-compressed and plain formats) to read existing notes back out.
- `pbstrings.py` — minimal protobuf varint/string scanner, used to pull text fields out
  of Anki's binary collection format.

`scripts/` holds the one-time data-fetch scripts (`fetch_pitch_data.py`,
`fetch_tatoeba_data.py`, `build_tatoeba_pairs.py`) plus one-off snapshot extraction
scripts (`extract_notetype_snapshot.py`, `extract_n3grammar_snapshot.py`) used to
generate the `notetype_*.json` files from a real Anki collection.
