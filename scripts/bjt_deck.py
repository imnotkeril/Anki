"""BJT Business Japanese vocab -> Anki notes, built on jpvocab (real 'Japanese Vocab Dynamic+' notetype).

Source of truth: <Japanese>/02_BJT/Source/bjt_vocab.txt
    Expression | reading | meaning | sentence (target in <b>) | translation

Safe by default: with no flags it only checks the data offline and touches nothing.

    uv run --with fugashi --with unidic-lite python scripts/bjt_deck.py              # offline summary
    uv run --with fugashi --with unidic-lite python scripts/bjt_deck.py --push --dry-run   # ask running Anki what would be added
    uv run --with fugashi --with unidic-lite python scripts/bjt_deck.py --push       # add NEW words to running Anki (AnkiConnect)
    uv run --with fugashi --with unidic-lite python scripts/bjt_deck.py --apkg <dir> # one .apkg per section

--push skips words already present in the deck (same Expression), so existing cards are never duplicated.
Sub-deck names match the already-imported deck: "BJT Business Japanese::<section>".
"""
import argparse
import re
from pathlib import Path

import fugashi

from jpvocab.assembler import assemble_note
from jpvocab.generate import DATA_DIR, build_deck, quick_add
from jpvocab.notetype import CORE_NOTETYPE
from jpvocab.pitch import render_pitch_svg, split_morae
from jpvocab.pitch_lookup import PitchLookup

ROOT = Path(__file__).resolve().parents[3]  # .../Japanese
DATA = ROOT / "02_BJT" / "Source" / "bjt_vocab.txt"
DECK_ROOT = "BJT Business Japanese"
# readings the morphological analyser gets wrong in our sentences
FIX = {"御社": "おんしゃ", "貴社": "きしゃ", "一割増": "いちわりぞう", "二日": "ふつか", "何か": "なにか",
       "太鼓判": "たいこばん", "原料高": "げんりょうだか", "一階": "いっかい", "四月": "しがつ", "十日": "とおか"}

_tagger = fugashi.Tagger()
_pitch = PitchLookup(DATA_DIR / "kanjium_accents.txt")
_KATA2HIRA = str.maketrans({chr(c): chr(c - 0x60) for c in range(0x30A1, 0x30F7)})


def parse(path: Path = DATA) -> list[tuple[str, list[str]]]:
    """-> [(section, [expr, reading, meaning, sentence, translation]), ...]"""
    out, section, seen = [], None, set()
    for line in path.read_text(encoding="utf8").splitlines():
        line = line.strip()
        if line.startswith("## "):
            section = line[3:]
        elif line and not line.startswith("#"):
            p = [x.strip() for x in line.split(" | ")]
            assert len(p) == 5, line
            assert p[0] not in seen, f"duplicate: {p[0]}"
            seen.add(p[0])
            out.append((section, p))
    return out


def _to_kana(text: str) -> str:
    words = []
    for w in _tagger(text):
        k = getattr(w.feature, "kana", None)
        if re.fullmatch(r"[゠-ヿ]+", w.surface) or not k or k == "*":
            words.append(w.surface)  # katakana words, digits, punctuation stay as-is
        else:
            words.append(k.translate(_KATA2HIRA))
    return " ".join(x for x in words if x.strip() and x not in "。、「」")


def sentence_kana(sent: str, expr: str, reading: str) -> str:
    out = []
    for i, part in enumerate(re.split(r"</?b>", sent)):
        if not part:
            continue
        if i % 2 and part == expr and "〜" not in reading:
            k = reading
        else:
            for a, b in FIX.items():
                part = part.replace(a, b)
            k = _to_kana(part)
        out.append(f"<b>{k}</b>" if i % 2 else k)
    return " ".join(x for x in out if x)


def reading_field(expr: str, reading: str) -> str:
    """Pitch-accent graph from Kanjium when the word is in it, else the plain reading."""
    try:
        accents = _pitch.get(expr, reading)
        if accents:
            return render_pitch_svg(split_morae(reading), accents[0])
    except Exception:  # phrases / patterns Kanjium has no entry for
        pass
    return reading


def build_fields(expr, reading, meaning, sent, trans) -> list[str]:
    return assemble_note(expression=expr, meaning=meaning, reading_with_pitch=reading_field(expr, reading),
                         sentence=sent, sentence_kana=sentence_kana(sent, expr, reading), sentence_english=trans)


def by_section() -> dict[str, list[list[str]]]:
    sections: dict[str, list[list[str]]] = {}
    for section, (expr, reading, meaning, sent, trans) in parse():
        sections.setdefault(f"{DECK_ROOT}::{section}", []).append(build_fields(expr, reading, meaning, sent, trans))
    return sections


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--push", action="store_true", help="add NEW words to running Anki via AnkiConnect")
    ap.add_argument("--dry-run", action="store_true", help="with --push: only report what would be added")
    ap.add_argument("--apkg", type=Path, metavar="DIR", help="write one .apkg per section into DIR")
    args = ap.parse_args()

    sections = by_section()
    print(f"{sum(map(len, sections.values()))} notes in {len(sections)} sections (notetype: {CORE_NOTETYPE.notetype_name})")
    for deck, notes in sections.items():
        if args.push:
            r = quick_add(notes, field_names=CORE_NOTETYPE.fields, deck_name=deck, dry_run=args.dry_run)
            print(f"  {deck}: add {r.added_count}, skip {len(r.skipped_duplicates)} existing")
        elif args.apkg:
            args.apkg.mkdir(parents=True, exist_ok=True)
            safe = re.sub(r'[\\/:*?"<>|]', "-", deck.split("::", 1)[1])
            r = build_deck(notes, deck_name=deck, out_path=args.apkg / f"BJT {safe}.apkg", existing_words=set())
            print(f"  {r.out_path.name}")
        else:
            print(f"  {deck}: {len(notes)}")


if __name__ == "__main__":
    main()
