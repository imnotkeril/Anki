from unittest.mock import patch, MagicMock
from jpvocab.ankiconnect import create_deck, find_notes, add_notes, model_names, create_model


def _mock_response(result):
    resp = MagicMock()
    resp.json.return_value = {"result": result, "error": None}
    return resp


@patch("jpvocab.ankiconnect.requests.post")
def test_create_deck_sends_correct_payload(mock_post):
    mock_post.return_value = _mock_response(None)
    create_deck("Core 2k_6k [ Pitch Graphs, Optimized, Links ]")
    sent = mock_post.call_args.kwargs["json"]
    assert sent["action"] == "createDeck"
    assert sent["params"]["deck"] == "Core 2k_6k [ Pitch Graphs, Optimized, Links ]"


@patch("jpvocab.ankiconnect.requests.post")
def test_find_notes_returns_ids(mock_post):
    mock_post.return_value = _mock_response([111, 222])
    ids = find_notes('deck:"Core 2k_6k" Expression:それ')
    assert ids == [111, 222]


@patch("jpvocab.ankiconnect.requests.post")
def test_add_notes_builds_field_dict_in_order(mock_post):
    mock_post.return_value = _mock_response([12345])
    ids = add_notes(
        deck_name="Core 2k_6k [ Pitch Graphs, Optimized, Links ]",
        model_name="Japanese Vocab Dynamic+",
        field_names=["Expression", "Meaning"],
        notes_fields=[["それ", "that"]],
    )
    assert ids == [12345]
    sent = mock_post.call_args.kwargs["json"]
    note = sent["params"]["notes"][0]
    assert note["fields"] == {"Expression": "それ", "Meaning": "that"}
    assert note["deckName"] == "Core 2k_6k [ Pitch Graphs, Optimized, Links ]"
    assert note["modelName"] == "Japanese Vocab Dynamic+"


@patch("jpvocab.ankiconnect.requests.post")
def test_model_names_returns_list(mock_post):
    mock_post.return_value = _mock_response(["Basic", "Japanese Vocab Dynamic+"])
    names = model_names()
    assert names == ["Basic", "Japanese Vocab Dynamic+"]


@patch("jpvocab.ankiconnect.requests.post")
def test_create_model_sends_correct_payload(mock_post):
    mock_post.return_value = _mock_response(None)
    create_model(
        model_name="Test Model",
        fields=["Front", "Back"],
        css=".card { color: red; }",
        templates=[{"Name": "Card 1", "Front": "{{Front}}", "Back": "{{Back}}"}],
    )
    sent = mock_post.call_args.kwargs["json"]
    assert sent["action"] == "createModel"
    assert sent["params"]["modelName"] == "Test Model"
    assert sent["params"]["inOrderFields"] == ["Front", "Back"]
    assert sent["params"]["cardTemplates"] == [{"Name": "Card 1", "Front": "{{Front}}", "Back": "{{Back}}"}]
