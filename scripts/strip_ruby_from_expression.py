"""Strip <ruby> furigana annotations from the Expression/ExpressionClean fields of
N3 Grammar+/N2 Grammar v3 notes. The separate Reading field already gives the full
sentence's kana reading on its own line (matching the reference JP Grammar card and
Core2k6k's own convention), so ruby directly in the sentence is redundant. Leaves
<b> bolding intact. Does NOT touch Connection (ruby there is the only reading source
for its short embedded examples, so it stays).
"""
import argparse
import json
import re
from pathlib import Path

import requests

ANKICONNECT_URL = "http://127.0.0.1:8765"


def invoke(action: str, **params) -> object:
    r = requests.post(ANKICONNECT_URL, json={"action": action, "version": 6, "params": params}).json()
    if r.get("error"):
        raise RuntimeError(f"{action}: {r['error']}")
    return r["result"]


_RUBY_RE = re.compile(r"<ruby>(.*?)<rt>.*?</rt></ruby>", re.DOTALL)


def strip_ruby(text: str) -> str:
    return _RUBY_RE.sub(r"\1", text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--sample", type=int, default=5)
    args = parser.parse_args()

    for deck in ["Japanese Grammar::Shin Kanzen Master N3", "Japanese Grammar::Shin Kanzen Master N2"]:
        note_ids = invoke("findNotes", query=f'deck:"{deck}"')
        infos = invoke("notesInfo", notes=note_ids)
        notes = [{k: v["value"] for k, v in n["fields"].items()} | {"noteId": n["noteId"]} for n in infos]

        updates = []
        for n in notes:
            new_expr = strip_ruby(n.get("Expression", ""))
            new_expr_clean = strip_ruby(n.get("ExpressionClean", ""))
            if new_expr != n.get("Expression", "") or new_expr_clean != n.get("ExpressionClean", ""):
                updates.append({"id": n["noteId"], "fields": {"Expression": new_expr, "ExpressionClean": new_expr_clean}})

        print(f"[{deck}] {len(updates)} / {len(notes)} notes have ruby to strip")

        if not args.apply:
            for u in updates[: args.sample]:
                print(f"  noteId={u['id']}")
                print(f"    Expression:      {u['fields']['Expression']!r}")
                print(f"    ExpressionClean: {u['fields']['ExpressionClean']!r}")
        else:
            for u in updates:
                invoke("updateNoteFields", note=u)
            print(f"[{deck}] applied {len(updates)} updates")


if __name__ == "__main__":
    main()
