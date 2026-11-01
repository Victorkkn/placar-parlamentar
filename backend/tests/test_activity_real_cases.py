"""Each metric on a REAL case from recorded fixtures (Phase B2 acceptance, item 3).

Runs the real clients, normalizers, storage and metrics offline on official responses
recorded from the 2026-11-01 snapshot (`tests/fixtures/*/activity/`, decision 0011).

- Deputy 220593 (in office 2023-02-01 to 2025-01-01): a session and a vote where he is
  recorded, a session and a vote where he is not, and a session after he left office.
- Senator 5917 (alternate in office for the whole window): an open vote, an absence with an
  official reason, and a secret vote.

Bill and speech totals equal those of the full 2026-11-01 load, because every page of those
lists was recorded.
"""

from datetime import date
from pathlib import Path

import pytest

from placar.activity.services import replace_activity
from placar.core.types import DateWindow
from placar.legislators.selectors import get_official
from placar.metrics.selectors import activity_metrics
from placar.sources.activity_runner import freshness_for
from placar.sources.cache import Freshness, RawCache
from placar.sources.clients import camara_activity as cam
from placar.sources.clients import senado_activity as sen
from placar.sources.fixtures import cache_from_fixtures
from placar.sources.management.commands.normalize_current import offline_fetcher
from placar.sources.normalize import activity as normalize

from .test_legislators_db import load_both

pytestmark = pytest.mark.django_db
FIXTURES = Path(__file__).resolve().parent / "fixtures"
TODAY = date(2026, 11, 1)
WINDOW = DateWindow(date(2023, 2, 1), TODAY)
C = "https://dadosabertos.camara.leg.br/api/v2"
S = "https://legis.senado.leg.br/dadosabertos"
EVENTS = {"codTipoEvento": "110", "idOrgao": "180", "itens": "100", "ordem": "ASC",
          "ordenarPor": "dataHoraInicio"}  # fmt: skip


@pytest.fixture
def offline(settings, tmp_path):
    settings.PLACAR = {**settings.PLACAR, "RAW_CACHE_DIR": tmp_path}
    cache_from_fixtures(FIXTURES, RawCache(tmp_path))
    load_both()


def camara_bundle():
    fetcher = offline_fetcher("camara")
    act = cam.CamaraActivityClient(fetcher)
    sessions = []
    for params in (
        {**EVENTS, "dataInicio": "2023-02-01", "dataFim": "2023-12-31", "pagina": "2"},
        {**EVENTS, "dataInicio": "2024-01-01", "dataFim": "2024-12-31"},
        {**EVENTS, "dataInicio": "2025-01-01", "dataFim": "2025-12-31"},
    ):
        page = fetcher.get(f"{C}/eventos", params, freshness=Freshness.DAILY)
        sessions += cam.parse_sessions(page.body, page.source, act.notes)
    presences = [p for s in sessions for p in act.presence(s.event_id, Freshness.DAILY)]
    page = fetcher.get(
        f"{C}/votacoes",
        {
            "dataInicio": "2024-01-01",
            "dataFim": "2024-03-31",
            "idOrgao": "180",
            "itens": "100",
            "ordem": "ASC",
            "ordenarPor": "dataHoraRegistro",
            "pagina": "2",
        },  # fmt: skip
        freshness=Freshness.DAILY,
    )
    votings = cam.parse_votings(page.body, page.source, act.notes)
    ballots = [b for v in votings for b in act.ballots(v.voting_id, Freshness.DAILY)]
    bills = act.bills(220593, [2023, 2024, 2025, 2026], Freshness.DAILY)
    speeches = act.speeches(220593, 57, Freshness.DAILY)
    return normalize.camara(sessions, presences, votings, ballots, bills, [], speeches)


def senado_bundle():
    fetcher = offline_fetcher("senado")
    act = sen.SenadoActivityClient(fetcher)
    codes, _ = act.vote_codes()
    votings, ballots = [], []
    for start, end in (("2023-02-01", "2023-12-31"), ("2024-01-01", "2024-12-31")):
        page = fetcher.get(f"{S}/votacao", {"dataInicio": start, "dataFim": end},
                           freshness=Freshness.DAILY)  # fmt: skip
        v, b = sen.parse_votings(page.body, page.source, act.notes)
        votings += v
        ballots += b
    bills = act.bills(5917, Freshness.DAILY)
    speeches = act.speeches(5917, WINDOW.start, WINDOW.end, freshness_for(TODAY))
    return normalize.senado(votings, ballots, codes, bills, [], speeches)


def test_camara_metrics_on_real_records(offline):
    bundle, notes = camara_bundle()
    assert notes.unknown_options == {}
    replace_activity(bundle)
    result = activity_metrics(get_official("CAMARA", 220593).pk, WINDOW, TODAY)

    attendance = result["plenary_attendance"]
    # 71463 (2023-12-04, not recorded) and 71957 (2024-03-05, recorded) are in office;
    # 75466 (2025-03-11) is after he left office on 2025-01-01 and is not counted.
    assert (attendance.numerator, attendance.denominator) == (1, 2)
    assert attendance.sources  # session lists and the presence record

    votes = result["vote_participation"]
    # 2417025-55: "Sim"; 2420014-8: no vote recorded for him.
    assert (votes.numerator, votes.denominator) == (1, 2)
    assert votes.details["by_category"] == {"TAKES_PART": 1, "NO_RECORD": 1}

    # Same totals as the full load of 2026-11-01 (every page recorded).
    assert result["bills_authored"].numerator == 49
    assert result["speeches"].numerator == 202
    assert all(r.sources for r in result.values() if r and r.numerator)


def test_senado_metrics_on_real_records(offline):
    bundle, notes = senado_bundle()
    assert notes.unknown_options == {}
    replace_activity(bundle)
    result = activity_metrics(get_official("SENADO", 5917).pk, WINDOW, TODAY)

    assert result["plenary_attendance"] is None  # not published by the Senado (decision 0014)
    votes = result["vote_participation"]
    # 6675: "Sim"; 6744: "AP" (absence with an official reason); 6894: secret, not counted.
    assert (votes.numerator, votes.denominator) == (1, 2)
    assert votes.details["by_category"] == {"TAKES_PART": 1, "JUSTIFIED": 1}

    assert result["bills_authored"].numerator == 37
    assert result["speeches"].numerator == 48
