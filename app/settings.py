"""Leitura e gravação das preferências usando QSettings."""
from PySide6.QtCore import QSettings

DEFAULTS = {
    "ruler/color": "#FFE66D",
    "ruler/opacity": 48,
    "ruler/height": 58,
    "ruler/width": 1000,
    "ruler/x": 180,
    "ruler/y": 300,
    "ruler/enabled": True,
    "ruler/click_through": False,
    "ruler/full_width": False,
}

def settings_store():
    return QSettings("ProjetoAcessibilidade", "LeituraAcessivel")

def read_setting(key):
    settings = settings_store()
    default = DEFAULTS[key]
    value = settings.value(key, default)
    if isinstance(default, bool):
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)
    if isinstance(default, int):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    return value
