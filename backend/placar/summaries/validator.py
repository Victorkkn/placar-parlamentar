"""Plain-Python checks every summary must pass before a visitor sees it (decision 0010, item 7).

The whole draft is rejected if any check fails. The template summary passes by construction,
and a test proves it for every fixture official.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from .facts import FactSheet
from .wording import banned_terms_in

MAX_SENTENCES = 6
MAX_CHARS = 200

NUMBER = re.compile(r"\d{2}/\d{2}/\d{4}|\d+(?:[.,]\d+)*%?")
WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")

# Capitalized words allowed without a fact: sentence starters and institutional terms.
# Any other capitalized word (a name, a party) must appear in the sentence's cited facts.
VOCABULARY = frozenset(
    """A As O Os Em No Na Nos Nas Entre Durante Desde De Do Da Dos Das Para Segundo Sem Com
    Não Nenhuma Nenhum Houve Foi Foram Teve Esteve Apresentou Fez Participou Registrou
    Câmara Deputados Senado Federal Plenário Congresso Nacional Mesa
    Partido Partidos Presença Proposições Participação Votações Discursos Registro Registros
    Tempo Cargo Período Licença Dias""".split()
)


@dataclass(frozen=True)
class Sentence:
    text: str
    fact_ids: tuple[str, ...]


def _tokens(values: Sequence[str]) -> tuple[set[str], set[str]]:
    numbers, words = set(), set()
    for value in values:
        numbers.update(NUMBER.findall(value))
        words.update(WORD.findall(value))
    return numbers, words


def validate(sentences: Sequence[Sentence], sheet: FactSheet) -> list[str]:
    """Problems found; an empty list means the draft passes."""
    problems: list[str] = []
    if not 1 <= len(sentences) <= MAX_SENTENCES:
        problems.append(f"sentence count {len(sentences)} not in 1..{MAX_SENTENCES}")
    facts = sheet.by_id()
    for n, sentence in enumerate(sentences, start=1):
        text = sentence.text.strip()
        where = f"sentence {n}"
        if not text:
            problems.append(f"{where}: empty")
            continue
        if len(text) > MAX_CHARS:
            problems.append(f"{where}: longer than {MAX_CHARS} characters")
        if not sentence.fact_ids:
            problems.append(f"{where}: cites no fact")
            continue
        unknown = [i for i in sentence.fact_ids if i not in facts]
        if unknown:
            problems.append(f"{where}: unknown fact ids {unknown}")
            continue
        cited = [facts[i] for i in sentence.fact_ids]
        if not any(f.sources for f in cited):
            problems.append(f"{where}: cited facts have no official source")
        numbers, words = _tokens([v for f in cited for v in f.values.values()])
        for number in NUMBER.findall(text):
            if number not in numbers:
                problems.append(f"{where}: number or date {number!r} not in its cited facts")
        for word in WORD.findall(text):
            if word[0].isupper() and word not in words and word not in VOCABULARY:
                problems.append(f"{where}: name {word!r} not in its cited facts")
        for term in banned_terms_in(text):
            problems.append(f"{where}: banned wording {term!r}")
    return problems
