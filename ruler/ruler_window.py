"""Janela de régua flutuante, sem moldura e sempre no topo.

- Os botões (play, repetir, engrenagem) ficam FORA da régua, ao lado dela,
  para nunca cobrirem o texto que está sendo lido.
- As bordas e os cantos da régua podem ser arrastados com o mouse para mudar
  a altura e a largura.
- No modo "reverso" a régua fica transparente e o resto da tela escurece.
"""
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget

from app.settings import HEIGHT_RANGE, WIDTH_RANGE
from ruler.dim_overlay import DimOverlay
from ruler.ruler_buttons import RulerButton

EDGE_LEFT, EDGE_RIGHT, EDGE_TOP, EDGE_BOTTOM = 1, 2, 4, 8

BUTTON_SIDE = 34     # tamanho de cada botão (independe da altura da régua)
BUTTON_GAP = 6       # espaço entre os botões
BUTTON_OFFSET = 8    # distância entre a régua e a fileira de botões


class RulerWindow(QWidget):
    # Emitido quando a posição "definitiva" muda (soltar o mouse, largura total).
    position_committed = Signal()
    # Emitido ao terminar de redimensionar com o mouse: (largura normal, altura).
    size_committed = Signal(int, int)
    # Arrasto do usuário: começou (para calar a voz) e terminou de fato movendo a régua.
    drag_started = Signal()
    user_moved = Signal()

    def __init__(self, color="#FFE66D", opacity=48, height=58, width=1000,
                 x=180, y=300, click_through=False, full_width=False,
                 reverse=False, dim=70):
        super().__init__(None)
        self._color = QColor(color)
        self._opacity = max(5, min(100, int(opacity))) / 100
        self._border_color = QColor("#5B4B00")
        self._border_width = 2
        self._radius = 10
        self._drag_offset = None
        self._drag_moved = False
        self._resize_edge = 0
        self._resize_origin = None
        self._resize_geo = None
        self._resize_moved = False
        self._click_through = False
        self._full_width = False
        self._reverse = bool(reverse)
        self._normal_width = int(width)   # largura "normal" (do controle deslizante)
        self._restore_x = int(x)          # x normal, usado ao sair da largura total
        self.close_allowed = False        # a janela principal liga isto ao encerrar

        # Camada escura da régua reversa (só aparece no modo reverso).
        self.overlay = DimOverlay()
        self.overlay.set_dim(dim)

        # Botões (da esquerda para a direita): play, liga/desliga a régua, engrenagem.
        # Cada um é uma janela própria, sempre opaca e sempre clicável.
        self.play_button = RulerButton("play", "Ler em voz alta o texto sob a régua")
        self.power_button = RulerButton("power_on", "Desativar régua")
        self.gear = RulerButton("gear", "Abrir configurações")
        self.buttons = [self.play_button, self.power_button, self.gear]

        self.setWindowTitle("Régua de leitura")
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)       # para trocar o cursor sobre as bordas
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

    # ------------------------------------------------------------------ régua reversa
    def set_reverse(self, enabled):
        self._reverse = bool(enabled)
        self.update()
        self._sync_overlay()

    def set_dim(self, percent):
        self.overlay.set_dim(percent)

    def is_reverse(self):
        return self._reverse

    def _sync_overlay(self):
        """Mostra/esconde o véu escuro e o mantém na tela onde está a régua."""
        if not (self._reverse and self.isVisible()):
            if self.overlay.isVisible():
                self.overlay.hide()
            return
        screen = self._target_screen()
        radius = 0 if self._full_width else self._radius
        self.overlay.follow(screen.geometry(), self.geometry(), radius)
        if not self.overlay.isVisible():
            self.overlay.show()
            # O véu fica por baixo da régua e dos botões.
            self.raise_()
            for button in self.buttons:
                button.raise_()

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
        self._sync_overlay()
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

    # ------------------------------------------------------------------ botões (fora da régua)
    def _sync_buttons(self):
        """Põe a fileira de botões ao lado da régua, sem cobrir a área de leitura.

        Ordem de preferência: à direita, à esquerda, acima e abaixo da régua
        (o que couber na tela). Em largura total não há espaço nas laterais,
        então os botões ficam acima (ou abaixo) da régua, no canto direito.
        """
        geo = self.geometry()
        side, gap, off = BUTTON_SIDE, BUTTON_GAP, BUTTON_OFFSET
        count = len(self.buttons)
        row_w = count * side + (count - 1) * gap
        mid_y = geo.y() + (geo.height() - side) // 2
        right = geo.x() + geo.width()
        candidates = [
            (right + off, mid_y),                            # à direita
            (geo.x() - off - row_w, mid_y),                  # à esquerda
            (right - row_w, geo.y() - off - side),           # acima, alinhado à direita
            (right - row_w, geo.y() + geo.height() + off),   # abaixo, alinhado à direita
        ]
        avail = self._target_screen().availableGeometry()
        chosen = None
        for x, y in candidates:
            if avail.contains(QRect(x, y, row_w, side)):
                chosen = (x, y)
                break
        if chosen is None:      # nenhum cabe inteiro: usa o primeiro, preso à tela
            x, y = candidates[0]
            x = max(avail.left(), min(x, avail.right() - row_w + 1))
            y = max(avail.top(), min(y, avail.bottom() - side + 1))
            chosen = (x, y)
        x, y = chosen
        for button in self.buttons:
            button.setFixedSize(side, side)
            button.move(x, y)
            x += side + gap

    def show_buttons(self):
        """Mostra os botões (mesmo com a régua desativada) e os põe na frente."""
        self._sync_buttons()
        for button in self.buttons:
            button.show()
        for button in self.buttons:
            button.raise_()

    def begin_capture(self):
        """Esconde régua, véu e botões para fotografar a tela sob a régua."""
        self._capture_was_visible = self.isVisible()
        if self._capture_was_visible:
            self.hide()          # o hideEvent também esconde o véu escuro
        for button in self.buttons:
            button.hide()

    def end_capture(self):
        if getattr(self, "_capture_was_visible", False):
            self.show()          # o showEvent traz os botões e o véu de volta
        else:
            self.show_buttons()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._sync_buttons()
        self._sync_overlay()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_buttons()
        self._sync_overlay()

    def showEvent(self, event):
        super().showEvent(event)
        self.show_buttons()
        self._sync_overlay()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.overlay.hide()

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

    # ------------------------------------------------------------------ desenho
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        radius = 0 if self._full_width else self._radius
        if self._reverse:
            # Régua reversa: interior transparente (alpha 1/255 só para o Windows
            # continuar entregando o mouse a esta janela) e um contorno fino na cor
            # escolhida, para enxergar e agarrar as bordas.
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 1))
            painter.drawRoundedRect(self.rect(), radius, radius)
            outline = QColor(self._color)
            outline.setAlphaF(0.95)
            painter.setPen(QPen(outline, self._border_width))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)
            return
        fill = QColor(self._color)
        fill.setAlphaF(self._opacity)
        pen_color = QColor(self._border_color)
        pen_color.setAlphaF(min(1.0, self._opacity + 0.35))
        painter.setPen(QPen(pen_color, self._border_width))
        painter.setBrush(QBrush(fill))
        painter.drawRoundedRect(rect, radius, radius)

    # ------------------------------------------------------------------ bordas (redimensionar)
    def _edge_margin(self):
        """Largura da faixa de borda que aceita arrasto (menor em réguas finas)."""
        return max(4, min(9, self.height() // 4))

    def _edge_at(self, pos):
        if self._click_through:
            return 0
        m = self._edge_margin()
        edge = 0
        if not self._full_width:          # em largura total só há bordas de cima e de baixo
            if pos.x() <= m:
                edge |= EDGE_LEFT
            elif pos.x() >= self.width() - 1 - m:
                edge |= EDGE_RIGHT
        if pos.y() <= m:
            edge |= EDGE_TOP
        elif pos.y() >= self.height() - 1 - m:
            edge |= EDGE_BOTTOM
        return edge

    @staticmethod
    def _cursor_for(edge):
        if edge in (EDGE_LEFT | EDGE_TOP, EDGE_RIGHT | EDGE_BOTTOM):
            return Qt.CursorShape.SizeFDiagCursor
        if edge in (EDGE_RIGHT | EDGE_TOP, EDGE_LEFT | EDGE_BOTTOM):
            return Qt.CursorShape.SizeBDiagCursor
        if edge & (EDGE_LEFT | EDGE_RIGHT):
            return Qt.CursorShape.SizeHorCursor
        return Qt.CursorShape.SizeVerCursor

    def _update_cursor(self, pos):
        edge = self._edge_at(pos)
        if edge:
            self.setCursor(self._cursor_for(edge))
        else:
            self.unsetCursor()

    def _apply_resize(self, delta):
        g, e = self._resize_geo, self._resize_edge
        x, y, w, h = g.x(), g.y(), g.width(), g.height()
        lo_w, hi_w = WIDTH_RANGE
        lo_h, hi_h = HEIGHT_RANGE
        if e & EDGE_LEFT:
            nw = max(lo_w, min(hi_w, w - delta.x()))
            x, w = x + (w - nw), nw
        elif e & EDGE_RIGHT:
            w = max(lo_w, min(hi_w, w + delta.x()))
        if e & EDGE_TOP:
            nh = max(lo_h, min(hi_h, h - delta.y()))
            y, h = y + (h - nh), nh
        elif e & EDGE_BOTTOM:
            h = max(lo_h, min(hi_h, h + delta.y()))
        self.setGeometry(x, y, w, h)
        if not self._full_width:
            self._normal_width = w

    # ------------------------------------------------------------------ mouse
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._click_through:
            for button in self.buttons:
                button.raise_()
            edge = self._edge_at(event.position().toPoint())
            if edge:                                   # começa a redimensionar
                self._resize_edge = edge
                self._resize_origin = event.globalPosition().toPoint()
                self._resize_geo = self.geometry()
                self._resize_moved = False
                event.accept()
                return
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._drag_start_pos = self.pos()
            self._drag_moved = False
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        pos = event.globalPosition().toPoint()
        if self._resize_edge:
            delta = pos - self._resize_origin
            if not self._resize_moved:
                if abs(delta.x()) + abs(delta.y()) < 3:      # ignora cliques "tremidos"
                    event.accept()
                    return
                self._resize_moved = True
                self.drag_started.emit()
            self._apply_resize(delta)
            event.accept()
        elif self._drag_offset is not None and not self._click_through:
            target = pos - self._drag_offset
            if not self._drag_moved:
                delta = target - self._drag_start_pos
                if abs(delta.x()) + abs(delta.y()) >= 4:     # ignora cliques "tremidos"
                    self._drag_moved = True
                    self.drag_started.emit()
            screen = QGuiApplication.screenAt(pos) if self._full_width else None
            self.move_ruler(target.x(), target.y(), screen)
            event.accept()
        else:
            self._update_cursor(event.position().toPoint())
            event.ignore()

    def mouseReleaseEvent(self, event):
        if self._resize_edge:
            moved = self._resize_moved
            self._resize_edge = 0
            self._resize_origin = None
            self._resize_geo = None
            self._resize_moved = False
            self._update_cursor(event.position().toPoint())
            if moved:
                self.size_committed.emit(self._normal_width, self.height())
                self.position_committed.emit()
                self.user_moved.emit()
            event.accept()
            return
        if self._drag_offset is not None:
            self._drag_offset = None
            self.position_committed.emit()
            if self._drag_moved:
                self._drag_moved = False
                self.user_moved.emit()
        event.accept()

    def leaveEvent(self, event):
        if not self._resize_edge:
            self.unsetCursor()
        super().leaveEvent(event)

    def closeEvent(self, event):
        if self.close_allowed or QGuiApplication.isSavingSession():
            for button in self.buttons:
                button.close()
            self.overlay.close()
            event.accept()
            return
        # A régua é controlada pela janela principal; fechar aqui só a oculta.
        self.hide()
        event.ignore()
