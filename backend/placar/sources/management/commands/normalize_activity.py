"""Load cached activity data into the database (Phase B2). Offline; no network."""

from django.core.management.base import BaseCommand, CommandError

from placar.activity.services import replace_activity
from placar.sources.activity_runner import freshness_for
from placar.sources.cache import CacheMissError, Freshness
from placar.sources.clients.camara import CamaraClient
from placar.sources.clients.camara_activity import CamaraActivityClient
from placar.sources.clients.senado import SenadoClient
from placar.sources.clients.senado_activity import SenadoActivityClient
from placar.sources.normalize import activity as normalize

from ._common import reference_date
from .normalize_current import offline_fetcher


class Missing:
    def __init__(self) -> None:
        self.items: list[str] = []

    def call(self, label, work, default):
        try:
            return work()
        except CacheMissError as exc:
            self.items.append(f"{label}: {exc}")
            return default


class Command(BaseCommand):
    help = "Normalize cached activity data (votes, attendance, bills, memberships, speeches)."

    def add_arguments(self, parser):
        parser.add_argument("--date", default=None, help="Date used by fetch_activity.")

    def handle(self, *args, **options):
        day = reference_date(options["date"])
        try:
            reports = [self._senado(day), self._camara(day)]
        except CacheMissError as exc:
            raise CommandError(f"not in the cache: {exc}. Run fetch_activity first.") from exc
        for title, counts, notes, missing in reports:
            self.stdout.write(f"== {title}")
            for name, value in counts.items():
                self.stdout.write(f"  {name}: {value}")
            self.stdout.write(f"  unknown vote options: {notes.unknown_options or 'none'}")
            self.stdout.write(f"  missing from cache (skipped): {len(missing.items)}")
            for item in missing.items[:20]:
                self.stdout.write(f"    - {item}")

    def _camara(self, day):
        fetcher = offline_fetcher("camara")
        people, act, miss = CamaraClient(fetcher), CamaraActivityClient(fetcher), Missing()
        pick = freshness_for(day)
        leg = people.legislature_on(day)
        end = min(day, leg.end)
        sessions = act.plenary_sessions(leg.start, end, pick)
        held = {s.event_id: s for s in sessions if (s.situation or "") == "Encerrada"}
        presences = []
        for s in held.values():
            presences += miss.call(
                f"presence {s.event_id}", lambda s=s: act.presence(s.event_id, Freshness.DAILY), []
            )
        votings = list({v.voting_id: v for v in act.plenary_votings(leg.start, end, pick)}.values())
        ballots = []
        for v in votings:
            ballots += miss.call(
                f"ballots {v.voting_id}", lambda v=v: act.ballots(v.voting_id, Freshness.DAILY), []
            )
        deputies = sorted({r.deputy_id for r in people.deputies(leg.number, Freshness.DAILY)})
        years = list(range(leg.start.year, end.year + 1))
        bills, memberships, speeches = [], [], []
        for d in deputies:
            bills += miss.call(f"bills {d}", lambda d=d: act.bills(d, years, Freshness.DAILY), [])
            memberships += miss.call(
                f"memberships {d}",
                lambda d=d: act.memberships(d, leg.start, end, Freshness.DAILY),
                [],
            )
            speeches += miss.call(
                f"speeches {d}", lambda d=d: act.speeches(d, leg.number, Freshness.DAILY), []
            )
        bundle, notes = normalize.camara(
            list(held.values()), presences, votings, ballots, bills, memberships, speeches
        )
        return "camara activity", replace_activity(bundle), notes, miss

    def _senado(self, day):
        fetcher = offline_fetcher("senado")
        people, act, miss = SenadoClient(fetcher), SenadoActivityClient(fetcher), Missing()
        pick = freshness_for(day)
        leg = people.legislature_on(day)
        end = min(day, leg.end)
        codes, _ = act.vote_codes()
        votings, ballots = act.votings(leg.start, end, pick)
        took = people.senators_in_legislature(leg.number, Freshness.DAILY, took_office_only=True)
        bills, memberships, speeches = [], [], []
        for code in sorted({s.code for s in took}):
            bills += miss.call(f"bills {code}", lambda c=code: act.bills(c, Freshness.DAILY), [])
            memberships += miss.call(
                f"memberships {code}", lambda c=code: act.memberships(c, Freshness.DAILY), []
            )
            speeches += miss.call(
                f"speeches {code}", lambda c=code: act.speeches(c, leg.start, end, pick), []
            )
        bundle, notes = normalize.senado(votings, ballots, codes, bills, memberships, speeches)
        return "senado activity", replace_activity(bundle), notes, miss
