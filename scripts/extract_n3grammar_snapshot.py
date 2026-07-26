import json
from pathlib import Path

OUT_PATH = Path(__file__).parent.parent / "src" / "jpvocab" / "notetype_jpgrammar.json"

# The real N3 Grammar.apkg deck has neither these fields nor any custom CSS — it can no
# longer be read 1:1 for the field list, since the redesigned notetype introduces fields
# (Construction, PatternForm, PatternMeaning) that don't exist in the real deck at all.
# So the field list is hardcoded here to match what the new template needs, while the
# CSS shell is still pulled from Core2k6k exactly as before.
FIELDS = [
    "Expression",
    "Reading",
    "Construction",
    "Meaning",
    "PatternForm",
    "PatternMeaning",
    "Connection",
    "ExpressionClean",
]

CORE_SNAPSHOT_PATH = Path(__file__).parent.parent / "src" / "jpvocab" / "notetype_snapshot.json"

# The Core2k6k stylesheet has no CSS custom properties at all (no `--fg-subtle` or any
# other `--*` variable defined) — confirmed by inspecting notetype_snapshot.json's css
# before trusting it. The new afmt below relies on `var(--fg-subtle)` for muted labels,
# so that variable is appended here to keep the template functional; without it the
# `color: var(--fg-subtle)` declarations would just fall back to the inherited text
# color (harmless, but not the intended muted look).
FG_SUBTLE_DEFINITION = "\n:root {\n  --fg-subtle: #8a7c6a;\n}\n"


def main() -> None:
    core_css = json.loads(CORE_SNAPSHOT_PATH.read_text(encoding="utf-8"))["css"]
    css = core_css + FG_SUBTLE_DEFINITION

    qfmt = "<div class=\"card\"><div class=\"cardClr\">{{ExpressionClean}}</div></div>"
    afmt = (
        "<div class=\"card\">"
        "<div class=\"cardClr\">{{Expression}}</div>"
        "<hr>{{Reading}}"
        "<hr><b style=\"font-size:1.3em\">{{Construction}}</b>"
        "<hr>{{Meaning}}"
        "<hr><span style=\"color:var(--fg-subtle)\">Конструкция:</span> {{PatternForm}}<br>"
        "<span style=\"color:var(--fg-subtle)\">Значение:</span> {{PatternMeaning}}"
        "<hr><span style=\"color:var(--fg-subtle)\">Примеры:</span><br>{{Connection}}"
        "</div>"
    )

    snapshot = {
        "notetype_name": "JP Grammar (jpvocab)",
        "fields": FIELDS,
        "templates": [{"name": "Card 1", "qfmt": qfmt, "afmt": afmt}],
        "css": css,
        "deck_name": "N3 Grammar",
    }
    OUT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(FIELDS)} fields)")


if __name__ == "__main__":
    main()
