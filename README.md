# Automated Multi-Platform Job Scraper & Candidate Qualification Pipeline

An intelligent, multi-board job scraping and evaluation system designed to bypass aggressive anti-bot protections (Naukri/Akamai), eliminate senior sponsored listings, deeply evaluate full Job Description (JD) text against a candidate's resume, and track applications in a centralized ledger.

---

## 📚 Documentation Links
- 🪟 **[Windows Installation & Execution Guide (`WINDOWS_SETUP.md`)](WINDOWS_SETUP.md)** — 1-click batch scripts, PowerShell instructions, and troubleshooting for Windows 10/11.
- 🛠️ **[Architecture & Engineering Guide (`HOW_TO_WRITE_THIS_PROJECT.md`)](HOW_TO_WRITE_THIS_PROJECT.md)** — Detailed technical blueprint explaining anti-bot bypass strategies (Playwright Firefox vs Akamai), JD NLP regex parsing, schema normalization, and system design.
- 🚀 **[User & Operator Guide (`HOW_TO_USE.md`)](HOW_TO_USE.md)** — Step-by-step instructions on environment setup, running scrape pipelines, interpreting generated artifacts, tracking applications, and customizing for new tech stacks.

---

## ⚡ Quick Start

### Cross-Platform (Windows, Linux, macOS)
```bash
# 1. Install dependencies or install package in editable mode
pip install -e .
playwright install firefox

# 2. Run the end-to-end multi-board scrape and qualification pipeline
job-scrape
# Or: python run_scrape_and_fit.py

# 3. View tracked applications and stats
job-track --list
job-track --stats
# Or: python track_applications.py --list
```

### Windows 1-Click Execution
- **Setup:** Double-click `setup_windows.bat`
- **Run Scraper:** Double-click `run_scraper.bat`
- **Check Tracker:** Double-click `track_applications.bat`


---

## 🎯 Key Features

1. **Tri-Engine Scraping Architecture:**
   - **Playwright Firefox for Naukri:** Bypasses Naukri's Next.js RSA encrypted tokens and Akamai Bot Manager (`406 recaptcha required` and `403 forbidden`).
   - **Playwright Firefox for Glassdoor:** Bypasses Cloudflare Turnstile bot challenges (`Security | Glassdoor`) through isolated browser sessions.
   - **JobSpy Integration:** Scrapes LinkedIn and Indeed concurrently with deep description parsing.
2. **Date Freshness Enforcement:**
   - Enforces native `jobAge=7` and date sorting (`sort=f`) on Naukri to prevent stale 3+ week old listings.
   - Converts relative dates (`"1 day ago"`, `"Few hours ago"`) into standardized ISO dates (`YYYY-MM-DD`).
3. **Deep Job Description (JD) NLP Qualification:**
   - Scans full JD text (not just card metadata) for hidden experience barriers (e.g. `6+ years of hands-on experience`, `at least 3 yrs`).
   - Handles unicode en-dashes (`–`), em-dashes (`—`), and markdown escapes (`\-`).
   - Disqualifies senior titles (`Senior`, `Lead`, `Principal`, `Architect`, `Manager`) and requirements $\ge 3$ years.
   - Categorizes early-career opportunities into **`APPLY`** (0–1 yr / Fresher) and **`SHOT`** (~2 yrs / Reach).
4. **Persistent State Tracking & De-Duplication:**
   - Maintains a central ledger (`applied_jobs.csv`).
   - Automatically suppresses already applied positions on future scrapes.
   - Includes a CLI tracker (`track_applications.py`) to manage interview stages.

---

## 📁 Repository Structure

```
job-scraping/
├── pyproject.toml                 # Standard PEP 517/621 packaging (entry points: job-scrape, job-track)
├── requirements.txt               # Pinned pip dependencies
├── WINDOWS_SETUP.md               # Dedicated Windows installation & troubleshooting guide
├── setup_windows.bat / .ps1       # 1-click Windows setup scripts
├── run_scraper.bat / .ps1         # 1-click scraper execution scripts
├── track_applications.bat         # 1-click tracker launcher for Windows
├── README.md                      # Project overview and quick links
├── HOW_TO_USE.md                  # Comprehensive user and operator guide
├── HOW_TO_WRITE_THIS_PROJECT.md   # Architectural and code-level engineering guide
├── naukri_scraper.py              # Anti-bot Playwright Firefox scraper for Naukri.com
├── glassdoor_scraper.py           # Anti-bot Playwright Firefox scraper for Glassdoor.com (Cloudflare bypass)
├── run_scrape_and_fit.py          # Multi-board orchestrator and deep JD evaluation engine
├── track_applications.py          # Application ledger CLI tool
├── applied_jobs.csv               # Active tracker of submitted job applications
├── master_applied_jobs.csv        # Master persistent backup of submitted job applications
├── job-scraper.ipynb              # Interactive Jupyter notebook playground
└── scrape_YYYYMMDD_HHMMSS/        # Timestamped folders created per execution
    ├── jobs.csv                   # Raw 34-column multi-board dump
    ├── apply_shortlist.csv        # Prioritized early-career roles with match justifications
    ├── job_fit_report.md          # Domain-grouped executive markdown report
    └── scrape.log                 # Execution logs and platform breakdown
```
