"""Replace literal newlines with <br> in PatternForm/PatternMeaning/Connection
fields of N3 Grammar+/N2 Grammar v3 notes. The original content used bare '\\n'
between example lines, relying on a 'white-space: pre-line' CSS rule that got
dropped when the notetype was restyled onto the shared Core2k6k stylesheet.
Using <br> directly in the field content is more robust (matches how the
reference JP Grammar card's content is authored) and doesn't depend on any
future CSS change.
"""
import argparse

import requests

ANKICONNECT_URL = "http://127.0.0.1:8765"


def invoke(action: str, **params) -> object:
    r = requests.post(ANKICONNECT_URL, json={"action": action, "version": 6, "params": params}).json()
    if r.get("error"):
        raise RuntimeError(f"{action}: {r['error']}")
    return r["result"]


FIELDS = ["PatternForm", "PatternMeaning", "Connection"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--sample", type=int, default=8)
    args = parser.parse_args()

    for deck in ["Japanese Grammar::Shin Kanzen Master N3", "Japanese Grammar::Shin Kanzen Master N2"]:
        note_ids = invoke("findNotes", query=f'deck:"{deck}"')
        infos = invoke("notesInfo", notes=note_ids)
        notes = [{k: v["value"] for k, v in n["fields"].items()} | {"noteId": n["noteId"]} for n in infos]

        updates = []
        for n in notes:
            changed_fields = {}
            for field in FIELDS:
                value = n.get(field, "")
                if "\n" in value:
                    changed_fields[field] = value.replace("\n", "<br>")
            if changed_fields:
                updates.append({"id": n["noteId"], "fields": changed_fields})

        print(f"[{deck}] {len(updates)} / {len(notes)} notes have literal newlines to convert")

        if not args.apply:
            for u in updates[: args.sample]:
                print(f"  noteId={u['id']}")
                for field, value in u["fields"].items():
                    print(f"    {field}: {value!r}")
        else:
            for u in updates:
                invoke("updateNoteFields", note=u)
            print(f"[{deck}] applied {len(updates)} updates")


if __name__ == "__main__":
    main()
