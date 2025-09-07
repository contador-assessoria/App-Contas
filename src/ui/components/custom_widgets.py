from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QDoubleValidator, QIcon
from PySide6.QtWidgets import (
    QDateEdit,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QLabel,
)


class CustomSpinBox(QDoubleSpinBox):
    """Spin box with decimal support and right aligned text.

    Parameters
    ----------
    minimum: float
        Minimum allowed value. Defaults to 0.0.
    maximum: float
        Maximum allowed value. Defaults to 1e9.
    decimals: int
        Number of decimal places to show. Defaults to 2.
    step: float
        Increment step. Defaults to 1.0.
    """

    def __init__(
        self,
        parent=None,
        *,
        minimum: float = 0.0,
        maximum: float = 1e9,
        decimals: int = 2,
        step: float = 1.0,
    ) -> None:
        super().__init__(parent)
        self.setRange(minimum, maximum)
        self.setDecimals(decimals)
        self.setSingleStep(step)
        self.setAlignment(Qt.AlignRight)

    def value_decimal(self) -> Decimal:
        """Return the current value as :class:`Decimal`."""

        return Decimal(str(self.value()))


class CurrencyInput(QLineEdit):
    """Line edit that accepts currency values using :class:`Decimal`."""

    def __init__(self, parent=None, *, decimals: int = 2) -> None:
        super().__init__(parent)
        self._decimals = decimals
        validator = QDoubleValidator(0.0, 1e12, decimals, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.setValidator(validator)
        self.setAlignment(Qt.AlignRight)

    def value(self) -> Decimal:
        text = self.text().replace(",", ".")
        return Decimal(text) if text else Decimal("0")

    def set_value(self, amount: Decimal) -> None:
        self.setText(f"{amount:.{self._decimals}f}")

    def focusOutEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        # Format value on focus out
        self.set_value(self.value())
        super().focusOutEvent(event)


class DatePicker(QDateEdit):
    """Simple :class:`QDateEdit` with calendar popup enabled."""

    def __init__(self, parent=None, *, format: str = "yyyy-MM-dd") -> None:
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat(format)
        self.setDate(QDate.currentDate())


class IconButton(QPushButton):
    """Push button that shows only an icon."""

    def __init__(self, icon: QIcon | str, tooltip: str = "", parent=None) -> None:
        super().__init__(parent)
        if isinstance(icon, str):
            icon = QIcon(icon)
        self.setIcon(icon)
        self.setToolTip(tooltip)
        self.setFlat(True)


class StatusIndicator(QLabel):
    """Colored circle used to indicate success/error states."""

    def __init__(self, parent=None, *, size: int = 10) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.set_status(False)

    def set_status(self, ok: bool) -> None:
        color = "#2ecc71" if ok else "#e74c3c"
        radius = self._size // 2
        self.setStyleSheet(
            f"background-color: {color}; border-radius: {radius}px;"
        )
  
