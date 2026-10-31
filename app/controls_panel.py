"""Controles de personalização da régua, reutilizados na caixa da engrenagem
e na janela do sistema. Só emitem sinais; quem aplica é a MainWindow."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QCheckBox


class RulerControls(QWidget):
    color_requested = Signal()
    opacity_changed = Signal(int)
    height_changed = Signal(int)
    width_changed = Signal(int)
    full_width_toggled = Signal(bool)
    click_through_toggled = Signal(bool)
    auto_read_toggled = Signal(bool)

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

        self.opacity_slider = self._add_slider(layout, "Transparência", 5, 100, "%")
        self.height_slider = self._add_slider(layout, "Altura", 24, 180, " px")
        self.width_slider = self._add_slider(layout, "Largura", 300, 1800, " px")

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

    def set_values(self, color, opacity, height, width, full_width, click_through, auto_read=True):
        """Atualiza os controles sem disparar sinais."""
        self.set_color(color)
        for (slider, label, suffix), value in zip(
                self._sliders, (opacity, height, width)):
            slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(False)
            label.setText(f"{slider.value()}{suffix}")
        for box, value in ((self.full_width, full_width), (self.click_through, click_through),
                           (self.auto_read, auto_read)):
            box.blockSignals(True)
            box.setChecked(bool(value))
            box.blockSignals(False)
        self.width_slider.setEnabled(not full_width)
