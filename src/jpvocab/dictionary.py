from dataclasses import dataclass

from beartype import beartype
from jamdict import Jamdict

_jam = Jamdict()

# JMdict priority tags; more tags and higher-tier tags = a more common word.
_PRIORITY_WEIGHT = {
    "ichi1": 4,
    "news1": 3,
    "gai1": 3,
    "spec1": 2,
    "ichi2": 1,
    "news2": 1,
    "gai2": 1,
    "spec2": 1,
}
_USUALLY_KANA = "word usually written using kana alone"


@dataclass(frozen=True)
class DictionaryEntry:
    expression: str
    reading: str
    glosses: list[str]
    # Every reading valid for `expression`, best first (`reading` is readings[0]).
    readings: tuple[str, ...] = ()
    # Written forms of the entry (e.g. 為る for する), used to find pitch data.
    kanji_forms: tuple[str, ...] = ()


def _priority(tags: list[str]) -> int:
    return sum(_PRIORITY_WEIGHT.get(tag, 0) for tag in set(tags))


def _score(entry, expression: str) -> int:
    """How likely `entry` is the word the user meant by `expression`."""
    matching_kanji = [k for k in entry.kanji_forms if k.text == expression]
    if matching_kanji:
        return _priority([t for k in matching_kanji for t in k.pri])
    matching_kana = [k for k in entry.kana_forms if k.text == expression]
    score = _priority([t for k in matching_kana for t in k.pri])
    if any(_USUALLY_KANA in sense.misc for sense in entry.senses):
        score += 2
    return score


def _readings(entry, expression: str) -> list[str]:
    applicable = [
        form
        for form in entry.kana_forms
        if not form.restr or expression in form.restr
    ]
    if not applicable:
        applicable = list(entry.kana_forms)
    # sorted() is stable, so equally common readings keep JMdict's own order.
    ranked = sorted(applicable, key=lambda form: -_priority(form.pri))
    return [form.text for form in ranked]


@beartype
def lookup_word(expression: str) -> DictionaryEntry | None:
    result = _jam.lookup(expression)
    if not result.entries:
        return None
    entry = max(result.entries, key=lambda e: _score(e, expression))
    readings = _readings(entry, expression)
    glosses = [
        gloss.text
        for sense in entry.senses
        for gloss in sense.gloss
    ]
    return DictionaryEntry(
        expression=expression,
        reading=readings[0] if readings else "",
        glosses=glosses,
        readings=tuple(readings),
        kanji_forms=tuple(k.text for k in entry.kanji_forms),
    )
