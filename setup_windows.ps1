# Windows PowerShell Setup Script for Job Scraping Pipeline
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  Job Scraping Pipeline - PowerShell Automated Setup" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $pythonCmd) {
    $pythonCmd = (Get-Command py -ErrorAction SilentlyContinue)
}

if (-not $pythonCmd) {
    Write-Error "Python was not found in PATH! Please install Python 3.10+ and enable 'Add to PATH'."
    exit 1
}

Write-Host "[1/4] Found Python: $($pythonCmd.Source)" -ForegroundColor Green
& $pythonCmd.Source --version

# 2. Virtual Environment
if (-not (Test-Path ".venv")) {
    Write-Host "[2/4] Creating virtual environment (.venv)..." -ForegroundColor Yellow
    & $pythonCmd.Source -m venv .venv
} else {
    Write-Host "[2/4] Virtual environment (.venv) already exists." -ForegroundColor Green
}

# 3. Dependencies
Write-Host "[3/4] Installing dependencies from requirements.txt..." -ForegroundColor Yellow
$venvPython = ".\.venv\Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt
& $venvPython -m pip install -e .

# 4. Playwright Browser
Write-Host "[4/4] Installing Playwright Firefox engine..." -ForegroundColor Yellow
$playwrightCmd = ".\.venv\Scripts\playwright.exe"
& $playwrightCmd install firefox

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  Setup Completed Successfully!" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "You can now run:"
Write-Host "  .\run_scraper.ps1              (to scrape and evaluate jobs)"
Write-Host "  .\track_applications.ps1 --list (to view/manage applications)"
Write-Host "  Or activate .venv and run: job-scrape / job-track"
