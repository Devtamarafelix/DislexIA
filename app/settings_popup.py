"""Caixa de configurações que abre logo abaixo da engrenagem."""
import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame

from app.controls_panel import RulerControls
from app.theme import build_stylesheet


class SettingsPopup(QWidget):
    toggle_requested = Signal()
    open_system_requested = Signal()

    def __init__(self):
        super().__init__(None)
        self.last_hidden = 0.0
        self.setObjectName("popupRoot")
        # Popup: fecha sozinho ao clicar fora, como um menu.
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoMouseReplay, True)
        self.setStyleSheet(build_stylesheet())
        self.setFixedWidth(410)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        panel = QFrame()
        panel.setObjectName("popupPanel")
        outer.addWidget(panel)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        self.status = QLabel("● Régua ativa")
        self.toggle_button = QPushButton("Desativar régua")
        header.addWidget(self.status)
        header.addStretch()
        header.addWidget(self.toggle_button)
        layout.addLayout(header)

        self.controls = RulerControls()
        layout.addWidget(self.controls)

        self.system_button = QPushButton("Abrir janela do sistema")
        self.system_button.setObjectName("secondary")
        layout.addWidget(self.system_button)

        self.toggle_button.clicked.connect(self.toggle_requested)
        self.system_button.clicked.connect(self._open_system)

    def set_active(self, active):
        self.toggle_button.setText("Desativar régua" if active else "Ativar régua")
        self.status.setText("● Régua ativa" if active else "○ Régua desativada")
        self.status.setStyleSheet(
            "color:#23835D;font-weight:650;" if active else "color:#7A8499;font-weight:650;"
        )

    def _open_system(self):
        self.hide()
        self.open_system_requested.emit()

    def show_below(self, anchor):
        """Abre a caixa logo abaixo do widget (ou acima, se faltar espaço)."""
        self.adjustSize()
        g = anchor.frameGeometry()
        screen = QGuiApplication.screenAt(g.center()) or QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        w, h = self.width(), self.height()
        x = max(avail.left(), min(g.right() - w + 1, avail.right() - w + 1))
        y = g.bottom() + 6
        if y + h > avail.bottom() + 1:
            y = g.top() - h - 6
        y = max(avail.top(), y)
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    def hideEvent(self, event):
        self.last_hidden = time.monotonic()
        super().hideEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)
