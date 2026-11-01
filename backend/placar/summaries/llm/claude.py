"""Claude API adapter (decision 0010, item 2). The only module that imports `anthropic`.

Structured outputs: `output_config.format` with a JSON schema (checked in the Claude API
reference on 2026-11-01). Tests never call this; they use a fake model.
"""

from __future__ import annotations

import anthropic

from ..facts import FactSheet
from ..validator import Sentence
from .base import OUTPUT_SCHEMA, SYSTEM_PROMPT, DraftError, parse_draft, user_message


class ClaudeSummaryModel:
    def __init__(self, api_key: str, model_id: str, timeout: float = 120.0) -> None:
        self.model_id = model_id
        self._client = anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=2)

    def draft(self, sheet: FactSheet) -> list[Sentence]:
        try:
            response = self._client.messages.create(
                model=self.model_id,
                max_tokens=8000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message(sheet)}],
                output_config={
                    "effort": "low",
                    "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
                },
            )
        except anthropic.APIError as exc:
            # Only the error type: messages could echo request details.
            raise DraftError(type(exc).__name__) from None
        if response.stop_reason != "end_turn":
            raise DraftError(f"stop_reason={response.stop_reason}")
        text = next((b.text for b in response.content if b.type == "text"), None)
        if text is None:
            raise DraftError("no text in response")
        return parse_draft(text)
