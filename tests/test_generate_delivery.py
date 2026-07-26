from unittest.mock import patch
from pathlib import Path
from jpvocab.generate import quick_add, build_deck

CORE_DECK = "Core 2k_6k [ Pitch Graphs, Optimized, Links ]"
CORE_MODEL = "Japanese Vocab Dynamic+"

@patch("jpvocab.generate.ankiconnect.add_notes")
@patch("jpvocab.generate.ankiconnect.find_notes")
@patch("jpvocab.generate.ankiconnect.create_deck")
def test_quick_add_skips_duplicates(mock_create, mock_find, mock_add):
    mock_find.side_effect = lambda query: [111] if "それ" in query else []
    mock_add.return_value = [222]

    report = quick_add([["それ", "that"], ["新語", "new word"]], field_names=["Expression", "Meaning"])

    assert report.skipped_duplicates == ["それ"]
    assert report.added_count == 1
    mock_add.assert_called_once()
    added_fields = mock_add.call_args.kwargs["notes_fields"]
    assert added_fields == [["新語", "new word"]]

@patch("jpvocab.generate.ankiconnect.add_notes")
@patch("jpvocab.generate.ankiconnect.find_notes")
@patch("jpvocab.generate.ankiconnect.create_deck")
def test_quick_add_escapes_tricky_expression_in_query(mock_create, mock_find, mock_add):
    mock_find.return_value = []
    mock_add.return_value = [1]

    quick_add([["四 (× yon)", "four"]], field_names=["Expression", "Meaning"])

    query = mock_find.call_args.args[0]
    assert 'Expression:"四 (× yon)"' in query

@patch("jpvocab.generate.ankiconnect.add_notes")
@patch("jpvocab.generate.ankiconnect.find_notes")
@patch("jpvocab.generate.ankiconnect.create_deck")
def test_quick_add_dry_run_does_not_call_add_notes(mock_create, mock_find, mock_add):
    mock_find.return_value = []

    report = quick_add(
        [["新語", "new word"]], field_names=["Expression", "Meaning"], dry_run=True
    )

    mock_add.assert_not_called()
    assert report.added_count == 1
    assert report.dry_run_preview == [["新語", "new word"]]

def test_build_deck_writes_file(tmp_path: Path):
    out_path = tmp_path / "out.apkg"
    result = build_deck(
        [["それ", "that, that one", "reading", "", "sentence", "kana", "english", ""]],
        deck_name=CORE_DECK,
        out_path=out_path,
        existing_words=set(),
    )
    assert result.out_path == out_path
    assert out_path.exists()
    assert result.skipped_duplicates == []

def test_build_deck_skips_existing_words(tmp_path: Path):
    out_path = tmp_path / "out.apkg"
    result = build_deck(
        [
            ["それ", "that, that one", "reading", "", "sentence", "kana", "english", ""],
            ["新語", "new word", "reading2", "", "sentence2", "kana2", "english2", ""],
        ],
        deck_name=CORE_DECK,
        out_path=out_path,
        existing_words={"それ"},
    )
    assert result.skipped_duplicates == ["それ"]
    con_words = _read_expressions(out_path)
    assert con_words == {"新語"}


def _read_expressions(apkg_path: Path) -> set[str]:
    from jpvocab.apkg_reader import open_collection
    con = open_collection(apkg_path)
    cur = con.cursor()
    cur.execute("select flds from notes")
    return {row[0].split("\x1f")[0] for row in cur.fetchall()}


# append to tests/test_generate_delivery.py
from jpvocab.engrammar import EN_GRAMMAR_NOTETYPE, build_note as build_engrammar_note

@patch("jpvocab.generate.ankiconnect.add_notes")
@patch("jpvocab.generate.ankiconnect.find_notes")
@patch("jpvocab.generate.ankiconnect.create_deck")
def test_quick_add_works_for_non_core_notetype(mock_create, mock_find, mock_add):
    mock_find.return_value = []
    mock_add.return_value = [999]

    fields = build_engrammar_note({
        "Pattern": "on the other hand",
        "Meaning": "с другой стороны",
        "Example": "Example sentence.",
        "Register": "formal",
    })

    report = quick_add(
        [fields],
        field_names=EN_GRAMMAR_NOTETYPE.fields,
        deck_name=EN_GRAMMAR_NOTETYPE.deck_name,
        model_name=EN_GRAMMAR_NOTETYPE.notetype_name,
        dedup_field="Pattern",
    )

    assert report.added_count == 1
    sent_model_name = mock_add.call_args.kwargs["model_name"]
    assert sent_model_name == "EN Grammar Collocations (jpvocab)"


def test_build_deck_works_for_non_core_notetype(tmp_path):
    fields = build_engrammar_note({
        "Pattern": "on the other hand",
        "Meaning": "с другой стороны",
        "Example": "Example sentence.",
        "Register": "formal",
    })
    out_path = tmp_path / "engrammar_deck_test.apkg"
    result = build_deck(
        [fields],
        deck_name=EN_GRAMMAR_NOTETYPE.deck_name,
        out_path=out_path,
        existing_words=set(),
        notetype=EN_GRAMMAR_NOTETYPE,
    )
    assert result.out_path.exists()


# append to tests/test_generate_delivery.py
from jpvocab.jpgrammar import JP_GRAMMAR_NOTETYPE

@patch("jpvocab.generate.ankiconnect.add_notes")
@patch("jpvocab.generate.ankiconnect.model_names")
@patch("jpvocab.generate.ankiconnect.create_model")
@patch("jpvocab.generate.ankiconnect.find_notes")
@patch("jpvocab.generate.ankiconnect.create_deck")
def test_quick_add_creates_missing_model(mock_create_deck, mock_find, mock_create_model, mock_model_names, mock_add):
    mock_find.return_value = []
    mock_model_names.return_value = ["Basic"]  # JP Grammar notetype not present yet
    mock_add.return_value = [1]

    quick_add(
        [["expr", "reading", "meaning", "pattern", "connection", "clean"]],
        field_names=JP_GRAMMAR_NOTETYPE.fields,
        deck_name=JP_GRAMMAR_NOTETYPE.deck_name,
        model_name=JP_GRAMMAR_NOTETYPE.notetype_name,
        dedup_field="Expression",
        notetype=JP_GRAMMAR_NOTETYPE,
    )

    mock_create_model.assert_called_once()
    sent_name = mock_create_model.call_args.kwargs["model_name"]
    assert sent_name == JP_GRAMMAR_NOTETYPE.notetype_name


@patch("jpvocab.generate.ankiconnect.add_notes")
@patch("jpvocab.generate.ankiconnect.model_names")
@patch("jpvocab.generate.ankiconnect.create_model")
@patch("jpvocab.generate.ankiconnect.find_notes")
@patch("jpvocab.generate.ankiconnect.create_deck")
def test_quick_add_skips_model_creation_if_already_exists(mock_create_deck, mock_find, mock_create_model, mock_model_names, mock_add):
    mock_find.return_value = []
    mock_model_names.return_value = [JP_GRAMMAR_NOTETYPE.notetype_name]  # already exists
    mock_add.return_value = [1]

    quick_add(
        [["expr", "reading", "meaning", "pattern", "connection", "clean"]],
        field_names=JP_GRAMMAR_NOTETYPE.fields,
        deck_name=JP_GRAMMAR_NOTETYPE.deck_name,
        model_name=JP_GRAMMAR_NOTETYPE.notetype_name,
        dedup_field="Expression",
        notetype=JP_GRAMMAR_NOTETYPE,
    )

    mock_create_model.assert_not_called()
