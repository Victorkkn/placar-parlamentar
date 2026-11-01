from datetime import date

import pytest

from placar.core.types import CoreValueError, DateWindow, Period, SourceRef

KEY = "a" * 64


def test_source_ref_requires_https_and_sha256_key():
    ref = SourceRef(api_url="https://dadosabertos.camara.leg.br/api/v2/legislaturas", cache_key=KEY)
    assert ref.public_url is None
    with pytest.raises(CoreValueError):
        SourceRef(api_url="http://dadosabertos.camara.leg.br/x", cache_key=KEY)
    with pytest.raises(CoreValueError):
        SourceRef(api_url="https://dadosabertos.camara.leg.br/x", cache_key="short")
    with pytest.raises(CoreValueError):
        SourceRef(api_url="https://a.camara.leg.br/x", cache_key=KEY, public_url="http://b")


def test_date_window_counts_both_ends():
    window = DateWindow(date(2023, 2, 1), date(2023, 2, 1))
    assert window.days == 1
    assert DateWindow(date(2023, 2, 1), date(2027, 1, 31)).days == 1461
    assert window.contains(date(2023, 2, 1))
    assert not window.contains(date(2023, 2, 2))


def test_date_window_rejects_reversed_dates():
    with pytest.raises(CoreValueError):
        DateWindow(date(2024, 1, 2), date(2024, 1, 1))


def test_period_open_and_closed():
    assert Period(date(2023, 9, 4)).is_open
    assert not Period(date(2023, 9, 4), date(2023, 9, 4)).is_open
    with pytest.raises(CoreValueError):
        Period(date(2023, 9, 5), date(2023, 9, 4))
