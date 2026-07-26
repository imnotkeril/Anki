import json
from pathlib import Path

from jpvocab.apkg_reader import open_collection

N3_APKG = Path(r"D:\User\Рабочий стол\Анки\колоды которые нужно сравнить\N3 Grammar.apkg")
OUT_PATH = Path(__file__).parent.parent / "src" / "jpvocab" / "notetype_jpgrammar.json"

# The user's real N3 Grammar deck has NO custom CSS (bare unstyled cards) — per the
# design spec, this new notetype reuses the Core2k6k CSS shell instead of the real
# deck's own (empty) styling, so we pull the CSS from the Core2k6k snapshot rather
# than from N3 Grammar itself.
CORE_SNAPSHOT_PATH = Path(__file__).parent.parent / "src" / "jpvocab" / "notetype_snapshot.json"


def main() -> None:
    con = open_collection(N3_APKG)
    cur = con.cursor()

    # Find the real N3 Grammar+ notetype id (don't hardcode — different collections
    # assign different ids to the same-named notetype).
    cur.execute("select id, name from notetypes")
    notetype_id = None
    for ntid, name in cur.fetchall():
        if name == "N3 Grammar+":
            notetype_id = ntid
            break
    if notetype_id is None:
        raise RuntimeError("N3 Grammar+ notetype not found in N3 Grammar.apkg")

    cur.execute("select ord, name from fields where ntid = ? order by ord", (notetype_id,))
    fields = [row[1] for row in cur.fetchall()]

    core_css = json.loads(CORE_SNAPSHOT_PATH.read_text(encoding="utf-8"))["css"]

    qfmt = "<div class=\"card\"><div class=\"cardClr\">{{ExpressionClean}}</div></div>"
    afmt = (
        "<div class=\"card\">"
        "<div class=\"cardClr\">{{Expression}}</div>"
        "<br>{{Reading}}<br><br>"
        "<div class=\"cardClr\">{{Meaning}}</div>"
        "<br>{{Pattern}}<br><br>{{Connection}}"
        "</div>"
    )

    snapshot = {
        "notetype_name": "JP Grammar (jpvocab)",
        "fields": fields,
        "templates": [{"name": "Card 1", "qfmt": qfmt, "afmt": afmt}],
        "css": core_css,
        "deck_name": "N3 Grammar",
    }
    OUT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(fields)} fields)")


if __name__ == "__main__":
    main()
