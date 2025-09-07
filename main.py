"""
Ponto de entrada principal para a aplicação _expense-splitter.

Este script inicializa a aplicação Qt, cria a janela principal
e inicia o loop de eventos. Adiciona tratamento de exceções para
maior robustez.
"""

import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.app import MainWindow

def main():
    """
    Função principal para iniciar a aplicação.
    """
    app = QApplication(sys.argv)
    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        # Captura exceções inesperadas durante a inicialização ou execução
        error_message = f"Ocorreu um erro inesperado:\n\n{str(e)}\n\n{traceback.format_exc()}"
        QMessageBox.critical(None, "Erro Crítico", error_message)
        sys.exit(1)

if __name__ == "__main__":
    main()

