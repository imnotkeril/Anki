# JP vocab deck generator — design

Sub-project 1 of 4 (JP vocab / JP grammar / mining redesign / EN family). This spec covers JP vocab only.

## Goal

Given a word list, screenshot, test question, or JLPT/frequency range, produce Anki notes
that are visually and structurally identical to the user's existing `Core 2k_6k [ Pitch
Graphs, Optimized, Links ]` deck (notetype `Japanese Vocab Dynamic+`), either appended
directly into the live collection or exported as a portable `.apkg`.

Source deck analyzed at: `D:\User\Рабочий стол\Анки\колоды которые нужно сравнить\Core 2k_6k [ Pitch Graphs, Optimized, Links ].apkg`
(5996 notes, single notetype, 2 card types: Listening, Reading).

Reference fields (exact order, must match):
`Expression | Meaning | Reading | Audio | Sentence | Sentence-Kana | Sentence-English | Sentence Audio`

`Reading` field contains inline `<svg>` pitch-accent graph baked into the field text itself
(not template-generated) — see Implementation risks.

## Platform

Runs under Claude Code with local filesystem + Bash/PowerShell + localhost network access
to the user's PC (works identically whether Claude Code is opened via terminal, desktop
app, or its web UI — distinguishing factor is Claude Code vs the separate claude.ai
consumer app/mobile, which is sandboxed and cannot reach the user's PC at all).

If a request ever comes from the sandboxed claude.ai app instead: no AnkiConnect, no local
dictionary files. Treat as an isolated one-off — best-effort ad-hoc lookups via whatever
web tools are available in that surface, output a `.apkg` file only, no live-collection
push. Not designed for further in this spec.

## Architecture

One enrichment core, two delivery adapters:

- **Quick add** (a handful of words / one screenshot) → AnkiConnect (`localhost:8765`,
  already installed for Yomitan) → pushes directly into the live
  `Core 2k_6k [ Pitch Graphs, Optimized, Links ]` deck using notetype
  `Japanese Vocab Dynamic+`.
- **Full deck** (word list / JLPT-range request) → genanki → `.apkg` file handed to the
  user to import manually. Notetype id/name/fields/templates/CSS are pulled 1:1 from the
  real collection so rendering is indistinguishable from existing cards.

## Components

1. **Input resolver** — normalizes input into a flat word list (+ optional context
   sentence when available):
   - plain text word list
   - screenshot of textbook/app (OCR / vision read)
   - screenshot of a test/exercise (must infer the tested word from context, not just
     transcribe the image)
   - named JLPT level / frequency range (no user-supplied list)
2. **Dictionary lookup (JMdict)** — `Expression → Reading + Meaning`. Homograph
   disambiguation uses the context sentence when one is available.
   - **Fallback**: if not found in JMdict, do not skip — fall back to LLM for
     reading/meaning, and flag the note as LLM-sourced in the run report.
3. **Pitch accent lookup (Kanjium/NHK accent data) + SVG renderer** — resolves
   `Reading → accent number`, then renders the inline SVG matching the format already
   present in the existing 5996 notes. No API cost (data lookup + deterministic
   rendering), kept in scope even though other secondary fields are deprioritized.
4. **Sentence sourcing** — Tatoeba JP/EN pair matched by containing `Expression`;
   fallback to LLM-drafted sentence + kana + translation when no corpus match exists.
   Run report tracks how many sentences per batch were LLM-generated vs corpus-sourced.
5. **Note assembler** — builds the 8-field record in the exact original order.
   `Audio` and `Sentence Audio` are deliberately left empty — the user fills these
   locally afterward with AwesomeTTS (already installed), no TTS API spend by design.
6. **Dedup guard** — before adding, checks whether the word already exists in the target
   deck (AnkiConnect `findNotes` for quick-add; a snapshot check against the known
   collection for full-deck generation) to avoid re-mining words already present.
7. **Delivery adapters**
   - AnkiConnect adapter: `createDeck` if missing, `addNotes` with
     `modelName=Japanese Vocab Dynamic+`.
   - genanki adapter: builds Model + Deck matching the real notetype (id, fields,
     templates, CSS extracted from the source collection), writes `.apkg`.

## Data flow

```
words[] → JMdict lookup (+LLM fallback) → pitch lookup + SVG render
        → sentence sourcing (Tatoeba → LLM fallback) → note assembler
        → dedup guard → delivery adapter (AnkiConnect | genanki)
        → run report (added / skipped-duplicate / LLM-sourced count)
```

## Error handling

- Word not in JMdict → LLM fallback for reading/meaning, flagged in report (not skipped).
- Ambiguous reading (multiple JMdict entries) → pick most common sense; note the
  alternate in the report if the choice is borderline.
- No pitch data found → note is added without the SVG (plain reading only), flagged in
  report.
- No Tatoeba match → LLM-drafted sentence, flagged in report.
- Duplicate word already in target deck → skip, listed in report.
- AnkiConnect unreachable during quick-add → fall back to genanki `.apkg` for that batch,
  tell the user to import manually.

## Testing / verification

- **Dry-run** for quick-add: show assembled fields as text before the actual AnkiConnect
  call, since a bad write to the live collection is more expensive to undo than reviewing
  first.
- For `.apkg` output: render a couple of sample notes as HTML using the real
  template + CSS (same approach as the comparison mockups already shown to the user)
  before handing over the file, as visual proof of a match.
- Spot check: after generation, re-open the produced `.apkg` with the same
  inspection approach used during the original 5-deck analysis (zstd-decompress →
  sqlite → check notetype id/fields/order) and diff against the source schema.

## Implementation risks

- **Pitch SVG format** must be reverse-engineered from real samples in the source
  collection (coordinates/dot placement vary by mora count and accent type) before this
  can be built — flagged for the implementation plan, not solved in this spec.
- JMdict / Kanjium pitch accent data / Tatoeba sentence pairs need to be sourced and
  stored locally under this project (exact source files/licenses to be pinned during
  implementation planning).

## Known gaps (spec describes intent; confirmed NOT implemented as of 2026-07-27 audit)

Two things this spec describes as design intent were never actually built — flagging so
a future session doesn't assume they work just because they're written above:

- **"AnkiConnect unreachable during quick-add → fall back to genanki `.apkg`"**
  (Error handling, above) — `generate.quick_add` has no try/except around the
  AnkiConnect calls at all; an unreachable AnkiConnect just raises an uncaught
  `requests` exception out of `quick_add`. No fallback path exists.
- **"Homograph disambiguation uses the context sentence when one is available"**
  (Component 2, above) — `dictionary.lookup_word`/`generate.draft_words` take no context
  parameter anywhere; it's always `entries[0]` from the JMdict lookup, full stop.

Neither has caused a real problem yet (not confirmed as a live bug, just an unbuilt
feature) — implement only if it actually bites in practice, don't build it speculatively.

## Out of scope (future sub-projects)

JP grammar generator, mining (Lapis) redesign, EN vocab/collocations/grammar family —
each gets its own spec once this one ships. **Update, 2026-07-27: all shipped** — see
`docs/superpowers/specs/2026-07-26-grammar-en-decks-design.md` for JP grammar / EN vocab
/ EN grammar-collocations / the Mining CSS-only restyle, and its "Wiring to the user's
real legacy notetypes" section for how TOEIC/N3/N2 ended up using their own real,
pre-existing notetypes rather than new jpvocab-specific ones.
