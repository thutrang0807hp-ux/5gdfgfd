@echo off
cd /d "%~dp0"
if not exist "..\gflow-cli\.venv\Scripts\python.exe" (
  echo Chua cai dat. Hay mo setup-windows.bat truoc.
  pause
  exit /b 1
)
"..\gflow-cli\.venv\Scripts\python.exe" app.py --open %*
if errorlevel 1 pause
