@echo off
chcp 65001 >nul
REM Arraste uma pasta ou arquivo de audio sobre este .bat
REM (deixe este .bat na mesma pasta do transcrever.py)
if "%~1"=="" (
  set /p ENTRADA=Cole o caminho da pasta ou arquivo de audio:
) else (
  set ENTRADA=%~1
)
python "%~dp0transcrever.py" "%ENTRADA%" --modelo small
pause
