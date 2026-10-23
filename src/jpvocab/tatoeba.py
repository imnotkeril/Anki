from dataclasses import dataclass
from pathlib import Path

from beartype import beartype

# Words this short and written only in hiragana (いる, する) match inside countless
# unrelated words, so a substring hit says nothing. Better no example than a wrong one.
_MIN_HIRAGANA_ONLY_LENGTH = 3

# Sentence length window that makes a readable flashcard example.
_PREFERRED_MIN_LENGTH = 8
_PREFERRED_MAX_LENGTH = 40


@dataclass(frozen=True)
class SentencePair:
    japanese: str
    english: str
    matched: str = ""


def _is_kanji(char: str) -> bool:
    return "一" <= char <= "鿿" or char == "々"


def _is_katakana(char: str) -> bool:
    return "ァ" <= char <= "ー"


def _is_hiragana(char: str) -> bool:
    return "ぁ" <= char <= "ゟ"


def _is_hiragana_only(text: str) -> bool:
    return bool(text) and all(_is_hiragana(c) for c in text)


def _same_script_run(left: str, right: str) -> bool:
    """True when `left` and `right` are adjacent characters of a script where an
    adjacent character means we are inside a longer word (kanji compounds, katakana
    words). Hiragana is excluded on purpose: it is mostly particles and okurigana."""
    return (_is_kanji(left) and _is_kanji(right)) or (
        _is_katakana(left) and _is_katakana(right)
    )


def _candidate_forms(expression: str) -> list[str]:
    """The expression itself first, then (for kanji + kana-ending words such as
    verbs and い-adjectives) its stem, so 食べる can also find 食べた / 食べて."""
    forms = [expression]
    if len(expression) >= 2 and _is_hiragana(expression[-1]):
        stem = expression[:-1]
        if any(_is_kanji(c) for c in stem):
            forms.append(stem)
    return forms


def _match_at_word_boundary(text: str, form: str, is_stem: bool) -> bool:
    start = text.find(form)
    while start != -1:
        end = start + len(form)
        before = text[start - 1] if start > 0 else ""
        after = text[end] if end < len(text) else ""
        inside_word = (before and _same_script_run(before, form[0])) or (
            after and (_same_script_run(form[-1], after) or (is_stem and _is_kanji(after)))
        )
        if not inside_word:
            return True
        start = text.find(form, start + 1)
    return False


def _length_rank(sentence: str) -> tuple[int, int]:
    in_window = _PREFERRED_MIN_LENGTH <= len(sentence) <= _PREFERRED_MAX_LENGTH
    return (0 if in_window else 1, len(sentence))


class TatoebaLookup:
    @beartype
    def __init__(self, path: Path) -> None:
        self._pairs: list[SentencePair] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            jp, en = line.split("\t", maxsplit=1)
            self._pairs.append(SentencePair(japanese=jp, english=en))

    @beartype
    def find(self, expression: str) -> SentencePair | None:
        """Best example sentence for `expression`: a whole-word match (not a piece of
        a longer kanji/katakana word), exact form preferred over a stem match, then a
        readable length. Returns None when nothing trustworthy is found."""
        if not expression or (
            _is_hiragana_only(expression) and len(expression) < _MIN_HIRAGANA_ONLY_LENGTH
        ):
            return None

        for rank, form in enumerate(_candidate_forms(expression)):
            best: SentencePair | None = None
            for pair in self._pairs:
                if form not in pair.japanese:
                    continue
                if not _match_at_word_boundary(pair.japanese, form, is_stem=rank > 0):
                    continue
                if best is None or _length_rank(pair.japanese) < _length_rank(best.japanese):
                    best = pair
            if best is not None:
                return SentencePair(best.japanese, best.english, matched=form)
        return None
