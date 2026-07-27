"""Replace bare Japanese grammatical-term jargon (labels like 動辞書形, た形, 尊敬語)
with Russian equivalents in PatternForm/Connection fields of N3 Grammar+/N2 Grammar v3
notes. Ruby on these label tokens is dropped (translated text needs no reading);
ruby on actual example words elsewhere in the field is left untouched, since this
only replaces exact dictionary-term matches, nothing else.
"""
import argparse
import json
import re

import requests

ANKICONNECT_URL = "http://127.0.0.1:8765"

TERM_DICT = {
    "尊敬語 特別形": "особая уважит. форма",
    "尊敬語特別形": "особая уважит. форма",
    "尊敬語": "уважит. форма (кэйго)",
    "謙譲語": "скромная форма (кэндзёго)",
    "動辞書形": "словарная форма гл.",
    "辞書形": "словарная форма",
    "ない形": "отриц. форма",
    "ます形": "масу-форма",
    "て形": "тэ-форма",
    "た形": "та-форма",
    "可能形": "потенциальная форма",
    "命令形": "повелительная форма",
    "意向形": "форма намерения",
    "使役形": "побудительная форма",
    "受身形": "форма страд. залога",
    "条件形": "условная форма",
    "名-の": "сущ.+の",
    "名": "сущ.",
    "動": "гл.",
}


def invoke(action: str, **params) -> object:
    r = requests.post(ANKICONNECT_URL, json={"action": action, "version": 6, "params": params}).json()
    if r.get("error"):
        raise RuntimeError(f"{action}: {r['error']}")
    return r["result"]


_TOKEN_RE = re.compile(r"<ruby>(.*?)<rt>.*?</rt></ruby>|([^<])", re.DOTALL)


def replace_jargon_terms(text: str, term_dict: dict[str, str]) -> str:
    plain_chars: list[str] = []
    spans: list[tuple[int, int, int, int]] = []  # plain_start, plain_end, orig_start, orig_end
    for m in _TOKEN_RE.finditer(text):
        token_plain = m.group(1) if m.group(1) is not None else m.group(2)
        start_plain = len(plain_chars)
        plain_chars.extend(token_plain)
        end_plain = len(plain_chars)
        spans.append((start_plain, end_plain, m.start(), m.end()))
    plain_text = "".join(plain_chars)

    terms_sorted = sorted(term_dict.keys(), key=len, reverse=True)
    covered = [False] * len(plain_text)
    replacements: list[tuple[int, int, str]] = []

    for term in terms_sorted:
        start_search = 0
        while True:
            idx = plain_text.find(term, start_search)
            if idx == -1:
                break
            end_idx = idx + len(term)
            if any(covered[idx:end_idx]):
                start_search = idx + 1
                continue
            orig_start = None
            orig_end = None
            for (ps, pe, os_, oe_) in spans:
                if ps <= idx < pe:
                    orig_start = os_
                if ps < end_idx <= pe:
                    orig_end = oe_
            if orig_start is not None and orig_end is not None:
                replacements.append((orig_start, orig_end, term_dict[term]))
                for i in range(idx, end_idx):
                    covered[i] = True
            start_search = end_idx

    replacements.sort(key=lambda r: r[0], reverse=True)
    result = text
    for (os_, oe_, repl) in replacements:
        result = result[:os_] + repl + result[oe_:]
    return result


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
            new_form = replace_jargon_terms(n.get("PatternForm", ""), TERM_DICT)
            new_conn = replace_jargon_terms(n.get("Connection", ""), TERM_DICT)
            if new_form != n.get("PatternForm", "") or new_conn != n.get("Connection", ""):
                updates.append({
                    "id": n["noteId"],
                    "fields": {"PatternForm": new_form, "Connection": new_conn},
                })

        print(f"[{deck}] {len(updates)} / {len(notes)} notes have jargon to translate")

        if not args.apply:
            for u in updates[: args.sample]:
                print(f"  noteId={u['id']}")
                print(f"    PatternForm: {u['fields']['PatternForm']!r}")
                print(f"    Connection:  {u['fields']['Connection']!r}")
        else:
            for u in updates:
                invoke("updateNoteFields", note=u)
            print(f"[{deck}] applied {len(updates)} updates")


if __name__ == "__main__":
    main()
