"""Leitura em voz alta do texto sob a régua, 100% local (sem internet).

Fluxo: fotografa a região da tela sob a régua -> OCR local (Tesseract) lê o
texto -> a voz do computador (QtTextToSpeech) fala. O botão de repetir fala de
novo o último texto, sem refazer o OCR.
"""
from PySide6.QtCore import (
    QBuffer, QByteArray, QIODevice, QLocale, QObject, QRect, Qt, QThread, QTimer, Signal
)
from PySide6.QtGui import QGuiApplication

from app import ocr

try:
    from PySide6.QtTextToSpeech import QTextToSpeech
except ImportError:  # módulo de voz ausente
    QTextToSpeech = None


class OcrWorker(QThread):
    """Roda o OCR local em segundo plano para não travar a régua."""
    done = Signal(int, str, str)    # job, idioma, texto
    failed = Signal(int, str)       # job, mensagem

    def __init__(self, job, png_bytes, lang):
        super().__init__()
        self.job = job
        self.png_bytes = png_bytes
        self.lang = lang

    def run(self):
        ok, error = ocr.check(self.lang)
        if not ok:
            self.failed.emit(self.job, error)
            return
        try:
            text = ocr.recognize(self.png_bytes, self.lang)
        except Exception as exc:  # noqa: BLE001 - qualquer falha vira aviso ao usuário
            self.failed.emit(self.job, f"Falha ao reconhecer o texto: {exc}")
            return
        if not text:
            self.failed.emit(self.job, "Não encontrei texto legível sob a régua.")
        else:
            self.done.emit(self.job, self.lang, text)


class ReadingController(QObject):
    state_changed = Signal(str)     # "idle" | "loading" | "speaking"
    message = Signal(str)           # aviso para o usuário

    def __init__(self, ruler, get_language, parent=None):
        super().__init__(parent)
        self.ruler = ruler
        self._get_language = get_language
        self._state = "idle"
        self._job = 0
        self._last_text = ""
        self._last_lang = "pt-BR"
        self._workers = set()
        self.tts = QTextToSpeech(self) if QTextToSpeech is not None else None
        if self.tts is not None:
            self.tts.stateChanged.connect(self._tts_state_changed)

    # ------------------------------------------------------------------ estado
    def state(self):
        return self._state

    def _set_state(self, state):
        if state != self._state:
            self._state = state
            self.state_changed.emit(state)

    def _tts_state_changed(self, state):
        if state == QTextToSpeech.State.Ready and self._state == "speaking":
            self._set_state("idle")
        elif state == QTextToSpeech.State.Speaking and self._state != "loading":
            self._set_state("speaking")

    # ------------------------------------------------------------------ ações
    def play(self):
        """Play: lê o texto sob a régua. Durante a leitura, vira 'parar'."""
        if self._state != "idle":
            self.stop()
            return
        if self.tts is None:
            self.message.emit("A voz do computador não está disponível (módulo QtTextToSpeech).")
            return
        if ocr.find_tesseract() is None:
            self.message.emit("O Tesseract (OCR) não foi encontrado. Veja o README, "
                              "seção Leitura offline.")
            return
        self._job += 1
        job = self._job
        self._set_state("loading")
        self.ruler.begin_capture()
        # Pequena espera para o Windows redesenhar a tela sem a régua.
        QTimer.singleShot(150, lambda: self._capture_and_read(job))

    def repeat(self):
        """Fala de novo o último texto, sem refazer o OCR."""
        if self._state == "loading":
            return
        if not self._last_text:
            self.message.emit("Ainda não há nada para repetir. Use o botão de play primeiro.")
            return
        if self.tts is None:
            return
        self.tts.stop()
        self._speak(self._last_text, self._last_lang)

    def stop(self):
        self._job += 1   # ignora respostas que ainda estejam a caminho
        if self.tts is not None:
            self.tts.stop()
        self._set_state("idle")

    # ------------------------------------------------------------------ captura + OCR
    def _capture_and_read(self, job):
        if job != self._job:             # o usuário parou antes da foto
            self.ruler.end_capture()
            return
        png = self._grab_ruler_area()
        self.ruler.end_capture()
        if png is None:
            self._set_state("idle")
            self.message.emit("Não consegui fotografar a tela sob a régua.")
            return
        worker = OcrWorker(job, png, self._get_language())
        worker.done.connect(self._on_done)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(lambda w=worker: self._workers.discard(w))
        self._workers.add(worker)
        worker.start()

    def _grab_ruler_area(self):
        geo = self.ruler.geometry()
        screen = QGuiApplication.screenAt(geo.center()) or QGuiApplication.primaryScreen()
        if screen is None:
            return None
        full = screen.grabWindow(0)
        sg = screen.geometry()
        if full.isNull() or sg.width() == 0:
            return None
        scale = full.width() / sg.width()          # pixels reais por pixel lógico
        rect = QRect(round((geo.x() - sg.x()) * scale), round((geo.y() - sg.y()) * scale),
                     round(geo.width() * scale), round(geo.height() * scale))
        crop = full.copy(rect.intersected(full.rect()))
        if crop.isNull():
            return None
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        crop.save(buffer, "PNG")
        buffer.close()
        return bytes(data)

    def _on_done(self, job, lang, text):
        if job != self._job or self._state != "loading":
            return
        self._last_text, self._last_lang = text, lang
        self._speak(text, lang)

    def _on_failed(self, job, text):
        if job != self._job:
            return
        self._set_state("idle")
        self.message.emit(text)

    # ------------------------------------------------------------------ voz
    def _speak(self, text, lang):
        self.tts.setLocale(QLocale(lang.replace("-", "_")))
        self.tts.say(text)
        self._set_state("speaking")
