"""Dialog allowing the user to tweak basic application settings."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QDialogButtonBox,
)

from ...core import ConfigManager


class SettingsDialog(QDialog):
    """Expose a minimal subset of application settings to the user."""

    def __init__(self, config_manager: ConfigManager, parent=None) -> None:
        super().__init__(parent)
        self.config_manager = config_manager

        self.setWindowTitle("Configurações")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Tema:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light", "auto"])
        self.theme_combo.setCurrentText(self.config_manager.get("theme", "dark"))
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)

        # Language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Idioma:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["pt_BR", "en_US", "es_ES"])
        self.lang_combo.setCurrentText(self.config_manager.get("language", "pt_BR"))
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # Auto-save option
        self.auto_save_cb = QCheckBox("Salvar automaticamente")
        self.auto_save_cb.setChecked(self.config_manager.get("auto_save", True))
        layout.addWidget(self.auto_save_cb)

        # Auto-save interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Intervalo de auto-salvamento (s):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 3600)
        self.interval_spin.setValue(self.config_manager.get("auto_save_interval", 60))
        interval_layout.addWidget(self.interval_spin)
        layout.addLayout(interval_layout)

        # Default percentage for house 2
        perc_layout = QHBoxLayout()
        perc_layout.addWidget(QLabel("% Casa 2:"))
        self.perc_spin = QSpinBox()
        self.perc_spin.setRange(0, 100)
        self.perc_spin.setValue(int(self.config_manager.get("default_casa2_percentage", 67)))
        perc_layout.addWidget(self.perc_spin)
        layout.addLayout(perc_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    def _save(self) -> None:
        """Persist changes through `ConfigManager`."""
        self.config_manager.set("theme", self.theme_combo.currentText())
        self.config_manager.set("language", self.lang_combo.currentText())
        self.config_manager.set("auto_save", self.auto_save_cb.isChecked())
        self.config_manager.set("auto_save_interval", self.interval_spin.value())
        self.config_manager.set(
            "default_casa2_percentage", float(self.perc_spin.value())
        )

        self.config_manager.save()
        self.accept()
