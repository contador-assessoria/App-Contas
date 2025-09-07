"""Miscellaneous helper functions for the UI layer."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QDir, QStandardPaths
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox, QWidget

from .constants import APP_NAME


def resource_path(relative: str) -> str:
    """Return the absolute path to a resource bundled with the application."""

    base = Path(__file__).resolve().parent.parent  # src/ui
    return str(base / "resources" / relative)


def load_icon(name: str) -> QIcon:
    """Load an icon from the ``resources`` directory."""

    return QIcon(resource_path(name))


def show_error(message: str, details: str | None = None, parent: QWidget | None = None) -> None:
    """Display a standard error message box."""

    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle(APP_NAME)
    box.setText(message)
    if details:
        box.setInformativeText(details)
    box.exec()


def ensure_app_dir() -> str:
    """Ensure that the application data directory exists and return its path."""

    path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    QDir().mkpath(path)
    return path


__all__ = ["resource_path", "load_icon", "show_error", "ensure_app_dir"]
