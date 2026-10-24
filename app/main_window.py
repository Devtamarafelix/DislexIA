"""Janela do sistema e controlador do programa.

O programa roda em segundo plano (régua + engrenagem + ícone na bandeja).
Esta janela só aparece quando pedida: pela caixa da engrenagem, pelo ícone
da bandeja ou com `python main.py --janela`.
"""
import time

from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QColorDialog,
    QFrame, QApplication, QSystemTrayIcon, QMenu, QComboBox
)
from PySide6.QtCore import Qt

from app.controls_panel import RulerControls
from app.reader import ReadingController
from app.settings import read_setting, settings_store
from app.settings_popup import SettingsPopup
from app.theme import build_stylesheet, font_found, make_app_icon
from ruler.ruler_window import RulerWindow


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.store = settings_store()
        self.state = {
            "color": read_setting("ruler/color"),
            "opacity": read_setting("ruler/opacity"),
            "height": read_setting("ruler/height"),
            "width": read_setting("ruler/width"),
            "full_width": read_setting("ruler/full_width"),
            "click_through": read_setting("ruler/click_through"),
        }
        self.ruler = RulerWindow(
            color=self.state["color"],
            opacity=self.state["opacity"],
            height=self.state["height"],
            width=self.state["width"],
            x=read_setting("ruler/x"),
            y=read_setting("ruler/y"),
            click_through=self.state["click_through"],
            full_width=self.state["full_width"],
        )
        self.popup = SettingsPopup()
        self.reader = ReadingController(
            self.ruler, lambda: read_setting("reader/language"), self)
        self._quitting = False

        self.setWindowTitle("Leitura Acessível")
        self.setWindowIcon(make_app_icon())
        self.setFixedWidth(520)
        self.setStyleSheet(build_stylesheet())
        self._build_ui()
        self._build_tray()

        self.panels = [self.controls, self.popup.controls]
        self._connect_signals()
        self._sync_panels()

        # A engrenagem fica sempre visível (mesmo com a régua desativada)
        # para dar acesso às configurações sem abrir esta janela.
        self.ruler.show_buttons()
        if read_setting("ruler/enabled"):
            self.ruler.show()
        self.ruler.show_buttons()
        self._refresh_state()

    # ------------------------------------------------------------------ interface
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel("Leitura Acessível")
        title.setObjectName("title")
        subtitle = QLabel("Um espaço de leitura no seu ritmo.")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.status = QLabel("● Régua ativa")
        layout.addWidget(self.status)

        if not font_found():
            warn = QLabel("A fonte OpenDyslexic não foi encontrada. Rode preparar_offline.py ou copie os "
                          ".otf para a pasta fonts/ (veja fonts/LEIAME.txt) e reabra o programa.")
            warn.setWordWrap(True)
            warn.setStyleSheet("color:#9A5B00;font-size:8.5pt;")
            layout.addWidget(warn)

        actions = QHBoxLayout()
        self.toggle_button = QPushButton("Desativar régua")
        self.toggle_button.setMinimumHeight(42)
        self.center_button = QPushButton("Centralizar")
        self.center_button.setObjectName("secondary")
        self.center_button.setMinimumHeight(42)
        actions.addWidget(self.toggle_button, 2)
        actions.addWidget(self.center_button, 1)
        layout.addLayout(actions)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(17, 17, 17, 17)
        panel_layout.setSpacing(14)
        heading = QLabel("Personalizar régua")
        heading.setObjectName("heading")
        panel_layout.addWidget(heading)
        self.controls = RulerControls()
        panel_layout.addWidget(self.controls)
        hint = QLabel("Dica: arraste a régua com o botão esquerdo do mouse. Para movê-la, desative "
                      "temporariamente a opção de cliques por baixo. A engrenagem na régua abre uma "
                      "caixa com estas mesmas opções.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#65718A;font-size:8.5pt;")
        panel_layout.addWidget(hint)
        layout.addWidget(panel)

        ai_panel = QFrame()
        ai_panel.setObjectName("panel")
        ai_layout = QVBoxLayout(ai_panel)
        ai_layout.setContentsMargins(17, 17, 17, 17)
        ai_layout.setSpacing(10)
        ai_heading = QLabel("Leitura em voz alta (100% local)")
        ai_heading.setObjectName("heading")
        ai_layout.addWidget(ai_heading)
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Idioma do texto"))
        lang_row.addStretch()
        self.language_combo = QComboBox()
        for label, code in (("Português (Brasil)", "pt-BR"), ("English (US)", "en-US"),
                            ("Español", "es-ES")):
            self.language_combo.addItem(label, code)
        index = self.language_combo.findData(read_setting("reader/language"))
        self.language_combo.setCurrentIndex(max(0, index))
        lang_row.addWidget(self.language_combo)
        ai_layout.addLayout(lang_row)
        ai_hint = QLabel("O botão ▶ da régua fotografa só a área sob a régua, o OCR do computador "
                         "(Tesseract) lê o texto e a voz do Windows fala. Tudo roda neste "
                         "computador, sem internet e sem enviar nada para fora.")
        ai_hint.setWordWrap(True)
        ai_hint.setStyleSheet("color:#65718A;font-size:8.5pt;")
        ai_layout.addWidget(ai_hint)
        layout.addWidget(ai_panel)

        self.quit_button = QPushButton("Encerrar programa")
        self.quit_button.setObjectName("secondary")
        self.quit_button.setToolTip("Fechar esta janela só a esconde; o programa continua em segundo plano. Use este botão para sair de vez.")
        layout.addWidget(self.quit_button)

        footer = QLabel("Protótipo 0.5 • Preferências salvas automaticamente")
        footer.setStyleSheet("color:#7A8499;font-size:8pt;")
        layout.addWidget(footer)

    def _build_tray(self):
        self.tray = QSystemTrayIcon(make_app_icon(), self)
        self.tray.setToolTip("Leitura Acessível — clique para ligar/desligar a régua")
        self._tray_menu = QMenu()
        self.tray_toggle_action = self._tray_menu.addAction("Desativar régua")
        self.tray_toggle_action.triggered.connect(self._toggle_ruler)
        self._tray_menu.addAction("Abrir janela do sistema").triggered.connect(self.show_settings)
        self._tray_menu.addSeparator()
        self._tray_menu.addAction("Encerrar programa").triggered.connect(self._quit_app)
        self.tray.setContextMenu(self._tray_menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _connect_signals(self):
        self.toggle_button.clicked.connect(self._toggle_ruler)
        self.center_button.clicked.connect(self._center_ruler)
        self.quit_button.clicked.connect(self._quit_app)
        self.language_combo.currentIndexChanged.connect(self._language_changed)
        self.ruler.play_button.clicked.connect(self.reader.play)
        self.ruler.repeat_button.clicked.connect(self.reader.repeat)
        self.reader.state_changed.connect(self._reader_state_changed)
        self.reader.message.connect(self._show_message)
        for panel in self.panels:
            panel.color_requested.connect(self._choose_color)
            panel.opacity_changed.connect(self._opacity_changed)
            panel.height_changed.connect(self._height_changed)
            panel.width_changed.connect(self._width_changed)
            panel.full_width_toggled.connect(self._full_width_changed)
            panel.click_through_toggled.connect(self._click_through_changed)
        self.popup.toggle_requested.connect(self._toggle_ruler)
        self.popup.open_system_requested.connect(self.show_settings)
        self.ruler.gear.clicked.connect(self._gear_clicked)
        self.ruler.position_committed.connect(self._save_ruler_position)

    # ------------------------------------------------------------------ estado
    def _save(self, key, value):
        self.store.setValue(key, value)
        self.store.sync()

    def _update(self, key, value):
        self.state[key] = value
        self._save(f"ruler/{key}", value)
        self._sync_panels()

    def _sync_panels(self):
        s = self.state
        for panel in self.panels:
            panel.set_values(s["color"], s["opacity"], s["height"], s["width"],
                             s["full_width"], s["click_through"])

    def _refresh_state(self):
        active = self.ruler.isVisible()
        self.toggle_button.setText("Desativar régua" if active else "Ativar régua")
        self.tray_toggle_action.setText("Desativar régua" if active else "Ativar régua")
        self.popup.set_active(active)
        self.status.setText("● Régua ativa" if active else "○ Régua desativada")
        self.status.setStyleSheet(
            "color:#23835D;font-weight:650;padding:4px 0;" if active
            else "color:#7A8499;font-weight:650;padding:4px 0;"
        )

    def _language_changed(self, _index):
        self._save("reader/language", self.language_combo.currentData())

    def _reader_state_changed(self, state):
        if state == "idle":
            self.ruler.play_button.set_kind("play", "Ler em voz alta o texto sob a régua")
        else:
            self.ruler.play_button.set_kind("stop", "Parar a leitura")

    def _show_message(self, text):
        self.tray.showMessage("Leitura Acessível", text,
                              QSystemTrayIcon.MessageIcon.Warning, 6000)

    def _save_ruler_position(self):
        # Em largura total o x "real" é o da tela; guardamos o x normal para poder voltar.
        self._save("ruler/x", self.ruler.normal_x())
        self._save("ruler/y", self.ruler.y())

    # ------------------------------------------------------------------ ações
    def _toggle_ruler(self):
        if self.ruler.isVisible():
            self.ruler.hide()
            self._save("ruler/enabled", False)
        else:
            self.ruler.show()
            self.ruler.raise_()
            self.ruler.show_buttons()
            self._save("ruler/enabled", True)
        self._refresh_state()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_ruler()

    def _gear_clicked(self):
        # Clicar na engrenagem com a caixa aberta só a fecha.
        if self.popup.isVisible():
            self.popup.hide()
            return
        if time.monotonic() - self.popup.last_hidden < 0.25:
            return
        self.popup.show_below(self.ruler.gear)

    def _center_ruler(self):
        screen = (QGuiApplication.screenAt(self.ruler.geometry().center())
                  or QGuiApplication.primaryScreen())
        if screen:
            area = screen.availableGeometry()
            x = area.x() + (area.width() - self.ruler.width()) // 2
            y = area.y() + area.height() // 2
            self.ruler.move_ruler(x, y, screen)
            self._save_ruler_position()
            if not self.ruler.isVisible():
                self.ruler.show()
                self._save("ruler/enabled", True)
            self._refresh_state()

    def _choose_color(self):
        popup_was_open = self.popup.isVisible()
        if popup_was_open:
            self.popup.hide()
        dialog = QColorDialog(QColor(self.state["color"]))
        dialog.setWindowTitle("Escolha a cor da régua")
        dialog.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        if dialog.exec():
            color = dialog.currentColor()
            if color.isValid():
                self.ruler.set_color(color.name())
                self._update("color", color.name())
        if popup_was_open:
            self.popup.show_below(self.ruler.gear)

    def _opacity_changed(self, value):
        self.ruler.set_opacity(value)
        self._update("opacity", value)

    def _height_changed(self, value):
        self.ruler.set_ruler_size(height=value)
        self._update("height", value)

    def _width_changed(self, value):
        self.ruler.set_ruler_size(width=value)
        self._update("width", value)

    def _full_width_changed(self, checked):
        self.ruler.set_full_width(checked)
        self._update("full_width", checked)
        self._save_ruler_position()

    def _click_through_changed(self, checked):
        self.ruler.set_click_through(checked)
        self._update("click_through", checked)

    def show_settings(self):
        """Abre (ou traz para a frente) a janela do sistema."""
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()

    def _quit_app(self):
        self._save("ruler/enabled", self.ruler.isVisible())
        self._save_ruler_position()
        self._quitting = True
        self.reader.stop()
        self.ruler.close_allowed = True
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        # Fechar esta janela só a esconde: o programa segue em segundo plano.
        if self._quitting or QGuiApplication.isSavingSession():
            event.accept()
            return
        self._save("ruler/enabled", self.ruler.isVisible())
        self._save_ruler_position()
        event.ignore()
        self.hide()
