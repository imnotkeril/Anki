# JP Vocab Deck Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python toolkit that turns a list of Japanese words into Anki notes matching the user's existing `Core 2k_6k [ Pitch Graphs, Optimized, Links ]` deck exactly (same notetype, fields, pitch-accent graphics, CSS), delivered either as a live push into the running Anki collection (AnkiConnect) or as a portable `.apkg` file (genanki).

**Architecture:** One deterministic enrichment core (JMdict dictionary + Kanjium pitch accent + Tatoeba sentence corpus, each with a documented gap the calling agent fills manually) feeds a single note-assembly function, which two thin delivery adapters (AnkiConnect, genanki) consume.

**Tech Stack:** Python 3.11+, managed with `uv`. Libraries: `genanki` (apkg writing), `jamdict` + `jamdict-data` (JMdict lookup), `zstandard` (reading real `.apkg`/`.anki21b` files), `requests` (AnkiConnect HTTP), `beartype` (runtime type checking per project convention), `pytest`.

---

## Reference data already extracted from the real collection

Source file: `D:\User\Рабочий стол\Анки\колоды которые нужно сравнить\Core 2k_6k [ Pitch Graphs, Optimized, Links ].apkg`

- Notetype id: `1780786985931`, name: `Japanese Vocab Dynamic+`
- Deck name: `Core 2k_6k [ Pitch Graphs, Optimized, Links ]`
- Fields (exact order): `Expression, Meaning, Reading, Audio, Sentence, Sentence-Kana, Sentence-English, Sentence Audio`
- Card templates: `Listening` (ord 0), `Reading` (ord 1)

### Pitch-accent SVG format (reverse-engineered from real notes, verified against 4 accent classes)

Confirmed from real `Reading` field values:

- `それ` (heiban, accent 0, 2 morae) →
  `それ<!-- accent_start --><br/><br/><svg class="pitch" height="75px" viewbox="0 0 102 75" width="102px"><text style="font-size:20px;font-family:sans-serif;fill:#000;" x="5" y="67.5">そ</text><text style="font-size:20px;font-family:sans-serif;fill:#000;" x="40" y="67.5">れ</text><path d="m 16,30 35,-25" style="fill:none;stroke:#000;stroke-width:1.5;"></path><path d="m 51,5 35,0" style="fill:none;stroke:#000;stroke-width:1.5;"></path><circle cx="16" cy="30" r="5" style="opacity:1;fill:#000;"></circle><circle cx="51" cy="5" r="5" style="opacity:1;fill:#000;"></circle><circle cx="86" cy="5" r="5" style="opacity:1;fill:#000;"></circle><circle cx="86" cy="5" r="3.25" style="opacity:1;fill:#fff;"></circle></svg><!-- accent_end -->`
- `二` (atamadaka, accent 1, 1 mora) →
  `に<!-- accent_start --><br/><br/><svg class="pitch" height="75px" viewbox="0 0 67 75" width="67px"><text style="font-size:20px;font-family:sans-serif;fill:#000;" x="5" y="67.5">に</text><path d="m 16,5 35,25" style="fill:none;stroke:#000;stroke-width:1.5;"></path><circle cx="16" cy="5" r="5" style="opacity:1;fill:#000;"></circle><circle cx="51" cy="30" r="5" style="opacity:1;fill:#000;"></circle><circle cx="51" cy="30" r="3.25" style="opacity:1;fill:#fff;"></circle></svg><!-- accent_end -->`
- `一` (odaka, accent 2, 2 morae) →
  `いち<!-- accent_start --><br/><br/><svg class="pitch" height="75px" viewbox="0 0 102 75" width="102px"><text style="font-size:20px;font-family:sans-serif;fill:#000;" x="5" y="67.5">い</text><text style="font-size:20px;font-family:sans-serif;fill:#000;" x="40" y="67.5">ち</text><path d="m 16,30 35,-25" style="fill:none;stroke:#000;stroke-width:1.5;"></path><path d="m 51,5 35,25" style="fill:none;stroke:#000;stroke-width:1.5;"></path><circle cx="16" cy="30" r="5" style="opacity:1;fill:#000;"></circle><circle cx="51" cy="5" r="5" style="opacity:1;fill:#000;"></circle><circle cx="86" cy="30" r="5" style="opacity:1;fill:#000;"></circle><circle cx="86" cy="30" r="3.25" style="opacity:1;fill:#fff;"></circle></svg><!-- accent_end -->`
- `日曜日` (nakadaka, accent 3, 5 morae) →
  `にちようび<!-- accent_start --><br/><br/><svg class="pitch" height="75px" viewbox="0 0 207 75" width="207px"><text style="font-size:20px;font-family:sans-serif;fill:#000;" x="5" y="67.5">に</text><text style="font-size:20px;font-family:sans-serif;fill:#000;" x="40" y="67.5">ち</text><text style="font-size:20px;font-family:sans-serif;fill:#000;" x="75" y="67.5">よ</text><text style="font-size:20px;font-family:sans-serif;fill:#000;" x="110" y="67.5">う</text><text style="font-size:20px;font-family:sans-serif;fill:#000;" x="145" y="67.5">び</text><path d="m 16,30 35,-25" style="fill:none;stroke:#000;stroke-width:1.5;"></path><path d="m 51,5 35,0" style="fill:none;stroke:#000;stroke-width:1.5;"></path><path d="m 86,5 35,25" style="fill:none;stroke:#000;stroke-width:1.5;"></path><path d="m 121,30 35,0" style="fill:none;stroke:#000;stroke-width:1.5;"></path><path d="m 156,30 35,0" style="fill:none;stroke:#000;stroke-width:1.5;"></path><circle cx="16" cy="30" r="5" style="opacity:1;fill:#000;"></circle><circle cx="51" cy="5" r="5" style="opacity:1;fill:#000;"></circle><circle cx="86" cy="5" r="5" style="opacity:1;fill:#000;"></circle><circle cx="121" cy="30" r="5" style="opacity:1;fill:#000;"></circle><circle cx="156" cy="30" r="5" style="opacity:1;fill:#000;"></circle><circle cx="191" cy="30" r="5" style="opacity:1;fill:#000;"></circle><circle cx="191" cy="30" r="3.25" style="opacity:1;fill:#fff;"></circle></svg><!-- accent_end -->`

Derived rule (matches all 4 samples exactly):
- `width = 32 + 35*N`, `height = 75` (N = mora count)
- text `i` (0-indexed) at `x=5+35*i, y=67.5`
- dot `j` for `j` in `0..N` (N+1 dots: one per mora plus one trailing "particle" dot) at `x=16+35*j`, `y=5` if high else `y=30`
- high/low rule for dot `j`:
  - if `j == N` (particle dot): high only when `accent == 0`
  - else (mora number `m = j+1`): if `accent==0`: high when `m>=2`. If `accent==1`: high when `m==1`. If `accent>=2`: high when `2<=m<=accent`.
- `path` `k` for `k` in `0..N-1` connects dot `k` to dot `k+1`: `m {x_k},{y_k} 35,{y_(k+1)-y_k}`
- every dot is a filled black circle `r=5`; the last dot (`j==N`) additionally gets a second circle at the same `cx,cy` with `r=3.25 fill:#fff` (hollow-ring effect)

---

## Task 1: Project scaffold

**Files:**
- Create: `E:\Main\Anki\pyproject.toml`
- Create: `E:\Main\Anki\src\jpvocab\__init__.py`
- Create: `E:\Main\Anki\tests\__init__.py`

- [ ] **Step 1: Initialize the uv project**

Run:
```bash
cd E:/Main/Anki
uv init --lib --name jpvocab --package
```
Expected: creates `pyproject.toml`, `src/jpvocab/__init__.py`, `src/jpvocab/py.typed`.

- [ ] **Step 2: Add dependencies**

Run:
```bash
uv add genanki jamdict jamdict-data zstandard requests beartype
uv add --dev pytest
```
Expected: `pyproject.toml` gets a `[project.dependencies]` block listing all 6 packages, `uv.lock` is created/updated.

- [ ] **Step 3: Create empty test package**

```python
# tests/__init__.py
```

- [ ] **Step 4: Verify the environment**

Run: `uv run python -c "import genanki, jamdict, zstandard, requests, beartype; print('ok')"`
Expected: prints `ok` (first run downloads the `jamdict-data` sqlite bundle, may take a minute).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock src tests
git commit -m "chore: scaffold jpvocab project with uv"
```

---

## Task 2: Shared `.apkg` reader (used by the snapshot extractor and the round-trip tests)

**Files:**
- Create: `src/jpvocab/apkg_reader.py`
- Test: `tests/test_apkg_reader.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_apkg_reader.py
from pathlib import Path
from jpvocab.apkg_reader import open_collection, existing_expressions

CORE_APKG = Path(r"D:\User\Рабочий стол\Анки\колоды которые нужно сравнить\Core 2k_6k [ Pitch Graphs, Optimized, Links ].apkg")

def test_open_collection_reads_real_apkg():
    con = open_collection(CORE_APKG)
    cur = con.cursor()
    cur.execute("select name from notetypes where id = 1780786985931")
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "Japanese Vocab Dynamic+"
    con.close()

def test_existing_expressions_reads_real_words():
    words = existing_expressions(CORE_APKG, notetype_id=1780786985931, field_index=0)
    assert "それ" in words
    assert len(words) > 5000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_apkg_reader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jpvocab.apkg_reader'`

- [ ] **Step 3: Write the implementation**

```python
# src/jpvocab/apkg_reader.py
import sqlite3
import tempfile
import zipfile
from pathlib import Path

import zstandard
from beartype import beartype


@beartype
def open_collection(apkg_path: Path) -> sqlite3.Connection:
    """Unzip an .apkg, decompress its zstd-framed collection, open it as sqlite."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="jpvocab_apkg_"))
    with zipfile.ZipFile(apkg_path) as zf:
        zf.extract("collection.anki21b", tmp_dir)
    compressed_path = tmp_dir / "collection.anki21b"
    db_path = tmp_dir / "collection.sqlite"
    dctx = zstandard.ZstdDecompressor()
    with open(compressed_path, "rb") as f_in, open(db_path, "wb") as f_out:
        dctx.copy_stream(f_in, f_out)
    return sqlite3.connect(db_path)


@beartype
def existing_expressions(apkg_path: Path, notetype_id: int, field_index: int) -> set[str]:
    """Read every note's field at `field_index` for a given notetype — used to dedup
    full-deck generation against words already present in the real collection."""
    con = open_collection(apkg_path)
    cur = con.cursor()
    cur.execute("select flds from notes where mid = ?", (notetype_id,))
    words = set()
    for (flds,) in cur.fetchall():
        parts = flds.split("\x1f")
        words.add(parts[field_index])
    con.close()
    return words
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_apkg_reader.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jpvocab/apkg_reader.py tests/test_apkg_reader.py
git commit -m "feat: add .apkg reader utility"
```

---

## Task 3: Notetype snapshot (extract the real Core2k6k notetype so genanki can rebuild it 1:1)

**Files:**
- Create: `src/jpvocab/pbstrings.py`
- Create: `scripts/extract_notetype_snapshot.py`
- Create: `src/jpvocab/notetype_snapshot.json` (generated by the script, committed)
- Create: `src/jpvocab/notetype.py`
- Test: `tests/test_notetype.py`

- [ ] **Step 1: Write the protobuf string-walker**

Anki's `notetypes.config` / `templates.config` columns are protobuf blobs. Rather than compile Anki's full `.proto` schema, walk the wire format generically and pull out every length-delimited field that decodes as mostly-printable UTF-8 (this is what CSS/HTML template text looks like; it was verified against the real collection during design).

```python
# src/jpvocab/pbstrings.py
from beartype import beartype


def _read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, pos


@beartype
def extract_strings(buf: bytes) -> list[str]:
    """Return every printable UTF-8 length-delimited field in a protobuf blob, in order."""
    out: list[str] = []
    pos = 0
    end = len(buf)
    while pos < end:
        tag, pos = _read_varint(buf, pos)
        wire_type = tag & 0x7
        if wire_type == 0:
            _, pos = _read_varint(buf, pos)
        elif wire_type == 1:
            pos += 8
        elif wire_type == 2:
            length, pos = _read_varint(buf, pos)
            sub = buf[pos : pos + length]
            pos += length
            try:
                text = sub.decode("utf-8")
                printable = sum(1 for c in text if c.isprintable() or c in "\n\t")
                if text and printable / len(text) > 0.85:
                    out.append(text)
                    continue
            except UnicodeDecodeError:
                pass
            out.extend(extract_strings(sub))
        elif wire_type == 5:
            pos += 4
        else:
            break
    return out
```

- [ ] **Step 2: Write the extractor script**

```python
# scripts/extract_notetype_snapshot.py
import json
from pathlib import Path

from jpvocab.apkg_reader import open_collection
from jpvocab.pbstrings import extract_strings

CORE_APKG = Path(r"D:\User\Рабочий стол\Анки\колоды которые нужно сравнить\Core 2k_6k [ Pitch Graphs, Optimized, Links ].apkg")
NOTETYPE_ID = 1780786985931
OUT_PATH = Path(__file__).parent.parent / "src" / "jpvocab" / "notetype_snapshot.json"


def main() -> None:
    con = open_collection(CORE_APKG)
    cur = con.cursor()

    cur.execute("select name, config from notetypes where id = ?", (NOTETYPE_ID,))
    name, config = cur.fetchone()
    css_candidates = [s for s in extract_strings(config) if ".card" in s or "cardClr" in s]
    css = css_candidates[0] if css_candidates else ""

    cur.execute("select ord, name from fields where ntid = ? order by ord", (NOTETYPE_ID,))
    fields = [row[1] for row in cur.fetchall()]

    cur.execute("select ord, name, config from templates where ntid = ? order by ord", (NOTETYPE_ID,))
    templates = []
    for ordn, tname, tconfig in cur.fetchall():
        strings = extract_strings(tconfig)
        qfmt = strings[0] if len(strings) > 0 else ""
        afmt = strings[1] if len(strings) > 1 else ""
        templates.append({"name": tname, "qfmt": qfmt, "afmt": afmt})

    snapshot = {
        "notetype_name": name,
        "fields": fields,
        "templates": templates,
        "css": css,
        "deck_name": "Core 2k_6k [ Pitch Graphs, Optimized, Links ]",
    }
    OUT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(fields)} fields, {len(templates)} templates)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the extractor**

Run: `uv run python scripts/extract_notetype_snapshot.py`
Expected: prints `wrote .../notetype_snapshot.json (8 fields, 2 templates)`

- [ ] **Step 4: Write the failing test for the loader**

```python
# tests/test_notetype.py
from jpvocab.notetype import CORE_NOTETYPE

def test_core_notetype_fields():
    assert CORE_NOTETYPE.fields == [
        "Expression", "Meaning", "Reading", "Audio",
        "Sentence", "Sentence-Kana", "Sentence-English", "Sentence Audio",
    ]
    assert CORE_NOTETYPE.deck_name == "Core 2k_6k [ Pitch Graphs, Optimized, Links ]"
    assert len(CORE_NOTETYPE.templates) == 2
    assert CORE_NOTETYPE.css != ""
```

- [ ] **Step 5: Run test to verify it fails**

Run: `uv run pytest tests/test_notetype.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jpvocab.notetype'`

- [ ] **Step 6: Write the loader**

```python
# src/jpvocab/notetype.py
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


def _load() -> NotetypeSnapshot:
    path = Path(__file__).parent / "notetype_snapshot.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return NotetypeSnapshot(
        notetype_name=data["notetype_name"],
        fields=data["fields"],
        templates=[Template(**t) for t in data["templates"]],
        css=data["css"],
        deck_name=data["deck_name"],
    )


CORE_NOTETYPE = _load()
```

- [ ] **Step 7: Run test to verify it passes**

Run: `uv run pytest tests/test_notetype.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/jpvocab/pbstrings.py src/jpvocab/notetype.py src/jpvocab/notetype_snapshot.json scripts/extract_notetype_snapshot.py tests/test_notetype.py
git commit -m "feat: extract and load the real Core2k6k notetype as a frozen snapshot"
```

---

## Task 4: Pitch-accent SVG renderer

**Files:**
- Create: `src/jpvocab/pitch.py`
- Test: `tests/test_pitch.py`

- [ ] **Step 1: Write the failing tests using the verified real samples**

```python
# tests/test_pitch.py
from jpvocab.pitch import render_pitch_svg

def test_heiban_sore():
    svg = render_pitch_svg(morae=["そ", "れ"], accent=0)
    assert svg == (
        '<svg class="pitch" height="75px" viewbox="0 0 102 75" width="102px">'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="5" y="67.5">そ</text>'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="40" y="67.5">れ</text>'
        '<path d="m 16,30 35,-25" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<path d="m 51,5 35,0" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<circle cx="16" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="51" cy="5" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="86" cy="5" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="86" cy="5" r="3.25" style="opacity:1;fill:#fff;"></circle>'
        '</svg>'
    )

def test_atamadaka_ni():
    svg = render_pitch_svg(morae=["に"], accent=1)
    assert svg == (
        '<svg class="pitch" height="75px" viewbox="0 0 67 75" width="67px">'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="5" y="67.5">に</text>'
        '<path d="m 16,5 35,25" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<circle cx="16" cy="5" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="51" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="51" cy="30" r="3.25" style="opacity:1;fill:#fff;"></circle>'
        '</svg>'
    )

def test_odaka_ichi():
    svg = render_pitch_svg(morae=["い", "ち"], accent=2)
    assert svg == (
        '<svg class="pitch" height="75px" viewbox="0 0 102 75" width="102px">'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="5" y="67.5">い</text>'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="40" y="67.5">ち</text>'
        '<path d="m 16,30 35,-25" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<path d="m 51,5 35,25" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<circle cx="16" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="51" cy="5" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="86" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="86" cy="30" r="3.25" style="opacity:1;fill:#fff;"></circle>'
        '</svg>'
    )

def test_nakadaka_nichiyoubi():
    svg = render_pitch_svg(morae=["に", "ち", "よ", "う", "び"], accent=3)
    assert svg == (
        '<svg class="pitch" height="75px" viewbox="0 0 207 75" width="207px">'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="5" y="67.5">に</text>'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="40" y="67.5">ち</text>'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="75" y="67.5">よ</text>'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="110" y="67.5">う</text>'
        '<text style="font-size:20px;font-family:sans-serif;fill:#000;" x="145" y="67.5">び</text>'
        '<path d="m 16,30 35,-25" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<path d="m 51,5 35,0" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<path d="m 86,5 35,25" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<path d="m 121,30 35,0" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<path d="m 156,30 35,0" style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        '<circle cx="16" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="51" cy="5" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="86" cy="5" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="121" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="156" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="191" cy="30" r="5" style="opacity:1;fill:#000;"></circle>'
        '<circle cx="191" cy="30" r="3.25" style="opacity:1;fill:#fff;"></circle>'
        '</svg>'
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_pitch.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jpvocab.pitch'`

- [ ] **Step 3: Implement the renderer**

```python
# src/jpvocab/pitch.py
from beartype import beartype


def _dot_high(mora_index_from_1: int | None, accent: int) -> bool:
    """mora_index_from_1 is None for the trailing particle dot."""
    if mora_index_from_1 is None:
        return accent == 0
    if accent == 0:
        return mora_index_from_1 >= 2
    if accent == 1:
        return mora_index_from_1 == 1
    return 2 <= mora_index_from_1 <= accent


@beartype
def render_pitch_svg(morae: list[str], accent: int) -> str:
    n = len(morae)
    width = 32 + 35 * n

    texts = "".join(
        f'<text style="font-size:20px;font-family:sans-serif;fill:#000;" '
        f'x="{5 + 35 * i}" y="67.5">{mora}</text>'
        for i, mora in enumerate(morae)
    )

    dot_y = [5 if _dot_high(j + 1 if j < n else None, accent) else 30 for j in range(n + 1)]
    dot_x = [16 + 35 * j for j in range(n + 1)]

    paths = "".join(
        f'<path d="m {dot_x[k]},{dot_y[k]} 35,{dot_y[k + 1] - dot_y[k]}" '
        f'style="fill:none;stroke:#000;stroke-width:1.5;"></path>'
        for k in range(n)
    )

    circles = "".join(
        f'<circle cx="{dot_x[j]}" cy="{dot_y[j]}" r="5" style="opacity:1;fill:#000;"></circle>'
        for j in range(n + 1)
    )
    circles += (
        f'<circle cx="{dot_x[n]}" cy="{dot_y[n]}" r="3.25" '
        f'style="opacity:1;fill:#fff;"></circle>'
    )

    return (
        f'<svg class="pitch" height="75px" viewbox="0 0 {width} 75" width="{width}px">'
        f'{texts}{paths}{circles}</svg>'
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_pitch.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/jpvocab/pitch.py tests/test_pitch.py
git commit -m "feat: add pitch-accent SVG renderer matching the real Core2k6k format"
```

---

## Task 5: Kanjium pitch-accent data loader

**Files:**
- Create: `data/.gitkeep`
- Modify: `.gitignore` (create if absent) — add `data/*.txt`, `data/*.tsv`, `data/*.tar.bz2`, `!data/.gitkeep`
- Create: `scripts/fetch_pitch_data.py`
- Create: `src/jpvocab/pitch_lookup.py`
- Test: `tests/test_pitch_lookup.py`

- [ ] **Step 1: Write the fetch script**

```python
# scripts/fetch_pitch_data.py
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/mifunetoshiro/kanjium/master/data/source_files/raw/accents.txt"
OUT = Path(__file__).parent.parent / "data" / "kanjium_accents.txt"


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    urllib.request.urlretrieve(URL, OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `uv run python scripts/fetch_pitch_data.py`
Expected: prints `wrote .../data/kanjium_accents.txt (...bytes)` — file is ~3.1MB.

- [ ] **Step 3: Write the failing test (uses a small embedded fixture, not the full file)**

```python
# tests/test_pitch_lookup.py
from pathlib import Path
from jpvocab.pitch_lookup import parse_accents_file, PitchLookup

FIXTURE = "1\tいち\t2\n二\tに\t1\nそれ\tそれ\t0\n"

def test_parse_accents_file(tmp_path: Path):
    path = tmp_path / "fixture.txt"
    path.write_text(FIXTURE, encoding="utf-8")
    entries = parse_accents_file(path)
    assert entries[("二", "に")] == [1]
    assert entries[("それ", "それ")] == [0]

def test_pitch_lookup_multiple_accents(tmp_path: Path):
    path = tmp_path / "fixture.txt"
    path.write_text("１\tいち\t2\n１\tひと\t0,2\n", encoding="utf-8")
    lookup = PitchLookup(path)
    assert lookup.get("１", "ひと") == [0, 2]
    assert lookup.get("不明", "ふめい") is None
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `uv run pytest tests/test_pitch_lookup.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jpvocab.pitch_lookup'`

- [ ] **Step 5: Implement the loader**

```python
# src/jpvocab/pitch_lookup.py
from pathlib import Path

from beartype import beartype


@beartype
def parse_accents_file(path: Path) -> dict[tuple[str, str], list[int]]:
    entries: dict[tuple[str, str], list[int]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expression, reading, accents_raw = line.split("\t")
        accents = [int(a) for a in accents_raw.split(",")]
        entries[(expression, reading)] = accents
    return entries


class PitchLookup:
    @beartype
    def __init__(self, path: Path) -> None:
        self._entries = parse_accents_file(path)

    @beartype
    def get(self, expression: str, reading: str) -> list[int] | None:
        return self._entries.get((expression, reading))
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_pitch_lookup.py -v`
Expected: 2 passed

- [ ] **Step 7: Commit**

```bash
git add data/.gitkeep .gitignore scripts/fetch_pitch_data.py src/jpvocab/pitch_lookup.py tests/test_pitch_lookup.py
git commit -m "feat: add Kanjium pitch-accent data loader"
```

---

## Task 6: JMdict dictionary lookup

**Files:**
- Create: `src/jpvocab/dictionary.py`
- Test: `tests/test_dictionary.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dictionary.py
from jpvocab.dictionary import lookup_word

def test_lookup_taberu():
    result = lookup_word("食べる")
    assert result is not None
    assert result.reading == "たべる"
    assert any("eat" in gloss for gloss in result.glosses)

def test_lookup_not_found_returns_none():
    result = lookup_word("ぞぞぞぞぞ存在しない")
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_dictionary.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jpvocab.dictionary'`

- [ ] **Step 3: Implement the wrapper**

```python
# src/jpvocab/dictionary.py
from dataclasses import dataclass

from beartype import beartype
from jamdict import Jamdict

_jam = Jamdict()


@dataclass(frozen=True)
class DictionaryEntry:
    expression: str
    reading: str
    glosses: list[str]


@beartype
def lookup_word(expression: str) -> DictionaryEntry | None:
    result = _jam.lookup(expression)
    if not result.entries:
        return None
    entry = result.entries[0]
    reading = entry.kana_forms[0].text if entry.kana_forms else ""
    glosses = [
        gloss.text
        for sense in entry.senses
        for gloss in sense.gloss
    ]
    return DictionaryEntry(expression=expression, reading=reading, glosses=glosses)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_dictionary.py -v`
Expected: 2 passed (first run may take longer while `jamdict-data`'s bundled sqlite is indexed)

- [ ] **Step 5: Commit**

```bash
git add src/jpvocab/dictionary.py tests/test_dictionary.py
git commit -m "feat: add JMdict dictionary lookup via jamdict"
```

---

## Task 7: Tatoeba sentence corpus

**Files:**
- Create: `scripts/fetch_tatoeba_data.py`
- Create: `scripts/build_tatoeba_pairs.py`
- Create: `src/jpvocab/tatoeba.py`
- Test: `tests/test_tatoeba.py`

- [ ] **Step 1: Write the fetch script**

```python
# scripts/fetch_tatoeba_data.py
import urllib.request
from pathlib import Path

FILES = {
    "sentences.tar.bz2": "https://downloads.tatoeba.org/exports/sentences.tar.bz2",
    "links.tar.bz2": "https://downloads.tatoeba.org/exports/links.tar.bz2",
    "jpn_indices.tar.bz2": "https://downloads.tatoeba.org/exports/jpn_indices.tar.bz2",
}
DATA_DIR = Path(__file__).parent.parent / "data"


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    for filename, url in FILES.items():
        out_path = DATA_DIR / filename
        print(f"downloading {url} -> {out_path}")
        urllib.request.urlretrieve(url, out_path)
    print("done")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `uv run python scripts/fetch_tatoeba_data.py`
Expected: `sentences.tar.bz2` (all languages, largest file), `links.tar.bz2`, `jpn_indices.tar.bz2` downloaded into `data/`.

- [ ] **Step 3: Write the script that builds a small JP→EN pairs file**

`jpn_indices.tar.bz2` contains, per Japanese sentence id, its id/text/lemma-annotated text (tab-separated, no header). `sentences.tar.bz2` contains `id\tlang\ttext` for every sentence in every language. `links.tar.bz2` contains `sentence_id\ttranslation_id` pairs. Join: Japanese sentence ids (from `jpn_indices`) → linked English sentence ids (via `links`, filtered to `sentences` where `lang == "eng"`) → write `expression-independent` `jp_text\ten_text` pairs to a flat file.

```python
# scripts/build_tatoeba_pairs.py
import tarfile
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OUT_PATH = DATA_DIR / "tatoeba_jpn_eng_pairs.tsv"


def _read_tsv_from_tar(tar_path: Path, member_suffix: str) -> list[list[str]]:
    with tarfile.open(tar_path, "r:bz2") as tar:
        member = next(m for m in tar.getmembers() if m.name.endswith(member_suffix))
        content = tar.extractfile(member).read().decode("utf-8")
    return [line.split("\t") for line in content.splitlines() if line.strip()]


def main() -> None:
    jpn_ids = {row[0] for row in _read_tsv_from_tar(DATA_DIR / "jpn_indices.tar.bz2", "jpn_indices.tsv")}

    links = _read_tsv_from_tar(DATA_DIR / "links.tar.bz2", "links.csv")
    jpn_to_eng_ids: dict[str, list[str]] = {}
    for sentence_id, translation_id in links:
        if sentence_id in jpn_ids:
            jpn_to_eng_ids.setdefault(sentence_id, []).append(translation_id)

    text_by_id: dict[str, str] = {}
    needed_ids = jpn_ids | {tid for ids in jpn_to_eng_ids.values() for tid in ids}
    for sentence_id, lang, text in _read_tsv_from_tar(DATA_DIR / "sentences.tar.bz2", "sentences.csv"):
        if sentence_id in needed_ids:
            text_by_id[sentence_id] = text

    with open(OUT_PATH, "w", encoding="utf-8") as out:
        for jpn_id, eng_ids in jpn_to_eng_ids.items():
            jpn_text = text_by_id.get(jpn_id)
            if not jpn_text:
                continue
            for eng_id in eng_ids:
                eng_text = text_by_id.get(eng_id)
                if eng_text:
                    out.write(f"{jpn_text}\t{eng_text}\n")
                    break
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run it**

Run: `uv run python scripts/build_tatoeba_pairs.py`
Expected: prints `wrote .../data/tatoeba_jpn_eng_pairs.tsv`. This step reads the full multi-language `sentences.tar.bz2` in memory-ish (line-by-line via `tarfile`); if it's too slow/large on this machine, note it as a follow-up to stream instead of loading `_read_tsv_from_tar`'s full return list — flag but don't block the plan on it.

- [ ] **Step 5: Write the failing test for the lookup (uses a small fixture file, not the real 3M-line one)**

```python
# tests/test_tatoeba.py
from pathlib import Path
from jpvocab.tatoeba import TatoebaLookup

FIXTURE = "彼は血に飢えた獣だ。\tHe is a beast thirsty for blood.\n猫が好きです。\tI like cats.\n"

def test_find_sentence_containing_word(tmp_path: Path):
    path = tmp_path / "pairs.tsv"
    path.write_text(FIXTURE, encoding="utf-8")
    lookup = TatoebaLookup(path)
    result = lookup.find("獣")
    assert result is not None
    assert result.japanese == "彼は血に飢えた獣だ。"
    assert result.english == "He is a beast thirsty for blood."

def test_no_match_returns_none(tmp_path: Path):
    path = tmp_path / "pairs.tsv"
    path.write_text(FIXTURE, encoding="utf-8")
    lookup = TatoebaLookup(path)
    assert lookup.find("存在しない単語") is None
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `uv run pytest tests/test_tatoeba.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jpvocab.tatoeba'`

- [ ] **Step 7: Implement the lookup**

```python
# src/jpvocab/tatoeba.py
from dataclasses import dataclass
from pathlib import Path

from beartype import beartype


@dataclass(frozen=True)
class SentencePair:
    japanese: str
    english: str


class TatoebaLookup:
    @beartype
    def __init__(self, path: Path) -> None:
        self._pairs: list[SentencePair] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            jp, en = line.split("\t", maxsplit=1)
            self._pairs.append(SentencePair(japanese=jp, english=en))

    @beartype
    def find(self, expression: str) -> SentencePair | None:
        for pair in self._pairs:
            if expression in pair.japanese:
                return pair
        return None
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `uv run pytest tests/test_tatoeba.py -v`
Expected: 2 passed

- [ ] **Step 9: Commit**

```bash
git add scripts/fetch_tatoeba_data.py scripts/build_tatoeba_pairs.py src/jpvocab/tatoeba.py tests/test_tatoeba.py
git commit -m "feat: add Tatoeba JP/EN sentence corpus lookup"
```

---

## Task 8: Note assembler

**Files:**
- Create: `src/jpvocab/assembler.py`
- Test: `tests/test_assembler.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_assembler.py
from jpvocab.assembler import assemble_note

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_assembler.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jpvocab.assembler'`

- [ ] **Step 3: Implement the assembler**

```python
# src/jpvocab/assembler.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_assembler.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jpvocab/assembler.py tests/test_assembler.py
git commit -m "feat: add note assembler with fixed 8-field order"
```

---

## Task 9: genanki delivery adapter (full-deck `.apkg` output)

**Files:**
- Create: `src/jpvocab/genanki_adapter.py`
- Test: `tests/test_genanki_adapter.py`

- [ ] **Step 1: Write the failing test — build a tiny deck and read it back with the Task 2 reader**

```python
# tests/test_genanki_adapter.py
from pathlib import Path
from jpvocab.apkg_reader import open_collection
from jpvocab.genanki_adapter import build_apkg

def test_build_apkg_round_trip(tmp_path: Path):
    out_path = tmp_path / "test_deck.apkg"
    fields_list = [
        ["それ", "that, that one", "それ<pitch-svg>", "", "それはいい 話だ。", "それ は いい はなし だ", "That's nice.", ""],
    ]
    build_apkg(fields_list, deck_name="Core 2k_6k [ Pitch Graphs, Optimized, Links ]", out_path=out_path)

    assert out_path.exists()
    con = open_collection(out_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    rows = cur.fetchall()
    assert len(rows) == 1
    parts = rows[0][0].split("\x1f")
    assert parts[0] == "それ"
    assert parts[1] == "that, that one"
    con.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_genanki_adapter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jpvocab.genanki_adapter'`

- [ ] **Step 3: Implement the adapter**

```python
# src/jpvocab/genanki_adapter.py
from pathlib import Path

import genanki
from beartype import beartype

from jpvocab.notetype import CORE_NOTETYPE

# Fixed IDs so re-running the generator produces stable, mergeable output.
# genanki matches an existing notetype/deck by name on import, so these
# values don't need to match Anki's internal 64-bit ids.
_MODEL_ID = 1976543210
_DECK_ID = 1976543211


def _build_model() -> genanki.Model:
    return genanki.Model(
        _MODEL_ID,
        CORE_NOTETYPE.notetype_name,
        fields=[{"name": f} for f in CORE_NOTETYPE.fields],
        templates=[
            {"name": t.name, "qfmt": t.qfmt, "afmt": t.afmt}
            for t in CORE_NOTETYPE.templates
        ],
        css=CORE_NOTETYPE.css,
    )


@beartype
def build_apkg(fields_list: list[list[str]], deck_name: str, out_path: Path) -> Path:
    model = _build_model()
    deck = genanki.Deck(_DECK_ID, deck_name)
    for fields in fields_list:
        deck.add_note(genanki.Note(model=model, fields=fields))
    genanki.Package(deck).write_to_file(str(out_path))
    return out_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_genanki_adapter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jpvocab/genanki_adapter.py tests/test_genanki_adapter.py
git commit -m "feat: add genanki delivery adapter with round-trip test"
```

---

## Task 10: AnkiConnect delivery adapter (quick-add live push)

**Files:**
- Create: `src/jpvocab/ankiconnect.py`
- Test: `tests/test_ankiconnect.py`

- [ ] **Step 1: Write the failing tests using a mocked HTTP layer (no real Anki needed)**

```python
# tests/test_ankiconnect.py
from unittest.mock import patch, MagicMock
from jpvocab.ankiconnect import create_deck, find_notes, add_notes

def _mock_response(result):
    resp = MagicMock()
    resp.json.return_value = {"result": result, "error": None}
    return resp

@patch("jpvocab.ankiconnect.requests.post")
def test_create_deck_sends_correct_payload(mock_post):
    mock_post.return_value = _mock_response(None)
    create_deck("Core 2k_6k [ Pitch Graphs, Optimized, Links ]")
    sent = mock_post.call_args.kwargs["json"]
    assert sent["action"] == "createDeck"
    assert sent["params"]["deck"] == "Core 2k_6k [ Pitch Graphs, Optimized, Links ]"

@patch("jpvocab.ankiconnect.requests.post")
def test_find_notes_returns_ids(mock_post):
    mock_post.return_value = _mock_response([111, 222])
    ids = find_notes('deck:"Core 2k_6k" Expression:それ')
    assert ids == [111, 222]

@patch("jpvocab.ankiconnect.requests.post")
def test_add_notes_builds_field_dict_in_order(mock_post):
    mock_post.return_value = _mock_response([12345])
    ids = add_notes(
        deck_name="Core 2k_6k [ Pitch Graphs, Optimized, Links ]",
        model_name="Japanese Vocab Dynamic+",
        field_names=["Expression", "Meaning"],
        notes_fields=[["それ", "that"]],
    )
    assert ids == [12345]
    sent = mock_post.call_args.kwargs["json"]
    note = sent["params"]["notes"][0]
    assert note["fields"] == {"Expression": "それ", "Meaning": "that"}
    assert note["deckName"] == "Core 2k_6k [ Pitch Graphs, Optimized, Links ]"
    assert note["modelName"] == "Japanese Vocab Dynamic+"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_ankiconnect.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jpvocab.ankiconnect'`

- [ ] **Step 3: Implement the client**

```python
# src/jpvocab/ankiconnect.py
import requests
from beartype import beartype

ANKICONNECT_URL = "http://127.0.0.1:8765"


def _invoke(action: str, **params) -> object:
    response = requests.post(
        ANKICONNECT_URL, json={"action": action, "version": 6, "params": params}
    ).json()
    if response.get("error"):
        raise RuntimeError(f"AnkiConnect error on {action}: {response['error']}")
    return response["result"]


@beartype
def create_deck(deck_name: str) -> None:
    _invoke("createDeck", deck=deck_name)


@beartype
def find_notes(query: str) -> list[int]:
    return _invoke("findNotes", query=query)


@beartype
def add_notes(
    deck_name: str,
    model_name: str,
    field_names: list[str],
    notes_fields: list[list[str]],
) -> list[int | None]:
    notes = [
        {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": dict(zip(field_names, fields)),
            "tags": ["jpvocab-generated"],
        }
        for fields in notes_fields
    ]
    return _invoke("addNotes", notes=notes)


@beartype
def store_media_file(filename: str, data_base64: str) -> None:
    _invoke("storeMediaFile", filename=filename, data=data_base64)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_ankiconnect.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/jpvocab/ankiconnect.py tests/test_ankiconnect.py
git commit -m "feat: add AnkiConnect delivery adapter with mocked tests"
```

---

## Task 11: Top-level orchestration (draft → agent fills gaps → finalize → deliver)

**Files:**
- Create: `src/jpvocab/generate.py`
- Test: `tests/test_generate.py`

This is the module the calling agent actually uses. `draft_words` is pure and deterministic;
it returns `None` for any field it couldn't resolve (dictionary miss, no pitch data, no
Tatoeba match) plus a `source` tag per field so the run report can say how many notes
needed an LLM assist. The calling agent (not this codebase) fills any `None` fields with
its own reasoning before calling `finalize`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_generate.py
from jpvocab.generate import draft_words, finalize_draft, WordDraft

def test_draft_known_word_has_no_gaps():
    drafts = draft_words(["それ"])
    assert len(drafts) == 1
    draft = drafts[0]
    assert draft.expression == "それ"
    assert draft.reading is not None
    assert draft.meaning is not None

def test_draft_unknown_word_flags_gaps():
    drafts = draft_words(["ぞぞぞぞぞ存在しない単語です"])
    draft = drafts[0]
    assert draft.reading is None
    assert draft.meaning is None
    assert draft.source["meaning"] == "needs_llm"

def test_finalize_fills_gaps_and_assembles_fields():
    draft = WordDraft(
        expression="不明語",
        reading=None,
        meaning=None,
        pitch_svg=None,
        sentence=None,
        sentence_kana=None,
        sentence_english=None,
        source={"meaning": "needs_llm", "reading": "needs_llm", "sentence": "needs_llm"},
    )
    fields = finalize_draft(
        draft,
        reading="ふめいご",
        meaning="an unclear term (example)",
        sentence="これは<b>不明語</b>です。",
        sentence_kana="これ は ふめいご です",
        sentence_english="This is an example term.",
    )
    assert fields[0] == "不明語"
    assert fields[1] == "an unclear term (example)"
    assert "不明語" in fields[2]
    assert fields[4] == "これは<b>不明語</b>です。"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jpvocab.generate'`

- [ ] **Step 3: Implement orchestration**

```python
# src/jpvocab/generate.py
from dataclasses import dataclass, field
from pathlib import Path

from beartype import beartype

from jpvocab.assembler import assemble_note
from jpvocab.dictionary import lookup_word
from jpvocab.pitch import render_pitch_svg
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
                pitch_svg = render_pitch_svg(list(reading), accents[0])
        source["pitch"] = "kanjium" if pitch_svg else "missing"

        sentence_pair = _tatoeba_lookup.find(expression)
        sentence = sentence_pair.japanese if sentence_pair else None
        sentence_english = sentence_pair.english if sentence_pair else None
        source["sentence"] = "tatoeba" if sentence_pair else "needs_llm"

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
    reading_field = draft.pitch_svg or final_reading
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generate.py -v`
Expected: 3 passed. Note: `test_draft_known_word_has_no_gaps` depends on `それ` actually
being present in the downloaded `data/tatoeba_jpn_eng_pairs.tsv` and `data/kanjium_accents.txt`
— if Task 5/7's fetch scripts haven't been run yet in this environment, run them first.

- [ ] **Step 5: Commit**

```bash
git add src/jpvocab/generate.py tests/test_generate.py
git commit -m "feat: add top-level draft/finalize orchestration"
```

---

## Task 12: Delivery entry points + dedup guard

**Files:**
- Modify: `src/jpvocab/generate.py`
- Test: `tests/test_generate_delivery.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_generate_delivery.py
from unittest.mock import patch
from pathlib import Path
from jpvocab.generate import quick_add, build_deck

CORE_DECK = "Core 2k_6k [ Pitch Graphs, Optimized, Links ]"
CORE_MODEL = "Japanese Vocab Dynamic+"

@patch("jpvocab.generate.ankiconnect.add_notes")
@patch("jpvocab.generate.ankiconnect.find_notes")
@patch("jpvocab.generate.ankiconnect.create_deck")
def test_quick_add_skips_duplicates(mock_create, mock_find, mock_add):
    mock_find.side_effect = lambda query: [111] if "それ" in query else []
    mock_add.return_value = [222]

    report = quick_add([["それ", "that"], ["新語", "new word"]], field_names=["Expression", "Meaning"])

    assert report.skipped_duplicates == ["それ"]
    assert report.added_count == 1
    mock_add.assert_called_once()
    added_fields = mock_add.call_args.kwargs["notes_fields"]
    assert added_fields == [["新語", "new word"]]

@patch("jpvocab.generate.ankiconnect.add_notes")
@patch("jpvocab.generate.ankiconnect.find_notes")
@patch("jpvocab.generate.ankiconnect.create_deck")
def test_quick_add_dry_run_does_not_call_add_notes(mock_create, mock_find, mock_add):
    mock_find.return_value = []

    report = quick_add(
        [["新語", "new word"]], field_names=["Expression", "Meaning"], dry_run=True
    )

    mock_add.assert_not_called()
    assert report.added_count == 1
    assert report.dry_run_preview == [["新語", "new word"]]

def test_build_deck_writes_file(tmp_path: Path):
    out_path = tmp_path / "out.apkg"
    result = build_deck(
        [["それ", "that, that one", "reading", "", "sentence", "kana", "english", ""]],
        deck_name=CORE_DECK,
        out_path=out_path,
        existing_words=set(),
    )
    assert result.out_path == out_path
    assert out_path.exists()
    assert result.skipped_duplicates == []

def test_build_deck_skips_existing_words(tmp_path: Path):
    out_path = tmp_path / "out.apkg"
    result = build_deck(
        [
            ["それ", "that, that one", "reading", "", "sentence", "kana", "english", ""],
            ["新語", "new word", "reading2", "", "sentence2", "kana2", "english2", ""],
        ],
        deck_name=CORE_DECK,
        out_path=out_path,
        existing_words={"それ"},
    )
    assert result.skipped_duplicates == ["それ"]
    con_words = _read_expressions(out_path)
    assert con_words == {"新語"}


def _read_expressions(apkg_path: Path) -> set[str]:
    from jpvocab.apkg_reader import open_collection
    con = open_collection(apkg_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    return {row[0].split("\x1f")[0] for row in cur.fetchall()}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generate_delivery.py -v`
Expected: FAIL — `quick_add`/`build_deck` don't exist yet in `jpvocab.generate`

- [ ] **Step 3: Add the delivery functions to `generate.py`**

```python
# append to src/jpvocab/generate.py
from dataclasses import dataclass as _dataclass

from jpvocab import ankiconnect
from jpvocab.genanki_adapter import build_apkg
from jpvocab.notetype import CORE_NOTETYPE


@_dataclass
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
) -> QuickAddReport:
    expression_index = field_names.index("Expression")

    to_add = []
    skipped = []
    for fields in notes_fields:
        expression = fields[expression_index]
        existing = ankiconnect.find_notes(f'deck:"{deck_name}" Expression:{expression}')
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
            model_name=CORE_NOTETYPE.notetype_name,
            field_names=field_names,
            notes_fields=to_add,
        )

    return QuickAddReport(
        added_count=len(to_add), skipped_duplicates=skipped, added_note_ids=added_ids
    )


@_dataclass
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
) -> BuildDeckReport:
    to_add = []
    skipped = []
    for fields in notes_fields:
        expression = fields[expression_index]
        if expression in existing_words:
            skipped.append(expression)
        else:
            to_add.append(fields)

    build_apkg(to_add, deck_name=deck_name, out_path=out_path)
    return BuildDeckReport(out_path=out_path, skipped_duplicates=skipped)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generate_delivery.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/jpvocab/generate.py tests/test_generate_delivery.py
git commit -m "feat: add quick_add (AnkiConnect + dedup) and build_deck (genanki) entry points"
```

---

## Task 13: Full test suite + manual end-to-end smoke test

**Files:**
- None created — verification only.

- [ ] **Step 1: Run the full automated suite**

Run: `uv run pytest -v`
Expected: all tests from Tasks 1–12 pass.

- [ ] **Step 2: Manual smoke test — quick add into the real, running Anki**

With Anki open and AnkiConnect active, run a short interactive script (or a Python REPL)
that calls `jpvocab.generate.draft_words(["面白い"])`, manually supplies any `None` fields
it reports, then calls `quick_add(...)` with the finalized fields. Open Anki's browser,
find the new note in `Core 2k_6k [ Pitch Graphs, Optimized, Links ]`, and visually compare
it against a neighboring pre-existing note: field order must match, the pitch graph must
render, and no duplicate notetype (e.g. `Japanese Vocab Dynamic+-2`) should have been
created.

- [ ] **Step 3: Manual smoke test — full deck `.apkg`**

Call `jpvocab.generate.build_deck(...)` with 3–5 finalized notes to a scratch `.apkg` file,
then import it into a **throwaway Anki profile** (Anki → switch profile → Add profile) to
confirm it imports cleanly into a fresh collection and renders identically to production
cards, before ever importing into the real collection.

- [ ] **Step 4: Record results**

If either smoke test surfaces a mismatch (wrong field order, notetype not merging, pitch
graph misrendering for some accent pattern not covered by Task 4's four samples), note it
as a follow-up task rather than declaring the plan complete.

---

## Notes for whoever executes this plan

- Every step above has real, complete code — no `TODO`/`TBD`. The one deliberately open
  item is Task 13's manual smoke test outcome, which can only be known by running it.
- `draft_words`/`finalize_draft` split (Task 11) is intentional: dictionary/pitch/sentence
  lookups are deterministic code, but any gap they can't fill is explicitly out of scope
  for this codebase — the calling agent (not a library call) supplies it, per the design
  spec's decision to keep LLM fallback outside the deterministic core.
- The spec's "input resolver" (plain list / screenshot OCR / test-question context /
  named JLPT-range) is **not implemented as code** on purpose: turning a screenshot or a
  test question into a flat `list[str]` of target words is exactly the kind of judgment
  call an agent with vision and reasoning already does natively — building a bespoke OCR
  or test-question-parsing pipeline here would duplicate that for no benefit (YAGNI). This
  codebase's contract starts at `draft_words(words: list[str])`; resolving whatever the
  user hands over into that list is the calling agent's job, every time.
- Both delivery paths now dedup: `quick_add` checks the live collection via AnkiConnect
  `find_notes`; `build_deck` checks a pre-extracted `existing_words` set (call
  `jpvocab.apkg_reader.existing_expressions` against the real Core2k6k `.apkg` to build it).
- `quick_add(..., dry_run=True)` returns a `QuickAddReport.dry_run_preview` instead of
  pushing to Anki, per the design spec's dry-run requirement for live-collection safety.
