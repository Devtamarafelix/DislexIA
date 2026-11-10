"""Botão de engrenagem flutuante: sempre opaco e sempre clicável.

É uma janela separada da régua (e não um filho dela) para continuar
clicável mesmo quando a régua está translúcida ou com "clique-transparente".
"""
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

class GearButton(QWidget):
    clicked = Signal()

    def __init__(self):
        super().__init__(None)
        self._hover = False
        self._pressed = False
        self.setWindowTitle("Configurações da régua")
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Abrir configurações")
        self.setFixedSize(34, 34)

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        s = min(w, h)
        if self._pressed:
            bg = QColor("#1F3566")
        elif self._hover:
            bg = QColor("#263D70")
        else:
            bg = QColor("#334E8C")

        # Fundo circular totalmente opaco.
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.setBrush(bg)
        painter.drawEllipse(QRectF(1, 1, w - 2, h - 2))

        # Engrenagem: corpo + 8 dentes + furo central.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FFFFFF"))
        painter.translate(QPointF(w / 2, h / 2))
        body, outer, tooth = s * 0.26, s * 0.37, s * 0.15
        painter.drawEllipse(QPointF(0, 0), body, body)
        for i in range(8):
            painter.save()
            painter.rotate(i * 45)
            painter.drawRoundedRect(
                QRectF(-tooth / 2, -outer, tooth, outer - body * 0.5),
                tooth * 0.25, tooth * 0.25,
            )
            painter.restore()
        painter.setBrush(bg)
        painter.drawEllipse(QPointF(0, 0), s * 0.11, s * 0.11)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._pressed:
            self._pressed = False
            self.update()
            if self.rect().contains(event.position().toPoint()):
                self.clicked.emit()
            event.accept()
        else:
            event.ignore()
