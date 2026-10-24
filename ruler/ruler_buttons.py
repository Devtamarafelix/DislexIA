"""Botões flutuantes da régua (engrenagem, play/stop, repetir).

Cada botão é uma janela própria, sempre opaca e sempre clicável, mesmo com a
régua translúcida ou com "clique-transparente" ligado.
"""
import math

from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

COLORS = {
    "gear": "#334E8C",
    "repeat": "#334E8C",
    "play": "#23835D",
    "stop": "#B3402F",
}


class RulerButton(QWidget):
    clicked = Signal()

    def __init__(self, kind, tooltip):
        super().__init__(None)
        self._kind = kind
        self._hover = False
        self._pressed = False
        self.setWindowTitle("Régua de leitura")
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setFixedSize(34, 34)

    def set_kind(self, kind, tooltip=None):
        self._kind = kind
        if tooltip is not None:
            self.setToolTip(tooltip)
        self.update()

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
        bg = QColor(COLORS[self._kind])
        if self._pressed:
            bg = bg.darker(145)
        elif self._hover:
            bg = bg.darker(120)

        # Fundo circular totalmente opaco.
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.setBrush(bg)
        painter.drawEllipse(QRectF(1, 1, w - 2, h - 2))

        painter.translate(QPointF(w / 2, h / 2))
        white = QColor("#FFFFFF")
        if self._kind == "gear":
            self._draw_gear(painter, s, white, bg)
        elif self._kind == "play":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(white)
            painter.drawPolygon(QPolygonF([
                QPointF(-0.14 * s, -0.23 * s),
                QPointF(-0.14 * s, 0.23 * s),
                QPointF(0.25 * s, 0.0),
            ]))
        elif self._kind == "stop":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(white)
            side = s * 0.30
            painter.drawRoundedRect(QRectF(-side, -side, 2 * side, 2 * side), s * 0.05, s * 0.05)
        elif self._kind == "repeat":
            self._draw_repeat(painter, s, white)

    @staticmethod
    def _draw_gear(painter, s, white, bg):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(white)
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

    @staticmethod
    def _draw_repeat(painter, s, white):
        r = s * 0.25
        pen = QPen(white, s * 0.09)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # Arco de 280° (anti-horário na tela), com uma abertura à direita.
        start, span = 60, 280
        painter.drawArc(QRectF(-r, -r, 2 * r, 2 * r), start * 16, span * 16)
        # Ponta de seta no fim do arco, apontando no sentido do movimento.
        theta = math.radians(start + span)
        px, py = r * math.cos(theta), -r * math.sin(theta)
        tx, ty = -math.sin(theta), -math.cos(theta)      # tangente
        nx, ny = math.cos(theta), -math.sin(theta)       # radial
        head, half = s * 0.13, s * 0.10
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(white)
        painter.drawPolygon(QPolygonF([
            QPointF(px + tx * head, py + ty * head),
            QPointF(px + nx * half, py + ny * half),
            QPointF(px - nx * half, py - ny * half),
        ]))

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
