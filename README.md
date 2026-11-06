# Transcritor de Áudio

Transforma áudios e vídeos em texto, com o tempo de cada fala, e exporta para **.txt**, **.srt** (legenda) e **.xlsx** (consolidado).
Usa o modelo **Whisper**, que roda **no seu navegador**: nenhum áudio é enviado para a internet.

## Como usar

**Pelo link (GitHub Pages):** abra a página, solte os áudios e aguarde.

**Neste computador:** clique duas vezes em `Abrir transcritor.bat` (precisa do Python).
Abrir o `index.html` direto com dois cliques **não funciona**.

Na primeira vez, o modelo escolhido é baixado (de 40 MB a 800 MB, conforme o modelo). Depois ele fica guardado no navegador e funciona offline.

## Formatos aceitos

MP3, M4A, WAV, OGG, OPUS (áudios do WhatsApp), FLAC, AAC, além do áudio de vídeos MP4, WEBM e MOV.

Quando o navegador não consegue ler um arquivo (ex.: **M4A sem perda/ALAC** do Gravador de Voz do iPhone, AMR, WMA), entra um leitor extra (FFmpeg em WebAssembly), baixado só na primeira vez que for necessário (~32 MB). Ele fica dividido em 3 partes (`vendor/ffmpeg-core.wasm.part0..2`) para respeitar o limite de 25 MB do upload pelo site do GitHub.

## Modelos

| Modelo | Velocidade | Precisão | Download |
|---|---|---|---|
| Tiny | muito rápido | baixa | ~40 MB |
| Base | rápido | média | ~80 MB |
| **Small** (padrão) | média | boa | ~250 MB |
| Large v3 Turbo | lenta sem GPU | alta | ~800 MB |

Se o computador tiver GPU compatível com WebGPU (Chrome/Edge atualizados), ela é usada automaticamente. Sem GPU, o processamento é feito na CPU.

## Saídas

- **.txt**: o texto da tela (editável antes de exportar).
- **.srt**: uma legenda com tempos por arquivo.
- **.xlsx** `consolidado_transcricoes_AAAAMMDD_HHMM.xlsx`, com duas abas:
  - `Transcricoes`: Arquivo, Duração, Tempo proc. (s), Palavras, Status, Modelo, Texto
  - `Trechos`: Arquivo, Início, Fim, Texto (uma linha por fala)

Mesmo modelo + mesmo áudio = mesmo resultado (decodificação determinística, sem amostragem aleatória).

## Áudios longos e progresso salvo

- Arquivos acima de 40 MB são lidos em **blocos de 10 minutos** (o arquivo não é carregado inteiro na memória), então gravações de várias horas funcionam.
- O progresso fica **salvo no navegador** a cada trecho. Se a aba fechar ou travar, solte o **mesmo arquivo** de novo: ele continua de onde parou. O ✕ ao lado do arquivo (ou "Limpar") apaga o progresso salvo.
- **Começar em** (ex.: `00:34:00` ou `34`): pula o início de um arquivo novo.
- Dá para exportar `.txt`, `.srt` e `.xlsx` a qualquer momento, mesmo no meio (no Excel aparece `PARCIAL até hh:mm:ss`).

## Como funciona

1. O navegador decodifica o áudio e converte para 16 kHz mono.
2. O áudio é dividido em blocos de até 29 s, sempre cortando no ponto mais silencioso entre 22 s e 29 s, para não partir palavras.
3. Blocos em silêncio são pulados, e frases típicas de "alucinação" do Whisper ("Legendas pela comunidade…", "Obrigado por assistir") são descartadas.
4. Cada bloco é transcrito por um worker em segundo plano, e os tempos são recompostos na linha do tempo do arquivo.

## Versão em Python (lote / pastas grandes)

A pasta `python/` tem a versão de linha de comando, que processa uma pasta inteira (inclusive subpastas) e gera o mesmo `.xlsx`:

```
pip install faster-whisper openpyxl
python python/transcrever.py "C:\Audios" --modelo small --srt
```

Ou arraste a pasta sobre `python/transcrever.bat`.

## Publicar no GitHub Pages

Settings → Pages → Branch: `main` / `root` → Save.
O link aparece em alguns minutos: `https://SEU-USUARIO.github.io/transcritor-audio/`

## Arquivos

- `index.html`: a página
- `worker.js`: roda o Whisper em segundo plano
- `vendor/`: bibliotecas (transformers.js 3.8.1 + ONNX Runtime WASM, SheetJS, FFmpeg.wasm 0.12)
- `python/`: versão em Python para lotes
