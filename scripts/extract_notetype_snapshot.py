import json
from pathlib import Path

from jpvocab.apkg_reader import open_collection
from jpvocab.pbstrings import extract_strings

CORE_APKG = Path(r"D:\User\Рабочий стол\Анки\колоды которые нужно сравнить\Core 2k_6k [ Pitch Graphs, Optimized, Links ].apkg")
NOTETYPE_ID = 1780786985931
OUT_PATH = Path(__file__).parent.parent / "src" / "jpvocab" / "notetype_snapshot.json"


def main() -> None:
    con = open_collection(CORE_APKG)
    cur = con.cursor()

    cur.execute("select name, config from notetypes where id = ?", (NOTETYPE_ID,))
    name, config = cur.fetchone()
    css_candidates = [s for s in extract_strings(config) if ".card" in s or "cardClr" in s]
    css = css_candidates[0] if css_candidates else ""

    cur.execute("select ord, name from fields where ntid = ? order by ord", (NOTETYPE_ID,))
    fields = [row[1] for row in cur.fetchall()]

    cur.execute("select ord, name, config from templates where ntid = ? order by ord", (NOTETYPE_ID,))
    templates = []
    for ordn, tname, tconfig in cur.fetchall():
        strings = extract_strings(tconfig)
        qfmt = strings[0] if len(strings) > 0 else ""
        afmt = strings[1] if len(strings) > 1 else ""
        templates.append({"name": tname, "qfmt": qfmt, "afmt": afmt})

    snapshot = {
        "notetype_name": name,
        "fields": fields,
        "templates": templates,
        "css": css,
        "deck_name": "Core 2k_6k [ Pitch Graphs, Optimized, Links ]",
    }
    OUT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(fields)} fields, {len(templates)} templates)")


if __name__ == "__main__":
    main()
