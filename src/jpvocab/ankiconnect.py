import requests
from beartype import beartype

ANKICONNECT_URL = "http://127.0.0.1:8765"


def _invoke(action: str, **params) -> object:
    response = requests.post(
        ANKICONNECT_URL, json={"action": action, "version": 6, "params": params}
    ).json()
    if response.get("error"):
        raise RuntimeError(f"AnkiConnect error on {action}: {response['error']}")
    return response["result"]


@beartype
def create_deck(deck_name: str) -> None:
    _invoke("createDeck", deck=deck_name)


@beartype
def find_notes(query: str) -> list[int]:
    return _invoke("findNotes", query=query)


@beartype
def add_notes(
    deck_name: str,
    model_name: str,
    field_names: list[str],
    notes_fields: list[list[str]],
) -> list[int | None]:
    notes = [
        {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": dict(zip(field_names, fields)),
            "tags": ["jpvocab-generated"],
        }
        for fields in notes_fields
    ]
    return _invoke("addNotes", notes=notes)


@beartype
def store_media_file(filename: str, data_base64: str) -> None:
    _invoke("storeMediaFile", filename=filename, data=data_base64)
