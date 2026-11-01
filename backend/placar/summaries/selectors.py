"""Thin shell: loads the data for a fact sheet and picks the summary to show (decision 0010)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from placar.core.types import DateWindow, SourceRef
from placar.legislators import selectors as legislators
from placar.metrics import selectors as metric_selectors

from .facts import FactSheet, OfficialInfo, PartySpell, build_fact_sheet
from .models import Summary
from .template import template_summary
from .validator import Sentence, validate

TEMPLATE, MODEL = "template", "model"


@dataclass(frozen=True)
class ShownSentence:
    text: str
    sources: tuple[SourceRef, ...]


@dataclass(frozen=True)
class ShownSummary:
    kind: str  # "template" or "model"
    sentences: tuple[ShownSentence, ...]


def activity_loaded(house: str) -> bool:
    return any(x.house == house and x.kind == "activity" for x in legislators.latest_loads())


def fact_sheet_for(official_id: int, window: DateWindow, today: date) -> FactSheet:
    official = legislators.official_by_id(official_id)
    info = OfficialInfo(official.pk, official.parliamentary_name, official.house, official.state,
                        official.source)  # fmt: skip
    affiliations = legislators.affiliations_by_official(official.house).get(official.pk, [])
    parties = [PartySpell(a.party, a.period, a.source) for a in affiliations]
    cov = metric_selectors.coverage(official.pk, window, today)
    metrics = {}
    if activity_loaded(official.house):  # decision 0015: nothing about data not loaded yet
        metrics = metric_selectors.activity_metrics(official.pk, window, today)
    return build_fact_sheet(info, cov, parties, metrics)


def stored_sentences(summary: Summary) -> list[Sentence]:
    return [Sentence(s["text"], tuple(s["fact_ids"])) for s in summary.sentences]


def _shown(kind: str, sentences: list[Sentence], sheet: FactSheet) -> ShownSummary:
    facts = sheet.by_id()
    shown = []
    for sentence in sentences:
        refs: dict[tuple[str, str], SourceRef] = {}
        for fact_id in sentence.fact_ids:
            for ref in facts[fact_id].sources:
                refs.setdefault((ref.api_url, ref.cache_key), ref)
        shown.append(ShownSentence(sentence.text, tuple(refs.values())))
    return ShownSummary(kind, tuple(shown))


def summary_for(official_id: int, window: DateWindow, today: date) -> ShownSummary:
    """A stored model summary only if it is current and passes the validator again; otherwise
    the template summary (also the only summary for custom windows)."""
    sheet = fact_sheet_for(official_id, window, today)
    stored = Summary.objects.filter(
        official_id=official_id,
        window_start=window.start,
        window_end=window.end,
        passed=True,
        fact_sheet_hash=sheet.digest(),
    ).first()
    if stored is not None:
        sentences = stored_sentences(stored)
        if not validate(sentences, sheet):
            return _shown(MODEL, sentences, sheet)
    return _shown(TEMPLATE, template_summary(sheet), sheet)
