@echo off
setlocal
cd /d "%~dp0"
title GFlow Studio
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONNOUSERSITE=1"
set "GFLOW_CLI_UPDATE_CHECK=0"
set "GFLOW_CLI_HOME=%~dp0data\profiles"
if not exist "%~dp0runtime\python.exe" goto incomplete
if not exist "%~dp0app\app.py" goto incomplete
echo GFlow Studio dang khoi dong...
echo Khong can cai Python. Khong dong cua so nay khi dang su dung.
"%~dp0runtime\python.exe" -s "%~dp0app\app.py" --port 0 --open
if errorlevel 1 (
  echo.
  echo Ung dung khong khoi dong duoc. Loi nam ngay phia tren.
  pause
  exit /b 1
)
exit /b 0
:incomplete
echo Hay nhan Extract All de giai nen TOAN BO tep ZIP truoc.
echo Giu MO-UNG-DUNG.bat canh hai thu muc app va runtime.
pause
exit /b 1
