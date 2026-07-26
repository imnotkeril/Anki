"""Extract a notetype's current live state from a running Anki (via AnkiConnect)
into a jpvocab notetype_*.json snapshot. Use this for notetypes that only exist in
the user's live collection (no clean .apkg source), unlike extract_notetype_snapshot.py
(Core2k6k) or extract_n3grammar_snapshot.py (hardcoded, not from a real deck).
"""
import json
import sys
from pathlib import Path

import requests

ANKICONNECT_URL = "http://127.0.0.1:8765"


def _invoke(action: str, **params) -> object:
    response = requests.post(
        ANKICONNECT_URL, json={"action": action, "version": 6, "params": params}
    ).json()
    if response.get("error"):
        raise RuntimeError(f"AnkiConnect error on {action}: {response['error']}")
    return response["result"]


def extract(model_name: str, deck_name: str, out_path: Path) -> None:
    fields = _invoke("modelFieldNames", modelName=model_name)
    templates = _invoke("modelTemplates", modelName=model_name)
    css = _invoke("modelStyling", modelName=model_name)["css"]

    snapshot = {
        "notetype_name": model_name,
        "fields": fields,
        "templates": [
            {"name": name, "qfmt": t["Front"], "afmt": t["Back"]}
            for name, t in templates.items()
        ],
        "css": css,
        "deck_name": deck_name,
    }
    out_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out_path} ({len(fields)} fields, {len(templates)} templates)")


if __name__ == "__main__":
    model_name, deck_name, out_filename = sys.argv[1], sys.argv[2], sys.argv[3]
    out_path = Path(__file__).parent.parent / "src" / "jpvocab" / out_filename
    extract(model_name, deck_name, out_path)
