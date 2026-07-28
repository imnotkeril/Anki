import json
from pathlib import Path

import requests

ANKICONNECT_URL = "http://127.0.0.1:8765"


def invoke(action: str, **params) -> object:
    r = requests.post(ANKICONNECT_URL, json={"action": action, "version": 6, "params": params}).json()
    if r.get("error"):
        raise RuntimeError(f"{action}: {r['error']}")
    return r["result"]


QFMT = '<div class="card"><div class="cardClr">{{Expression}}</div></div>'
AFMT = (
    '<div class="card">'
    '<div class="cardClr">{{Expression}}</div><br>{{furigana:Reading}}'
    '<hr>{{Meaning}}'
    '<hr>{{furigana:Sentence}}<br>{{Sentence-English}}<br>{{Sentence-Kana}}'
    '</div>'
)


def main() -> None:
    core_css = json.loads((Path(__file__).parent.parent / "src" / "jpvocab" / "notetype_snapshot.json").read_text(encoding="utf-8"))["css"]

    for model in ["Japanese ShinKanzenMasterVocabN3", "Japanese ShinKanzenMasterVocabN2"]:
        backup = {
            "templates": invoke("modelTemplates", modelName=model),
            "css": invoke("modelStyling", modelName=model)["css"],
        }
        backup_path = Path(__file__).parent / f"backup_{model.replace(' ', '_')}_before_restyle.json"
        backup_path.write_text(json.dumps(backup, ensure_ascii=False, indent=2), encoding="utf-8")

        card_name = list(backup["templates"].keys())[0]
        invoke("updateModelStyling", model={"name": model, "css": core_css})
        invoke("updateModelTemplates", model={"name": model, "templates": {card_name: {"Front": QFMT, "Back": AFMT}}})
        print(f"{model} restyled (card: {card_name}), backup at {backup_path}")


if __name__ == "__main__":
    main()
