"""The one pt-BR formatter shared by facts, templates and the validator (decision 0010, item 7).

Numbers and dates are compared as these exact strings, so every part of the summary feature
must format through here.
"""

from datetime import date
from fractions import Fraction


def integer(n: int) -> str:
    """1370 -> "1.370"."""
    return f"{n:,}".replace(",", ".")


def decimal(x: float | Fraction, places: int = 1) -> str:
    """3.25 -> "3,3" (one decimal place by default)."""
    text = f"{float(x):,.{places}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def percent(x: float | Fraction) -> str:
    """0.823 -> "82,3%"."""
    return decimal(float(x) * 100) + "%"


def day(d: date) -> str:
    """date(2023, 2, 1) -> "01/02/2023"."""
    return d.strftime("%d/%m/%Y")
