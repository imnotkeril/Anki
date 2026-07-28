"""Compute the deterministic/mechanical parts of migrating Shin Kanzen Master
Vocab N3/N2 to the Core2k6k vocab structure: parse the existing bracket-notation
Reading into a plain kana reading, look up pitch accent + render the SVG, and
find a Tatoeba sentence match. Everything else (Russian meaning, Russian
sentence translation, sentence kana reading when no Tatoeba match, or a
hand-authored sentence when there's no match at all) is left for the agent to
fill in afterward - this script only computes what's free and deterministic.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jpvocab.pitch import render_pitch_svg, split_morae
from jpvocab.pitch_lookup import PitchLookup
from jpvocab.tatoeba import TatoebaLookup

ANKICONNECT_URL = "http://127.0.0.1:8765"
DATA_DIR = Path(__file__).parent.parent / "data"

_pitch_lookup = PitchLookup(DATA_DIR / "kanjium_accents.txt")
_tatoeba_lookup = TatoebaLookup(DATA_DIR / "tatoeba_jpn_eng_pairs.tsv")


def invoke(action: str, **params) -> object:
    r = requests.post(ANKICONNECT_URL, json={"action": action, "version": 6, "params": params}).json()
    if r.get("error"):
        raise RuntimeError(f"{action}: {r['error']}")
    return r["result"]


_BRACKET_SUB_RE = re.compile(r"[^\[\]\s]+\[([^\]]+)\]")


def plain_reading_from_bracket_notation(reading_field: str) -> str:
    """'行[い]き 先[さき]' -> 'いきさき' (okurigana between/after bracket groups, e.g.
    the 'き' here, must be preserved - only the kanji-with-bracket part gets replaced
    by its reading, everything else in the field is already plain kana and stays as-is).
    '愛[あい]' -> 'あい'; 'アイデア' (no brackets at all) -> 'アイデア'."""
    substituted = _BRACKET_SUB_RE.sub(r"\1", reading_field)
    return substituted.replace(" ", "").replace("～", "")


def draft_word(expression: str, reading_field: str) -> dict:
    expression_clean = expression.replace("～", "")
    reading = plain_reading_from_bracket_notation(reading_field)

    pitch_svg = None
    accents = _pitch_lookup.get(expression_clean, reading)
    if accents:
        try:
            pitch_svg = render_pitch_svg(split_morae(reading), accents[0])
        except (ValueError, IndexError):
            pitch_svg = None

    sentence_pair = _tatoeba_lookup.find(expression_clean)

    return {
        "expression": expression,
        "reading_plain": reading,
        "pitch_svg": pitch_svg,
        "tatoeba_japanese": sentence_pair.japanese if sentence_pair else None,
        "tatoeba_english": sentence_pair.english if sentence_pair else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    note_ids = invoke("findNotes", query=f'deck:"{args.deck}"')
    infos = invoke("notesInfo", notes=note_ids)
    if args.limit:
        infos = infos[: args.limit]

    drafts = []
    pitch_hits = 0
    tatoeba_hits = 0
    for n in infos:
        expr = n["fields"]["Expression"]["value"]
        reading_field = n["fields"]["Reading"]["value"]
        meaning_en = n["fields"]["Meaning"]["value"]
        d = draft_word(expr, reading_field)
        d["noteId"] = n["noteId"]
        d["meaning_en"] = meaning_en
        if d["pitch_svg"]:
            pitch_hits += 1
        if d["tatoeba_japanese"]:
            tatoeba_hits += 1
        drafts.append(d)

    Path(args.out).write_text(json.dumps(drafts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(drafts)} words drafted -> {args.out}")
    print(f"pitch data found: {pitch_hits} / {len(drafts)}")
    print(f"Tatoeba sentence found: {tatoeba_hits} / {len(drafts)}")


if __name__ == "__main__":
    main()
