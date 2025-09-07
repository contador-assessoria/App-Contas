"""Common constants shared across the UI layer.

These values centralise strings and numbers that are used in more than one
place of the interface.  Keeping them here avoids magic values scattered across
the code base and makes it easier to tweak behaviour such as default formats or
file dialog filters.
"""

from __future__ import annotations

# General application information -------------------------------------------------

APP_NAME = "App-Contas"
"""Human readable name used in window titles and dialogs."""

APP_VERSION = "0.1.0"
"""Semver compatible application version."""


# Formatting ----------------------------------------------------------------------

DATE_FORMAT = "%d/%m/%Y"
"""Default date format using day/month/year (Brazilian style)."""

DATETIME_FORMAT = "%d/%m/%Y %H:%M"
"""Default date and time format."""

CURRENCY_SYMBOL = "R$"
"""Currency symbol used throughout the UI."""


# File dialog filters -------------------------------------------------------------

JSON_FILTER = "JSON files (*.json)"
CSV_FILTER = "CSV files (*.csv)"
EXCEL_FILTER = "Excel files (*.xlsx *.xls)"
PDF_FILTER = "PDF files (*.pdf)"


__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "DATE_FORMAT",
    "DATETIME_FORMAT",
    "CURRENCY_SYMBOL",
    "JSON_FILTER",
    "CSV_FILTER",
    "EXCEL_FILTER",
    "PDF_FILTER",
]
