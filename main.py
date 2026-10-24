"""Ponto de entrada do protótipo de acessibilidade."""
import sys
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow
from app.theme import setup_fonts, make_app_icon

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Leitura Acessível")
    app.setOrganizationName("ProjetoAcessibilidade")
    # O programa roda em segundo plano (régua + engrenagem + ícone da bandeja).
    # O botão "Encerrar programa" sai de vez.
    app.setQuitOnLastWindowClosed(False)
    setup_fonts(app)
    app.setWindowIcon(make_app_icon())
    window = MainWindow()
    if "--janela" in sys.argv:
        window.show_settings()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
