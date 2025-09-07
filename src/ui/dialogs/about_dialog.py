"""Simple About dialog for the application."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QDialogButtonBox,
)


class AboutDialog(QDialog):
    """Display basic information about the application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre o App-Contas")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        info = QLabel(
            """<h3>App-Contas</h3>
            <p>Aplicativo para controle e divisão de despesas domésticas.</p>
            <p>Versão 2.0</p>
            <p>Projeto open source sob licença MIT.</p>"""
        )
        info.setTextFormat(Qt.RichText)
        info.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        info.setWordWrap(True)
        layout.addWidget(info)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
