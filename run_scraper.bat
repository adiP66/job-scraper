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

echo =======================================================
echo   Launching Job Scraping & JD Evaluation Pipeline
echo =======================================================

python run_scrape_and_fit.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Script encountered an error (exit code %errorlevel%).
)

echo.
pause
