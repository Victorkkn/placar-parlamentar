"""Model adapter entry point. Without ANTHROPIC_API_KEY there is no model: templates only."""

from __future__ import annotations

import os

from django.conf import settings

from .base import PROMPT_VERSION, DraftError, SummaryModel

__all__ = ["PROMPT_VERSION", "DraftError", "SummaryModel", "configured_model"]


def configured_model() -> SummaryModel | None:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return None
    from .claude import ClaudeSummaryModel  # the provider SDK loads only when a key is set

    return ClaudeSummaryModel(key, settings.PLACAR["SUMMARY_MODEL"])
