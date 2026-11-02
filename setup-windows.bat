@echo off
setlocal
cd /d "%~dp0"
echo === Cai dat GFlow Studio cho Windows ===
echo Can Python 3.11 tro len, Google Chrome va ket noi Internet.
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m venv .bootstrap
) else (
  python -m venv .bootstrap
)
if errorlevel 1 goto failed
".bootstrap\Scripts\python.exe" -m pip install uv
if errorlevel 1 goto failed
cd /d "%~dp0..\gflow-cli"
"%~dp0.bootstrap\Scripts\python.exe" -m uv sync --frozen --no-dev --python 3.12 --managed-python --no-build-package lz4
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto failed
echo.
echo Cai dat thanh cong. Mo start.bat de su dung.
pause
exit /b 0
:failed
echo.
echo Chua cai dat xong. Xem loi phia tren.
echo Neu chua co Python, cai Python 3.12 tu https://www.python.org/downloads/windows/
echo Chon Add python.exe to PATH khi cai, sau do mo lai tep nay.
pause
exit /b 1
