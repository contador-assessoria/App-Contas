"""Helper functions for formatting values for display in the UI."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Union

from PySide6.QtCore import QDate

from .constants import CURRENCY_SYMBOL, DATE_FORMAT, DATETIME_FORMAT

Number = Union[int, float, Decimal]


def _to_decimal(value: Number, places: int = 2) -> Decimal:
    """Convert ``value`` to :class:`~decimal.Decimal` with ``places`` precision."""

    quant = Decimal(f"1.{'0'*places}")
    return Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP)


def format_currency(value: Number, symbol: str = CURRENCY_SYMBOL, places: int = 2) -> str:
    """Return ``value`` formatted as a currency string.

    The number is rounded using bankers' rounding and formatted using the
    Brazilian locale (comma as decimal separator).
    """

    dec = _to_decimal(value, places)
    formatted = f"{dec:,.{places}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{symbol} {formatted}"


def format_percentage(value: Number, places: int = 2) -> str:
    """Return ``value`` as a percentage string with the given precision."""

    dec = _to_decimal(value, places)
    formatted = f"{dec:.{places}f}".replace(".", ",")
    return f"{formatted}%"


def format_date(value: Union[date, datetime, QDate], fmt: str | None = None) -> str:
    """Format ``value`` using either ``fmt`` or :data:`DATE_FORMAT`.

    ``value`` can be a :class:`datetime.date`, :class:`datetime.datetime` or a
    Qt :class:`~PySide6.QtCore.QDate` instance.
    """

    fmt = fmt or (DATETIME_FORMAT if isinstance(value, datetime) else DATE_FORMAT)

    if isinstance(value, QDate):
        return value.toString(fmt)

    if isinstance(value, datetime):
        return value.strftime(fmt)

    if isinstance(value, date):
        return value.strftime(fmt)

    raise TypeError(f"Unsupported type for formatting: {type(value)!r}")


__all__ = ["format_currency", "format_percentage", "format_date"]
