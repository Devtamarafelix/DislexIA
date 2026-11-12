"""Camada escura da régua reversa.

Cobre a tela inteira com um véu escuro e deixa um "buraco" transparente na
posição da régua. É uma janela sem moldura, sempre no topo e que ignora o
mouse, então não atrapalha cliques nem digitação no que estiver por baixo.
"""
from PySide6.QtCore import Qt, QRect, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget


class DimOverlay(QWidget):
    def __init__(self):
        super().__init__(None)
        self._dim = 0.7
        self._hole = QRect()
        self._radius = 10
        self.setWindowTitle("Régua reversa")
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_dim(self, percent):
        self._dim = max(5, min(95, int(percent))) / 100
        self.update()

    def follow(self, screen_geometry, ruler_geometry, radius):
        """Acompanha a tela e a posição da régua (coordenadas globais)."""
        # 1 px a menos na altura: uma janela translúcida com o tamanho exato da tela
        # pode ser tratada como "tela cheia" no Windows e perder a transparência.
        target = screen_geometry.adjusted(0, 0, 0, -1)
        if self.geometry() != target:
            self.setGeometry(target)
        self._hole = ruler_geometry.translated(-screen_geometry.topLeft())
        self._radius = radius
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        veil = QPainterPath()
        veil.addRect(QRectF(self.rect()))
        hole = QPainterPath()
        hole.addRoundedRect(QRectF(self._hole), self._radius, self._radius)
        painter.fillPath(veil.subtracted(hole), QColor(0, 0, 0, round(self._dim * 255)))
