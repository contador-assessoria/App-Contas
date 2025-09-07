"""Dialog for exporting application data to various formats."""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFileDialog,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
)

from ...core import DataManager, ExportManager


class ExportDialog(QDialog):
    """Allow the user to export stored data to a file."""

    def __init__(
        self,
        data_manager: DataManager,
        export_manager: ExportManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.data_manager = data_manager
        self.export_manager = export_manager

        self.setWindowTitle("Exportar Dados")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        # Format selection
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("Formato:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(self.export_manager.supported_formats)
        fmt_layout.addWidget(self.format_combo)
        layout.addLayout(fmt_layout)

        # Output file path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        browse_btn = QPushButton("Procurar...")
        browse_btn.clicked.connect(self._browse)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # Option: include charts
        self.charts_cb = QCheckBox("Incluir gráficos (se suportado)")
        self.charts_cb.setChecked(True)
        layout.addWidget(self.charts_cb)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.accepted.connect(self._export)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    def _browse(self) -> None:
        """Open file dialog to choose output path."""
        fmt = self.format_combo.currentText()
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Arquivo",
            "",
            f"*.* (*.{fmt})",
        )
        if selected:
            if not selected.lower().endswith(f".{fmt}"):
                selected = f"{selected}.{fmt}"
            self.path_edit.setText(selected)

    # ------------------------------------------------------------------
    def _export(self) -> None:
        """Execute export using `ExportManager`."""
        file_path = self.path_edit.text().strip()
        fmt = self.format_combo.currentText()

        if not file_path:
            QMessageBox.warning(self, "Exportar", "Informe o arquivo de destino.")
            return

        data = self.data_manager._prepare_data_for_serialization()
        options = {"include_charts": self.charts_cb.isChecked()}
        success, message = self.export_manager.export_data(
            data, Path(file_path), fmt, options
        )

        if success:
            QMessageBox.information(self, "Exportar", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Exportar", message)
