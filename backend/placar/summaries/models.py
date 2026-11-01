"""Stored model summaries (decision 0010, item 11). Template summaries are never stored: they
are rebuilt from the fact sheet on each request."""

from django.db import models

from placar.legislators.models import Official


class Summary(models.Model):
    """The latest model attempt for one official and one preset window.

    It is shown only if it passed validation, its fact-sheet hash equals the current fact sheet,
    and it passes validation again when read.
    """

    official = models.ForeignKey(Official, on_delete=models.CASCADE, related_name="summaries")
    window_start = models.DateField()
    window_end = models.DateField()
    sentences = models.JSONField(default=list)  # [{"text": str, "fact_ids": [str]}]
    model_id = models.CharField(max_length=100)
    prompt_version = models.CharField(max_length=20)
    fact_sheet_hash = models.CharField(max_length=64)
    passed = models.BooleanField(default=False)
    problems = models.JSONField(default=list)  # validator messages or error names, no secrets
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["official", "window_start", "window_end"], name="summary_per_window"
            )
        ]

    def __str__(self) -> str:
        return f"Summary {self.official_id} {self.window_start}..{self.window_end}"
