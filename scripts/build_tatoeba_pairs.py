import tarfile
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OUT_PATH = DATA_DIR / "tatoeba_jpn_eng_pairs.tsv"


def _read_tsv_from_tar(tar_path: Path, member_suffix: str) -> list[list[str]]:
    with tarfile.open(tar_path, "r:bz2") as tar:
        member = next(m for m in tar.getmembers() if m.name.endswith(member_suffix))
        content = tar.extractfile(member).read().decode("utf-8")
    return [line.split("\t") for line in content.splitlines() if line.strip()]


def main() -> None:
    # NOTE: jpn_indices.tar.bz2 actually contains a member named "jpn_indices.csv"
    # (not "jpn_indices.tsv" as originally assumed) - verified by inspecting the
    # real downloaded archive with tarfile.getnames().
    jpn_ids = {
        row[0]
        for row in _read_tsv_from_tar(DATA_DIR / "jpn_indices.tar.bz2", "jpn_indices.csv")
        if len(row) >= 1
    }

    # links.csv pairs a sentence with ANY translation, in any language - it does
    # NOT mean the translation is English. Collect candidate translation ids per
    # jpn sentence here; language filtering happens below against sentences.csv.
    links = _read_tsv_from_tar(DATA_DIR / "links.tar.bz2", "links.csv")
    jpn_to_candidate_ids: dict[str, list[str]] = {}
    for row in links:
        if len(row) != 2:
            continue
        sentence_id, translation_id = row
        translation_id = translation_id.strip()
        if sentence_id in jpn_ids:
            jpn_to_candidate_ids.setdefault(sentence_id, []).append(translation_id)

    needed_ids = jpn_ids | {tid for ids in jpn_to_candidate_ids.values() for tid in ids}

    # Single pass over the (huge, all-languages) sentences.csv: capture text for
    # every id we might need, AND record which of those ids are actually English
    # (lang == "eng") so the join below can filter out non-English translations
    # (e.g. links to German/Chinese translations of the same Japanese sentence).
    text_by_id: dict[str, str] = {}
    eng_ids: set[str] = set()
    for row in _read_tsv_from_tar(DATA_DIR / "sentences.tar.bz2", "sentences.csv"):
        if len(row) != 3:
            continue
        sentence_id, lang, text = row
        text = text.rstrip("\n")
        if sentence_id in needed_ids:
            text_by_id[sentence_id] = text
            if lang == "eng":
                eng_ids.add(sentence_id)

    with open(OUT_PATH, "w", encoding="utf-8") as out:
        for jpn_id, candidate_ids in jpn_to_candidate_ids.items():
            jpn_text = text_by_id.get(jpn_id)
            if not jpn_text:
                continue
            for candidate_id in candidate_ids:
                if candidate_id not in eng_ids:
                    continue
                eng_text = text_by_id.get(candidate_id)
                if eng_text:
                    out.write(f"{jpn_text}\t{eng_text}\n")
                    break
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
