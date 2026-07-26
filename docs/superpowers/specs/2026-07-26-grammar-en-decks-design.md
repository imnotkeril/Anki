# JP grammar + EN vocab + EN grammar/collocations — design

Sub-projects 2-4 of 4 (JP vocab already shipped). Combined into one spec since all three
share the same architecture and, per user decision, none of them need an automated
lookup pipeline — the user supplies pattern/word + examples (text or screenshot), the
agent assembles the note. Only JP vocab needed real dictionary/pitch/corpus automation;
these three are simpler by design.

## Shared architecture (extends the existing `jpvocab` package, not a new project)

Per explicit instruction: "design always unified" applies to the codebase, not just the
CSS. Generalize the three JP-vocab-specific pieces that were hardcoded to one notetype:

- `jpvocab/notetype.py` becomes a generic loader: `load_notetype(json_path) -> NotetypeSnapshot`.
  `CORE_NOTETYPE = load_notetype(DATA/"notetype_core.json")` stays as the existing constant
  (nothing about JP vocab breaks); each new notetype gets its own snapshot JSON + constant
  the same way.
- `jpvocab/ankiconnect.add_notes` and `jpvocab/genanki_adapter.build_apkg` already take
  `model_name`/`deck_name` as parameters — no change needed, they're already generic.
- `jpvocab/generate.quick_add`/`build_deck` currently default `deck_name=CORE_NOTETYPE.deck_name`
  — keep that default for backward compatibility, callers for the new notetypes just pass
  their own `deck_name` explicitly.
- `jpvocab/assembler.assemble_note` is JP-vocab-specific (fixed 8-arg signature). Add one
  new generic function `assemble_fields(values: dict[str, str], field_order: list[str]) -> list[str]`
  that any notetype can use — looks up each field name in `values` (defaulting to `""` for
  fields not supplied), returns them in `field_order`. Keep `assemble_note` as-is (JP vocab
  still uses it), don't refactor it to call the generic one — not worth the churn for a
  6-line function.

## New notetype 1: JP Grammar

Reuses the field schema already present in the user's real `N3 Grammar.apkg`
(`D:\User\Рабочий стол\Анки\колоды которые нужно сравнить\N3 Grammar.apkg`, notetype
`N3 Grammar+`), restyled with the Core2k6k CSS shell (card-shell, colors, fonts — the
`.card`/`.cardClr` rules already extracted in `notetype_snapshot.json`). The existing N3
Grammar deck's own CSS is empty/bare — this fixes that, per the "always unified visual"
requirement.

Fields (unchanged from the real deck, order matters): `Expression, Reading, Meaning, Pattern, Connection, ExpressionClean`
- `Expression`: full example sentence, pattern in bold (`<b>...</b>`), may include `<ruby>` furigana
- `Reading`: same sentence in plain kana
- `Meaning`: Russian translation
- `Pattern`: `Паттерн: [...] Значение: ...` — the grammar explanation
- `Connection`: the conjugation-form connection rules (`гл.辞書形→...`, etc.)
- `ExpressionClean`: bare sentence, no bold/ruby (used on the front-card side)

Cards: 1 card type, front = `ExpressionClean`, back = `Expression` + `Meaning` + `Pattern` + `Connection`,
same shape as the real deck's existing templates but wrapped in the Core2k6k `.card`/`.cardClr`
shell instead of bare unstyled divs.

Notetype name: `JP Grammar (jpvocab)`. Default deck name: `N3 Grammar` (matches the
existing deck the user already studies from — new cards land alongside it).

## New notetype 2: EN Vocab

Fields: `Word, Transcription, POS, Meaning, ExampleEN, ExampleRU`
- `Word`: the English headword
- `Transcription`: IPA, e.g. `/kəˈlætərəl/`
- `POS`: part of speech tag, e.g. `noun`
- `Meaning`: Russian translation
- `ExampleEN`: example sentence, headword in `<b>`
- `ExampleRU`: Russian translation of the example

Cards: 2 card types (Listening-style / Reading-style, matching Core2k6k's own 2-card
pattern) — Card 1 front = `Word`, Card 1 back = everything; Card 2 front = `ExampleEN`
with `Word` blanked via CSS-hidden `<b>`, Card 2 back = everything (mirrors how Core2k6k's
"Reading" card front-loads the sentence). Same CSS shell as Core2k6k.

Notetype name: `EN Vocab (jpvocab)`. Default deck name: caller-supplied (no existing EN
vocab deck to default to — `TOEIC 1600 Essential Words` exists but has a different,
inferior schema per the earlier deck analysis; don't default into it).

## New notetype 3: EN Grammar / Collocations

Fields: `Pattern, Meaning, Example, Register`
- `Pattern`: the collocation or grammar pattern itself (e.g. `on the other hand`)
- `Meaning`: Russian translation
- `Example`: example sentence, pattern in `<b>`
- `Register`: usage tag, e.g. `formal / academic`, `informal`, `IELTS Writing Task 2`

Cards: 1 card type, front = `Pattern`, back = everything. Same CSS shell.

Notetype name: `EN Grammar Collocations (jpvocab)`. Default deck name: caller-supplied.

## Data flow (all three)

```
user gives pattern/word + example (text or screenshot, read directly by the agent —
no OCR/lookup code, this is exactly what the agent already does natively)
  → agent fills the field dict itself (no draft/finalize split needed — there's no
    deterministic lookup step to leave gaps for; the agent IS the only source)
  → assemble_fields(values, field_order)
  → quick_add(...) or build_deck(...) (existing, generic, unchanged)
```

No dictionary/pitch/corpus lookups, no `WordDraft`/`draft_words` equivalent for these
three — that machinery is specific to JP vocab's automatable data sources. Building a
parallel "draft" abstraction here would be speculative generality for inputs that are,
by the user's own decision, always agent-authored.

## Testing

- One round-trip test per new notetype: build a snapshot JSON (extracted from the real
  `N3 Grammar.apkg` for JP Grammar; hand-written for the two new EN notetypes, there's no
  existing real deck to extract from), assemble a sample note, push through `build_apkg`,
  read it back via `apkg_reader.open_collection`, confirm fields round-trip.
- One test for `assemble_fields`'s field-order + missing-key-defaults-to-empty-string behavior.
- Manual smoke test (same shape as JP vocab's Task 13): one real `quick_add` per new
  notetype into the user's live Anki, visual comparison against neighboring cards.

## Error handling

Since there's no automated lookup, there's no "not found" case to handle — if the agent
doesn't have a value for a field, it leaves it `""` (same as JP vocab's Audio fields).
No dedup-by-content-lookup either: `quick_add`'s existing `Expression:`-field dedup only
applies to JP vocab's fixed field name; for these three notetypes, dedup is out of scope
for this pass (grammar patterns and collocations are added in much smaller batches than
6000-word vocab lists, duplicate risk is low and the user reviews before pushing anyway).

## Out of scope

Mining (Lapis) CSS restyle — separate, smaller follow-up (styling-only change to an
existing notetype via AnkiConnect `updateModelStyling`/`updateModelTemplates`, no new
Python module needed).
