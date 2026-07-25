from dataclasses import dataclass

from beartype import beartype
from jamdict import Jamdict

_jam = Jamdict()


@dataclass(frozen=True)
class DictionaryEntry:
    expression: str
    reading: str
    glosses: list[str]


@beartype
def lookup_word(expression: str) -> DictionaryEntry | None:
    result = _jam.lookup(expression)
    if not result.entries:
        return None
    entry = result.entries[0]
    reading = entry.kana_forms[0].text if entry.kana_forms else ""
    glosses = [
        gloss.text
        for sense in entry.senses
        for gloss in sense.gloss
    ]
    return DictionaryEntry(expression=expression, reading=reading, glosses=glosses)
