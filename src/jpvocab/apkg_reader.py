import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path

import zstandard
from beartype import beartype


@beartype
def open_collection(apkg_path: Path) -> sqlite3.Connection:
    """Unzip an .apkg, decompress its collection (zstd-framed or plain), open it as sqlite.

    Handles both:
    - Anki 2.1.45+ format: collection.anki21b (zstandard compressed)
    - Older/genanki format: collection.anki2 (plain SQLite)
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="jpvocab_apkg_"))
    try:
        with zipfile.ZipFile(apkg_path) as zf:
            # Try modern format first (.anki21b with zstandard)
            if "collection.anki21b" in zf.namelist():
                zf.extract("collection.anki21b", tmp_dir)
                compressed_path = tmp_dir / "collection.anki21b"
                db_path = tmp_dir / "collection.sqlite"
                dctx = zstandard.ZstdDecompressor()
                with open(compressed_path, "rb") as f_in, open(db_path, "wb") as f_out:
                    dctx.copy_stream(f_in, f_out)
            elif "collection.anki2" in zf.namelist():
                # Fallback to older format (.anki2 plain SQLite)
                zf.extract("collection.anki2", tmp_dir)
                db_path = tmp_dir / "collection.anki2"
            else:
                raise FileNotFoundError(
                    "No collection.anki21b or collection.anki2 found in .apkg"
                )

        # Open disk connection and back it up to in-memory connection
        disk_con = sqlite3.connect(db_path)
        mem_con = sqlite3.connect(":memory:")
        disk_con.backup(mem_con)
        disk_con.close()

        return mem_con
    finally:
        # Clean up the temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)


@beartype
def existing_expressions(apkg_path: Path, notetype_id: int, field_index: int) -> set[str]:
    """Read every note's field at `field_index` for a given notetype — used to dedup
    full-deck generation against words already present in the real collection."""
    con = open_collection(apkg_path)
    try:
        cur = con.cursor()
        cur.execute("select flds from notes where mid = ?", (notetype_id,))
        words = set()
        for (flds,) in cur.fetchall():
            parts = flds.split("\x1f")
            words.add(parts[field_index])
        return words
    finally:
        con.close()
