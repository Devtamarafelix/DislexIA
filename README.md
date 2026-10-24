# Leitura Acessível — Protótipo 0.5

Protótipo desktop em Python com uma régua de leitura flutuante, caixa de configurações na engrenagem e leitura em voz alta do texto sob a régua. Tudo roda **100% local**: não precisa de internet e nada sai do computador.

## Requisitos

- Windows 10/11 (primeiro alvo testável).
- Python 3.14.x de 64 bits recomendado para o projeto completo, por equilibrar atualidade e compatibilidade de bibliotecas.
- Dependências Python: PySide6 6.12.0, Pillow e pytesseract (já em `requirements.txt`).
- Para a leitura em voz alta: o programa **Tesseract OCR** instalado no Windows (veja "Leitura offline" abaixo) e uma voz em português instalada no Windows (Configurações > Hora e idioma > Fala).
- PySide6/Qt possui licenças LGPL/GPL e comercial. Antes de distribuir um executável, leia as condições oficiais: https://doc.qt.io/qt-6/licensing.html

## Instalação no Windows

1. Instale Python 3.14 (64-bit) em https://www.python.org/downloads/windows/.
2. Durante a instalação, marque **Add Python to PATH**.
3. Extraia o ZIP para uma pasta, por exemplo `C:\Projetos\dislexia_app_prototipo`.
4. Abra essa pasta no VS Code ou no Explorador de Arquivos.
5. Abra um terminal nessa pasta e execute:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Se o PowerShell impedir a ativação do ambiente virtual, você pode usar o Prompt de Comando (cmd):

```bat
py -3.14 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Se o comando `py -3.14` não for encontrado, confira a instalação com `py --list` ou `python --version`.

## Fonte OpenDyslexic

A interface usa a OpenDyslexic. O `preparar_offline.py` (veja "Leitura offline") baixa os arquivos `.otf` para a pasta `fonts/`; também dá para baixá-los em https://opendyslexic.org/ (licença SIL OFL) e copiá-los para lá (veja `fonts/LEIAME.txt`). Se a fonte já estiver instalada no Windows, também funciona. Sem ela, o programa usa Segoe UI e mostra um aviso na janela do sistema.

## Leitura offline (voz alta sob a régua)

Tudo é local: o OCR é o Tesseract (via `pytesseract`) e a voz é a do próprio Windows (QtTextToSpeech). Não há chamadas à internet.

### Deixar o projeto autocontido (recomendado)

Para o usuário final não precisar baixar nada, deixe o Tesseract, os idiomas e a fonte **dentro da pasta do projeto**. Faça isto uma vez, na sua máquina, com internet:

1. Instale o Tesseract no Windows com o instalador da UB Mannheim: https://github.com/UB-Mannheim/tesseract/wiki (pasta padrão `C:\Program Files\Tesseract-OCR`).
2. Na pasta do projeto, rode (ou dê dois cliques em `preparar_offline.bat`):

```powershell
python preparar_offline.py
```

O script (só biblioteca padrão do Python):
- copia o Tesseract instalado para `tesseract/`;
- baixa `por`, `eng` e `spa` (tessdata_fast) para `tessdata/`;
- baixa a OpenDyslexic (Regular e Bold) para `fonts/`.

Se o Tesseract estiver em outra pasta: `python preparar_offline.py --tesseract-origem "D:\Programas\Tesseract-OCR"`. O script pode ser rodado de novo sem problema e pula o que já existe.

Depois, é só copiar/zipar a pasta inteira do projeto: ela funciona sem internet e sem instalar o Tesseract nem a fonte no sistema. O programa procura primeiro `tesseract/tesseract.exe` do projeto e usa os idiomas de `tessdata/`. Licenças em `LICENCAS-TERCEIROS.txt`.

### Sem o script (manual)

- Instale o Tesseract normalmente marcando **Portuguese** em *Additional language data*; o programa o encontra sozinho.
- Ou copie a pasta do Tesseract para `tesseract/` e o `por.traineddata` para `tessdata/` (veja `tessdata/LEIAME.txt`).

**Usar:**

- Os botões ficam na ponta direita da régua: **▶ play**, **↻ repetir** e **⚙ engrenagem**.
- **▶ play**: a régua some por um instante, o programa fotografa só a área sob ela, o OCR lê o texto e a voz do computador fala. Durante a leitura o botão vira **■ parar**.
- **↻ repetir**: fala de novo o último texto, sem refazer o OCR.
- Escolha o **idioma do texto** (Português, English ou Español) na janela do sistema; ele define o OCR e a voz.
- Dica de qualidade: o OCR funciona melhor com texto nítido e contraste alto; fundos escuros são invertidos automaticamente.

## Como usar

O programa roda em segundo plano: ao abrir, aparecem só a régua, a engrenagem e um ícone na bandeja do sistema.

- **Engrenagem**: abre uma caixa logo abaixo dela com ligar/desligar, cor, transparência, altura, largura, largura total, cliques por baixo e o botão **Abrir janela do sistema**.
- **Ícone da bandeja**: clique para ligar/desligar a régua; clique direito para abrir a janela do sistema ou encerrar.
- **Janela do sistema**: fechar pelo X só a esconde. Use **Encerrar programa** para sair de vez. Para abri-la já na inicialização: `python main.py --janela`.

## Como testar

1. Abra o aplicativo: a régua deve aparecer sobre as outras janelas.
2. Arraste a régua pelo corpo dela com o botão esquerdo do mouse.
3. Use **Escolher cor** para mudar a cor.
4. Ajuste transparência, altura e largura nos controles deslizantes.
5. Clique em **Desativar régua** e depois em **Ativar régua**.
6. Ative **Permitir cliques no conteúdo abaixo** e teste clicar em uma janela atrás da régua. Para arrastá-la novamente, desmarque essa opção.
7. Feche e reabra o aplicativo para verificar se as preferências foram mantidas.
8. Clique no botão de engrenagem na ponta direita da régua: uma caixa de configurações deve abrir logo abaixo dela (clicar fora ou em Esc fecha). A engrenagem é sempre opaca, mesmo com a régua bem transparente, e continua clicável com **Permitir cliques no conteúdo abaixo** ativado.
9. Na caixa, use **Abrir janela do sistema**; feche-a pelo X: a régua e a engrenagem devem continuar na tela. Use **Encerrar programa** para sair de vez.
10. Ative **Régua em largura total da tela**: a régua ocupa toda a largura da tela e, ao arrastar, só se move na vertical (com vários monitores, ela se ajusta ao monitor onde o mouse estiver). Ao desativar, volta à largura anterior.
11. Coloque a régua sobre uma linha de texto e clique em **▶**: a régua pisca, o botão vira **■** e o texto é lido. Clique em **↻** para ouvir de novo, e em **■** para interromper.
12. Desligue a internet e repita o teste: deve funcionar igual. Sem o Tesseract ou sem o idioma, deve aparecer uma notificação na bandeja explicando o que falta.

## Limitações conhecidas desta versão

- O modo de clique-transparente usa a flag de janela do Qt. O comportamento deve ser testado no Windows real; outros sistemas operacionais ainda não foram validados.
- Quando a régua ignora os eventos do mouse, ela não pode ser arrastada diretamente. Desative temporariamente essa opção para mover a régua.
- A régua é uma faixa visual, não identifica linhas de texto automaticamente.
- OCR, leitura em voz alta, atalhos globais, perfis e empacotamento em executável ainda não estão incluídos.
- A aplicação foi criada no ambiente de desenvolvimento desta conversa, mas não foi possível executar uma validação gráfica no Windows do usuário. Por isso, siga a lista de testes e compartilhe qualquer erro exato do terminal.

## Estrutura

```text
dislexia_app_prototipo/
├── main.py
├── requirements.txt
├── README.md
├── app/
│   ├── __init__.py
│   ├── controls_panel.py
│   ├── main_window.py
│   ├── ocr.py
│   ├── reader.py
│   ├── settings.py
│   ├── settings_popup.py
│   └── theme.py
├── preparar_offline.py
├── preparar_offline.bat
├── LICENCAS-TERCEIROS.txt
├── fonts/
│   └── LEIAME.txt
├── tessdata/
│   └── LEIAME.txt
└── ruler/
    ├── __init__.py
    ├── ruler_buttons.py
    └── ruler_window.py
```

## Próximas etapas

1. Validar no Windows a captura sob a régua em monitores com escala de DPI diferente.
2. Escolher a velocidade e a voz da leitura nas configurações.
3. Opção de ler a partir da régua para baixo (mais de uma linha).
4. Avaliar vozes neurais offline (por exemplo Piper) se a voz do Windows não agradar.
5. Empacotar em um único `.exe` (PyInstaller) incluindo `tesseract/`, `tessdata/` e `fonts/`, para o usuário nem precisar instalar o Python.
6. Testes automatizados e testes manuais.
