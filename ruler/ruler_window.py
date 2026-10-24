"""Janela de régua flutuante, sem moldura e sempre no topo."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget

from ruler.ruler_buttons import RulerButton


class RulerWindow(QWidget):
    # Emitido quando a posição "definitiva" muda (soltar o mouse, largura total).
    position_committed = Signal()

    def __init__(self, color="#FFE66D", opacity=48, height=58, width=1000,
                 x=180, y=300, click_through=False, full_width=False):
        super().__init__(None)
        self._color = QColor(color)
        self._opacity = max(5, min(100, int(opacity))) / 100
        self._border_color = QColor("#5B4B00")
        self._border_width = 2
        self._radius = 10
        self._drag_offset = None
        self._click_through = False
        self._full_width = False
        self._normal_width = int(width)   # largura "normal" (do controle deslizante)
        self._restore_x = int(x)          # x normal, usado ao sair da largura total
        self.close_allowed = False        # a janela principal liga isto ao encerrar

        # Botões (da esquerda para a direita): play, repetir, engrenagem.
        # Cada um é uma janela própria, sempre opaca e sempre clicável.
        self.play_button = RulerButton("play", "Ler em voz alta o texto sob a régua")
        self.repeat_button = RulerButton("repeat", "Repetir a última leitura")
        self.gear = RulerButton("gear", "Abrir configurações")
        self.buttons = [self.play_button, self.repeat_button, self.gear]

        self.setWindowTitle("Régua de leitura")
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(int(width), int(height))
        self.move(int(x), int(y))
        self.set_click_through(click_through)
        self.set_full_width(full_width)
        self._sync_buttons()

    # ------------------------------------------------------------------ cor / opacidade
    def set_color(self, color):
        self._color = QColor(color)
        self.update()

    def set_opacity(self, value):
        self._opacity = max(5, min(100, int(value))) / 100
        self.update()

    # ------------------------------------------------------------------ tamanho / largura total
    def set_ruler_size(self, width=None, height=None):
        if width is not None:
            self._normal_width = int(width)
        w = self.width() if self._full_width else self._normal_width
        h = height if height is not None else self.height()
        self.resize(w, h)
        self._sync_buttons()

    def is_full_width(self):
        return self._full_width

    def normal_x(self):
        """Posição x 'normal' da régua (a que vale quando não está em largura total)."""
        return self._restore_x if self._full_width else self.x()

    def set_full_width(self, enabled):
        enabled = bool(enabled)
        if enabled == self._full_width:
            return
        if enabled:
            self._restore_x = self.x()
            self._full_width = True
            self._apply_full_geometry(self._target_screen(), self.y())
        else:
            self._full_width = False
            geo = self._target_screen().geometry()
            x = self._restore_x
            if x < geo.left() or x + self._normal_width > geo.right() + 1:
                x = geo.x() + max(0, (geo.width() - self._normal_width) // 2)
            self.setGeometry(x, self.y(), self._normal_width, self.height())
        self.update()
        self._sync_buttons()
        self.position_committed.emit()

    def move_ruler(self, x, y, screen=None):
        """Move a régua; em largura total só vale o y (o x acompanha a tela)."""
        if self._full_width:
            self._apply_full_geometry(screen or self._target_screen(), y)
        else:
            self.move(x, y)

    def _target_screen(self):
        return (QGuiApplication.screenAt(self.geometry().center())
                or self.screen()
                or QGuiApplication.primaryScreen())

    def _apply_full_geometry(self, screen, y):
        geo = screen.geometry()
        self.setGeometry(geo.x(), y, geo.width(), self.height())

    # ------------------------------------------------------------------ botões
    def _sync_buttons(self):
        geo = self.geometry()
        side = max(18, min(36, geo.height() - 10))
        margin = max(4, (geo.height() - side) // 2)
        gap = 6
        y = geo.y() + (geo.height() - side) // 2
        x = geo.x() + geo.width() - margin
        for button in reversed(self.buttons):
            x -= side
            button.setFixedSize(side, side)
            button.move(x, y)
            x -= gap

    def show_buttons(self):
        """Mostra os botões (mesmo com a régua desativada) e os põe na frente."""
        self._sync_buttons()
        for button in self.buttons:
            button.show()
        for button in self.buttons:
            button.raise_()

    def begin_capture(self):
        """Esconde régua e botões para fotografar a tela sob a régua."""
        self._capture_was_visible = self.isVisible()
        if self._capture_was_visible:
            self.hide()
        for button in self.buttons:
            button.hide()

    def end_capture(self):
        if getattr(self, "_capture_was_visible", False):
            self.show()          # o showEvent traz os botões de volta
        else:
            self.show_buttons()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._sync_buttons()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_buttons()

    def showEvent(self, event):
        super().showEvent(event)
        self.show_buttons()

    # ------------------------------------------------------------------ clique-transparente
    def set_click_through(self, enabled):
        """Quando ligado, a régua ignora o mouse; desligue para movê-la."""
        enabled = bool(enabled)
        if self._click_through == enabled:
            return
        self._click_through = enabled
        visible = self.isVisible()
        if visible:
            self.hide()
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowTransparentForInput
        else:
            flags &= ~Qt.WindowType.WindowTransparentForInput
        self.setWindowFlags(flags)
        if visible:
            self.show()
        self.update()

    # ------------------------------------------------------------------ desenho / mouse
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fill = QColor(self._color)
        fill.setAlphaF(self._opacity)
        pen_color = QColor(self._border_color)
        pen_color.setAlphaF(min(1.0, self._opacity + 0.35))
        painter.setPen(QPen(pen_color, self._border_width))
        painter.setBrush(QBrush(fill))
        rect = self.rect().adjusted(1, 1, -1, -1)
        radius = 0 if self._full_width else self._radius
        painter.drawRoundedRect(rect, radius, radius)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._click_through:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            for button in self.buttons:
                button.raise_()
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and not self._click_through:
            pos = event.globalPosition().toPoint()
            target = pos - self._drag_offset
            screen = QGuiApplication.screenAt(pos) if self._full_width else None
            self.move_ruler(target.x(), target.y(), screen)
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if self._drag_offset is not None:
            self._drag_offset = None
            self.position_committed.emit()
        event.accept()

    def closeEvent(self, event):
        if self.close_allowed or QGuiApplication.isSavingSession():
            for button in self.buttons:
                button.close()
            event.accept()
            return
        # A régua é controlada pela janela principal; fechar aqui só a oculta.
        self.hide()
        event.ignore()
