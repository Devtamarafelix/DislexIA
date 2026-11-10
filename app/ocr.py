"""OCR 100% local com Tesseract (via pytesseract). Nada sai do computador."""
import io
import os
import shutil

# idioma da leitura -> código do Tesseract
LANGS = {"pt-BR": "por", "en-US": "eng", "es-ES": "spa"}

_languages_cache = {}


def _project_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_tesseract():
    """Procura o tesseract: pasta do projeto (portátil), PATH e instalações comuns."""
    exe = "tesseract.exe" if os.name == "nt" else "tesseract"
    candidates = [os.path.join(_project_dir(), "tesseract", exe)]
    found = shutil.which("tesseract")
    if found:
        candidates.append(found)
    for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            candidates.append(os.path.join(base, "Tesseract-OCR", "tesseract.exe"))
            candidates.append(os.path.join(base, "Programs", "Tesseract-OCR", "tesseract.exe"))
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def _use_local_tessdata():
    """Se existir tessdata/ no projeto com idiomas, o Tesseract passa a usá-la."""
    folder = os.path.join(_project_dir(), "tessdata")
    if os.path.isdir(folder) and any(f.endswith(".traineddata") for f in os.listdir(folder)):
        os.environ["TESSDATA_PREFIX"] = folder


def check(lang_code):
    """Confere bibliotecas, programa e idioma. Retorna (ok, mensagem_de_erro)."""
    try:
        import pytesseract
        import PIL  # noqa: F401
    except ImportError:
        return False, ("Faltam as bibliotecas 'pytesseract' e 'Pillow'. "
                       "Rode: pip install -r requirements.txt")
    except Exception as exc:  # noqa: BLE001 - ex.: Pillow incompatível com esta versão do Python
        return False, ("As bibliotecas de OCR não funcionam nesta versão do Python "
                       f"({exc}). Use o Python 3.14 em um ambiente virtual (.venv); "
                       "veja o README, seção Instalação.")
    cmd = find_tesseract()
    if not cmd:
        return False, ("O Tesseract (OCR) não foi encontrado. Rode preparar_offline.py ou instale-o; veja "
                       "o README, seção Leitura offline.")
    pytesseract.pytesseract.tesseract_cmd = cmd
    _use_local_tessdata()
    key = (cmd, os.environ.get("TESSDATA_PREFIX", ""))
    if key not in _languages_cache:
        try:
            _languages_cache[key] = set(pytesseract.get_languages(config=""))
        except Exception as exc:  # noqa: BLE001
            return False, f"Não consegui executar o Tesseract: {exc}"
    need = LANGS.get(lang_code, "por")
    if need not in _languages_cache[key]:
        return False, (f"Falta o idioma '{need}' do Tesseract (arquivo {need}.traineddata). "
                       "Veja o README, seção Leitura offline.")
    return True, ""


def recognize(png_bytes, lang_code):
    """Reconhece o texto de uma imagem PNG. Retorna o texto (vazio se não achar nada), sem ação."""
    import pytesseract
    from PIL import Image, ImageOps, ImageStat

    image = Image.open(io.BytesIO(png_bytes)).convert("L")
    if ImageStat.Stat(image).mean[0] < 110:        # fundo escuro: inverte
        image = ImageOps.invert(image)
    # Faixas finas rendem mais ampliadas (alvo: ~120 px de altura, até 4x).
    factor = max(1, min(4, round(120 / max(1, image.height))))
    if factor > 1:
        resample = getattr(Image, "Resampling", Image).LANCZOS
        image = image.resize((image.width * factor, image.height * factor), resample)
    image = ImageOps.autocontrast(image)
    image = ImageOps.expand(image, border=16, fill=255)
    text = pytesseract.image_to_string(
        image, lang=LANGS.get(lang_code, "por"), config="--psm 6")
    return " ".join(text.split())
