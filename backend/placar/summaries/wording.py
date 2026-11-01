"""The banned-wording list (decision 0018: one file for interface text and summaries)."""

from __future__ import annotations

import re
import unicodedata
from functools import cache
from pathlib import Path

from django.conf import settings


def normalize(text: str) -> str:
    """Lower case, accents removed: matching ignores both (file header)."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


@cache
def _patterns(path: Path) -> tuple[tuple[str, re.Pattern], ...]:
    terms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        term = line.strip()
        if term and not term.startswith("#"):
            terms.append((term, re.compile(rf"(?<!\w){re.escape(normalize(term))}(?!\w)")))
    return tuple(terms)


def banned_terms_in(text: str, path: Path | None = None) -> list[str]:
    """Banned terms found in `text`, as whole words or phrases."""
    source = path or Path(settings.PLACAR["BANNED_WORDING_FILE"])
    plain = normalize(text)
    return [term for term, pattern in _patterns(source) if pattern.search(plain)]
