@echo off
setlocal
cd /d "%~dp0"

:: Enforce UTF-8 in Windows terminal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

:: Activate virtual environment if available
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

if "%~1"=="" (
    python track_applications.py --list
) else (
    python track_applications.py %*
)
