@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo   Job Scraping Pipeline - Windows Automated Setup
echo =======================================================

:: 1. Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python was not found in PATH!
        echo Please install Python 3.10+ from https://www.python.org/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    ) else (
        set PY_CMD=py
    )
) else (
    set PY_CMD=python
)

echo [1/4] Found Python:
%PY_CMD% --version

:: 2. Create Virtual Environment if not exists
if not exist ".venv" (
    echo [2/4] Creating virtual environment (.venv)...
    %PY_CMD% -m venv .venv
) else (
    echo [2/4] Virtual environment (.venv) already exists.
)

:: 3. Activate Virtual Environment & Install Dependencies
echo [3/4] Installing dependencies from requirements.txt...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

:: 4. Install Playwright Firefox Browser
echo [4/4] Installing Playwright Firefox engine...
playwright install firefox

echo =======================================================
echo   Setup Completed Successfully!
echo =======================================================
echo You can now run:
echo   - run_scraper.bat         (to scrape and evaluate jobs)
echo   - track_applications.bat  (to view/manage applications)
echo   - Or inside .venv: job-scrape / job-track
echo =======================================================
pause
