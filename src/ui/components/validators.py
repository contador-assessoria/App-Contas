from __future__ import annotations

"""Reusable validators for Qt input widgets."""

from decimal import Decimal, InvalidOperation
from PySide6.QtGui import QValidator


class DecimalValidator(QValidator):
    """Validator for decimal numbers using :class:`~decimal.Decimal`.

    Parameters
    ----------
    bottom: float | Decimal, optional
        Minimum allowed value, default ``0``.
    top: float | Decimal, optional
        Maximum allowed value, default ``1e9``.
    decimals: int, optional
        Maximum number of decimal places allowed, default ``2``.
    """

    def __init__(
        self,
        bottom: float | Decimal = 0,
        top: float | Decimal = 1e9,
        *,
        decimals: int = 2,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._bottom = Decimal(str(bottom))
        self._top = Decimal(str(top))
        self._decimals = decimals

    # QValidator.validate signature -> tuple[state, string, position]
    def validate(self, input_str: str, pos: int):  # noqa: D401 - Qt API
        """See :class:`QValidator`."""
        if input_str in {"", "+", "-", ".", ","}:
            return QValidator.Intermediate, input_str, pos

        try:
            value = Decimal(input_str.replace(",", "."))
        except InvalidOperation:
            return QValidator.Invalid, input_str, pos

        if not self._bottom <= value <= self._top:
            return QValidator.Invalid, input_str, pos

        if "." in str(value):
            decimal_part = str(value).split(".")[1]
            if len(decimal_part) > self._decimals:
                return QValidator.Invalid, input_str, pos

        return QValidator.Acceptable, input_str, pos

    def fixup(self, input_str: str) -> str:  # noqa: D401 - Qt API
        """Attempt to coerce value into a valid decimal representation."""
        if not input_str:
            return ""

        try:
            value = Decimal(input_str.replace(",", "."))
        except InvalidOperation:
            return ""

        if value < self._bottom:
            value = self._bottom
        elif value > self._top:
            value = self._top

        return f"{value:.{self._decimals}f}"


class PercentageValidator(DecimalValidator):
    """Validator constrained between 0 and 100 percent."""

    def __init__(self, *, decimals: int = 2, parent=None) -> None:
        super().__init__(0, 100, decimals=decimals, parent=parent)


__all__ = ["DecimalValidator", "PercentageValidator"]
