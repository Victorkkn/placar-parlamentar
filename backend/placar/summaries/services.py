"""Writes model summaries ahead of time (decision 0010, items 8 and 10-11)."""

from __future__ import annotations

from datetime import date

from placar.core.types import DateWindow

from .llm import PROMPT_VERSION, DraftError, SummaryModel
from .models import Summary
from .selectors import fact_sheet_for
from .validator import validate

ATTEMPTS = 2  # one try and one retry, then the template is shown


def generate(official_id: int, window: DateWindow, model: SummaryModel, today: date) -> str:
    """Outcome: "up_to_date", "no_time_in_office", "model" or "template_fallback"."""
    sheet = fact_sheet_for(official_id, window, today)
    if sheet.days_in_office == 0:
        return "no_time_in_office"  # the template says it; no paid call needed
    digest = sheet.digest()
    current = Summary.objects.filter(
        official_id=official_id, window_start=window.start, window_end=window.end,
        fact_sheet_hash=digest, model_id=model.model_id, prompt_version=PROMPT_VERSION,
        passed=True,
    ).exists()  # fmt: skip
    if current:
        return "up_to_date"
    problems: list[str] = []
    sentences = []
    passed = False
    for attempt in range(1, ATTEMPTS + 1):
        try:
            sentences = model.draft(sheet)
        except DraftError as exc:
            problems.append(f"attempt {attempt}: {exc}")
            continue
        found = validate(sentences, sheet)
        if not found:
            passed = True
            break
        problems.extend(f"attempt {attempt}: {p}" for p in found)
    Summary.objects.update_or_create(
        official_id=official_id,
        window_start=window.start,
        window_end=window.end,
        defaults={
            "sentences": [{"text": s.text, "fact_ids": list(s.fact_ids)} for s in sentences]
            if passed
            else [],
            "model_id": model.model_id,
            "prompt_version": PROMPT_VERSION,
            "fact_sheet_hash": digest,
            "passed": passed,
            "problems": problems,
        },
    )
    return "model" if passed else "template_fallback"
