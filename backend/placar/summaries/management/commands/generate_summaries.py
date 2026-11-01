"""Generate model summaries for the preset windows (decision 0010, item 10).

Paid calls happen only here, never during a visitor's request. Without ANTHROPIC_API_KEY the
command stops: the app shows template summaries. With a key it lists the planned calls and
stops unless `--yes` is given (Phase D plan, choice 1A: the owner approves each run).
"""

from collections import Counter
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from placar.core.types import DateWindow
from placar.legislators import selectors as legislators
from placar.metrics import selectors as metric_selectors
from placar.summaries.llm import configured_model
from placar.summaries.services import generate


def preset_windows() -> list[DateWindow]:
    """The same presets as the frontend: current legislature and the last 2 years."""
    people = [x.reference_date for x in legislators.latest_loads() if x.kind == "people"]
    if not people:
        raise CommandError("No data loaded. Run normalize_current first.")
    snapshot = max(people)
    windows = [DateWindow(snapshot - timedelta(days=729), snapshot)]
    legislature = legislators.legislature_on(snapshot)
    if legislature:
        windows.insert(0, DateWindow(legislature.start, snapshot))
    return windows


class Command(BaseCommand):
    help = "Generate model summaries for the preset windows (needs ANTHROPIC_API_KEY and --yes)."

    def add_arguments(self, parser):
        parser.add_argument("--house", choices=["CAMARA", "SENADO"], default=None)
        parser.add_argument("--limit", type=int, default=None, help="First N officials only.")
        parser.add_argument("--yes", action="store_true", help="Confirm the paid run.")

    def handle(self, *args, **options):
        model = configured_model()
        if model is None:
            self.stdout.write("ANTHROPIC_API_KEY is not set: the app uses template summaries.")
            return
        windows = preset_windows()
        today = windows[-1].end
        officials = list(legislators.officials(options["house"]).values_list("pk", flat=True))
        officials = officials[: options["limit"]] if options["limit"] else officials
        jobs = []
        for window in windows:
            coverages = metric_selectors.coverage_bulk(options["house"], window, today)
            jobs += [(pk, window) for pk in officials if coverages[pk].days_in_office > 0]
        self.stdout.write(
            f"Model: {settings.PLACAR['SUMMARY_MODEL']}. Windows: "
            + ", ".join(f"{w.start}..{w.end}" for w in windows)
            + f". Officials with time in office: {len(jobs)} summaries, at most {2 * len(jobs)}"
            " calls (summaries already up to date are skipped)."
        )
        if not options["yes"]:
            self.stdout.write("Nothing sent. Run again with --yes to confirm this paid run.")
            return
        outcomes = Counter(generate(pk, window, model, today) for pk, window in jobs)
        self.stdout.write("Done: " + ", ".join(f"{k} {v}" for k, v in sorted(outcomes.items())))
