"""Assemble and push a batch of Shin Kanzen Master Vocab notes to the Core2k6k
vocab structure, combining the mechanical draft (reading/pitch/tatoeba match) with
hand-authored Russian content (meaning, sentence translation, sentence kana, and
occasional sentence overrides where the Tatoeba match used the wrong word sense).
"""
import argparse
import json
from pathlib import Path

import requests

ANKICONNECT_URL = "http://127.0.0.1:8765"


def invoke(action: str, **params) -> object:
    r = requests.post(ANKICONNECT_URL, json={"action": action, "version": 6, "params": params}).json()
    if r.get("error"):
        raise RuntimeError(f"{action}: {r['error']}")
    return r["result"]


def bold_first_occurrence(text: str, target: str) -> str:
    if not text or not target or target not in text or "<b>" in text:
        return text
    idx = text.index(target)
    return text[:idx] + f"<b>{target}</b>" + text[idx + len(target):]


def build_reading_field(reading_plain: str, pitch_svg: str | None) -> str:
    if pitch_svg:
        return f"{reading_plain}<!-- accent_start --><br/><br/>{pitch_svg}<!-- accent_end -->"
    return reading_plain


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", required=True)
    parser.add_argument("--content", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    drafts = {d["noteId"]: d for d in json.loads(Path(args.draft).read_text(encoding="utf-8"))}
    content = json.loads(Path(args.content).read_text(encoding="utf-8"))

    for c in content:
        d = drafts[c["noteId"]]
        expression = d["expression"]
        sentence_jp = c.get("sentence_jp") or d["tatoeba_japanese"]
        sentence_jp_bolded = bold_first_occurrence(sentence_jp, expression)

        fields = {
            "Reading": build_reading_field(d["reading_plain"], d["pitch_svg"]),
            "Meaning": c["meaning_ru"],
            "Sentence": sentence_jp_bolded,
            "Sentence-Kana": c["sentence_kana"],
            "Sentence-English": c["sentence_ru"],
        }

        if args.apply:
            invoke("updateNoteFields", note={"id": c["noteId"], "fields": fields})
            print(f"pushed {expression} ({c['noteId']})")
        else:
            print(f"=== {expression} ({c['noteId']}) ===")
            for k, v in fields.items():
                print(f"  {k}: {v[:150]!r}")


if __name__ == "__main__":
    main()
