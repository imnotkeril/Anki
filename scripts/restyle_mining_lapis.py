"""Bring Lapis (Mining deck notetype) fonts/accent color under the shared
Core2k6k tone, without touching its structure (pitch graphs, dropdown glossary,
image occlusion, etc.) — only the CSS custom-property values change.
"""
import json
from pathlib import Path

import requests

ANKICONNECT_URL = "http://127.0.0.1:8765"


def invoke(action: str, **params) -> object:
    r = requests.post(ANKICONNECT_URL, json={"action": action, "version": 6, "params": params}).json()
    if r.get("error"):
        raise RuntimeError(f"{action}: {r['error']}")
    return r["result"]


def main() -> None:
    model = "Lapis"
    css = invoke("modelStyling", modelName=model)["css"]

    backup_path = Path(__file__).parent / "backup_lapis_css_before_restyle.json"
    backup_path.write_text(json.dumps({"css": css}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"backup written to {backup_path}")

    jp_font_stack = '"Hiragino Kaku Gothic Pro", "Noto Sans JP", "Meiryo", "MS PGothic"'
    new_css = css.replace(
        "--font-serif: serif;",
        f"--font-serif: {jp_font_stack}, serif;",
    ).replace(
        "--font-sans: sans-serif;",
        f"--font-sans: {jp_font_stack}, sans-serif;",
    ).replace(
        "--bold: #50c5d9;",
        "--bold: #ab997e;",
    )

    assert new_css.count("--bold: #ab997e;") == 2, "expected exactly 2 --bold replacements"
    assert "--font-serif: serif;" not in new_css
    assert "--font-sans: sans-serif;" not in new_css

    invoke("updateModelStyling", model={"name": model, "css": new_css})
    print("Lapis restyled: font stack + bold-accent color aligned to Core2k6k tone")


if __name__ == "__main__":
    main()
