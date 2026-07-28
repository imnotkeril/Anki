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

> **Revised after first live smoke test + user review (2026-07-27).** The 6-field schema
> below (copied straight from the real N3 Grammar.apkg) tested poorly: no visual
> separation between sections, the pattern explanation ran into the meaning as one
> unbroken line, and the connection-rules content used bare Japanese grammar jargon
> (ない形, 辞書形, ...) that the user can't read without furigana. Superseded by the
> 8-field schema and content conventions documented below the original 6-field notes.

Fields (original, now superseded — kept for history): `Expression, Reading, Meaning, Pattern, Connection, ExpressionClean`
- `Expression`: full example sentence, pattern in bold (`<b>...</b>`), may include `<ruby>` furigana
- `Reading`: same sentence in plain kana
- `Meaning`: Russian translation
- `Pattern`: `Паттерн: [...] Значение: ...` — the grammar explanation
- `Connection`: the conjugation-form connection rules (`гл.辞書形→...`, etc.)
- `ExpressionClean`: bare sentence, no bold/ruby (used on the front-card side)

### Current fields (7, order matters): `Expression, Reading, Construction, Meaning, PatternForm, PatternMeaning, Connection`

> **Revised again during the bug audit (2026-07-27):** `ExpressionClean` was removed
> entirely — once the front card switched to `{{Expression}}<hr>{{Construction}}` (see
> below), nothing referenced `ExpressionClean` anymore. Confirmed dead via grep across
> `src/jpvocab/` before removing it from the notetype JSON, the extractor script, and
> the live Anki notetype (`modelFieldRemove`). If you're reading an older note about "8
> fields" anywhere, it's stale — 7 is current.

- `Expression`: full example sentence, the grammar point in `<b>...</b>`, may include `<ruby>` furigana
- `Reading`: same sentence in plain kana
- `Construction`: the bare grammar point alone, restated on its own line (e.g. `うちに`) — shown big/bold on its own, doesn't require the reader to re-spot it inside the bolded sentence
- `Meaning`: Russian translation of the example sentence
- `PatternForm`: the abstract pattern, e.g. `[отриц. форма гл.] + うちに` — own line, own field (previously crammed onto the same line as `PatternMeaning`)
- `PatternMeaning`: what the pattern means, e.g. `сделай, пока состояние не изменилось` — own line, own field
- `Connection`: conjugation-form examples. **Content convention (always follow this):**
  never use bare Japanese grammar terminology (ない形, 辞書形, ている形, etc.) — always
  give the Russian label instead (`отриц. форма`, `словарная форма`, `длительная форма`, ...).
  Any Japanese word that appears must carry a literal `<ruby>kanji<rt>reading</rt></ruby>` tag —
  never bare kanji with no reading shown, the user cannot parse unfamiliar kanji chains
  without it. Example: `<ruby>食べる<rt>たべる</rt></ruby> (словарная форма) → 食べるうちに<br><ruby>見<rt>み</rt></ruby>ている (длительная форма) → 見ているうちに`
Cards: 1 card type. Front = `{{Expression}}<hr>{{Construction}}` (shows the bolded
construction inline in context, then repeats it bare below — mirrors how Core2k6k's own
Reading-card front works, not a "clean/spoiler-free" front; `ExpressionClean` served that
purpose in an earlier revision and was removed once this became the front, see above).
Back = every field in the order above,
separated by `<hr>` between EVERY section (not just some) — this was the other major
readability complaint: the original template ran everything together with no visual
break at all. `PatternForm`/`PatternMeaning` render as two explicitly labeled lines
(`Конструкция: ...` / `Значение: ...`), never merged into one paragraph.

CSS note: the shared Core2k6k stylesheet doesn't define a muted/secondary text color
variable. This notetype's own CSS snapshot (`notetype_jpgrammar.json`, not the shared
`notetype_snapshot.json`) adds `:root { --fg-subtle: #8a7c6a; }` locally for the
`Конструкция:`/`Значение:`/`Примеры:` labels — don't add this to the shared Core2k6k
snapshot, it's specific to this notetype's template needs.

Notetype name: `JP Grammar (jpvocab)`. Default deck name: `N3 Grammar`.

> **Important, discovered 2026-07-27 during real-data migration:** `N3 Grammar` (this
> notetype's default deck) is a near-empty deck (1 note — the original smoke test) —
> it is **not** the user's real, actively-studied N3 grammar deck. That real deck is
> `Japanese Grammar::Shin Kanzen Master N3` (205 notes, notetype `N3 Grammar+`), a
> completely different, pre-existing notetype. See "Wiring to the user's real legacy
> notetypes" below — **for actual N3/N2 grammar generation, use `n3grammar_live.py` /
> `n2grammar_live.py`, not `jpgrammar.py`.** `jpgrammar.py`/`JP_GRAMMAR_NOTETYPE` is kept
> only as the pattern to copy for a brand-new JP-grammar-style deck that has no existing
> legacy notetype to reuse — it is not deleted, but it is not the live path for N3/N2.

## New notetype 2: EN Vocab

Fields: `Word, Transcription, POS, Meaning, ExampleEN, ExampleRU`
- `Word`: the English headword
- `Transcription`: IPA, e.g. `/kəˈlætərəl/`
- `POS`: part of speech tag, e.g. `noun`
- `Meaning`: Russian translation
- `ExampleEN`: example sentence, headword in `<b>`
- `ExampleRU`: Russian translation of the example

> **Revised after user review (2026-07-27):** originally 2 card types (Word→everything,
> Example→word), mirroring Core2k6k's Listening/Reading pattern. User found 2 cards per
> word confusing ("одна начинается как фраза другая как слово") — reduced to 1 card.

Cards: 1 card type — front = `Word`, back = everything. Same CSS shell as Core2k6k.

Notetype name: `EN Vocab (jpvocab)`. Default deck name: caller-supplied (no existing EN
vocab deck to default to — `TOEIC 1600 Essential Words` exists but has a different,
inferior schema per the earlier deck analysis; don't default into it).

## New notetype 3: EN Grammar / Collocations

> **Revised after user review (2026-07-27):** added `ExampleRU` — the original 4-field
> version left the example sentence untranslated, inconsistent with EN Vocab which
> always translates its example.

Fields: `Pattern, Meaning, Example, ExampleRU, Register`
- `Pattern`: the collocation or grammar pattern itself (e.g. `on the other hand`)
- `Meaning`: Russian translation of the pattern
- `Example`: example sentence, pattern in `<b>`
- `ExampleRU`: Russian translation of the example sentence
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

## Real-data migration lessons (N3/N2 Grammar, 210 real notes, 2026-07-27)

Migrating the user's actual `N3 Grammar+`/`N2 Grammar v3` decks to the reference
structure took several extra correction passes beyond the initial field-split. Recording
what broke so it doesn't repeat on the next real-data migration (Mining, or any future
legacy deck):

- **Use literal `<br>`, never bare `\n`, in any field the template renders directly.**
  The original content used `\n` between multiple "label→example" lines, relying on a
  `white-space: pre-line` CSS rule on the old `.connection`/`.pattern` classes. Restyling
  onto the shared Core2k6k CSS (which has no such rule) silently collapsed every `\n` to
  a space, cramming every example onto one line. Always author/convert multi-line field
  content with real `<br>` tags — don't depend on any particular CSS having
  `white-space: pre-line`.
- **When a template already renders its own label (e.g. `Конструкция: {{PatternForm}}`),
  strip any leading `{label}:` prefix from the field's own text first** (`Паттерн:`,
  `尊敬語:`, `尊敬語 特別形:`, `禁止:`, ...) — otherwise it duplicates as
  "Конструкция: Паттерн: [...]". A generic `^[^:：]{0,20}[:：]\s*` strip (not just a
  literal-string match on "Паттерн:") is needed since the real data used several
  different label words, not one consistent prefix.
- **Ruby goes on the sentence's own reading ONLY if there's no separate reading field
  covering it.** The main `Expression`/`ExpressionClean` sentence should have NO ruby at
  all when a separate `Reading` field already gives the full kana reading below (matches
  Core2k6k's own convention — ruby in a `Sentence` field would be redundant with
  `Sentence-Kana`). Ruby stays on short embedded examples inside `Connection` (e.g.
  `食べる (словарная форма) → 食べるうちに`) since nothing else gives those a reading.
- **Translate every bare Japanese grammar-form label, not just the common ones.** A fixed
  dictionary (辞書形→"словарная форма", た形→"та-форма", ない形→"отриц. форма", ます形,
  て形, 尊敬語, 尊敬語 特別形, 謙譲語, 名→"сущ.", 動→"гл.", etc.) covers the vast majority,
  but treat any bare kanji-only label discovered later the same way — the rule is "no
  Japanese metalanguage without a Russian gloss," not "these specific N terms."
- **Cramped/unspaced prose (`«когда/вмомент»`, `NEдляповседневного`) is a pre-existing
  content defect independent of the field-split** — grep for long unbroken
  Cyrillic runs (`[а-яА-Я]{20,}` after stripping HTML tags) across a deck before
  declaring a migration done; don't assume mechanical field-splitting alone fixes prose
  quality.

## Cross-cutting content conventions (apply to all four notetypes, added 2026-07-27)

- **Meaning fields are always Russian**, never left as JMdict's raw English gloss. JP
  vocab's `draft_words` still resolves an English gloss internally (used for homograph
  disambiguation and as a fallback), but `finalize_draft`'s parameters now take priority
  over the draft value (`generate.py`, commit `a547053`) specifically so the calling
  agent can — and should — always supply its own Russian translation instead of letting
  the English JMdict gloss pass through unchanged.
- **This applies to `Sentence-English` too, despite its name.** That field name is
  inherited verbatim from the real Core2k6k notetype (can't rename it — the schema must
  match exactly) — but its CONTENT must be the agent's own Russian translation of the
  sentence, not the raw English `draft.sentence_english` that `_tatoeba_lookup` resolves
  (Tatoeba only pairs Japanese with English, there's no Russian corpus to draw from).
  Always pass an explicit `sentence_english=` override in Russian to `finalize_draft` —
  don't let the English default through just because the field's name says "English."
- **Never show raw Japanese grammar terminology without a Russian gloss** (no bare ない形,
  辞書形, ている形, etc. anywhere in generated content) — always pair with a Russian label.
- **Never show kanji without furigana** in any field the user is expected to read for
  comprehension (not just headwords) — literal `<ruby>kanji<rt>reading</rt></ruby>` tags,
  every time, including inside example/connection/explanation text, not only the main
  expression field.
- **Visually separate every distinct piece of information with `<hr>`** — cramming
  multiple semantically different lines together (as the very first JP Grammar template
  did) was the single most common complaint across both live smoke tests.
  - **Explicit exception, EN Vocab and EN Grammar/Collocations only (user decision,
    2026-07-27):** headword/pattern and its meaning stay together with NO `<hr>` between
    them (just `<br>`) — the only `<hr>` in these two templates sits right before the
    example sentence. This was deliberate, requested twice after the general rule had
    already been applied and reverted: `{{Word}}<br>{{Meaning}}<hr><i>{{ExampleEN}}</i>`
    for EN Vocab, `{{Pattern}}<br>{{Meaning}}<hr><i>{{Example}}</i>` for EN Grammar. Do
    NOT "fix" this back to hr-between-everything — it was tried and explicitly rejected.
    JP Grammar's every-section-hr rule stands as originally specified; this exception is
    scoped to only these two English notetypes.
  - Also for EN Vocab/EN Grammar: `Transcription`/`POS` (EN Vocab) and `Register` (EN
    Grammar) are real fields kept in the schema but deliberately **not rendered** in the
    template at all — the user asked for the word/pattern to flow straight into the
    translation with nothing in between, not even on its own hr-separated line.

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

## Wiring to the user's real legacy notetypes (TOEIC / N3 / N2, 2026-07-27)

Beyond the three brand-new notetypes above, three of the user's pre-existing real decks
were restyled AND wired into the codebase so future generation targets them directly
instead of creating yet another parallel notetype:

- `TOEIC Formatted` (1596 real notes, deck `TOEIC 1600 Essential Words`) → restyled
  (Core2k6k CSS, one `<hr>` between `Front` and `Back`) → `src/jpvocab/toeic.py`
  (`TOEIC_NOTETYPE`, `build_note`).
- `N3 Grammar+` (205 real notes, deck `Japanese Grammar::Shin Kanzen Master N3`) →
  restyled + content-migrated (see "Real-data migration lessons" above) →
  `src/jpvocab/n3grammar_live.py` (`N3_GRAMMAR_LIVE_NOTETYPE`, `build_note`).
- `N2 Grammar v3` (5 real notes, deck `Japanese Grammar::Shin Kanzen Master N2`) → same
  treatment → `src/jpvocab/n2grammar_live.py` (`N2_GRAMMAR_LIVE_NOTETYPE`, `build_note`).

Snapshots for these three are extracted directly from the live, already-restyled Anki
collection via `scripts/extract_live_notetype.py` (AnkiConnect `modelFieldNames` +
`modelTemplates` + `modelStyling`, read-only) — there's no clean `.apkg` export to pull
them from the way `notetype_snapshot.json`/`notetype_jpgrammar.json` were extracted, since
these notetypes only exist live in the user's own collection.

**Field-value migration on the 210 real N3/N2 notes was safe because it never changed
notetype** — see "Real-data migration lessons" above for exactly what was touched
(new fields added, `Pattern` split, jargon translated, ruby/newlines fixed) and what
wasn't (no note ever changed which notetype it uses, so review scheduling was never at
risk).

### AnkiConnect notetype auto-creation

`ankiconnect.py` gained `model_names()` and `create_model(model_name, fields, css,
templates)` (wrapping AnkiConnect's `modelNames`/`createModel`). `generate.quick_add`
gained an optional `notetype: NotetypeSnapshot | None = None` parameter — when supplied
and `model_name` isn't in `model_names()` yet, it auto-creates the notetype in Anki
before adding notes. This exists because `AnkiConnect.addNotes` cannot create a new
notetype on the fly — the very first live push of a genuinely new notetype (JP Grammar,
EN Vocab, EN Grammar) hit `model was not found` until this was added. Not needed for
`toeic.py`/`n3grammar_live.py`/`n2grammar_live.py` (those notetypes already exist), but
still safe to pass `notetype=` for them too — the "already exists" branch is a no-op.

## Mining (Lapis) — done, minimal (2026-07-27)

User's ask, verbatim: bring fonts/accent color under the Core2k6k tone, keep everything
else (structure, pitch graphs, dropdown glossary, image occlusion) exactly as-is — Lapis
is a well-regarded third-party template, not something to restructure.

Applied via `scripts/restyle_mining_lapis.py` (backup of the original CSS saved to
`scripts/backup_lapis_css_before_restyle.json` first): only two CSS custom properties
changed —
- `--font-serif`/`--font-sans`: now lead with the same JP font stack used everywhere
  else in this project (`"Hiragino Kaku Gothic Pro", "Noto Sans JP", "Meiryo", "MS
  PGothic"`) before falling back to generic serif/sans-serif.
- `--bold`: `#50c5d9` (cyan) → `#ab997e` (Core2k6k's tan accent) — this only affects
  `<b>` emphasis inside glossary/hint text.

**Deliberately left untouched:** the pitch-accent color variables (`--*-heiban`,
`--*-atamadaka`, `--*-nakadaka`, `--*-odaka`, `--*-kifuku`) — these are semantically
meaningful (they encode which pitch class a word belongs to) and the same distinct-hue
convention Lapis ships with everywhere; recoloring them was explicitly declined by the
user ("cмысловые, менять рискованно"). No new Python module — this is a live
styling-only change, no notes are generated through Mining/Lapis by this project (the
user's own Yomitan + asbplayer pipeline handles that, unrelated to `jpvocab`).
