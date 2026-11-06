"""
transcrever.py - Transcrição de áudios em lote (offline, gratuita)

Uso:
    python transcrever.py "C:\\caminho\\pasta_ou_arquivo"
    python transcrever.py "C:\\audios" --modelo medium
    python transcrever.py "C:\\audios" --srt

Saídas (na pasta "transcricoes" ao lado dos áudios):
    - <nome_do_audio>.txt          texto corrido
    - <nome_do_audio>.srt          legenda com tempos (opcional, --srt)
    - consolidado_transcricoes.xlsx  1 linha por áudio + aba com trechos e tempos

Modelos (precisão x velocidade): tiny < base < small (padrão) < medium < large-v3
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

EXTENSOES = {".mp3", ".wav", ".m4a", ".ogg", ".opus", ".flac", ".aac",
             ".wma", ".mp4", ".mkv", ".webm", ".mov", ".amr"}


def fmt_tempo(seg: float, srt: bool = False) -> str:
    h = int(seg // 3600)
    m = int((seg % 3600) // 60)
    s = int(seg % 60)
    ms = int(round((seg - int(seg)) * 1000))
    if srt:
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    return f"{h:02d}:{m:02d}:{s:02d}"


def listar_audios(caminho: Path) -> list[Path]:
    if caminho.is_file():
        return [caminho]
    return sorted(p for p in caminho.rglob("*")
                  if p.is_file() and p.suffix.lower() in EXTENSOES
                  and "transcricoes" not in p.parts)


def main():
    ap = argparse.ArgumentParser(description="Transcreve áudios para texto.")
    ap.add_argument("entrada", help="Arquivo de áudio ou pasta com áudios")
    ap.add_argument("--modelo", default="small",
                    help="tiny, base, small, medium, large-v3 (padrão: small)")
    ap.add_argument("--idioma", default="pt", help="Código do idioma (padrão: pt)")
    ap.add_argument("--srt", action="store_true", help="Gerar também legenda .srt")
    ap.add_argument("--saida", default=None, help="Pasta de saída (opcional)")
    args = ap.parse_args()

    entrada = Path(args.entrada).expanduser().resolve()
    if not entrada.exists():
        sys.exit(f"Não encontrado: {entrada}")

    audios = listar_audios(entrada)
    if not audios:
        sys.exit("Nenhum arquivo de áudio encontrado.")

    base = entrada if entrada.is_dir() else entrada.parent
    pasta_saida = Path(args.saida) if args.saida else base / "transcricoes"
    pasta_saida.mkdir(parents=True, exist_ok=True)

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("Instale as dependências: pip install faster-whisper openpyxl")

    print(f"Carregando modelo '{args.modelo}' (1ª vez faz download)...")
    try:
        modelo = WhisperModel(args.modelo, device="cuda", compute_type="float16")
        print("Usando GPU.")
    except Exception:
        modelo = WhisperModel(args.modelo, device="cpu", compute_type="int8")
        print("Usando CPU.")

    resumo, trechos = [], []

    for i, audio in enumerate(audios, 1):
        print(f"\n[{i}/{len(audios)}] {audio.name}")
        t0 = time.time()
        try:
            segmentos, info = modelo.transcribe(
                str(audio), language=args.idioma, beam_size=5,
                vad_filter=True,          # ignora silêncios
                temperature=0.0,          # resultado reprodutível
            )
            textos, srt_linhas = [], []
            for n, seg in enumerate(segmentos, 1):
                txt = seg.text.strip()
                textos.append(txt)
                trechos.append([audio.name, fmt_tempo(seg.start),
                                fmt_tempo(seg.end), txt])
                srt_linhas.append(f"{n}\n{fmt_tempo(seg.start, True)} --> "
                                  f"{fmt_tempo(seg.end, True)}\n{txt}\n")
                print(f"  {fmt_tempo(seg.start)} {txt}")

            texto = " ".join(textos)
            nome = audio.stem
            (pasta_saida / f"{nome}.txt").write_text(texto, encoding="utf-8")
            if args.srt:
                (pasta_saida / f"{nome}.srt").write_text("\n".join(srt_linhas),
                                                         encoding="utf-8")
            resumo.append([audio.name, str(audio.parent), fmt_tempo(info.duration),
                           round(time.time() - t0, 1), len(texto.split()),
                           "OK", texto])
        except Exception as e:
            print(f"  ERRO: {e}")
            resumo.append([audio.name, str(audio.parent), "", "", 0,
                           f"ERRO: {e}", ""])

    # Planilha consolidada
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Transcricoes"
    cab = ["Arquivo", "Pasta", "Duração", "Tempo proc. (s)", "Palavras",
           "Status", "Texto"]
    ws.append(cab)
    for r in resumo:
        ws.append(r)
    for c, larg in zip("ABCDEFG", [30, 40, 10, 14, 10, 12, 100]):
        ws.column_dimensions[c].width = larg
    for cel in ws["G"][1:]:
        cel.alignment = Alignment(wrap_text=True, vertical="top")

    ws2 = wb.create_sheet("Trechos")
    ws2.append(["Arquivo", "Início", "Fim", "Texto"])
    for t in trechos:
        ws2.append(t)
    ws2.column_dimensions["A"].width = 30
    ws2.column_dimensions["D"].width = 100

    for planilha in (ws, ws2):
        for cel in planilha[1]:
            cel.font = Font(bold=True)
        planilha.freeze_panes = "A2"
        planilha.auto_filter.ref = planilha.dimensions

    carimbo = datetime.now().strftime("%Y%m%d_%H%M")
    xlsx = pasta_saida / f"consolidado_transcricoes_{carimbo}.xlsx"
    wb.save(xlsx)
    print(f"\nConcluído. Saídas em: {pasta_saida}\nPlanilha: {xlsx.name}")


if __name__ == "__main__":
    main()
