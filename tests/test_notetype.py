from pathlib import Path
import json
from jpvocab.notetype import CORE_NOTETYPE, load_notetype


def test_core_notetype_fields():
    assert CORE_NOTETYPE.fields == [
        "Expression", "Meaning", "Reading", "Audio",
        "Sentence", "Sentence-Kana", "Sentence-English", "Sentence Audio",
    ]
    assert CORE_NOTETYPE.deck_name == "Core 2k_6k [ Pitch Graphs, Optimized, Links ]"
    assert len(CORE_NOTETYPE.templates) == 2
    assert CORE_NOTETYPE.css != ""


def test_load_notetype_generic(tmp_path: Path):
    snapshot_data = {
        "notetype_name": "Test Notetype",
        "fields": ["A", "B"],
        "templates": [{"name": "Card 1", "qfmt": "{{A}}", "afmt": "{{B}}"}],
        "css": ".card { color: red; }",
        "deck_name": "Test Deck",
    }
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_data), encoding="utf-8")
    snapshot = load_notetype(path)
    assert snapshot.notetype_name == "Test Notetype"
    assert snapshot.fields == ["A", "B"]
    assert snapshot.templates[0].qfmt == "{{A}}"
