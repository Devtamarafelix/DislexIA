"""Controles de personalização da régua, reutilizados na caixa da engrenagem
e na janela do sistema. Só emitem sinais; quem aplica é a MainWindow."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QCheckBox

from app.settings import DIM_RANGE, HEIGHT_RANGE, WIDTH_RANGE


class RulerControls(QWidget):
    color_requested = Signal()
    opacity_changed = Signal(int)
    height_changed = Signal(int)
    width_changed = Signal(int)
    full_width_toggled = Signal(bool)
    click_through_toggled = Signal(bool)
    auto_read_toggled = Signal(bool)
    reverse_toggled = Signal(bool)
    dim_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controls")
        self._sliders = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Cor da régua"))
        color_row.addStretch()
        self.color_button = QPushButton("Escolher cor")
        self.color_button.setObjectName("secondary")
        color_row.addWidget(self.color_button)
        layout.addLayout(color_row)

        self.reverse = QCheckBox("Régua reversa (escurece o resto da tela)")
        self.reverse.setToolTip("Em vez de colorir a faixa, a régua fica transparente e o resto da tela "
                                "escurece, para você focar só no trecho iluminado.")
        layout.addWidget(self.reverse)

        # A ordem dos controles deslizantes precisa bater com a de set_values().
        self.opacity_slider = self._add_slider(layout, "Transparência", 5, 100, "%")
        self.dim_slider = self._add_slider(layout, "Escurecimento do fundo", DIM_RANGE[0], DIM_RANGE[1], "%")
        self.height_slider = self._add_slider(layout, "Altura", HEIGHT_RANGE[0], HEIGHT_RANGE[1], " px")
        self.width_slider = self._add_slider(layout, "Largura", WIDTH_RANGE[0], WIDTH_RANGE[1], " px")

        self.full_width = QCheckBox("Régua em largura total da tela")
        self.full_width.setToolTip("A régua ocupa a tela inteira na horizontal; ao arrastar, ela só se move para cima e para baixo.")
        layout.addWidget(self.full_width)

        self.click_through = QCheckBox("Permitir cliques no conteúdo abaixo")
        self.click_through.setToolTip("Ao ativar, a régua ignora o mouse. Desative para voltar a movê-la.")
        layout.addWidget(self.click_through)

        self.auto_read = QCheckBox("Ler em voz alta ao mover a régua")
        self.auto_read.setToolTip("Ao soltar a régua sobre um texto, ele é lido automaticamente. "
                                  "Mover a régua de novo interrompe a leitura.")
        layout.addWidget(self.auto_read)

        self.color_button.clicked.connect(self.color_requested)
        self.opacity_slider.valueChanged.connect(self.opacity_changed)
        self.height_slider.valueChanged.connect(self.height_changed)
        self.width_slider.valueChanged.connect(self.width_changed)
        self.full_width.toggled.connect(self.full_width_toggled)
        self.click_through.toggled.connect(self.click_through_toggled)
        self.auto_read.toggled.connect(self.auto_read_toggled)
        self.reverse.toggled.connect(self.reverse_toggled)
        self.dim_slider.valueChanged.connect(self.dim_changed)
        self.reverse.toggled.connect(self._update_reverse_enabled)
        self.full_width.toggled.connect(lambda checked: self.width_slider.setEnabled(not checked))

    def _add_slider(self, parent, label_text, minimum, maximum, suffix):
        row = QHBoxLayout()
        value_label = QLabel()
        value_label.setMinimumWidth(70)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(QLabel(label_text))
        row.addStretch()
        row.addWidget(value_label)
        parent.addLayout(row)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        parent.addWidget(slider)
        slider.valueChanged.connect(lambda value, t=value_label, s=suffix: t.setText(f"{value}{s}"))
        self._sliders.append((slider, value_label, suffix))
        return slider

    def set_color(self, color):
        self.color_button.setStyleSheet(
            f"background:{color}; color:#20283A; border:1px solid #C7CEDC;"
            "border-radius:9px;padding:10px 12px;font-weight:600;"
        )

    def _update_reverse_enabled(self, reverse):
        """Na régua reversa a faixa é transparente (só o escurecimento vale)."""
        self.opacity_slider.setEnabled(not reverse)
        self.dim_slider.setEnabled(reverse)

    def set_values(self, color, opacity, height, width, full_width, click_through,
                   auto_read=True, reverse=False, dim=70):
        """Atualiza os controles sem disparar sinais."""
        self.set_color(color)
        for (slider, label, suffix), value in zip(
                self._sliders, (opacity, dim, height, width)):
            slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(False)
            label.setText(f"{slider.value()}{suffix}")
        for box, value in ((self.full_width, full_width), (self.click_through, click_through),
                           (self.auto_read, auto_read), (self.reverse, reverse)):
            box.blockSignals(True)
            box.setChecked(bool(value))
            box.blockSignals(False)
        self.width_slider.setEnabled(not full_width)
        self._update_reverse_enabled(bool(reverse))
