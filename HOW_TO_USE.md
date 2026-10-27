# User & Operator Guide: How to Use the Job Scraping Pipeline

This guide walks you through setting up, running, customizing, and tracking jobs using the automated job-scraping and qualification pipeline.

---

## 1. Prerequisites & Environment Setup

### 1. Python Environment
Make sure you have Python 3.10 or higher installed:
```bash
python3 --version
```

### 2. Install Required Packages
Install the required scraping and data processing libraries (or install the package in editable mode):
```bash
pip install -e .
# Or: pip install -r requirements.txt
```

### 3. Install Playwright Firefox Binary
Both the Naukri and Glassdoor scrapers rely on Playwright Firefox to bypass Akamai and Cloudflare Turnstile anti-bot protections:
```bash
playwright install firefox
```

> **Windows Users:** You can simply double-click `setup_windows.bat` or run `.\setup_windows.ps1` in PowerShell to complete this entire setup automatically. See [WINDOWS_SETUP.md](WINDOWS_SETUP.md).

---

## 2. Running a Scrape Pipeline

To execute a fresh multi-platform scrape across LinkedIn, Indeed, Glassdoor, and Naukri with deep JD evaluation:

```bash
# Using CLI entry point
job-scrape

# Or directly via Python:
python run_scrape_and_fit.py

# Windows 1-click runner:
# Double-click run_scraper.bat (or run .\run_scraper.ps1)
```

### What Happens During Execution:
1. **Reads Applied Tracker:** Loads `applied_jobs.csv` so previously applied jobs are not re-suggested.
2. **LinkedIn & Indeed Scrape:** Queries LinkedIn and Indeed via JobSpy with full JD retrieval.
3. **Glassdoor Scrape:** Launches headless Playwright Firefox in clean sessions to bypass Cloudflare Turnstile bot blocks and auto-dismiss popups.
4. **Naukri Scrape:** Launches headless Playwright Firefox and queries fresh listings (`sort=f`, `jobAge=7`, `experience=0`) bypassing Akamai Bot Manager and Next.js RSA encryption.
5. **Data Normalization:** Deduplicates raw postings across all platforms by `(title, company)`.
6. **Deep JD NLP Analysis:** Inspects both metadata and full text to disqualify senior roles ($\ge 3$ years) and score alignment against your resume.
7. **Generates Timestamped Folder:** Creates a dedicated directory `scrape_YYYYMMDD_HHMMSS/` containing all run artifacts.

---

## 3. Understanding the Output Artifacts

Every run creates a new folder (e.g., `scrape_20260906_115155/`) with four files:

| File | Purpose | When to Use |
|---|---|---|
| **`job_fit_report.md`** | High-level executive brief formatted in markdown. Groups top jobs by domain (AI/ML, Python Backend, Data Engineering) with match reasons and direct application links. | **Read this first** for a quick visual overview of what to apply to today. |
| **`apply_shortlist.csv`** | Clean tabular CSV of all qualified jobs (`APPLY` and `SHOT` tiers), including direct URLs, salaries, and match justifications. | Import into Google Sheets, Notion, or Excel for tabular filtering. |
| **`jobs.csv`** | Complete raw data dump (34 columns) containing every scraped listing before filtering. | Use for debugging or investigating why a specific company/role was excluded. |
| **`scrape.log`** | Execution transcript and summary counts by platform. | Check to verify all platforms returned listings without network timeouts. |

---

## 4. Tracking & Managing Job Applications

The project includes a central ledger (`applied_jobs.csv`) and a CLI tracking tool (`track_applications.py`).

### 1. View All Applied Jobs
```bash
python3 track_applications.py --list
```
Prints an interactive terminal view of all applied companies, roles, application dates, platforms, and URLs.

### 2. View Application Pipeline Statistics
```bash
python3 track_applications.py --stats
```
Displays a breakdown of applications by current status (`Applied`, `Interview`, `Assessment`, `Offer`) and by platform.

### 3. Update Application Status (Interview / Assessment / Offer)
When an employer gets in touch, update their status directly from the terminal:
```bash
# Mark as in interview stage
python3 track_applications.py --company "Atidan" --status "Interview"

# Mark online assessment received
python3 track_applications.py --company "JPMorganChase" --status "Assessment"

# Record offer or rejection
python3 track_applications.py --company "HDFC Bank" --status "Offer"
```

### 4. Automatic Scraper De-Duplication
Because `applied_jobs.csv` is checked during every run of `run_scrape_and_fit.py`, any job you have already applied to will automatically be suppressed in subsequent scrape runs.

---

## 5. Customizing the Pipeline for Your Profile

All parameters are centrally defined in `run_scrape_and_fit.py` and can be customized in seconds.

### 1. Change Location
In `run_scrape_and_fit.py`:
```python
# To target Pune, Bengaluru, or All India Remote:
LOCATION = "Pune"  # or "Bengaluru" or "India"
```

### 2. Change Target Queries
Under `main()` in `run_scrape_and_fit.py`:
```python
# Add your custom search keywords
naukri_queries = [
    ("fastapi developer", 0),
    ("machine learning intern", None),
    ("data engineer fresher", 0)
]
```

### 3. Change Tech Stack Keywords
In `evaluate_job()`:
```python
# Customize tech stack flags to match your resume
has_golang = "golang" in combined_text or "go" in combined_text
has_react = "react" in combined_text or "nextjs" in combined_text
```

### 4. Adjust Freshness Window
In `run_scrape_and_fit.py`:
```python
HOURS_OLD = 72   # Past 3 days only (default is 168 hours = 7 days)
```

---

## 6. Interactive Jupyter Notebook (`job-scraper.ipynb`)

If you prefer exploring jobs inside an interactive Jupyter interface:
1. Start Jupyter:
   ```bash
   jupyter lab  # or jupyter notebook
   ```
2. Open [`job-scraper.ipynb`](file:///run/media/adityaparkhe/A006623906621118/Python/job-scraping/job-scraper.ipynb).
3. Run the cells to interactively test queries, inspect DataFrames, and visualize salary distributions.

---

## 7. Troubleshooting & FAQs

### Q: Naukri returns 0 jobs or times out.
* **Fix:** Ensure Playwright Firefox is installed (`playwright install firefox`). Do not switch to Chromium as Akamai Bot Manager will block headless Chromium.

### Q: Why did a job with "Fresher" in the title get skipped?
* **Fix:** Check the JD in `jobs.csv`. Some agencies put "Fresher" in the title to attract clicks, but specify "3+ years hands-on experience required" inside the text. The pipeline prioritizes JD reality over title bait.

### Q: How do I run this automatically every morning?
* Add a cron job on Linux:
  ```bash
  crontab -e
  # Run every weekday at 9:00 AM
  0 9 * * 1-5 cd /run/media/adityaparkhe/A006623906621118/Python/job-scraping && python3 run_scrape_and_fit.py >> daily_scrape.log 2>&1
  ```
