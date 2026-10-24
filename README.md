# Leitura Acessível — Protótipo 0.3

Primeiro protótipo desktop em Python com uma janela de controle e uma régua flutuante. Nesta etapa, o OCR e a leitura em voz alta ainda **não foram implementados**.

## Requisitos

- Windows 10/11 (primeiro alvo testável).
- Python 3.14.x de 64 bits recomendado para o projeto completo, por equilibrar atualidade e compatibilidade de bibliotecas.
- Para esta primeira versão, a dependência Python é apenas PySide6 6.12.0.
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

A interface usa a OpenDyslexic. Baixe em https://opendyslexic.org/ (licença SIL OFL) e copie os arquivos `.otf` para a pasta `fonts/` (veja `fonts/LEIAME.txt`). Se a fonte já estiver instalada no Windows, também funciona. Sem ela, o programa usa Segoe UI e mostra um aviso na janela do sistema.

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
│   ├── settings.py
│   ├── settings_popup.py
│   └── theme.py
├── fonts/
│   └── LEIAME.txt
└── ruler/
    ├── __init__.py
    ├── gear_button.py
    └── ruler_window.py
```

## Próximas etapas

1. Validar esta janela e corrigir eventuais diferenças de DPI/monitores.
2. Implementar captura pontual de uma região com MSS.
3. Adicionar OCR em português (Tesseract + `pytesseract`) e pré-processamento.
4. Integrar síntese de voz offline depois de comparar a qualidade e as licenças das vozes pt-BR.
5. Adicionar testes automatizados, testes manuais por sistema operacional e empacotamento.

## Referências técnicas

- Python: https://www.python.org/downloads/
- PySide6: https://pypi.org/project/PySide6/
- Qt — janelas translúcidas: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html
- Qt — licenciamento: https://doc.qt.io/qt-6/licensing.html
- MSS: https://python-mss.readthedocs.io/latest/
- Tesseract: https://github.com/tesseract-ocr/tesseract
