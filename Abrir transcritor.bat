@echo off
cd /d "%~dp0"
echo Abrindo o Transcritor de Audio em http://localhost:8766
echo Deixe esta janela aberta enquanto usa. Feche para encerrar.
start "" http://localhost:8766
python -m http.server 8766 --bind 127.0.0.1
if errorlevel 1 (
  echo.
  echo Nao foi possivel iniciar. Este atalho precisa do Python instalado.
  pause
)
