"""
User interface module for expense tracking application.
Contains all GUI components and dialogs.
"""

from .main_window import MainWindow
from .widgets import (
    MonthWidget,
    DashboardWidget,
    HistoryWidget,
    ChartsWidget
)
from .dialogs import (
    SettingsDialog,
    ExportDialog,
    AboutDialog,
    ExpenseDialog
)
from .components import (
    CustomSpinBox,
    CurrencyInput,
    DatePicker,
    IconButton,
    StatusIndicator
)

__all__ = [
    # Main window
    'MainWindow',
    
    # Widgets
    'MonthWidget',
    'DashboardWidget', 
    'HistoryWidget',
    'ChartsWidget',
    
    # Dialogs
    'SettingsDialog',
    'ExportDialog',
    'AboutDialog',
    'ExpenseDialog',
    
    # Components
    'CustomSpinBox',
    'CurrencyInput',
    'DatePicker',
    'IconButton',
    'StatusIndicator'
]
"""Custom UI components used across the application."""

from .custom_widgets import (
    CustomSpinBox,
    CurrencyInput,
    DatePicker,
    IconButton,
    StatusIndicator,
)

__all__ = [
    "CustomSpinBox",
    "CurrencyInput",
    "DatePicker",
    "IconButton",
    "StatusIndicator",
]
