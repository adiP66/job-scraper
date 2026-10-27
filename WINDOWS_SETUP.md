# Windows Installation & Execution Guide

This project is **100% compatible with Windows 10 & Windows 11**. All file operations, network requests, terminal logging, and browser automations use cross-platform standards (Python standard library, `os.path`, explicit `utf-8` encoding, and Playwright for Windows).

---

## 🚀 Method 1: Automatic 1-Click Setup (Recommended)

### 1. Install Python
If not already installed, download **Python 3.10+** from [python.org](https://www.python.org/downloads/).
> ⚠️ **CRITICAL:** On the first installer screen, make sure to check **"Add python.exe to PATH"**.

### 2. Run the Windows Setup Script
Double-click **`setup_windows.bat`** (or open Command Prompt / PowerShell in this folder and run it):
```cmd
setup_windows.bat
```
This script will automatically:
1. Verify Python and PATH configuration
2. Create an isolated virtual environment (`.venv`)
3. Upgrade `pip` and install all dependencies from `requirements.txt`
4. Install the package in editable mode (`pip install -e .`)
5. Download the headless **Playwright Firefox** engine for Windows

---

## 🏃 Running the Project on Windows

Once setup is complete, you have three easy ways to run the scraper and application tracker:

### Option A: 1-Click Batch Runners
- **Run the Scraper & JD Evaluation:** Double-click **`run_scraper.bat`**
- **View All Applications:** Double-click **`track_applications.bat`**
- **Manage Applications via CMD:**
  ```cmd
  track_applications.bat --stats
  track_applications.bat --follow-ups
  track_applications.bat --company "HDFC Bank" --status "Interview"
  track_applications.bat --template -c "JPMorganChase"
  ```

### Option B: PowerShell Runners
```powershell
# Setup via PowerShell
.\setup_windows.ps1

# Run Scraper
.\run_scraper.ps1

# Track Applications
.\track_applications.ps1 --stats
.\track_applications.ps1 --follow-ups
.\track_applications.ps1 --template -c "JPMorganChase"
```

### Option C: CLI Commands inside Virtual Environment
Open PowerShell or CMD inside the project folder:
```cmd
.venv\Scripts\activate
job-scrape
job-track --stats
job-track --follow-ups
```

---

## 🛠️ Method 2: Manual Step-by-Step Setup

If you prefer setting up manually via Command Prompt or PowerShell:

```cmd
:: 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

:: 2. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

:: 3. Install Playwright Firefox engine
playwright install firefox

:: 4. Run the scraper
python run_scrape_and_fit.py

:: 5. Use the tracker
python track_applications.py --list
```

---

## 🔍 Common Windows Troubleshooting

### 1. "playwright: command not found" or Playwright browser missing
Make sure your virtual environment is active before installing or running:
```cmd
.venv\Scripts\activate
playwright install firefox
```

### 2. PowerShell: "Execution of scripts is disabled on this system"
If PowerShell blocks `activate.ps1` or `setup_windows.ps1`, run this once in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Special Characters or Emojis in Legacy Command Prompt
Windows Command Prompt (`cmd.exe`) historically defaults to codepage 437/1252. The batch scripts and Python files automatically set `chcp 65001` and configure `sys.stdout.reconfigure(encoding="utf-8")`. For the best terminal experience on Windows, use **Windows Terminal** (pre-installed on Windows 11, or free from Microsoft Store for Windows 10).

---

## 📦 Package Summary
- **Package Name:** `job-scraper-pipeline`
- **Version:** `1.1.0`
- **Entry Points:** `job-scrape`, `job-track`
- **Supported OS:** Windows 10/11, macOS, Linux (x86_64 / ARM64)
- **Primary Scraper Engines:**
  - **Naukri Engine:** Playwright Firefox (Akamai Bot Manager & RSA bypass)
  - **Glassdoor Engine:** Playwright Firefox (Cloudflare Turnstile challenge bypass)
  - **LinkedIn & Indeed:** JobSpy TLS Client with deep description parsing
