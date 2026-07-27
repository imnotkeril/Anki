"""Migrate N3 Grammar+ / N2 Grammar v3 note content to the reference JP Grammar
structure: split the merged Pattern field into PatternForm/PatternMeaning, and
extract the bolded construction from Expression into its own Construction field.
Does NOT touch scheduling/history (field values only, same notetype, same cards).
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


def extract_construction(expression: str) -> str:
    m = re.search(r"<b>(.*?)</b>", expression)
    return m.group(1) if m else ""


def split_pattern(pattern: str) -> tuple[str, str]:
    if "Значение:" in pattern:
        form, meaning = pattern.split("Значение:", 1)
        return form.strip(), meaning.strip()
    return pattern.strip(), ""


def build_updates(notes: list[dict]) -> tuple[list[dict], list[int]]:
    updates = []
    no_meaning_marker = []
    for n in notes:
        construction = extract_construction(n.get("Expression", ""))
        pattern_form, pattern_meaning = split_pattern(n.get("Pattern", ""))
        if not pattern_meaning:
            no_meaning_marker.append(n["noteId"])
        updates.append({
            "id": n["noteId"],
            "fields": {
                "Construction": construction,
                "PatternForm": pattern_form,
                "PatternMeaning": pattern_meaning,
            },
        })
    return updates, no_meaning_marker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="actually write to Anki; default is dry-run preview only")
    parser.add_argument("--sample", type=int, default=5, help="how many notes to preview in dry-run mode")
    args = parser.parse_args()

    decks_models = [
        ("Japanese Grammar::Shin Kanzen Master N3", "N3 Grammar+"),
        ("Japanese Grammar::Shin Kanzen Master N2", "N2 Grammar v3"),
    ]

    for deck, model in decks_models:
        note_ids = invoke("findNotes", query=f'deck:"{deck}"')
        infos = invoke("notesInfo", notes=note_ids)
        notes = [{k: v["value"] for k, v in n["fields"].items()} | {"noteId": n["noteId"]} for n in infos]

        for field in ["Construction", "PatternForm", "PatternMeaning"]:
            existing_fields = invoke("modelFieldNames", modelName=model)
            if field not in existing_fields:
                invoke("modelFieldAdd", modelName=model, fieldName=field)
        print(f"[{model}] ensured Construction/PatternForm/PatternMeaning fields exist")

        updates, no_meaning = build_updates(notes)
        print(f"[{model}] {len(updates)} notes total, {len(no_meaning)} have no 'Значение:' marker (PatternMeaning will be empty for these)")

        if not args.apply:
            print(f"[{model}] DRY RUN — showing first {args.sample} notes:")
            for u in updates[: args.sample]:
                print(f"  noteId={u['id']}")
                print(f"    Construction:     {u['fields']['Construction']!r}")
                print(f"    PatternForm:      {u['fields']['PatternForm']!r}")
                print(f"    PatternMeaning:   {u['fields']['PatternMeaning']!r}")
            if no_meaning:
                print(f"  note ids with NO 'Значение:' marker (first 10): {no_meaning[:10]}")
        else:
            for u in updates:
                invoke("updateNoteFields", note=u)
            print(f"[{model}] applied {len(updates)} field updates")


if __name__ == "__main__":
    main()
