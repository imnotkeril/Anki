import sqlite3
import tempfile
import zipfile
from pathlib import Path

import zstandard
from beartype import beartype


@beartype
def open_collection(apkg_path: Path) -> sqlite3.Connection:
    """Unzip an .apkg, decompress its zstd-framed collection, open it as sqlite."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="jpvocab_apkg_"))
    with zipfile.ZipFile(apkg_path) as zf:
        zf.extract("collection.anki21b", tmp_dir)
    compressed_path = tmp_dir / "collection.anki21b"
    db_path = tmp_dir / "collection.sqlite"
    dctx = zstandard.ZstdDecompressor()
    with open(compressed_path, "rb") as f_in, open(db_path, "wb") as f_out:
        dctx.copy_stream(f_in, f_out)
    return sqlite3.connect(db_path)


@beartype
def existing_expressions(apkg_path: Path, notetype_id: int, field_index: int) -> set[str]:
    """Read every note's field at `field_index` for a given notetype — used to dedup
    full-deck generation against words already present in the real collection."""
    con = open_collection(apkg_path)
    cur = con.cursor()
    cur.execute("select flds from notes where mid = ?", (notetype_id,))
    words = set()
    for (flds,) in cur.fetchall():
        parts = flds.split("\x1f")
        words.add(parts[field_index])
    con.close()
    return words
