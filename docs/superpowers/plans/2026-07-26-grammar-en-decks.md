# JP Grammar + EN Vocab + EN Grammar/Collocations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Per user instruction, run a SINGLE combined review pass per task (spec compliance + code quality together) instead of two separate passes — speed over ceremony for this plan.

**Goal:** Add three new agent-authored (no automated lookup) Anki notetypes to the existing `jpvocab` package — JP Grammar, EN Vocab, EN Grammar/Collocations — all sharing the Core2k6k CSS shell and the existing generic AnkiConnect/genanki delivery machinery.

**Architecture:** Generalize `notetype.py` (multi-notetype loader) and add `assemble_fields` (generic field-order assembler) to `assembler.py`; then one module per new notetype (snapshot JSON + a thin `build_note(values) -> list[str]` wrapper) reusing those two plus the existing `quick_add`/`build_deck`.

**Tech Stack:** same as the existing `jpvocab` project (Python, uv, beartype, pytest, genanki, AnkiConnect).

---

## Task A: Generalize shared infra

**Files:**
- Modify: `src/jpvocab/notetype.py`
- Modify: `src/jpvocab/assembler.py`
- Test: `tests/test_notetype.py` (extend)
- Test: `tests/test_assembler.py` (extend)

- [ ] **Step 1: Add a generic loader alongside the existing `CORE_NOTETYPE` constant**

```python
# src/jpvocab/notetype.py — replace the bottom of the file (keep Template/NotetypeSnapshot dataclasses unchanged)
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Template:
    name: str
    qfmt: str
    afmt: str


@dataclass(frozen=True)
class NotetypeSnapshot:
    notetype_name: str
    fields: list[str]
    templates: list[Template]
    css: str
    deck_name: str


def load_notetype(json_path: Path) -> NotetypeSnapshot:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return NotetypeSnapshot(
        notetype_name=data["notetype_name"],
        fields=data["fields"],
        templates=[Template(**t) for t in data["templates"]],
        css=data["css"],
        deck_name=data["deck_name"],
    )


CORE_NOTETYPE = load_notetype(Path(__file__).parent / "notetype_snapshot.json")
```

This is a pure rename/extraction (old private `_load()` becomes public `load_notetype(json_path)`, taking the path as a parameter instead of hardcoding it) — `CORE_NOTETYPE`'s value and every existing caller's behavior is unchanged.

- [ ] **Step 2: Extend `tests/test_notetype.py`**

```python
# append to tests/test_notetype.py
from pathlib import Path
from jpvocab.notetype import load_notetype

def test_load_notetype_generic(tmp_path: Path):
    import json
    snapshot_data = {
        "notetype_name": "Test Notetype",
        "fields": ["A", "B"],
        "templates": [{"name": "Card 1", "qfmt": "{{A}}", "afmt": "{{B}}"}],
        "css": ".card { color: red; }",
        "deck_name": "Test Deck",
    }
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_data), encoding="utf-8")
    snapshot = load_notetype(path)
    assert snapshot.notetype_name == "Test Notetype"
    assert snapshot.fields == ["A", "B"]
    assert snapshot.templates[0].qfmt == "{{A}}"
```

- [ ] **Step 3: Add `assemble_fields` to `assembler.py`**

```python
# append to src/jpvocab/assembler.py
from beartype import beartype


@beartype
def assemble_fields(values: dict[str, str], field_order: list[str]) -> list[str]:
    """Generic field assembler for any notetype: looks up each field name in
    `field_order` inside `values`, defaulting to "" for anything not supplied."""
    return [values.get(name, "") for name in field_order]
```

- [ ] **Step 4: Extend `tests/test_assembler.py`**

```python
# append to tests/test_assembler.py
from jpvocab.assembler import assemble_fields

def test_assemble_fields_in_order_with_missing_defaults_empty():
    fields = assemble_fields(
        values={"Pattern": "on the other hand", "Meaning": "с другой стороны"},
        field_order=["Pattern", "Meaning", "Example", "Register"],
    )
    assert fields == ["on the other hand", "с другой стороны", "", ""]
```

- [ ] **Step 5: Run tests, confirm nothing regresses**

Run: `cd E:/Main/Anki && uv run pytest -v`
Expected: all previous 31 tests still pass, plus 2 new ones = 33 passed. `CORE_NOTETYPE`'s existing behavior must be byte-identical — `tests/test_notetype.py`'s original `test_core_notetype_fields` test must still pass unchanged.

- [ ] **Step 6: Commit**

```bash
git add src/jpvocab/notetype.py src/jpvocab/assembler.py tests/test_notetype.py tests/test_assembler.py
git commit -m "feat: generalize notetype loader and add generic field assembler"
```

---

## Task B: JP Grammar notetype

**Files:**
- Create: `scripts/extract_n3grammar_snapshot.py`
- Create: `src/jpvocab/notetype_jpgrammar.json` (generated, committed)
- Create: `src/jpvocab/jpgrammar.py`
- Test: `tests/test_jpgrammar.py`

- [ ] **Step 1: Write the extractor for the real N3 Grammar deck**

```python
# scripts/extract_n3grammar_snapshot.py
import json
from pathlib import Path

from jpvocab.apkg_reader import open_collection
from jpvocab.pbstrings import extract_strings

N3_APKG = Path(r"D:\User\Рабочий стол\Анки\колоды которые нужно сравнить\N3 Grammar.apkg")
OUT_PATH = Path(__file__).parent.parent / "src" / "jpvocab" / "notetype_jpgrammar.json"

# The user's real N3 Grammar deck has NO custom CSS (bare unstyled cards) — per the
# design spec, this new notetype reuses the Core2k6k CSS shell instead of the real
# deck's own (empty) styling, so we pull the CSS from the Core2k6k snapshot rather
# than from N3 Grammar itself.
CORE_SNAPSHOT_PATH = Path(__file__).parent.parent / "src" / "jpvocab" / "notetype_snapshot.json"


def main() -> None:
    con = open_collection(N3_APKG)
    cur = con.cursor()

    # Find the real N3 Grammar+ notetype id (don't hardcode — different collections
    # assign different ids to the same-named notetype).
    cur.execute("select id, name from notetypes")
    notetype_id = None
    for ntid, name in cur.fetchall():
        if name == "N3 Grammar+":
            notetype_id = ntid
            break
    if notetype_id is None:
        raise RuntimeError("N3 Grammar+ notetype not found in N3 Grammar.apkg")

    cur.execute("select ord, name from fields where ntid = ? order by ord", (notetype_id,))
    fields = [row[1] for row in cur.fetchall()]

    core_css = json.loads(CORE_SNAPSHOT_PATH.read_text(encoding="utf-8"))["css"]

    front_fields = ["ExpressionClean"]
    back_fields = ["Expression", "Reading", "Meaning", "Pattern", "Connection"]
    qfmt = "<div class=\"card\"><div class=\"cardClr\">{{ExpressionClean}}</div></div>"
    afmt = (
        "<div class=\"card\">"
        "<div class=\"cardClr\">{{Expression}}</div>"
        "<br>{{Reading}}<br><br>"
        "<div class=\"cardClr\">{{Meaning}}</div>"
        "<br>{{Pattern}}<br><br>{{Connection}}"
        "</div>"
    )

    snapshot = {
        "notetype_name": "JP Grammar (jpvocab)",
        "fields": fields,
        "templates": [{"name": "Card 1", "qfmt": qfmt, "afmt": afmt}],
        "css": core_css,
        "deck_name": "N3 Grammar",
    }
    OUT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(fields)} fields)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the extractor**

Run: `uv run python scripts/extract_n3grammar_snapshot.py`
Expected: prints `wrote .../notetype_jpgrammar.json (6 fields)`. If the field count or
order differs from `Expression, Reading, Meaning, Pattern, Connection, ExpressionClean`
(the order established during this project's original 5-deck analysis), stop and report
the actual fields rather than forcing downstream code to assume the wrong order.

- [ ] **Step 3: Write the failing test**

```python
# tests/test_jpgrammar.py
from pathlib import Path
from jpvocab.apkg_reader import open_collection
from jpvocab.genanki_adapter import build_apkg
from jpvocab.jpgrammar import JP_GRAMMAR_NOTETYPE, build_note

def test_jp_grammar_notetype_loaded():
    assert JP_GRAMMAR_NOTETYPE.fields == [
        "Expression", "Reading", "Meaning", "Pattern", "Connection", "ExpressionClean",
    ]
    assert JP_GRAMMAR_NOTETYPE.css != ""

def test_build_note_and_round_trip(tmp_path: Path):
    fields = build_note({
        "Expression": "日本にいる<b>うちに</b>富士山に登ってみたい。",
        "Reading": "にほんにいるうちにふじさんにのぼってみたい。",
        "Meaning": "Пока я в Японии, хочу подняться на Фудзи.",
        "Pattern": "Паттерн: [состояние] + うちに",
        "Connection": "гл.辞書形→食べるうちに",
        "ExpressionClean": "日本にいるうちに富士山に登ってみたい。",
    })
    assert len(fields) == 6

    out_path = tmp_path / "grammar_test.apkg"
    build_apkg([fields], deck_name="N3 Grammar", out_path=out_path)
    con = open_collection(out_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    rows = cur.fetchall()
    assert len(rows) == 1
    parts = rows[0][0].split("\x1f")
    assert "うちに" in parts[0]
```

- [ ] **Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_jpgrammar.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jpvocab.jpgrammar'`

- [ ] **Step 5: Implement the module**

```python
# src/jpvocab/jpgrammar.py
from pathlib import Path

from beartype import beartype

from jpvocab.assembler import assemble_fields
from jpvocab.notetype import load_notetype

JP_GRAMMAR_NOTETYPE = load_notetype(Path(__file__).parent / "notetype_jpgrammar.json")


@beartype
def build_note(values: dict[str, str]) -> list[str]:
    return assemble_fields(values, JP_GRAMMAR_NOTETYPE.fields)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_jpgrammar.py -v`
Expected: 2 passed

- [ ] **Step 7: Commit**

```bash
git add scripts/extract_n3grammar_snapshot.py src/jpvocab/notetype_jpgrammar.json src/jpvocab/jpgrammar.py tests/test_jpgrammar.py
git commit -m "feat: add JP Grammar notetype (N3 Grammar schema, Core2k6k CSS shell)"
```

---

## Task C: EN Vocab notetype

**Files:**
- Create: `src/jpvocab/notetype_envocab.json` (hand-written, no real deck to extract from)
- Create: `src/jpvocab/envocab.py`
- Test: `tests/test_envocab.py`

- [ ] **Step 1: Hand-write the snapshot JSON**

```python
# a small one-off script is overkill for a hand-written snapshot; write the file directly
```

```json
{
  "notetype_name": "EN Vocab (jpvocab)",
  "fields": ["Word", "Transcription", "POS", "Meaning", "ExampleEN", "ExampleRU"],
  "templates": [
    {
      "name": "Card 1",
      "qfmt": "<div class=\"card\"><div class=\"cardClr\">{{Word}}</div></div>",
      "afmt": "<div class=\"card\"><div class=\"cardClr\">{{Word}}</div><br>{{Transcription}} &middot; {{POS}}<br><br>{{Meaning}}<br><br><i>{{ExampleEN}}</i><br>{{ExampleRU}}</div>"
    },
    {
      "name": "Card 2",
      "qfmt": "<div class=\"card\"><div class=\"cardClr\"><i>{{ExampleEN}}</i></div></div>",
      "afmt": "<div class=\"card\"><div class=\"cardClr\"><i>{{ExampleEN}}</i></div><br>{{ExampleRU}}<hr><div class=\"cardClr\">{{Word}}</div><br>{{Transcription}} &middot; {{POS}}<br>{{Meaning}}</div>"
    }
  ],
  "css": "PLACEHOLDER_REPLACE_WITH_CORE_CSS",
  "deck_name": "EN Vocab"
}
```

Write this file at `src/jpvocab/notetype_envocab.json`, but before saving, replace the
`"css"` value with the real Core2k6k CSS string — read it programmatically rather than
retyping ~1500 characters by hand:

```bash
uv run python -c "
import json
from pathlib import Path
core = json.loads(Path('src/jpvocab/notetype_snapshot.json').read_text(encoding='utf-8'))
envocab_path = Path('src/jpvocab/notetype_envocab.json')
data = json.loads(envocab_path.read_text(encoding='utf-8'))
data['css'] = core['css']
envocab_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('css length:', len(data['css']))
"
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_envocab.py
from pathlib import Path
from jpvocab.apkg_reader import open_collection
from jpvocab.genanki_adapter import build_apkg
from jpvocab.envocab import EN_VOCAB_NOTETYPE, build_note

def test_en_vocab_notetype_loaded():
    assert EN_VOCAB_NOTETYPE.fields == [
        "Word", "Transcription", "POS", "Meaning", "ExampleEN", "ExampleRU",
    ]
    assert EN_VOCAB_NOTETYPE.css != "" and "PLACEHOLDER" not in EN_VOCAB_NOTETYPE.css
    assert len(EN_VOCAB_NOTETYPE.templates) == 2

def test_build_note_and_round_trip(tmp_path: Path):
    fields = build_note({
        "Word": "collateral",
        "Transcription": "/k\u0259\u02c8l\u00e6t\u0259r\u0259l/",
        "POS": "noun",
        "Meaning": "\u0437\u0430\u043b\u043e\u0433, \u043e\u0431\u0435\u0441\u043f\u0435\u0447\u0435\u043d\u0438\u0435",
        "ExampleEN": "The bank asked for <b>collateral</b>.",
        "ExampleRU": "\u0411\u0430\u043d\u043a \u043f\u043e\u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043b \u0437\u0430\u043b\u043e\u0433.",
    })
    assert len(fields) == 6

    out_path = tmp_path / "envocab_test.apkg"
    build_apkg([fields], deck_name="EN Vocab", out_path=out_path)
    con = open_collection(out_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    rows = cur.fetchall()
    assert len(rows) == 1
    assert rows[0][0].split("\x1f")[0] == "collateral"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_envocab.py -v`
Expected: FAIL — `jpvocab.envocab` doesn't exist yet (and/or `notetype_envocab.json` doesn't exist yet if Step 1 wasn't done first)

- [ ] **Step 4: Implement the module**

```python
# src/jpvocab/envocab.py
from pathlib import Path

from beartype import beartype

from jpvocab.assembler import assemble_fields
from jpvocab.notetype import load_notetype

EN_VOCAB_NOTETYPE = load_notetype(Path(__file__).parent / "notetype_envocab.json")


@beartype
def build_note(values: dict[str, str]) -> list[str]:
    return assemble_fields(values, EN_VOCAB_NOTETYPE.fields)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_envocab.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add src/jpvocab/notetype_envocab.json src/jpvocab/envocab.py tests/test_envocab.py
git commit -m "feat: add EN Vocab notetype (Core2k6k CSS shell)"
```

---

## Task D: EN Grammar / Collocations notetype

**Files:**
- Create: `src/jpvocab/notetype_engrammar.json` (hand-written)
- Create: `src/jpvocab/engrammar.py`
- Test: `tests/test_engrammar.py`

- [ ] **Step 1: Hand-write the snapshot JSON** (same CSS-injection approach as Task C Step 1)

```json
{
  "notetype_name": "EN Grammar Collocations (jpvocab)",
  "fields": ["Pattern", "Meaning", "Example", "Register"],
  "templates": [
    {
      "name": "Card 1",
      "qfmt": "<div class=\"card\"><div class=\"cardClr\">{{Pattern}}</div></div>",
      "afmt": "<div class=\"card\"><div class=\"cardClr\">{{Pattern}}</div><br><span class=\"tags\">{{Register}}</span><br><br>{{Meaning}}<br><br><i>{{Example}}</i></div>"
    }
  ],
  "css": "PLACEHOLDER_REPLACE_WITH_CORE_CSS",
  "deck_name": "EN Grammar Collocations"
}
```

Write to `src/jpvocab/notetype_engrammar.json`, then run the same CSS-injection one-liner
as Task C Step 1 (adjust the path to `notetype_engrammar.json`).

- [ ] **Step 2: Write the failing test**

```python
# tests/test_engrammar.py
from pathlib import Path
from jpvocab.apkg_reader import open_collection
from jpvocab.genanki_adapter import build_apkg
from jpvocab.engrammar import EN_GRAMMAR_NOTETYPE, build_note

def test_en_grammar_notetype_loaded():
    assert EN_GRAMMAR_NOTETYPE.fields == ["Pattern", "Meaning", "Example", "Register"]
    assert EN_GRAMMAR_NOTETYPE.css != "" and "PLACEHOLDER" not in EN_GRAMMAR_NOTETYPE.css

def test_build_note_and_round_trip(tmp_path: Path):
    fields = build_note({
        "Pattern": "on the other hand",
        "Meaning": "\u0441 \u0434\u0440\u0443\u0433\u043e\u0439 \u0441\u0442\u043e\u0440\u043e\u043d\u044b",
        "Example": "Some prefer cities. <b>On the other hand</b>, others value quiet.",
        "Register": "formal / academic",
    })
    assert len(fields) == 4

    out_path = tmp_path / "engrammar_test.apkg"
    build_apkg([fields], deck_name="EN Grammar Collocations", out_path=out_path)
    con = open_collection(out_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    rows = cur.fetchall()
    assert len(rows) == 1
    assert rows[0][0].split("\x1f")[0] == "on the other hand"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_engrammar.py -v`
Expected: FAIL — `jpvocab.engrammar` doesn't exist yet

- [ ] **Step 4: Implement the module**

```python
# src/jpvocab/engrammar.py
from pathlib import Path

from beartype import beartype

from jpvocab.assembler import assemble_fields
from jpvocab.notetype import load_notetype

EN_GRAMMAR_NOTETYPE = load_notetype(Path(__file__).parent / "notetype_engrammar.json")


@beartype
def build_note(values: dict[str, str]) -> list[str]:
    return assemble_fields(values, EN_GRAMMAR_NOTETYPE.fields)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_engrammar.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add src/jpvocab/notetype_engrammar.json src/jpvocab/engrammar.py tests/test_engrammar.py
git commit -m "feat: add EN Grammar/Collocations notetype (Core2k6k CSS shell)"
```

---

## Task E: Full suite + manual smoke tests

**Files:** none created — verification only.

- [ ] **Step 1: Run the full automated suite**

Run: `cd E:/Main/Anki && uv run pytest -v`
Expected: all tests from this plan plus the pre-existing JP vocab suite pass — 33 (Task A)
+ 2 (Task B) + 2 (Task C) + 2 (Task D) = 39 total, give or take exact counts; the important
thing is zero failures.

- [ ] **Step 2: Manual smoke test — one real note per new notetype into the live Anki collection**

With Anki open and AnkiConnect active, for each of the three new notetypes, call
`quick_add` with one realistic note and the notetype's own `deck_name`/`notetype_name`,
e.g.:

```python
from jpvocab.jpgrammar import JP_GRAMMAR_NOTETYPE, build_note as build_jpgrammar_note
from jpvocab.generate import quick_add

fields = build_jpgrammar_note({...})
quick_add([fields], field_names=JP_GRAMMAR_NOTETYPE.fields,
          deck_name=JP_GRAMMAR_NOTETYPE.deck_name)
```

(swap in `envocab`/`engrammar` equivalents for the other two). Open Anki's browser,
confirm each new note renders with the Core2k6k visual shell (fonts/colors/card-shell)
and that the fields display correctly for that notetype's own template.

- [ ] **Step 3: Record results**

If any notetype's card doesn't render as expected (CSS not applying, template selector
mismatch), note it as a follow-up rather than declaring done.

---

## Notes for whoever executes this plan

- Task A is a prerequisite for B/C/D (they all depend on `load_notetype`/`assemble_fields`)
  but B/C/D are otherwise independent of each other and could be parallelized across
  workers if desired — this plan lists them sequentially for a single-worker flow.
- Per user instruction, use a single combined spec+quality review pass per task instead
  of two separate reviewer dispatches.
