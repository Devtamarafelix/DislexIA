"""Fonte (OpenDyslexic), estilo visual e ícone compartilhados."""
import os

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPen, QPixmap

FALLBACK_FAMILY = "Segoe UI"
_state = {"family": FALLBACK_FAMILY, "found": False}


def _fonts_dir():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "fonts")


def setup_fonts(app):
    """Carrega a OpenDyslexic (pasta fonts/ ou instalada no sistema).

    Deve ser chamada depois de criar o QApplication.
    """
    families = []
    fonts_dir = _fonts_dir()
    if os.path.isdir(fonts_dir):
        for name in sorted(os.listdir(fonts_dir)):
            if name.lower().endswith((".otf", ".ttf")):
                font_id = QFontDatabase.addApplicationFont(os.path.join(fonts_dir, name))
                if font_id != -1:
                    families.extend(QFontDatabase.applicationFontFamilies(font_id))
    families.extend(QFontDatabase.families())

    chosen = next((f for f in families if f.lower() == "opendyslexic"), None)
    if chosen is None:
        chosen = next((f for f in families if f.lower().startswith("opendyslexic")), None)
    if chosen:
        _state["family"] = chosen
        _state["found"] = True
    app.setFont(QFont(_state["family"], 9))


def font_family():
    return _state["family"]


def font_found():
    return _state["found"]


def build_stylesheet():
    fam = font_family()
    return f"""
        QWidget {{ background: #F4F6FA; color: #20283A; font-family: "{fam}"; font-size: 9pt; }}
        QWidget#popupRoot {{ background: transparent; }}
        QWidget#controls {{ background: transparent; }}
        QLabel, QCheckBox, QSlider {{ background: transparent; }}
        QLabel#title {{ font-size: 17pt; font-weight: 700; color: #19243A; }}
        QLabel#subtitle {{ color: #65718A; }}
        QLabel#heading {{ font-size: 10pt; font-weight: 700; }}
        QFrame#panel {{ background: white; border: 1px solid #E0E5EF; border-radius: 14px; }}
        QFrame#popupPanel {{ background: white; border: 1px solid #C9D1E3; border-radius: 14px; }}
        QPushButton {{ background: #334E8C; color: white; border: 0; border-radius: 9px; padding: 10px 12px; font-weight: 600; }}
        QPushButton:hover {{ background: #263D70; }}
        QPushButton:disabled {{ background: #AEB8D0; }}
        QPushButton#secondary {{ background: #E8EDF7; color: #263D70; }}
        QPushButton#secondary:hover {{ background: #DDE5F4; }}
        QSlider::groove:horizontal {{ height: 6px; background: #DCE2EE; border-radius: 3px; }}
        QSlider::handle:horizontal {{ background: #334E8C; width: 16px; margin: -5px 0; border-radius: 8px; }}
        QSlider::groove:horizontal:disabled {{ background: #ECEFF5; }}
        QSlider::handle:horizontal:disabled {{ background: #AEB8D0; }}
        QCheckBox {{ spacing: 8px; }}
        QLineEdit {{ background: white; border: 1px solid #C9D1E3; border-radius: 9px; padding: 9px 10px; }}
        QLineEdit:focus {{ border: 1px solid #334E8C; }}
        QComboBox {{ background: white; border: 1px solid #C9D1E3; border-radius: 9px; padding: 8px 10px; }}
        QComboBox QAbstractItemView {{ background: white; selection-background-color: #DDE5F4; selection-color: #20283A; }}
    """


def make_app_icon():
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#5B4B00"), 3))
    painter.setBrush(QColor("#FFE66D"))
    painter.drawRoundedRect(QRectF(4, 20, 56, 24), 6, 6)
    painter.end()
    return QIcon(pix)
